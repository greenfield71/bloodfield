#!/usr/bin/env python3
"""Passive Domain Reconnaissance & Asset Discovery Tool for CTF OSINT.

Leverages Certificate Transparency logs (crt.sh) and Wayback Machine CDX API
to enumerate subdomains, sensitive historical endpoints, and configuration files
without sending active probing traffic directly to the target.

Features:
- Certificate Transparency log harvesting (crt.sh) with wildcard removal & dedup
- Wayback Machine CDX URL indexing (endpoint discovery, deleted paths)
- Automated detection of high-value CTF targets (.git, .env, /admin, backups, swagger, flags)
- Standard well-known endpoints probe (/robots.txt, /.well-known/security.txt)
- Optional IP address resolution for discovered subdomains via stdlib socket

Usage:
    python3 -I domain_recon.py subdomains example.com
    python3 -I domain_recon.py wayback example.com --limit 500
    python3 -I domain_recon.py scan example.com --resolve
    python3 -I domain_recon.py --test

Deps:
    Standard Python library (urllib, json, re, socket, argparse).
    Optional: requests (used if available).
"""
import argparse
import json
import re
import socket
import sys
import urllib.parse
import urllib.request

USER_AGENT = "Mozilla/5.0 (compatible; CTF-OSINT-Recon/1.0; +https://github.com/ctf-osint)"
CRTSH_URL = "https://crt.sh/?q={query}&output=json"
WAYBACK_CDX_URL = "http://web.archive.org/cdx/search/cdx"

INTERESTING_PATH_PATTERNS = [
    r"\.git(/.*)?",
    r"\.env",
    r"\.bak$",
    r"\.backup$",
    r"\.sql(\.gz)?$",
    r"\.tar(\.gz)?$",
    r"\.zip$",
    r"/admin(/.*)?",
    r"/administrator(/.*)?",
    r"/dashboard(/.*)?",
    r"/portal(/.*)?",
    r"/internal(/.*)?",
    r"/debug(/.*)?",
    r"/api(/.*)?",
    r"/v[0-9]+(/.*)?",
    r"/swagger(\.json|/.*)?",
    r"/openapi(\.json|/.*)?",
    r"/graphql",
    r"/graphiql",
    r"config(\.inc|\.json|\.php|\.yml|\.yaml)?",
    r"flag(\.txt)?",
    r"secret",
    r"token",
    r"id_rsa",
    r"passwords?",
]


# ---------------------------------------------------------------------------
# HTTP Helpers
# ---------------------------------------------------------------------------

def _fetch(url, timeout=30):
    """Fetch URL returning (status_code, body_string)."""
    headers = {"User-Agent": USER_AGENT}
    try:
        import requests
        r = requests.get(url, headers=headers, timeout=timeout)
        return r.status_code, r.text
    except ImportError:
        pass

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)


# ---------------------------------------------------------------------------
# Certificate Transparency (crt.sh)
# ---------------------------------------------------------------------------

def parse_crtsh_response(json_data, root_domain):
    """Extract and deduplicate subdomains from crt.sh JSON response."""
    root_domain = root_domain.lower().strip(".")
    subdomains = set()

    for entry in json_data:
        name_val = entry.get("name_value", "")
        common_name = entry.get("common_name", "")
        for raw in (name_val, common_name):
            if not raw:
                continue
            for line in raw.split("\n"):
                clean = line.strip().lower()
                clean = clean.lstrip("*.")  # remove wildcards
                if clean and (clean == root_domain or clean.endswith("." + root_domain)):
                    subdomains.add(clean)

    return sorted(list(subdomains))


def query_crtsh(domain):
    """Query crt.sh for all certificates matching %.domain."""
    domain = domain.lower().strip(".")
    query = f"%.{domain}"
    url = CRTSH_URL.format(query=urllib.parse.quote(query))
    code, body = _fetch(url, timeout=45)

    if code != 200:
        # Fall back to querying without wildcard
        url_direct = CRTSH_URL.format(query=urllib.parse.quote(domain))
        code, body = _fetch(url_direct, timeout=45)
        if code != 200:
            raise RuntimeError(f"crt.sh returned HTTP {code}: {body[:200]}")

    try:
        data = json.loads(body)
        return parse_crtsh_response(data, domain)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse crt.sh JSON response: {e}")


