---
name: ctf-misc
description: >-
  Miscellaneous CTF challenges — encodings, esolangs, jails, and "guess the
  gimmick". Use for mystery encodings (base16/32/64/85/58, hex, binary, decimal,
  ROT, URL, morse, braille, tap code), esoteric languages (brainfuck, Ook!,
  Malbolge, Whitespace, Piet), QR/barcode decoding, pyjail / Python sandbox
  escapes, bash/shell jail escapes, chained multi-layer decoding, plus 2026
  additions: proof-of-work gating (pwn.red/redpwn, kCTF), modern jails
  (ML-classifier/CNN-prefiltered adversarial evasion, Java reflection, Emacs/Lisp
  native-compile), traceback source-leak, and automation-under-latency (ANSI maze
  BFS, HTTP pipelining). Triggers on: "encoding", "decode", "base64", "base32",
  "base85", "base58", "morse", "braille", "brainfuck", "esolang", "whitespace",
  "QR code", "barcode", "pyjail", "jail escape", "sandbox escape", "cyberchef",
  "what is this encoding", "misc", "PoW", "proof of work", "pwn.red", "redpwn",
  "kCTF", "adversarial", "CNN", "classifier", "Java jail", "Emacs", "Lisp jail",
  "native-compile", "SecurityManager", "traceback", "ANSI", "maze", "captcha",
  "pipelining".
---

# CTF Misc — encodings, esolangs, jails, gimmicks

Python (`pip install --user pwntools requests`) + CLI tools.
Check before installing (`command -v <tool>`):
```bash
command -v zbarimg >/dev/null || paru -S --needed zbar qrencode
python3 -c "import PIL" 2>/dev/null || sudo pacman -S --needed python-pillow
```
The multi-decode helper `references/multidecode.py` auto-detects and recursively peels
encoding layers — run it first on any mystery blob. A reusable **PoW runner** is in
`references/pow_solver.py` (pwn.red/redpwn + kCTF). Run scripts with `python3 -I`.

## Step 1 — Mystery blob → auto-decode

```bash
python3 -I references/multidecode.py 'INPUT_STRING'
python3 -I references/multidecode.py -f blob.txt
```
Decodes base64/32/16/85/58, hex, binary, decimal, URL/HTML, ROT13/47, reversed,
morse — stopping at readable text/flag. Stubborn? CyberChef "Magic".

Manual quick decodes:
```bash
echo 'aGVsbG8=' | base64 -d ; echo '68656c6c6f' | xxd -r -p
python3 -c "import base64;print(base64.b85decode('...'))"
```

## Encoding recognition cheatsheet

| Looks like | Encoding |
|-----------|----------|
| `A-Za-z0-9+/` ending `=` | base64 (`-_`=url) |
| `A-Z2-7` ending `=` | base32 |
| only `0-9a-f`, even len | hex |
| `0`/`1` groups of 8 | binary → ASCII |
| `.-` and spaces/`/` | **morse** |
| Unicode dots `⠁⠃⠉` | **braille** |
| `!-u` 5-char / `<~ ~>` | base85 |
| no 0 O I l | base58 |
| `%41%42` | URL-encode |
| `&#65;` | HTML entities |
| `+[]{}()` only | **brainfuck**/JSFuck |
| whitespace only | **Whitespace** lang |
| `Ook. Ook?` | **Ook!** |
| emoji / zero-width | zero-width stego |

## Esolangs

```bash
command -v beef >/dev/null || paru -S beef
beef prog.bf          # brainfuck
command -v npiet >/dev/null || paru -S npiet
npiet prog.png       # Piet (image-as-program)
# Whitespace: ws interpreter ; Ook!/Blub: -> brainfuck ; Malbolge: known generator
```
A minimal brainfuck interpreter is in `references/multidecode.py` (`brainfuck()`).

## QR / barcodes

```bash
zbarimg code.png ; qrencode -o out.png 'text'
python3 -I references/multidecode.py --qr grid.txt     # 0/1 matrix -> render -> scan
```

## Proof-of-work gating (now routine)

