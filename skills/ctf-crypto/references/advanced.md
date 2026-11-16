# Advanced & Academic Cryptography — Primitives & Code Patterns

Mainstreamed in 2025–2026 CTF majors (UIUCTF, L3akCTF, VuwCTF, SECCON, BuckeyeCTF).
Standard rule: **Recognize the algebraic structure → Identify broken assumption → Load SageMath / Python toolkit → Invert it.**

---

## 1. FHE — CKKS Sign / Comparison Oracle (TenSEAL)
- **Seen at:** UIUCTF 2026 (*positive-thinking*).
- **Tell:** `tenseal` / Microsoft SEAL context, CKKS scheme (approximate floating point), remote service evaluates a polynomial or ciphertext and returns only the **sign** ($\text{sign}(x)$) or comparison ($\pm 1$).
- **Vulnerability:** Ciphertexts are malleable under the public context. An oracle that leaks $\text{sign}(T_8(x / 2^{49}))$ or $\text{sign}(x - c)$ leaks exactly 1 bit of plaintext information per query without decryption keys.
- **Attack Strategy:**
  1. Use coarse root search over Chebyshev polynomial $T_n(x)$ roots to isolate the interval.
  2. Perform fine binary search: shift ciphertext $C' = C - c$ or double ciphertext $C' = 2 \cdot C$ (homomorphic addition preserves the modulus level without noise budget burn).
  3. 50 queries recover a 50-bit secret float/integer.
- **Code Pattern (TenSEAL / Python):**
```python
import tenseal as ts

# Load public context from server
ctx = ts.context_from(public_context_bytes)
# To test hypothesis c without consuming scale:
# Server evaluates eval_poly(C - c) and returns sign
def query_sign(c_offset_encrypted):
    io.sendline(c_offset_encrypted.serialize().hex().encode())
    return int(io.recvline().strip())  # +1 or -1

# Binary search loop
low, high = 0.0, 1.0
for _ in range(50):
    mid = (low + high) / 2.0
    # Add plain scalar -mid to encrypted secret
    shifted = enc_secret - mid
    if query_sign(shifted) > 0:
        low = mid
    else:
        high = mid
secret = (low + high) / 2.0
```

---

## 2. zk-SNARK — Groth16 Weak CRS Trapdoor Forgery
- **Seen at:** L3akCTF 2026 (*1+1=3*).
- **Tell:** `gnark` (Go), `py_ecc`, Groth16 verification over BN254 / BLS12-381 curves, verification key provided, objective is to forge a proof for an invalid statement (e.g. prove $1+1=3$).
- **Vulnerability:** Weak Common Reference String (CRS). If verification key parameters satisfy $\delta = \lambda \cdot \gamma$ with small or smooth $\lambda$, the discrete logarithm can be solved in $G_1 / G_2$.
- **Attack Strategy:**
  1. Extract $\gamma, \delta \in G_2$ from verification key.
  2. Solve $\delta = \lambda \cdot \gamma$ using Baby-Step Giant-Step (BSGS) over $G_2$ (or Sage `discrete_log`).
  3. Groth16 pairing equation: $e(A, B) = e(\alpha, \beta) + e(K_{stmt}, \gamma) + e(C, \delta)$.
  4. With $\lambda$ known, $e(C, \delta) = e(\lambda \cdot C, \gamma)$. Any term in $K_{stmt}$ can be cancelled or forged by adjusting $C' = C - \lambda^{-1} \cdot K_{target}$.
  5. Craft proof with zero randomizers ($r=0, s=0$), setting $A = \alpha$, $B = \beta$, cancelling false statement inputs in $C$.
- **Code Pattern (SageMath / Go gnark):**
```python
# SageMath — BSGS recovery of lambda
# E is the BN254 G2 curve
gamma = E_G2(vk.gamma)
delta = E_G2(vk.delta)
# If lambda < 2^40:
lam = delta.discrete_log(gamma)  # baby-step giant-step
inv_lam = inverse_mod(lam, r)     # r = group order

# Proof forgery:
# Target modifies public input index 3 (cancelling +1)
C_forged = C - int(inv_lam) * vk.K[3]
```

---

