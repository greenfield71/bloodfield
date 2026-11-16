---
name: ctf-web
description: >-
  Web exploitation CTF challenges. Use when given a URL / http(s) endpoint, a web
  app, or its source, and the goal is a flag via a web vulnerability. Covers recon
  and content discovery, SQL injection, XSS, SSTI, SSRF, LFI/RFI, JWT, IDOR,
  insecure deserialization, command injection, plus modern archetypes: parser /
  encoding differentials (js-yaml vs PyYAML, json vs ujson, NFKC, URL double-decode,
  proxy path normalization), framework / in-the-wild CVEs (Next.js React2Shell
  CVE-2025-55182, workerd/V8, Traefik, MLflow), and XS-leaks / client-side oracles
  (frame count, status code, CSS injection) vs admin bots. Prefer curl and
  python-requests. Triggers on: "web", "SQLi", "SQL injection", "XSS", "SSTI",
  "SSRF", "LFI", "RFI", "JWT", "IDOR", "deserialization", "command injection",
  "sqlmap", "gobuster", "ffuf", "cookie", "login bypass", "file upload", "http",
  "url", "parser differential", "encoding differential", "Next.js", "React",
  "Server Action", "RSC", "React2Shell", "CVE", "workerd", "V8", "Traefik",
  "MLflow", "XS-leak", "XSLeak", "CSS injection", "bcrypt", "middleware", "method
  override", "path normalization", "prototype pollution", "desync".
---

# CTF Web Exploitation

Prefer fast, reproducible scripted probing with `curl` and Python `requests`.
Keep sessions stateful: `s = requests.Session()`.

### Tools & Setup (Arch Linux)
Check `command -v` first (honoring "Install Nothing Silently"):
```bash
command -v curl || sudo pacman -S curl
command -v python3 && python3 -c "import requests" 2>/dev/null || pip install --user requests
command -v ffuf || paru -S ffuf
command -v gobuster || paru -S gobuster
command -v sqlmap || paru -S sqlmap
command -v jwt_tool || paru -S jwt-tool
```

**Meta note (2025–2026+):** Challenges are increasingly **version-specific** and **architecture-aware**. Rather than blind fuzzing, prioritize reading provided source code, diffing exact package versions (`package.json`, `package-lock.json`, `requirements.txt`, `Cargo.toml`, `go.mod`), and analyzing how different components along the request pipeline parse identical input.

Reference files:
- Detailed payload dictionary: [`references/payloads.md`](references/payloads.md)
- XS-Leak & client-side oracle toolkit: [`references/xs_leak_oracle.py`](references/xs_leak_oracle.py)

---

## Decision Tree

When evaluating a challenge, match observed stack characteristics or clues to the primary attack vector:

