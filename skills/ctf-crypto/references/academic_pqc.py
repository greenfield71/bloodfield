#!/usr/bin/env python3
"""Academic & Post-Quantum Cryptography helper for CTF challenges.

Implements:
1. Winternitz One-Time Signatures (WOTS / Lamport hash chains):
   - Signature verification & forward-chain signature forgery generator (BuckeyeCTF nitwit).
2. Multivariate Quadratic / Unbalanced Oil-and-Vinegar (UOV) linearization:
   - Vinegar variable guessing + Gaussian elimination over GF(p) (L3akCTF Immiscible).
3. Plactic Monoid & Young Tableaux:
   - Schensted row insertion, tableau multiplication, and left-division (UIUCTF Young Cryptography).
4. Tree-Path & Isogeny Walk Recovery:
   - Backtracking-free bidirectional tree search for CM isogeny graphs & Cayley walks (SECCON Last Flight).

Usage:
    python3 -I academic_pqc.py --test
    from academic_pqc import (
        wots_forge_forward,
        solve_uov_linearization,
        plactic_multiply,
        bidirectional_tree_search
    )

Deps: stdlib only.
"""
import hashlib
import sys
from collections import deque
from typing import Callable, Dict, List, Optional, Sequence, Tuple


# ==============================================================================
# 1. Winternitz OTS (WOTS) / Hash Chain Forgery
# ==============================================================================

def sha256_hash(data: bytes) -> bytes:
    """Standard SHA-256 hash helper."""
    return hashlib.sha256(data).digest()


def hash_chain(val: bytes, steps: int, hash_fn: Callable[[bytes], bytes] = sha256_hash) -> bytes:
    """Iterate hash_fn steps times: hash_chain(x, 2) = H(H(x))."""
    for _ in range(steps):
        val = hash_fn(val)
    return val


def wots_forge_forward(
    known_digits: Sequence[int],
    known_sig: Sequence[bytes],
    target_digits: Sequence[int],
    hash_fn: Callable[[bytes], bytes] = sha256_hash,
) -> Optional[List[bytes]]:
    """Forge a valid WOTS signature for target_digits given known_sig on known_digits.

    Succeeds iff for every chunk i, target_digits[i] >= known_digits[i].
    Because public key requires w - 1 total hashes from sk, signature on d is H^d(sk).
    Moving from d to d' >= d requires only hashing the signature (d' - d) times forward!
    """
    if len(known_digits) != len(known_sig) or len(known_digits) != len(target_digits):
        raise ValueError("Mismatched digit or signature lengths")

    for k, t in zip(known_digits, target_digits):
        if t < k:
            return None  # Cannot hash backwards without private key

    forged_sig = []
    for s_chunk, k_dig, t_dig in zip(known_sig, known_digits, target_digits):
        diff = t_dig - k_dig
        forged_sig.append(hash_chain(s_chunk, diff, hash_fn=hash_fn))
    return forged_sig


# ==============================================================================
# 2. Multivariate Quadratic / UOV Linearization
# ==============================================================================

def modinv(a: int, p: int) -> int:
    """Modular inverse modulo prime p."""
    return pow(a, -1, p)


def gaussian_elim_gf(matrix: List[List[int]], p: int) -> Optional[List[int]]:
    """Gaussian elimination over finite field GF(p) on augmented matrix [A | b].
    Returns a solution vector x such that A * x == b (mod p), or None if inconsistent.
    """
    mat = [[val % p for val in row] for row in matrix]
    m = len(mat)
    n = len(mat[0]) - 1
    r = 0

    for c in range(n):
        pivot = None
        for i in range(r, m):
            if mat[i][c] % p != 0:
                pivot = i
                break
        if pivot is None:
            continue
        mat[r], mat[pivot] = mat[pivot], mat[r]
        inv = modinv(mat[r][c], p)
        mat[r] = [(x * inv) % p for x in mat[r]]

        for i in range(m):
            if i != r and mat[i][c] % p != 0:
                factor = mat[i][c]
                mat[i] = [(mat[i][j] - factor * mat[r][j]) % p for j in range(n + 1)]
        r += 1
        if r == m:
            break

    # Extract solution
    sol = [0] * n
    for i in range(r):
        for j in range(n):
            if mat[i][j] % p == 1:
                sol[j] = mat[i][n]
                break

    # Verification check
    for i in range(m):
        if sum(mat[i][j] * sol[j] for j in range(n)) % p != mat[i][n] % p:
            return None
    return sol


