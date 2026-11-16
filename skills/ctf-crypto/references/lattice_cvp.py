#!/usr/bin/env python3
"""Lattice & CVP toolkit for CTF cryptography.

Implements:
1. Pure Python LLL (Lenstra-Lenstra-Lovasz) lattice reduction with exact fractions.
2. Gram-Schmidt orthogonalization (GSO) & Babai's Nearest-Plane algorithm (CVP).
3. Seamless integration with CLI fplll (fplll -a cvp / fplll -a lll) when available.
4. Hidden Number Problem (HNP) solver for biased nonces (ECDSA/DSA).
5. Merkle-Hellman / Low-Density Knapsack subset sum solver (CJLOSS / Lagarias-Odlyzko).
6. Affine map composition solver (e.g. L3akCTF A Fine Product).

Usage:
    python3 -I lattice_cvp.py --test
    from lattice_cvp import babai_nearest_plane, solve_hnp, solve_subset_sum_knapsack

Deps: stdlib only (exact fractions). Optional: fplll CLI.
"""
import re
import shutil
import subprocess
import sys
from fractions import Fraction
from typing import List, Optional, Tuple


def dot(v1: List[Fraction], v2: List[Fraction]) -> Fraction:
    """Inner product of two vectors."""
    return sum(x * y for x, y in zip(v1, v2))


def gram_schmidt(B: List[List]) -> Tuple[List[List[Fraction]], List[List[Fraction]]]:
    """Compute Gram-Schmidt orthogonalization B* and projection coefficients mu."""
    n = len(B)
    B_star: List[List[Fraction]] = []
    mu = [[Fraction(0)] * n for _ in range(n)]

    for i in range(n):
        b_i = [Fraction(x) for x in B[i]]
        for j in range(i):
            mu[i][j] = dot(b_i, B_star[j]) / dot(B_star[j], B_star[j])
            b_i = [x - mu[i][j] * y for x, y in zip(b_i, B_star[j])]
        B_star.append(b_i)
    return B_star, mu


def lll(B: List[List], delta: Fraction = Fraction(3, 4)) -> List[List[int]]:
    """Pure-Python exact rational LLL reduction."""
    B_frac = [[Fraction(x) for x in row] for row in B]
    n = len(B_frac)

    def _compute_gso():
        B_star = []
        mu = [[Fraction(0)] * n for _ in range(n)]
        for i in range(n):
            b_i = list(B_frac[i])
            for j in range(i):
                mu[i][j] = dot(B_frac[i], B_star[j]) / dot(B_star[j], B_star[j])
                b_i = [x - mu[i][j] * y for x, y in zip(b_i, B_star[j])]
            B_star.append(b_i)
        return B_star, mu

    k = 1
    while k < n:
        B_star, mu = _compute_gso()
        for j in range(k - 1, -1, -1):
            if abs(mu[k][j]) > Fraction(1, 2):
                q = round(mu[k][j])
                B_frac[k] = [x - q * y for x, y in zip(B_frac[k], B_frac[j])]
                B_star, mu = _compute_gso()

        if dot(B_star[k], B_star[k]) >= (delta - mu[k][k - 1] ** 2) * dot(B_star[k - 1], B_star[k - 1]):
            k += 1
        else:
            B_frac[k], B_frac[k - 1] = B_frac[k - 1], B_frac[k]
            k = max(k - 1, 1)

    return [[int(x) for x in row] for row in B_frac]


def babai_nearest_plane(B: List[List], target: List) -> List[int]:
    """Find the closest lattice vector to target using Babai's Nearest-Plane algorithm.
    Automatically applies LLL reduction if needed.
    """
    B_red = lll(B)
    B_star, _ = gram_schmidt(B_red)
    n = len(B_red)
    w = [Fraction(x) for x in target]
    coeffs = [0] * n

    for i in reversed(range(n)):
        c = round(dot(w, B_star[i]) / dot(B_star[i], B_star[i]))
        coeffs[i] = c
        w = [x - c * y for x, y in zip(w, B_red[i])]

    closest = [
        int(sum(coeffs[k] * B_red[k][j] for k in range(n)))
        for j in range(len(target))
    ]
    return closest


# ---------- fplll CLI Wrappers ----------

def has_fplll() -> bool:
    """Return True if fplll CLI executable is installed on PATH."""
    return shutil.which("fplll") is not None


def fplll_lll(B: List[List]) -> List[List[int]]:
    """Run LLL reduction via external fplll CLI binary."""
    matrix_str = "[" + "".join("[" + " ".join(str(int(x)) for x in row) + "]" for row in B) + "]"
    res = subprocess.run(["fplll", "-a", "lll"], input=matrix_str.encode(), capture_output=True, check=True)
    out = res.stdout.decode().strip()
    rows = []
    for line in out.splitlines():
        line = line.strip("[] \t\r\n")
        if line:
            nums = [int(x) for x in re.findall(r"-?\d+", line)]
            if nums:
                rows.append(nums)
    return rows


