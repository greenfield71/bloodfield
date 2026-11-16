#!/usr/bin/env python3
"""Minimal MAVLink v2 parser for CTF telemetry -> extract GLOBAL_POSITION_INT and
plot the track (also used from ctf-osint for geoint).

MAVLink v2 frame:
  0xFD | len | incompat | compat | seq | sysid | compid | msgid(3 LE) | payload | crc(2)
Payloads are often TRUNCATED (trailing zero bytes dropped) -> zero-pad to the
message's documented length before unpacking.

GLOBAL_POSITION_INT (msgid 33): lat, lon (int32, 1e7 deg), alt, relative_alt (mm),
vx, vy, vz (int16), hdg (uint16) -- 28 bytes.

    python3 -I mavlink.py telemetry.bin        # prints coords, saves track.png if matplotlib
    python3 -I mavlink.py --test

Deps: stdlib (matplotlib optional for plotting).
"""
import struct
import sys

MAGIC_V2 = 0xFD
GLOBAL_POSITION_INT = 33
GPI_LEN = 28


def iter_frames(data):
    """Yield (msgid, payload_bytes) for each MAVLink v2 frame found."""
    i, n = 0, len(data)
    while i < n:
        if data[i] != MAGIC_V2:
            i += 1
            continue
        if i + 10 > n:
            break
        plen = data[i + 1]
        msgid = data[i + 7] | (data[i + 8] << 8) | (data[i + 9] << 16)
        start = i + 10
        end = start + plen
        if end + 2 > n:
            break
        yield msgid, data[start:end]
        i = end + 2            # skip CRC


def parse_positions(data):
    out = []
    for msgid, payload in iter_frames(data):
        if msgid != GLOBAL_POSITION_INT:
            continue
        payload = payload.ljust(GPI_LEN, b"\x00")[:GPI_LEN]   # zero-pad truncated
        time_boot, lat, lon, alt, rel_alt, vx, vy, vz, hdg = struct.unpack(
            "<IiiiihhhH", payload)
        out.append({"lat": lat / 1e7, "lon": lon / 1e7, "alt_m": alt / 1000.0})
    return out


def plot(points, path="track.png"):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    xs = [p["lon"] for p in points]
    ys = [p["lat"] for p in points]
    plt.figure(figsize=(8, 8))
    plt.plot(xs, ys, "-o", ms=2)
    plt.xlabel("lon"); plt.ylabel("lat"); plt.title("MAVLink track")
    plt.savefig(path, dpi=120)
    return path


def _build_gpi_frame(lat, lon, alt_mm=0):
    payload = struct.pack("<IiiiihhhH", 0, int(lat * 1e7), int(lon * 1e7),
                          alt_mm, 0, 0, 0, 0, 0)
    header = bytes([MAGIC_V2, len(payload), 0, 0, 0, 1, 1,
                    GLOBAL_POSITION_INT & 0xFF,
                    (GLOBAL_POSITION_INT >> 8) & 0xFF,
                    (GLOBAL_POSITION_INT >> 16) & 0xFF])
    return header + payload + b"\x00\x00"


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        blob = _build_gpi_frame(51.5, -0.12) + _build_gpi_frame(48.85, 2.35)
        pts = parse_positions(blob)
        assert len(pts) == 2 and abs(pts[0]["lat"] - 51.5) < 1e-6, pts
        assert abs(pts[1]["lon"] - 2.35) < 1e-6, pts
        print("[ok] parsed", len(pts), "positions:", pts)
    elif len(sys.argv) > 1:
        data = open(sys.argv[1], "rb").read()
        pts = parse_positions(data)
        for p in pts:
            print(f"{p['lat']:.6f}, {p['lon']:.6f}  alt={p['alt_m']:.1f}m")
        out = plot(pts)
        if out:
            print("track plotted ->", out)
    else:
        print(__doc__)
