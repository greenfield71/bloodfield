#!/usr/bin/env python3
"""CCSDS Space Packet parser for CTF: split on the ASM sync marker, parse the
6-byte primary header, group by APID, sort by sequence count, reassemble.

Primary header (6 bytes, big-endian bitfields):
  word0 (16b): version(3) | type(1) | sec_hdr_flag(1) | APID(11)
  word1 (16b): seq_flags(2) | seq_count(14)
  word2 (16b): data_length - 1   (so actual data field = length+1 bytes)

ASM sync marker for CADUs: 0x1ACFFC1D (often precedes frames).

    python3 -I ccsds.py packets.bin
    python3 -I ccsds.py --test

Covert-channel tip: a field holding an out-of-range/unused value every packet is
usually the payload -- read those bytes as ASCII.
Deps: stdlib only.
"""
import struct
import sys

ASM = bytes.fromhex("1ACFFC1D")


def split_on_sync(data, marker=ASM):
    """Split a stream on the ASM sync marker; returns chunks after each marker."""
    parts, i = [], data.find(marker)
    if i < 0:
        return [data]                 # no marker: treat whole blob as one stream
    while i >= 0:
        j = data.find(marker, i + len(marker))
        parts.append(data[i + len(marker): (j if j >= 0 else len(data))])
        i = j
    return parts


def parse_header(pkt):
    if len(pkt) < 6:
        return None
    w0, w1, w2 = struct.unpack(">HHH", pkt[:6])
    return {
        "version": (w0 >> 13) & 0x7,
        "type": (w0 >> 12) & 0x1,
        "sec_hdr": (w0 >> 11) & 0x1,
        "apid": w0 & 0x7FF,
        "seq_flags": (w1 >> 14) & 0x3,
        "seq_count": w1 & 0x3FFF,
        "data_len": w2 + 1,           # CCSDS stores length-minus-1
    }


def parse_packets(data):
    """Parse a concatenation of CCSDS packets (no ASM) into header+data dicts."""
    out, i = [], 0
    while i + 6 <= len(data):
        h = parse_header(data[i:i + 6])
        if h is None:
            break
        start = i + 6
        end = start + h["data_len"]
        h["data"] = data[start:end]
        out.append(h)
        i = end
    return out


def group_by_apid(packets):
    groups = {}
    for p in packets:
        groups.setdefault(p["apid"], []).append(p)
    for apid in groups:
        groups[apid].sort(key=lambda p: p["seq_count"])
    return groups


def reassemble(packets, apid):
    g = [p for p in packets if p["apid"] == apid]
    g.sort(key=lambda p: p["seq_count"])
    return b"".join(p["data"] for p in g)


def _mk(apid, seq, data):
    w0 = (apid & 0x7FF)
    w1 = (seq & 0x3FFF)
    w2 = len(data) - 1
    return struct.pack(">HHH", w0, w1, w2) + data


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        stream = _mk(100, 1, b"AB") + _mk(100, 0, b"fl") + _mk(200, 0, b"XX")
        pkts = parse_packets(stream)
        assert len(pkts) == 3, pkts
        assert reassemble(pkts, 100) == b"flAB", reassemble(pkts, 100)
        g = group_by_apid(pkts)
        assert set(g) == {100, 200}
        print("[ok] CCSDS parse/group/reassemble works:", reassemble(pkts, 100))
    elif len(sys.argv) > 1:
        data = open(sys.argv[1], "rb").read()
        for chunk in split_on_sync(data):
            pkts = parse_packets(chunk)
            for apid, g in group_by_apid(pkts).items():
                blob = reassemble(pkts, apid)
                printable = bytes(c for c in blob if 0x20 <= c < 0x7f)
                print(f"APID {apid}: {len(g)} pkts, {len(blob)}B  ascii={printable[:80]!r}")
    else:
        print(__doc__)
