---
name: ctf-crypto
description: >-
  Cryptography CTF challenges. Use for RSA attacks (small e, common modulus,
  Wiener, Hastad, Franklin-Reiter, structured/close primes, factordb), AES mode
  misuse (ECB byte-at-a-time, CBC bit-flip, padding oracle), XOR & chained CBC-XOR,
  classical ciphers, hash cracking (hashcat/john), lattice+Babai (fplll, CVP, HNP),
  PRNG state recovery (MT19937 untemper/unshuffle, LCG unknown modulus, shuffle undo),
  isogeny & tree-path walks (CM curves, Cayley graphs, backtracking filter),
  and advanced/academic primitives (FHE/CKKS/TenSEAL, zk-SNARK/Groth16/gnark,
  multivariate/UOV, Winternitz OTS, knapsack/subset-sum, plactic monoid, Dickson)
  in SageMath and Python. Triggers on: "RSA", "cipher", "encrypt", "AES", "ECB",
  "CBC", "padding oracle", "XOR", "modulus", "n e c", "Vigenere", "hash", "crack",
  "crypto", "key", "factordb", "Wiener", "Hastad", "Franklin-Reiter", "private key",
  "ciphertext", "FHE", "CKKS", "TenSEAL", "zk-SNARK", "SNARK", "Groth16", "gnark",
  "lattice", "fplll", "fpylll", "Babai", "CVP", "HNP", "hidden number problem",
  "LLL", "MT19937", "Mersenne", "LCG", "knapsack", "Merkle-Hellman", "Oil and Vinegar",
  "UOV", "multivariate", "WOTS", "Winternitz", "Lamport", "hash chain", "plactic",
  "Dickson", "isogeny", "isogenies", "j-invariant", "tree walk", "Cayley",
  "structured primes", "shuffle inversion", "SageMath", "Sage", "PoW", "proof of work".
---

# CTF Crypto

Python toolkit: `pycryptodome` (`from Crypto...`), `sympy`, `gmpy2`, `pwntools`
for remote oracles. **SageMath** is central for anything lattice/polynomial/
algebraic. Install on Arch (check `command -v` first; install nothing silently):

```bash
command -v python3 && pip install --user pycryptodome gmpy2 sympy pwntools requests
command -v sage    || paru -S sagemath fplll          # Sage + fplll (lattice/Babai)
# optional/special:
# command -v tenseal || pip install --user tenseal    # FHE/CKKS (+ Microsoft SEAL)
# command -v go      || sudo pacman -S go             # zk-SNARK uses gnark (Go)
# factoring: paru -S yafu   ; web: http://factordb.com
# hash cracking: sudo pacman -S hashcat john ; wordlist: rockyou (AUR: rockyou)
```

Run analysis scripts with `python3 -I`. Reference scripts live in `references/`:
- `references/rsa.py`: small e, factordb, fermat, common modulus, hastad, wiener, pollard p-1, structured primes ($p=2^k-a$), shared factor gcd, franklin-reiter.
- `references/aes.py`: detect_ecb, cbc_bitflip, padding_oracle_decrypt.
- `references/prng.py`: MT19937 untemper & clone, LCG recovery (known/unknown modulus), undo_shuffle.
- `references/xor_classical.py`: single_byte_xor, repeating_key_xor, cbc_xor_decrypt (chained XOR), caesar, rot13, rot47.
- `references/lattice_cvp.py`: pure Python exact LLL, Gram-Schmidt, Babai nearest-plane CVP, fplll CLI wrapper, solve_hnp, solve_subset_sum_knapsack.
- `references/academic_pqc.py`: wots_forge_forward, solve_uov_linearization, plactic_multiply & Schensted insertion, bidirectional_tree_search.
- `references/advanced.md`: detailed formulas, threat models, and code patterns for 2025–2026 academic primitives.

All scripts support `--test` mode (`python3 -I references/<script>.py --test`) with passing self-tests.