## 3. Multivariate PQC — Unbalanced Oil-and-Vinegar (UOV)
- **Seen at:** L3akCTF 2026 (*Immiscible*).
- **Tell:** System of quadratic equations over finite field $GF(p)$ (e.g. $GF(79)$) where variables are partitioned into $v$ vinegar variables and $o$ oil variables ($v \ge o$).
- **Key Property:** No oil $\times$ oil terms exist ($Q_{i, oj, ok} = 0$). Equations are of the form:
  $$\sum a_{jk} v_j v_k + \sum b_{jk} v_j o_k + \sum c_j v_j + \sum d_k o_k + e = 0 \pmod p$$
- **Attack Strategy:**
  1. Fix / enumerate vinegar variables $v \in GF(p)^v$ (for small $p^v$ like $79^2$ or $79^3$ or through targeted subspaces).
  2. Once vinegar variables are fixed to constants, every equation becomes strictly **linear** in oil variables: $M(v) \cdot o = b(v) \pmod p$.
  3. Solve the resulting linear system via Gaussian elimination over $GF(p)$ using `references/academic_pqc.py` (`solve_uov_linearization`).
- **Code Pattern:**
```python
from academic_pqc import solve_uov_linearization

# Enumerate candidate vinegar assignments
for v0 in range(p):
    for v1 in range(p):
        sol = solve_uov_linearization(equations, num_vinegar=2, num_oil=2, p=p, vinegar_guess=[v0, v1])
        if sol is not None:
            print("Recovered full secret vector [v || o]:", sol)
            break
```

---

