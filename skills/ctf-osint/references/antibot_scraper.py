#!/usr/bin/env python3
"""Anti-Bot Scraper using Playwright Headed Browser with Persistent Profile.

Used in CTF OSINT challenges (e.g. newspaper archives or gated platforms protected
by Cloudflare / bot challenges where headless requests receive HTTP 403):
- Launches persistent Chromium context (`launch_persistent_context`)
- Disables automation flags (`--disable-blink-features=AutomationControlled`)
- Reuses browser cookies/cache across runs to pass interstitials
- Optional screenshot & tesseract OCR extraction

Usage:
    python3 -I antibot_scraper.py fetch https://chroniclingamerica.loc.gov/... output.html
    python3 -I antibot_scraper.py screenshot https://target.com/ page.png
    python3 -I antibot_scraper.py --test

Deps:
    pip install --user playwright pytesseract
    playwright install chromium
"""
import os
import sys


DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

CHROMIUM_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-infobars",
    "--start-maximized",
]


def build_context_options(user_data_dir="/tmp/playwright_osint_profile", headless=False, user_agent=None):
    """Generate launch arguments and options for persistent context."""
    os.makedirs(user_data_dir, exist_ok=True)
    return {
        "user_data_dir": user_data_dir,
        "headless": headless,
        "user_agent": user_agent or DEFAULT_UA,
        "args": CHROMIUM_ARGS,
        "viewport": {"width": 1920, "height": 1080},
    }


def fetch_page(url, user_data_dir="/tmp/playwright_osint_profile", headless=False,
               wait_until="networkidle", screenshot_path=None, timeout_ms=30000):
    """Fetch full HTML page content bypassing client-side anti-bot gates."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("Playwright not installed. Install with: pip install --user playwright && playwright install chromium")

    opts = build_context_options(user_data_dir=user_data_dir, headless=headless)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            opts["user_data_dir"],
            headless=opts["headless"],
            user_agent=opts["user_agent"],
            args=opts["args"],
            viewport=opts["viewport"],
        )
        page = ctx.new_page()
        page.goto(url, wait_until=wait_until, timeout=timeout_ms)
        content = page.content()
        if screenshot_path:
            page.screenshot(path=screenshot_path, full_page=True)
        ctx.close()
        return content


def ocr_image(image_path, psm=6):
    """Run tesseract OCR on an image file using psm mode."""
    import subprocess
    cmd = ["tesseract", image_path, "stdout", "--psm", str(psm)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return res.stdout


def _self_test():
    # 1. Test profile and options builder
    opts = build_context_options("/tmp/_test_osint_profile", headless=True)
    assert opts["headless"] is True
    assert "--disable-blink-features=AutomationControlled" in opts["args"]
    assert "Mozilla/5.0" in opts["user_agent"]
    assert os.path.exists("/tmp/_test_osint_profile")

    # 2. Check Playwright availability
    try:
        import playwright
        has_pw = True
    except ImportError:
        has_pw = False

    print(f"[ok] antibot_scraper options builder verified (Playwright present={has_pw})")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        _self_test()
    elif len(sys.argv) > 3 and sys.argv[1] == "fetch":
        url, out = sys.argv[2], sys.argv[3]
        html = fetch_page(url)
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved {len(html)} chars to {out}")
    elif len(sys.argv) > 3 and sys.argv[1] == "screenshot":
        url, shot = sys.argv[2], sys.argv[3]
        fetch_page(url, screenshot_path=shot)
        print(f"Saved screenshot to {shot}")
    else:
        print(__doc__)
