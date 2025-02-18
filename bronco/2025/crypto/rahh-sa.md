#  Rahh-SA

In this challenge, we are given an unusual twist on RSA where one of the primes is negative:

```py
# RAHHH!!!!!

import math

e = 65537

p = -811

q = 0#??????

n = p * q

phi_n = (p + 1) * (q + 1) 

# but first, a word from
# our sponsored function!
def extendedEuclideanAlgo(e, phi_n):
    A1, A2, A3 = 1, 0, phi_n # var "b"
    B1, B2, B3 = 0, 1, e # var "a

    while (True):
        if B3 == 0:
            return -1 
            # indicates no inverse!
        if B3 == 1:
            return B2 
            # B2: modular inverse

        Q = math.floor(A3 / B3)
        T1, T2, T3 = A1 - (Q * B1), A2 - (Q * B2), A3 - (Q * B3)
        A1, A2, A3 = B1, B2, B3
        B1, B2, B3 = T1, T2, T3

def encrypt(int, e, n):
    return pow(int, e, -n)
```

Because of this, the totient is computed as **φ(n) = (p + 1)·(q + 1)** (instead of the usual (p - 1)·(q - 1)).
With the public modulus n and the negative prime p provided, we compute q by dividing n by p. Then, using a custom implementation of the extended Euclidean algorithm, we obtain the private exponent d as the modular inverse of e modulo φ(n).

## solve.py

```py
import math

e = 65537
n = 3429719
c = [-53102, -3390264, -2864697, -3111409, -2002688, -2864697, -1695722, -1957072, -1821648, -1268305, -3362005, -712024, -1957072, -1821648, -1268305, -732380, -2002688, -967579, -271768, -3390264, -712024, -1821648, -3069724, -732380, -892709, -271768, -732380, -2062187, -271768, -292609, -1599740, -732380, -1268305, -712024, -271768, -1957072, -1821648, -3418677, -732380, -2002688, -1821648, -3069724, -271768, -3390264, -1847282, -2267004, -3362005, -1764589, -293906, -1607693]
p = -811

def extendedEuclidean(e, phi_n):
    A1, A2, A3 = 1, 0, phi_n
    B1, B2, B3 = 0, 1, e

    while (True):
        if B3 == 0:
            return -1
            # indicates no inverse!
        if B3 == 1:
            return B2
            # B2: modular inverse

        Q = math.floor(A3 / B3)
        T1, T2, T3 = A1 - (Q * B1), A2 - (Q * B2), A3 - (Q * B3)
        A1, A2, A3 = B1, B2, B3
        B1, B2, B3 = T1, T2, T3

q = n // p
phi_n = (p + 1) * (q + 1)
d = extendedEuclidean(e, phi_n)

if d < 0:
    d = d % phi_n

flag = ""
for ct in c:
    pt = pow(ct, d, n)
    flag += chr(pt)

print(flag)
```
