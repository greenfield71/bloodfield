#!/usr/bin/env python3
"""RSA attack toolkit for CTF.

Attacks included:
- factordb(n) - query factordb.com
- fermat(n) - factor n when p, q are close
- iroot(c, e) - small e integer root when m**e < n
- common_modulus(n, e1, e2, c1, c2) - same n, coprime e1, e2
- hastad(ns, cs, e) - Hastad broadcast attack (CRT + e-th root)
- wiener(e, n) - Wiener continued fraction attack for small d
- pollard_pm1(n) - Pollard p-1 factorisation for smooth p-1
- franklin_reiter(c1, c2, n, a, b, e) - related message attack (m2 = a*m1 + b)
- structured_primes_power_of_two(n, k, m) - primes near powers of two (p=2^k-a, q=2^m-b)
- gcd_factor(n, leak) - factor n when a shared factor with leak exists

Usage:
    python3 -I rsa.py --test
    from rsa import wiener, hastad, common_modulus, franklin_reiter

Deps: pycryptodome, gmpy2, sympy, requests.
"""
import sys
from math import gcd, isqrt, comb

try:
    import gmpy2
except ImportError:
    gmpy2 = None
from Crypto.Util.number import long_to_bytes, inverse


def decrypt(c, d, n):
    return long_to_bytes(pow(c, d, n))


def from_pq(c, e, p, q):
    phi = (p - 1) * (q - 1)
    d = inverse(e, phi)
    return long_to_bytes(pow(c, d, n=p * q))


