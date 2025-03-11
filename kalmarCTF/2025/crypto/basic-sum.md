# basic-sum

The challenge allows us connect to a remote server running this code:

```py
with open("flag.txt", "rb") as f:
    flag = f.read()

# I found this super cool function on stack overflow \o/ https://stackoverflow.com/questions/2267362/how-to-convert-an-integer-to-a-string-in-any-base
def numberToBase(n, b):
    if n == 0:
        return [0]
    digits = []
    while n:
        digits.append(int(n % b))
        n //= b
    return digits[::-1]

assert len(flag) <= 45

flag = int.from_bytes(flag, 'big')

base = int(input("Give me a base! "))

if base < 2:
    print("Base is too small")
    quit()
if base > 256:
    print("Base is too big")
    quit()

print(f'Here you go! {sum(numberToBase(flag, base))}')
```

We see that we can get the sum of the digits of the flag in any base between 2 and 256.

I first dumped all sums in every base to avoid overloading the remote server. We can do this with this simple script:

```py
from pwn import remote
import json

dump = {}

for base in range(2, 257):
    try:
        with remote('basic-sums.chal-kalmarc.tf', 2256) as r:
            r.recv(1024) 
            r.sendline(str(base).encode())
            res = r.recvline().decode().strip()
            sum_val = res.split('! ')[1]
            dump[str(base)] = int(sum_val)
            print(f"Base {base}: Sum {sum_val}")
    except Exception as e:
        print(f"Error with base {base}: {e}")
        exit(1)

with open("dump.txt", "w") as f:
    json.dump(dump, f, indent=4)
```

The key insight comes from a property of digit sums in number systems. For any number represented in base b, the following property holds:

If we represent a number N in base b as:

$N = d₀×bⁿ + d₁×bⁿ⁻¹ + ... + dₙ₋₁×b¹ + dₙ×b⁰$

Then:

$N ≡ (d₀ + d₁ + ... + dₙ₋₁ + dₙ)$ % $(b-1)$

This happens because:

$bᵏ ≡ 1$ % $(b-1)$ for any $k ≥ 0$

So each term $dᵢ×bᵏ ≡ dᵢ×1 ≡ dᵢ$ % $(b-1)$

This means that N is congruent to the sum of its digits modulo b-1.

In our case, this means the flag is congruent to the sum of digits modulo b-1:

- $flag ≡ sum₂$ % 1
- $flag ≡ sum₃$ % 2
- $flag ≡ sum₄$ % 3
- ...
- flag ≡ sum₂₅₆ (mod 255)


We can then solve this system using the [Chinese Remainder Theorem](https://en.wikipedia.org/wiki/Chinese_remainder_theorem).

## solve.py:

```py
import json
from sympy.ntheory.modular import crt

with open("dump.txt", "r") as f:
    data = json.load(f)

moduli = []
remainders = []
for b_str, s in data.items():
    b = int(b_str)
    if not (2 <= b <= 256):
        continue
    mod = b - 1
    rem = s % mod
    moduli.append(mod)
    remainders.append(rem)

solution, mod_product = crt(moduli, remainders)
if solution is None:
    raise ValueError("No solution found for the given congruences.")

nbytes = (solution.bit_length() + 7) // 8
flag = solution.to_bytes(nbytes, "big").decode()

print(flag)
```
