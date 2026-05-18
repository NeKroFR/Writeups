from circuit import Circuit
from galois_ring import RingElement
from params import NU, Check, CheckT, Input, InputT, RingCheckChallenge, Witness, WitnessT, commitment, gmul, gsum
from rng import Rng
from sharing import interpolation_coeffs


class Party:
    def __init__(self,
                 party: int,
                 # The type for view should be enough for our purposes
                 view: list[int | list[int] | list[list[int]]],
                 ring_check_seed: bytes,
                 mulcheck_seeds: list[list[bytes]],
                 comms_to_check: list[bytes],
                 context_comm: bytes,
                 opened_values: list[RingElement]):
        self.party: int = party
        self.view: list[int | list[int] | list[list[int]]] = view[::-1]
        self.ring_check_seed: bytes = ring_check_seed
        self.mulcheck_seeds: list[list[bytes]] = mulcheck_seeds
        self.comms_to_check: list[bytes] = comms_to_check[::-1]
        self.opened_values: list[RingElement] = opened_values[::-1]
        self.last_comm: bytes = context_comm
        self.commit_buf: list[RingElement] = []
        self.mults: list[tuple[WitnessT, WitnessT, WitnessT]] = []
        self.openings: list = []

    def assert_commitment(self, *extra_inputs):
        actual = commitment([self.last_comm, *self.commit_buf, *extra_inputs])
        self.last_comm = actual
        self.commit_buf = []
        assert actual == self.comms_to_check.pop()

    def get_hint[T: RingElement](self, cls: type[T]) -> T:
        res = cls(self.view.pop())
        self.commit_buf.append(res)
        return res

    def open(self, share: RingElement) -> RingElement:
        self.openings.append(share)
        res = self.opened_values.pop()
        self.commit_buf.append(res)
        return res

    def ring_check(self, inputs: list[InputT], mask: InputT) -> list[WitnessT]:
        """
            Pi_{RingCheck}, Figure 6
            Returns the truncated inputs
        """
        # Step 1
        x0 = mask
        # Step 2 was doing in `verify`, sampled after the inputs were committed to
        ro = Rng(self.ring_check_seed)
        # Extending rather than truncating, but it works
        rs: list[InputT] = [Input([Input.base_ring()(int(RingCheckChallenge.sample(ro)))]) for _ in inputs] # type: ignore
        # Step 3
        v = x0 + gsum(map(gmul, rs, inputs))
        # Step 4 is handled by `check_openings`
        self.open(v)
        return [x.truncate(Witness.base_ring()) for x in inputs] # type: ignore (truncation doesn't quite work well with typing)

    def compress(self, x: list[list[CheckT]], y: list[list[CheckT]], z: list[CheckT], rand: bool, epsilon: CheckT) -> tuple[list[CheckT], list[CheckT], CheckT]:
        """
            Follows Figure 4
        """
        alpha = [Check.exseq(i + 1) for i in range(2 * NU + 1)]
        # Step 1
        if rand:
            assert len(x) == NU
            # get v
            v = [self.get_hint(Check) for _ in x[0]]
            x.append(v)
            # get w
            w = [self.get_hint(Check) for _ in y[0]]
            y.append(w)

        # In verification, we know ε beforehand
        coeffs = interpolation_coeffs(epsilon, alpha[:len(x)])
        f = [gsum(map(gmul, coeffs, [e[i] for e in x])) for i in range(len(x[0]))]
        g = [gsum(map(gmul, coeffs, [e[i] for e in y])) for i in range(len(y[0]))]

        # Step 2
        z = z[:]
        for _ in range(NU + 1, 2*NU):
            z.append(self.get_hint(Check))
        if rand:
            z.append(self.get_hint(Check))
            z.append(self.get_hint(Check))

        # Step 3
        coeffs = interpolation_coeffs(epsilon, alpha[:len(z)])
        h = gsum(map(gmul, coeffs, z))

        # Step 4: validate the commitment from before we gave out epsilon
        self.assert_commitment()

        # Step 5
        return (f, g, h)

    def mul_check(self, seeds: list[bytes]):
        """
            Follows Figure 5
        """
        # Step 1:
        mults = [(Check([a]), Check([b]), Check([c])) for (a, b, c) in self.mults] # type: ignore (No idea how to get __init__ to typecheck :/)
        # Step 2:
        #  a
        eta_rng = Rng(seeds[0])
        eta = [Check.sample(eta_rng) for _ in mults]
        #  b
        x = list(map(gmul, eta, [x for x, _, _ in mults]))
        y = [y for _, y, _ in mults]
        z = gsum(map(gmul, eta, [z for _, _, z in mults]))

        # Step 3
        round = 1 # Start at 1 to skip the dummy
        while len(x) > 1:
            assert len(x) % NU == 0
            #  a
            length = len(x) // NU
            a = [x[i * length:(i + 1) * length] for i in range(NU)]
            b = [y[i * length:(i + 1) * length] for i in range(NU)]

            #  b
            c = [self.get_hint(Check) for _ in range(NU)]

            #  c
            x, y, z = self.compress(a, b, c, length == 1, Check.sample(Rng(seeds[round])))

            round += 1

        # Step 4
        rec = self.open(x[0])

        # Step 5:
        self.open(rec * y[0] - z)

    def verify(self, circuit: Circuit):
        """
            Follows Figure 1 for a single party
            Verify that a single party acted honestly by re-running its part in the protocol.
            Returns the shares opened by the party for later checking of the consistency of openings.
        """
        # Input
        inputs_: list[InputT] = [self.get_hint(Input) for _ in range(circuit.ninputs)]
        ringcheck_mask: InputT = self.get_hint(Input)
        self.assert_commitment()

        # Step 1
        inputs: list[WitnessT] = self.ring_check(inputs_, ringcheck_mask)

        extwit: list[WitnessT] = [self.get_hint(Witness) for _ in range(circuit.nmults)][::-1]
        self.assert_commitment()

        # Step 2
        wires = inputs[:]
        for gate in circuit:
            match gate:
                case ("MUL", a, b):
                    c = extwit.pop()
                    self.mults.append((wires[a], wires[b], c))
                    wires.append(c)
                case ("ADD", a, b):
                    c = wires[a] + wires[b]
                    wires.append(c)
                case ("INV", a):
                    wires.append(Witness.one()-wires[a])
                case x:
                    assert False, f"Unknown gate: {x}"

        # Step 3
        for o in circuit.outputs:
            self.open(wires[o])

        # Step 4
        for seeds in self.mulcheck_seeds:
            self.mul_check(seeds)

        assert not self.comms_to_check
        assert not self.opened_values
