import base64, json, re
from pwn import *

def padd(P1, P2, a, N):
    x1,y1,z1 = P1
    x2,y2,z2 = P2
    return ((x1*x2 + a*(y2*z1 + y1*z2)) % N,
            (x2*y1 + x1*y2 + a*z1*z2)   % N,
            (y1*y2 + x2*z1 + x1*z2)     % N)

def smul(k, P, a, N):
    R, B = (1,0,0), P
    while k:
        if k & 1:
            R = padd(R, B, a, N)
        B = padd(B, B, a, N)
        k >>= 1
    return R

def factor_Nhat(Nh):
    PR = PolynomialRing(Zmod(Nh), 'x')
    x = PR.gen()
    inv = int(pow(2, -141, Nh))
    for g in range(1, 1 << 16):
        try:
            roots = (x + g*inv).small_roots(X=2^115, beta=0.49, epsilon=0.03)
        except:
            roots = []
        for r in roots:
            ph = (int(r) << 141) + g
            if ph > 1 and Nh % ph == 0:
                return ph, Nh // ph

def ppe_recover_y(N, e, p0, delta=0.615, gamma=0.28, m=2):
    pr = ZZ['v, y, z']
    v, y, z = pr.gens()
    q0 = N // p0
    A = 2*(p0 + q0) - 2*(N + 1)
    B = (p0 + q0)^2 - 2*(N + 1)*(p0 + q0) + (N + 1)^2
    f = v*(y^2 + A*y + B) + 1
    qr = pr.quotient((v*y^2 + 1) - z)
    V, Y = int(8*e*N^delta / N^2), int(3*N^gamma)
    bnd = [V, Y, V*Y^2 + 1]

    shifts = []
    for u in range(m + 1):
        for i in range(u + 1):
            for j in range(2):
                shifts.append(qr(v^(u-i) * y^j * f^i * e^(m-i)).lift())
        for j in range(2, 2 + u):
            shifts.append(qr(y^j * f^u * e^(m-u)).lift())

    pr2 = pr.change_ring(ZZ, order='invlex')
    shifts = sorted(pr2(s) for s in shifts)
    mons = sorted({mn for s in shifts for mn in s.monomials()})
    L = matrix(ZZ, len(shifts), len(mons))
    for r, s in enumerate(shifts):
        for c, mn in enumerate(mons):
            L[r, c] = s.monomial_coefficient(mn) * mn(*bnd)
    L = L.LLL()

    fr = ZZ['v, y']
    fv, fy = fr.gens()
    polys = []
    for row in range(L.nrows()):
        p = sum((L[row, c] // mn(*bnd)) * pr(mn) for c, mn in enumerate(mons) if L[row, c])
        if p and not p.is_constant():
            polys.append(fr(p(fv, fy, fv*fy^2 + 1)))

    s = Sequence(polys, fr.change_ring(QQ, order='lex'))
    while s:
        for poly in s.groebner_basis():
            vs = poly.variables()
            if len(vs) == 1 and vs[0] == fy:
                for r in poly.univariate_polynomial().roots(multiplicities=False):
                    if r:
                        return int(r)
        s.pop()

# io = process(["python3", "given-files/chall.py"])
io = remote("chall.polygl0ts.ch", 6931)
io.recvuntil(b"DATA:")

buf = re.sub(rb"\x1b\[[\d;?]*[A-Za-z]", b"", io.recvuntil(b"!", drop=True))
o = json.loads(base64.b64decode(re.sub(rb"[^A-Za-z0-9+/=]", b"", buf)))
N, e, a, C = int(o["N"]), int(o["e"]), int(o["a"]), tuple(int(c) for c in o["C"])
Nh, eh    = int(o["N_hat"]), int(o["e_hat"])

ph, qh = factor_Nhat(Nh)
p0 = ph - (ph % (1 << 141))
y0 = ppe_recover_y(N, e, p0)

S = y0 + p0 + N // p0
disc = isqrt(S*S - 4*N)
p, q = (S + disc) // 2, (S - disc) // 2
assert p * q == N

m = smul(int(pow(e, -1, (p-1)^2 * (q-1)^2)), C, a, N)[0]
s = int(pow(m, int(pow(eh, -1, (ph-1)*(qh-1))), Nh))
secret = s.to_bytes((s.bit_length()+7)//8, 'big')
io.sendline(secret)
io.interactive()