Many services open with a PoW challenge before the real interaction. Detect the
banner and solve it first (`references/pow_solver.py`):
- **pwn.red / redpwn** (`kctf`-style and `redpwn` S-prefixed): "proof of work:
  solve <challenge>" / a `curl <url> | sh` hint — compute the required hashcash.
- **kCTF**: `python3 <(curl -sSL ...kctf-pow...) solve <chal>` — reproduce with gmpy2.
```python
# python3 -I references/pow_solver.py <recv-banner>   OR import solve_redpwn/solve_kctf
```
Wire the solver before your padding-oracle / jail / automation loop (also used by
`ctf-crypto`).

## Pyjail / Python sandbox escape

Assess what's blocked (builtins, `import`, dots, quotes, keywords, `__`). Core:

```python
().__class__.__base__.__subclasses__()                 # find useful classes
[].__class__.__base__.__subclasses__()[IDX]()._module.__builtins__['__import__']('os').system('sh')
__builtins__.__import__('os').system('cat /flag')      # if builtins intact
breakpoint()                                           # pdb -> import os (Py3.7+)
getattr(__import__('o'+'s'),'sys'+'tem')('sh')         # keyword-filter bypass
open('/flag').read()                                   # no os needed
```
Filter tricks: `__`→`getattr`/`\x5f\x5f`; `.`→`getattr`/`operator.attrgetter`;
quotes→`chr()`/`().__doc__[i]`/f-string; builtins gone→`subclasses()` walk;
`()` blocked→decorators `@`. Fuller catalog: `references/pyjail.md`.

## Modern jails (2026)

Jails have evolved past plain pyjail — see `references/modern_jails.md` for detail:

- **(a) ML-classifier / CNN pre-filtered jails** — a model scores your bytes and
  rejects "malicious" input. **Adversarially evade** it: block comments, string
  concatenation, `\uXXXX` escapes, and identifier-ignorable code points
  (e.g. U+008A, U+0013) nudge the classifier logit below threshold while staying
  valid Python. Reimplement the model offline with NumPy/safetensors (or PyTorch)
  to test payloads before spending a connection.
- **(b) Non-Python jails:**
  - **Java** — reflection on `Class.getDeclaredFields0` to null `System.security`
    (defeat SecurityManager), then `Runtime.exec`.
  - **Emacs Lisp** — a compile-time `(eval form)` via a `featurep` compiler macro,
    executed during native-compile *before* a Capstone call/jmp output check.
- **(c) Traceback source-leak** — force an uncaught exception (e.g. a huge number
  into a `float` modulo → `ZeroDivisionError`, or a type error) so the traceback
  prints the source lines + the flag. Common behind a PoW.

## Automation under latency

Timed/interactive puzzles (mazes, many rounds):
- Parse the **ANSI**-colored / double-width-unicode screen into a weighted graph;
  run **Dijkstra/BFS**; output the move sequence.
  Helper: `python3 -I references/ansi_maze_solver.py solve maze.txt` (or `--test`).
- Beat round-trip latency with **HTTP/1.1 pipelining** (batch many requests on one
  connection) or raw-TLS batched sends (`pipeline_commands()` in helper). Keep the
  socket open; don't reconnect.
- Web-API captchas: OCR (tesseract) or solve the intended logic, then replay fast.

## Bash / shell jail escape

```bash
$'\x2f'bin/sh ; /bin/sh -i ; busybox sh ; python3 -c 'import pty;pty.spawn("/bin/sh")'
awk 'BEGIN{system("/bin/sh")}' ; find . -exec /bin/sh \; -quit ; env /bin/sh   # GTFOBins
# ${IFS} for spaces, ${PATH:0:1} to build '/', brace/glob expansion
```

## Protocol-aware packet carving

Telemetry/space protocols (CCSDS, MAVLink) in a misc challenge → parse the frames
with `struct`; see **`ctf-rf-space`** for ready parsers and the OOK/Morse demod.

## "Guess the gimmick" patterns

- Decode layers until readable (multidecode handles chains).
- Flag in filename, title, byte counts, RGB-as-ASCII, timestamps, keypad/T9, chess/
  coordinate notation, periodic-table symbols.
- Esoteric/joke encodings — identify by charset, use the right interpreter.
- Stuck: count chars, CyberChef Magic, **re-read the prompt** — the gimmick is hinted.
