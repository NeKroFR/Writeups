from galois_ring import RingElement
from params import gsum, gmul, commitment, N

def interpolation_coeffs[T: RingElement](eval_point: T, interp_points: list[T]) -> list[T]:
    """
        Lagrange interpolation: return the coefficients `(λ_1, ..., λ_m)`
        such that `λ_1 * y_1 + ... + λ_m + y_m` is the evaluation in `eval_point`
        of the interpolating polynomial on the points `(interp_points[i], y_i)`
    """
    res = []
    for i in range(len(interp_points)):
        numerator = eval_point.one()
        denominator = eval_point.one()
        for j in range(len(interp_points)):
            if i == j:
                continue
            numerator *= eval_point - interp_points[j]
            denominator *= interp_points[i] - interp_points[j]
        res.append(numerator / denominator)
    return res

def check_openings(openings: dict[int, list[RingElement]], open_claims: list[RingElement], comm: bytes):
    assert len(set(map(len, openings.values()))) == 1
    assert min(set(map(len, openings.values()))) == len(open_claims)
    party_indices = [x + 1 for x in sorted(openings.keys())]
    party_indices.insert(0, 0)

    coeff_map = {}
    for c in open_claims:
        if str(type(c)) in coeff_map: continue
        coeff_map[str(type(c))] = [interpolation_coeffs(c.exseq(i), list(map(c.exseq, party_indices))) for i in range(N + 1)]

    all_shares = []
    for i, value in enumerate(open_claims):
        points = [value] + [openings[party][i] for party in sorted(openings.keys())]
        all_shares.extend([gsum(map(gmul, cs, points)) for cs in coeff_map[str(type(value))]])

    assert commitment(all_shares) == comm

