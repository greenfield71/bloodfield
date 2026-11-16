#!/usr/bin/env python3
"""Decode USB HID keyboard keystrokes from a pcap capture.

1) extract the capdata:
   tshark -r cap.pcap -Y 'usb.capdata' -T fields -e usb.capdata > caps.txt
   (some captures use -e usbhid.data ; try both)
2) python3 -I usb_hid.py caps.txt
3) python3 -I usb_hid.py --test

Each keyboard HID report is 8 bytes: [modifier, reserved, k1..k6].
Byte 3 (index 2) usually holds the active keycode. Shift = modifier bit 0x22 (0x02 or 0x20).
"""
import sys

HID = {
    0x04: ("a", "A"), 0x05: ("b", "B"), 0x06: ("c", "C"), 0x07: ("d", "D"),
    0x08: ("e", "E"), 0x09: ("f", "F"), 0x0a: ("g", "G"), 0x0b: ("h", "H"),
    0x0c: ("i", "I"), 0x0d: ("j", "J"), 0x0e: ("k", "K"), 0x0f: ("l", "L"),
    0x10: ("m", "M"), 0x11: ("n", "N"), 0x12: ("o", "O"), 0x13: ("p", "P"),
    0x14: ("q", "Q"), 0x15: ("r", "R"), 0x16: ("s", "S"), 0x17: ("t", "T"),
    0x18: ("u", "U"), 0x19: ("v", "V"), 0x1a: ("w", "W"), 0x1b: ("x", "X"),
    0x1c: ("y", "Y"), 0x1d: ("z", "Z"),
    0x1e: ("1", "!"), 0x1f: ("2", "@"), 0x20: ("3", "#"), 0x21: ("4", "$"),
    0x22: ("5", "%"), 0x23: ("6", "^"), 0x24: ("7", "&"), 0x25: ("8", "*"),
    0x26: ("9", "("), 0x27: ("0", ")"),
    0x28: ("\n", "\n"), 0x2a: ("[BS]", "[BS]"), 0x2b: ("\t", "\t"),
    0x2c: (" ", " "), 0x2d: ("-", "_"), 0x2e: ("=", "+"), 0x2f: ("[", "{"),
    0x30: ("]", "}"), 0x31: ("\\", "|"), 0x33: (";", ":"), 0x34: ("'", '"'),
    0x35: ("`", "~"), 0x36: (",", "<"), 0x37: (".", ">"), 0x38: ("/", "?"),
}


def decode(lines):
    out = []
    for line in lines:
        h = line.strip().replace(":", "")
        if not h:
            continue
        try:
            data = bytes.fromhex(h)
        except ValueError:
            continue
        if len(data) < 3:
            continue
        # find the 8-byte keyboard report: modifier at [0], keycode at [2]
        mod = data[0]
        key = data[2]
        if key == 0:
            continue
        shift = bool(mod & 0x22)
        if key in HID:
            ch = HID[key][1 if shift else 0]
            out.append(ch)
    text = "".join(out)
    # apply backspaces
    res = []
    for c in text.replace("[BS]", "\b"):
        if c == "\b":
            if res:
                res.pop()
        else:
            res.append(c)
    return "".join(res)


def _self_test():
    # Build synthetic HID reports:
    # 1. Shift + 'f' -> 'F' (mod=0x02, key=0x09)
    # 2. 'l' (mod=0x00, key=0x0f)
    # 3. 'a' (mod=0x00, key=0x04)
    # 4. 'g' (mod=0x00, key=0x0a)
    # 5. Shift + '[' -> '{' (mod=0x02, key=0x2f)
    # 6. 'x' (mod=0x00, key=0x1b)
    # 7. Backspace (mod=0x00, key=0x2a)
    # 8. 'h' (mod=0x00, key=0x0b)
    # 9. 'i' (mod=0x00, key=0x0c)
    # 10. Shift + ']' -> '}' (mod=0x02, key=0x30)
    synthetic_packets = [
        "02:00:09:00:00:00:00:00",
        "00:00:0f:00:00:00:00:00",
        "00:00:04:00:00:00:00:00",
        "00:00:0a:00:00:00:00:00",
        "02:00:2f:00:00:00:00:00",
        "00:00:1b:00:00:00:00:00",
        "00:00:2a:00:00:00:00:00",
        "00:00:0b:00:00:00:00:00",
        "00:00:0c:00:00:00:00:00",
        "02:00:30:00:00:00:00:00",
    ]
    res = decode(synthetic_packets)
    assert res == "Flag{hi}", f"Decoded mismatch: got '{res}'"
    print(f"[ok] usb_hid self-test passed: '{res}'")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python3 -I usb_hid.py caps.txt (or --test)")
        sys.exit(1)
    if sys.argv[1] == "--test":
        _self_test()
    else:
        with open(sys.argv[1]) as f:
            print(decode(f))