def iroot(c, e):
    """Unpadded small-e: m = e-th root of c when m**e < n."""
    if gmpy2:
        r, ok = gmpy2.iroot(c, e)
        return long_to_bytes(int(r)) if ok else None
    # pure-python fallback
    lo, hi = 0, 1 << ((c.bit_length() // e) + 2)
    while lo < hi:
        mid = (lo + hi) // 2
        if mid ** e < c:
            lo = mid + 1
        else:
            hi = mid
    return long_to_bytes(lo) if lo ** e == c else None


def factordb(n):
    """Query factordb.com for known factors."""
    import requests
    r = requests.get("http://factordb.com/api", params={"query": str(n)}, timeout=15)
    data = r.json()
    factors = []
    for base, power in data.get("factors", []):
        factors += [int(base)] * int(power)
    return factors if len(factors) >= 2 and factors[0] != n else None


def fermat(n):
    """Factor n when p and q are close."""
    a = isqrt(n)
    if a * a < n:
        a += 1
    while True:
        b2 = a * a - n
        b = isqrt(b2)
        if b * b == b2:
            return a - b, a + b
        a += 1


def gcd_factor(n, leak):
    """Factor n if leak shares a prime factor with n."""
    g = gcd(n, leak)
    if 1 < g < n:
        return g, n // g
    return None


def common_modulus(n, e1, e2, c1, c2):
    """Same n, two coprime exponents, same plaintext."""
    g, a, b = _egcd(e1, e2)
    assert g == 1, "e1,e2 not coprime"
    if a < 0:
        c1 = inverse(c1, n)
        a = -a
    if b < 0:
        c2 = inverse(c2, n)
        b = -b
    return long_to_bytes(pow(c1, a, n) * pow(c2, b, n) % n)


def hastad(ns, cs, e):
    """Hastad broadcast: same m sent to e recipients with exponent e."""
    from sympy.ntheory.modular import crt
    M, _ = crt(ns, cs)
    return iroot(int(M), e)


def wiener(e, n):
    """Wiener's attack: small private exponent d < (1/3) * n^(1/4)."""
    for k, dg in _convergents(e, n):
        if k == 0:
            continue
        if (e * dg - 1) % k:
            continue
        phi = (e * dg - 1) // k
        s = n - phi + 1
        disc = s * s - 4 * n
        if disc >= 0:
            t = isqrt(disc)
            if t * t == disc and (s + t) % 2 == 0:
                return dg  # recovered private exponent
    return None


def pollard_pm1(n, bound=2 ** 20):
    a = 2
    for j in range(2, bound):
        a = pow(a, j, n)
        d = gcd(a - 1, n)
        if 1 < d < n:
            return d, n // d
    return None


def structured_primes_power_of_two(n, k, m):
    """Factor n = (2^k - a)(2^m - b) where a, b are small offsets (e.g. L3akCTF RSA Eclipse).
    Assumes k != m, say k > m, and small offsets a < 2^(k-m), ab < 2^m.
    Returns (p, q).
    """
    if k < m:
        k, m = m, k
    ab = n % (1 << m)
    S = ((1 << (k + m)) - n) + ab
    val = S >> m
    a = val % (1 << (k - m))
    b = (val - a) >> (k - m)
    p = (1 << k) - a
    q = (1 << m) - b
    if p * q == n:
        return p, q
    # Check swapped
    p2 = (1 << k) - b
    q2 = (1 << m) - a
    if p2 * q2 == n:
        return p2, q2
    return None


# ---------- Polynomial GCD for Franklin-Reiter ----------

def _poly_sub(p1, p2, mod):
    deg = max(len(p1), len(p2))
    res = [0] * deg
    for i in range(deg):
        v1 = p1[i] if i < len(p1) else 0
        v2 = p2[i] if i < len(p2) else 0
        res[i] = (v1 - v2) % mod
    while len(res) > 1 and res[-1] == 0:
        res.pop()
    return res


def _poly_divmod(p1, p2, mod):
    inv_lc = inverse(p2[-1], mod)
    p1 = list(p1)
    quot = [0] * max(1, len(p1) - len(p2) + 1)
    while len(p1) >= len(p2) and (len(p1) > 1 or p1[0] != 0):
        deg_diff = len(p1) - len(p2)
        factor = (p1[-1] * inv_lc) % mod
        quot[deg_diff] = factor
        sub = [0] * deg_diff + [(c * factor) % mod for c in p2]
        p1 = _poly_sub(p1, sub, mod)
    return quot, p1


def _poly_gcd_modn(p1, p2, mod):
    while len(p2) > 1 or (len(p2) == 1 and p2[0] != 0):
        _, rem = _poly_divmod(p1, p2, mod)
        p1, p2 = p2, rem
    inv_lc = inverse(p1[-1], mod)
    return [(c * inv_lc) % mod for c in p1]


def franklin_reiter(c1, c2, n, a, b, e=3):
    """Franklin-Reiter related message attack:
    c1 = m1^e mod n
    c2 = (a*m1 + b)^e mod n
    Returns recovered m1 as integer (or bytes if decode=True).
    """
    g1 = [-c1 % n] + [0] * (e - 1) + [1]
    g2 = [0] * (e + 1)
    for k in range(e + 1):
        g2[k] = (comb(e, k) * pow(a, k, n) * pow(b, e - k, n)) % n
    g2[0] = (g2[0] - c2) % n
    g = _poly_gcd_modn(g1, g2, n)
    if len(g) == 2 and g[1] == 1:
        return (-g[0]) % n
    return None


def _egcd(a, b):
    if b == 0:
        return a, 1, 0
    g, x, y = _egcd(b, a % b)
    return g, y, x - (a // b) * y


def _convergents(e, n):
    cf = []
    a, b = e, n
    while b:
        cf.append(a // b)
        a, b = b, a % b
    num0, num1 = 0, 1
    den0, den1 = 1, 0
    for q in cf:
        num0, num1 = num1, q * num1 + num0
        den0, den1 = den1, q * den1 + den0
        yield num1, den1


def run_tests():
    """Self-test suite for RSA attacks."""
    print("=== RSA Self-Tests ===")

    # 1. iroot
    msg = b"small_root"
    m_int = int.from_bytes(msg, "big")
    c = pow(m_int, 3)
    assert iroot(c, 3) == msg
    print("[ok] iroot (unpadded small e)")

    # 2. Fermat
    p_close = 1000000007
    q_close = 1000000009
    p_rec, q_rec = fermat(p_close * q_close)
    assert {p_rec, q_rec} == {p_close, q_close}
    print("[ok] fermat factorization")

    # 3. Common modulus
    from Crypto.Util.number import getPrime
    p_cm = getPrime(64); q_cm = getPrime(64); n_cm = p_cm * q_cm
    e1, e2 = 17, 19
    msg_cm = b"secret_cm"
    m_cm = int.from_bytes(msg_cm, "big")
    c1, c2 = pow(m_cm, e1, n_cm), pow(m_cm, e2, n_cm)
    assert common_modulus(n_cm, e1, e2, c1, c2) == msg_cm
    print("[ok] common modulus")

    # 4. Hastad broadcast
    from Crypto.Util.number import getPrime
    ps = [getPrime(128) for _ in range(3)]
    qs = [getPrime(128) for _ in range(3)]
    ns = [ps[i] * qs[i] for i in range(3)]
    e = 3
    secret = b"broadcast_msg"
    m_b = int.from_bytes(secret, "big")
    cs = [pow(m_b, e, ni) for ni in ns]
    assert hastad(ns, cs, e) == secret
    print("[ok] hastad broadcast")

    # 5. Wiener
    p_w = getPrime(256)
    q_w = getPrime(256)
    n_w = p_w * q_w
    phi_w = (p_w - 1) * (q_w - 1)
    d_small = 10007
    e_w = inverse(d_small, phi_w)
    assert wiener(e_w, n_w) == d_small
    print("[ok] wiener small d")

    # 6. Pollard p-1
    # p-1 is smooth
    p_smooth = 2 * 3 * 5 * 7 * 11 * 13 + 1
    while not sympy_isprime(p_smooth):
        p_smooth += 2 * 3 * 5 * 7 * 11 * 13
    q_rand = getPrime(64)
    d_fac, _ = pollard_pm1(p_smooth * q_rand)
    assert d_fac in (p_smooth, q_rand)
    print("[ok] pollard p-1")

    # 7. Structured primes near powers of two (RSA Eclipse)
    k, m_pow = 607, 521
    a_off, b_off = 13371337, 73317331
    p_pow = (1 << k) - a_off
    q_pow = (1 << m_pow) - b_off
    n_pow = p_pow * q_pow
    rec_p, rec_q = structured_primes_power_of_two(n_pow, k, m_pow)
    assert {rec_p, rec_q} == {p_pow, q_pow}
    print("[ok] structured primes near powers of two")

    # 8. Shared GCD factor (JerseyCTF TX-7)
    leak = p_pow * 9999991
    f1, f2 = gcd_factor(n_pow, leak)
    assert {f1, f2} == {p_pow, q_pow}
    print("[ok] gcd factor via leak")

    # 9. Franklin-Reiter related messages
    p_fr = getPrime(128)
    q_fr = getPrime(128)
    n_fr = p_fr * q_fr
    m1 = int.from_bytes(b"flag{rel_msg}", "big")
    a_rel = 3
    b_rel = 1337
    m2 = (a_rel * m1 + b_rel) % n_fr
    c1_fr = pow(m1, 3, n_fr)
    c2_fr = pow(m2, 3, n_fr)
    rec_m1 = franklin_reiter(c1_fr, c2_fr, n_fr, a_rel, b_rel, e=3)
    assert rec_m1 == m1
    assert long_to_bytes(rec_m1) == b"flag{rel_msg}"
    print("[ok] franklin-reiter related messages")

    print("ALL RSA TESTS PASSED!")


def sympy_isprime(n):
    from sympy import isprime
    return isprime(n)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_tests()
        sys.exit(0)

    print("RSA toolkit ready. Run with --test to verify attacks, or import functions.")
    print("Available: factordb, fermat, iroot, common_modulus, hastad, wiener, pollard_pm1,")
    print("           structured_primes_power_of_two, gcd_factor, franklin_reiter.")
