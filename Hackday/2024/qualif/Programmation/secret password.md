# Secret password - 100

The chall consists in retrieving a password and they tell us to connect to this instance: `nc challenges.hackday.fr 50393`

```
>> nc challenges.hackday.fr 50393

Charset is abcdefghijklmnopqrstuvwxyz
Size is 5
>>> a
Bad length input. Expected 1, got 5
>>> abcd
Bad length input. Expected 4, got 5
>>> abcde
1 character are correct 
```
It seems like we need to guess a 5 chars strings to get the password, let's write a script to bruteforce it.
After some searchs, we can see that the chall had 3 steps:

|step | charsets | size
|---|---|---|
| 1 | abcdefghijklmnopqrstuvwxyz | 5 |
| 2 | abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ | 15 |
| 3 | abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 | 35 |


So we made this garbage code: 
 ```py
import socket, time
import pwn


def isint(a):
    try:
        int(a)
        return True
    except:
        return False

def findcharsets(charsets, size):
    keys = []
    for c in charsets:
        password_attempt = (c * size).encode()
        time.sleep(0.1)
        s.send(password_attempt)
        response = s.recvuntil(">>> ")
        occur = response.decode()[0]
        if isint(occur):
            occur = int(occur)
            if occur > 0:
                print('Found:', c)
                keys.append(c)
    return keys

def findflag(keys, size):
    flag = ['$'] * size
    for c in keys:
        for i in range(size):
            a = ['$'] * size
            a[i] = c
            tentative = ''.join(a)
            time.sleep(0.1)
            s.send(tentative)
            response = s.recvuntil(">>> ")
            print(response)
            occur = response.decode()[0]
            if isint(occur):
                occur = int(occur)
                print(tentative, occur)
                if occur == 1:
                    flag[i] = c
    return ''.join(flag)


s = pwn.remote('challenges.hackday.fr', 50393)
response = s.recvuntil(">>> ")


flag1 = findflag(findcharsets("abcdefghijklmnopqrstuvwxyz", 5), 5)
s.send(flag1)
response = s.recvuntil(">>> ")
flag2 = findflag(findcharsets("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", 15), 15)
s.send(flag2)
response = s.recvuntil(">>> ")
print(response)
flag3 = findflag(findcharsets("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", 35), 35)
s.send(flag3)

while True:
    try:
        response = s.recv(1024)
        print(response)
    except:
        exit()
```

it could be optimized but it works so it's fine.

