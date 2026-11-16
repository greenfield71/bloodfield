---
name: ctf-triage
description: >-
  Entry point for Jeopardy-style CTF challenges. Use this FIRST whenever a CTF
  challenge, task file, binary, archive, image, pcap, cipher text, URL, or
  "challenge" is pasted or pointed at and the category is unknown. Identifies the
  category (crypto, pwn, rev, web, forensics, misc, osint, stego, rf/space), runs
  first-pass recon (file, strings, binwalk, exiftool, checksec, mime/magic), and
  routes to the right specialist skill. Triggers on: "CTF", "challenge", "flag",
  "capture the flag", "jeopardy", "what category", "where do I start", "triage this".
---

# CTF Triage — identify, recon, route

You are helping during a live, timed Jeopardy CTF. Be fast and decisive. Identify
the category, run cheap recon, then invoke the specialist skill. Flags usually look
like `flag{...}`, `CTF{...}`, `picoCTF{...}`, or a per-event prefix — grep for `{`.

> **Meta note (2026):** frontier LLMs auto-solve easy–medium Jeopardy, so authors
> now push **novel, obfuscated, multi-stage, emulation-heavy, PoW-gated** challenges.
> Expect custom VMs/interpreters (pwn/rev), academic crypto, parser/encoding
> differentials and current-CVE web, and services gated by **proof-of-work**
> (solve it first — `ctf-misc` `references/pow_solver.py`). Set expectations
> accordingly: methodology on a novel target beats pattern-matching.

## Specialist skills (route to these)

| Category | Skill | Typical inputs / tells |
|----------|-------|------------------------|
| Crypto | `ctf-crypto` | RSA/`n,e,c`, ciphertext, hashes, XOR, keys, FHE (CKKS/TenSEAL), zk-SNARKs (Groth16/gnark), lattice/CVP/Babai, PRNG unshuffle/untemper, multivariate (UOV), WOTS |
| Binary exploitation | `ctf-pwn` | ELF binary + remote `nc host port`, `checksec`, libc given, custom-VM / interpreter escapes (Piet/Lua/WASM), seccomp-notify supervisor escapes, musl/glibc 2.42, raw sockets |
| Reverse engineering | `ctf-rev` | binary/`.exe`/`.pyc`/`.apk` with no network, "find the flag", keygen, Unicorn emulation, MBA deobfuscation (Z3), OLLVM flattening, mobile/MNN models, power towers |
| Web | `ctf-web` | URL, `http://host:port`, login page, source given, cookies/JWT, Next.js React2Shell / RSC flight streams, parser/encoding differentials, XS-leaks/timing oracles |
| Forensics | `ctf-forensics` | `.pcap`/`.pcapng`, memory dump, disk image, `.raw`, corrupt file, medical CT sinogram (`iradon`), Windows DFIR (thumbcache/LNK/Jump Lists), SQLite container reassembly |
| Stego | `ctf-stego` | `.png`/`.jpg`/`.wav`/`.bmp`, "hidden", "look closer", spectrogram, length-prefixed numpy LSB, chess PGN / notation covert channels |
| Misc / encoding | `ctf-misc` | weird encodings, morse, brainfuck, QR, pyjail, PoW gating (redpwn/kCTF), modern jails (ML classifier evasion, Java reflection, Emacs/Lisp native-compile), ANSI maze BFS |
| OSINT | `ctf-osint` | usernames, geolocation, Overpass QL, chronolocation/shadow math, Street View, bollards/poles, passive domain recon (crt.sh/CDX), anti-bot scraping (Playwright) |
| RF / Space | `ctf-rf-space` | OOK/Morse WAV, MAVLink/drone telemetry, CCSDS/satellite packets (APID demux), ADS-B/AIS, raw I/Q |