**Anti-AI meta note:** Modern crypto challenges lean on academic primitives and PoW gating.
Identify the *algebraic structure* first, reach for Sage/Python helpers, then invert.
Many services are **PoW-gated** (pwn.red/kCTF/hashcash) — solve the PoW before the real interaction.

## Triage

1. `grep`/read the challenge for `n`, `e`, `c`, `p`, `q`, `d`, PEM blocks, or a described scheme.
   Identify category: RSA? AES? XOR? classical? hash? lattice? PRNG? academic (FHE/SNARK/multivariate/WOTS/knapsack/isogeny)?
2. Count ciphertext size / alphabet. Hex? base64? Decode first.
3. Remote service (`nc`) that encrypts/decrypts on demand → **oracle attack** (padding oracle, CBC bit-flip, ECB, FHE sign oracle). PoW banner first? Solve the PoW before looping.
4. Given a hash → `hashid`/`hashcat --identify`, then crack.
5. Imports `tenseal`/`gnark`/`fpylll`, mentions a monoid/polynomial ring/isogeny/knapsack, or provides a lattice basis → **academic / modern primitives** (`references/advanced.md`).

---

## Decision Matrix — Attack Selection

| You see | Primitive / Vulnerability | First move & Tool |
|---|---|---|
| `n, e, c`, factors on factordb | **RSA trivial factor** | `references/rsa.py factordb` |
| Small $e$ (3), unpadded $m^e < n$ | **RSA small root** | `references/rsa.py iroot` (`gmpy2.iroot`) |
| Same $m, e$ under $e$ distinct $N_i$ | **Hastad Broadcast** | `references/rsa.py hastad` (CRT + root) |
| Two ciphertexts, same $n$, coprime $e_1, e_2$ | **Common Modulus** | `references/rsa.py common_modulus` (Bézout) |
| $d < \frac{1}{3} n^{1/4}$, $e$ large | **Wiener's Attack** | `references/rsa.py wiener` (convergents) |
| $p, q$ close | **Fermat Factorization** | `references/rsa.py fermat` |
| $p = 2^k - a, q = 2^m - b$ for small $a, b$ | **Structured Primes** | `references/rsa.py structured_primes_power_of_two` |
| Leaked fingerprint/diagnostic sharing factor | **Prime Reuse GCD** | `references/rsa.py gcd_factor` |
| Same $n$, $m_2 = a \cdot m_1 + b$ | **Franklin-Reiter** | `references/rsa.py franklin_reiter` |
| Repeated 16-byte ciphertext blocks | **AES-ECB mode** | `references/aes.py detect_ecb`, byte-at-a-time |
| CBC encryption, modify next plaintext block | **CBC Bit-Flip** | `references/aes.py cbc_bitflip` |
| Padding validity error leak (valid/invalid) | **Padding Oracle** | `references/aes.py padding_oracle_decrypt` |
| Chained image XOR ($P_i = C_i \oplus C_{i-1}$) | **CBC-style XOR** | `references/xor_classical.py cbc_xor_decrypt` |
| English ciphertext, single key byte | **Single-byte XOR** | `references/xor_classical.py single_byte_xor` |
| Repeating key XOR / Vigenère | **Repeating-key XOR** | `references/xor_classical.py repeating_key_xor_break` |
| 624 32-bit outputs from `random` | **MT19937 State Clone** | `references/prng.py untemper`, `clone_mt` |
| Shuffled MT19937 outputs | **MT19937 Dependency Graph**| Twist relation hypergraph $\to$ graph-iso $\to$ clone |
| 3+ consecutive LCG states ($m$ unknown) | **LCG Modulus Recovery** | `references/prng.py recover_lcg(states, m=None)` |
| Flag bits shuffled $k$ times with seeded RNG | **Shuffle Inversion** | `references/prng.py undo_shuffle` |
| Closest vector target $t$ to lattice basis $B$ | **Babai Nearest-Plane** | `references/lattice_cvp.py babai_nearest_plane` / `fplll -a cvp` |
| Biased nonces in ECDSA/DSA ($t_i \alpha - k_i \equiv u_i$) | **Hidden Number Problem (HNP)** | `references/lattice_cvp.py solve_hnp` (Kannan embedding) |
| Subset sum $S = \sum x_i a_i$ with $x_i \in \{0, 1\}$ | **Low-Density Knapsack** | `references/lattice_cvp.py solve_subset_sum_knapsack` |
| TenSEAL / CKKS float sign oracle | **FHE Sign Oracle** | Binary search via scalar subtraction (`advanced.md`) |
| Groth16 zk-SNARK with $\delta = \lambda \cdot \gamma$ | **Weak CRS Forgery** | BSGS on $G_2 \to \lambda \to$ cancel terms via $C'$ (`advanced.md`) |
| Quadratic equations over $GF(p)$ without oil-oil | **Multivariate (UOV)** | `references/academic_pqc.py solve_uov_linearization` |
| Winternitz hash chain, target digits $d'_i \ge d_i$ | **WOTS Forward Forgery** | `references/academic_pqc.py wots_forge_forward` |
| Schensted row insertion / Young tableaux DH | **Plactic Monoid DH** | `references/academic_pqc.py plactic_multiply` |
| Permutation polynomial $D_k(x, a)$ over $GF(2^{128})$ | **Dickson S-Box** | Inverse polynomial $D_m$ with $m \equiv k^{-1} \pmod{q^2-1}$ |
| CM curve isogeny graph, conductor $2^{128}$ | **Isogeny Tree Walk** | `references/academic_pqc.py bidirectional_tree_search` |

