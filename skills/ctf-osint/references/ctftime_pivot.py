#!/usr/bin/env python3
"""CTFtime OSINT pivots: team / event lookup via the JSON API with HTML fallback,
plus a leetspeak-tolerant regex scan across a team's results.

CTFtime's API sometimes returns null/empty for valid ids — fall back to scraping
the HTML page. Be polite: a descriptive UA, and don't hammer (the API asks for it).

    python3 -I ctftime_pivot.py team 1005
    python3 -I ctftime_pivot.py event 2302
    python3 -I ctftime_pivot.py leet "flag"        # -> regex that matches 1337-speak
    python3 -I ctftime_pivot.py --test

Deps: requests (stdlib urllib fallback built in).
"""
import json
import re
import sys

UA = "ctf-osint-pivot/1.0 (CTF research; contact via challenge platform)"
API = "https://ctftime.org/api/v1"


def _get(url):
    try:
        import requests
        r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
        return r.status_code, r.text
    except ImportError:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")


def team(team_id):
    code, body = _get(f"{API}/teams/{team_id}/")
    if code == 200 and body.strip() and body.strip() not in ("null", "{}"):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            pass
    # HTML fallback
    code, html = _get(f"https://ctftime.org/team/{team_id}")
    m = re.search(r"<h2[^>]*>(.*?)</h2>", html, re.S)
    return {"id": team_id, "name_html": (m.group(1).strip() if m else None),
            "source": "html"}


def event(event_id):
    code, body = _get(f"{API}/events/{event_id}/")
    if code == 200 and body.strip() and body.strip() not in ("null", "{}"):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            pass
    code, html = _get(f"https://ctftime.org/event/{event_id}")
    m = re.search(r"<h2[^>]*>(.*?)</h2>", html, re.S)
    return {"id": event_id, "name_html": (m.group(1).strip() if m else None),
            "source": "html"}


_LEET = {"a": "[a4@]", "e": "[e3]", "i": "[i1!|]", "l": "[l1|]", "o": "[o0]",
         "s": "[s5$]", "t": "[t7+]", "g": "[g9]", "b": "[b8]", "z": "[z2]"}


def leet_regex(word):
    """Build a case-insensitive regex that matches leetspeak variants of `word`."""
    return "".join(_LEET.get(c.lower(), re.escape(c)) for c in word)


def scan(text, word):
    pat = re.compile(leet_regex(word), re.IGNORECASE)
    return pat.findall(text)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "--test":
        rx = leet_regex("flag")
        assert re.fullmatch(rx, "F1@9", re.IGNORECASE)      # F l a g -> F 1 @ 9
        assert scan("my name is l33t h4x0r", "leet")
        print("[ok] leetspeak regex:", rx)
    elif args[0] == "team":
        print(json.dumps(team(args[1]), indent=2)[:2000])
    elif args[0] == "event":
        print(json.dumps(event(args[1]), indent=2)[:2000])
    elif args[0] == "leet":
        print(leet_regex(args[1]))
    else:
        print(__doc__)
