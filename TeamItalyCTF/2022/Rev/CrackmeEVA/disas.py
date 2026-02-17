import struct

def reg(b):
    if 0x81 <= b <= 0x85:
        return f"r{b - 0x80}"
    return f"?reg(0x{b:02x})"

def tape(b):
    return "rodata" if b else "data"

def disas(code):
    pc = 0
    lines = []
    while pc < len(code):
        addr = pc
        op = code[pc]

        # 1-byte instructions
        if op == 0x99:
            lines.append((addr, "exit"))
            pc += 1
        elif op == 0x97:
            lines.append((addr, "getchar"))
            pc += 1
        elif op == 0x69:
            lines.append((addr, "ret"))
            pc += 1
        elif op == 0x74:
            lines.append((addr, "fneg"))
            pc += 1

        # 2-byte instructions
        elif op == 0x58:
            ch = code[pc+1]
            if 0x20 <= ch <= 0x7e:
                lines.append((addr, f"puti '{chr(ch)}'"))
            elif ch == 0x0a:
                lines.append((addr, "puti '\\n'"))
            else:
                lines.append((addr, f"puti 0x{ch:02x}"))
            pc += 2
        elif op == 0x90:
            s = code[pc+1]
            lines.append((addr, f"inc {tape(s)}"))
            pc += 2
        elif op == 0x89:
            s = code[pc+1]
            lines.append((addr, f"dec {tape(s)}"))
            pc += 2
        elif op == 0x98:
            s = code[pc+1]
            lines.append((addr, f"putchar {tape(s)}"))
            pc += 2
        elif op == 0x75:
            r = code[pc+1]
            lines.append((addr, f"store {reg(r)}"))
            pc += 2

        # 3-byte: reg,reg instructions
        elif op == 0x91:
            lines.append((addr, f"add {reg(code[pc+1])}, {reg(code[pc+2])}"))
            pc += 3
        elif op == 0x93:
            r1, r2 = reg(code[pc+1]), reg(code[pc+2])
            lines.append((addr, f"sub {r1}, {r2}"))
            pc += 3
        elif op == 0x52:
            r1, r2 = reg(code[pc+1]), reg(code[pc+2])
            lines.append((addr, f"div {r1}, {r2}"))
            pc += 3
        elif op == 0x96:
            lines.append((addr, f"mov {reg(code[pc+1])}, {reg(code[pc+2])}"))
            pc += 3
        elif op == 0x71:
            r1, r2 = reg(code[pc+1]), reg(code[pc+2])
            lines.append((addr, f"cmp_lt {r1}, {r2}"))
            pc += 3
        elif op == 0x76:
            r1, r2 = reg(code[pc+1]), reg(code[pc+2])
            lines.append((addr, f"cmp_eq {r1}, {r2}"))
            pc += 3

        # 3-byte: reg,imm instructions
        elif op == 0x57:
            r, imm = code[pc+1], code[pc+2]
            lines.append((addr, f"addi {reg(r)}, {imm}"))
            pc += 3
        elif op == 0x59:
            r, imm = code[pc+1], code[pc+2]
            lines.append((addr, f"subi {reg(r)}, {imm}"))
            pc += 3

        # 3-byte: load (tape selector + reg)
        elif op == 0x78:
            s, r = code[pc+1], code[pc+2]
            lines.append((addr, f"load {reg(r)}, {tape(s)}"))
            pc += 3

        # 3-byte: jmp_if (direction + offset)
        elif op == 0x86:
            d, off = code[pc+1], code[pc+2]
            target = addr + off if d == 0 else addr - off
            signed = off if d == 0 else -off
            lines.append((addr, f"jmp_if {signed:+d}  ; -> 0x{target:04x}"))
            pc += 3

        # 3-byte: call (direction + offset)
        elif op == 0x73:
            d, off = code[pc+1], code[pc+2]
            base = addr + 3
            target = base + off if d == 0 else base - off
            lines.append((addr, f"call 0x{target:04x}"))
            pc += 3

        else:
            # unknown opcode — causes handler() to return -1 (VM exit)
            lines.append((addr, f".byte 0x{op:02x}"))
            pc += 1

    return lines


if __name__ == "__main__":
    raw = open("crackme_eva.ik1vm", "rb").read()
    code_len = struct.unpack_from("<I", raw, 0)[0]
    code = raw[12 : 12 + code_len]

    print(f"; ik1vm disassembly: {code_len} bytes\n")
    for addr, text in disas(code):
        print(f"  {addr:04x}:  {text}")
