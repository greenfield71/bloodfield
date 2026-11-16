---
name: ctf-forensics
description: >-
  Digital forensics CTF challenges. Use for file carving, memory forensics,
  network (pcap) analysis, disk images, corrupt-file repair, plus 2026 additions:
  medical/volumetric imaging reconstruction (CT sinogram → scikit-image iradon),
  Windows DFIR shell artifacts (thumbcache, Jump Lists/LNK, Distributed Link
  Tracker, RDP tsclient), and SQLite-as-container payloads. Covers
  binwalk/foremost/photorec carving, volatility3 memory, wireshark/tshark pcap,
  USB/HID keystroke reconstruction, disk images (sleuthkit), and magic-byte
  repair. Triggers on: "forensics", "pcap", "pcapng", "wireshark", "tshark",
  "memory dump", "volatility", "disk image", "carve", "foremost", "binwalk",
  "recover file", "corrupt file", "magic bytes", "USB keystrokes", "network
  capture", "e01", "raw", "sinogram", "Radon", "scikit-image", "iradon", "CT
  scan", "volumetric", "thumbcache", "Jump List", "LNK", "shellbag", "KAPE",
  "SQLite", "tsclient", "DFIR", "Windows artifact".
---

# CTF Forensics

Tools (Arch): check before installing (`command -v <tool>`):
```bash
command -v binwalk >/dev/null || sudo pacman -S --needed binwalk foremost tcpdump wireshark-cli sleuthkit testdisk exiftool p7zip
command -v vol >/dev/null || paru -S --needed volatility3 bulk-extractor
python3 -c "import skimage" 2>/dev/null || pip install --user scikit-image numpy pyfiglet
python3 -c "import LnkParse3" 2>/dev/null || pip install --user LnkParse3
```
Work on a copy; extract into an empty dir.

## Step 1 — Identify the evidence type

```bash
file evidence.* ; binwalk evidence.bin ; exiftool evidence.* ; xxd evidence.* | head
```
Route: **pcap/pcapng** → network; **.raw/.mem/.vmem/.dmp/.lime** → memory;
**.img/.dd/.E01/.iso** → disk; **office/zip/pdf/image** → carve+metadata+repair;
**.db / "SQLite"** → SQLite-as-container (Step 5).

## Step 2 — Carving & recovery

```bash
binwalk evidence.bin ; mkdir ext && binwalk -e evidence.bin -C ext
foremost -i evidence.bin -o out_fm ; photorec evidence.img
strings -n 8 evidence.bin | grep -aiE 'flag|ctf\{|BEGIN|password'
```

## Step 3a — Network (pcap)

```bash
capinfos cap.pcap ; tshark -r cap.pcap -q -z io,phs ; tshark -r cap.pcap -q -z conv,tcp
tshark -r cap.pcap -T fields -e data.text -e http.file_data | grep -ai flag
tshark -r cap.pcap --export-objects http,http_out        # transferred files
tshark -r cap.pcap -q -z follow,tcp,ascii,0              # follow a stream
tshark -r cap.pcap -T fields -e dns.qry.name 'dns' | sort -u   # DNS exfil
tshark -r cap.pcap -Y 'ftp || telnet' -T fields -e ftp.request.arg
```
Filter for the single interesting response (often one `200`). GUI: Export Objects,
Follow Stream, Protocol Hierarchy.

### USB / HID keystroke reconstruction
```bash
tshark -r cap.pcap -Y 'usb.capdata' -T fields -e usb.capdata > caps.txt
python3 -I references/usb_hid.py caps.txt      # keyboard; mouse: plot dx,dy deltas
```

## Step 3b — Memory (volatility3)

```bash
vol -f mem.raw windows.info ; vol -f mem.raw windows.pslist ; vol -f mem.raw windows.pstree
vol -f mem.raw windows.cmdline ; vol -f mem.raw windows.filescan | grep -i flag
vol -f mem.raw windows.dumpfiles --virtaddr 0x... ; vol -f mem.raw windows.netscan
vol -f mem.raw windows.hashdump ; vol -f mem.raw windows.clipboard
# Linux: vol -f mem.lime linux.pslist / linux.bash (shell history!)
```
Also `strings mem.raw | grep -ai 'flag{'` and `bulk_extractor` first. (Memory was
quiet in the thin in-window sample but is a perennial — keep this.)

## Step 3c — Disk images

