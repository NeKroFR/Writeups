import os
from hashlib import shake_256
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


class Code:
    def __init__(self, m, t, n, modulus, irr_poly):
        self.m = m
        self.t = t
        self.n = n
        self.k = n - m * t
        self.setup_fields(modulus, irr_poly)
        self.H = None
        while self.H is None:
            self.goppa_poly = self.random_goppa_poly(t)
            field_elems = list(self.F)
            start_support = field_elems[:n - (t * (m - 2) - 1)]
            end_support = field_elems[n - (t * (m - 2) - 1):n]
            shuffle(start_support)
            # shuffle(end_support)
            self.support = start_support + end_support
            self.H = self.build_parity_check()
        self.syndrome_poly_elems = self.prepare_syndrome_poly()
        self._precompute_sqrt_x()

    def setup_fields(self, modulus, irr_poly):
        P = PolynomialRing(GF(2), "z")
        f = P(modulus)
        self.F = GF(2 ^ self.m, "z", modulus=f)
        self.R = PolynomialRing(self.F, "x")
        self.X = self.R.gen()
        irr_poly = self.R([self.F.from_integer(u) for u in irr_poly])
        assert irr_poly.is_irreducible()
        self.quotient_ring = self.R.quotient(irr_poly)

    def _precompute_sqrt_x(self):
        coeffs = self.goppa_poly.list()
        sqrt_in_field = lambda c: c ** (2 ** (self.m - 1))  # sqrt in GF(2^m)

        # Extract even/odd coefficients AND take sqrt of each in GF(2^m)
        even_coeffs = [sqrt_in_field(c) for c in coeffs[0::2]]
        odd_coeffs = [sqrt_in_field(c) for c in coeffs[1::2]]

        ae = self.R(even_coeffs)
        ao = self.R(odd_coeffs)
        _, _, ao_inv = self.goppa_poly.xgcd(ao)

        self._sqrt_x = ae * ao_inv % self.goppa_poly
        assert (self._sqrt_x * self._sqrt_x) % self.goppa_poly == self.X

    def random_goppa_poly(self, degree):
        g = None
        while g is None or g.degree() < degree:
            coeffs = [self.F.random_element() for _ in range(degree)] + [self.F.one()]
            g = self.quotient_ring(coeffs).minpoly()
        return g

    def build_parity_check(self):
        cols = []
        for gamma in self.support:
            val = self.goppa_poly(gamma) ^ (-1)
            col_bits = []
            for i in range(self.t):
                elem = val * gamma ^ i
                coords = elem._vector_()
                col_bits.extend(list(coords))
            cols.append(col_bits)
        H_raw = matrix(GF(2), self.n, self.m * self.t, cols).T
        H_rref = H_raw.rref()
        pivot_cols = list(H_rref.pivots())
        if pivot_cols != list(range(H_rref.nrows())):
            return None
        return H_rref

    def prepare_syndrome_poly(self):
        # Computing all possible syndromes to speed up key encapsulation
        elems = []
        for i, gamma in enumerate(self.support):
            denom = self.X - gamma
            _, _, inv = self.goppa_poly.xgcd(denom)
            inv = inv % self.goppa_poly
            elems.append(inv)
        return elems

    def compute_syndrome_poly(self, received):
        S = self.R(0)
        for i, gamma in enumerate(self.support):
            if received[i] == 1:
                S = (S + self.syndrome_poly_elems[i]) % self.goppa_poly
        return S

    def poly_sqrt_mod(self, f):
        # from https://crypto.stackexchange.com/questions/17988/algorithm-for-computing-square-roots-in-gf2n
        f = self.R(f) % self.goppa_poly
        coeffs = f.list()
        sqrt_in_field = lambda c: c ** (2 ** (self.m - 1))  # sqrt in GF(2^m)

        # Extract even/odd coefficients AND take sqrt of each in GF(2^m)
        even_coeffs = [sqrt_in_field(c) for c in coeffs[0::2]]
        odd_coeffs = [sqrt_in_field(c) for c in coeffs[1::2]]

        ae = self.R(even_coeffs)
        ao = self.R(odd_coeffs)

        # sqrt(f) = ae + sqrt(x) * ao, then reduce mod goppa_poly
        result = (ae + self._sqrt_x * ao) % self.goppa_poly

        assert (result * result) % self.goppa_poly == f, "sqrt failed"
        return result

    def patterson_error_locator(self, received):
        S_x = self.compute_syndrome_poly(received)
        if S_x == 0:
            return self.R(1)  # no errors
        _, _, S_x_inv = self.R(self.goppa_poly).xgcd(S_x)
        S_x_inv = S_x_inv % self.goppa_poly
        if S_x_inv == self.X:
            return self.X
        T = self.poly_sqrt_mod(S_x_inv + self.X)
        # EEA decode: find x,y with deg(x) <= t/2
        # Run EEA on (goppa_poly, T) stopping when remainder degree < t/2
        r0, r1 = self.R(self.goppa_poly), T % self.goppa_poly
        s0, s1 = self.R(0), self.R(1)
        while r1.degree() > self.t // 2:
            q = r0 // r1
            r0, r1 = r1, r0 - q * r1
            s0, s1 = s1, s0 - q * s1
        x_poly = r1
        y_poly = s1
        assert x_poly == y_poly * T % self.goppa_poly
        u = (x_poly ^ 2 + self.X * y_poly ^ 2)
        return u

    def find_errors(self, msg):
        errors = []
        error_locator = self.patterson_error_locator(msg)
        for i, gamma in enumerate(self.support):
            if error_locator(gamma) == 0:
                errors.append(i)
        return errors