| Clue / Stack / Observation | Vulnerability Class | Immediate Action | Payload / Tool |
| :--- | :--- | :--- | :--- |
| **Next.js 14–16, React 19**, `Next-Action` header | RSC Flight Deserialization (**React2Shell CVE-2025-55182**) | Extract action ID from build manifests; forge multipart deserialization | `payloads.md` §1 |
| **Next.js Server Actions** with internal microservices | Server Action Parameter Forgery / SSRF | Inspect client source map for deprecated fields (`baoAddr`); steal Vault tokens | `payloads.md` §1 |
| **Cloudflare Workers / workerd runtime**, V8 engine | JS Engine Sandbox Escape (**CVE-2022-1310**) | Trigger RegExp `lastIndex` missing write barrier UAF; WASM jump-table overwrite | `payloads.md` §1 |
| **Traefik + Python/Flask/MLflow** backend | Reverse Proxy Routing Differential | Bypass `PathPrefix(/api)` auth using `/%2fapi/`; MLflow artifact `..` traversal | `payloads.md` §1 |
| **Multi-language verification** (JS + Python, Go + Python) | Parser / Encoding Differentials | Diff YAML merge keys (`<<:`), JSON surrogates (`\ud800`), or NFKC normalization | `payloads.md` §2 |
| **Single-decode route** followed by second unquote | Double-URL-Decode Path Traversal | Bypass extension checks with `%2500` null byte or `%252e%252e%252f` | `payloads.md` §2 |
| **Admin bot visits URL**; target has search/results iframe | XS-Leak (Frame Counting) | Open cross-origin window; measure `win.length` across character guesses | `xs_leak_oracle.py --frame` |
| **Admin bot visits URL**; secret in DOM/attribute | CSS Injection Prefix Oracle | Attribute selectors `input[value^="..."]` leaking chars via background URLs | `xs_leak_oracle.py --css` |
| **Admin bot visits URL**; 403 vs 404 response | Status-Code Side-Channel | Probe endpoints cross-origin via `<script>`/`<img>` `onload`/`onerror` | `xs_leak_oracle.py --status` |
| **Password/secret check** with length ≥ 72 bytes | bcrypt 72-Byte Truncation | Truncation collision; pad prefix to byte 71 for byte-at-a-time recovery | `xs_leak_oracle.py --bcrypt` |
| **Express.js** with `methodOverride` and CSRF | Middleware Ordering Bypass | Issue `POST /path?_method=GET` to skip POST-only CSRF verification | `payloads.md` §4 |
| **Rust web service** with path traversal + file write | Arbitrary Code Patching via procfs | Leak PIE base via `/proc/self/maps`; patch conditional branch via `/proc/self/mem` | `payloads.md` §4 |
| **SQLite query** with double quotes in `SET` clause | SQLite Double-Quote Column Fallback | Use `"col_name"` to reference existing column without quotes | `payloads.md` §4 |
| `{{...}}`, `${...}`, `<%= ... %>` in template | SSTI (Jinja2 / Twig / FreeMarker / Nunjucks) | Identify template engine syntax; execute command via reflection or builtins | `payloads.md` §5 |
| Dynamic SQL with user input | SQL Injection (SQLi) | Probe `'` / `"`; check UNION count; extract schema or run blind boolean/time | `payloads.md` §6 |
| User input reflected in HTML/DOM | XSS & CSP Bypass | Break out of context; bypass CSP via allowed CDNs or gadgets; exfiltrate DOM | `payloads.md` §7 |
| URL fetcher / webhook tester | SSRF | Target `127.0.0.1`, cloud metadata `169.254.169.254`, internal services | `payloads.md` §1 |
| File inclusion / path parameter | LFI / RFI / Directory Traversal | Test `php://filter/`, `data://`, `/proc/self/environ`, null-byte bypass | `payloads.md` §8 |
| JWT in cookie / Authorization header | JWT Tampering | Test `alg:none`, crack weak HMAC secret, test RS256→HS256 key confusion | `payloads.md` §10 |

---

## Attack Methodology

### Step 1 — Reconnaissance & Source Audit
1. **Network & Headers:**
   ```bash
   U="http://host:port"
   curl -sI "$U"                       # Server, Set-Cookie, X-Powered-By, CSP, framework
   curl -s "$U" | grep -iE 'csrf|token|action=|Next-Action|_next|api/'
   curl -s "$U/robots.txt" "$U/sitemap.xml" "$U/.git/HEAD" "$U/.env"
   ```
2. **Examine Dependencies:**
   - Check `package.json` / `package-lock.json`: Next.js version (CVE-2025-55182 if React 19 Server Actions), Express middlewares, DOMPurify.
   - Check `requirements.txt`: `ujson` vs `json`, PyYAML version, Flask / Werkzeug version.
   - Check reverse proxy configuration: Nginx `merge_slashes`, Traefik version and path rules.
3. **Source Code Review:**
   - Search for endpoints accepting object deserialization, reflection, or raw parameters.
   - Identify every parser in the pipeline and check for encoding normalization differences.

---

### Step 2 — Vulnerability Exploitation Playbook

