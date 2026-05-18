from pwn import *
import random

def gf_mult(x, y):
    R = 0xE1000000000000000000000000000000
    z = 0
    for i in range(128):
        if (y & (1 << (127 - i))):
            z ^= x
        carry = x & 1
        x >>= 1
        if carry:
            x ^= R
    return z

def gf_pow(x, power):
    res = 1 << 127
    base = x
    while power > 0:
        if power & 1:
            res = gf_mult(res, base)
        base = gf_mult(base, base)
        power >>= 1
    return res

def gf_inv(x):
    return gf_pow(x, (1 << 128) - 2)

def gf_sqrt(x):
    return gf_pow(x, 1 << 127)

def bytes_to_int(b):
    return int.from_bytes(b, 'big')

def int_to_bytes(i):
    return i.to_bytes(16, 'big')
    
def explore(io, pt):
    io.sendlineafter(b"> ", b"1")
    io.sendlineafter(b"for?: ", pt)
    res = io.recvline().decode().strip()
    nonce, sec, mag = res.split()[-1].split(":")
    return bytes.fromhex(sec), bytes.fromhex(mag)

def bitwise_or(byte_lists):
    res = bytearray(16)
    for b in byte_lists:
        for i in range(16):
            res[i] |= b[i]
    return bytes(res)

# io = process(["python3", "given-files/chal.py"])
io = remote("chall.polygl0ts.ch", 6273)

PT1 = b'A' * 16
PT2 = b'B' * 16

ct1_list, t1_list = [], []
for _ in range(19):
    c, t = explore(io, PT1)
    ct1_list.append(c)
    t1_list.append(t)

ct2_list, t2_list = [], []
for _ in range(19):
    c, t = explore(io, PT2)
    ct2_list.append(c)
    t2_list.append(t)
io.sendlineafter(b"> ", b"2")

C1 = bitwise_or(ct1_list)
T1 = bitwise_or(t1_list)
C2 = bitwise_or(ct2_list)
T2 = bitwise_or(t2_list)

T1_int = bytes_to_int(T1)
T2_int = bytes_to_int(T2)
C1_int = bytes_to_int(C1)
C2_int = bytes_to_int(C2)
T_xor = T1_int ^ T2_int
C_xor = C1_int ^ C2_int

H2 = gf_mult(T_xor, gf_inv(C_xor))
H = gf_sqrt(H2)
A = b"explorarationing"
L = (128).to_bytes(8, 'big') + (128).to_bytes(8, 'big')
H3 = gf_mult(H2, H)

t1 = gf_mult(bytes_to_int(A), H3)
t2 = gf_mult(C1_int, H2)
t3 = gf_mult(bytes_to_int(L), H)
S0 = T1_int ^ t1 ^ t2 ^ t3
t2_list = []

for _ in range(15):
    io.sendlineafter(b"word: ", b"FAIL")
    res = io.recvline().decode().strip()
    parts = res.split()[-1].strip("!").split(":")
    mag = bytes.fromhex(parts[2])
    t2_list.append(mag)

T2 = bitwise_or(t2_list)
T2_int = bytes_to_int(T2)
PT2 = b"give me the flag"

# S1 = C1 ^ PT1. => CT2 = PT2 ^ S1
CT2 = bytes([p ^ c ^ p1 for p, c, p1 in zip(PT2, C1, PT1)])
B3_int = bytes_to_int(CT2)

L2 = (17*8).to_bytes(8, 'big') + (16*8).to_bytes(8, 'big')
B4_int = bytes_to_int(L2)
H4 = gf_mult(H3, H)
V = T2_int ^ gf_mult(B3_int, H2) ^ gf_mult(B4_int, H) ^ S0
inv_H4 = gf_inv(H4)
correct_storm = None

for b in range(256):
    B2 = bytes([b]) + b'\x00'*15
    B1_int = gf_mult(V ^ gf_mult(bytes_to_int(B2), H3), inv_H4)
    candidate = int_to_bytes(B1_int) + bytes([b])
    
    random.seed(candidate)
    r_ct1 = random.getrandbits(128).to_bytes(16, "little")
    r_t1 = random.getrandbits(128).to_bytes(16, "little")
    
    if (bytes([x & y for x, y in zip(C1, r_ct1)]) == ct1_list[0] and 
        bytes([x & y for x, y in zip(T1, r_t1)]) == t1_list[0]):
        correct_storm = candidate
        break

log.success(f"Storm recovered: {correct_storm.hex()}")

random.seed(correct_storm)
for _ in range(38 + 15):
    random.getrandbits(128)
    random.getrandbits(128)

random.getrandbits(128).to_bytes(16, "little")
r_t_16 = random.getrandbits(128).to_bytes(16, "little")

io.sendlineafter(b"word: ", bytes([x & y for x, y in zip(T2, r_t_16)]).hex().encode())
io.interactive()
