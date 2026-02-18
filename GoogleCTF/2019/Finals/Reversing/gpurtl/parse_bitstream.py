import struct, sys
from collections import Counter

def parse_bitstream(filename):
    with open(filename, 'rb') as f:
        data = f.read()

    assert data[:8] == b'gpurtlPC', f"bad magic: {data[:8]}"
    block_count = struct.unpack('>I', data[8:12])[0]
    port_bits = struct.unpack('>H', data[12:14])[0]
    jump_count = struct.unpack('>H', data[14:16])[0]

    print(f"gpurtlPC: {block_count} blocks ({block_count * 256} BLEs), "
          f"{port_bits} port bits, {jump_count} jumps")

    total_bles = block_count * 256
    bles = []
    offset = 16
    for i in range(total_bles):
        a, b = struct.unpack('>II', data[offset:offset+8])
        offset += 8
        bles.append({
            'index': i,
            'lut': a >> 16,
            'addrs': [b & 0xFFF, (b >> 12) & 0xFFF,
                      ((a & 0xF) << 8) | (b >> 24), (a >> 4) & 0xFFF],
            'raw_a': a, 'raw_b': b,
        })

    jumps = []
    for i in range(jump_count):
        jumps.append(struct.unpack('>I', data[offset:offset+4])[0])
        offset += 4

    assert offset == len(data), f"extra data: {len(data) - offset} bytes"
    return {
        'block_count': block_count,
        'port_bits': port_bits,
        'bles': bles,
        'jumps': jumps,
    }


KNOWN_LUTS = {
    0x0000: "CONST_0", 0xFFFF: "CONST_1",
    0xAAAA: "BUF(A)", 0x5555: "NOT(A)",
    0xCCCC: "BUF(B)", 0x3333: "NOT(B)",
    0xF0F0: "BUF(C)", 0x0F0F: "NOT(C)",
    0xFF00: "BUF(D)", 0x00FF: "NOT(D)",
    0x8888: "AND(A,B)", 0xEEEE: "OR(A,B)",
    0x6666: "XOR(A,B)", 0x9999: "XNOR(A,B)",
    0x1111: "NOR(A,B)", 0x7777: "NAND(A,B)",
    0x6996: "XOR4(A,B,C,D)", 0x9669: "XNOR4(A,B,C,D)",
    0x9696: "XOR3(A,B,C)", 0x6969: "XNOR3(A,B,C)",
    0xCACA: "MUX(C,A,B)", 0xACAC: "MUX(C,B,A)",
    0xE8E8: "MAJ(A,B,C)",
}


def analyze_luts(config):
    lut_counts = Counter(b['lut'] for b in config['bles'])
    non_dummy = sum(1 for b in config['bles'] if b['lut'] != 0)

    print(f"\n{len(config['bles'])} BLEs, {non_dummy} active, {len(lut_counts)} unique LUTs")
    print(f"\nTop 30 LUT truth tables:")
    for lut, count in lut_counts.most_common(30):
        name = KNOWN_LUTS.get(lut, "")
        print(f"  0x{lut:04X}: {count:4d}  {name}")


def analyze_addresses(config):
    jump_refs = Counter()
    local_refs = Counter()
    for ble in config['bles']:
        if ble['lut'] == 0:
            continue
        for addr in ble['addrs']:
            if addr & 0x800:
                jump_refs[addr & 0x7FF] += 1
            else:
                local_refs[addr] += 1

    print(f"\n{len(jump_refs)} unique jump refs, {len(local_refs)} unique local offsets")
    print(f"\nTop 20 jump references:")
    for idx, count in jump_refs.most_common(20):
        dest = config['jumps'][idx] if idx < len(config['jumps']) else '???'
        print(f"  jump[{idx}] -> data[{dest}]: {count} refs")


def simulate(config, input_bits_map, input_data, output_bits_map, done_bit, max_iters=512):
    port_bits = config['port_bits']
    total_bles = len(config['bles'])
    bp = port_bits

    state = [0] * (port_bits + 2 * total_bles)

    # resolve all addresses up front
    resolved = []
    for ble in config['bles']:
        addrs = []
        for a in ble['addrs']:
            if a & 0x800:
                addrs.append(config['jumps'][a & 0x7FF])
            else:
                addrs.append(bp + 2 * ble['index'] + a - 0x400)
        resolved.append(addrs)

    # write input
    bit_idx = 0
    for byte_val in input_data:
        for bit_pos in range(7, -1, -1):
            if bit_idx < len(input_bits_map):
                state[input_bits_map[bit_idx]] = (byte_val >> bit_pos) & 1
            bit_idx += 1

    COMB_CYCLES = 64
    iteration = 0
    while iteration < max_iters:
        for _ in range(COMB_CYCLES):
            for i, ble in enumerate(config['bles']):
                lut = ble['lut']
                a = resolved[i]
                lut_idx = state[a[0]] | (state[a[1]] << 1) | (state[a[2]] << 2) | (state[a[3]] << 3)
                state[bp + 2 * i] = (lut >> lut_idx) & 1

        # check done
        if state[bp + done_bit] == 1:
            break

        # rising edge: latch registers
        for i in range(total_bles):
            state[bp + 2*i + 1] = state[bp + 2*i]

        iteration += 1
        if iteration % 10 == 0:
            print(f"  iter {iteration}...", end='\r')

    iteration += 1  # count from 1
    if state[bp + done_bit] != 1:
        print(f"\nno convergence after {max_iters} iters!")
        return None

    print(f"\nconverged after {iteration} iterations")

    result = []
    for i in range(0, len(output_bits_map), 8):
        v = 0
        for j in range(8):
            if i + j < len(output_bits_map):
                v |= state[bp + output_bits_map[i + j]] << (7 - j)
        result.append(v)
    return bytes(result)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <bitstream.bin> [--simulate] [--analyze]")
        sys.exit(1)

    filename = sys.argv[1]
    config = parse_bitstream(filename)

    if '--analyze' in sys.argv or len(sys.argv) == 2:
        analyze_luts(config)
        analyze_addresses(config)

    if '--simulate' in sys.argv:
        INPUT_BITS = list(range(0xFF, -1, -1))
        OUTPUT_BITS = list(range(0x4D8, 0x2D8, -2))
        DONE_BIT = 0x4DA

        test_input = input().encode()
        assert len(test_input) == len(b"CTF{---------------------------}"), "invalid input length"
        print(f"\nsimulating: {test_input}")

        EXPECTED = bytes([
            0x5c, 0xba, 0x23, 0xde, 0x38, 0x7a, 0x00, 0x67,
            0x7d, 0x8f, 0x7c, 0x6e, 0xf2, 0x11, 0x10, 0xe8,
            0x29, 0x0a, 0x1e, 0xb6, 0xad, 0x34, 0x36, 0x74,
            0x45, 0xfe, 0x3b, 0x6d, 0xf5, 0xa0, 0x8f, 0x9d,
        ])

        result = simulate(config, INPUT_BITS, test_input, OUTPUT_BITS, DONE_BIT)
        if result:
            print(f"output:   {result.hex()}")
            print(f"expected: {EXPECTED.hex()}")
            print(f"match: {result == EXPECTED}")
