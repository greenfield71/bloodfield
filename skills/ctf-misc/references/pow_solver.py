#!/usr/bin/env python3
"""Reusable proof-of-work solvers for CTF service gating.

Two common families:
  * redpwn / "hashcash"-style: find a suffix whose sha256 has N leading zero bits,
    or the classic "sha256(prefix+X) starts with 0*n" variant.
  * kCTF: the service prints  s = <b64>  and wants  pow(2, 2^d, n)  (VDF-style);
    the official client does this with gmpy2. We reproduce the squaring.

    python3 -I pow_solver.py --test
    from pow_solver import solve_leading_zero_bits, solve_prefix_zeros, solve_kctf

Deps: stdlib (gmpy2 optional, only speeds up kCTF).
"""
import hashlib
import itertools
import re
import sys


def solve_leading_zero_bits(prefix: bytes, bits: int):
    """Find suffix s.t. sha256(prefix + s) has >= `bits` leading zero bits."""
    need_bytes = bits // 8
    rem = bits % 8
    for i in itertools.count():
        s = str(i).encode()
        h = hashlib.sha256(prefix + s).digest()
        if h[:need_bytes] != b"\x00" * need_bytes:
            continue
        if rem == 0 or (h[need_bytes] >> (8 - rem)) == 0:
            return s


def solve_prefix_zeros(prefix: bytes, nzeros: int, hexdigest=True):
    """Find suffix s.t. sha256(prefix + s).hexdigest() starts with '0'*nzeros."""
    target = "0" * nzeros
    for i in itertools.count():
        s = str(i).encode()
        d = hashlib.sha256(prefix + s).hexdigest()
        if d.startswith(target):
            return s


def solve_kctf(challenge: str):
    """kCTF VDF: challenge is 's.<b64 d>.<b64 n>' -> returns the base64 answer.

    Computes x = 2 ; repeat d times: x = x*x mod n ; answer = b64(x).
    """
    import base64
    def _d(b):
        return int.from_bytes(base64.b64decode(b + "=" * (-len(b) % 4)), "big")
    parts = challenge.strip().split(".")
    assert parts[0] == "s" and len(parts) == 3, "not a kctf 's.d.n' challenge"
    d, n = _d(parts[1]), _d(parts[2])
    try:
        import gmpy2
        x = gmpy2.mpz(2)
        for _ in range(d):
            x = gmpy2.powmod(x, 2, n)
        x = int(x)
    except ImportError:
        x = 2
        for _ in range(d):
            x = x * x % n
    return "s." + base64.b64encode(x.to_bytes((x.bit_length() + 7) // 8, "big")).decode()


def auto(banner: str):
    """Best-effort: sniff a banner and return the answer string, or None."""
    m = re.search(r"(s\.[A-Za-z0-9+/=]+\.[A-Za-z0-9+/=]+)", banner)
    if m:
        return solve_kctf(m.group(1))
    m = re.search(r"prefix\s*[:=]?\s*([A-Za-z0-9+/=]+).*?(\d+)\s*zero", banner, re.S)
    if m:
        return solve_prefix_zeros(m.group(1).encode(), int(m.group(2))).decode()
    return None


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        import base64
        s = solve_prefix_zeros(b"abc", 2)
        assert hashlib.sha256(b"abc" + s).hexdigest().startswith("00")
        b = solve_leading_zero_bits(b"xyz", 10)
        h = hashlib.sha256(b"xyz" + b).digest()
        assert h[0] == 0 and (h[1] >> 6) == 0

        # Test kCTF solver (2^(2^3) mod 1000 = 256)
        d_b64 = base64.b64encode((3).to_bytes(1, "big")).decode()
        n_b64 = base64.b64encode((1000).to_bytes(2, "big")).decode()
        kres = solve_kctf(f"s.{d_b64}.{n_b64}")
        assert kres == "s.AQA=", f"kCTF mismatch: {kres}"

        # Test auto sniffing
        banner = f"Challenge: s.{d_b64}.{n_b64} please solve"
        assert auto(banner) == "s.AQA="

        print("[ok] redpwn-style and kCTF PoW solvers work")
    else:
        print(__doc__)
