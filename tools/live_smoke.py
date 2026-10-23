#!/usr/bin/env python3
"""Host-up smoke for BEE Check on Streamlit Community Cloud.

Community Cloud redirects anonymous clients through share.streamlit.io auth cookies, then
serves a JS shell. This script checks HTTP 200 after that dance and looks for a distinctive
marker. It does not drive the Streamlit websocket UI (see QA live-smoke.md for that).

Usage:
  python tools/live_smoke.py
  python tools/live_smoke.py --url https://beecalculator.streamlit.app/
"""

from __future__ import annotations

import argparse
import http.cookiejar
import sys
import urllib.error
import urllib.request

DEFAULT_URL = "https://beecalculator.streamlit.app/"
# Prefer app strings when present; fall back to Cloud shell markers (SPA first paint).
MARKERS = (
    "BEE Check",
    "Privacy",
    "streamlitAppPage",
    "You need to enable JavaScript to run this app",
)


def fetch(url: str, timeout: float) -> tuple[int, str]:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "BEECheck-live-smoke/1.0 (+prod-v1-hardening)"},
    )
    with opener.open(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return int(resp.status), body


def main() -> int:
    p = argparse.ArgumentParser(description="Live host-up smoke for BEE Check")
    p.add_argument("--url", default=DEFAULT_URL)
    p.add_argument("--timeout", type=float, default=45.0)
    args = p.parse_args()

    try:
        status, body = fetch(args.url, args.timeout)
    except urllib.error.HTTPError as e:
        print(f"FAIL: HTTP {e.code} for {args.url}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001 — CLI surface
        print(f"FAIL: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    if status != 200:
        print(f"FAIL: expected HTTP 200, got {status}", file=sys.stderr)
        return 1

    hit = next((m for m in MARKERS if m in body), None)
    if not hit:
        print("FAIL: HTTP 200 but no distinctive marker in body", file=sys.stderr)
        print(f"looked for: {', '.join(MARKERS)}", file=sys.stderr)
        return 1

    print(f"PASS: HTTP {status}; marker={hit!r}; url={args.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
