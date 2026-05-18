"""
    This module provides an unoptimized implementation of Galois rings over Z_{2^k}
    It is not meant to have vulnerabilities :)
"""

import itertools
from abc import ABC, ABCMeta, abstractmethod
from functools import cache
from typing import Self

from rng import Rng


class RingElement(ABC):
    @classmethod
    @abstractmethod
    def total_degree(cls) -> int: ...

    @classmethod
    @abstractmethod
    def two_adicity(cls) -> int: ...

    @classmethod
    @abstractmethod
    def sample(cls, rng: Rng) -> Self: ...

    @classmethod
    @abstractmethod
    def zero(cls) -> Self: ...

    @classmethod
    @abstractmethod
    def one(cls) -> Self: ...

    @staticmethod
    @abstractmethod
    def exseq_size() -> int: ...

    @classmethod
    @abstractmethod
    def exseq(cls, i: int) -> Self: ...

    @abstractmethod
    def is_zero(self) -> bool: ...

    @abstractmethod
    def __add__(self, other: Self) -> Self: ...

    @abstractmethod
    def __sub__(self, other: Self) -> Self: ...

    @abstractmethod
    def __mul__(self, other: Self) -> Self: ...

    @abstractmethod
    def __neg__(self) -> Self: ...

    @abstractmethod
    def __repr__(self) -> str: ...

    @abstractmethod
    def inv(self) -> Self: ...

    @abstractmethod
    def __truediv__(self, other: Self) -> Self: ...

    @abstractmethod
    def __pow__(self, exponent: int) -> Self: ...

    @abstractmethod
    def serialize(self) -> bytes: ...

    @abstractmethod
    def to_json(self): ...

class GRingElement(RingElement):
    @staticmethod
    @abstractmethod
    def base_ring() -> type[RingElement]: ...

    @abstractmethod
    def truncate(self, R: type[RingElement]) -> "GRingElement": ...

def generic_pow[E: RingElement](self_: E, exponent: int) -> E:
    if exponent < 0:
        return self_.inv() ** (-exponent)
    else:
        res = self_.__class__.one()
        base = self_
        while exponent:
            if exponent & 1:
                res = res * base
            base = base * base
            exponent >>= 1
        return res

try:
    import _galois_ring
except ImportError:
    _galois_ring = None # type: ignore

