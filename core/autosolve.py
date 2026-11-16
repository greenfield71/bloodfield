"""Deterministic, 0-token auto-solver. Knocks out trivial challenges before any LLM/agent
is involved, so they cost nothing. Uses only stdlib + external CLI tools (strings, file,
zsteg, steghide, exiftool) invoked with argument arrays — NEVER a shell, and NEVER by
executing the challenge itself.

Prompt-injection guard: a flag is only *trusted* (auto-submittable) when we DERIVE it — from
a file's bytes or by decoding. A flag-shaped string sitting in the task *description* (the
most attacker-controlled surface) is reported as an untrusted CANDIDATE and never auto-sent.
"""
from __future__ import annotations

import base64
import binascii
import codecs
import re
import subprocess
import urllib.parse
from collections import deque
from pathlib import Path

from . import coord


def _run(cmd: list[str], timeout: int = 30, cap: int = 100_000, binary: bool = False):
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout)  # no shell, args only
        out = p.stdout[:cap]
        return out if binary else out.decode("latin1", "ignore")
    except Exception:
        return b"" if binary else ""


def _variants(b: bytes) -> list[bytes]:
    s = b.strip()
    out: list[bytes] = []

    def pad(x, n):
        return x + b"=" * ((-len(x)) % n)

    clean = re.sub(rb"\s", b"", s)
    if re.fullmatch(rb"[A-Za-z0-9+/=\s]+", s) and len(clean) >= 8:
        try:
            out.append(base64.b64decode(pad(clean, 4)))
        except Exception:
            pass
    if re.fullmatch(rb"[A-Za-z0-9_\-=\s]+", s) and len(clean) >= 8:
        try:
            out.append(base64.urlsafe_b64decode(pad(clean, 4)))
        except Exception:
            pass
    if re.fullmatch(rb"[A-Z2-7=\s]+", s) and len(clean) >= 8:
        try:
            out.append(base64.b32decode(pad(clean, 8)))
        except Exception:
            pass
    if re.fullmatch(rb"(?:[0-9a-fA-F]{2})+", clean):
        try:
            out.append(binascii.unhexlify(clean))
        except Exception:
            pass
    for fn in (lambda: base64.a85decode(s, adobe=False), lambda: base64.b85decode(s)):
        try:
            out.append(fn())
        except Exception:
            pass
    try:
        out.append(codecs.decode(b.decode("latin1"), "rot13").encode("latin1"))
    except Exception:
        pass
    try:
        u = urllib.parse.unquote_to_bytes(bytes(b))
        if u != b:
            out.append(u)
    except Exception:
        pass
    out.append(b[::-1])

    seen, res = set(), []
    for o in out:
        if o and o != b and o not in seen and len(o) < 200_000:
            seen.add(o)
            res.append(o)
    return res


def _cascade(seed: bytes, rx: re.Pattern, depth: int = 12, width: int = 6) -> str | None:
    seen = {seed}
    q = deque([(seed, 0)])
    while q:
        cur, d = q.popleft()
        if d > 0:  # only accept AFTER at least one real decode; a flag sitting in the raw
            m = rx.search(cur)  # seed (e.g. injected into a description) is never "decoded"
            if m:
                return m.group(0).decode("latin1")
        if d >= depth:
            continue
        for nx in _variants(cur)[:width]:
            if nx not in seen:
                seen.add(nx)
                q.append((nx, d + 1))
    return None


def autosolve(chaldir) -> tuple[str | None, str, str | None]:
    """Return (trusted_flag_or_None, recon_text, untrusted_candidate_or_None)."""
    rx = coord.flag_re()
    chaldir = Path(chaldir)
    recon: list[str] = []
    flag: str | None = None
    candidate: str | None = None

    task = chaldir / "task.md"
    task_b = task.read_bytes() if task.exists() else b""
    fdir = chaldir / "files"
    files = [p for p in fdir.rglob("*") if p.is_file()] if fdir.exists() else []
    recon.append(f"files: {len(files)}")

    # (A) flag literally present in a file's bytes (trusted)
    for f in files:
        size = f.stat().st_size
        ty = _run(["file", "-b", str(f)]).strip()[:70]
        recon.append(f"- {f.name} [{size}B] {ty}")
        if size > 5_000_000:
            continue
        m = rx.search(_run(["strings", "-n", "6", str(f)]).encode("latin1", "ignore"))
        if m:
            flag = m.group(0).decode("latin1")
            recon.append(f"  -> flag in strings({f.name})")
            break

    # (B) decode cascade over tokens from task + small text files (trusted: derived)
    if not flag:
        seeds: set[bytes] = set()
        if task_b:
            seeds.add(task_b.strip())
            seeds.update(re.findall(rb"[A-Za-z0-9+/=_\-]{12,}", task_b))
        for f in files:
            if f.stat().st_size <= 65_536 and f.suffix.lower() in ("", ".txt", ".b64", ".enc", ".dat", ".hex"):
                try:
                    d = f.read_bytes()
                    seeds.add(d.strip())
                    seeds.update(re.findall(rb"[A-Za-z0-9+/=_\-]{12,}", d))
                except Exception:
                    pass
        for seed in list(seeds)[:60]:
            r = _cascade(seed, rx)
            if r:
                flag = r
                recon.append("  -> flag via decode cascade")
                break

    # (C) stego quick wins
    if not flag:
        for f in files:
            ext = f.suffix.lower()
            hit = None
            if ext in (".png", ".bmp"):
                m = rx.search(_run(["zsteg", "-a", str(f)], timeout=60).encode("latin1", "ignore"))
                hit = ("zsteg", m) if m else None
            if not hit and ext in (".jpg", ".jpeg", ".bmp", ".wav"):
                out = _run(["steghide", "extract", "-sf", str(f), "-p", "", "-xf", "-"],
                           timeout=25, binary=True)
                m = rx.search(out)
                hit = ("steghide-emptypw", m) if m else None
            if not hit:
                m = rx.search(_run(["exiftool", str(f)], timeout=20).encode("latin1", "ignore"))
                hit = ("exif", m) if m else None
            if hit:
                flag = hit[1].group(0).decode("latin1")
                recon.append(f"  -> flag via {hit[0]}({f.name})")
                break

    # (D) flag-shaped string in the DESCRIPTION only -> untrusted candidate, never auto-sent
    if not flag and task_b:
        m = rx.search(task_b)
        if m:
            candidate = m.group(0).decode("latin1")
            recon.append(f"CANDIDATE in description (UNTRUSTED, not auto-submitted): {candidate}")

    text = "\n".join(recon)[: int(coord.get("MAX_RECON_CHARS"))]
    return flag, text, candidate