#### 1. Framework & CVE Exploitation
- **Next.js React2Shell (CVE-2025-55182):**
  - Look for Server Actions indicated by the `Next-Action` HTTP header.
  - Send crafted multipart request with `constructor:constructor` gadget targeting `Function`.
  - If blocked by WAF/reverse proxy, encode parts with `charset=utf-16le`.
  - See full curl examples in [`references/payloads.md`](references/payloads.md#nextjs-react2shell-cve-2025-55182--rsc-flight-protocol-deserialization).
- **Traefik + Backend Path Differentials:**
  - If Traefik guards an administrative path (`PathPrefix(/api)`), test `/%2fapi/...`.
  - Chain with backend path traversal (e.g. MLflow artifact roots) to read host `/flag`.
- **workerd / V8 Sandbox Escapes:**
  - If running in Cloudflare Workers / workerd, look for RegExp write-barrier bugs (CVE-2022-1310) to corrupt heap pointers, overwrite WASM jump-tables, and execute `/readflag`.

#### 2. Parser & Encoding Differentials
- **js-yaml vs PyYAML:**
  - Duplicate YAML merge keys (`<<:`) overwrite values differently in Python vs JavaScript.
  - Exploit to pass authorization checks in JS while assigning administrative roles in Python.
- **json vs ujson:**
  - Lone surrogates (`\ud800`) cause `ujson` to truncate or discard following characters while Python's `json` retains them.
- **NFKC / Casefold Unicode Normalization:**
  - Characters like `ｓｙｓｔｅｍ` (`\uff53...`) bypass regex blacklists but normalize to `system` upon `unicodedata.normalize('NFKC', ...)`.
- **Reverse Proxy Normalization:**
  - Test `/..;/` (Spring/Tomcat), `/%252e%252e%252f` (double-encoded traversal), and double slashes `//`.

#### 3. XS-Leaks & Client-Side Oracles
When an admin bot visits an attacker URL:
- **Frame Counting (`window.length`):**
  - Use `win = window.open(...)` and read `win.length` to detect whether search queries matched.
  - Generate harness using [`references/xs_leak_oracle.py`](references/xs_leak_oracle.py) (`--frame`).
- **CSS-Injection Attribute Prefix Oracle:**
  - Inject CSS rules: `input[name="csrf"][value^="<char>"] { background: url(...) }`.
  - Bypass partial sanitizers (such as `svg-hush`) using `image-set()`.
  - Generate rules using [`references/xs_leak_oracle.py`](references/xs_leak_oracle.py) (`--css`).
- **Status-Code Error Leak:**
  - Differentiate 403 Forbidden vs 404 Not Found cross-origin using `<script>` / `<img>` error events.

#### 4. Modern Auth & Session Quirks
- **bcrypt 72-Byte Truncation:**
  - Passwords longer than 72 bytes share hash prefixes.
  - If hashing `input + secret`, pad `input` to 71 bytes to isolate the 72nd byte for byte-at-a-time recovery.
  - Calculate padding tables with [`references/xs_leak_oracle.py`](references/xs_leak_oracle.py) (`--bcrypt`).
- **Express Middleware Ordering:**
  - When `express.urlencoded()` runs before `methodOverride()`, a request with `_method=GET` can bypass POST-only CSRF checks.
- **Rust `/proc/self/mem`:**
  - Use path traversal to read `/proc/self/maps` and leak PIE base, then write to `/proc/self/mem` to patch conditional jumps.
- **SQLite Double-Quoted Tokens:**
  - Double quotes around column names compile to column references (`SET crew = "age"`).

---

### Step 3 — Scripted Probing Template

```python
#!/usr/bin/env python3
import requests

BASE_URL = "http://target.local"
s = requests.Session()

def probe():
    # 1. Recon request
    r = s.get(f"{BASE_URL}/")
    print(f"[*] Base status: {r.status_code}, server: {r.headers.get('Server')}")
    
    # 2. Targeted test
    # (replace with specific vector: RSC action, parser diff, or SQLi)
    test_url = f"{BASE_URL}/api/test"
    resp = s.post(test_url, json={"test": "probe"})
    if "flag{" in resp.text:
        print("[+] Flag found:", resp.text)

if __name__ == "__main__":
    probe()
```
