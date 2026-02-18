import struct
from collections import Counter, defaultdict

import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')


def parse_bitstream(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    assert data[:8] == b'gpurtlPC'

    block_count = struct.unpack('>I', data[8:12])[0]
    port_bits = struct.unpack('>H', data[12:14])[0]
    jump_count = struct.unpack('>H', data[14:16])[0]

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
        })

    jumps = []
    for i in range(jump_count):
        jumps.append(struct.unpack('>I', data[offset:offset+4])[0])
        offset += 4

    return {
        'block_count': block_count,
        'port_bits': port_bits,
        'bles': bles,
        'jumps': jumps,
    }


LUT_NAMES = {
    0x0000: "CONST_0", 0xFFFF: "CONST_1",
    0xAAAA: "BUF(A)", 0x5555: "NOT(A)",
    0xCCCC: "BUF(B)", 0x3333: "NOT(B)",
    0xF0F0: "BUF(C)", 0x0F0F: "NOT(C)",
    0xFF00: "BUF(D)", 0x00FF: "NOT(D)",
    0x8888: "AND2", 0xEEEE: "OR2",
    0x6666: "XOR2", 0x9999: "XNOR2",
    0x1111: "NOR2", 0x7777: "NAND2",
    0x6996: "XOR4", 0x9669: "XNOR4",
    0x9696: "XOR3", 0x6969: "XNOR3",
    0xCACA: "MUX2",
}


def classify_lut(lut_val):
    if lut_val in LUT_NAMES:
        return LUT_NAMES[lut_val]
    lo4 = lut_val & 0xF
    if lut_val == lo4 | (lo4 << 4) | (lo4 << 8) | (lo4 << 12):
        return "FUNC2(A,B)"
    return "LUT4"


def analyze_signals(config):
    print("\n--- High fan-out signals ---")

    ref_count = Counter()
    for ble in config['bles']:
        if ble['lut'] == 0:
            continue
        for addr in ble['addrs']:
            if addr & 0x800:
                ref_count[addr & 0x7FF] += 1

    mux_count = sum(1 for b in config['bles'] if 'MUX' in classify_lut(b['lut']))
    xor_count = sum(1 for b in config['bles'] if 'XOR' in classify_lut(b['lut']))
    print(f"MUX gates: {mux_count}, XOR gates: {xor_count}")
    print(f"Estimated 32-bit adders: ~{mux_count // 32}")
    print(f"Jump table: {len(config['jumps'])} entries")

    print(f"\nTop fan-out signals:")
    for idx, count in ref_count.most_common(10):
        dest = config['jumps'][idx]
        if dest < config['port_bits']:
            loc = f"PORT[{dest}]"
        else:
            ble_idx = (dest - config['port_bits']) // 2
            is_reg = (dest - config['port_bits']) % 2
            loc = f"BLE[{ble_idx}].{'REG' if is_reg else 'LUT'}"
        print(f"  jump[{idx}] -> {loc}: fan-out={count}")


