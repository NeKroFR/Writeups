# Brainrot13

The challenge gives us a `dist.py` file:

```py
from Crypto.Util.number import bytes_to_long, getPrime
import codecs
import re

p = getPrime(512)
q = getPrime(512)
n = p * q
e = 3

flag = 'UMDCTF{redacted}'
assert re.fullmatch("UMDCTF\\{[a-z]+\\}", flag)
assert len(flag) == 28
rotflag = codecs.encode(flag, 'rot13')

def encrypt(b):
    while (len(b) < 120):
        # Optimal Asymmetric Encryption Padding
        b += b'OAEP'
    pt = bytes_to_long(b)
    return pow(pt, e, n)

print(f"n = {n}")
print(f"ct1 = {encrypt(flag.encode())}")
print(f"ct2 = {encrypt(rotflag.encode())}")
```

We can see that the flag is encrypted using RSA with `e=3` and then it creates two ciphertexts:
- `ct1`: The encrypted flag
- `ct2`: The encrypted ROT13 version of the flag

We also know that the flag len is 28 and the encryption add padding bytes `OAEP` to reach 120 bytes.


This challenge is vulnerable to Coppersmith's small roots attack because `e=3` and the flag len is only 28. Furthermore, we can predict the padding.

We can represent the plaintext as `flag * 256^92 + padding`, create a polynomial representing `(x * 256^92 + padding)^3 ≡ ct1 (mod n)`
and  make it a monic polynomial to then find its small roots (the flag).

## solve.sage

```py
from sage.all import *
from Crypto.Util.number import long_to_bytes

n = 96685821958083526684938680238271304286887980859392922334047044570819254535637534763165507014186569373580269436562287115575895071477094697751185058766474544708343165263644182297048851208627306861544906558700694910255483830223450427540731613986917757415247541102253686241820221043700623282515147528145504812161
ct1 = 31415617614942980419493801728329478459882170524654275330189702271291172239569974917796230082992620119324013322311500280165046115132115888952730272833129650105740565501270236988682510607126061981801996717672566496111413558704046446132351270004211376270714769910968931266620926532143617027921568831958784579911

# Compute padding
padding_unit = 79 * 256**3 + 65 * 256**2 + 69 * 256 + 80  # "OAEP"
padding = sum(padding_unit * (256**(4 * (22 - k))) for k in range(23))

# Define the polynomial ring
R = IntegerModRing(n)
P = PolynomialRing(R, 'x')
x = P.gen()

# Define the polynomial
f = (x * 256**92 + padding)**3 - ct1

# Get the leading coefficient
leading_coeff = (256**92)**3

# Compute the modular inverse of the leading coefficient
inv_leading_coeff = inverse_mod(leading_coeff, n)

# Make the polynomial monic
f_monic = (f * inv_leading_coeff)

# Find small roots
roots = f_monic.small_roots(X=2**224, beta=0.5)  # Flag is 28 bytes

flag = long_to_bytes(int(roots[0]))
print(flag.decode())
```