# ---------------------------------------------------------------------------
# Wayback Machine CDX API
# ---------------------------------------------------------------------------

def parse_cdx_response(json_data):
    """Parse CDX JSON table [[fl1, fl2, ...], [row1...], ...] into records."""
    if not json_data or len(json_data) < 2:
        return []

    headers = [h.lower() for h in json_data[0]]
    records = []
    for row in json_data[1:]:
        rec = dict(zip(headers, row))
        records.append(rec)
    return records


def filter_interesting_urls(urls):
    """Filter list of URLs matching high-value CTF / security patterns."""
    compiled = [re.compile(p, re.IGNORECASE) for p in INTERESTING_PATH_PATTERNS]
    matches = []
    for u in urls:
        parsed = urllib.parse.urlparse(u)
        path = parsed.path
        query = parsed.query
        full_check = f"{path}?{query}" if query else path
        matched_category = None
        for pat in compiled:
            if pat.search(full_check):
                matched_category = pat.pattern
                break
        if matched_category:
            matches.append({"url": u, "pattern": matched_category})
    return matches


def query_wayback_cdx(domain, match_type="domain", limit=1000):
    """Query Wayback CDX API for historical URLs under domain."""
    params = {
        "url": f"*.{domain}/*" if match_type == "domain" else f"{domain}/*",
        "output": "json",
        "fl": "original,timestamp,statuscode,mimetype",
        "collapse": "urlkey",
        "limit": str(limit),
    }
    url = f"{WAYBACK_CDX_URL}?{urllib.parse.urlencode(params)}"
    code, body = _fetch(url, timeout=45)
    if code != 200:
        raise RuntimeError(f"Wayback CDX API returned HTTP {code}: {body[:200]}")

    try:
        data = json.loads(body)
        records = parse_cdx_response(data)
        all_urls = [r["original"] for r in records if "original" in r]
        interesting = filter_interesting_urls(all_urls)
        return {
            "total_urls_found": len(all_urls),
            "sample_urls": all_urls[:100],
            "interesting_targets": interesting,
        }
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Wayback CDX JSON: {e}")


# ---------------------------------------------------------------------------
# Well-Known & Standard Endpoints Probe
# ---------------------------------------------------------------------------

def check_well_known(domain):
    """Check standard public configuration files on domain."""
    targets = [
        "/.well-known/security.txt",
        "/robots.txt",
        "/sitemap.xml",
    ]
    results = {}
    for path in targets:
        url = f"https://{domain}{path}"
        code, body = _fetch(url, timeout=10)
        if code == 200 and len(body.strip()) > 0:
            results[path] = {
                "status": 200,
                "url": url,
                "snippet": body[:500].strip(),
            }
        else:
            # Try HTTP if HTTPS was not reachable
            url_http = f"http://{domain}{path}"
            c2, b2 = _fetch(url_http, timeout=10)
            if c2 == 200 and len(b2.strip()) > 0:
                results[path] = {
                    "status": 200,
                    "url": url_http,
                    "snippet": b2[:500].strip(),
                }
    return results


# ---------------------------------------------------------------------------
# DNS Resolution Helper
# ---------------------------------------------------------------------------

def resolve_subdomains(subdomains, timeout=2.0):
    """Resolve list of hostnames to IP addresses using stdlib socket."""
    resolved = []
    orig_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        for host in subdomains:
            try:
                ips = socket.gethostbyname_ex(host)[2]
                resolved.append({"host": host, "ips": ips, "status": "active"})
            except socket.gaierror:
                resolved.append({"host": host, "ips": [], "status": "unresolved"})
    finally:
        socket.setdefaulttimeout(orig_timeout)
    return resolved


