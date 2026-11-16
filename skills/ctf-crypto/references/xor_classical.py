#!/usr/bin/env python3
"""XOR and classical-cipher helpers for CTF.

Functions:
- single_byte_xor(ct)
- repeating_key_xor_break(ct)
- cbc_xor_decrypt(ct, key) / cbc_xor_encrypt(pt, key) - chained XOR (BlueHens CTF)
- caesar_all(text)
- rot13(s), rot47(s)

Usage:
    python3 -I xor_classical.py --test
    python3 -I xor_classical.py <file-with-ciphertext-bytes-or-hex>
    from xor_classical import single_byte_xor, repeating_key_xor_break, cbc_xor_decrypt

Deps: stdlib only.
"""
import sys
from itertools import cycle

ENGLISH = b"ETAOIN SHRDLUetaoin shrdlu"  # rough frequency weighting


def xor_bytes(a, b):
    return bytes(x ^ y for x, y in zip(a, cycle(b)))


def score(bs):
    return sum(ENGLISH.count(bytes([c])) for c in bs) + sum(1 for c in bs if 32 <= c < 127)


def single_byte_xor(ct):
    """Brute force single-byte XOR key (0-255) scored by English frequency."""
    best = (None, -1, None)
    for k in range(256):
        pt = bytes(c ^ k for c in ct)
        s = score(pt)
        if s > best[1]:
            best = (k, s, pt)
    return best  # (key_byte, score, plaintext)


def _hamming(a, b):
    return sum(bin(x ^ y).count("1") for x, y in zip(a, b))


def _keysize(ct, lo=2, hi=40):
    results = []
    for ks in range(lo, min(hi, len(ct) // 4) + 1):
        chunks = [ct[i * ks:(i + 1) * ks] for i in range(4)]
        dist = (_hamming(chunks[0], chunks[1]) + _hamming(chunks[1], chunks[2]) +
                _hamming(chunks[2], chunks[3])) / 3 / ks
        results.append((dist, ks))
    return [ks for _, ks in sorted(results)[:5]]


def repeating_key_xor_break(ct):
    """Break repeating-key XOR using Hamming distance keysize estimation."""
    for ks in _keysize(ct):
        key = bytearray()
        for col in range(ks):
            column = ct[col::ks]
            key.append(single_byte_xor(column)[0])
        pt = xor_bytes(ct, bytes(key))
        yield bytes(key), pt


def cbc_xor_decrypt(ct: bytes, key: int) -> bytes:
    """CBC-style chained XOR decryption (e.g. BlueHens CTF XORDECRYPT):
    P[0] = C[0] ^ key
    P[i] = C[i] ^ C[i-1]
    """
    if not ct:
        return b""
    pt = bytearray(len(ct))
    pt[0] = ct[0] ^ key
    for i in range(1, len(ct)):
        pt[i] = ct[i] ^ ct[i - 1]
    return bytes(pt)


def cbc_xor_encrypt(pt: bytes, key: int) -> bytes:
    """CBC-style chained XOR encryption:
    C[0] = P[0] ^ key
    C[i] = P[i] ^ C[i-1]
    """
    if not pt:
        return b""
    ct = bytearray(len(pt))
    ct[0] = pt[0] ^ key
    for i in range(1, len(pt)):
        ct[i] = pt[i] ^ ct[i - 1]
    return bytes(ct)


def caesar_all(text):
    """Generate all 26 Caesar shift variants."""
    out = {}
    for sh in range(26):
        out[sh] = "".join(
            chr((ord(c) - base + sh) % 26 + base) if c.isalpha()
            else c
            for c in text for base in [65 if c.isupper() else 97]
        )
    return out


def rot13(s):
    import codecs
    return codecs.encode(s, "rot13")


def rot47(s):
    return "".join(chr(33 + (ord(c) - 33 + 47) % 94) if 33 <= ord(c) <= 126 else c for c in s)


def run_tests():
    """Self-test suite for classical ciphers and XOR helpers."""
    print("=== XOR & Classical Self-Tests ===")

    # 1. Single-byte XOR
    pt_sample = b"Flag{Single_Byte_XOR_Secret_Found}"
    key_sb = 0x5A
    ct_sb = bytes(c ^ key_sb for c in pt_sample)
    rec_k, _, rec_pt = single_byte_xor(ct_sb)
    assert rec_k == key_sb
    assert rec_pt == pt_sample
    print("[ok] single_byte_xor")

    # 2. Repeating-key XOR
    rep_key = b"KEY"
    long_pt = b"The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog again and again."
    ct_rep = xor_bytes(long_pt, rep_key)
    guesses = list(repeating_key_xor_break(ct_rep))
    assert any(g[0] == rep_key for g in guesses)
    print("[ok] repeating_key_xor_break")

    # 3. CBC-style chained XOR
    msg_cbc = b"Flag{Chained_CBC_XOR_Decrypted}"
    ct_cbc = cbc_xor_encrypt(msg_cbc, 0x67)
    dec_cbc = cbc_xor_decrypt(ct_cbc, 0x67)
    assert dec_cbc == msg_cbc
    print("[ok] cbc_xor_decrypt")

    # 4. Caesar, ROT13, ROT47
    plain_txt = "Hello World"
    assert rot13(rot13(plain_txt)) == plain_txt
    assert rot47(rot47(plain_txt)) == plain_txt
    c_all = caesar_all("abc")
    assert c_all[1] == "bcd"
    print("[ok] caesar, rot13, rot47")

    print("ALL XOR & CLASSICAL TESTS PASSED!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_tests()
        sys.exit(0)

    if len(sys.argv) < 2:
        print("usage: python3 -I xor_classical.py <file-with-ciphertext-bytes-or-hex> [--test]")
        sys.exit(0)

    raw = open(sys.argv[1], "rb").read().strip()
    try:
        data = bytes.fromhex(raw.decode())
    except ValueError:
        data = raw
    print("[single-byte]", single_byte_xor(data))
    print("[repeating-key best guesses]")
    for key, pt in repeating_key_xor_break(data):
        print("  key=", key, "->", pt[:60])
