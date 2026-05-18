#! /usr/bin/env -S python3 -u
# Reference: https://eprint.iacr.org/2023/1057.pdf

import json
import secrets

from circuit import Circuit
from params import commitment, N, T, TAU_IN, TAU_OUT, CheckT, NU, Check, Input, Witness
from sharing import check_openings
from party import Party


def commit_mulcheck(nmults: int) -> tuple[list[bytes], list[list[bytes]], CheckT]:
    """
        Run enough rounds of getting a new commitment and sending a challenge seed over
        returns a list of seeds, a list of commitments per party, and a the reconstruction claim at the end
    """
    compress_seed = secrets.token_bytes(32)
    print("Compression seed:", compress_seed.hex())
    seeds = [compress_seed]
    comms = []
    while nmults > 1:
        rcomms = json.loads(input("Commitments? "))
        comms.append(list(map(bytes.fromhex, rcomms)))
        seed = secrets.token_bytes(32)
        print("Seed:", seed.hex())
        seeds.append(seed)
        nmults //= NU
    claim = Check(json.loads(input("Rec claim? ")))
    return seeds, comms, claim


def verify(circuit: Circuit):
    """
        Follows Figure 1
        O_R takes a commitment to the current views and gives a seed
        O_H adds to things needing committing
    """
    open_claims = []

    # Commitment before O_R in RingCheck, includes ring check mask
    input_comms = list(map(bytes.fromhex, json.loads(input("Input commitments? "))))
    ring_check_seed = secrets.token_bytes()
    print(f"Ring check rng seed: {ring_check_seed.hex()}")
    # Claimed output from the ring_check protocol (i.e. a Z2k element)
    open_claims.append(Input([Input.base_ring()(json.loads(input("Ring check output claim? ")))])) # type: ignore

    # Commit to the O_H calls in the circuit evaluation
    extwit_comms = list(map(bytes.fromhex, json.loads(input("Extended witness commitments? "))))

    # Zero-check is free, since we know t shares + the output
    for _ in circuit.outputs:
        open_claims.append(Witness.zero())

    mulchecks = [commit_mulcheck(circuit.nmults) for _ in range(TAU_IN)]
    for mc in mulchecks:
        open_claims.append(mc[2]) # The claimed reconstruction of x
        open_claims.append(Check.zero()) # The zero check for the final mult

    # Commit to all the opened shares from everyone
    opening_comm = bytes.fromhex(input("Global opening commitment? "))
    openings = {}
    for _ in range(T):
        party_idx = secrets.randbelow(N)
        if party_idx in openings:
            continue
        view = json.loads(input(f"Open party {party_idx}? "))
        comms_to_check = [input_comms[party_idx], extwit_comms[party_idx]]
        for mc in mulchecks:
            for round in mc[1]:
                comms_to_check.append(round[party_idx])
        party = Party(party_idx, view, ring_check_seed, [mc[0] for mc in mulchecks], comms_to_check, commitment([b"ZK4Z2K", str(circuit)]), open_claims)
        party.verify(circuit)
        openings[party_idx] = party.openings

    check_openings(openings, open_claims, opening_comm)


if __name__ == "__main__":
    print("\n\n\t\t\tProve your Omniscience, Lain.\n\n")

    # Prove knowledge of a key that sends all zeros to all zeros under AES-128 (but mod 2^32, just for fun)
    with open("aes_128.txt") as f:
        CIRCUIT = Circuit.parse(f)
        CIRCUIT.pad(NU)
        CIRCUIT.outputs += list(range(128, 256))
    for _ in range(TAU_OUT):
        verify(CIRCUIT)

    print(open("response.txt").read())
    print(open("flag.txt").read())