# ---------------------------------------------------------------------------
# Self-Test Suite
# ---------------------------------------------------------------------------

def _self_test():
    """Verify crt.sh parsing, CDX normalization, and URL pattern matching offline."""
    print("[*] Running domain_recon.py self-test suite...")

    # 1. crt.sh mock parsing
    mock_crtsh = [
        {"name_value": "*.internal.corp.com\ncorp.com", "common_name": "corp.com"},
        {"name_value": "api-v1.corp.com", "common_name": "api-v1.corp.com"},
        {"name_value": "DEV.CORP.COM\nadmin.corp.com", "common_name": "*.dev.corp.com"},
        {"name_value": "otherdomain.com", "common_name": "otherdomain.com"},  # Out of scope
    ]
    subdomains = parse_crtsh_response(mock_crtsh, "corp.com")
    assert "admin.corp.com" in subdomains
    assert "api-v1.corp.com" in subdomains
    assert "dev.corp.com" in subdomains
    assert "corp.com" in subdomains
    assert "internal.corp.com" in subdomains
    assert "otherdomain.com" not in subdomains
    assert not any(s.startswith("*") for s in subdomains)
    print(f"  [+] crt.sh response parser and wildcard cleaner [OK] ({len(subdomains)} subdomains parsed)")

    # 2. Wayback CDX JSON table parser
    mock_cdx = [
        ["original", "timestamp", "statuscode", "mimetype"],
        ["https://corp.com/index.html", "20240101", "200", "text/html"],
        ["https://corp.com/.git/config", "20240201", "200", "text/plain"],
        ["https://corp.com/api/v1/users", "20240301", "200", "application/json"],
        ["https://corp.com/backup/database.sql.gz", "20240401", "200", "application/gzip"],
        ["https://corp.com/admin/login", "20240501", "200", "text/html"],
        ["https://corp.com/secret/flag.txt", "20240601", "200", "text/plain"],
        ["https://corp.com/static/style.css", "20240701", "200", "text/css"],
    ]
    parsed_cdx = parse_cdx_response(mock_cdx)
    assert len(parsed_cdx) == 7
    assert parsed_cdx[0]["original"] == "https://corp.com/index.html"
    print("  [+] CDX tabular response parser [OK]")

    # 3. Interesting URLs security scanner
    urls = [r["original"] for r in parsed_cdx]
    hits = filter_interesting_urls(urls)
    hit_urls = [h["url"] for h in hits]
    assert "https://corp.com/.git/config" in hit_urls
    assert "https://corp.com/api/v1/users" in hit_urls
    assert "https://corp.com/backup/database.sql.gz" in hit_urls
    assert "https://corp.com/admin/login" in hit_urls
    assert "https://corp.com/secret/flag.txt" in hit_urls
    assert "https://corp.com/static/style.css" not in hit_urls
    print(f"  [+] High-value CTF target identifier ({len(hits)} sensitive paths found) [OK]")

    print("[+] All domain_recon self-tests PASSED successfully!")


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Passive Domain & Asset Reconnaissance Tool (crt.sh & Wayback CDX)")
    parser.add_argument("--test", action="store_true", help="Run offline self-test suite")
    subparsers = parser.add_subparsers(dest="subcommand")

    # subdomains
    p_sub = subparsers.add_parser("subdomains", help="Enumerate subdomains via crt.sh Certificate Transparency")
    p_sub.add_argument("domain", help="Target domain (e.g. example.com)")
    p_sub.add_argument("--resolve", action="store_true", help="Attempt DNS resolution on found subdomains")
    p_sub.add_argument("--json", action="store_true", help="Output raw JSON")

    # wayback
    p_wb = subparsers.add_parser("wayback", help="Query Wayback CDX for historical URLs and sensitive endpoints")
    p_wb.add_argument("domain", help="Target domain")
    p_wb.add_argument("--limit", type=int, default=500, help="Max URLs to fetch (default: 500)")
    p_wb.add_argument("--json", action="store_true", help="Output raw JSON")

    # scan (complete recon)
    p_scan = subparsers.add_parser("scan", help="Run comprehensive passive reconnaissance on target")
    p_scan.add_argument("domain", help="Target domain")
    p_scan.add_argument("--resolve", action="store_true", help="Resolve subdomains to IP addresses")
    p_scan.add_argument("--out", help="Save complete JSON report to file")

    args = parser.parse_args()

    if args.test:
        _self_test()
        sys.exit(0)

    if not args.subcommand:
        parser.print_help()
        sys.exit(1)

    clean_domain = args.domain.lower().strip()
    if clean_domain.startswith("http://") or clean_domain.startswith("https://"):
        clean_domain = urllib.parse.urlparse(clean_domain).netloc

    if args.subcommand == "subdomains":
        print(f"[*] Querying Certificate Transparency logs for: {clean_domain}...")
        subs = query_crtsh(clean_domain)
        print(f"[+] Found {len(subs)} unique subdomains.")

        if args.resolve:
            print("[*] Resolving subdomains via DNS...")
            resolved = resolve_subdomains(subs)
            if args.json:
                print(json.dumps(resolved, indent=2))
            else:
                for r in resolved:
                    ips_str = ", ".join(r["ips"]) if r["ips"] else "NO_IP"
                    print(f"  - {r['host']:<40} [{ips_str}]")
        else:
            if args.json:
                print(json.dumps(subs, indent=2))
            else:
                for s in subs:
                    print(f"  - {s}")

    elif args.subcommand == "wayback":
        print(f"[*] Querying Wayback CDX for URLs under: {clean_domain}...")
        wb = query_wayback_cdx(clean_domain, limit=args.limit)
        print(f"[+] Found {wb['total_urls_found']} URLs.")
        print(f"[!] Discovered {len(wb['interesting_targets'])} high-value security/CTF targets:")
        for t in wb["interesting_targets"]:
            print(f"  [!] {t['url']} (matches: {t['pattern']})")

        if args.json:
            print(json.dumps(wb, indent=2))

    elif args.subcommand == "scan":
        print(f"[*] Starting complete passive recon on: {clean_domain}")
        report = {"domain": clean_domain}

        try:
            print("  [>] Fetching Certificate Transparency subdomains...")
            subs = query_crtsh(clean_domain)
            report["subdomains_count"] = len(subs)
            if args.resolve:
                report["subdomains"] = resolve_subdomains(subs)
            else:
                report["subdomains"] = [{"host": s} for s in subs]
            print(f"  [+] Found {len(subs)} subdomains.")
        except Exception as e:
            print(f"  [-] crt.sh query failed: {e}")
            report["subdomains_error"] = str(e)

        try:
            print("  [>] Fetching Wayback Machine CDX endpoints...")
            wb = query_wayback_cdx(clean_domain, limit=1000)
            report["wayback_total_urls"] = wb["total_urls_found"]
            report["interesting_targets"] = wb["interesting_targets"]
            print(f"  [+] Found {wb['total_urls_found']} archived URLs, {len(wb['interesting_targets'])} sensitive paths.")
        except Exception as e:
            print(f"  [-] Wayback query failed: {e}")
            report["wayback_error"] = str(e)

        try:
            print("  [>] Checking standard endpoints (/robots.txt, security.txt)...")
            wk = check_well_known(clean_domain)
            report["well_known"] = wk
            for path, info in wk.items():
                print(f"  [+] Discovered {path} (HTTP {info['status']})")
        except Exception as e:
            report["well_known_error"] = str(e)

        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            print(f"[+] Full recon report written to {args.out}")
        else:
            print("\n" + "=" * 50)
            print(f"RECON SUMMARY: {clean_domain}")
            print(f"Subdomains: {report.get('subdomains_count', 0)}")
            print(f"Sensitive URLs: {len(report.get('interesting_targets', []))}")
            for t in report.get("interesting_targets", [])[:15]:
                print(f"  * {t['url']}")
            print("=" * 50)


if __name__ == "__main__":
    main()