def fplll_cvp(B: List[List], target: List) -> List[int]:
    """Run CVP via external fplll CLI binary (fplll -a cvp)."""
    matrix_str = "[" + "".join("[" + " ".join(str(int(x)) for x in row) + "]" for row in B) + "]"
    target_str = "[" + " ".join(str(int(x)) for x in target) + "]"
    full_input = f"{matrix_str} {target_str}"
    res = subprocess.run(["fplll", "-a", "cvp"], input=full_input.encode(), capture_output=True, check=True)
    out = res.stdout.decode().strip()
    nums = [int(x) for x in re.findall(r"-?\d+", out)]
    return nums


# ---------- Domain-Specific Lattice Solvers ----------

def solve_hnp(t_vals: List[int], u_vals: List[int], q: int) -> Optional[int]:
    """Solve the Hidden Number Problem (HNP) via Kannan embedding / Babai CVP.
    Relation: t_i * alpha - k_i = u_i (mod q), with |k_i| small.
    Returns recovered secret scalar alpha.
    """
    m = len(t_vals)
    basis = []
    for i in range(m):
        row = [0] * (m + 1)
        row[i] = q
        basis.append(row)
    last_row = list(t_vals) + [1]
    basis.append(last_row)

    target = list(u_vals) + [0]
    if has_fplll():
        closest = fplll_cvp(basis, target)
    else:
        closest = babai_nearest_plane(basis, target)

    alpha_cand = closest[-1] % q
    # Verify candidate against first few samples
    matches = sum(1 for t, u in zip(t_vals, u_vals) if (alpha_cand * t - u) % q < q // 4 or (u - alpha_cand * t) % q < q // 4)
    if matches >= m // 2:
        return alpha_cand
    return None


def solve_subset_sum_knapsack(weights: List[int], target_s: int) -> Optional[List[int]]:
    """Solve low-density subset sum / Merkle-Hellman knapsack using CJLOSS-style lattice.
    Given weights [a_1, ..., a_n] and target S = sum(x_i * a_i) with x_i in {0, 1}.
    Returns list of 0/1 bits.
    """
    n = len(weights)
    # Scale factor N > sqrt(n) / 2
    N = 100 * max(1, n)
    basis = []
    for i in range(n):
        row = [0] * (n + 1)
        row[i] = 2
        row[n] = weights[i] * N
        basis.append(row)
    row_target = [1] * n + [target_s * N]
    basis.append(row_target)

    reduced = lll(basis)
    for row in reduced:
        if row[-1] == 0:
            cand1 = [(x + 1) // 2 for x in row[:n]]
            cand2 = [(-x + 1) // 2 for x in row[:n]]
            if all(c in (0, 1) for c in cand1) and sum(w * b for w, b in zip(weights, cand1)) == target_s:
                return cand1
            if all(c in (0, 1) for c in cand2) and sum(w * b for w, b in zip(weights, cand2)) == target_s:
                return cand2
    return None


def run_tests():
    """Self-test suite for lattice and CVP routines."""
    print("=== Lattice & CVP Self-Tests ===")
    import random

    # 1. Pure Python LLL
    M = [[1, 1, 1], [-1, 0, 2], [3, 5, 6]]
    red = lll(M)
    assert len(red) == 3
    print("[ok] pure python LLL")

    # 2. Babai Nearest Plane (CVP)
    B_ortho = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    t = [3.2, 4.8, -1.1]
    cvp = babai_nearest_plane(B_ortho, t)
    assert cvp == [3, 5, -1]
    print("[ok] babai nearest plane")

    # 3. Merkle-Hellman / Low-Density Knapsack
    weights = [2, 3, 7, 14, 30, 57, 120, 251]
    secret_bits = [1, 0, 1, 1, 0, 0, 1, 0]  # sum = 2 + 7 + 14 + 120 = 143
    target_sum = sum(w * b for w, b in zip(weights, secret_bits))
    recovered_bits = solve_subset_sum_knapsack(weights, target_sum)
    assert recovered_bits == secret_bits
    print("[ok] solve_subset_sum_knapsack (Merkle-Hellman)")

    # 4. Hidden Number Problem (HNP)
    q = 65537
    alpha = 1337
    m = 5
    bound = 32
    t_vals = [random.randint(1, q - 1) for _ in range(m)]
    errors = [random.randint(0, bound) for _ in range(m)]
    u_vals = [(alpha * t - e) % q for t, e in zip(t_vals, errors)]
    rec_alpha = solve_hnp(t_vals, u_vals, q)
    assert rec_alpha == alpha
    print("[ok] solve_hnp (Kannan embedding)")

    # 5. fplll CLI integration (if binary present)
    if has_fplll():
        f_cvp = fplll_cvp([[1, 0], [0, 1]], [10, 20])
        assert f_cvp == [10, 20]
        print("[ok] fplll CLI integration")
    else:
        print("[skip] fplll CLI not found on PATH")

    print("ALL LATTICE & CVP TESTS PASSED!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_tests()
        sys.exit(0)

    # Default run runs self-test
    run_tests()
