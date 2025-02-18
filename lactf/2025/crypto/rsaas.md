# RSAaaS

In this challenge, we interact with an RSA-as-a-Service that asks for two 64‑bit prime numbers (p and q) and then sets up RSA using the public exponent `e = 65537`.
The idea is that if the provided primes make it impossible to compute the private key, the service triggers an exception and prints the flag:

```py
#!/usr/local/bin/python3

from Crypto.Util.number import isPrime


def RSAaaS():
    try:
        print("Welcome to my RSA as a Service! ")
        print("Pass me two primes and I'll do the rest for you. ")
        print("Let's keep the primes at a 64 bit size, please. ")

        while True:
            p = input("Input p: ")
            q = input("Input q: ")
            try:
                p = int(p)
                q = int(q)
                assert isPrime(p)
                assert isPrime(q)
            except:
                print("Hm, looks like something's wrong with the primes you sent. ")
                print("Please try again. ")
                continue

            try:
                assert p != q
            except:
                print("You should probably make your primes different. ")
                continue

            try:
                assert (p > 2**63) and (p < 2**64)
                assert (q > 2**63) and (q < 2**64)
                break
            except:
                print("Please keep your primes in the requested size range. ")
                print("Please try again. ")
                continue

        n = p * q
        phi = (p - 1) * (q - 1)
        e = 65537
        d = pow(e, -1, phi)

        print("Alright! RSA is all set! ")
        while True:
            print("1. Encrypt 2. Decrypt 3. Exit ")
            choice = input("Pick an option: ")

            if choice == "1":
                msg = input("Input a message (as an int): ")
                try:
                    msg = int(msg)
                except:
                    print("Hm, looks like something's wrong with your message. ")
                    continue
                encrypted = pow(msg, e, n)
                print("Here's your ciphertext! ")
                print(encrypted)

            elif choice == "2":
                ct = input("Input a ciphertext (as an int): ")
                try:
                    ct = int(ct)
                except:
                    print("Hm, looks like something's wrong with your message. ")
                    continue
                decrypted = pow(ct, d, n)
                print("Here's your plaintext! ")
                print(decrypted)

            else:
                print("Thanks for using my service! ")
                print("Buh bye! ")
                break

    except Exception:
        print("Oh no! My service! Please don't give us a bad review! ")
        print("Here, have a complementary flag for your troubles. ")
        with open("flag.txt", "r") as f:
            print(f.read())

RSAaaS()
```

The idea behind our solution is purely mathematical: we choose a prime p such that **p ≡ 1 (mod 65537)**, which ensures that 65537 divides p−1. This makes e and φ(n) share a factor (since φ(n) = (p−1)(q−1)), so the modular inverse for e does not exist. When we then send this specially chosen p (along with any other valid prime q) to the service, the calculation of d fails and the exception handler reveals the flag.

## solve.py

```py
from pwn import remote
from sympy import isprime, randprime
import sys

# We need 64-bit primes, i.e. in the interval (2^63, 2^64)
LOW  = 2**63 + 1
HIGH = 2**64 - 1
E = 65537

# Choose a 64-bit prime p such that p ≡ 1 (mod 65537)
# That is, we want p-1 to be divisible by 65537.
# Write p = 65537*k + 1 and search for a prime in our range.
k = (2**63 - 1) // E + 1  # smallest k such that 65537*k+1 >= 2^63
p = None
while True:
    candidate = E * k + 1
    if candidate > HIGH:
        sys.exit("No candidate found in range!")
    if isprime(candidate):
        p = candidate
        break
    k += 1

# Choose any other 64-bit prime q (ensuring q != p)
q = randprime(LOW, HIGH)
if q == p:
    q = randprime(LOW, HIGH)

print(f"Using p = {p}")
print(f"Using q = {q}")

r = remote("chall.lac.tf", 31176)
r.recvuntil("Input p: ")
r.sendline(str(p))
r.recvuntil("Input q: ")
r.sendline(str(q))

# After p and q are given, the service computes the RSA key.
# Since p-1 is divisible by 65537, the modular inverse in
# d = pow(65537, -1, phi) will fail, causing an exception.
# The outer exception handler then prints the flag.
print(r.recvall())
```
