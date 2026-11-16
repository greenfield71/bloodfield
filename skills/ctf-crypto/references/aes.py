#!/usr/bin/env python3
"""AES mode-misuse helpers for CTF: ECB detection, CBC bit-flip, padding oracle.

Usage:
    python3 -I aes.py --test
    from aes import detect_ecb, cbc_bitflip, padding_oracle_decrypt

Deps: pycryptodome, pwntools.
"""
import sys
from pwn import remote, xor  # pip install --user pwntools


BS = 16


def blocks(data, bs=BS):
    return [data[i:i + bs] for i in range(0, len(data), bs)]


def detect_ecb(ct, bs=BS):
    """True if any 16-byte block repeats (ECB tell)."""
    b = blocks(ct, bs)
    return len(b) != len(set(b))


def cbc_bitflip(prev_ct_block, current_pt, desired_pt):
    """Return the mutated previous ciphertext block (or IV) so that the NEXT
    decrypted plaintext block becomes desired_pt. XOR trick:
      new_prev = prev ^ current_pt ^ desired_pt
    """
    return xor(prev_ct_block, current_pt, desired_pt)


# ---------------- Padding oracle ----------------
# Supply an oracle(ct_bytes)->bool that returns True iff PKCS#7 padding is valid.

def make_oracle(host, port):
    def oracle(ct):
        io = remote(host, port, level="error")
        io.sendlineafter(b"> ", ct.hex().encode())
        ok = b"valid" in io.recvline().lower()  # <-- adapt to the service
        io.close()
        return ok
    return oracle


def padding_oracle_decrypt(ct, oracle, iv=b"\x00" * BS):
    """Decrypt CBC ciphertext using a padding oracle. ct = all ciphertext blocks
    (without IV); pass the real IV if known."""
    cblocks = [iv] + blocks(ct)
    recovered = b""
    for i in range(1, len(cblocks)):
        prev, cur = cblocks[i - 1], cblocks[i]
        inter = bytearray(BS)  # D(cur)
        for pad in range(1, BS + 1):
            forged = bytearray(BS)
            for k in range(1, pad):
                forged[BS - k] = inter[BS - k] ^ pad
            for guess in range(256):
                forged[BS - pad] = guess
                if oracle(bytes(forged) + cur):
                    # guard against the pad==1 false positive
                    if pad == 1 and BS > 1:
                        forged[BS - 2] ^= 1
                        if not oracle(bytes(forged) + cur):
                            forged[BS - 2] ^= 1
                            continue
                        forged[BS - 2] ^= 1
                    inter[BS - pad] = guess ^ pad
                    break
        recovered += xor(bytes(inter), prev)
    # strip PKCS#7
    pad_len = recovered[-1]
    if 1 <= pad_len <= BS and recovered.endswith(bytes([pad_len]) * pad_len):
        return recovered[:-pad_len]
    return recovered


def run_tests():
    """Self-test suite for AES attacks."""
    print("=== AES Self-Tests ===")
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    import os

    # 1. ECB Detection
    key = os.urandom(16)
    cipher_ecb = AES.new(key, AES.MODE_ECB)
    repeated_pt = b"A" * 64
    ct_ecb = cipher_ecb.encrypt(repeated_pt)
    assert detect_ecb(ct_ecb) is True
    assert detect_ecb(os.urandom(64)) is False
    print("[ok] detect_ecb")

    # 2. CBC Bit-Flip
    iv = os.urandom(16)
    pt_orig = b"user=guest;id=10"
    cipher_cbc = AES.new(key, AES.MODE_CBC, iv)
    ct_cbc = cipher_cbc.encrypt(pt_orig)
    pt_desired = b"user=admin;id=10"
    forged_iv = cbc_bitflip(iv, pt_orig, pt_desired)
    cipher_cbc2 = AES.new(key, AES.MODE_CBC, forged_iv)
    pt_flipped = cipher_cbc2.decrypt(ct_cbc)
    assert pt_flipped == pt_desired
    print("[ok] cbc_bitflip")

    # 3. Padding Oracle Decryption
    secret_msg = b"Flag{P4dd1ng_0r4cl3_W0rks}"
    iv_oracle = os.urandom(16)
    padded = pad(secret_msg, BS)
    cipher_oracle = AES.new(key, AES.MODE_CBC, iv_oracle)
    ct_oracle = cipher_oracle.encrypt(padded)

    def mock_oracle(c):
        test_iv = c[:BS]
        test_data = c[BS:]
        dec_cipher = AES.new(key, AES.MODE_CBC, test_iv)
        raw_dec = dec_cipher.decrypt(test_data)
        try:
            unpad(raw_dec, BS)
            return True
        except Exception:
            return False

    decrypted = padding_oracle_decrypt(ct_oracle, mock_oracle, iv=iv_oracle)
    assert decrypted == secret_msg
    print("[ok] padding_oracle_decrypt")

    print("ALL AES TESTS PASSED!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_tests()
        sys.exit(0)

    print("Edit the oracle for your target. Helpers: detect_ecb, cbc_bitflip,")
    print("make_oracle(host,port), padding_oracle_decrypt(ct, oracle, iv).")
    print("Run with --test to verify attacks.")
