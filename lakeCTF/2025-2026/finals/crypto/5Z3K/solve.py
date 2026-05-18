from pwn import *
import json, sys, subprocess

sys.path.insert(0, "given-files/dist/5z3k-dist")
from circuit import Circuit
from params import commitment, gmul, gsum, N, T, TAU_OUT, NU, Check, Input, Witness
from sharing import interpolation_coeffs
from rng import Rng

MASK = (1 << 32) - 1

def affine_outputs(circuit):
    # Symbolic pass over circuit with inputs=0:
    # each output wire becomes an affine form
    # (dict {mult_idx: coeff}, const) over Z_{2^32}.
    nin = circuit.ninputs
    wire = {i: ({}, 0) for i in range(nin)}
    use = {}
    for g in circuit.gates:
        for s in g[1:]:
            use[s] = use.get(s, 0) + 1
    for o in circuit.outputs:
        use[o] = use.get(o, 0) + 1

    midx, wi = 0, nin
    outset = set(circuit.outputs)
    for op, *args in circuit.gates:
        if op == "MUL":
            f = ({midx: 1}, 0); midx += 1
        elif op == "ADD":
            (da, ca), (db, cb) = wire[args[0]], wire[args[1]]
            d = dict(da)
            for k, v in db.items():
                d[k] = (d.get(k, 0) + v) & MASK
                if d[k] == 0:
                    del d[k]
            f = (d, (ca + cb) & MASK)
        else:  # INV
            da, ca = wire[args[0]]
            f = ({k: (-v) & MASK for k, v in da.items()}, (1 - ca) & MASK)
        wire[wi] = f
        for s in args:
            use[s] -= 1
            if use[s] == 0 and s not in outset:
                del wire[s]
        wi += 1
    return [wire[o] for o in circuit.outputs[:128]], midx

def hensel(forms, ncols):
    # Solve M*c + b = 0 % 2^32 by GF(2) RREF + Hensel lift.
    nrows = len(forms)
    rows = [sum((1 << k) for k, v in d.items() if v & 1) | (1 << (ncols + i)) for i, (d, _) in enumerate(forms)]
    pivots, used = [], [False] * nrows
    for col in range(ncols):
        pr = next((r for r in range(nrows) if not used[r] and (rows[r] >> col) & 1), -1)
        if pr < 0:
            continue
        used[pr] = True; pivots.append((pr, col))
        for r in range(nrows):
            if r != pr and (rows[r] >> col) & 1:
                rows[r] ^= rows[pr]
        if len(pivots) == nrows:
            break
    cons = [rows[r] >> ncols for r in range(nrows) if not used[r]]

    c = [0] * ncols
    res = [cv & MASK for _, cv in forms]
    for bit in range(32):
        rhs = sum((1 << r) for r in range(nrows) if (res[r] >> bit) & 1)
        for cm in cons:
            assert not (bin(cm & rhs).count("1") & 1), "inconsistent"
        delta = 0
        for r, col in pivots:
            if bin((rows[r] >> ncols) & rhs).count("1") & 1:
                delta |= 1 << col
        col = 0
        while delta:
            if delta & 1:
                c[col] = (c[col] + (1 << bit)) & MASK
                for r in range(nrows):
                    cf = forms[r][0].get(col, 0)
                    if cf: res[r] = (res[r] + (cf << bit)) & MASK
            delta >>= 1; col += 1
    assert all(r == 0 for r in res)
    return c


def circuit_ab(circuit, c):
    # (a, b) Check values per MUL gate, computed honestly with inputs=0 and our
    # forged c-vals replacing MUL outputs.
    w = [0] * (circuit.ninputs + len(circuit.gates))
    aa, bb, mi = [], [], 0
    for gi, (op, *args) in enumerate(circuit.gates):
        wi = circuit.ninputs + gi
        if op == "MUL":
            aa.append(w[args[0]]); bb.append(w[args[1]])
            w[wi] = c[mi]; mi += 1
        elif op == "ADD":
            w[wi] = (w[args[0]] + w[args[1]]) & MASK
        else:
            w[wi] = (1 - w[args[0]]) & MASK
    return [Check([Witness([v])]) for v in aa], [Check([Witness([v])]) for v in bb]

def lagr(values, at, alpha):
    return gsum(map(gmul, interpolation_coeffs(at, alpha[:len(values)]), values))

