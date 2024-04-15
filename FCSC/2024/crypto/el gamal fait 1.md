# El Gamal Fait 1/2 - 320

The service sign messages using El Gamal vulnerable to forgery attacks.

Looking to [wikipedia](https://en.wikipedia.org/wiki/ElGamal_signature_scheme#Existential_forgery), we can see this:
![alt-text](https://i.imgur.com/5YGzS9H.png)

So we can take $e = 1$ and we have:
$r = gy$ [p]
and
$s = -r$ [p-1]

```py
from random import randint
from Crypto.Util.number import long_to_bytes, bytes_to_long
from pwn import *

sock = remote("challengesock.france-cybersecurity-challenge.fr",2151)

sock.recvline()
p = int(sock.recvline()[len(b'p = '):-1])
g = int(sock.recvline()[len(b'g = '):-1])
y = int(sock.recvline()[len(b'y = '):-1])

r = g*y % p
s = (-r) % (p-1)
m = (-r) % (p-1)

M = str(m).encode()
R = str(r).encode()
S = str(s).encode()
sock.recvline()
sock.sendline(M)
sock.recvline()
sock.sendline(R)
sock.recvline()
sock.sendline(S)
print(sock.recvline())
print(sock.recvline())
```
