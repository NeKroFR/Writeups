from typing import Any, Callable, Iterable, NewType, TypeAlias
from functools import reduce
import hashlib

from galois_ring import GR, GRingElement, RingElement, Z2k

# Table 3 parameters: 40 bits of statistical security is fine with an interactive verifier
K = 32
N = 63
T = 1

S = 0
S_RC = 17

D0 = 6
D0_REDUCE = (1, 1, 0, 0, 0, 0)

InputT = NewType("InputT", GRingElement)
Input: type[InputT] = GR(Z2k(K + S_RC), D0, D0_REDUCE, "Input") # type: ignore (workaround)

RingCheckChallengeT = NewType("RingCheckChallengeT", RingElement)
RingCheckChallenge: type[RingCheckChallengeT] = Z2k(1 + S_RC) # type: ignore (workaround)

WitnessT = NewType("WitnessT", GRingElement)
Witness: type[WitnessT] = GR(Z2k(K + S), D0, D0_REDUCE, "Witness") # type: ignore (workaround)
Witgen: TypeAlias = Callable[[], WitnessT]

D1 = 4
D1_REDUCE = ((0, 1, 0, 0, 0, 0), (0, 0, 1, 0, 0, 0), (0, 1, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0))

CheckT = NewType("CheckT", GRingElement)
Check: type[CheckT] = GR(Witness, D1, D1_REDUCE, "Check") # type: ignore (workaround)

NU = 4

TAU_IN = 1
TAU_OUT = 7


# Generic things, good for typing purposes
def gsum[T: RingElement](items: Iterable[T]) -> T:
    return reduce(lambda x, y: x + y, items)

def gmul[T: RingElement](x: T, y: T) -> T:
    return x * y

def serialize(x):
    res = b""
    if isinstance(x, bytes):
        res += b"b" + len(x).to_bytes(4, "big") + x
    elif isinstance(x, str):
        res += b"s" + serialize(x.encode())
    elif isinstance(x, list):
        res += b"l" + len(x).to_bytes(4, "big") + b"".join(serialize(y) for y in x)
    else:
        res += x.serialize()
    return res


# Kinda shitty commitment since we're not very hiding; but no big issue for this challenge, ig
def commitment(x: Any) -> bytes:
    return hashlib.sha256(serialize(x)).digest()
