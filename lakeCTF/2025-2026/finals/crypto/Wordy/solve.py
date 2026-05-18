from pwn import *
import math, random, re
import numpy as np

WORDS = [w.strip().upper() for w in open("given-files/wordlist.txt")]
N = len(WORDS)
USEFUL_BITS = math.ceil(math.log2(N))
MASK = (1 << USEFUL_BITS) - 1
HIGH_BIT = 1 << (USEFUL_BITS - 1)

def pat(g, a):
    r = [0]*5
    c = list(a)
    for i in range(5):
        if g[i] == a[i]:
            r[i] = 2
            c[i] = ""
    for i in range(5):
        if r[i] != 2 and g[i] in c:
            r[i] = 1
            c[c.index(g[i])] = ""
    p = 0
    for v in r:
        p = p*3 + v
    return p

def pat_str(s):
    v = 0
    for ch in s:
        v = v*3 + {"B":0,"Y":1,"G":2}[ch]
    return v

def get_pm():
    if os.path.exists("pattern_matrix.npy"):
        return np.load("pattern_matrix.npy")
    pm = np.zeros((N, N), dtype=np.uint8)
    for i, g in enumerate(WORDS):
        for j, a in enumerate(WORDS):
            pm[i, j] = pat(g, a)
    np.save("pattern_matrix.npy", pm)
    return pm

def best_guess(cands, pm):
    if len(cands) == 1:
        return cands[0]
    arr = np.array(cands)
    best = (-1.0, cands[0])
    for g in cands:
        cnt = np.bincount(pm[g, arr])
        cnt = cnt[cnt > 0]
        p = cnt / len(arr)
        e = -float(np.sum(p * np.log2(p)))
        if e > best[0]:
            best = (e, g)
    return best[1]

# MT19937 over GF(2)
NS, M, A = 624, 397, 0x9908B0DF

def temper(y):
    y = list(y)
    for i in range(21):
        y[i] ^= y[i+11]
    M1 = 0x9D2C5680
    n = list(y)
    for i in range(7, 32):
        if (M1 >> i) & 1:
            n[i] = y[i] ^ y[i-7]
    y = n
    M2 = 0xEFC60000
    n = list(y)
    for i in range(15, 32):
        if (M2 >> i) & 1:
            n[i] = y[i] ^ y[i-15]
    y = n
    n = list(y)
    for i in range(14):
        n[i] = y[i] ^ y[i+18]
    return n

def twist(state):
    new = [None]*NS
    for k in range(NS):
        s31 = state[k][31]
        s1 = state[k+1] if k+1 < NS else new[0]
        sM = state[k+M] if k+M < NS else new[k+M-NS]
        out = [None]*32
        for b in range(30):
            out[b] = sM[b] ^ s1[b+1]
        out[30] = sM[30] ^ s31
        out[31] = sM[31]
        y0 = s1[0]
        for j in range(32):
            if (A >> j) & 1:
                out[j] ^= y0
        new[k] = out
    return new

class SymMT:
    def __init__(self):
        self.s = [[1 << (i*32+b) for b in range(32)] for i in range(NS)]
        self.i = NS
    
    def out(self):
        if self.i >= NS:
            self.s = twist(self.s)
            self.i = 0
        o = temper(self.s[self.i])
        self.i += 1
        return o

# incremental GF(2) RREF
class GF2:
    def __init__(self):
        self.p = {}
    
    def add(self, v, b):
        while v:
            p = v.bit_length() - 1
            row = self.p.get(p)
            if row is None:
                self.p[p] = (v, b)
                return
            v ^= row[0]
            b ^= row[1]
    def rank(self):
        return len(self.p)
    
    def solve(self):
        bits = [0] * (NS*32)
        acc = 0
        for p in sorted(self.p):
            v, b = self.p[p]
            par = bin((v & ((1 << p)-1)) & acc).count("1") & 1
            bits[p] = b ^ par
            if bits[p]:
                acc |= 1 << p
        return bits

ANSI = re.compile(rb"\x1b\[[0-9;]*m")

def chunk2idx(c):
    i = c & MASK
    return i ^ HIGH_BIT if i >= N else i

def add_eqs(syst, sc, idx, leak):
    for b in range(11):
        syst.add(sc[b], (idx >> b) & 1)
    if not (N - HIGH_BIT <= idx < HIGH_BIT):
        syst.add(sc[11], (idx >> 11) & 1)
    syst.add(sc[12], leak & 1)
    syst.add(sc[13], (leak >> 1) & 1)

def read_prompt(io):
    buf = io.recvuntil([b"> ", b"enigma: "], timeout=20)
    return ANSI.sub(b"", buf).decode(errors="replace")

# io = process(["python3", "server.py"], cwd="given-files")
io = remote("chall.polygl0ts.ch", 6067)

pm = get_pm()
fg = best_guess(list(range(N)), pm)
log.info(f"first guess: {WORDS[fg]}")

sym = SymMT()
syst = GF2()
sym_cache, pred_cache = [], []
chunks = 0
clone = None
read_prompt(io)

def take_sym():
    if not sym_cache:
        sv = sym.out()
        sym_cache.append([sv[16+b] for b in range(16)])
        sym_cache.append([sv[b] for b in range(16)])
    return sym_cache.pop(0)

def take_pred():
    if clone is None:
        return None
    if not pred_cache:
        v = clone.getrandbits(32)
        pred_cache.extend([(v >> 16) & 0xFFFF, v & 0xFFFF])
    return pred_cache.pop(0)

for r in range(3000):
    sc = take_sym()
    chunks += 1
    p = take_pred()
    pi = chunk2idx(p) if p is not None else None
    cands = list(range(N))
    won = False
    att = 0
    final = False
    for k in range(6):
        g = (pi if pi is not None else fg) if k == 0 else best_guess(cands, pm)
        io.sendline(WORDS[g].encode())
        att += 1
        t = read_prompt(io)
        if "\nCONNECTED" in t:
            won = True
            leak = int(re.search(r"LEAK:\s*([01]{2})", t).group(1), 2)
            final = "enigma:" in t
            add_eqs(syst, sc, g, leak)
            break
        m = re.search(r"Pattern:\s*([BYG]{5})", t)
        cands = [c for c in cands if pm[g, c] == pat_str(m.group(1))]
    if (r+1) % 50 == 0 or not won:
        log.info(f"R{r+1:04d} won={won} att={att} rank={syst.rank()}")
    if final:
        break
    if clone is None and syst.rank() >= 19900:
        log.info(f"recovering at rank {syst.rank()}")
        bits = syst.solve()
        mt = tuple(sum(bits[i*32+b] << b for b in range(32)) for i in range(NS))
        clone = random.Random()
        clone.setstate((3, mt + (624,), None))
        for _ in range(chunks // 2):
            clone.getrandbits(32)
        if chunks % 2:
            pred_cache.append(clone.getrandbits(32) & 0xFFFF)
        log.success("rng cloned")

ans = "LAIN"[(take_pred() >> 12) & 3]
log.info(f"enigma -> '{ans}'")
io.sendline(ans.encode())
io.interactive()