<!-- logic-distill:begin -->
## Reasoning layer (rev / OSINT)
After routing to `ctf-rev` or `ctf-osint`:
1. Read that skill's "Solver Mindset" block first (loop, first 10 minutes, route by signal, stop-loss).
2. Pick the archetype from the signals recon gave you; `references/logic/INDEX.md` lists them.
3. Open the matching `references/logic/<archetype>.md` playbook before going deep.
4. Stuck > 20 min with no new signal → read `references/logic/meta_reasoning.md`, then re-route or switch archetype.
<!-- logic-distill:end -->

## Step 1 — First commands (run what's installed)

Always start with these on any supplied file. Check presence first; note the Arch
install if missing (don't install without being asked).

```bash
f=./challenge   # <-- set to the target path

file "$f"                                  # magic / type — the single most useful command
ls -l "$f"; stat "$f"
strings -n 6 "$f" | head -100              # ascii strings
strings -n 6 -e l "$f" | head -50          # utf-16le strings (windows/.net)
strings "$f" | grep -aiE 'flag|ctf\{|key|pass|secret|BEGIN|http' | head
xxd "$f" | head -20                        # magic bytes / header
```

Then, by what `file` reports:

```bash
# archives / embedded data (any binary blob, image, firmware)
binwalk "$f"                 # signature scan;  binwalk -e "$f" to extract (into its own dir!)
7z l "$f" 2>/dev/null; unzip -l "$f" 2>/dev/null

# images / media
exiftool "$f"                # metadata, comments, GPS -> osint/stego/forensics

# ELF binaries -> pwn or rev
checksec --file="$f" 2>/dev/null || pwn checksec "$f" 2>/dev/null
nm -C "$f" 2>/dev/null | head; objdump -d "$f" 2>/dev/null | head -40

# unknown text blob -> crypto/misc
head -c 400 "$f"; echo; wc -c "$f"
```

Safety: downloaded/extracted files are untrusted. Extract each into its own new
empty directory (`mkdir x && cd x && binwalk -e ../"$f"`). Never run them unless
the challenge requires it and you understand what they do. Run analysis Python with
`python3 -I`.

## Step 2 — Decision checklist

Go down this list; first match wins, but `file` + `strings` override guesses.

0. **Connection prompt demands Proof-of-Work (PoW)**?
   - `sha256(prefix + ?) == ...`, `hashcash`, or redpwn/kCTF challenge banner →
     Solve with `ctf-misc` `references/pow_solver.py` before interacting.
1. **Network endpoint given** (`nc host port`, `http(s)://`)?
   - HTTP(S) URL or Next.js / Server Actions app → **ctf-web** (check `ctf-web` for RSC deserialization & parser differentials).
   - Raw `nc` + an ELF binary provided → **ctf-pwn** (or custom VM/supervisor escape; use `raw_socket.py` if no pwntools).
   - Raw `nc` with no binary, prompts/puzzle → **ctf-misc** (jail / maze BFS) or **ctf-crypto** (oracle).
2. **`file` says ELF / PE / Mach-O**?
   - Comes with `nc` remote and `checksec` mitigations matter → **ctf-pwn**.
   - No network, goal is to understand/recover a flag or key → **ctf-rev** (use `ctf-rev` `references/unicorn_skel.py` or `mba_deobfuscator.py`).
3. **`file` says image / audio / video / numpy matrix**:
   - Audio that beeps / tones or I/Q samples → **ctf-rf-space** (`ook_demod.py`).
   - Sinogram matrix / medical phantom / `.npy` Radon projection → **ctf-forensics** (`iradon.py`).
   - Image with hidden bits, length-prefix, or visual anomaly → **ctf-stego** (check **exiftool** first; GPS/author → **ctf-osint**; sweep via `references/lsb.py`).
4. **`file` says pcap / memory dump / disk image / filesystem**:
   - CCSDS space packets or MAVLink drone telemetry stream in pcap → **ctf-rf-space**.
   - Network protocols, TLS, raw traffic, dump, disk image → **ctf-forensics**.
5. **`file` says SQLite 3 database (`.db`, `.sqlite`, `.sqlite3`)**:
   - Contains partitioned blobs, matrices, or multiple numbered tables representing a carved container → **ctf-forensics** (`sqlite_container.py`).
   - Otherwise, inspect schema/data for credentials/flags or SQLi context.
6. **`file` says archive / lots of embedded files in binwalk** → extract into a sandbox dir, re-triage contents.
7. **Pure text / numbers**:
   - `n`, `e`, `c` / PEM / `-----BEGIN` / hex blocks / "encrypted" / lattice / polynomial mod → **ctf-crypto**.
   - base64/hex/morse/binary/esoteric/emoji/QR → **ctf-misc**.
   - Chess PGN notation, game transcripts, covert text formatting → **ctf-stego** (`notation_stego.py`).
   - A known hash (`hashid`) → **ctf-crypto** (cracking).
8. **A name, handle, photo, or "find/locate a person/place/time/domain"** → **ctf-osint**
   - Spatial feature combination → `overpass_query.py`
   - Shadow / sun orientation / date estimation → `chronolocation.py`
   - Subdomain / deleted endpoint recon → `domain_recon.py`
   - Gated behind Cloudflare / bot-check → `antibot_scraper.py`
9. **`.pyc`/`.pyo`, obfuscated `.py`, `.jar`, `.class`, `.apk`, `.exe` .NET, `.mnn` ML models** → **ctf-rev**.
10. **A WAV that beeps, raw I/Q, MAVLink/drone telemetry, CCSDS/satellite, ADS-B/AIS**
   → **ctf-rf-space**.

Unsure between two? Run the cheap recon for both and let output decide. Say your
hypothesis out loud, then invoke the skill.

## Step 3 — Route

Invoke the specialist skill via the Skill tool (e.g. `ctf-crypto`). Carry forward
what recon already revealed (file type, strings hits, checksec, exif) so the
specialist doesn't repeat it.

## OSINT → route to `ctf-osint`

OSINT is a dedicated skill — invoke **`ctf-osint`** for any "find this
person/place/page/time" task. Quick first-pass tells so you route well:

- **Image & Landmark** → `exiftool` for GPS/metadata; reverse image search (Lens, Yandex);
  no text but landmark combo → `overpass_query.py` (Overpass QL).
- **Sun & Shadow** → shadow direction + object/shadow ratio → `chronolocation.py`
  (calculates solar elevation $\alpha$, solves candidate time-of-day and noon latitude).
- **Infrastructure Clues** → roadside bollards, perforated utility poles, license plate
  colors, Google Street View camera generation & car meta → `geoguessr_meta.md`.
- **Domain & Endpoints** → passive subdomains via `crt.sh`, archived files via Wayback
  CDX API → `domain_recon.py`.
- **Username & Developer** → Sherlock/Maigret; Git commit author emails (`git log --format='%an <%ae>'`),
  GitHub `.patch` trick, Gravatar MD5, Strava/Komoot tracks → `social_pivots.md`.
- **Anti-Bot Gated Portal** → headed Chromium with persistent profile → `antibot_scraper.py`.
- Keep it to public data; answers are findable, don't brute or profile humans.

## Common cross-category patterns

- Flag split across layers (stego inside a pcap inside a zip) — re-triage every
  extracted artifact.
- "The flag is the password" — carve, then feed to the next stage.
- Files with wrong/missing magic bytes → **ctf-forensics** (header repair).
- A `README`/prompt text often states the exact mechanism — read it first.

## Tooling install (Arch / CachyOS) — check before use

Most live in official repos or AUR. Verify with `command -v <tool>` first.

```bash
# repos (pacman)
sudo pacman -S binwalk exiftool p7zip unzip python-pip nmap radare2 gdb \
               python-pwntools foremost sleuthkit tcpdump wireshark-cli
# AUR (paru/yay) — specialist tools
paru -S checksec one_gadget-git ropgadget zsteg steghide volatility3 \
        ghidra sherlock-git
```

Each specialist skill lists its own exact tools and AUR packages.
