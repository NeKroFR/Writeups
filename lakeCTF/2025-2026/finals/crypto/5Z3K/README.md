# 5Z3K

This is an interactive MPC in the Head ZKP system from the recent [ZK-for-Z2K paper, eprint 2023/1057](https://eprint.iacr.org/2023/1057.pdf) (Braun, Delpech de Saint Guilhem, Jadoul, Orsini, Smart, Tanguy). The prover claims to know an AES-128 key that maps the all-zero plaintext to the all-zero ciphertext (mod $2^{32}$, so the relation is actually false). We need to convince the verifier to get the flag.

We are given the full reference implementation under [dist/5z3k-dist](./dist/5z3k-dist/): [verifier.py](./dist/5z3k-dist/verifier.py), [party.py](./dist/5z3k-dist/party.py), [sharing.py](./dist/5z3k-dist/sharing.py), [galois_ring.py](./dist/5z3k-dist/galois_ring.py), [circuit.py](./dist/5z3k-dist/circuit.py), [params.py](./dist/5z3k-dist/params.py), and the Bristol-fashion AES circuit.

The bug is an honest-to-god soundness flaw in the compressed multiplication check (3.3 of the paper): the implementation never links round $j$'s $c$-hints to round $j-1$'s $z$, which severs the protocol's only invariant. A cheating prover can run an *honest* compression on a *forged* extended witness.

## Parameters

[params.py](./dist/5z3k-dist/params.py) instantiates Table 3 of the paper:

```python
K = 32; N = 63; T = 1; S_RC = 17
Input   = GR(Z_{2^{49}}, 6, ...)    # 49 = K + S_RC
Witness = GR(Z_{2^{32}}, 6, ...)
Check   = GR(Witness,    4, ...)    # degree d0*d1 = 24 Galois ring
NU = 4; TAU_IN = 1; TAU_OUT = 7
```

The circuit is AES-128 (6400 ANDs, padded with dummy multiplications to $4^7 = 16384$ to match $\nu = 4$, $\log_\nu m = 7$). Inputs are 128 key bits + 128 plaintext bits, outputs are 128 ciphertext bits with the second 128 plaintext input wires appended to `circuit.outputs` so the zero-check covers them too.

## What the verifier does

For each of $\tau_\text{out} = 7$ repetitions, [verifier.py](./dist/5z3k-dist/verifier.py):

1. asks for $N = 63$ commitments to per-party input hints, releases the `ring_check` randomness, reads back the claimed value $v_\text{RC}$.
2. asks for $N$ commitments to per-party extended-witness hints (one $\mathbb{Z}_{2^{32}}$ per multiplication gate).
3. runs $\tau_\text{in} = 1$ rounds of `commit_mulcheck`, which is 1 compression seed and then 7 rounds of (commitments, fresh seed), and finally reads the claimed reconstruction $x_{\log_\nu m}$ at the bottom of the compression tree.
4. asks for one global opening commitment, then samples $T = 1$ party index, reads that party's view, and re-runs the party's protocol locally checking every per-round commitment + reconstructed share against the open claims.

To win we have to make every commitment, every opened claim, and the final opening-commitment line up, with $T = 1$ random party-opening as the only "honesty" check.

## The flaw: $\Pi_\text{Comp-Check}$ doesn't link rounds

In the figure 5 of the paper (The compressed multiplication check), round $j$ of the compression check parses the previous round's tuple $(\!|\boldsymbol{x}^{j-1}|\!), (\!|\boldsymbol{y}^{j-1}|\!), (\!|z^{j-1}|\!)$ and obtains, via $\mathcal{O}_\mathcal{H}$, hints $(\!|c_i^j|\!)$ with $c_i^j = \langle \boldsymbol{a}_i^j, \boldsymbol{b}_i^j\rangle$. These hints are fed to $\Pi_\text{Compress}$ as the $z_i$ slots. The whole point of having $\mathcal{O}_\mathcal{H}$ inject these is so that the verifier later notices if any $c_i \ne \langle \boldsymbol{a}_i, \boldsymbol{b}_i\rangle$ via the polynomial check $h \equiv \langle\boldsymbol{f}, \boldsymbol{g}\rangle$ in $\Pi_\text{Compress}$. The *invariant* that ties rounds together is

$$z^{j-1} \;=\; \sum_{i=1}^{\nu} c_i^{j},$$

because $\boldsymbol{x}^{j-1} = \boldsymbol{a}_1 \| \cdots \| \boldsymbol{a}_\nu$, $\boldsymbol{y}^{j-1} = \boldsymbol{b}_1 \| \cdots \| \boldsymbol{b}_\nu$, so $z^{j-1} = \langle \boldsymbol{x}^{j-1}, \boldsymbol{y}^{j-1}\rangle = \sum_i \langle \boldsymbol{a}_i, \boldsymbol{b}_i\rangle = \sum_i c_i$. Without this link, the chain of (in)correctness from Lemma 3.1 ("If one of the inner product tuples … is incorrect, …, then the output inner tuple is also incorrect") fires only locally inside one $\Pi_\text{Compress}$ call. Across rounds, the prover gets to *reset* the constraint.

Now look at `party.mul_check` in [party.py](./dist/5z3k-dist/party.py):

```python
def mul_check(self, seeds):
    mults = [(Check([a]), Check([b]), Check([c])) for (a, b, c) in self.mults]
    eta_rng = Rng(seeds[0])
    eta = [Check.sample(eta_rng) for _ in mults]
    x = list(map(gmul, eta, [x for x, _, _ in mults]))
    y = [y for _, y, _ in mults]
    z = gsum(map(gmul, eta, [z for _, _, z in mults]))   # (*)
    round = 1
    while len(x) > 1:
        ...
        c = [self.get_hint(Check) for _ in range(NU)]
        x, y, z = self.compress(a, b, c, length == 1, Check.sample(Rng(seeds[round])))
        round += 1
```

The line marked `(*)` is the entire connection of `mul_check` to the actual multiplication triples $(a_i, b_i, c_i)$ coming from the circuit evaluation: $z^0 := \langle \boldsymbol{\eta}, \boldsymbol{z}\rangle$ is Lemma 3.2's compressed scalar. It is computed, and then immediately *thrown away* — the next line shadows `z` with the return value of `compress(..., c, ...)`, where inside `compress` the `z` parameter is the freshly-read $c$-hints, not the previous $z^0$. The c-hints `c = [self.get_hint(Check) for _ in range(NU)]` are committed to `commit_buf` but never summed and never compared against the prior $z$. Round-after-round, $z^j$ is just $h^j(\varepsilon^j)$ where $h^j$ is the polynomial *the prover chose* (via the injected $z_i$'s).

