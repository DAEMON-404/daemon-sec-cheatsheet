#!/usr/bin/env python3
"""Build a metadata index of all candidate cheatsheet files for curation.

Scans the NetrunnerVault cheatsheets + the Ethical_Hacking-Cheatsheets repo,
emitting one JSON record per file with path, size, line count, title,
frontmatter fields, and a content preview. Output: candidates.json
"""
import json, os, re, sys

SOURCES = [
    ("vault", "/Volumes/bmdrbeKUVgvV/NetrunnerVault/02Cybersecurity/Cheatsheets"),
    ("repo", "/Users/daemon1/git/Ethical_Hacking-Cheatsheets"),
]
SKIP_DIRS = {".space", ".git", "attachments", "node_modules", ".obsidian"}
SKIP_NAMES = {".DS_Store"}

def parse_frontmatter(text):
    fm = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end]
            for line in block.splitlines():
                m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
                if m:
                    fm[m.group(1).strip()] = m.group(2).strip()
    return fm

def title_from(text, path):
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return os.path.splitext(os.path.basename(path))[0]

def preview(text, n=45):
    # strip frontmatter for preview
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end+4:]
    lines = [l for l in text.splitlines()]
    return "\n".join(lines[:n])

records = []
for src, root in SOURCES:
    if not os.path.isdir(root):
        print(f"WARN missing source {root}", file=sys.stderr); continue
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            if fn in SKIP_NAMES or fn.startswith(".fuse_hidden"):
                continue
            ext = os.path.splitext(fn)[1].lower()
            if ext not in (".md", ".pdf", ".svg", ".html"):
                continue
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, root)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            rec = {"source": src, "path": full, "rel": rel, "ext": ext.lstrip("."),
                   "bytes": size, "topdir": rel.split(os.sep)[0] if os.sep in rel else "(root)"}
            if ext == ".md":
                try:
                    with open(full, encoding="utf-8", errors="replace") as f:
                        text = f.read()
                except OSError:
                    continue
                rec["lines"] = text.count("\n") + 1
                rec["title"] = title_from(text, full)
                rec["frontmatter"] = parse_frontmatter(text)
                rec["preview"] = preview(text)
                # heuristics
                rec["h2_count"] = len(re.findall(r"^##\s", text, re.M))
                rec["code_blocks"] = text.count("```") // 2
            records.append(rec)

records.sort(key=lambda r: (r["source"], r["topdir"], r["rel"].lower()))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "candidates.json")
out = os.path.normpath(out)
with open(out, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=1, ensure_ascii=False)

md = [r for r in records if r["ext"] == "md"]
print(f"total files: {len(records)}  md: {len(md)}  pdf/svg/html: {len(records)-len(md)}")
print(f"written: {out}")
