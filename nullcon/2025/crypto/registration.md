# Registration

This challenge asks us to forge a valid signature without knowing the secret key.
Here is the code of the remote:

```py
#!/bin/python3
from hashlib import sha256
from secret import flag
from Crypto.Util import number
import math
import os

BITS = 1024

class Pubkey(object):
	def __init__(self, n, e, a):
		self.n = n
		self.a = a
		self.e = e

	def verify(self, msg, s):
		if type(msg) == str: msg = msg.encode()
		h = number.bytes_to_long(sha256(msg).digest())
		return pow(s,self.e,self.n) == pow(self.a, h, self.n)

	def __str__(self):
		return f'n = {self.n}\na = {self.a}\ne = {self.e}'

class Key(Pubkey):
	def __init__(self, bits):
		self.p = number.getPrime(bits >> 1)
		self.q = number.getPrime(bits >> 1)
		self.n = self.p * self.q
		phi = (self.p - 1) * (self.q - 1)
		while True:
			e = number.getRandomInteger(bits)
			if math.gcd(e, phi) == 1: break
		self.e = e
		self.d = number.inverse(e, phi)
		while True:
			a = number.getRandomInteger(bits)
			if math.gcd(a, self.n) == 1: break
		self.a = a

	def sign(self, msg):
		if type(msg) == str: msg = msg.encode()
		h = number.bytes_to_long(sha256(msg).digest())
		return pow(self.a, h * self.d, self.n)

	def public(self):
		return Pubkey(self.n, self.e, self.a)

	def __str__(self):
		return f'n = {self.n}\na = {self.a}\ne = {self.e}\np = {self.p}'

if __name__ == '__main__':
	key = Key(BITS)
	print(key.public())
	while True:
		print('''Welcome to our conference reception. Can you provide a valid signature to confirm that you are alowed to participate? If not, please be patient and let the next person in the queue go fist.
		1) wait
		2) sign''')
		option = int(input('> '))
		if option == 1:
			challenge = os.urandom(BITS >> 3)
			signature = key.sign(challenge)
			print(f'Challenge: {challenge.hex()}')
			print(f'Signature: {signature}')
		elif option == 2:
			challenge = os.urandom(BITS >> 3)
			print(f'Challenge: {challenge.hex()}')
			signature = int(input('Signature: '))
			if key.verify(challenge, signature):
				print(flag)
			else:
				print('YOU SHALL NOT PASS!')
				break
		else:
			print('Invalid answer')
			break
```

The vulnerability here lies in the fact that the message hash is directly multiplied by the private exponent `d`, which allows us to leverage the extended Euclidean algorithm to compute a valid signature for any challenge.
To do it we will collect multiple `(h, s)` pairs then find two hash values that are coprime.
Then we will use the extended Euclidean algorithm to compute a valid signature using modular exponentiation.


## solve.py

```py
from pwn import *
import hashlib
from Crypto.Util.number import bytes_to_long, long_to_bytes

def extended_gcd(a, b):
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = extended_gcd(b % a, a)
        return (g, x - (b // a) * y, y)

def mod_pow(base, exp, mod):
    if exp >= 0:
        return pow(base, exp, mod)
    else:
        inverse = pow(base, -1, mod)
        return pow(inverse, -exp, mod)

def find_co_prime_pair(h_list):
    for i in range(len(h_list)):
        for j in range(i + 1, len(h_list)):
            h1 = h_list[i]
            h2 = h_list[j]
            g, _, _ = extended_gcd(h1, h2)
            if g == 1:
                return (i, j)
    return None

r = remote('52.59.124.14', 5026)

r.recvuntil(b'n = ')
n = int(r.recvline().strip())
r.recvuntil(b'a = ')
a = int(r.recvline().strip())
r.recvuntil(b'e = ')
e = int(r.recvline().strip())

h_list = []
s_list = []

while True:
    r.sendlineafter(b'> ', b'1')

    r.recvuntil(b'Challenge: ')
    challenge_hex = r.recvline().strip().decode()
    challenge = bytes.fromhex(challenge_hex)
    h = bytes_to_long(hashlib.sha256(challenge).digest())

    r.recvuntil(b'Signature: ')
    s = int(r.recvline().strip())
    h_list.append(h)
    s_list.append(s)
    print(f"Collected h={h}")

    pair = find_co_prime_pair(h_list)
    if pair:
        i, j = pair
        h1 = h_list[i]
        h2 = h_list[j]
        s1 = s_list[i]
        s2 = s_list[j]
        print(f"Found co-prime h1={h1}, h2={h2}")
        break

g, x, y = extended_gcd(h1, h2)
assert g == 1, "GCD is not 1"

r.sendlineafter(b'> ', b'2')
r.recvuntil(b'Challenge: ')
challenge_hex = r.recvline().strip().decode()
challenge = bytes.fromhex(challenge_hex)
h_target = bytes_to_long(hashlib.sha256(challenge).digest())

x_prime = x * h_target
y_prime = y * h_target

s_part1 = mod_pow(s1, x_prime, n)
s_part2 = mod_pow(s2, y_prime, n)
signature = (s_part1 * s_part2) % n

r.sendlineafter(b'Signature: ', str(signature).encode())
print(r.recvline().decode())

a = int(r.recvline().strip())
r.recvuntil(b'e = ')
e = int(r.recvline().strip())

h_list = []
s_list = []

while True:
    r.sendlineafter(b'> ', b'1')

    r.recvuntil(b'Challenge: ')
    challenge_hex = r.recvline().strip().decode()
    challenge = bytes.fromhex(challenge_hex)
    h = bytes_to_long(hashlib.sha256(challenge).digest())

    r.recvuntil(b'Signature: ')
    s = int(r.recvline().strip())
    h_list.append(h)
    s_list.append(s)
    print(f"Collected h={h}")

    pair = find_co_prime_pair(h_list)
    if pair:
        i, j = pair
        h1 = h_list[i]
        h2 = h_list[j]
        s1 = s_list[i]
        s2 = s_list[j]
        print(f"Found co-prime h1={h1}, h2={h2}")
        break

g, x, y = extended_gcd(h1, h2)
assert g == 1, "GCD is not 1"

r.sendlineafter(b'> ', b'2')
r.recvuntil(b'Challenge: ')
challenge_hex = r.recvline().strip().decode()
challenge = bytes.fromhex(challenge_hex)
h_target = bytes_to_long(hashlib.sha256(challenge).digest())

x_prime = x * h_target
y_prime = y * h_target

s_part1 = mod_pow(s1, x_prime, n)
s_part2 = mod_pow(s2, y_prime, n)
signature = (s_part1 * s_part2) % n

r.sendlineafter(b'Signature: ', str(signature).encode())
print(r.recvline().decode())
```