def one_proof(io, circuit, c):
    nm = circuit.nmults
    view = [[0]] * (circuit.ninputs + 1)  # zero inputs + zero ring-check mask
    view.extend([v] for v in c)

    ctx = commitment([b"ZK4Z2K", str(circuit)])
    input_comm  = commitment([ctx] + [Input([0])] * (circuit.ninputs + 1))
    extwit_comm = commitment([input_comm, Input([0])] + [Witness([v]) for v in c])

    io.sendline(json.dumps([input_comm.hex()] * N).encode())
    io.recvuntil(b"Ring check rng seed: "); io.recvline()
    io.sendline(b"0")
    io.sendline(json.dumps([extwit_comm.hex()] * N).encode())

    io.recvuntil(b"Compression seed: ")
    seed = bytes.fromhex(io.recvline().strip().decode())
    a_ck, b_ck = circuit_ab(circuit, c)
    eta_rng = Rng(seed)
    x = [Check.sample(eta_rng) * ai for ai in a_ck]
    y = list(b_ck)

    nrounds = 0
    n = nm
    while n > 1:
        nrounds += 1; n //= NU
    alpha = [Check.exseq(i + 1) for i in range(2 * NU + 1)]
    prev = extwit_comm
    pre = [Witness.zero()] * len(circuit.outputs)

    for r in range(nrounds):
        last = (r == nrounds - 1)
        L = len(x) // NU
        ax = [x[i * L:(i + 1) * L] for i in range(NU)]
        by = [y[i * L:(i + 1) * L] for i in range(NU)]
        prefix = pre if r == 0 else []

        if not last:
            hints = [Check.zero()] * (NU + NU - 1)
        else:
            assert L == 1
            xp = [ax[i][0] for i in range(NU)] + [Check.zero()]
            yp = [by[i][0] for i in range(NU)] + [Check.zero()]
            hints = ([ax[i][0] * by[i][0] for i in range(NU)] + [Check.zero(), Check.zero()] +
                     [lagr(xp, alpha[k], alpha) * lagr(yp, alpha[k], alpha) for k in range(NU, 2 * NU + 1)])

        view.extend(h.to_json() for h in hints)
        comm = commitment([prev] + prefix + hints)
        io.sendline(json.dumps([comm.hex()] * N).encode())
        io.recvuntil(b"Seed: ")
        eps = Check.sample(Rng(bytes.fromhex(io.recvline().strip().decode())))

        if not last:
            cs = interpolation_coeffs(eps, alpha[:NU])
            x = [gsum(gmul(cs[i], ax[i][k]) for i in range(NU)) for k in range(L)]
            y = [gsum(gmul(cs[i], by[i][k]) for i in range(NU)) for k in range(L)]
            prev = comm
        else:
            cs = interpolation_coeffs(eps, alpha[:NU + 1])
            rec = gsum(map(gmul, cs, xp))
    io.sendline(json.dumps(rec.to_json()).encode())

    claims = [Input([0])] + [Witness.zero()] * len(circuit.outputs) + [rec, Check.zero()]
    io.sendline(commitment(sum(([cl] * (N + 1) for cl in claims), [])).hex().encode())
    for _ in range(T):
        io.recvuntil(b"Open party "); io.recvuntil(b"? ")
        io.sendline(json.dumps(view).encode())


with open("given-files/dist/5z3k-dist/aes_128.txt") as f:
    circuit = Circuit.parse(f)
circuit.pad(NU)
circuit.outputs += list(range(128, 256))

forms, _ = affine_outputs(circuit)
c_vals = hensel(forms, circuit.nmults)

# context.log_level = "debug"
# io = process(["python3", "-u", "verifier.py"], cwd="given-files/dist/5z3k-dist")
io = remote("chall.polygl0ts.ch", 6563)
io.recvuntil(b"proof of work:\n")
token = io.recvline().decode().strip().split()[-1]
io.recvuntil(b"solution: ")
print(f"Solving PoW: {token}")
sol = subprocess.check_output(["bash", "-c", f"curl -sSfL https://pwn.red/pow | sh -s {token}"]).strip()
print(f"PoW solution: {sol.decode()}")
io.sendline(sol)

for _ in range(TAU_OUT):
    io.recvuntil(b"Input commitments? ")
    one_proof(io, circuit, c_vals)
io.recvuntil(b"EPFL{")
print("EPFL{" + io.recvline().decode())
