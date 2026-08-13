#!/usr/bin/env python3
"""Post-modernization sanity check on generated content."""
import json, os, re, sys, glob

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SHEETS = os.path.join(ROOT, "src", "content", "sheets")
TAX = {"active-directory","enumeration","exploitation","privilege-escalation",
       "password-attacks","web","tunneling-pivoting","cryptography","dfir",
       "tools","linux-it","git-workflow"}

manifest = json.load(open(os.path.join(ROOT, "content-manifest.json")))
expected = {(s["category"], s["slug"]) for s in manifest["sheets"]}

files = glob.glob(os.path.join(SHEETS, "**", "*.md"), recursive=True)
found = set()
issues = []
warns = []

for f in files:
    rel = os.path.relpath(f, SHEETS)
    txt = open(f, encoding="utf-8", errors="replace").read()
    if not txt.startswith("---"):
        issues.append(f"{rel}: no frontmatter"); continue
    end = txt.find("\n---", 3)
    fm = txt[3:end]
    body = txt[end+4:]
    def field(name):
        m = re.search(rf"^{name}:\s*(.*)$", fm, re.M)
        return m.group(1).strip() if m else None
    cat = field("category")
    title = field("title")
    if cat not in TAX: issues.append(f"{rel}: bad/missing category '{cat}'")
    if not title: issues.append(f"{rel}: missing title")
    # slug from filename
    slug = os.path.splitext(os.path.basename(f))[0]
    found.add((cat, slug))
    # InternalAllTheThings is mirrored on-site under /internal, so a sheet
    # linking the live upstream site walks the reader off the deployment.
    for m in re.finditer(r"https?://swisskyrepo\.github\.io/InternalAllTheThings/(\S*?)[)\s]", body):
        issues.append(f"{rel}: links live IATT site, use /internal/{m.group(1).strip('/')}")
    # leftover Obsidian syntax
    if re.search(r"\[\[[^\]]+\]\]", body): warns.append(f"{rel}: leftover [[wikilink]]")
    if re.search(r"!\[\[", body): warns.append(f"{rel}: leftover ![[embed]]")
    if "%%" in body: warns.append(f"{rel}: leftover %%comment%%")
    # unlabeled code fences
    fences = re.findall(r"^```(.*)$", body, re.M)
    unl = sum(1 for i,x in enumerate(fences) if i % 2 == 0 and not x.strip())
    if unl: warns.append(f"{rel}: {unl} code fence(s) without a language")

missing = expected - found
extra = found - expected

print(f"files on disk : {len(files)}")
print(f"manifest wants: {len(expected)}")
print(f"matched       : {len(expected & found)}")
if missing:
    print(f"\nMISSING ({len(missing)}):")
    for c, s in sorted(missing): print(f"  {c}/{s}")
if extra:
    print(f"\nEXTRA/misplaced ({len(extra)}):")
    for c, s in sorted(extra): print(f"  {c}/{s}")
if issues:
    print(f"\nISSUES ({len(issues)}):")
    for i in issues: print(f"  {i}")
if warns:
    print(f"\nWARNINGS ({len(warns)}):")
    for w in warns[:40]: print(f"  {w}")
    if len(warns) > 40: print(f"  ... +{len(warns)-40} more")

ok = not missing and not issues
print("\n" + ("PASS" if ok else "NEEDS ATTENTION"))
sys.exit(0 if ok else 1)