As long as the prover picks $h^j \equiv \langle \boldsymbol{f}^j, \boldsymbol{g}^j\rangle$ in every round (which it can do honestly by computing $c_i^j = \langle \boldsymbol{a}_i^j, \boldsymbol{b}_i^j\rangle$ and the injected $z_i$'s as $\langle \boldsymbol{f}^j(\alpha_i), \boldsymbol{g}^j(\alpha_i)\rangle$), then $z^j = \langle \boldsymbol{x}^j, \boldsymbol{y}^j\rangle$ holds at every level *regardless* of the original $(a_i, b_i, c_i)$ triples. The final $\Pi_\text{Zero-Check}(x_{\log_\nu m} \cdot y_{\log_\nu m} - z_{\log_\nu m})$ passes by construction. The multiplication gates of the circuit are no longer checked.

## What's left for the verifier?

Just the linear part. With every MUL gate unconstrained, the prover gets to pick a free value $c_g \in \mathbb{Z}_{2^{32}}$ for each multiplication gate $g$, and the rest of the circuit is affine: ADD = sum, INV = $1 - x$. The 128 ciphertext output wires become *affine functions* of the $c$'s once we also force all 256 inputs to zero. Let

$$\text{out}_o(c) \;=\; \sum_{g} M_{o,g}\, c_g + b_o \;\;\pmod{2^{32}}, \qquad o \in [0, 128),$$

with $M \in \mathbb{Z}_{2^{32}}^{128 \times 16384}$ and $b \in \mathbb{Z}_{2^{32}}^{128}$. We want all 128 outputs zero, i.e. $M c + b \equiv 0 \pmod{2^{32}}$. 128 equations in 16384 unknowns mod a power of 2.

### Building M, b

[`affine_outputs`](./solve.py) does a symbolic pass over the circuit with all inputs set to zero. Each wire carries `(dict {mult_idx: coeff}, const)`. A MUL gate $g$ produces $(\{g_\text{idx}: 1\}, 0)$ (a fresh free variable), and ADD/INV combine affine forms in the obvious way. A reference-counted free-list keeps memory bounded, and the symbolic pass over the full 46647-gate AES runs in a few seconds. With all inputs = 0, the affine forms for the 128 extra `outputs` in $[128, 256)$ (the plaintext-input wires) come out trivially `({}, 0)`, which is a handy sanity check.

### Solving $M c + b \equiv 0 \pmod{2^{32}}$ by Hensel lifting

A standard 2-adic lift. Solve mod 2 to find $c_0 \in \mathbb{F}_2^{16384}$, then lift bit by bit. At bit $k$, the residual $r := M c + b \pmod{2^{k+1}}$ has a known bit-$k$ pattern, and we need a $\delta \in \mathbb{F}_2^{16384}$ with $M \delta \equiv (r \gg k) \pmod 2$. The GF(2) row-reduction of $M$ is the same every iteration, so we do it once (with an augmented identity to record the transform), then for each of the 32 bits we apply the recorded transform to the bit-$k$ RHS and back-substitute. That's 32 GF(2) back-solves on a once-reduced $128 \times 16384$ matrix.

The system is wildly underdetermined (16384 unknowns, 128 equations) and consistent for our $b$, so a solution always exists.

## The cheating proof, end to end

Phase 1 gives us 16384 forged `extwit` values, one $c_g \in \mathbb{Z}_{2^{32}}$ per MUL gate, such that the symbolic circuit (with inputs = 0, $c_g$ replacing each MUL output) produces all-zero ciphertext outputs. Now we need to produce a transcript Lain will accept. The challenge author hints at the simplification we use: *"you can simplify and speed things up a tiny bit by making all parties just have a trivial sharing (the underlying value itself)"*. We let all $N = 63$ parties have the same view, so every share is a degree-0 polynomial equal to the secret. That removes any Shamir-interpolation gymnastics.

* every per-party input/extwit commitment is the same hex, so `[h] * N`.
* `party.openings[i] == open_claims[i]` for every $i$, so `check_openings`'s reconstructed shares are just $[c, c, \dots, c]$ at every evaluation point, and `commitment([c]*(N+1))` matches whatever opening commitment we send.
* it doesn't matter which party index $T = 1$ picks, they all reveal the same view.

The transcript we send per `verify()` iteration:

1. **Inputs.** view contains 256 `Input([0])` hints + one zero ring-check mask. The first round commitment is $\text{SHA256}([c_\text{ctx}, \mathtt{Input}([0])^{256}, \mathtt{Input}([0])])$.
2. **Ring check.** All inputs and mask are zero, so $v_\text{RC} = 0$ regardless of which random combiners Lain samples. We send `0`. `party.ring_check` calls `self.open(0)`, which under the hood appends `Input([0])` (the opened claim we provided) to the running `commit_buf`. **Easy to miss:** the extwit commitment that comes next must therefore include this `Input([0])` between the previous commit and the witness values. The verifier will compute $\text{SHA256}([c_\text{input}, \mathtt{Input}([0]), \mathtt{Witness}([c_0]), \mathtt{Witness}([c_1]), \dots])$ and our matching commitment must be identical.
3. **Extended witness.** $16384$ `Witness([c_g])` for our forged $c$.
4. **Output opens.** The 256 calls to `self.open(wires[o])` between the extwit assert and `mul_check` pour 256 `Witness.zero()` into `commit_buf`. Round 0 of `mul_check` commits over all of those + that round's c-hints and z-extras. We need to prepend them in our `round_0_comm` calculation, or Lain refuses.
5. **Mul check, rounds 0 through 5 (non-`rand`).** Each round we send a commitment over $4$ zero c-hints and $3$ zero $z$-extras. The values don't matter — the prover discards $z$ anyway, and the next round's $\boldsymbol{f}^j(\alpha_i) \cdot \boldsymbol{g}^j(\alpha_i)$ interpolation drives everything off $\boldsymbol{x}^j, \boldsymbol{y}^j$, which we recompute from the prior round's Lagrange interpolation at $\varepsilon$ honestly.
6. **Mul check, round 6 (`rand = ⊤`).** This is the *only* round where $h$'s coefficients have to be the right polynomial: we set $v = w = 0$, $c_i = a_i \cdot b_i$ (correct inner products at $\alpha_1 \dots \alpha_4$), and the 5 $z$-extras as $h(\alpha_k) = f(\alpha_k) \cdot g(\alpha_k)$ for $k \in \{4, 5, 6, 7, 8\}$. After Lain's $\varepsilon^{(6)}$ challenge, the reconstruction claim $x_{\log_\nu m} = f(\varepsilon)$ matches $z_{\log_\nu m} = f(\varepsilon) \cdot g(\varepsilon)$ to within `rec * y[0] - z = 0`, so the implicit final `open(rec * y[0] - z)` reveals `Check.zero()` and `check_openings` is happy.
7. **Global opening commitment.** With trivial sharing, `all_shares = [c0] * (N+1) + [c1] * (N+1) + ... + [c_last] * (N+1)`, hashed with SHA256.
8. **Open party.** Send our view (identical for every party index).

Every $\Pi_\text{Comp-Check}$ assertion holds within a single round because we run an *honest* compression, so Lemma 3.1's chain-of-incorrectness has nothing to propagate locally. The missing inter-round link (the invariant $z^{j-1} = \sum_i c_i^j$ that would have let Lemma 3.1 chain across rounds) is exactly what lets the underlying claim, "I know an AES-128 key sending zero to zero mod $2^{32}$", be false.

## solve.py

[solve.py](./solve.py) does both phases. It also dispatches the redpwn proof of work the remote requires.

```sh
❯ time python solve.py
[+] Opening connection to chall.polygl0ts.ch on port 6563: Done
Solving PoW: s.AACvyA==.YJb9E5ZVCLq89E9eu9u5NQ==
PoW solution: s.SCttm5xJ6HkWjT2bhfElABD0N85brUZBGB3C0kTlmE3fUiPAVrT/q+7s3QwfMGyCtM3Wf8jIB4dCUtKo90yRLTQlL7bFrFk/kHsV5BY4iHgNqEeX5fs0yoZmlRGAQsGZ/ZbS7D2d1mXIOxxWOzJeekfBKBDD3DI6Hf1R4WPT3zM4xhGmm+Ok1tQNWs8rJwkcQZpIh3bUQLyAJNg4ILzpsA==
EPFL{an_eprint_update_is_on_the_way..._eventually}

[*] Closed connection to chall.polygl0ts.ch port 6563
python3 solve.py  284.41s user 0.71s system 89% cpu 5:20.02 total
```
