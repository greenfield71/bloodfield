---
name: ctf-rf-space
description: >-
  RF, radio, and space/aerospace protocol CTF challenges. Use for signal
  demodulation (OOK/on-off-keying audio → Morse via numpy/scipy DSP), drone
  telemetry (MAVLink v2 GLOBAL_POSITION_INT track plotting → geoint), space
  protocols (CCSDS packets, APID filtering, covert channels in out-of-range
  fields), and ADS-B / AIS frame parsing. Pure-Python numpy/scipy DSP (not GNU
  Radio) suits CTF-scale signals; struct for protocol parsing. Triggers on: "RF",
  "radio", "OOK", "Morse", "demodulate", "MAVLink", "drone", "CCSDS", "satellite",
  "space", "telemetry", "ADS-B", "AIS", "I/Q", "SDR", "URH".
---

# CTF RF & Space protocols

For radio/aerospace challenges (e.g. STARPWN / Aerospace Village). The 2026 reality:
these are solved with **pure-Python numpy/scipy DSP** and `struct` protocol parsers —
**not** GNU Radio / URH / inspectrum GUIs (those are only for raw I/Q captures).

Tools (Arch): check before installing (`command -v <tool>`):
```bash
command -v sox >/dev/null || sudo pacman -S --needed sox
python3 -c "import scipy, pymavlink" 2>/dev/null || pip install --user numpy scipy pymavlink
command -v urh >/dev/null || paru -S --needed urh inspectrum
```
Run scripts with `python3 -I`.

Helpers: `references/ook_demod.py` (OOK→Morse), `references/mavlink.py`
(MAVLink v2 parse + track), `references/ccsds.py` (CCSDS primary-header parse).

## Step 0 — Identify the signal / protocol

```bash
file capture.*                         # wav? raw I/Q? binary telemetry?
xxd capture.bin | head                 # magic: MAVLink 0xFD, CCSDS version bits
sox --i capture.wav                    # audio: rate, channels, duration
```
- **.wav / audio** that beeps → likely **OOK → Morse** (Step 1).
- Binary stream with `0xFD` frame starts → **MAVLink v2** (Step 2).
- Fixed 6-byte headers, sync `0x1ACFFC1D` → **CCSDS** (Step 3).
- Raw I/Q (`.cfile`, `.iq`, complex float) → inspectrum/URH, or numpy demod.

## Step 1 — WAV / OOK demod → Morse

On-off keying: the carrier is present (dot/dash) or absent (gap). Envelope-detect,
threshold, run-length → Morse → text.

```bash
python3 -I references/ook_demod.py capture.wav       # -> Morse + decoded text
```
Method (in the helper): read samples (`scipy.io.wavfile`), take the **envelope**
(abs + moving-average, or Hilbert), **threshold** (Otsu/mean), collapse to on/off
**run-lengths**, cluster short/long on-runs → dot/dash and gaps → letter/word breaks,
map via the Morse table. Tune the moving-average window to the symbol rate if noisy.

For a raw I/Q file: mix to baseband, low-pass, take magnitude, then the same pipeline.

## Step 2 — MAVLink v2 (drone telemetry)

MAVLink v2 frames start with magic **`0xFD`**; the payload may be **truncated**
(trailing zero bytes dropped) — **zero-pad to the message's full length** before
unpacking. `GLOBAL_POSITION_INT` (msg id 33) carries lat/lon in 1e7 degrees.

```bash
python3 -I references/mavlink.py telemetry.bin       # -> list of (lat, lon, alt), plots track
```
Plot the track (matplotlib) and read the shape/endpoint — the path often *draws* the
flag or points at a location (→ geoint, cross-link `ctf-osint`). `pymavlink` can also
parse: `from pymavlink import mavutil; m = mavutil.mavlink_connection('telemetry.bin')`.

## Step 3 — CCSDS space packets

CCSDS Space Packet Protocol: a **6-byte primary header** (version, type, APID,
sequence flags + 14-bit sequence count, 16-bit length), then the data field. A frame
sync marker **`0x1ACFFC1D`** (ASM) often precedes CADUs.

```bash
python3 -I references/ccsds.py packets.bin           # parse headers, group by APID
```
Workflow: split on the sync marker, parse each primary header, **filter by APID**
(each APID = one data stream), **sort by sequence count**, reassemble the data field.
**Covert channel:** values placed in **out-of-range / unused fields** are the payload
(e.g. an "impossible" field value read as ASCII). Diff fields against spec ranges.

## Step 4 — ADS-B / AIS (completeness)

- **ADS-B** (1090 MHz aircraft): 112-bit Mode-S extended squitter; type code in the
  first 5 bits of the message; CPR lat/lon needs an even+odd frame pair to decode.
  `pyModeS` (`python3 -c "import pyModeS" 2>/dev/null || pip install --user pyModeS`) decodes frames if you have hex messages.
- **AIS** (ship transponders): NMEA `!AIVDM` sentences, 6-bit ASCII armor; `pyais`
  (`python3 -c "import pyais" 2>/dev/null || pip install --user pyais`) parses position reports.

## Common RF/space patterns

- Audio that sounds like beeping → OOK → Morse → flag.
- A telemetry log whose plotted track spells text or marks a spot → geoint.
- Packets where one field is "wrong" every time → covert channel, read as ASCII.
- Truncated/zero-trimmed payloads — pad to the spec length before `struct.unpack`.
- I/Q capture → inspectrum to eyeball modulation, then numpy to demod at CTF scale.