```bash
mmls disk.img ; fls -r -o <offset> disk.img ; icat -o <offset> disk.img <inode> > file
tsk_recover -o <offset> disk.img out/
sudo mount -o ro,loop,offset=$((512*OFFSET)) disk.img /mnt/x    # E01: ewfmount
```
Look in deleted files, slack, `.bash_history`, browser dbs, Recycle Bin, hives.

## Step 4 — File repair (broken magic / headers)

| Type | Magic (hex) | Notes |
|------|-------------|-------|
| PNG | `89 50 4E 47 0D 0A 1A 0A` | fix IHDR width/height for cropped flags |
| JPG | `FF D8 FF E0` (…`FF D9`) | multi-chunk; fix trailer too |
| GIF | `47 49 46 38 39 61` | |
| PDF | `25 50 44 46` | |
| ZIP/docx/jar | `50 4B 03 04` (end `50 4B 05 06`) | |
| MP4 | `.... 66 74 79 70` (`ftyp` at off 4) | repair box headers/trailer |
| ELF | `7F 45 4C 46` | |
| PCAP | `D4 C3 B2 A1` / `A1 B2 C3 D4` | |

```bash
printf '\x89PNG\r\n\x1a\n' | dd of=broken.png bs=1 conv=notrunc    # rewrite header
pngcheck -v file.png         # dimension/CRC; fix IHDR height to reveal cut-off flag
```

## Step 5 — Imaging / scikit-image (NEW)

**Recognize a sinogram**: an `N × angles` 2-D array (often stored *inside a DB* or a
`.npy`) that looks like smeared bands — it's a CT projection set. Invert with the
inverse Radon transform:

```python
# python3 -I
from skimage.transform import iradon
import numpy as np
sino = np.load("sino.npy")                     # shape (detectors, n_angles)
theta = np.linspace(0., 180., sino.shape[1], endpoint=False)
recon = iradon(sino, theta=theta, filter_name="ramp")   # center-pad if needed
# save/view recon; the flag is drawn in the reconstructed slice
```
A ready helper (center-pad + iradon + optional volumetric stacking) is in
`references/iradon.py`. **Volumetric**: reconstruct each slice, then **sum along an
axis** to reveal hidden text across the stack. Install (check first):
`python3 -c "import skimage, numpy" 2>/dev/null || pip install --user scikit-image numpy`.

## Step 6 — Windows DFIR artifacts (NEW)

- **thumbcache** (`thumbcache_*.db`): carve embedded images —
  `binwalk -e` or grep for `ffd8ff`/`89504e47`.
- **Jump Lists** (`*.automaticDestinations-ms`): OLE compound file —
  `7z x file.automaticDestinations-ms` → embedded `.lnk` targets.
- **LNK / Distributed Link Tracker**: parse with `LnkParse3`
  (`python3 -I -m LnkParse3 file.lnk`); the Tracker GUIDs hold a MAC/volume id.
- **RDP** `\\tsclient\` shares in artifacts → files came from the client host.
- KAPE-style triage packages bundle all of the above; enumerate then parse.

## Step 7 — SQLite as container (NEW)

When `file` says SQLite (or the artifact is a `.db`), the payload may be split across
**hundreds of tables/rows**:
```bash
sqlite3 eviden.db .tables ; sqlite3 eviden.db '.schema'
sqlite3 eviden.db 'SELECT name FROM sqlite_master;'
# Reassemble tables, blobs, or sinograms using helper:
python3 -I references/sqlite_container.py dump-tables eviden.db
python3 -I references/sqlite_container.py extract-blobs eviden.db file_chunks chunk out.bin
python3 -I references/sqlite_container.py extract-matrix eviden.db slice_001 sino_001.npy
```
Reassemble bytes in order with numpy/Python (sort by an index column, concat blobs).
Custom byte-pair/RLE formats sometimes decode to a **FIGlet banner** → `pyfiglet`.

## Common forensics patterns

- Flag reassembled only when you follow the stream / export the object.
- Data in DNS/ICMP/TLS-SNI; base64/hex-encoded.
- Memory `cmdline`/`bash` history holds the flag or a decrypt command.
- "Corrupt" image → wrong header or truncated height; repair reveals the flag.
- Re-triage every carved artifact (zip-in-pcap-in-memory). Protected zip → `zip2john` → crack.

> **Top-up flag:** forensics corpus is thin (autumn-major writeups pending) —
> re-check volatility/memory + classic image forensics before treating as complete.