@cache
def Z2k(k: int) -> type[RingElement]:
    if _galois_ring is not None and hasattr(_galois_ring, f"Z2k{k}"):
        return getattr(_galois_ring, f"Z2k{k}")

    MASK = (1 << k) - 1
    class Meta(ABCMeta, type):
        def __repr__(self):
            return f"ℤ_{{2^{k}}}"

    class Element(RingElement, metaclass=Meta):
        def __init__(self, v):
            self.v = int(v) & MASK

        def __int__(self):
            return self.v

        @classmethod
        def total_degree(cls) -> int:
            return 1

        @classmethod
        def two_adicity(cls) -> int:
            return k

        @classmethod
        def sample(cls, rng: Rng) -> Self:
            return cls(int.from_bytes(rng.get(), "big"))

        @classmethod
        def zero(cls) -> Self:
            return cls(0)

        @classmethod
        def one(cls) -> Self:
            return cls(1)

        @staticmethod
        def exseq_size() -> int:
            return 2

        @classmethod
        def exseq(cls, i: int) -> Self:
            assert 0 <= i < cls.exseq_size()
            return cls(i)

        def is_zero(self) -> bool:
            return self.v == 0

        def __add__(self, other: Self) -> Self:
            return self.__class__(self.v + other.v)

        def __sub__(self, other: Self) -> Self:
            return self.__class__(self.v - other.v)

        def __mul__(self, other: Self) -> Self:
            return self.__class__(self.v * other.v)

        def __neg__(self) -> Self:
            return self.__class__.zero() - self

        def __repr__(self) -> str:
            return f"{self.v} ∈ {Element}"

        def inv(self) -> Self:
            assert self.v & 1
            return self.__class__(pow(self.v, -1, 1 << k))

        def __truediv__(self, other: Self) -> Self:
            return self * other.inv()

        def __pow__(self, exponent: int) -> Self:
            return generic_pow(self, exponent)

        def serialize(self) -> bytes:
            return b"z" + k.to_bytes(4, "big") + self.v.to_bytes((k + 7) // 8, "big")

        def to_json(self):
            return int(self)

    return Element


@cache
def GR[Relem: RingElement](R: type[Relem], d: int, reduce_: tuple[RingElement, ...], name: str = "Typename") -> type[GRingElement]:
    if _galois_ring is not None and hasattr(_galois_ring, name):
        return getattr(_galois_ring, name)

    class Meta(ABCMeta, type):
        def __repr__(self):
            return f"GR({R}, {d})"

    class Poly:
        def __init__(self, elems: list[Relem]):
            self.elems: list[Relem] = elems[:]

        @classmethod
        def zero(cls) -> Self:
            return cls([])

        def is_zero(self) -> bool:
            return self.normalize().elems == []

        def normalize(self) -> Self:
            elems = self.elems[:]
            while elems and elems[-1].is_zero():
                elems.pop()
            return self.__class__(elems)

        def __add__(self, other: Self) -> Self:
            return self.__class__([a + b for (a, b) in itertools.zip_longest(self.elems, other.elems, fillvalue=R.zero())]).normalize()

        def __sub__(self, other: Self) -> Self:
            return self.__class__([a - b for (a, b) in itertools.zip_longest(self.elems, other.elems, fillvalue=R.zero())]).normalize()

        def __mul__(self, other: Self) -> Self:
            unreduced = [R.zero() for _ in range(len(self.elems) + len(other.elems) - 1)]
            for i in range(len(self.elems)):
                for j in range(len(other.elems)):
                    unreduced[i + j] += self.elems[i] * other.elems[j]
            return self.__class__(unreduced).normalize()

        def __neg__(self) -> Self:
            return self.__class__([-x for x in self.elems])

        def __floordiv__(self, denom_: Self) -> Self:
            num = self.elems[:]
            denom = denom_.elems[:]
            while denom and denom[-1].is_zero():
                denom.pop()
            assert denom
            res = []
            d = denom[-1]
            for _ in range(max(0, len(num) - len(denom) + 1)):
                res.append(num.pop() / d)
            return self.__class__(res[::-1])

        def __repr__(self) -> str:
            if not self.elems:
                return "0"
            else:
                return " + ".join(f"({e}) * X^{i}" for (i, e) in reversed(list(enumerate(self.elems))))

        def __iter__(self):
            return iter(self.elems)

        def __len__(self):
            return len(self.elems)

        def __getitem__(self, idx):
            return self.elems[idx]

    class Element(GRingElement, metaclass=Meta):
        @staticmethod
        def base_ring():
            return R

        @classmethod
        def total_degree(cls) -> int:
            return d * R.total_degree()

        @classmethod
        def two_adicity(cls) -> int:
            return R.two_adicity()

        def __init__(self, elems: list[Relem]):
            # Stored low to high
            elems = list(elems)
            for i in range(len(elems)):
                if str(type(elems[i])) != str(R):
                    elems[i] = R(elems[i])
            self.v = Poly([elems[i] if i < len(elems) else R.zero() for i in range(d)])

        @classmethod
        def from_poly(cls, poly: Poly) -> Self:
            self = cls([])
            self.v = poly
            return self

        @classmethod
        def sample(cls, rng: Rng) -> Self:
            return cls([R.sample(rng) for _ in range(d)])

        @classmethod
        def zero(cls) -> Self:
            return cls([])

        @classmethod
        def one(cls) -> Self:
            return cls([R.one()])

        @staticmethod
        def exseq_size() -> int:
            return R.exseq_size() ** d

        @classmethod
        def exseq(cls, i: int) -> Self:
            assert 0 <= i < cls.exseq_size()
            S = R.exseq_size()
            elems = []
            for _ in range(d):
                elems.append(R.exseq(i % S))
                i //= S
            return cls(elems)

        def is_zero(self) -> bool:
            return all(e.is_zero() for e in self.v.elems)

        def __neg__(self) -> Self:
            return self.__class__.zero() - self

        def __add__(self, other: Self) -> Self:
            return self.__class__.from_poly(self.v + other.v)

        def __sub__(self, other: Self) -> Self:
            return self.__class__.from_poly(self.v - other.v)

        def truncate(self, R2: type[RingElement]) -> RingElement:
            if R2.total_degree() == 1:
                return GR(R2, d, reduce_)(list(map(int, self.v))) # type: ignore (We know the constructor works)
            else:
                return GR(R2, d, reduce_)([x.truncate(R2.base_ring()) for x in self.v]) # type: ignore (We know the constructor works)
        def __mul__(self, other: Self) -> Self:
            return do_reduction(self.__class__, self.v * other.v)

        def __repr__(self) -> str:
            return f"{repr(self.v)} ∈ {repr(Element)}"

        def inv(self) -> Self:
            res = self.one()
            D = self.total_degree()
            K = self.two_adicity()
            a = self
            for i in range(K + D - 1):
                if i != K - 1:
                    res *= a
                a = a * a
            return res
            # s = Poly([R.one()])
            # old_s = Poly([])
            # r = self.v
            # old_r = Poly(reduce.elems + [-R.one()])
            # while not r.is_zero():
                # quotient = old_r // r
                # (old_r, r) = (r, old_r - quotient * r)
                # (old_s, s) = (s, old_s - quotient * s)
            # return self.__class__.from_poly(old_s // old_r)

        def __truediv__(self, other: Self) -> Self:
            return self * other.inv()

        def __pow__(self, exponent: int) -> Self:
            return generic_pow(self, exponent)

        def serialize(self) -> bytes:
            elems = self.v.normalize().elems
            return b"g" + len(elems).to_bytes(4, "big") + b"".join(e.serialize() for e in elems)

        def to_json(self):
            return [x.to_json() for x in self.v]

    RingElement.register(Element)

    reduce = Poly(list(map(R, reduce_)))
    def do_reduction[E: Element](cls: type[E], poly: Poly) -> E:
        low = Poly(poly.elems[:d])
        high = Poly(poly.elems[d:])
        if high.is_zero():
            return cls.from_poly(low)
        return do_reduction(cls, reduce * high + low)

    return Element
