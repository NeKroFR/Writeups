# Storm

This challenge wraps AES-GCM in a "stormy weather" gimmick: every ciphertext byte and every tag byte gets bitwise-AND-ed with a Mersenne-Twister keystream before being shown to us, so each output looks like noise. Underneath the noise the GCM nonce is a constant string and the same key is reused forever, which is the textbook setup for the *forbidden attack*. The win condition is to predict the GCM tag for `b"give me the flag"` under a status string we don't know.

We are given a single file: [chal.py](./given-files/chal.py).

## What the server does

```python
storm = os.urandom(17)
random.seed(storm)
key = os.urandom(16)

def attempt(key, pt, status):
    c  = AES.new(key, AES.MODE_GCM, nonce=b'{status}')   # literal! not an f-string
    c.update(status)
    ct, t = c.encrypt_and_digest(pt)
    ct = bytes([a & b for a,b in zip(ct, random.getrandbits(len(ct)*8).to_bytes(len(ct),"little"))])
    t  = bytes([a & b for a,b in zip(t,  random.getrandbits(len(t)*8 ).to_bytes(len(t), "little"))])
    return c.nonce.hex(), ct.hex(), t.hex()
```

Two phases:

* **Explore.** As long as the running total of `max(len(pt), 16)` stays below 624, we can call `attempt(key, pt, b"explorarationing")` with any plaintext. The status string here is fixed.
* **Speak.** We get 16 attempts to hand back the (masked) tag the server is about to print. The server runs `attempt(key, b"give me the flag", storm)` and asks for the AND-ed tag. Match it once and we get the flag.

There are three bugs stacked on top of each other.

1. `nonce=b'{status}'` is a *literal* bytestring, not an f-string. The nonce is the constant 8 bytes `{status}` for every single call, regardless of what `status` actually is. Same key + same nonce => GCM forbidden attack.
2. The masking RNG is python's `random` module (CPython's Mersenne Twister), seeded with `storm`. Once we know `storm` we can replay every mask the server will ever produce.
3. Mask-by-AND only ever turns 1-bits into 0-bits. A bit set in the output is *guaranteed* to be set in the underlying ciphertext/tag. OR-ing many outputs of the same underlying value recovers it bit by bit.

## Step 1: peel off the mask (bitwise OR)

For a fixed plaintext `PT` and fixed status, the underlying $(C, T)$ are deterministic (key and nonce are constant). Each call ANDs them with fresh MT bits. Each output bit is 1 with probability $1/2$ when the true bit is 1, and 0 always when the true bit is 0.

$$\bigvee_i C_i = C, \qquad \bigvee_i T_i = T$$

So after enough samples, for example 19 samples. The probability that any given true-1 bit stays unmasked the whole time is $2^{-19}$, and a union bound over $128 \cdot 2$ bits gives a failure probability under $2^{-10}$, which is confortable.

We do this twice in the explore phase, with two distinct 16-byte plaintexts $PT_1 = \texttt{A}^{16}$, $PT_2 = \texttt{B}^{16}$, 19 calls each. That's $19 \cdot 2 \cdot 16 = 608 \le 624$ counter budget, leaving us with clean $(C_1, T_1)$ and $(C_2, T_2)$ for the same key, same nonce, same AAD, same length. Exactly the Joux setup for the forbidden attack.

## Step 2: recover the GHASH key $H$ (forbidden attack)

GCM's authentication tag is

$$T = E_K(J_0) \oplus \mathrm{GHASH}_H(A \,\|\, C \,\|\, L)$$

where $\mathrm{GHASH}$ is a polynomial evaluation in $\mathbb{F}_{2^{128}}$ at the point $H = E_K(0)$:

$$\mathrm{GHASH}_H(X_1, X_2, \dots, X_n) = \sum_{i=1}^{n} X_i \cdot H^{n-i+1}.$$

For our two single-block messages with one AAD block and identical lengths, $A, L$ cancel in $T_1 \oplus T_2$ and so do the $E_K(J_0)$ masks. Only the ciphertext-block term survives:

