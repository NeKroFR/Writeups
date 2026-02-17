# CrackmeEVA

This challenge is a custom VM (Ik1VM) with anti-debugging, self-modifying code and a hidden x86-64 backdoor. We need to reverse both the emulator binary and the VM bytecode to uncover an encrypted flag check.

We are given an [emulator](https://github.com/TeamItaly/TeamItalyCTF-2022/blob/master/CrackmeEVA/attachments/emulator) binary and a [crackme_eva.ik1vm](https://github.com/TeamItaly/TeamItalyCTF-2022/blob/master/CrackmeEVA/attachments/crackme_eva.ik1vm) bytecode file.

## Reversing the emulator

Opening the emulator in IDA, the binary is not stripped so we get symbol names right away: `handler`, `main`, `print_logo`, `get_reg`, `get_regs`, `start_stub_func`.

### _start and the self-modifying stub:

First thing, `_start` (0x401170) looks wrong, instead of the normal CRT init it's just a `push`/`ret` gadget:

```asm
_start:
  endbr64
  push    offset sub_401289
  retn
```

This jumps to `sub_401289`, which sits right after `start_stub_func` (a tiny function at 0x401256 that's just a prologue with no body, the real code lives in the NOP sled after it at 0x401289).

IDA's decompilation of the stub, with the usual "write access to const memory" warning:

```c
// write access to const memory has been detected, the output may be wrong!
void __fastcall __noreturn sub_401289(__int64 a1, __int64 a2, void (*a3)(void))
{
  sys_mprotect(&dword_400000, 0x6000, 7);       // RWX
  loc_401858 = 0x9090C30040254268;               // patched!
  *(&loc_401858 + 1) = 0x9090909090909090;       // NOP sled
  *(&loc_401858 + 2) = 0x8B4800000392E990;       // jmp back to handler loop
  _libc_start_main(main, argc, &argv, ...);
}
```

So it calls `mprotect` to make `.text` and `.rodata` writable, patches 24 bytes at `loc_401858` inside `handler()`, then resumes normal startup with `__libc_start_main`. More on what that patch does after we look at `handler`.

### main:

`main` is straightforward, reads the `.ik1vm` file header (3 uint32: `code_len`, `ro_data_len`, `data_len`), mallocs buffers, reads code and ro_data, sets up register pointers, calls `print_logo()` then `handler()`:

```c
int main(int argc, const char **argv)
{
  fp = fopen(argv[1], "rb");
  fread(&code_len, 4, 1, fp);
  fread(&ro_data_len, 4, 1, fp);
  fread(&data_len, 4, 1, fp);
  vm.code = malloc(code_len);
  vm.ro_data = malloc(ro_data_len);
  vm.data = malloc(data_len);
  fread(vm.code, code_len, 1, fp);
  fread(vm.ro_data, ro_data_len, 1, fp);
  vm.reg.IP = vm.code;
  vm.reg.ro_data_ptr = vm.ro_data;
  vm.reg.data_ptr = vm.data;
  print_logo();
  return handler();
}
```

The binary has debug info so IDA already knows the struct layouts. The global `vm` is a `virtual_machine`:

```c
struct virtual_machine {  // size=0x48
  +0x00: char *code;
  +0x08: char *ro_data;
  +0x10: char *data;
  +0x18: int code_len;
  +0x1c: int ro_data_len;
  +0x20: int data_len;
  +0x28: registers reg;
};

struct registers {  // size=0x20
  +0x00: char reg1;
  +0x01: char reg2;
  +0x02: char reg3;
  +0x03: char reg4;
  +0x04: char reg5;
  +0x05: char flag;
  +0x08: char *data_ptr;
  +0x10: char *ro_data_ptr;
  +0x18: char *IP;
};
```

Registers are single bytes, so it's an 8-bit VM with two tape pointers and an instruction pointer.

### handler, the VM execution loop:

`handler` is the big one. It puts a `stack` struct on the native stack and loops on `*vm.reg.IP`:

```c
char handler()
{
  stack s;                   // [rbp-0x340]
  s.c.i = 0;                // call stack index = 0
  while (2) {
    switch (*vm.reg.IP) {
      case 0x52: ...         // div
      case 0x57: ...         // addi
      ...
    }
  }
}
```

The `stack` struct:

```c
struct stack {              // size=0x338
  +0x00: char *tmp1;       // temp pointer for current op
  +0x08: char *tmp2;       // temp pointer for current op
  +0x10: cache c;           // call stack
};

struct cache {              // size=0x328
  +0x00: int i;            // stack index
  +0x08: char *cache[100]; // 100-entry return address stack
};
```

Going through each switch case we get the full opcode table. `get_reg` maps `0x81`-`0x85` to r1-r5, `get_regs` reads two consecutive register selectors:

| Opcode | Mnemonic | Description |
|--------|----------|-------------|
| `0x52` | `div` | Division; prints error on div-by-zero |
| `0x57` | `addi` | Add immediate to register |
| `0x58` | `puti` | Print immediate character |
| `0x59` | `subi` | Subtract immediate from register |
| `0x69` | `ret` | Pop IP from call stack |
| `0x71` | `cmp <` | Compare less-than, set flag |
| `0x73` | `call` | Push IP to stack, jump |
| `0x74` | `fneg` | Flip flag register |
| `0x75` | `store` | Store register to data pointer |
| `0x76` | `cmp ==` | Compare equal, set flag |
| `0x78` | `load` | Load from data/ro_data pointer to register |
| `0x86` | `jmp_if` | Conditional jump if flag set |
| `0x89` | `dec` | Decrement data/ro_data pointer |
| `0x90` | `inc` | Increment data/ro_data pointer |
| `0x91` | `add` | Add two registers |
| `0x93` | `sub` | Subtract two registers |
| `0x96` | `mov` | Move register to register |
| `0x97` | `getchar` | Read byte from stdin |
| `0x98` | `putchar` | Write byte from data/ro_data pointer |
| `0x99` | `exit` | Return reg1 |

### What does the startup patch do?

Now looking at what `sub_401289` actually patched. `0x401858` is the div-by-zero error path in the `case 0x52`:

```asm
; original code at 0x401858:
  lea     rdi, "Error: attempting division by 0."
  call    _puts
  mov     eax, 0FFFFFFFFh
  jmp     locret_401C17       ; return -1
```

The patch turns it into:

```asm
; patched code at 0x401858:
  push    0x402542            ; address in .rodata
  ret                         ; jump there
  nop (x11)                   ; padding
  jmp     loc_401C00          ; back to handler's ++IP loop
```

So division by zero doesn't print an error anymore, it jumps to `0x402542` in `.rodata`, and when that returns execution continues in the handler loop.

### Anti-debug routine at 0x402542:

`0x402542` sits in the `.rodata` section, in a region referenced by the `evildata` global (which points to 0x402008, the start of the ASCII art logo, the code blob comes later at 0x402542).

The bytes there start with `push` instructions saving all registers, then a `call $+0` / `pop rsi` to get RIP. On first call it XOR-decrypts 528 bytes of itself (key `0xd30a92546f566c8c`), then runs three anti-debug checks:

- **ptrace:** `ptrace(PTRACE_TRACEME)` via syscall 0x65. Returns -1 if a debugger is attached.
- **Breakpoint scan:** walks `handler()` memory (0x4014db to 0x401c19), counting `0xCC` bytes (INT3 breakpoints).
- **GDB detection:** enumerates `/proc/[1..99999]/status` looking for processes named `"gdb\n"` (checks the 32-bit value `0x0a626467`).

If any check fails: sets `vm.reg.flag = 1` and overwrites 88 bytes at `0x402c39` with garbage.

If all pass: calls `mprotect` on the heap pages containing VM code to make them RWX, then returns to the handler loop.

## Reversing the VM bytecode

### The .ik1vm file format:

```
Offset  Size  Field
0x00    4     code_len    = 4811
0x04    4     ro_data_len = 2171
0x08    4     data_len    = 100
0x0C    4811  code section
0x12D7  2171  ro_data section
```

### Instruction encoding:

Instructions are 1-3 bytes. Register selectors `0x81`-`0x85` (r1-r5), tape selectors `0x00` = data, nonzero = ro_data.

| Size | Opcodes |
|------|---------|
| 1 byte: `[op]` | `exit`(0x99), `getchar`(0x97), `ret`(0x69), `fneg`(0x74) |
| 2 bytes: `[op][arg]` | `puti`(0x58), `inc`(0x90), `dec`(0x89), `putchar`(0x98), `store`(0x75) |
| 3 bytes: `[op][a][b]` | `addi`(0x57), `subi`(0x59), `add`(0x91), `sub`(0x93), `div`(0x52), `mov`(0x96), `cmp_lt`(0x71), `cmp_eq`(0x76), `load`(0x78), `jmp_if`(0x86), `call`(0x73) |

One thing that tripped me up: `jmp_if` always clears the flag to 0 when the branch is taken. When not taken, flag is unchanged. This matters a lot for understanding the control flow.

`jmp_if` encoding: `[86][dir][off]`, `dir=0` means forward (`addr + off`), `dir≠0` means backward (`addr - off`).
`call`: `[73][dir][off]`, same but relative to `addr + 3`. Pushes return address.

I wrote a disassembler [disas.py](./disas.py) based on the opcodes above. Full output is in [asm.txt](./asm.txt).

### The VM program:

Using [disas.py](./disas.py), the bytecode breaks down into these phases:

**1. Print prompt (0x0000-0x000e):**

```
  0000:  sub r1, r1           ; r1 = 0 (null sentinel)
  0003:  putchar rodata       ; print *rodata_ptr
  0005:  inc rodata           ; rodata_ptr++
  0007:  load r3, rodata      ; r3 = *rodata_ptr
  000a:  cmp_eq r3, r1        ; flag = (r3 == 0)
  000d:  fneg                 ; flag = !flag (true while not null)
  000e:  jmp_if -11  ; -> 0x0003
```

Prints ro_data until null byte (the ASCII art logo).

**2. Copy metadata to data tape (0x0011-0x002d):**

```
  0011:  inc rodata           ; skip past null
  0013:  load r2, rodata      ; r2 = flag_len (38)
  0016:  inc rodata
  0018:  sub r5, r5           ; r5 = 0
  001b:  addi r5, 23          ; r5 = 23 (loop count: 1 + 24 bytes)
  001e:  load r4, rodata      ; r4 = *rodata_ptr
  0021:  store r4             ; *data_ptr = r4
  0023:  cmp_lt r1, r5        ; flag = (r1 < 23)
  0026:  addi r1, 1           ; r1++ (counter)
  0029:  inc data
  002b:  inc rodata
  002d:  jmp_if -15  ; -> 0x001e
```

Copies flag length + 24 bytes of decryption parameters (payload offset, length, XOR key as 3x uint64) from ro_data onto the data tape.

**3. Read input (0x0030-0x0042):**

```
  0030:  mov r3, r2           ; r3 = flag_len (38)
  0033:  sub r1, r1           ; r1 = 0
  0036:  addi r1, 1           ; r1 = 1
  0039:  getchar              ; *data_ptr = stdin byte
  003a:  inc data
  003c:  cmp_lt r1, r2        ; flag = (r1 < 38)
  003f:  addi r1, 1           ; r1++
  0042:  jmp_if -9  ; -> 0x0039
```

Reads 38 bytes of input.

**4. Trigger anti-debug via div-by-zero (0x0045-0x004f):**

```
  0045:  subi r3, 1           ; r3 = 37
  0048:  addi r5, 233         ; r5 = 23 + 233 = 256 = 0 (8-bit overflow!)
  004b:  div r1, r5           ; div by zero → patched handler → anti-debug
  004e:  fneg                 ; invert flag
  004f:  jmp_if +117  ; -> 0x00c4
```

This is sneaky, r5 was 23 from phase 2, `addi 233` overflows it to 0 in 8-bit. Division by zero triggers the patched handler which runs the anti-debug routine. After it returns:
- Clean (flag=0): `fneg` makes it 1, jump taken → 0x00c4
- Detected (flag=1): `fneg` makes it 0, falls through → 0x0052

**5a. Fake check, debugger detected path (0x0052-0x00c1):**

```
  0052:  dec data
  0054:  load r3, data        ; r3 = last input byte
  0057:  sub r1, r1
  005a:  addi r1, 125         ; r1 = '}' (125)
  005d:  cmp_eq r3, r1        ; check last byte == '}'
  0060:  fneg
  0061:  jmp_if +103  ; -> 0x00c8   (fail: "Not even the flag format")
  0064:  sub r5, r5
  0067:  sub r2, r2
  006a:  addi r2, 33
  006d:  dec data             ; rewind 33 positions
  006f:  addi r5, 1
  0072:  cmp_lt r5, r2
  0075:  jmp_if -8  ; -> 0x006d
  0078:  subi r1, 2           ; r1 = 123 = '{'
  007b:  load r3, data
  007e:  cmp_eq r3, r1
  0081:  fneg
  0082:  jmp_if +70  ; -> 0x00c8   (fail)
  0085:  dec data
  0087:  subi r1, 20          ; r1 = 103 = 'g'
  ...
  0096:  subi r1, 6           ; r1 = 97 = 'a'
  ...
  00a5:  subi r1, 245         ; r1 = 108 = 'l' (97-245 = 108 mod 256)
  ...
  00b4:  subi r1, 6           ; r1 = 102 = 'f'
  00b7:  load r3, data
  00ba:  cmp_eq r3, r1
  00bd:  jmp_if +74  ; -> 0x0107  (format OK → stack overflow, but backdoor destroyed)
  00c0:  fneg
  00c1:  jmp_if +7  ; -> 0x00c8  (fail)
```

This walks backward through input checking for `flag{...}` format. If it matches, it jumps to the stack overflow, but the anti-debug already trashed the backdoor at `0x402c39`, so it'll crash. This is a decoy to waste your time if you're debugging.

**5b. Clean path trampolines (0x00c4-0x0107):**

```
  00c4:  fneg                 ; flag was cleared to 0 by jmp_if, fneg→1
  00c5:  jmp_if +65  ; -> 0x0106
  ...
  0106:  fneg
  0107:  jmp_if +105  ; -> 0x0170
```

Two `fneg`+`jmp_if` hops over the error message strings to reach 0x0170. The error messages sit between them as `puti` sequences terminated by invalid opcodes (which make the VM exit):

```
  00c8-0103:  puti "\nNot even the flag format...?\n"
  0104:       .byte 0x18    ; invalid opcode → VM exit
  010a-016d:  puti "\nOh no...\nWe better get ready for another impact.\n"
  016e:       .byte 0x10    ; invalid opcode → VM exit
```

**6. Stack overflow (0x0170-0x12ba):**

103 identical blocks that each do a `call` to the next instruction. The VM call stack only has 100 entries, so after 100 calls it overflows past `cache[100]` and starts corrupting the native x86 stack frame of `handler()` (remember the `stack` struct is on the native stack, `cache` is at offset 0x10 in that struct, so overflowing it overwrites `handler()`'s saved rbp and return address).

**7. x86-64 shellcode tail (0x12bd-0x12ca):**

```
  12bd:  .byte 0x48 0xc7 0xc0 0x77 0xa1 ...   ; mov eax, 0x71a177
  12c2:  ...  0x35 0x4e 0x8d 0x31 0x00         ; xor eax, 0x318d4e → 0x402c39
  12c9:  .byte 0x50                             ; push rax
  12ca:  .byte 0xc3                             ; ret → jump to backdoor
```

14 bytes of x86-64 at the end of the bytecode. When `handler()` returns after the stack corruption, it lands here, computes `0x71a177 ^ 0x318d4e = 0x402c39`, and jumps to that address.

So now the full picture: if the anti-debug passes (no debugger), we reach the stack overflow, corrupt the return address, land on the shellcode, and jump to `0x402c39`. If the anti-debug detected something, it already overwrote `0x402c39` with garbage, so even if you get to the shellcode through the fake check path, it crashes.

At `0x402c39` there's a backdoor that reads the decryption parameters from the data tape (the ones copied in phase 2), XOR-decrypts a payload in ro_data, and jumps to the decrypted code. That decrypted code is the real flag check.

## Solving the challenge

### Decrypting the ro_data payload:

The decryption parameters from the metadata:

```
Flag length:     38
Payload offset:  1611 (in ro_data)
Payload length:  560 bytes
XOR key:         0x46bca179a0862975
```

After XOR decryption we get x86-64 code with these strings embedded in it:

```
\nCongratulations!\nSometimes you need a little wishful thinking to keep on hacking.\n
\nOh no...\nWe better get ready for another impact.\n
\nNot even the flag format...?\n
fKfcmxnbfKfKnF$onF$omxnFnQnbnb$onSnQmxfK$onbfKnFfKnQnF$onQnFnbmx
flag{}
```

### The flag check:

The decrypted code checks that the input starts with `flag{` and ends with `}` (38 bytes total, so 32 content bytes). Then it does a bit-level comparison between each content byte and pairs of characters from that 64-byte `other_buf` string.

Tracing through the loop: for each pair of `other_buf` characters, it extracts 4 bits from each using a rotating mask (`rol` by 3, starting at bit 2, so it hits bits 4, 7, 2, 5 in order). These get compared against the input byte's bits via a `neg`/`sbb`/`inc`/`not` sequence that isolates each bit. The even character encodes the high nibble, the odd character encodes the low nibble.

Working out the full mapping:

| Input Bit | other_buf Source Bit |
|-----------|---------------------|
| bit 7 | even char bit 4 |
| bit 6 | even char bit 7 |
| bit 5 | even char bit 2 |
| bit 4 | even char bit 5 |
| bit 3 | odd char bit 4 |
| bit 2 | odd char bit 7 |
| bit 1 | odd char bit 2 |
| bit 0 | odd char bit 5 |

Reversing this on the `other_buf` string gives us the flag. [solve.py](./solve.py):

```py
import struct
from pathlib import Path

def unshuffle(c):
    return ((c>>4)&1)<<3 | ((c>>7)&1)<<2 | ((c>>2)&1)<<1 | ((c>>5)&1)

ik1vm = open("crackme_eva.ik1vm", "rb").read()

# header
code_len, ro_data_len, _ = struct.unpack_from("<III", ik1vm)
ro_data = ik1vm[12 + code_len : 12 + code_len + ro_data_len]

# metadata
meta = ro_data.index(b"\x00") + 1
flag_len = ro_data[meta]
offset, length, key = struct.unpack_from("<QQQ", ro_data, meta + 1)

# decrypt the payload
key_bytes = struct.pack("<Q", key)
buf = bytearray(ro_data)
for i in range(length):
    buf[offset + i] ^= key_bytes[i % 8]
payload = bytes(buf[offset : offset + length])

# grab other_buf between the error string and "flag{}"
fmt_end = payload.index(b"Not even the flag format")
fmt_end = payload.index(b"\n", fmt_end) + 1
flag_buf = payload.index(b"flag{}")
other_buf = payload[fmt_end:flag_buf]
assert len(other_buf) == 64

# revert the bit shuffle
flag = "flag{"
for i in range(32):
    hi, lo = other_buf[2*i], other_buf[2*i+1]
    flag += chr(unshuffle(hi) << 4 | unshuffle(lo))
flag += "}"

print(flag)
```
