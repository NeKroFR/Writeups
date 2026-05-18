# mac-n-cheese

This challenge is a Classic McEliece KEM (`n=3488, t=64, m=12`) wrapping the flag in AES ECB. The public key is a parity-check matrix $H_\text{pub}$, and the ciphertext is the syndrome $H_\text{pub} \cdot e$ for a random weight `t` and error `e`. We get $H_\text{pub}$, the syndrome `protocol_7`, the encrypted flag, and two entries of a private "syndrome polynomial" cache that should never have left the server. Recovering the flag means recovering `e`, which means recovering the private Goppa polynomial $g(x)$ and the full support. We have two files to work with: [mac_n_cheese.sage](./given-files/mac_n_cheese.sage) (the cipher) and [wired_transmission.txt](./given-files/wired_transmission.txt) (the transcript).

The transcript ships two leaks and the cipher has a missing `shuffle`. Together they put us in the known-`g` partial-exposure regime of Kirshanova–May ([eprint 2022/525](https://eprint.iacr.org/2022/525), *"Breaking Goppa-Based McEliece with Hints"*), which is solvable in polynomial time.

## What the cipher does

The AES key is `SHAKE256(b'\x01' || e || protocol_7)[:16]`, so to get the flag we need to recover `e` bit-for-bit. The classical route is Patterson decoding (see §2.3 of [Engelbert–Overbeck–Schmidt](https://eprint.iacr.org/2006/162), *"A Summary of McEliece-Type Cryptosystems and their Security"*), which needs $g(x)$ and the full support $(\alpha_0, \dots, \alpha_{n-1})$.

One bug is in `Code.__init__`:

```python
field_elems = list(self.F)
start_support = field_elems[:n - (t * (m - 2) - 1)]
end_support = field_elems[n - (t * (m - 2) - 1):n]
shuffle(start_support)
# shuffle(end_support)
self.support = start_support + end_support
```

`shuffle(end_support)` is commented out, so the last $t(m-2) - 1 = 639$ entries of `support` are just `list(GF(2^12))[2849:3488]` in field order. That's 639 support points we know for free.

The other is in the transcript writer:

```python
# memory fragments lain scattered across the nodes, only two were recovered
f.write(str(cipher.code.syndrome_poly_elems[1337]).encode())
f.write(SPLIT_STRING)
f.write(str(cipher.code.syndrome_poly_elems[1420]).encode())
```

`wired_transmission.txt` is `SPLIT_STRING`-delimited and contains, in order: $H_\text{pub}$, the encrypted flag, `protocol_7`, $s_{1337}$, $s_{1420}$. The last two are the leak: `syndrome_poly_elems[i]` is $(x - \alpha_i)^{-1} \bmod g(x)$, so leaking two of them is enough to recover $g$ and the two corresponding support points $\alpha_{1337}, \alpha_{1420}$.

Together that's $639 + 2 = 641$ known support points, which is the threshold the known-`g` variant of the paper needs to start.

## Recovering $g(x)$ and two support points

```python
    def prepare_syndrome_poly(self):
        # Computing all possible syndromes to speed up key encapsulation
        elems = []
        for i, gamma in enumerate(self.support):
            denom = self.X - gamma
            _, _, inv = self.goppa_poly.xgcd(denom)
            inv = inv % self.goppa_poly
            elems.append(inv)
        return elems
```

Each leak $s_i(x) = (x - \alpha_i)^{-1} \bmod g(x)$ satisfies $g(x) \mid (x - \alpha_i) s_i(x) - 1$. We don't know $\alpha_{1337}$, but it lives in `GF(2^12)` (only 4096 elements), so we can just try every candidate. For each $\alpha$, the polynomial `((x - α) * s1337 - 1) / lc` is monic of degree at most 64. For the right $\alpha$ it equals $g(x)$, irreducible of degree 64. A wrong $\alpha$ also produces a degree-64 irreducible polynomial roughly 1/64 of the time, so we cross-check survivors against the second leak: the real $g$ must divide $(x - \alpha') \cdot s_{1420}(x) - 1$ for some $\alpha'$ in `GF(2^12)`. Exactly one $(g, \alpha_{1337}, \alpha_{1420})$ triple passes both tests.

So now we have $g$, $\alpha_{1337}$, $\alpha_{1420}$, and the 639 sequential tail entries. The starting set is $I_0$ with $|I_0| = 639 + 2 = 641 = t(m-2) + 1$, which is what Algorithm 3.6 of the paper takes as input.

## Extend from 641 to 769 support points (Algorithm 3.6)

The known-`g` algorithm uses set-intersection on low-support codewords:

* Construct $c_1 \in C(L, g)$ with $\mathrm{supp}(c_1) \subseteq I \cup J_1$, $|J_1| \le t+1$.
* Construct $c_2 \in C(L, g)$ sharing one position $i^* \in J_1$ with weight $\le t+1$ outside $I$.
* The Goppa identity makes both codewords yield candidate sets $A_1, A_2 \subset \mathbb F_{2^m}$ for the unknown $\alpha$-values. Their intersection is $\\{\alpha_{i^*}\\}$.

With $|I| = 641$, the algorithm extends $I$ to $tm + 1 = 769$, after which Algorithm 3.3 (`recover_Hpriv_complete`) recovers everything else deterministically.

### The rank twist

Algorithm 3.3 needs $\mathrm{rank}(H_{\text{pub}}[:, I]) = tm = 768$, i.e. an invertible $768 \times 768$ submatrix of the chosen 769 columns. The paper proves this holds with high probability when $I$ is uniformly random. Ours isn't: 639 of its elements are sequential (`field_elems[2849:3488]`). About 75% of straight Algorithm 3.6 runs land at $|I| = 769$ with rank only $766$ or $767$, and Algorithm 3.3 won't budge.

The fix is to make Phase 1 rank-aware: maintain an incremental row-echelon basis of accepted columns, and reject any new candidate $i^*$ whose `H_pub[:, i*]` doesn't extend the current rank, until rank reaches $768$. "Reject" just means try another codeword pair, since the algorithm only adds positions it can recover anyway. Once rank hits $768$, accept one final candidate to bring $|I|$ to $769$.

```python
class RankTracker:
    def __init__(self):
        self.basis = []   # GF(2) row-echelon rows
        self.pivots = []
        self.rank = 0
    def would_extend(self, v):
        for row, p in zip(self.basis, self.pivots):
            if v[p] == 1: v = v + row
        return any(v[i] == 1 for i in range(mt))
    def add(self, v):
        for row, p in zip(self.basis, self.pivots):
            if v[p] == 1: v = v + row
        for i in range(mt):
            if v[i] == 1:
                self.basis.append(v); self.pivots.append(i)
                self.rank += 1
                return

# inside the alg-3.6 loop:
if rt.rank < mt and not rt.would_extend(Hcols[istar]):
    continue                               # not rank-extending; keep searching
```

Each accepted point bumps rank by 1, so rank hits $768$ after $127$ iterations. Even with the rank filter, late-game $i^*$ candidates often fail the codeword construction and a worker can stall. About 3 in 4 runs end up burning their fail counter without ever closing the gap. We just throw 14 workers at it with different RNG seeds and let the first one win. After a few rounds (~15 minutes total) seed `2262004` reached $|I| = 769$ with rank $768$ and dropped the pickle.

`gen_c2` is also biased to try rank-extending $i^*$ candidates first (cheap given the tracker), and we cache $1/(x-\alpha_i) \bmod g^2$ for each known anchor.

## Recover $H_{\text{priv}}$ (Algorithm 3.3)

Given 769 known $(\text{idx}, \alpha)$ pairs with full rank, build the canonical parity check restricted to those columns:

$$\big[H_{\text{priv}}^{(I)}\big]_{mi + r,\, j} = \text{bit}_r\!\left(\frac{\alpha_{I[j]}^{i}}{g(\alpha_{I[j]})}\right) \quad \text{for } i \in [0, t),\ r \in [0, m).$$

Pick a $768 \times 768$ invertible block of $H_{\text{pub}}^{(I)}$ (drop one of the 769 columns) and solve

$$U = H_{\text{priv}}^{(I, \text{block})} \cdot \big(H_{\text{pub}}^{(I, \text{block})}\big)^{-1},$$

then $H_{\text{priv}} = U \cdot H_{\text{pub}}$. This is `recover_Hpriv_complete` from the [reference implementation](https://github.com/ElenaKirshanova/leaky_goppa_in_mceliece).

## Full support by column lookup

Each column of $H_{\text{priv}}$ is the canonical column of one specific field element: column $j$ is `can_col(α)` for some $\alpha$ in `GF(2^12)`, where `can_col(α)` is the $tm$-bit vector built by stacking the bits of $\alpha^i / g(\alpha)$ for $i \in [0, t)$ (same formula as the previous section). Precompute `{can_col(α): α for α in GF(2^12)}`, then look up `H_priv[:, j]` for each $j \in [0, n)$. 4096 hashes, 3488 lookups, done.

## Patterson decode + AES

To decapsulate, `mac_n_cheese.sage` zero-pads the syndrome `protocol_7` into $v = s \,\|\, 0^k$, treats it as a received word, and finds the closest codeword in $C(L, g)$. The Patterson syndrome is

$$S(x) = \sum_{i \in \mathrm{supp}(v)} (x - \alpha_i)^{-1} \pmod{g(x)},$$

and the error locator $\sigma_e$ comes from the EEA on $\sqrt{S^{-1} + x}$ and $g$. The first 768 coordinates of $v$ are `protocol_7`, the rest are zero, so $S(x)$ only sums over $i < mt$ where `s_pub[i] = 1`.

Roots of $\sigma_e$ in `support` give the error positions. Verify that $H_{\text{pub}} \cdot e$ equals `protocol_7`, then

```python
key = shake_256(b'\x01' + int(e).to_bytes(...) + int(C).to_bytes(...)).digest(16)
flag = unpad(AES.new(key, AES.MODE_ECB).decrypt(enc_flag), 16)
```

## solve.sage

The rank-aware Algorithm 3.6 worker is in [phase1.sage](./phase1.sage), one RNG seed per run. Once a worker drops a full-rank pickle, [solve.sage](./solve.sage) does the rest: recover $g$, run Algorithm 3.3, Patterson, decrypt. Most of the heavy linear-algebra helpers in [utils.sage](./utils.sage) are lifted from the [paper's reference impl](https://github.com/ElenaKirshanova/leaky_goppa_in_mceliece). To race 14 workers in parallel, run [solve.sh](./solve.sh).

```sh
# fresh run: ./solve.sh (races 14 phase1 workers, then runs solve.sage)
# below is a replay with the known-winning seed:
❯ time sage phase1.sage 2262004 phase1_result.pkl
sage phase1.sage 2262004 phase1_result.pkl  125.60s user 0.18s system 99% cpu 2:05.83 total
❯ time sage solve.sage
a1337=z^10 + z^8 + z^3 + z^2 + z, a1420=z^8 + z^7 + z^5 + z^4 + z^2 + 1
seed=2262004 |I|=769 rank=768
EPFL{P0intS_pO1NTs_p0iNt5_3verywher3}
sage solve.sage  38.75s user 0.23s system 99% cpu 38.989 total
```