$$T_1 \oplus T_2 = (C_1 \oplus C_2) \cdot H^2.$$

So $H^2 = (T_1 \oplus T_2)/(C_1 \oplus C_2)$ in $\mathbb{F}_{2^{128}}$, and $H = \sqrt{H^2}$. Squaring is a linear, invertible map in characteristic 2, with $\sqrt{x} = x^{2^{127}}$. This is the Joux *forbidden attack* ([Authentication Failures in NIST version of GCM](https://csrc.nist.gov/csrc/media/projects/block-cipher-techniques/documents/bcm/comments/800-38-series-drafts/gcm/joux_comments.pdf)).

Once $H$ is known we recover the per-(key,nonce) pad $S_0 := E_K(J_0)$ algebraically:

$$S_0 = T_1 \oplus A \cdot H^3 \oplus C_1 \cdot H^2 \oplus L \cdot H.$$

This $S_0$ depends only on key+nonce, both of which are constant across the whole session. It will reappear unchanged in the speak phase.

## Step 3: collect the masked target tag

In the speak phase, every wrong guess prints the masked $(C_\text{flag}, T_\text{flag})$ for $PT = \texttt{"give me the flag"}$ with $\text{AAD} = \text{storm}$. We have 16 attempts. We burn 15 of them on garbage to OR up 15 noisy copies of the real $T_\text{flag}$, keeping the 16th for the actual answer. (15 samples is a hair tighter than the explore phase but still fine: failure probability per bit $\le 2^{-15}$, so $\le 2^{-7}$ over 128 bits.)

We *don't* need the masked $C_\text{flag}$ from this phase: we already know what the underlying ciphertext is. Same key, same nonce, same plaintext-length-1 means the GCM keystream block $S_1 = E_K(J_0 + 1)$ is the same as in the explore phase, so

$$C_\text{flag} = PT_\text{flag} \oplus S_1 = PT_\text{flag} \oplus PT_1 \oplus C_1.$$

## Step 4: solve for `storm`

Now we have the real $T_\text{flag}$ and we know the GCM tag equation it satisfies:

$$T_\text{flag} = S_0 \oplus B_1 H^4 \oplus B_2 H^3 \oplus C_\text{flag} \cdot H^2 \oplus L_2 \cdot H$$

where $(B_1, B_2)$ is `storm` padded to two 16-byte blocks (17 bytes → block 1 is `storm[:16]`, block 2 is `storm[16] || 0^{15}`) and $L_2$ encodes the bit-lengths $(17 \cdot 8, 16 \cdot 8)$.

Everything is known except $B_1$ and the single byte $B_2$. Brute-force the 256 choices for $B_2$, for each, solve linearly for $B_1$:

$$B_1 = H^{-4} \cdot \big( T_\text{flag} \oplus S_0 \oplus B_2 H^3 \oplus C_\text{flag} H^2 \oplus L_2 H \big).$$

To pick the right one, reseed `random.seed(B_1 \,\|\, B_2)` and check that the resulting masks reproduce the very first explore output (`ct1_list[0]`, `t1_list[0]`). Exactly one candidate will match, and that's `storm`.

## Step 5: predict the next mask

With `storm` we own the MT state. Replay it forward through every `random.getrandbits(128)` call the server has made (38 explore calls × 2 + 15 speak failures × 2), then read off the next two draws,  that's the mask the server will apply to the 16th tag. AND it with our recovered $T_\text{flag}$, send as hex and get the flag.

## solve.py

The full solver is [here](./solve.py).

```sh
❯ python solve.py
[/.......] Opening connection to chall.polygl0ts.ch on port 6273: Trying 64:ff9b::54ea[+] Opening connection to chall.polygl0ts.ch on port 6273: Done
[+] Storm recovered: f9c79e87b60df6533ba7906e75483c8f2b
[*] Switching to interactive mode
       [  Lain descends, the storm dissipating...  ]
EPFL{you-qu3lled-the-electric-st0rm}

[*] Got EOF while reading in interactive
$
```
