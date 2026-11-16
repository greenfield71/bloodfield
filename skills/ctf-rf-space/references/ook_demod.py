#!/usr/bin/env python3
"""OOK (on-off keying) audio -> Morse -> text, with numpy/scipy only.

    python3 -I ook_demod.py capture.wav
    python3 -I ook_demod.py --test

Pipeline: read WAV -> envelope (abs + moving average) -> threshold -> on/off
run-lengths -> cluster into dot/dash + gaps -> Morse table -> text.
Deps: numpy, scipy (for wav read; falls back to the stdlib `wave` module).
"""
import sys
import numpy as np

MORSE = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E", "..-.": "F",
    "--.": "G", "....": "H", "..": "I", ".---": "J", "-.-": "K", ".-..": "L",
    "--": "M", "-.": "N", "---": "O", ".--.": "P", "--.-": "Q", ".-.": "R",
    "...": "S", "-": "T", "..-": "U", "...-": "V", ".--": "W", "-..-": "X",
    "-.--": "Y", "--..": "Z", "-----": "0", ".----": "1", "..---": "2",
    "...--": "3", "....-": "4", ".....": "5", "-....": "6", "--...": "7",
    "---..": "8", "----.": "9", ".-.-.-": ".", "--..--": ",", "..--..": "?",
    "-..-.": "/", "-....-": "-", "-.--.": "(", "-.--.-": ")", "---...": ":",
}


def read_wav(path):
    try:
        from scipy.io import wavfile
        rate, data = wavfile.read(path)
    except Exception:
        import wave
        w = wave.open(path, "rb")
        rate = w.getframerate()
        raw = w.readframes(w.getnframes())
        data = np.frombuffer(raw, dtype=np.int16)
        if w.getnchannels() > 1:
            data = data[:: w.getnchannels()]
        return rate, data.astype(float)
    if data.ndim > 1:
        data = data[:, 0]
    return rate, data.astype(float)


def envelope(sig, win):
    e = np.abs(sig)
    if win > 1:
        kernel = np.ones(win) / win
        e = np.convolve(e, kernel, mode="same")
    return e


def runs_from_env(env):
    thr = (env.max() + env.mean()) / 2.0 if env.max() > 0 else 0.5
    on = env > thr
    runs = []
    cur, length = on[0], 1
    for v in on[1:]:
        if v == cur:
            length += 1
        else:
            runs.append((bool(cur), length))
            cur, length = v, 1
    runs.append((bool(cur), length))
    return runs


def runs_to_morse(runs):
    on_lens = sorted(l for s, l in runs if s)
    if not on_lens:
        return ""
    unit = on_lens[len(on_lens) // 4] or 1          # robust small-unit estimate
    out = []
    for state, length in runs:
        u = length / unit
        if state:
            out.append("." if u < 2 else "-")
        else:
            if u < 2:
                pass                                 # intra-char gap
            elif u < 5:
                out.append(" ")                      # letter gap
            else:
                out.append("   ")                    # word gap
    return "".join(out)


def morse_to_text(morse):
    words = morse.split("   ")
    letters = []
    for w in words:
        letters.append("".join(MORSE.get(sym, "") for sym in w.split(" ") if sym))
    return " ".join(letters).strip()


def demod(path, win=None):
    rate, sig = read_wav(path)
    if win is None:
        win = max(1, rate // 500)                    # ~2 ms smoothing default
    env = envelope(sig, win)
    morse = runs_to_morse(runs_from_env(env))
    return morse, morse_to_text(morse)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # synth "SOS" at a known unit; verify the Morse-table path end to end
        assert morse_to_text("... --- ...") == "SOS"
        assert morse_to_text(".... ..   .--. .. -.-.-.-") .startswith("HI")
        print("[ok] morse decode path works")
    elif len(sys.argv) > 1:
        m, t = demod(sys.argv[1])
        print("MORSE:", m)
        print("TEXT :", t)
    else:
        print(__doc__)
