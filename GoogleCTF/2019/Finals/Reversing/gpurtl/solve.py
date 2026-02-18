import struct
import sys
import time

from z3 import Bool, Not, If, Solver, sat, is_true, BoolVal

# from ctf.lua
INPUT_BITS = list(range(0xFF, -1, -1))
OUTPUT_BITS = list(range(0x4D8, 0x2D8, -2))
DONE_BIT = 0x4DA
EXPECTED = bytes([
    0x5c, 0xba, 0x23, 0xde, 0x38, 0x7a, 0x00, 0x67,
    0x7d, 0x8f, 0x7c, 0x6e, 0xf2, 0x11, 0x10, 0xe8,
    0x29, 0x0a, 0x1e, 0xb6, 0xad, 0x34, 0x36, 0x74,
    0x45, 0xfe, 0x3b, 0x6d, 0xf5, 0xa0, 0x8f, 0x9d,
])

# 9 passes suffice for combinational convergence
COMB_PASSES = 9

def parse_bitstream(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    assert data[:8] == b'gpurtlPC'
    block_count = struct.unpack('>I', data[8:12])[0]
    port_bits = struct.unpack('>H', data[12:14])[0]
    jump_count = struct.unpack('>H', data[14:16])[0]

    n = block_count * 256
    bles = []
    offset = 16
    for i in range(n):
        a, b = struct.unpack('>II', data[offset:offset+8])
        offset += 8
        bles.append((
            a >> 16,
            b & 0xFFF, (b >> 12) & 0xFFF,
            ((a & 0xF) << 8) | (b >> 24), (a >> 4) & 0xFFF,
        ))

    jumps = []
    for i in range(jump_count):
        jumps.append(struct.unpack('>I', data[offset:offset+4])[0])
        offset += 4

    return port_bits, bles, jumps


def resolve_addresses(port_bits, bles, jumps):
    state_size = port_bits + 2 * len(bles)
    resolved = []
    for i, (lut, a0, a1, a2, a3) in enumerate(bles):
        addrs = []
        for a in (a0, a1, a2, a3):
            if a & 0x800:
                addrs.append(jumps[a & 0x7FF])
            else:
                v = port_bits + 2 * i + a - 0x400
                addrs.append(v if 0 <= v < state_size else 0)
        resolved.append(tuple(addrs))
    return resolved


def simulate(port_bits, bles, resolved, input_bytes, max_iters=512):
    n = len(bles)
    state = [0] * (port_bits + 2 * n)

    bit_idx = 0
    for byte_val in input_bytes:
        for bit_pos in range(7, -1, -1):
            if bit_idx < 256:
                state[INPUT_BITS[bit_idx]] = (byte_val >> bit_pos) & 1
            bit_idx += 1

    bp = port_bits
    for iteration in range(1, max_iters + 1):
        for _ in range(COMB_PASSES):
            for i in range(n):
                lut = bles[i][0]
                li = bp + 2 * i
                if lut == 0:
                    state[li] = 0
                    continue
                a = resolved[i]
                state[li] = (lut >> (state[a[0]] | (state[a[1]] << 1) | 
                            (state[a[2]] << 2) | (state[a[3]] << 3))) & 1

        if state[bp + DONE_BIT]:
            break
        for i in range(n):
            state[bp + 2*i + 1] = state[bp + 2*i]

    output = bytearray(32)
    for bi in range(32):
        v = 0
        for j in range(8):
            idx = bi * 8 + j
            if idx < len(OUTPUT_BITS):
                v |= state[bp + OUTPUT_BITS[idx]] << (7 - j)
        output[bi] = v
    return bytes(output), iteration


def find_block_structure(port_bits, bles, resolved):
    base = b'CTF{---------------------------}'
    base_out, base_iters = simulate(port_bits, bles, resolved, base)
    print(f"  base: {base_iters} cycles")

    groups = {}
    for byte_idx in range(32):
        test = bytearray(base)
        test[byte_idx] ^= 0x01
        test_out, _ = simulate(port_bits, bles, resolved, bytes(test))
        changed = tuple(sorted(i for i in range(32) if test_out[i] != base_out[i]))
        if changed:
            groups.setdefault(changed, []).append(byte_idx)

    blocks = []
    for out_bytes, in_bytes in sorted(groups.items()):
        blocks.append((sorted(in_bytes), list(out_bytes)))
    return blocks, base_iters


def solve_block(port_bits, bles, resolved, symbolic_byte_indices,
                constrained_output_bytes, num_cycles):
    n = len(bles)
    bp = port_bits

    symbolic_set_bytes = set(symbolic_byte_indices)
    constrained_set = set(constrained_output_bytes)
    template = bytearray(b'CTF{---------------------------}')

    sym_vars = {}
    input_vals = []
    for bit_idx in range(256):
        byte_idx = bit_idx // 8
        bit_pos = 7 - (bit_idx % 8)
        if byte_idx in symbolic_set_bytes:
            v = Bool(f'b{byte_idx}_{bit_pos}')
            input_vals.append(v)
            sym_vars[(byte_idx, bit_pos)] = v
        else:
            input_vals.append(bool((template[byte_idx] >> bit_pos) & 1))

    state = [False] * (bp + 2 * n)
    symbolic_set = set()
    for bit_idx in range(256):
        port = INPUT_BITS[bit_idx]
        state[port] = input_vals[bit_idx]
        if not isinstance(input_vals[bit_idx], bool):
            symbolic_set.add(port)

    print(f"    {len(symbolic_set)} symbolic bits, {len(symbolic_byte_indices)} symbolic bytes")

    def ite(c, t, f):
        if isinstance(c, bool):
            return t if c else f
        if isinstance(t, bool) and isinstance(f, bool):
            if t == f:
                return t
            return c if t else Not(c)
        if t is f:
            return t
        return If(c, t if not isinstance(t, bool) else BoolVal(t),
                     f if not isinstance(f, bool) else BoolVal(f))

    def eval_lut(lut, b0, b1, b2, b3):
        if all(isinstance(x, bool) for x in (b0, b1, b2, b3)):
            return bool((lut >> (int(b0) | (int(b1) << 1) |
                                  (int(b2) << 2) | (int(b3) << 3))) & 1)
        vals = [bool((lut >> i) & 1) for i in range(16)]
        l1 = [ite(b0, vals[2*i+1], vals[2*i]) for i in range(8)]
        l2 = [ite(b1, l1[2*i+1], l1[2*i]) for i in range(4)]
        l3 = [ite(b2, l2[2*i+1], l2[2*i]) for i in range(2)]
        return ite(b3, l3[1], l3[0])

    t0 = time.time()
    for cycle in range(1, num_cycles + 1):
        if cycle == 1 or cycle % 50 == 0:
            elapsed = time.time() - t0
            print(f"    cycle {cycle}/{num_cycles}, "
                  f"{len(symbolic_set)} symbolic, "
                  f"{elapsed:.1f}s      ", end='\r')
            sys.stdout.flush()

        for _ in range(COMB_PASSES):
            for i in range(n):
                lut = bles[i][0]
                li = bp + 2 * i
                if lut == 0:
                    state[li] = False
                    symbolic_set.discard(li)
                    continue
                a = resolved[i]
                if any(addr in symbolic_set for addr in a):
                    result = eval_lut(lut, state[a[0]], state[a[1]],
                                           state[a[2]], state[a[3]])
                    state[li] = result
                    if isinstance(result, bool):
                        symbolic_set.discard(li)
                    else:
                        symbolic_set.add(li)
                else:
                    idx = int(state[a[0]]) | (int(state[a[1]]) << 1) | \
                          (int(state[a[2]]) << 2) | (int(state[a[3]]) << 3)
                    state[li] = bool((lut >> idx) & 1)
                    symbolic_set.discard(li)

        done = state[bp + DONE_BIT]
        if isinstance(done, bool) and done:
            elapsed = time.time() - t0
            print(f"\n    done at cycle {cycle} ({elapsed:.1f}s)")
            break

        for i in range(n):
            li = bp + 2 * i
            ri = li + 1
            state[ri] = state[li]
            if li in symbolic_set:
                symbolic_set.add(ri)
            else:
                symbolic_set.discard(ri)

    sim_time = time.time() - t0

    solver = Solver()
    expected_bits = []
    for bv in EXPECTED:
        for p in range(7, -1, -1):
            expected_bits.append(bool((bv >> p) & 1))

    n_constraints = 0
    for i, bit_offset in enumerate(OUTPUT_BITS):
        byte_idx = i // 8
        if byte_idx not in constrained_set:
            continue
        if i >= len(expected_bits):
            break
        out_val = state[bp + bit_offset]
        exp = expected_bits[i]
        if isinstance(out_val, bool):
            if out_val != exp:
                print(f"\n    concrete mismatch at output bit {i}")
                return None
        else:
            solver.add(out_val if exp else Not(out_val))
            n_constraints += 1

    # ASCII (MSB=0)
    for byte_idx in symbolic_byte_indices:
        v = sym_vars.get((byte_idx, 7))
        if v is not None:
            solver.add(Not(v))

    print(f"    solving ({n_constraints} constraints)...")
    t0 = time.time()
    result = solver.check()
    solve_time = time.time() - t0

    if result == sat:
        model = solver.model()
        solved = {}
        for byte_idx in symbolic_byte_indices:
            val = 0
            for bit_pos in range(7, -1, -1):
                v = sym_vars.get((byte_idx, bit_pos))
                if v is not None and is_true(model.evaluate(v)):
                    val |= 1 << bit_pos
            solved[byte_idx] = val
        print(f"    solved in {solve_time:.1f}s (sim: {sim_time:.1f}s)")
        return solved
    else:
        print(f"    UNSAT ({solve_time:.1f}s)")
        return None


if __name__ == '__main__':
    print("[*] parsing bitstream...")
    port_bits, bles, jumps = parse_bitstream('ctf.bin')
    n = len(bles)
    active = sum(1 for b in bles if b[0] != 0)
    print(f"    {n} BLEs ({active} active)")

    print("\n[*] resolving addresses...")
    resolved = resolve_addresses(port_bits, bles, jumps)

    print("\n[*] concrete simulation check...")
    test_out, test_iters = simulate(
        port_bits, bles, resolved, b'CTF{---------------------------}')
    print(f"    {test_iters} cycles, output: {test_out.hex()}")

    print("\n[*] differential analysis...")
    blocks, num_cycles = find_block_structure(port_bits, bles, resolved)
    for i, (in_bytes, out_bytes) in enumerate(blocks):
        print(f"    block {i}: in={in_bytes} -> out={out_bytes}")

    print(f"\n[*] Z3 symbolic solve...")
    print(f"    target: {EXPECTED.hex()}")
    print(f"    depth: {num_cycles} cycles")

    flag = bytearray(b'CTF{' + b'\x00' * 27 + b'}')

    total_t0 = time.time()
    for i, (in_bytes, out_bytes) in enumerate(blocks):
        unknown = [b for b in in_bytes if 4 <= b <= 30]
        if not unknown:
            for b in in_bytes:
                if b < 4:
                    flag[b] = b'CTF{'[b]
                elif b == 31:
                    flag[b] = ord('}')
            continue

        print(f"\n  block {i}: solving bytes {unknown}")
        solved = solve_block(port_bits, bles, resolved, unknown,
                             set(out_bytes), num_cycles + 10)
        if solved is None:
            print(f"  FAILED on block {i}!")
            exit(1)

        for byte_idx, val in sorted(solved.items()):
            flag[byte_idx] = val
            ch = chr(val) if 32 <= val < 127 else '?'
            print(f"    byte[{byte_idx}] = 0x{val:02x} '{ch}'")

    total_time = time.time() - total_t0
    print(flag.decode())
    print(f"\n    total solve time: {total_time:.1f}s")
