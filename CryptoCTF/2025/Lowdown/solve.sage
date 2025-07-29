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