class McEliece:

    def __init__(self):
        f = [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1]  # z^12 + z^3 + 1
        F = [2, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        # x^64 + x^3 + x + z
        self.code = Code(12, 64, 3488, f, F)
        self.pub_key = self.code.H

    def create_wired_key(self):
        mt = self.code.m * self.code.t
        error_positions = sample(range(self.code.n), self.code.t)
        error_vector = vector(GF(2), [1 if i in error_positions else 0 for i in range(self.code.n)])
        protocol_7 = self.pub_key * error_vector
        e = int("".join([str(v) for v in error_vector]), 2)
        C = int("".join([str(v) for v in protocol_7]), 2)
        WIRED_KEY_SIZE = int(128 / 8)
        wired_key = shake_256(b"\x01" +
                                e.to_bytes(ceil(self.code.n / 8), "big") +
                                C.to_bytes(ceil(mt / 8), "big")).digest(WIRED_KEY_SIZE)
        return wired_key, protocol_7

    def decap_key(self, protocol_7):
        protocol_7 = vector(GF(2), protocol_7)
        n = self.code.n
        k = self.code.k
        mt = self.code.m * self.code.t
        v = vector(GF(2), n, list(protocol_7) + [0] * k)
        error_positions = self.code.find_errors(v)
        c_bits = list(v)
        for i in error_positions:
            c_bits[i] += 1
        c = vector(GF(2), c_bits)
        e = v + c
        if sum([int(bit) for bit in e]) != self.code.t or self.code.H * e != protocol_7:
            return None
        e_int = int("".join(str(b) for b in e), 2)
        C_int = int("".join(str(b) for b in protocol_7), 2)
        WIRED_KEY_SIZE = 128 // 8
        wired_key = shake_256(b"\x01" +
                                e_int.to_bytes(ceil(n / 8), "big") +
                                C_int.to_bytes(ceil(mt / 8), "big")).digest(WIRED_KEY_SIZE)
        return wired_key

    def pub_key_to_bytes(self):
        num_bits = self.pub_key.nrows() * self.pub_key.ncols()
        assert num_bits == self.code.m * self.code.t * self.code.n
        num_bytes = ceil(num_bits / 8)
        s = int(0)
        for row in self.pub_key:
            s += ZZ(list(row), base=2)
            s <<= self.code.n
        return int(s >> self.code.n).to_bytes(num_bytes, "big")

    def pub_key_from_bytes(self, encoded_mat):
        num_bits = self.code.m * self.code.t * self.code.n
        num_bytes = ceil(num_bits / 8)
        assert num_bytes >= len(encoded_mat)
        s = int.from_bytes(encoded_mat, "big")
        binary_repr = Integer(s).digits(2)
        binary_repr = [0] * (num_bits - len(binary_repr)) + binary_repr
        rows = []
        for row_inv in range(self.code.m * self.code.t):
            rows.append(binary_repr[row_inv * self.code.n:(row_inv + 1) * self.code.n])
        reconstructed = matrix(GF(2), rows[::-1])
        return reconstructed


FLAG = os.getenv("flag", "EPFL{fake_flag}").encode()

cipher = McEliece()
wired_key, protocol_7 = cipher.create_wired_key()
enc_flag = AES.new(wired_key, AES.MODE_ECB).encrypt(pad(FLAG, 16))

f = open("wired_transmission.txt", "wb")
SPLIT_STRING = b"\n---- present day, present time. haha. ----\n"

f.write(cipher.pub_key_to_bytes())
f.write(SPLIT_STRING)
f.write(enc_flag)
f.write(SPLIT_STRING)
f.write(str(protocol_7).encode())
f.write(SPLIT_STRING)
# memory fragments lain scattered across the nodes, only two were recovered
f.write(str(cipher.code.syndrome_poly_elems[1337]).encode())
f.write(SPLIT_STRING)
f.write(str(cipher.code.syndrome_poly_elems[1420]).encode())
f.close()
