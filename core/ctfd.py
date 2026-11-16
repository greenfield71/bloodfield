"""Build a vendored umbra2728 ``CTFdClient`` from ctf.conf, resolving auth in this order:
token  >  explicit cookie (ctf.conf / $CTFD_SESSION)  >  browser auto-extract (Firefox/Chrome).

The browser path lets "just give a link" work when you are already logged into the CTF; if
nothing resolves, a one-line instruction tells you to paste the ``session`` cookie.
"""
from __future__ import annotations

import glob
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from ctfd_mcp.config import Config
from ctfd_mcp.ctfd_client import CTFdClient

from . import coord


def _firefox_session(dom: str) -> str | None:
    home = Path.home()
    dbs: list[str] = []
    for base in (
        home / ".mozilla/firefox",
        home / ".config/mozilla/firefox",
        home / "snap/firefox/common/.mozilla/firefox",
    ):
        dbs += glob.glob(str(base / "*/cookies.sqlite"))
    for db in dbs:
        tmp = tempfile.mktemp(suffix=".sqlite")
        try:
            shutil.copy2(db, tmp)
            con = sqlite3.connect(tmp)
            rows = con.execute(
                "SELECT value, host FROM moz_cookies WHERE name='session'"
            ).fetchall()
            con.close()
            for value, host in rows:
                h = host.lstrip(".")
                if dom == h or dom.endswith("." + h) or h.endswith("." + dom):
                    return value
        except Exception:
            continue
        finally:
            with _suppress():
                os.unlink(tmp)
    return None


def _bc3_session(dom: str, browser: str) -> str | None:
    try:
        import browser_cookie3 as bc3
    except Exception:
        return None
    order = []
    for name in (browser, "firefox", "chrome", "chromium"):
        fn = getattr(bc3, name, None)
        if fn and fn not in order:
            order.append(fn)
    order.append(bc3.load)
    for fn in order:
        try:
            for c in fn(domain_name=dom):
                if c.name == "session":
                    return c.value
        except Exception:
            continue
    return None


def resolve_session(url: str) -> tuple[str | None, str | None]:
    raw = coord.get("CTFD_COOKIE").strip()
    if raw:
        import re
        m = re.search(r"session=([^;]+)", raw)
        return (m.group(1) if m else raw), "config:CTFD_COOKIE"
    env = os.environ.get("CTFD_SESSION", "").strip()
    if env:
        return env, "env:CTFD_SESSION"
    dom = coord.domain(url)
    br = coord.get("BROWSER").strip().lower()
    val = _firefox_session(dom) if br.startswith("f") else None
    if val:
        return val, "firefox"
    val = _bc3_session(dom, br)
    if val:
        return val, f"browser:{br or 'auto'}"
    val = _firefox_session(dom)
    if val:
        return val, "firefox"
    return None, None


def make_client(url: str | None = None):
    """Return (client, url, auth_source). Raises SystemExit with a clear fix if no auth."""
    url = (url or coord.get("CTFD_URL")).rstrip("/")
    if not url:
        raise SystemExit("CTFD_URL not set — pass a URL (`bin/ctf sync <url>`) or set it in ctf.conf")
    # Accept a challenges-page URL (e.g. .../challenges) and reduce it to the site origin,
    # since the API is always rooted at "/api/v1/..." off the origin, not off that path.
    parts = urlsplit(url)
    url = f"{parts.scheme}://{parts.netloc}"
    ua = coord.get("CTFD_USER_AGENT").strip() or None
    token = coord.get("CTFD_TOKEN").strip()
    if token:
        return CTFdClient(Config(url, token=token, user_agent=ua)), url, "token"
    session, src = resolve_session(url)
    if not session:
        raise SystemExit(
            "No CTFd auth found. Do ONE of:\n"
            "  * set CTFD_TOKEN in ctf.conf (Settings -> Access Tokens on CTFd), or\n"
            "  * set CTFD_COOKIE=session=<value> in ctf.conf (devtools -> Application -> Cookies), or\n"
            "  * log into the CTF in Firefox/Chrome first (auto-extracted)."
        )
    cfg = Config(
        url,
        session_cookie=session,
        csrf_token=coord.get("CTFD_CSRF_TOKEN").strip() or None,
        user_agent=ua,
    )
    return CTFdClient(cfg), url, src


class _suppress:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return True
