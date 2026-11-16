#!/usr/bin/env python3
"""CyberChef-style multi-decoder for CTF: auto-detect and recursively peel
encoding layers until readable text (or a flag) appears.

Usage:
    python3 -I multidecode.py 'STRING'
    python3 -I multidecode.py -f blob.txt
    python3 -I multidecode.py --qr grid.txt     # 0/1 (or '#'/' ') grid -> render+scan
    echo 'STRING' | python3 -I multidecode.py -

Deps (optional): pip install --user base58  ; zbarimg + pillow for --qr.
Pure-stdlib for the common bases. Run with -I (isolated) on untrusted input.
"""
import sys
import base64
import binascii
import codecs
import re
import urllib.parse
import html

FLAG_RE = re.compile(rb"[A-Za-z0-9_]{2,}\{[^}]{1,120}\}")


def printable_ratio(b):
    if not b:
        return 0
    return sum(1 for c in b if 9 <= c <= 13 or 32 <= c <= 126) / len(b)


def looks_text(b):
    return printable_ratio(b) > 0.90


# ---------- individual decoders (return bytes or None) ----------
def d_base64(s):
    t = s.strip().replace("\n", "")
    if not re.fullmatch(r"[A-Za-z0-9+/=_-]+", t) or len(t) < 4:
        return None
    try:
        pad = t.replace("-", "+").replace("_", "/")
        pad += "=" * (-len(pad) % 4)
        out = base64.b64decode(pad, validate=False)
        return out if out and printable_ratio(out) > 0.8 else None
    except Exception:
        return None


def d_base32(s):
    t = s.strip().upper().replace("\n", "")
    if not re.fullmatch(r"[A-Z2-7=]+", t) or len(t) < 8:
        return None
    try:
        t += "=" * (-len(t) % 8)
        return base64.b32decode(t)
    except Exception:
        return None


def d_base85(s):
    t = s.strip()
    for fn in (base64.b85decode, base64.a85decode):
        try:
            out = fn(t)
            if looks_text(out):
                return out
        except Exception:
            pass
    return None


def d_base58(s):
    t = s.strip()
    if not re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]+", t):
        return None
    try:
        import base58
        return base58.b58decode(t)
    except Exception:
        return None


def d_hex(s):
    t = re.sub(r"[\s:]", "", s.strip())
    if not re.fullmatch(r"(?:0x)?[0-9a-fA-F]+", t) or len(t) % 2:
        return None
    try:
        return bytes.fromhex(t.removeprefix("0x"))
    except Exception:
        return None


def d_binary(s):
    t = re.sub(r"[\s]", "", s.strip())
    if not re.fullmatch(r"[01]+", t) or len(t) < 8 or len(t) % 8:
        return None
    try:
        return bytes(int(t[i:i + 8], 2) for i in range(0, len(t), 8))
    except Exception:
        return None


def d_decimal(s):
    nums = re.findall(r"\d+", s)
    if len(nums) < 2 or any(int(n) > 255 for n in nums):
        return None
    try:
        return bytes(int(n) for n in nums)
    except Exception:
        return None


def d_url(s):
    if "%" not in s:
        return None
    out = urllib.parse.unquote_to_bytes(s)
    return out if out != s.encode(errors="ignore") else None


def d_html(s):
    if "&" not in s:
        return None
    out = html.unescape(s)
    return out.encode() if out != s else None


def d_rot13(s):
    if not re.search(r"[A-Za-z]", s):
        return None
    return codecs.encode(s, "rot13").encode()


def d_rot47(s):
    out = "".join(chr(33 + (ord(c) - 33 + 47) % 94) if 33 <= ord(c) <= 126 else c for c in s)
    return out.encode() if out != s else None


def d_reverse(s):
    return s.strip()[::-1].encode()


MORSE = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E", "..-.": "F",
    "--.": "G", "....": "H", "..": "I", ".---": "J", "-.-": "K", ".-..": "L",
    "--": "M", "-.": "N", "---": "O", ".--.": "P", "--.-": "Q", ".-.": "R",
    "...": "S", "-": "T", "..-": "U", "...-": "V", ".--": "W", "-..-": "X",
    "-.--": "Y", "--..": "Z", "-----": "0", ".----": "1", "..---": "2",
    "...--": "3", "....-": "4", ".....": "5", "-....": "6", "--...": "7",
    "---..": "8", "----.": "9",
}


