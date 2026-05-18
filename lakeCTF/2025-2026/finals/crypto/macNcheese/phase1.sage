# Algorithm 3.6 from Kirshanova-May (https://eprint.iacr.org/2022/525.pdf):
# extend known support I from t(m-2)+1 = 641 to tm+1 = 769 with rank 768.
# Use solve.sh to run in parallel
# Usage: sage phase1.sage <seed> <out.pkl>
import sys, pickle

SEED = int(sys.argv[1])
OUT = sys.argv[2]
set_random_seed(SEED)

P = PolynomialRing(GF(2), 'z')
ff = GF(2^12, 'z', modulus=P([1,0,0,1,0,0,0,0,0,0,0,0,1]))
F = GF(2)
m, t, n = 12, 64, 3488
mt = m*t
R = PolynomialRing(ff, 'x')
x = R.gen()

with open('given-files/wired_transmission.txt', 'rb') as fh:
    blob = fh.read()

SPLIT = b'\n---- present day, present time. haha. ----\n'
pub_key_bytes, _, _, syn1337_str, syn1420_str = blob.split(SPLIT)
inv1 = sage_eval(syn1337_str.decode(), locals={'x': x, 'z': ff.gen()})
inv2 = sage_eval(syn1420_str.decode(), locals={'x': x, 'z': ff.gen()})
field_elems = list(ff)

# (x - alpha_i) * s_i = 1 % g  =>  brute-force alpha_1337 over GF(2^12)
g = None
a1337 = a1420 = None
lc = inv1.leading_coefficient()
for a in field_elems:
    cand = (x - a) * inv1 - 1
    if cand.leading_coefficient() != lc:
        continue
    g_cand = cand / lc
    if g_cand.degree() != t or not g_cand.is_monic():
        continue
    _, _, inv2inv = g_cand.xgcd(inv2)
    beta = ((x*inv2 - 1) * (inv2inv % g_cand)) % g_cand
    if beta.degree() <= 0 and g_cand.is_irreducible():
        g = g_cand
        a1337 = a
        a1420 = beta.constant_coefficient()
        break
assert g is not None

def pub_key_from_bytes(em):
    s = int.from_bytes(em, 'big')
    br = Integer(s).digits(2)
    br = [0]*(mt*n - len(br)) + br
    return matrix(GF(2), [br[r*n:(r+1)*n] for r in range(mt)][::-1])

H = pub_key_from_bytes(pub_key_bytes)
Hcols = [H.column(j) for j in range(n)]

# 641 anchors: 639 unshuffled tail + 2 leaks
init_anchors = {1337: a1337, 1420: a1420}
for k in range(n - (t*(m-2) - 1), n):
    init_anchors[k] = field_elems[k]

Rg2 = R.quotient(g*g, 'xq2')

# Find c in ker(H) with supp(c) in I + J, |J INTER supp(c)| <= t+1
def gen_codeword(I_set, I_list):
    for _ in range(300):
        notI = set()
        need = (mt + 1) - len(I_list)
        if need <= 0:
            return []
        while len(notI) < need:
            p = ZZ.random_element(0, n)
            if p not in I_set and p not in notI:
                notI.add(p)
        cols = sorted(I_set | notI)
        Habr = matrix(F, [list(Hcols[j]) for j in cols]).transpose()
        for v in Habr.right_kernel().basis():
            cw = [F(0)]*n
            for idx, col in enumerate(cols):
                cw[col] = v[idx]
            if sum(int(cw[i]) for i in notI) < t + 2:
                return cw
    return []

# Find c2 sharing istar in supp(c1) \ I, prefer rank-extending istars
def gen_c2(I_set, I_list, c1, rt):
    supp_c1 = [i for i in range(n) if i not in I_set and c1[i] == 1]
    if not supp_c1:
        return [], None
    if rt.rank < mt:
        good = set(i for i in supp_c1 if rt.would_extend(Hcols[i]))
        supp_c1 = [i for i in supp_c1 if i in good] + [i for i in supp_c1 if i not in good]
    Habr = matrix(F, mt, mt + 2)
    ctr = 0
    for j in I_list:
        for i in range(mt):
            Habr[i, ctr] = H[i, j]
        ctr += 1
    save = ctr
    for _ in range(700):
        new_cols = []
        ctr = save
        while ctr < mt + 2:
            j = ZZ.random_element(0, n)
            if j not in I_set and j not in new_cols and j not in supp_c1:
                for i in range(mt):
                    Habr[i, ctr] = H[i, j]
                new_cols.append(j)
                ctr += 1
        if Habr.rank() < mt:
            continue
        for istar in supp_c1:
            try:
                res = Habr.solve_right(vector(F, [H[i, istar] for i in range(mt)]))
            except Exception:
                continue
            cw = [F(0)]*n
            cw[istar] = F(1)
            wt = 1
            k = 0
            for j in I_list:
                cw[j] = res[k]
                k += 1
            for j in new_cols:
                cw[j] = res[k]
                k += 1
                if cw[j] == 1:
                    wt += 1
            if wt < t + 1:
                return cw, istar
    return [], None

