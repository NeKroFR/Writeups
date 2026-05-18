# Requires phase1_result.pkl (run phase1.sage first)
import pickle
from hashlib import shake_256
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

load("utils.sage")  # https://github.com/ElenaKirshanova/leaky_goppa_in_mceliece/blob/master/utils.sage

P = PolynomialRing(GF(2), 'z')
ff = GF(2^12, 'z', modulus=P([1,0,0,1,0,0,0,0,0,0,0,0,1]))
F = GF(2)
m, t, n = 12, 64, 3488
mt = m*t
kappa = m
R = PolynomialRing(ff, 'x')
x = R.gen()

# Parse + recover g, alpha_1337, alpha_1420
with open('given-files/wired_transmission.txt', 'rb') as fh:
    blob = fh.read()

SPLIT = b'\n---- present day, present time. haha. ----\n'
pub_key_bytes, enc_flag, proto7_str, syn1337_str, syn1420_str = blob.split(SPLIT)
inv1 = sage_eval(syn1337_str.decode(), locals={'x': x, 'z': ff.gen()})
inv2 = sage_eval(syn1420_str.decode(), locals={'x': x, 'z': ff.gen()})
field_elems = list(ff)

g = None
a1337 = a1420 = None
lc = inv1.leading_coefficient()
for a in field_elems[:n]:
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
print(f'a1337={a1337}, a1420={a1420}')

def pub_key_from_bytes(em):
    s = int.from_bytes(em, 'big')
    br = Integer(s).digits(2)
    br = [0]*(mt*n - len(br)) + br
    return matrix(GF(2), [br[r*n:(r+1)*n] for r in range(mt)][::-1])

H = pub_key_from_bytes(pub_key_bytes)
s_pub = vector(GF(2), eval(proto7_str.decode()))

# Load phase 1 output
with open('phase1_result.pkl', 'rb') as fh:
    pdata = pickle.load(fh)

I_list = list(pdata['I_list'])
Lleaked = [ff(bits) for bits in pdata['Lleaked_bits']]
rk = H.matrix_from_columns(I_list).rank()
print(f'seed={pdata["seed"]} |I|={len(I_list)} rank={rk}')

# if |I| > mt+1 or rank < mt, trim greedily to a full-rank mt+1 subset.
if len(I_list) != mt + 1 or rk != mt:
    pairs = sorted(zip(I_list, Lleaked), key=lambda p: p[0])
    chosen = []
    cols = []
    cur = 0
    for idx, a in pairs:
        if H.matrix_from_columns(cols + [idx]).rank() > cur:
            chosen.append((idx, a))
            cols.append(idx)
            cur += 1
            if cur == mt:
                break
    assert cur == mt
    extra = next(((i, a) for i, a in pairs if i not in {x for x, _ in chosen}), None)
    chosen.append(extra)
    chosen.sort()
    I_list = [i for i, _ in chosen]
    Lleaked = [a for _, a in chosen]
    rk = H.matrix_from_columns(I_list).rank()
    print(f'    trimmed to |I|={len(I_list)} rank={rk}')
assert len(I_list) == mt + 1 and rk == mt

# Recover Hpriv = U*H (Algorithm 3.3, full-rank case: https://eprint.iacr.org/2022/525.pdf)
Hpriv = recover_Hpriv_complete(H, g, list(Lleaked), F, ff, kappa, set(I_list))
assert Hpriv != 0

# Map each column of Hpriv to a field element
def can_col(gamma):
    val = g(gamma)^(-1)
    bits = []
    for i_ in range(t):
        bits.extend(list((val * gamma^i_)._vector_()))
    return tuple(bits)

can_table = {can_col(a): a for a in ff}
support = [None] * n
seen = set()
for j in range(n):
    a = can_table[tuple(Hpriv.column(j))]
    assert a not in seen
    seen.add(a)
    support[j] = a

# Patterson decode: v = protocol_7 || 0,  S(x) = sum 1/(x-alpha_i)
S_poly = R(0)
for i_ in range(mt):
    if s_pub[i_] == 1:
        _, _, inv = g.xgcd(x - support[i_])
        S_poly = (S_poly + inv % g) % g

# sqrt(x) % g
coeffs = g.list()
sqrt_field = lambda c_: c_ ** (2**(m-1))
ae = R([sqrt_field(c) for c in coeffs[0::2]])
ao = R([sqrt_field(c) for c in coeffs[1::2]])
_, _, ao_inv = g.xgcd(ao)
ao_inv = ao_inv % g
sqrt_x = (ae * ao_inv) % g

def poly_sqrt(f_):
    f_ = R(f_) % g
    cs = f_.list()
    return (R([sqrt_field(c) for c in cs[0::2]]) + sqrt_x * R([sqrt_field(c) for c in cs[1::2]])) % g

if S_poly == 0:
    sigma_e = R(1)
else:
    _, _, Sinv = g.xgcd(S_poly)
    Sinv = Sinv % g
    if Sinv == x:
        sigma_e = x
    else:
        T = poly_sqrt(Sinv + x)
        r0, r1, s0, s1 = R(g), T % g, R(0), R(1)
        while r1.degree() > t // 2:
            q = r0 // r1
            r0, r1 = r1, r0 - q*r1
            s0, s1 = s1, s0 - q*s1
        sigma_e = r1^2 + x * s1^2

err_pos = [i for i, gamma in enumerate(support) if sigma_e(gamma) == 0]
err = vector(GF(2), [1 if i in err_pos else 0 for i in range(n)])
assert len(err_pos) == t and H * err == s_pub

# Derive AES key, decrypt
e_int = int(''.join(str(int(b)) for b in err), 2)
C_int = int(''.join(str(int(b)) for b in s_pub), 2)
key = shake_256(b'\x01' + e_int.to_bytes(ceil(n/8), 'big') + C_int.to_bytes(ceil(mt/8), 'big')).digest(16)
flag = unpad(AES.new(key, AES.MODE_ECB).decrypt(enc_flag), 16)
print(flag.decode())
