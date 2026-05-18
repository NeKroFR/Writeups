# Wordy

This challenge wraps an MT19937-prediction problem in a Wordle gimmick. Each round the server picks a 5-letter word from a 2315 words wordlist using `random.getrandbits(32)`, gives us 6 guesses, and on a win prints two bits of the underlying RNG output back to us as a "leak". The flag drops after a streak of 20 first-attempt wins plus one final L/A/I/N letter chosen by yet another leak. So we have to break the PRNG.

We are given two files: [server.py](./given-files/server.py) and [wordlist.txt](./given-files/wordlist.txt).

## What the server does

```python
def get_next_word(rng, cache, wordlist):
    if not cache:
        value = rng.getrandbits(32)
        cache.extend([(value >> 16) & 0xFFFF, value & 0xFFFF])
    idx_raw = cache.pop(0)
    useful_bits = math.ceil(math.log2(len(wordlist)))   # = 12
    idx = idx_raw & ((1 << useful_bits) - 1)            # & 0xFFF
    if idx >= len(wordlist):
        idx ^= 1 << (useful_bits - 1)                   # ^= 0x800
    return wordlist[idx], (idx_raw >> 12) & 3            # leak = bits 12..13
```

Every `getrandbits(32)` is split into two 16-bit chunks (high then low), one chunk per round. With $N = 2315$ words, $\lceil \log_2 N \rceil = 12$ bits pick the index, with one fold-back when the raw index lands in $[N, 4096[$. The leak is bits 12-13 of the chunk.

The streak only ticks on `attempts == 1`, and 20 in a row by chance is $(1/N)^{20} \approx 2^{-225}$. So we need to predict the next words.

## What one round tells us about the chunk

Per round we learn the word index, and on a win two extra bits.

The bottom 11 bits of the raw chunk always equal `word_idx & 0x7FF`, since the fold only ever flips bit 11. Bit 11 itself is pinned only when the word index falls outside the collapse range $[N - 2048, 2048[ = [267, 2048[$: index $< 267$ came from raw bit 11 = 0, index $\ge 2048$ came from raw bit 11 = 1. Inside the range it could go either way and we skip the equation. Bits 12-13 we only get on a win. Bits 14-15 are gone forever.

So a won, unambiguous round gives us 14 GF(2) equations on the 16-bit chunk. A worst-case round still gives 11.

## Symbolic MT19937 over GF(2)

Tempering, twist, the conditional XOR with `0x9908B0DF`: all linear over $\mathbb{F}_2$. So every output bit the server ever produces is a fixed XOR of the $624 \dot 32 = 19968$ initial state bits.

We start with each state bit as a basis vector:

```python
state[i][b] = 1 << (i * 32 + b)
```

and run the symbolic twist + tempering in parallel with the server. After $r$ rounds we have, for each past and future output bit, a 19968-bit Python `int` that says which state bits XOR into it.

**Note:** CPython's twist is in-place, and for $kk \ge N - M$ the read of `mt[kk + M - N]` picks up the *post*-twist word. The symbolic version has to do the same, otherwise it diverges from CPython right after the first twist.

## Incremental Gaussian elimination

Every round we throw the bits we know into a GF(2) system. Each equation is a (vector, bit) pair. We keep an RREF-like pivot table indexed by the highest set bit of each row. A new row reduces against existing pivots, and if it survives nonzero it becomes a new pivot, otherwise it was dependent.

```python
def add(vec, val):
    while vec:
        p = vec.bit_length() - 1
        row = pivots.get(p)
        if row is None:
            pivots[p] = (vec, val); return
        v2, b2 = row
        vec ^= v2; val ^= b2
```

Achievable rank caps at **19937**, not 19968. MT19937's effective state has 19937 bits, the remaining 31 are phantom bits that show up in our equations but never affect any output (bit 31 of `state[0]` is the textbook one).

We want rank close to 19937 before solving. At lower ranks the free vars in `state[i]` propagate through the twist into bits 0..11 of future outputs, which is exactly the part we want to predict. Empirically rank 18000 gave wrong predictions, 19900 gave perfect ones. Threshold: 19900.

Once we cross it, back-substitute pivots in increasing order, read off the state, and clone the RNG:

```python
clone = random.Random()
clone.setstate((3, mt + (624,), None))
```

Then advance `clone` past `chunks_consumed` chunks so its cache lines up with the server's.

## Actually winning the rounds

We need to win the round to learn the word index. Information-theoretic Wordle is more than enough on 2315 words: opener is `RAISE` (entropy-max over the full pool, cached), and subsequent guesses are entropy-max over the remaining candidates. The pattern matrix `PM[g, a]` is built once and cached on disk. Average lands around 3.6 attempts/round with a ~1% loss rate.

## Putting it together

Play normally for ~2500 rounds. Each won round adds 11-14 GF(2) equations. Once rank hits 19900, recover the state, clone the RNG, and from then on submit the predicted word as the very first guess. The streak gets to 20 inside ~25 more rounds, after which the server calls `get_next_word` one last time and asks `Answer the last enigma:`. Read bits 12-13 of that chunk off the clone, look up `"LAIN"[leak]`, send it.

## solve.py

Full solve script here: [solve.py](./solve.py).

```sh
❯ time python solve.py
[+] Opening connection to chall.polygl0ts.ch on port 6067: Done
[*] first guess: RAISE
[*] R0050 won=True att=3 rank=655
[*] R0100 won=True att=3 rank=1314
...
[*] R2350 won=True att=5 rank=19558
[*] R2400 won=True att=3 rank=19691
[*] R2450 won=True att=3 rank=19833
[*] R2476 won=False att=6 rank=19898
[*] recovering at rank 19903
[+] rng cloned
[*] R2500 won=True att=1 rank=19937
[*] enigma -> 'A'
[*] Switching to interactive mode
Here is your truth: EPFL{wiNNing_w0rdl3_is_E4sy}
[*] Got EOF while reading in interactive
$
[*] Interrupted
[*] Closed connection to chall.polygl0ts.ch port 6067
python3 solve.py  20.75s user 1.58s system 3% cpu 9:54.76 total
```