# Cache 1/(x - alpha) % g^2
_inv_cache = {}
def inv_xLi(alpha):
    if alpha not in _inv_cache:
        _inv_cache[alpha] = Rg2(1) / Rg2(x - alpha)
    return _inv_cache[alpha]

# Recover candidate alphas in notI from a codeword via the polynomial system
def obtain_alphas(cw, I_list, notI, Lleaked):
    known = Rg2(0)
    for i_, idx in enumerate(I_list):
        if cw[idx] == 1:
            known += inv_xLi(Lleaked[i_])
    u = len(notI)
    A = matrix(ff, 2*t, 2*u - 1)
    for j in range(u):
        for i, c in enumerate(list(Rg2(known * x^j))):
            A[i, j] = c
    for i in range(u, 2*u - 1):
        A[i - u, i] = -1
    target = vector(ff, list(Rg2(known * x^u + (u % 2) * x^(u-1))))
    try:
        res = A.solve_right(target)
    except Exception:
        return []
    return [r[0] for r in R(list(res[:u]) + [ff(1)]).roots(ff)]

# Row-echelon basis of GF(2) column vectors, O(mt) per query/add
class RankTracker:
    def __init__(self):
        self.basis = []
        self.pivots = []
    def _reduce(self, v):
        v = vector(F, v)
        for row, p in zip(self.basis, self.pivots):
            if v[p] == 1:
                v = v + row
        return v
    def would_extend(self, v):
        rv = self._reduce(v)
        return any(rv[i] == 1 for i in range(mt))
    def add(self, v):
        rv = self._reduce(v)
        for i in range(mt):
            if rv[i] == 1:
                new = [row + rv if row[i] == 1 else row for row in self.basis]
                ins = 0
                while ins < len(self.pivots) and self.pivots[ins] < i:
                    ins += 1
                new.insert(ins, rv)
                self.basis = new
                self.pivots.insert(ins, i)
                return True
        return False
    @property
    def rank(self):
        return len(self.basis)

I_list = sorted(init_anchors.keys())
Lleaked = [init_anchors[i] for i in I_list]
I_set = set(I_list)
rt = RankTracker()
for j in I_list:
    rt.add(Hcols[j])

# Strict rank-aware loop: until rank=mt, accept only rank-extending istars.
# After rank=mt, accept anything to fill |I| to mt+1.
fails = 0
FAIL_LIMIT = 3000
while True:
    if len(I_list) >= mt + 1 and rt.rank == mt:
        break
    c1 = gen_codeword(I_set, I_list)
    if not c1:
        fails += 1
        if fails > FAIL_LIMIT:
            sys.exit(1)
        continue
    notI1 = [i for i in range(n) if i not in I_set and c1[i] == 1]
    c2, istar = gen_c2(I_set, I_list, c1, rt)
    if not c2 or istar is None or istar in I_set:
        fails += 1
        if fails > FAIL_LIMIT:
            sys.exit(1)
        continue
    notI2 = [i for i in range(n) if i not in I_set and c2[i] == 1]
    a1 = obtain_alphas(c1, I_list, notI1, Lleaked)
    a2 = obtain_alphas(c2, I_list, notI2, Lleaked)
    common = list(set(a1) & set(a2))
    if len(common) != 1:
        continue
    new_alpha = common[0]
    if rt.rank < mt and not rt.would_extend(Hcols[istar]):
        continue
    pos = 0
    while pos < len(I_list) and istar > I_list[pos]:
        pos += 1
    I_list.insert(pos, istar)
    Lleaked.insert(pos, new_alpha)
    I_set.add(istar)
    rt.add(Hcols[istar])
    fails = 0

with open(OUT, 'wb') as fh:
    pickle.dump({
        'I_list': list(I_list),
        'Lleaked_bits': [list(l._vector_()) for l in Lleaked],
        'seed': SEED,
    }, fh)
