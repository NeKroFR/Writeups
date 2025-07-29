# Lowdown - Tough Cookie 🥴

The challenge involves a custom signature scheme built on matrix operations over the finite field $GF(256)$ with 10x10 matrices. The goal is to forge a valid signature for a randomly generated 40-character message provided by the server, which we cannot sign directly because the signing oracle only allows messages shorter than 10 characters.

## Given files
We are given the remote sources in the [lowdown.sage](./lowdown.sage) sage script. Let's go through it's main components.

### Key generation:
First the key is based on two matrices, `g` a random invertible matrix and `ga` which is derived from `g` raised to some powers involving secret values:
```py
def makey(k):
    while True:
        g = random_matrix(F, k)
        if g.is_invertible():
            ng = 1 << 192  # approximated order
            break
    r, a = [randint(2, ng - 2) for _ in '01']
    gg = g ** r
    pkey, skey = (g, gg ** a), r
    return (pkey, skey)
```

### Signing messages:

To sign a message, the remote computes the `sha1` of the message, picks a random `n`, and generates signature matrices `s` and `t` using matrix exponentiation and inversion:

```py
def sign(pkey, skey, msg):
	g, ga = pkey
	ng = 1 << 192 # g.order()
	_h = random_oracle(msg)
	assert _h <= ng
	_g = g ** skey
	n = randint(2, ng - 2)
	s, t = ga * (_g.inverse()) ** (n * _h), _g ** n
	return (s, t)
```

Also, the server let us sign some messages, however they must  be less than 10 chars:

```py
if len(_msg) >= 10:
	die(border, 'Sorry, I sign only short messages! :/')
_s, _t = sign(pkey, skey, _msg)
```

### Verification

To get the flag, we must sign a random message: 
```py
msg = ''.join([string.printable[randint(0, 85)] for _ in range(40)]).encode()
```
and check that we have `s * t^h == ga`  with `s` starting with `13` and `t` with `37`:

```py
def verify(sgn, pkey, msg):
    _, ga = pkey
    s, t = sgn
    _h = random_oracle(msg)
    return s * t ** _h == ga
```

```py
if verify(sgn, pkey, msg) and str(_s).startswith('13') and str(_t).startswith('37'):
	pr(border, f'Congratulation! You got the flag!')
	die(border, f'flag = {flag}')
```

Finally, matrices are converted to long for transmission using a custom hash `H(M)`, which takes discrete logs of each matrix element and concatenates their 8-bit binary strings:
```py
def H(M):
    k, _H = M.nrows(), []
    for i in range(k):
        for j in range(k):
            _h = h(M[i, j])  # discrete log
            _H.append(bin(_h)[2:].zfill(8))
    return ''.join(_H)

def M2i(M):
    return int(H(M), 2)
```

We can also convert them back to matrix using the `Hinv` function.

To sum up, through the server we can get the public key, sign short messages, verify signatures and sign the target message to get the flag.

## Solving the challenge

To get the flag we must assert `s * t^h == ga` where `h = SHA1(message)`, `s` and `t` are 10x10 invertible matrices over GF(256), and `ga` is the public key matrix. We must also have the integer representations `M2i(s)` and `M2i(t)` starting with `13` and `37`.

First of all we can rearrange the equation from `s * t^h == ga` to `s = ga * t^(-h)`. Thanks to this transformation, we can then pick any matrix `t` and compute the corresponding valid signature.

Once we can generate signatures for any matrix, we just need to bruteforce to find the right matrix which will ensure that `M2i(t)` starts with 37, then we compute `s` and check that `M2i(s)` starts with 13.


## solve.sage:
```py
import os
os.environ["TERM"] = "xterm-256color"

from pwn import *
from sage.all import *
from hashlib import sha1
from Crypto.Util.number import *


def M2i(M, F):
    return int(H(M, F), 2)

def random_oracle(msg):
    return bytes_to_long(sha1(msg).digest())

def h(a, F):
    if a == 0:
        return 0
    g = F.gen()
    for i in range(1, 256):
        if g ** i == a:
            return i

def H(M, F):
    k = M.nrows()
    _H = []
    for i in range(k):
        for j in range(k):
            _h = h(M[i, j], F)
            _H.append(bin(_h)[2:].zfill(8))
    return ''.join(_H)

def Hinv(m, k, F):
    B = bin(m)[2:].zfill(8 * k**2)
    g = F.gen()
    _H = [int(B[8*i:8*i + 8], 2) for i in range(k**2)]
    _M = [0 if _h == 0 else g ** _h for _h in _H]
    M = Matrix(F, [[a for a in _M[k*i:k*i + k]] for i in range(k)])
    return M


#r = process(["sage", "lowdown.sage"])
r = remote('91.107.132.34', 31113)

F = GF(256)
k = 10

r.sendlineafter(b'|\t[Q]uit', b'p')
r.recvuntil(b'g  = ')
g_int = int(r.recvline().decode().strip())
r.recvuntil(b'ga = ')  
ga_int = int(r.recvline().decode().strip())
ga = Hinv(ga_int, k, F)

r.sendlineafter(b'|\t[Q]uit', b'g')
r.recvuntil(b'Message = ')
msg_line = r.recvline().decode().strip()

if msg_line.startswith("b'") and msg_line.endswith("'"):
    target_msg = msg_line[2:-1].encode('latin1')
else:
    target_msg = eval(msg_line)

target_h = random_oracle(target_msg)
print(f"Target: {target_msg}")
print(f"Hash: {target_h}")

# Bruteforce a valid signature
for attempt in range(100000):
    t = random_matrix(F, k)
    while not t.is_invertible():
        t = random_matrix(F, k)
    
    t_int = M2i(t, F)
    if not str(t_int).startswith('37'):
        continue
    
    t_inv_h = t ** (-target_h)
    s = ga * t_inv_h
    s_int = M2i(s, F)
    
    if str(s_int).startswith('13'):
        print(f"Found signature: s={str(s_int)[:10]}..., t={str(t_int)[:10]}...")
        
        # Verify the signature
        _h = random_oracle(target_msg)
        if s * (t ** _h) == ga:
            signature = f"{s_int},{t_int}".encode()
            r.sendline(signature)
            response = r.recvall(timeout=10).decode()
            print(response)
            exit()

print("Failed to find signature")
```