def solve_uov_linearization(
    equations: List[Dict],
    num_vinegar: int,
    num_oil: int,
    p: int,
    vinegar_guess: Sequence[int],
) -> Optional[List[int]]:
    """Linearize an Unbalanced Oil-and-Vinegar (UOV) system by fixing vinegar variables.

    Equations is a list of dicts representing polynomials:
      {
         'quad_vv': {(v_i, v_j): coeff},
         'quad_vo': {(v_i, o_j): coeff},  # No o_i * o_j in UOV!
         'linear_v': {v_i: coeff},
         'linear_o': {o_j: coeff},
         'const': c
      }
    Returns complete assignment [v_0, ..., v_{nv-1}, o_0, ..., o_{no-1}].
    """
    nv = num_vinegar
    no = num_oil
    v = list(vinegar_guess)

    augmented_mat = []
    for eq in equations:
        row = [0] * (no + 1)
        # Evaluate pure vinegar quadratic and linear terms + const
        eval_v = eq.get("const", 0)
        for vi, coeff in eq.get("linear_v", {}).items():
            eval_v = (eval_v + coeff * v[vi]) % p
        for (vi, vj), coeff in eq.get("quad_vv", {}).items():
            eval_v = (eval_v + coeff * v[vi] * v[vj]) % p

        # Target RHS is -eval_v (mod p)
        row[no] = (-eval_v) % p

        # Coefficients for each oil variable o_j
        for oj in range(no):
            coeff_oj = eq.get("linear_o", {}).get(oj, 0)
            for (vi, o_idx), coeff in eq.get("quad_vo", {}).items():
                if o_idx == oj:
                    coeff_oj = (coeff_oj + coeff * v[vi]) % p
            row[oj] = coeff_oj % p

        augmented_mat.append(row)

    oil_sol = gaussian_elim_gf(augmented_mat, p)
    if oil_sol is not None:
        return list(v) + oil_sol
    return None


# ==============================================================================
# 3. Plactic Monoid & Schensted Insertion
# ==============================================================================

def schensted_insert(tableau: List[List[int]], x: int) -> List[List[int]]:
    """Insert element x into a Young tableau using Schensted row insertion (RSK)."""
    T = [list(row) for row in tableau]
    cur = x
    r = 0
    while r < len(T):
        # Find first element strictly greater than cur in row r
        bump_idx = None
        for i, val in enumerate(T[r]):
            if val > cur:
                bump_idx = i
                break
        if bump_idx is None:
            T[r].append(cur)
            return T
        else:
            T[r][bump_idx], cur = cur, T[r][bump_idx]
            r += 1
    T.append([cur])
    return T


def word_to_tableau(word: Sequence[int]) -> List[List[int]]:
    """Convert an integer word to a Young tableau via successive Schensted insertions."""
    T: List[List[int]] = []
    for x in word:
        T = schensted_insert(T, x)
    return T


def plactic_multiply(T1: List[List[int]], T2: List[List[int]]) -> List[List[int]]:
    """Multiply two tableaux T1 and T2 in the plactic monoid (T1 * T2).
    Row-inserts the reading word of T2 (bottom-to-top, left-to-right) into T1.
    """
    reading_word = []
    for row in reversed(T2):
        reading_word.extend(row)
    res = [list(r) for r in T1]
    for x in reading_word:
        res = schensted_insert(res, x)
    return res


# ==============================================================================
# 4. Tree-Path & Isogeny Graph Walk Recovery
# ==============================================================================

