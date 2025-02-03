# Next Level

This challenge provides us with an RSA-like encryption scheme, but instead of the usual two prime factors, the modulus is the product of **3 consecutive prime numbers**:

```py
from Crypto.Util import number

def nextprime(n):
	p = n
	while True:
		if number.isPrime(p := p+1): return p

p = number.getPrime(512)
q = nextprime(p)
r = nextprime(q)
n = p*q*r
e = 0x10001
flag = int.from_bytes(open('flag.txt','r').read().encode())
c = pow(flag,e,n)
print(n)
print(c)
```

Since the three prime numbers (p, q, r) are consecutive, we can use the [Fermat's factorization method](https://en.wikipedia.org/wiki/Fermat%27s_factorization_method) with an initial estimate close to $ \sqrt[3]{n} $.
Given that the primes are relatively close, we can iterate to find the correct factors efficiently.

## solve.py

```py
from Crypto.Util.number import long_to_bytes
from sympy import nextprime
from gmpy2 import iroot, invert

def fermat_factor(n):
    approx_p = int(iroot(n, 3)[0])  # Estimate p as the cube root of n
    while True:
        if n % approx_p == 0:
            p = approx_p
            q = nextprime(p)
            r = nextprime(q)
            if p * q * r == n:
                return p, q, r
        approx_p -= 1

n = 325378258217467275820423507015467827165514682602728540991457523627701812198269842826079276781544852654502649837609750975919597279415413488886639422208968198891482250819043765146242585644632868956342687066351825944436223046088321133925752199524203624445385991061392907003035330622037093762268517152467139568374165219056106861172136601365420382665970596621060829444276186578039784985066558144658990403643152194206163055145307445753156150710273413764981796280324971
c = 67185454692888016429698943070436732670833796930255592801111175196788532330300404985009673862249188569397734831253642258785985995470104030940772101453046210853501468269635746346615765303296114222385300646129749676034640933562552097264001995658561937633626468288690690107963274297674144801123075456590268872391218152410951381049466179700879317108683244886460628764825911427854025435424801344519194024404351578939445768188062907255668115377725170507692644248448901
e = 0x10001

p, q, r = fermat_factor(n)
print(f"Found factors:\np = {p}\nq = {q}\nr = {r}")

phi = (p-1) * (q-1) * (r-1)
d = invert(e, phi)
m = pow(c, d, n)
flag = long_to_bytes(m)
print(f"Flag: {flag.decode()}")
```