#!/usr/bin/env python3
"""Flexible LSB (least-significant-bit) extraction for CTF stego.

Images:  python3 -I lsb.py image.png
Audio:   python3 -I lsb.py --audio sound.wav
Test:    python3 -I lsb.py --test

Tries common channel orders / bit counts and prints any printable runs.
When you know the scheme (e.g. zsteg said 'b1,rgb,lsb'), use extract() directly.
Deps: pip install --user pillow numpy
"""
import os
import sys


def _bits_to_bytes(bits):
    out = bytearray()
    for i in range(0, len(bits) - 7, 8):
        byte = 0
        for b in bits[i:i + 8]:
            byte = (byte << 1) | b
        out.append(byte)
    return bytes(out)


def _printable_runs(data, minlen=6):
    import re
    return [m.decode("latin1") for m in re.findall(rb"[\x20-\x7e]{%d,}" % minlen, data)]


def extract_image(path):
    from PIL import Image
    import numpy as np
    img = Image.open(path).convert("RGBA")
    arr = np.array(img)
    results = {}
    channel_sets = {"r": [0], "g": [1], "b": [2], "rgb": [0, 1, 2],
                    "bgr": [2, 1, 0], "a": [3]}
    for name, chans in channel_sets.items():
        for order, label in ((arr, "xy"), (np.transpose(arr, (1, 0, 2)), "yx")):
            for nbits in (1, 2):
                bits = []
                flat = order.reshape(-1, 4)
                for px in flat:
                    for c in chans:
                        for bit in range(nbits):
                            bits.append((int(px[c]) >> bit) & 1)
                data = _bits_to_bytes(bits)
                runs = _printable_runs(data)
                hits = [r for r in runs if any(k in r.lower() for k in
                        ("flag", "ctf{", "{", "http"))]
                if hits:
                    results[f"{name},{label},b{nbits}"] = hits
    return results


def extract_audio(path):
    import wave
    import numpy as np
    w = wave.open(path, "rb")
    frames = w.readframes(w.getnframes())
    sw = w.getsampwidth()
    dtype = {1: np.uint8, 2: np.int16, 4: np.int32}[sw]
    samples = np.frombuffer(frames, dtype=dtype)
    out = {}
    for nbits in (1, 2):
        bits = []
        for s in samples:
            for bit in range(nbits):
                bits.append((int(s) >> bit) & 1)
        data = _bits_to_bytes(bits)
        runs = _printable_runs(data)
        if runs:
            out[f"audio,b{nbits}"] = runs[:20]
    return out


def extract(path, channels="rgb", order="xy", nbits=1):
    """Deterministic single-scheme extraction (when you know it)."""
    from PIL import Image
    import numpy as np
    arr = np.array(Image.open(path).convert("RGBA"))
    if order == "yx":
        arr = np.transpose(arr, (1, 0, 2))
    idx = {"r": [0], "g": [1], "b": [2], "rgb": [0, 1, 2], "bgr": [2, 1, 0]}[channels]
    bits = []
    for px in arr.reshape(-1, 4):
        for c in idx:
            for bit in range(nbits):
                bits.append((int(px[c]) >> bit) & 1)
    return _bits_to_bytes(bits)


def extract_length_prefixed(path, channels="r", order="xy", nbits=1, prefix_bits=16):
    """Length-prefixed single-channel LSB (a 2026 flavor, e.g. STARPWN / UIUCTF).

    First `prefix_bits` bits = big-endian payload length in BYTES, MSB-first;
    then that many bytes follow in the same bit stream. Default = red channel,
    16-bit length prefix — the scheme zsteg misses.
    """
    data = extract(path, channels=channels, order=order, nbits=nbits)
    bitstream = []
    for byte in data:
        for bit in range(8):
            bitstream.append((byte >> (7 - bit)) & 1)
    n = 0
    for b in bitstream[:prefix_bits]:
        n = (n << 1) | b
    payload_bits = bitstream[prefix_bits:prefix_bits + n * 8]
    return _bits_to_bytes(payload_bits)


def _self_test():
    from PIL import Image
    import numpy as np

    # Synthetic image with 16-bit length-prefixed flag in red channel
    msg = b"flag{numpy_lsb_verified}"
    prefix_bits = 16
    length = len(msg)
    bits = []
    for i in range(prefix_bits - 1, -1, -1):
        bits.append((length >> i) & 1)
    for byte in msg:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)

    arr = np.zeros((32, 32, 4), dtype=np.uint8)
    flat = arr.reshape(-1, 4)
    for idx, bit in enumerate(bits):
        flat[idx, 0] = (flat[idx, 0] & 0xFE) | bit

    test_png = "/tmp/_test_lsb.png"
    img = Image.fromarray(arr)
    img.save(test_png)

    try:
        res = extract_length_prefixed(test_png, channels="r", prefix_bits=16)
        assert res == msg, f"Extracted mismatch: {res} != {msg}"
        print(f"[ok] lsb self-test passed: extracted length-prefixed payload '{res.decode()}'")
    finally:
        if os.path.exists(test_png):
            os.remove(test_png)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)
    if args[0] == "--test":
        _self_test()
    elif args[0] == "--audio":
        res = extract_audio(args[1])
        for scheme, hits in res.items():
            print(f"[{scheme}]")
            for h in hits:
                print("   ", h)
    else:
        res = extract_image(args[0])
        if not res:
            print("No obvious LSB hits. Try zsteg -a, other channel orders, or 2+ bits.")
        for scheme, hits in res.items():
            print(f"[{scheme}]")
            for h in hits:
                print("   ", h)
