# Conversation

This challenge is an RSA-like cryptosystem built on a cubic Pell curve. Lain shares a "secret" obtained by scalar-multiplying a point that encodes a 32-byte string, and asks us to echo it back. Recovering it requires factoring two related moduli and inverting the scalar multiplication.

We are given two files: [chall.py](./given-files/chall.py) (the protocol) and [fancy.py](./given-files/fancy.py) (just pretty printing, no crypto).

## What the server sends

After some flavor text Lain prints a base64 blob:

```
DATA = b64( {N_hat, e_hat=65537, N, e, a, C} )
```

The construction in `chall.py` is:

* $N = pq$ with $p$ and $q$ two 256-bit primes with $p, q \equiv 1 \pmod 3$ and $p, q \not\equiv 1 \pmod 9$.
* $a = r^3 \bmod N$ for random $r$, so $a$ is a cube modulo each prime factor.
* $\widehat{N} = \widehat{p}\widehat{q}$ where $\widehat{p} = \texttt{nextprime}((p \gg 141) \ll 141)$ and similarly for $\widehat{q}$. So $\widehat{p}$ is a prime built from the **top 115 bits** of $p$, with 141 zero low bits up to a tiny "next-prime" gap.
* `secret` is 32 random lowercase letters.
* $m = \texttt{secret}^{65537} \bmod \widehat{N}$ (plain RSA against $\widehat{N}$).
* A "point" $P = (m, v, 0)$. The third coord matters, we'll come back to it.
* $d$ random in $[0, 2^{311}[$ with $\gcd(d, ((p-1)(q-1))^2) = 1$.
* $e = d^{-1} \bmod ((p-1)(q-1))^2$.
* $C = e \otimes P$ using a custom group law:

```
(x1,y1,z1) ^ (x2,y2,z2) = ( x1*x2 + a(y2*z1 + y1*z2),
                            x2*y1 + x1*y2 + a*z1*z2,
                            y1*y2 + x2*z1 + x1*z2 )
```

This is the **cubic Pell curve** (Hessian / cubic-norm form):

$$x^3 + a y^3 + a^2 z^3 - 3 a x y z = 1.$$

When $a$ is a cube mod a prime $p$, the curve splits into a product of two copies of $\mathbb{F}_p^*$, so the group order over $\mathbb{Z}/N$ is $((p-1)(q-1))^2$. That's exactly the modulus used to derive $e$, so the natural attack is: find the group order, invert $e$, undo the scalar mult, recover $m$, then RSA-decrypt mod $\widehat{N}$.

## Step 1: factor $\widehat{N}$ (Coppersmith, known low bits)

$\widehat{p} = \texttt{nextprime}(K \cdot 2^{141})$ means $\widehat{p} \bmod 2^{141}$ is just the next-prime gap $g_p$, which is tiny (under $2^{16}$). That gives **141 known low bits** of $\widehat{p}$, comfortably above the $\widehat{N}^{1/4} \approx 2^{128}$ threshold for univariate Coppersmith.

For each candidate $g \in [1, 2^{16}[$ we run

$$f(x) = x + g \cdot (2^{141})^{-1} \pmod{\widehat{N}}$$

and call `small_roots(X = 2^115, beta = 0.49)`.

The unique $g$ for which a root exists yields $K$, hence $\widehat{p} = K \cdot 2^{141} + g$.

## Step 2: factor $N$ (the actual challenge)

Once we have $\widehat{p}$ we know the **top 115 bits** of $p$ exactly. The natural attempt is the same trick as above: standard high-bits Coppersmith on $N$.

But the bound says no. Univariate Coppersmith with known high bits requires the unknown low part to be smaller than $N^{1/4} = 2^{128}$, and our unknown is $2^{141}$, about 13 bits too large. The challenge author even left a hint in the source:

```py
# should be coppersmith safe... mostly?
hint_size = 115
```

Bridging those 13 bits by brute force is roughly $2^{18}$ Coppersmith runs (~19 CPU*days serial). That works but it's way too long for a CTF.

### Looking for the right paper

We have a very specific shape. An RSA modulus where the top 115 bits of both $p$ and $q$ are known, the public exponent $e$ is huge (close to $N^2$ since $d < 2^{311} \ll \psi(N) \approx N^2$), and the cryptosystem lives on a cubic Pell curve. That's narrow enough that someone has probably written the paper already.

My teammate **:chakouto:** found this paper: [eprint 2026/519](https://eprint.iacr.org/2026/519) *A Generalized Partial Exposure Lattice Attack Against an RSA variant Based on Cubic Pell Curves*. The paper is basically tailor-made for this challenge. Same curve ("cubic Pell equation $\mathcal{P}_c(N): u^3 + cv^3 + c^2w^3 - 3cuvw = 1$"), same key equation:

$$e u_0 - (p-1)^2 (q-1)^2 v_0 = w_0$$

studied "when some bits of $p$ or $q$ are known", which is exactly our situation. The authors also ship a [Sage PoC on GitHub](https://github.com/mseckept/partial-prime-exposure-attack25). Couldn't ask for more.

### The attack in our setting

The attack target is the *private exponent* equation. Since $e d \equiv 1 \pmod{\psi(N)}$ with $\psi(N) = (p-1)^2(q-1)^2$, there exists an integer $k$ with

$$ed - k\,\psi(N) = 1.$$

Write $p + q = (p_0 + q_0) + y$ where $p_0$ is our approximation of $p$, $q_0 = \lfloor N/p_0 \rfloor$, and $y = (p+q) - (p_0+q_0)$ is small. Then

$$\psi(N) = ((p+q) - (N+1))^2 = y^2 + Ay + B$$

with

$$A = 2(p_0+q_0) - 2(N+1), \quad B = (p_0+q_0)^2 - 2(N+1)(p_0+q_0) + (N+1)^2.$$

Plug into the key equation and reduce mod $e$:

$$f(v, y) = v(y^2 + Ay + B) + 1 \equiv 0 \pmod{e}$$

with small roots $v_0 = k$ and $y_0 = (p+q) - p_0 - q_0$. This is *Kunihiro's* bivariate modular polynomial form $u \cdot H(v) + c \equiv 0$, for which there's a tailored lattice construction (Theorem 1 of the paper). Substituting $z = vy^2 + 1$ to absorb the leading term we get $z + v \cdot h(y) \equiv 0 \pmod e$ with $h(y) = Ay + B$, then build shift polynomials

$$g_{a,b,k}(v, y, z) = v^a y^b (z + v h(y))^k \cdot e^{m-k}$$

over the index sets $\mathcal{E} = \{[k-a, b, a] : 0 \le a \le k \le m,\, 0 \le b < 2\}$ and $\mathcal{F} = \{[0, b, k] : 0 \le k \le m,\, 2 \le b < 2 + \lfloor \tau k \rfloor\}$. Scale $(v, y, z) \mapsto (vV, yY, zZ)$ with $Z = VY^2 + 1$, run LLL, and recover algebraically-independent polynomials. Groebner over $\mathbb{Q}$ extracts $y_0$.

### Bound check

Theorem 4 of the paper says this works in polynomial time when

$$\delta < 2 - \frac{\alpha}{3} - \frac{5\gamma}{2} - 6\varepsilon \quad \text{if} \quad 0 < \gamma < \frac{2\alpha}{9} - \varepsilon$$

with $e = N^\alpha$, $d < N^\delta$, $|p - p_0| < N^\gamma$, $\varepsilon = \log 2 / \log N$.

For our instance:

* $N$ is 512 bits, so $\varepsilon \approx 1/512$.
* $e = d^{-1} \bmod \psi(N)$, $\psi(N) \approx N^2$, so $\alpha \approx 2$.
* $d < 2^{311}$, so $\delta < 311/512 \approx 0.607$.
* $p_0$ is $\widehat{p}$ with low 141 bits zeroed, so $|p - p_0| < 2^{141}$ and $\gamma \approx 141/512 \approx 0.276$.

Check: $\gamma \approx 0.276 < 2\alpha/9 \approx 0.444$, so we're in the first regime. The bound becomes

$$\delta < 2 - \tfrac{2}{3} - \tfrac{5 \cdot 0.276}{2} - 6\varepsilon \approx 0.631$$

and indeed $0.607 < 0.631$. Tight but it holds.

### Recovering p and q

Once $y_0$ is out, $p + q = y_0 + p_0 + q_0$ and $pq = N$. Two equations, quadratic in $p$:

$$p, q = \frac{S \pm \sqrt{S^2 - 4N}}{2}, \quad S = y_0 + p_0 + q_0.$$

With $m = 2, \tau = 1$ the lattice is $15$-dimensional and finishes LLL + Groebner in seconds. Catch: sort the shifts (`invlex` order) before building $L$. At $m=2$ the lattice is tight enough that row order decides whether LLL finds useful short vectors. At $m=3$ there's enough slack you can skip it.

## Step 3: invert the scalar multiplication

With $p, q$ in hand the group order is $((p-1)(q-1))^2$. Compute $d = e^{-1} \bmod ((p-1)(q-1))^2$ (we just recover the exponent the server already chose) and run $d \otimes C$ on the cubic Pell curve. The first coordinate of the result is $m$.

## Step 4: RSA decrypt mod $\widehat{N}$

We already have $\widehat{p}, \widehat{q}$ from step 1, so:

$$\widehat{d} = 65537^{-1} \bmod (\widehat{p}-1)(\widehat{q}-1), \qquad \texttt{secret} = m^{\widehat{d}} \bmod \widehat{N}.$$

Decode 32 bytes, send back, get the flag.

## solve.sage

You can find my complete solver [here](./solve.sage).

```sh
❯ sage solve.sage
[+] Opening connection to chall.polygl0ts.ch on port 6931: Done
[*] Switching to interactive mode

lain do you feel connected?

You ikwtkzyjeterebvwoofjqlixrlrvkpmy
lain that was pretty cool... heres another secret! b'EPFL{i7_will_b3_0ur_0wn_li77l3_s3cr37_f66908d81da2cfe3f4da9e61cd66d124}'
[*] Got EOF while reading in interactive
$
```