## 4. Hash-Based Signatures — Winternitz OTS (WOTS) Forward Forgery
- **Seen at:** BuckeyeCTF 2025 (*nitwit*).
- **Tell:** Hash-based one-time signature with parameter $w$, message digits $d_i \in [0, w-1]$, public key $y_i = H^{w-1}(x_i)$, signature $\sigma_i = H^{d_i}(x_i)$.
- **Vulnerability:** Forward-chaining malleability. Anyone who holds signature $\sigma_i = H^{d_i}(x_i)$ can compute $H^{d'_i}(x_i)$ for any $d'_i \ge d_i$ simply by applying $H$ an additional $(d'_i - d_i)$ times!
- **Attack Strategy:**
  1. Request signature for chosen message $m_0$ having small digits $d_i$ (e.g. zeros).
  2. For target message $m_{target}$, ensure all digits $d'_i \ge d_i$ (if checksum is appended, manipulate padding or message chunks so checksum digit is also $\ge$).
  3. Apply `wots_forge_forward(m0_digits, sig0, target_digits)` from `references/academic_pqc.py`.

---

## 5. Exotic Non-Commutative Algebra — Plactic Monoid DH
- **Seen at:** UIUCTF 2026 (*Young Cryptography*).
- **Tell:** Key exchange protocol defined over words or Young Tableaux using Schensted row insertion / Robinson-Schensted-Knuth (RSK) algorithm.
- **Key Property:** The plactic monoid is associative and weakly cancellative. Tableau product $A \cdot B$ is formed by row-inserting the reading word of $B$ into $A$.
- **Attack Strategy:**
  1. Monico probabilistic left-division: given $C = A \cdot B$ and $A$, invert Schensted bumping from bottom to top to peel off letters of $B$.
  2. Implement Schensted insertion using `references/academic_pqc.py` (`schensted_insert`, `plactic_multiply`).
  3. Derive shared key from tableau representation (e.g. SHA-256 of flattened tableau rows).

---

## 6. Permutation Polynomials — Dickson Polynomials over Finite Fields
- **Seen at:** VuwCTF 2026 (*D*).
- **Tell:** Custom block cipher nonlinear layer / S-box defined over $GF(2^{128})$ via Dickson polynomials $D_k(x, a)$.
- **Key Property:** For $x = u + a/u$, $D_k(x, a) = u^k + (a/u)^k$. Over $GF(q)$ with $q = 2^{128}$, $D_k(x, a)$ is a permutation polynomial iff $\gcd(k, q^2 - 1) = 1$.
- **Inverse:**
  $$D_k^{-1}(x, a) = D_m(x, a^k) \quad \text{where } m \equiv k^{-1} \pmod{q^2 - 1}$$
- **Code Pattern (SageMath):**
```python
# SageMath — Inverting Dickson polynomial layer over GF(2^128)
F = GF(2^128, 'a')
q = 2^128
order = q^2 - 1
m = inverse_mod(k, order)
# Inverse of y = D_k(x, alpha):
# x = D_m(y, alpha^k)
```

---

## 7. Lattice CVP & Babai Nearest-Plane
- **Seen at:** L3akCTF 2026 (*A Fine Product*).
- **Tell:** Hidden number problem, truncated LCG, affine map compositions $F(s) = a \cdot s + b \pmod M$, low-density knapsacks, Coppersmith small roots.
- **Tools:** `fplll` CLI (`fplll -a cvp`), `fpylll` in Sage, or `references/lattice_cvp.py`.
- **Babai Nearest-Plane Algorithm:**
  1. Reduce basis $B$ using LLL.
  2. Compute Gram-Schmidt orthogonal basis $B^*$.
  3. For $i = n-1 \dots 0$: project target onto $B^*_i$, round to nearest integer $c_i = \lfloor \frac{\langle w, B^*_i \rangle}{\|B^*_i\|^2} \rceil$, update $w \leftarrow w - c_i B_i$.
  4. Output closest lattice vector $v = t - w$.
- **Code Pattern (`references/lattice_cvp.py`):**
```python
from lattice_cvp import babai_nearest_plane, solve_hnp, solve_subset_sum_knapsack

# 1. Direct CVP on custom lattice basis
closest = babai_nearest_plane(basis_matrix, target_vector)

# 2. Hidden Number Problem (ECDSA biased nonces / truncated multiplier)
alpha = solve_hnp(t_samples, u_samples, modulus_q)

# 3. Merkle-Hellman Subset Sum
secret_bits = solve_subset_sum_knapsack(public_weights, target_sum)
```

---

## 8. Isogeny & Cayley Graph Tree Walks
- **Seen at:** SECCON CTF 14 Quals (*Last Flight*).
- **Tell:** Elliptic curves over $GF(p)$ with CM (Complex Multiplication), conductor $f = 2^{128}$ (binary tree structure of depth 128), degree-2 isogenies between $j$-invariants.
- **Key Property:** Degree-$\ell$ isogeny neighbors can be found by solving the modular polynomial $\Phi_\ell(X, j) = 0 \pmod p$. In a tree structure of depth $h$, each step has $\le 3$ neighbors, where 1 is the backtrack (parent).
- **Attack Strategy:**
  1. Filter out immediate predecessor: $\text{codomain}.j \ne \text{visited}[-2]$.
  2. Use bidirectional meet-in-the-middle tree search (`bidirectional_tree_search` from `academic_pqc.py`).
  3. Reconstruct full sequence of choice indices (flight plan) from start curve to destination curve.
- **Code Pattern (SageMath / Python):**
```python
# Sage modular polynomial neighbor generator
R.<X> = PolynomialRing(GF(p))
def neighbors(j, prev=None):
    poly = classical_modular_polynomial(2, X, j)
    roots = [int(r) for r in poly.roots(multiplicities=False)]
    return [r for r in roots if r != prev]

from academic_pqc import bidirectional_tree_search
path = bidirectional_tree_search(vulcan_j, bell_j, neighbors, max_depth=160)
```

---

## 9. PRNG State Cloning & Output Reordering
- **Seen at:** L3akCTF 2026 (*po1337nomial-revenge*), UMassCTF 2026 (*The Accursed Lego Bin*).
- **Tell:** MT19937 outputs given out of order, or repeated deterministic `random.shuffle()` applied to secret flag bits.
- **Attack Strategy:**
  1. **Untempering:** Invert MT19937 output masks (`references/prng.py` `untemper`).
  2. **Shuffled MT19937:** Build adjacency graph of twist relations ($x_k = x_{k+1} \oplus \dots$) across output indices, solve graph isomorphism to recover chronological sequence, then clone via `clone_mt`.
  3. **Shuffle Inversion:** Invert each round's permutation in reverse order (`undo_shuffle` from `references/prng.py`).
- **Code Pattern (`references/prng.py`):**
```python
from prng import untemper, clone_mt, recover_lcg, undo_shuffle

# 1. Clone MT19937
rng = clone_mt(consecutive_624_outputs)
predicted_token = rng.getrandbits(32)

# 2. Recover LCG with unknown modulus
a, c, m = recover_lcg(observed_states, m=None)

# 3. Undo deterministic shuffles
recovered_bytes = undo_shuffle(shuffled_flag_bytes, seed=known_seed, rounds=10)
```