---

## Code Patterns

### 1. RSA Attacks (`references/rsa.py`)
```python
from rsa import iroot, fermat, common_modulus, hastad, wiener, franklin_reiter, structured_primes_power_of_two

# Small e integer root
m = iroot(c, e=3)

# Franklin-Reiter related messages: m2 = a*m1 + b (mod n)
m1_int = franklin_reiter(c1, c2, n, a=1, b=100, e=3)

# Structured primes near powers of two: n = (2^k - a)(2^m - b)
p, q = structured_primes_power_of_two(n, k=607, m=521)
```

### 2. Lattice & CVP (`references/lattice_cvp.py`)
```python
from lattice_cvp import babai_nearest_plane, solve_hnp, solve_subset_sum_knapsack

# Solve Closest Vector Problem (CVP)
closest_vector = babai_nearest_plane(basis_matrix, target_vector)

# Recover secret scalar from biased samples: t_i * alpha - k_i = u_i (mod q)
alpha = solve_hnp(t_samples, u_samples, q)

# Solve low-density subset sum knapsack
bits = solve_subset_sum_knapsack(weights, target_sum)
```

### 3. PRNG State Recovery (`references/prng.py`)
```python
from prng import untemper, clone_mt, recover_lcg, undo_shuffle

# Clone MT19937 and predict all future outputs
rng = clone_mt(outputs_624)
next_int = rng.getrandbits(32)

# Recover unknown modulus and multiplier of LCG
a, c, m = recover_lcg(states, m=None)

# Invert deterministic bit/byte shuffle
orig_bytes = undo_shuffle(shuffled_bytes, seed=1337, rounds=10)
```

### 4. Academic & Post-Quantum (`references/academic_pqc.py`)
```python
from academic_pqc import wots_forge_forward, solve_uov_linearization, plactic_multiply, bidirectional_tree_search

# Forging Winternitz OTS signatures forward
forged_sig = wots_forge_forward(m0_digits, sig0, target_digits)

# Multivariate UOV linearization by fixing vinegar variables
sol = solve_uov_linearization(equations, num_vinegar=2, num_oil=2, p=79, vinegar_guess=[5, 12])

# Isogeny graph path recovery with backtracking filter
path = bidirectional_tree_search(start_j, goal_j, neighbor_fn)
```

### 5. Remote Oracle Template with PoW Solving
```python
from pwn import remote

io = remote("host", 1337)
# If a PoW banner appears first (kCTF / pwn.red / hashcash):
# solve it using ctf-misc pow_solver before interacting
io.recvuntil(b"> ")
io.sendline(payload)
resp = io.recvline().strip()
```
