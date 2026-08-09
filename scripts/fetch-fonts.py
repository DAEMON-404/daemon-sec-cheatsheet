#!/usr/bin/env python3
"""Download latin-subset woff2 for the 3 site fonts from Google Fonts.
Best-effort: on any failure the CSS fallback stacks take over."""
import os, re, sys, urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "fonts")
OUT = os.path.normpath(OUT)
os.makedirs(OUT, exist_ok=True)

JOBS = [
    ("Chakra+Petch", 600, "chakra-petch-600.woff2"),
    ("Chakra+Petch", 700, "chakra-petch-700.woff2"),
    ("Inter", 400, "inter-400.woff2"),
    ("Inter", 500, "inter-500.woff2"),
    ("Inter", 600, "inter-600.woff2"),
    ("JetBrains+Mono", 400, "jetbrains-mono-400.woff2"),
    ("JetBrains+Mono", 600, "jetbrains-mono-600.woff2"),
]

def fetch(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()

def latin_url_from_css(css):
    # Split into @font-face blocks; pick the one whose unicode-range covers basic latin.
    blocks = re.findall(r"@font-face\s*{[^}]*}", css)
    best = None
    for b in blocks:
        m = re.search(r"url\((https://[^)]+\.woff2)\)", b)
        if not m:
            continue
        ur = re.search(r"unicode-range:\s*([^;]+);", b)
        rng = ur.group(1) if ur else ""
        if "U+0000" in rng or "U+0041" in rng or "U+00" in rng and best is None:
            best = m.group(1)
        if "U+0000" in rng:
            return m.group(1)
    if best:
        return best
    # fallback: last woff2 in the whole css (latin is usually last)
    urls = re.findall(r"url\((https://[^)]+\.woff2)\)", css)
    return urls[-1] if urls else None

ok = 0
for fam, wght, fname in JOBS:
    try:
        css = fetch(f"https://fonts.googleapis.com/css2?family={fam}:wght@{wght}&display=swap").decode("utf-8", "replace")
        url = latin_url_from_css(css)
        if not url:
            print(f"  no url for {fam} {wght}", file=sys.stderr); continue
        data = fetch(url)
        with open(os.path.join(OUT, fname), "wb") as f:
            f.write(data)
        print(f"  ok {fname} ({len(data)} bytes)")
        ok += 1
    except Exception as e:
        print(f"  FAIL {fam} {wght}: {e}", file=sys.stderr)

print(f"downloaded {ok}/{len(JOBS)} fonts -> {OUT}")
sys.exit(0 if ok else 1)
