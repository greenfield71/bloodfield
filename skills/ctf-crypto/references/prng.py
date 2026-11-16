#!/usr/bin/env python3
"""PRNG state recovery for CTF crypto.

MT19937 (Python's random): recover full state from 624 consecutive 32-bit
outputs, then predict.
LCG: recover (a, c) [and unknown m] from consecutive states.
Permutation inversion: undo deterministic PRNG shuffles.

Usage:
    python3 -I prng.py --test
    from prng import untemper, clone_mt, recover_lcg, undo_shuffle

Deps: stdlib only.
"""
import random
import sys
from math import gcd


# ---------- MT19937 ----------
def _undo_right_xor(y, shift):
    """Invert  y = x ^ (x >> shift)  for 32-bit x."""
    x = 0
    for bit in range(31, -1, -1):            # MSB -> LSB
        xb = (y >> bit) & 1
        if bit + shift < 32:
            xb ^= (x >> (bit + shift)) & 1
        x |= xb << bit
    return x


def _undo_left_xor_and(y, shift, mask):
    """Invert  y = x ^ ((x << shift) & mask)  for 32-bit x."""
    x = 0
    for bit in range(32):                    # LSB -> MSB
        xb = (y >> bit) & 1
        if bit - shift >= 0:
            xb ^= ((x >> (bit - shift)) & 1) & ((mask >> bit) & 1)
        x |= xb << bit
    return x & 0xFFFFFFFF


def untemper(y):
    """Invert MT19937's tempering to get a raw state word from one 32-bit output."""
    y = _undo_right_xor(y, 18)
    y = _undo_left_xor_and(y, 15, 0xEFC60000)
    y = _undo_left_xor_and(y, 7, 0x9D2C5680)
    y = _undo_right_xor(y, 11)
    return y & 0xFFFFFFFF


def clone_mt(outputs):
    """outputs = 624 consecutive getrandbits(32) values -> a cloned random.Random."""
    assert len(outputs) >= 624, "need >=624 consecutive 32-bit outputs"
    state = tuple(untemper(o) for o in outputs[:624])
    r = random.Random()
    r.setstate((3, state + (624,), None))   # index 624 forces a regen on next draw
    return r


# ---------- LCG ----------
def _modinv(a, m):
    return pow(a, -1, m)


def recover_lcg(states, m=None):
    """states: consecutive LCG outputs s0,s1,s2,...  Returns (a, c, m).

    s_{n+1} = (a*s_n + c) mod m. Needs >=3 states if m known; if m is None,
    recover it from >=4 states (e.g. 6-10 states) via gcd of t-products.
    """
    s = states
    if m is None:
        t = [s[i + 1] - s[i] for i in range(len(s) - 1)]
        zeroes = [t[i + 1] * t[i - 1] - t[i] * t[i] for i in range(1, len(t) - 1)]
        m = 0
        for z in zeroes:
            m = gcd(m, abs(z))
        if m == 0:
            raise ValueError("could not recover modulus; need more states")
    a = (s[2] - s[1]) * _modinv((s[1] - s[0]) % m, m) % m
    c = (s[1] - a * s[0]) % m
    return a, c, m


# ---------- Permutation Inversion ----------
def invert_permutation(perm):
    """Invert a permutation list where perm[i] is the destination index."""
    inv = [0] * len(perm)
    for i, p in enumerate(perm):
        inv[p] = i
    return inv


def undo_shuffle(data, seed, rounds=1):
    """Undo deterministic random.shuffle() rounds when seed is known (e.g. UMassCTF)."""
    data = list(data)
    n = len(data)
    round_perms = []
    for r in range(rounds):
        rng = random.Random(seed * (r + 1))
        indices = list(range(n))
        rng.shuffle(indices)
        round_perms.append(indices)
    for indices in reversed(round_perms):
        inv = invert_permutation(indices)
        data = [data[inv[i]] for i in range(n)]
    return bytes(data) if isinstance(data[0], int) else data


def run_tests():
    """Self-test suite for PRNG state recovery and helpers."""
    print("=== PRNG Self-Tests ===")

    # 1. MT19937 clone test
    seed_rng = random.Random(1337)
    outs = [seed_rng.getrandbits(32) for _ in range(624)]
    cloned = clone_mt(outs)
    assert all(cloned.getrandbits(32) == seed_rng.getrandbits(32) for _ in range(20))
    print("[ok] MT19937 clone predicts next outputs")

    # 2. LCG with known modulus
    m, a, c, x = 2**31 - 1, 1103515245, 12345, 42
    seq = []
    for _ in range(6):
        x = (a * x + c) % m
        seq.append(x)
    ra, rc, rm = recover_lcg(seq, m=m)
    assert (ra, rc) == (a, c)
    print("[ok] LCG params recovered (known m)")

    # 3. LCG with unknown modulus
    seq_long = []
    x = 1337
    for _ in range(10):
        x = (a * x + c) % m
        seq_long.append(x)
    ra2, rc2, rm2 = recover_lcg(seq_long, m=None)
    assert (ra2, rc2, rm2) == (a, c, m)
    print("[ok] LCG params & modulus recovered (unknown m)")

    # 4. Deterministic shuffle inversion
    orig = b"flag{prng_shuffle_inverted_cleanly}"
    shuffled = list(orig)
    for r in range(3):
        rng = random.Random(999 * (r + 1))
        rng.shuffle(shuffled)
    unshuffled = undo_shuffle(shuffled, 999, rounds=3)
    assert unshuffled == orig
    print("[ok] undo_shuffle inversion")

    print("ALL PRNG TESTS PASSED!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_tests()
        sys.exit(0)

    # Default run executes tests
    run_tests()