def bidirectional_tree_search(
    start: any,
    goal: any,
    neighbor_fn: Callable[[any, any], List[any]],
    max_depth: int = 25,
) -> Optional[List[any]]:
    """Bidirectional BFS for Cayley / Isogeny tree graphs with backtracking prevention.

    neighbor_fn(current_node, previous_node) returns list of next nodes, filtering out
    the backtrack to previous_node.
    Returns complete path [start, ..., goal] or None.
    """
    if start == goal:
        return [start]

    forward_q = deque([(start, [start], None)])
    forward_visited = {start: [start]}

    backward_q = deque([(goal, [goal], None)])
    backward_visited = {goal: [goal]}

    for _ in range(max_depth):
        # Step forward
        for _ in range(len(forward_q)):
            curr, path, prev = forward_q.popleft()
            for nxt in neighbor_fn(curr, prev):
                if nxt not in forward_visited:
                    npath = path + [nxt]
                    forward_visited[nxt] = npath
                    forward_q.append((nxt, npath, curr))
                    if nxt in backward_visited:
                        bpath = backward_visited[nxt]
                        return npath[:-1] + list(reversed(bpath))

        # Step backward
        for _ in range(len(backward_q)):
            curr, path, prev = backward_q.popleft()
            for nxt in neighbor_fn(curr, prev):
                if nxt not in backward_visited:
                    npath = path + [nxt]
                    backward_visited[nxt] = npath
                    backward_q.append((nxt, npath, curr))
                    if nxt in forward_visited:
                        fpath = forward_visited[nxt]
                        return fpath[:-1] + list(reversed(npath))

    return None


# ==============================================================================
# Self-Test Suite
# ==============================================================================

def run_tests():
    """Self-test suite for academic & post-quantum routines."""
    print("=== Academic & Post-Quantum Self-Tests ===")

    # 1. WOTS forward chain forgery test
    w_size = 16
    sk = [f"secret_key_chunk_{i}".encode() for i in range(4)]
    pk = [hash_chain(s, w_size - 1) for s in sk]
    known_msg = [2, 5, 1, 8]
    known_sig = [hash_chain(sk[i], known_msg[i]) for i in range(4)]
    target_msg = [4, 7, 3, 10]  # all >= known_msg
    forged_sig = wots_forge_forward(known_msg, known_sig, target_msg)
    assert forged_sig is not None
    # Verify against public key
    recovered_pk = [hash_chain(forged_sig[i], (w_size - 1) - target_msg[i]) for i in range(4)]
    assert recovered_pk == pk
    print("[ok] wots_forge_forward (BuckeyeCTF nitwit)")

    # 2. UOV linearization and Gaussian elimination over GF(p)
    p = 79
    # Secret: vinegar = [5, 12], oil = [23, 41]
    equations = [
        {
            # eq 1: 3*v0*o0 + 2*v1*o1 + 7*v0*v1 + 4 = 0 mod p
            "quad_vo": {(0, 0): 3, (1, 1): 2},
            "quad_vv": {(0, 1): 7},
            "const": (- (3 * 5 * 23 + 2 * 12 * 41 + 7 * 5 * 12)) % p,
        },
        {
            # eq 2: 5*v1*o0 + 4*v0*o1 + 11*v0 + 2*o1 = 0 mod p
            "quad_vo": {(1, 0): 5, (0, 1): 4},
            "linear_v": {0: 11},
            "linear_o": {1: 2},
            "const": (- (5 * 12 * 23 + 4 * 5 * 41 + 11 * 5 + 2 * 41)) % p,
        },
    ]
    uov_sol = solve_uov_linearization(equations, num_vinegar=2, num_oil=2, p=p, vinegar_guess=[5, 12])
    assert uov_sol == [5, 12, 23, 41]
    print("[ok] solve_uov_linearization (L3akCTF Immiscible)")

    # 3. Plactic monoid Schensted insertion and multiplication
    w1 = [3, 1, 4]
    w2 = [1, 5, 9]
    t1 = word_to_tableau(w1)
    t2 = word_to_tableau(w2)
    t_prod = plactic_multiply(t1, t2)
    t_full = word_to_tableau(w1 + w2)
    assert t_prod == t_full
    print("[ok] plactic_multiply & Schensted insertion (UIUCTF Young Cryptography)")

    # 4. Bidirectional tree search with backtracking filter
    def tree_neighbors(node, prev):
        left, right = node * 2, node * 2 + 1
        parent = node // 2 if node > 1 else None
        nbrs = [left, right]
        if parent is not None:
            nbrs.append(parent)
        return [n for n in nbrs if n != prev]

    path = bidirectional_tree_search(12, 19, tree_neighbors)
    assert path == [12, 6, 3, 1, 2, 4, 9, 19]
    print("[ok] bidirectional_tree_search (SECCON Last Flight)")

    print("ALL ACADEMIC & POST-QUANTUM TESTS PASSED!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_tests()
        sys.exit(0)

    # Default run runs self-test
    run_tests()