def generate_plots(config, prefix="circuit"):
    categories = Counter(classify_lut(b['lut']) for b in config['bles'])

    fig, axes = plt.subplots(1, 2, figsize=(18, 8), gridspec_kw={'width_ratios': [1.2, 1]})

    # gate type distribution
    filtered = {k: v for k, v in categories.items() if k != "CONST_0"}
    sorted_cats = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
    labels = [k for k, _ in sorted_cats]
    sizes = [v for _, v in sorted_cats]
    colors = plt.cm.Set3([i / len(labels) for i in range(len(labels))])

    bars = axes[0].barh(range(len(labels)), sizes, color=colors, edgecolor='grey', linewidth=0.5)
    axes[0].set_yticks(range(len(labels)))
    axes[0].set_yticklabels(labels, fontsize=9)
    axes[0].set_xlabel('Count')
    axes[0].set_title(f'Gate Types ({sum(sizes)} active, {categories.get("CONST_0", 0)} padding)')
    axes[0].invert_yaxis()
    for bar, count in zip(bars, sizes):
        axes[0].text(bar.get_width() + 3, bar.get_y() + bar.get_height() / 2,
                     str(count), va='center', fontsize=8)

    # inter-block connectivity heatmap
    bc = config['block_count']
    conn = [[0] * bc for _ in range(bc)]
    for ble in config['bles']:
        if ble['lut'] == 0:
            continue
        src = ble['index'] // 256
        for addr in ble['addrs']:
            if addr & 0x800:
                dest = config['jumps'][addr & 0x7FF]
            else:
                dest = config['port_bits'] + 2 * ble['index'] + addr - 0x400
            if dest >= config['port_bits']:
                dst_block = (dest - config['port_bits']) // 2 // 256
                if 0 <= dst_block < bc:
                    conn[src][dst_block] += 1

    im = axes[1].imshow(conn, cmap='YlOrRd', interpolation='nearest')
    axes[1].set_xlabel('Source Block')
    axes[1].set_ylabel('Destination Block')
    axes[1].set_title('Inter-Block Connectivity')
    axes[1].set_xticks(range(bc))
    axes[1].set_yticks(range(bc))
    plt.colorbar(im, ax=axes[1], shrink=0.8)

    plt.tight_layout()
    plt.savefig(f'{prefix}_analysis.png', dpi=150, bbox_inches='tight')
    print(f"saved {prefix}_analysis.png")

    # per-block gate composition + fan-out
    fig2, axes2 = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={'height_ratios': [1.5, 1]})

    block_cats = defaultdict(Counter)
    for ble in config['bles']:
        cat = classify_lut(ble['lut'])
        if cat != "CONST_0":
            block_cats[ble['index'] // 256][cat] += 1

    all_types = sorted(filtered.keys(), key=lambda k: filtered[k], reverse=True)
    type_colors = {t: plt.cm.Set3(i / len(all_types)) for i, t in enumerate(all_types)}

    x = range(bc)
    bottoms = [0] * bc
    for gt in all_types:
        vals = [block_cats[b].get(gt, 0) for b in range(bc)]
        axes2[0].bar(x, vals, bottom=bottoms, label=gt,
                     color=type_colors[gt], edgecolor='grey', linewidth=0.3)
        bottoms = [b + v for b, v in zip(bottoms, vals)]

    axes2[0].set_xlabel('Block Index')
    axes2[0].set_ylabel('Active Gates')
    axes2[0].set_title('Gate Composition per Block')
    axes2[0].set_xticks(range(bc))
    axes2[0].legend(loc='upper right', fontsize=7, ncol=3)

    fan_out = Counter()
    for ble in config['bles']:
        if ble['lut'] == 0:
            continue
        for addr in ble['addrs']:
            if addr & 0x800:
                dest = config['jumps'][addr & 0x7FF]
            else:
                dest = config['port_bits'] + 2 * ble['index'] + addr - 0x400
            fan_out[dest] += 1

    fo_vals = sorted(fan_out.values(), reverse=True)
    axes2[1].bar(range(len(fo_vals)), fo_vals, color='steelblue', width=1.0)
    axes2[1].set_xlabel('Signal (ranked)')
    axes2[1].set_ylabel('Fan-out')
    axes2[1].set_title('Signal Fan-Out Distribution')
    axes2[1].set_xlim(0, min(200, len(fo_vals)))

    plt.tight_layout()
    plt.savefig(f'{prefix}_layout.png', dpi=150, bbox_inches='tight')
    print(f"saved {prefix}_layout.png")


def main():
    import sys
    filename = sys.argv[1] if len(sys.argv) > 1 else 'ctf.bin'
    config = parse_bitstream(filename)

    print(f"--- {filename} ---")
    print(f"blocks: {config['block_count']}, BLEs: {len(config['bles'])}")
    print(f"port bits: {config['port_bits']}, jumps: {len(config['jumps'])}")

    categories = Counter(classify_lut(b['lut']) for b in config['bles'])
    print(f"\n--- Gate types ---")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat:15s}: {count:4d}")

    analyze_signals(config)
    generate_plots(config)


if __name__ == '__main__':
    main()