def d_morse(s):
    if not re.fullmatch(r"[.\-/ \n]+", s.strip()) or "." not in s:
        return None
    words = re.split(r"\s*/\s*|\s{2,}", s.strip())
    out = []
    for w in words:
        out.append("".join(MORSE.get(c, "?") for c in w.split()))
    return " ".join(out).encode()


def brainfuck(code, inp=b""):
    tape = bytearray(30000)
    ptr = ip = ic = 0
    out = bytearray()
    code = re.sub(r"[^><+\-.,\[\]]", "", code)
    while ip < len(code):
        c = code[ip]
        if c == ">": ptr += 1
        elif c == "<": ptr -= 1
        elif c == "+": tape[ptr] = (tape[ptr] + 1) & 0xff
        elif c == "-": tape[ptr] = (tape[ptr] - 1) & 0xff
        elif c == ".": out.append(tape[ptr])
        elif c == ",":
            tape[ptr] = inp[ic] if ic < len(inp) else 0; ic += 1
        elif c == "[" and tape[ptr] == 0:
            depth = 1
            while depth:
                ip += 1; depth += (code[ip] == "[") - (code[ip] == "]")
        elif c == "]" and tape[ptr] != 0:
            depth = 1
            while depth:
                ip -= 1; depth += (code[ip] == "]") - (code[ip] == "[")
        ip += 1
    return bytes(out)


DECODERS = [
    ("base64", d_base64), ("base32", d_base32), ("base85", d_base85),
    ("base58", d_base58), ("hex", d_hex), ("binary", d_binary),
    ("decimal", d_decimal), ("url", d_url), ("html", d_html),
    ("morse", d_morse), ("rot13", d_rot13), ("rot47", d_rot47),
]


def peel(data, depth=0, trail=()):
    """Recursively try decoders; print anything containing a flag or readable text."""
    s = data.decode("latin1") if isinstance(data, bytes) else data
    raw = data if isinstance(data, bytes) else data.encode("latin1")
    if FLAG_RE.search(raw):
        print(f"[FLAG? via {' -> '.join(trail) or 'raw'}] {raw}")
    if depth >= 8:
        return
    for name, fn in DECODERS:
        try:
            out = fn(s)
        except Exception:
            out = None
        if not out or out == raw:
            continue
        newtrail = trail + (name,)
        if FLAG_RE.search(out):
            print(f"[FLAG? {' -> '.join(newtrail)}] {out}")
            return
        if looks_text(out) and out != raw:
            print(f"[{' -> '.join(newtrail)}] {out[:200]!r}")
            peel(out, depth + 1, newtrail)


def qr_from_grid(path):
    from PIL import Image
    import subprocess
    lines = [ln.rstrip("\n") for ln in open(path) if ln.strip()]
    on = {"1", "#", "█", "*", "X"}
    h, w = len(lines), max(len(l) for l in lines)
    scale = 10
    img = Image.new("1", (w * scale, h * scale), 1)
    px = img.load()
    for y, row in enumerate(lines):
        for x, ch in enumerate(row):
            if ch in on:
                for dy in range(scale):
                    for dx in range(scale):
                        px[x * scale + dx, y * scale + dy] = 0
    out = "/tmp/_qr.png"
    img.save(out)
    print("rendered grid ->", out)
    try:
        print(subprocess.run(["zbarimg", "-q", out], capture_output=True, text=True).stdout)
    except FileNotFoundError:
        print("install zbar (paru -S zbar) then: zbarimg", out)


def _self_test():
    assert d_base64("aGVsbG8=") == b"hello"
    assert d_hex("68656c6c6f") == b"hello"
    assert d_rot13("uryyb") == b"hello"
    assert d_morse(".... . .-.. .-.. ---") == b"HELLO"
    assert d_binary("01101000 01100101 01101100 01101100 01101111") == b"hello"

    bf_hello = "++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++."
    assert brainfuck(bf_hello) == b"Hello World!\n"

    chain = b"aGVsbG9fd29ybGRfdGVzdA=="
    assert d_base64(chain.decode()) == b"hello_world_test"
    print("[ok] multidecode self-tests passed (base64, hex, rot13, morse, binary, brainfuck)")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); return
    if args[0] == "--test":
        _self_test(); return
    if args[0] == "--qr":
        qr_from_grid(args[1]); return
    if args[0] == "-f":
        data = open(args[1], "rb").read().strip()
    elif args[0] == "-":
        data = sys.stdin.buffer.read().strip()
    else:
        data = args[0].encode()
    print(f"[input] {data[:200]!r}")
    peel(data)


if __name__ == "__main__":
    main()
