---
name: ctf-stego
description: >-
  Steganography CTF challenges — data hidden in images, audio, or other media.
  Use for PNG/BMP/JPG/WAV/GIF files where something is concealed ("hidden",
  "look closer", "nothing to see"). Covers zsteg (PNG/BMP LSB), steghide (JPG/WAV/BMP
  with passphrase), stegsolve-style channel/bit-plane analysis, binwalk/foremost
  for appended data, exiftool metadata, LSB extraction scripts, audio spectrogram
  (sox/spectrogram), outguess, strings, plus manual numpy/PIL LSB (length-prefixed
  custom schemes zsteg misses) and notation/protocol-field stego (chess PGN, packet
  fields). Triggers on: "stego", "steganography", "hidden", "zsteg", "steghide",
  "stegsolve", "LSB", "least significant bit", "spectrogram", "outguess", "hidden
  message", "image", "png", "wav", "PGN", "chess", "notation", "length prefix",
  "numpy LSB".
---

# CTF Stego

> **2026 note:** stego is a **shrinking standalone category** — the in-window
> Jeopardy majors had *no* stego track (it folded into forensics/misc). Triage
> accordingly and don't over-invest; cross-link `ctf-forensics` (carving/repair)
> and `ctf-misc` (encodings). Core tooling below is still correct for quick wins.

Tools (Arch): check before installing (`command -v <tool>`):
```bash
command -v exiftool >/dev/null || sudo pacman -S --needed exiftool imagemagick sox
command -v zsteg >/dev/null || paru -S --needed zsteg steghide stegsolve outguess binwalk foremost
python3 -c "import PIL, numpy" 2>/dev/null || pip install --user pillow numpy
```
`references/lsb.py` has flexible LSB extraction helpers. `references/notation_stego.py`
handles chess PGN move tracking and covert protocol fields. Work on a copy.

## Step 0 — Always first (cheap wins)

```bash
f=./chall.png
file "$f"                    # is the extension even correct? repair if not (ctf-forensics)
exiftool "$f"               # comments, author, GPS, software, odd fields
strings -n 6 "$f" | grep -aiE 'flag|ctf\{|pass|key|BEGIN'
binwalk "$f"               # appended ZIP/file after image data? -> binwalk -e (own dir)
xxd "$f" | tail -20        # data after the IEND/trailer?
```
A huge fraction of "stego" is just: metadata, appended archive, or `strings`.

## Step 1 — Route by media type

| Type | Primary tools |
|------|---------------|
| PNG, BMP (lossless) | **zsteg**, LSB scripts, stegsolve bit-planes |
| JPG | **steghide** (passphrase), outguess, exiftool, `stegseek` for brute |
| WAV, MP3, audio | **spectrogram** (sox), LSB on samples, steghide (wav), DTMF/morse |
| GIF | frame-by-frame (`convert -coalesce`), compare frames, LSB per frame |
| any | binwalk/foremost carve, strings, metadata |

## Step 2 — Images (PNG/BMP)

```bash
zsteg -a chall.png                 # tries ALL bit/channel/order combos (best first move)
zsteg -E 'b1,rgb,lsb,xy' chall.png # extract a specific payload zsteg named
```
Channel / bit-plane analysis (stegsolve, or ImageMagick/Python):
```bash
# stegsolve GUI: step through planes, color-channel views, data extract, XOR
# ImageMagick: isolate planes / amplify LSB
convert chall.png -channel R -separate r.png      # per-channel
convert chall.png -threshold 50% bw.png
```
Python LSB (when zsteg finds nothing or the scheme is custom) — see
`references/lsb.py`: pull LSBs across R/G/B, row/column order, 1–4 bits.

**Manual numpy/PIL LSB (custom schemes zsteg misses).** A 2026 flavor stores a
**length prefix** then the payload in a single channel's LSB plane:
```bash
python3 -c "import PIL, numpy" 2>/dev/null || pip install --user pillow numpy
python3 -I references/lsb.py chall.png            # sweeps channel × bit × order
python3 -c "import references.lsb as L; print(L.extract_length_prefixed('chall.png', channels='r', prefix_bits=16))"
```
`extract_length_prefixed()` reads the first 16 bits as a big-endian byte length
(MSB-first), then exactly that many payload bytes — iterate channel/bit/order if the
default red-channel scheme misses.

JPG (zsteg does NOT work on JPG — LSB isn't preserved):
```bash
steghide info chall.jpg                            # is there embedded data?
steghide extract -sf chall.jpg                     # prompts for passphrase
steghide extract -sf chall.jpg -p ''               # try empty pass first
stegseek chall.jpg /usr/share/wordlists/rockyou.txt  # brute the passphrase (fast)
outguess -r chall.jpg out.txt                      # alternative embed scheme
```

## Step 3 — Audio

```bash
# spectrogram — flags are often "drawn" in the frequency domain:
sox chall.wav -n spectrogram -o spec.png          # then open spec.png
# (Audacity GUI: Spectrogram view, or Analyze; also view the waveform zoomed in)
ffmpeg -i chall.wav -lavfi showspectrumpic=s=1024x512 spec.png   # alt
```
Other audio tricks:
- **LSB** on PCM samples (`references/lsb.py --audio`).
- **Morse** in tone on/off → decode by ear or `morse` tooling (→ ctf-misc).
- **DTMF** phone tones → `multimon-ng -a DTMF -t wav chall.wav`.
- **SSTV** (slow-scan TV image in audio) → `qsstv` / `sstv` decoder.
- Reversed/sped audio, hidden channel (stereo L-R diff), steghide on WAV.

## Step 4 — Custom / last resort

- `stegsolve` "Data Extract" to pull arbitrary bit-plane combinations.
- Compare to an original image if provided: `compare a.png b.png diff.png` —
  the delta is the payload.
- XOR two frames/channels; look at the alpha channel; check palette (indexed PNG).
- Try multiple layers: extracted data may itself be base64/zip/another image
  (re-triage via ctf-triage).

## Data in notation / protocol fields

Not all "stego" is pixels/audio — data can ride inside **structured notation**:
- **Chess PGN** — the moves (e.g. queen-move destination squares) encode bytes;
  plot the coordinates on an 8x8 grid to draw letters, or map squares → values.
  Helper: `python3 -I references/notation_stego.py pgn games.pgn --piece Q`
- **Protocol/packet fields** — out-of-range or unused header fields carry data
  (crosses over with `ctf-misc` and `ctf-rf-space` — CCSDS/MAVLink telemetry).
  Helper: `decode_covert_fields()` in `references/notation_stego.py`.
Recognize by: a "normal-looking" game/log/capture whose values are too regular or
out of range. Decode with a short Python script.

## Common stego patterns

- zsteg `b1,rgb,lsb,xy` is the single most common PNG hiding scheme.
- steghide with an empty or guessable (title of the challenge) passphrase.
- Flag written in the spectrogram of a WAV.
- ZIP appended after image data (`binwalk -e`), sometimes password-protected.
- EXIF comment / `UserComment` holds the flag or the steghide passphrase.
- Wrong image height crops out the flag → fix IHDR (ctf-forensics repair).
