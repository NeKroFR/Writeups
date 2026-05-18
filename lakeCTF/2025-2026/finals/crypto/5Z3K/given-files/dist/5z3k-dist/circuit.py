"""
    This module provides an representation for arithmetic circuits, Bristol fashion, with some restrictions
    (see https://nigelsmart.github.io/MPC-Circuits/)
    It is not meant to have vulnerabilities :)
"""

from typing import Literal, Self, TypeAlias, Iterator

BinaryGateType: TypeAlias = Literal["MUL", "ADD"]
UnaryGateType: TypeAlias = Literal["INV"]
Gate: TypeAlias = tuple[BinaryGateType, int, int] | tuple[UnaryGateType, int]

TRANSLATE = {
    "XOR": "ADD",
    "AND": "MUL",
    "INV": "INV",
}

class Circuit:
    def __init__(self, ninputs: int, nmults: int, outputs: list[int], gates: list[Gate]):
        self.ninputs: int = ninputs
        self.nmults: int = nmults
        self.outputs: list[int] = outputs
        self.gates: list[Gate] = gates

    @classmethod
    def parse(cls, lines: Iterator[str]) -> Self:
        def get():
            while True:
                res = next(lines).strip()
                if res:
                    return res

        relabel = {}

        ngates, nwires = map(int, get().split())
        niv, *nis = map(int, get().split())
        assert len(nis) == niv
        ninputs = sum(nis)
        nov, *nos = map(int, get().split())
        assert len(nos) == nov
        noutputs = sum(nos)
        assert nwires == ngates + ninputs

        nmults = 0

        for i in range(ninputs):
            relabel[i] = i

        gates = []
        for gate_idx in range(ngates):
            parts = get().split()
            nin = int(parts[0])
            assert nin in {1, 2}
            nout = int(parts[1])
            assert nout == 1
            ins = [relabel[int(parts[2 + i])] for i in range(nin)]
            outs = [int(parts[2 + nin + i]) for i in range(nout)]
            relabel[outs[0]] = ninputs + gate_idx
            outs[0] = ninputs + gate_idx
            operation = parts[2 + nin + nout]
            assert operation in TRANSLATE.keys()
            if operation in {"XOR", "AND"}:
                assert nin == 2
            else:
                assert nin == 1
            gates.append((TRANSLATE[operation], *ins))
            if operation == "AND":
                nmults += 1
        outputs = [relabel[nwires - 1 - i] for i in range(noutputs)]

        return cls(ninputs, nmults, outputs, gates)

    def pad(self, base: int):
        """Pad the circuit with extra multiplications until you have a power of `base`"""
        target = 1
        while target < self.nmults:
            target = base * target
        while self.nmults < target:
            self.gates.append(("MUL", 0, 0))
            self.nmults += 1

    def __iter__(self) -> Iterator[Gate]:
        return iter(self.gates)

    def __len__(self) -> int:
        return len(self.gates)

    def __str__(self):
        return f"Circuit({self.ninputs}, {self.outputs}, {self.gates})"
