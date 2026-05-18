#! /usr/bin/env -S python3 -u

from Crypto.Util.number import getPrime
from random import randrange, choices
from sympy import nextprime, gcd
from sympy.ntheory.modular import crt
import json, base64

# run with this line commented to build a local solve, but remember to turn it back on for the server
from fancy import *

try:
    from secret import flag
except:
    flag = b"meowwwww"

print("You", "whats up!")


def _point_add(P1, P2, a_val, N):
    x1, y1, z1 = P1
    x2, y2, z2 = P2
    X = (x1 * x2 + a_val * (y2 * z1 + y1 * z2)) % N
    Y = (x2 * y1 + x1 * y2 + a_val * z1 * z2) % N
    Z = (y1 * y2 + x2 * z1 + x1 * z2) % N
    return (X, Y, Z)


def _scalar_mult(k, P, a_val, N):
    res = (1, 0, 0)
    base = P
    while k > 0:
        if k % 2 == 1:
            res = _point_add(res, base, a_val, N)
        base = _point_add(base, base, a_val, N)
        k //= 2
    return res


print("lain", "oh!")
print(
    "lain", "i havent had a conversation in a while, i wonder what people usually say."
)
print("lain", "i know i know!! we can share a secret!")
print("lain", "all cool people know each others secrets right?")

while True:
    p, q = getPrime(256), getPrime(256)
    if p % 3 == 1 and p % 9 != 1 and q % 3 == 1 and q % 9 != 1:
        break

N = p * q
a = pow(randrange(N), 3, N)

# should be coppersmith safe... mostly?
hint_size = 115

p_hint = p.bit_length() - hint_size
q_hint = q.bit_length() - hint_size

p_hat = nextprime((p >> p_hint) << p_hint)
q_hat = nextprime((q >> q_hint) << q_hint)
N_hat = p_hat * q_hat
e_hat = 65537

while True:
    secret = "".join(choices(list("abcdefghijklmnopqrstuvwxyz"), k=32)).encode()
    m = int.from_bytes(secret, "big")
    m = pow(m, e_hat, N_hat)
    val = ((1 - pow(m, 3, N)) * pow(a, -1, N)) % N

    if pow(val, (p - 1) // 3, p) == 1 and pow(val, (q - 1) // 3, q) == 1:
        v_p = pow(val, pow(3, -1, (p - 1) // 3), p)
        v_q = pow(val, pow(3, -1, (q - 1) // 3), q)
        crt_sol = crt([v_p, v_q], [p, q])
        if crt_sol is None:
            continue
        v, _ = crt_sol
        break

P = (m, v, 0)

# weiner safe i think
while True:
    d = randrange(2 << 310)
    if gcd(d, (p - 1) ** 2 * (q - 1) ** 2) == 1:
        break

e = pow(d, -1, (p - 1) ** 2 * (q - 1) ** 2)

C = _scalar_mult(e, P, a, N)

# did my best to make the data as unpainful as possible, sorry
params = base64.b64encode(
    json.dumps({"N_hat": N_hat, "e_hat": e_hat, "N": N, "e": e, "a": a, "C": list(C)}).encode()
).decode()
print("lain", f"lets connect!\nDATA:{params}!")
print("lain", "do you feel connected?\n")


attempt = input()
print("You", attempt)

if attempt.encode() == secret:
    print("lain", f"that was pretty cool... heres another secret! {flag}")
else:
    print("lain", f"that wasnt very cool... i wanted to share {secret}...")
    print("lain", "maybe next time then")
