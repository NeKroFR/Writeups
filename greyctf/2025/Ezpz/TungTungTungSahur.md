# TungTungTungSahur - crypto

The challenge provide us with this python script:
```py
from Crypto.Util.number import getPrime, bytes_to_long

flag = "grey{flag_here}"

e = 3
p, q = getPrime(512), getPrime(512)
N = p * q 
m = bytes_to_long(flag.encode())
C = pow(m,e)

assert C < N 
while (C < N):
    C *= 2
    print("Tung!")

# now C >= N

while (C >= N):
    C -= N 
    print("Sahur!")


print(f"{e = }")
print(f"{N = }")
print(f"{C = }")
```
We can see that the flag is encrypted using RSA with a vulnerable exponent **(e=3)** wich means that `C = m^3`. The little twist is that the ciphertext `C` is multiplyed by 2  until it is bigger than `n` and then they substract n to it. Basically we have `C = (m^3 * 2^k) - N`, whith k the number of `"Thung!"` in the output.

To recover the flag, we just need to recover m^3 and qualculate the cube root.

## solve.py

```py
from Crypto.Util.number import long_to_bytes
import gmpy2

with open('output.txt', 'r') as f:
    lines = f.readlines()

k = 0
for line in lines:
    if line.strip() == "Tung!":
        k += 1
    if line.startswith("e = "):
        e = int(line.split("=")[1].strip())
    elif line.startswith("N = "):
        N = int(line.split("=")[1].strip())
    elif line.startswith("C = "):
        C = int(line.split("=")[1].strip())

m3 = (C + N) // (2 ** k)

m, _ = gmpy2.iroot(m3, 3)
flag = long_to_bytes(int(m)).decode()
print("Flag:", flag)
```
