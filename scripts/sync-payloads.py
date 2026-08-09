#!/usr/bin/env python3
"""Mirror PayloadsAllTheThings (MIT, swisskyrepo) into the site as the `payloads`
content collection. Faithful markdown mirror; images + raw payload files hotlink
to upstream GitHub. Deterministic + re-runnable.

Usage: python3 scripts/sync-payloads.py /path/to/patt-clone <sha>
"""
import json, os, re, shutil, sys

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(REPO, "src", "content", "payloads")
VENDOR = os.path.join(REPO, "vendor", "PayloadsAllTheThings")
UPSTREAM = "https://github.com/swisskyrepo/PayloadsAllTheThings"

SRC = sys.argv[1] if len(sys.argv) > 1 else None
SHA = sys.argv[2] if len(sys.argv) > 2 else "master"
if not SRC or not os.path.isdir(SRC):
    sys.exit("usage: sync-payloads.py <patt-clone-dir> <sha>")

# Skip non-topic root entries.
SKIP_TOP = {".git", ".github", "Images", "assets"}
SKIP_FILES = {"readme.md", "contributing.md", "license.md", "code_of_conduct.md",
              "security.md", "changelog.md", "_template_vulnerability.md"}


def slugify(s):
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-") or "x"


def topic_slug(topic):
    return slugify(topic)


def file_slug(name):  # name without .md
    return slugify(name)


def blob_url(relpath):
    # GitHub blob URL for a repo-relative path (spaces -> %20)
    from urllib.parse import quote
    return f"{UPSTREAM}/blob/{SHA}/{quote(relpath)}"


def raw_url(relpath):
    from urllib.parse import quote
    return f"https://raw.githubusercontent.com/swisskyrepo/PayloadsAllTheThings/{SHA}/{quote(relpath)}"


# --- Discover all mirrored markdown, build a path->route map first --------------
topics = sorted(d for d in os.listdir(SRC)
                if os.path.isdir(os.path.join(SRC, d)) and d not in SKIP_TOP
                and not d.startswith(".") and not d.startswith("_"))

# map: repo-relative md path (posix) -> site route (/payloads/...)
route_of = {}
md_files = []  # (topic, relpath, abspath, is_readme)
for topic in topics:
    tdir = os.path.join(SRC, topic)
    for root, _dirs, files in os.walk(tdir):
        for f in files:
            if not f.lower().endswith(".md"):
                continue
            if f.lower() in SKIP_FILES and os.path.basename(root) != topic:
                pass  # only skip template-ish names anywhere
            abspath = os.path.join(root, f)
            relpath = os.path.relpath(abspath, SRC).replace(os.sep, "/")
            is_readme = f.lower() == "readme.md"
            ts = topic_slug(topic)
            # sub-path inside the topic (for nested files), slugified per segment
            inner = os.path.relpath(abspath, tdir).replace(os.sep, "/")
            if is_readme and "/" not in inner:
                route = f"/payloads/{ts}"
                out_id = f"{ts}/index"
            else:
                parts = inner[:-3].split("/")  # drop .md
                seg = "/".join(slugify(p) for p in parts)
                route = f"/payloads/{ts}/{seg}"
                out_id = f"{ts}/{seg}"
            route_of[relpath] = route
            md_files.append((topic, relpath, abspath, is_readme, out_id, route))

# --- Link rewriting -------------------------------------------------------------
LINK = re.compile(r"(!?)\[([^\]]*)\]\(([^)]+)\)")


# Absolute upstream URLs that actually point back into the repo. Two hosts:
#   github.com/swisskyrepo/PayloadsAllTheThings/(blob|tree|raw)/<ref>/<path>
#   raw.githubusercontent.com/swisskyrepo/PayloadsAllTheThings/<ref>/<path>
UPSTREAM_URL = re.compile(
    r"^https?://(?:www\.)?github\.com/swisskyrepo/PayloadsAllTheThings/(?:blob|tree|raw)/[^/]+/(.*)$"
    r"|^https?://raw\.githubusercontent\.com/swisskyrepo/PayloadsAllTheThings/[^/]+/(.*)$",
    re.I,
)
_route_lc = None  # built lazily: lowercased path -> route


def _rlc():
    global _route_lc
    if _route_lc is None:
        _route_lc = {k.lower(): v for k, v in route_of.items()}
    return _route_lc


def route_for_repo_path(resolved, anchor):
    """Map a repo-relative path to an internal route or a pinned upstream URL."""
    resolved = resolved.strip("/")
    if resolved == "":
        return "/payloads" + anchor
    low = resolved.lower()
    if low.endswith(".md"):
        r = _rlc().get(low)
        return (r + anchor) if r else blob_url(resolved) + anchor
    # a directory link (topic listing) -> that topic's index if mirrored
    idx = _rlc().get((resolved + "/readme.md").lower())
    if idx:
        return idx + anchor
    # non-md file (image, txt, py, ...) -> pinned raw upstream
    return raw_url(resolved) + anchor


def resolve(cur_relpath, target):
    """Return rewritten URL for a markdown link target, or None to leave as-is."""
    from urllib.parse import unquote
    t = target.strip().strip("<>").strip()
    anchor = ""

    # 1) Absolute upstream URL pointing into the repo -> internalize.
    m = UPSTREAM_URL.match(t)
    if m:
        path = m.group(1) or m.group(2) or ""
        path = path.split("?", 1)[0]  # drop ?raw=true etc.
        if "#" in path:
            path, a = path.split("#", 1); anchor = "#" + a
        return route_for_repo_path(unquote(path), anchor)

    # 2) Other absolute / protocol-relative / anchors / mailto -> leave.
    if re.match(r"^([a-z]+:|//|#|mailto:)", t, re.I):
        return None

    # 3) Relative in-repo link.
    if "#" in t:
        t, a = t.split("#", 1); anchor = "#" + a
    if not t:
        return None
    cur_dir = os.path.dirname(cur_relpath)
    resolved = os.path.normpath(os.path.join(cur_dir, unquote(t))).replace(os.sep, "/")
    return route_for_repo_path(resolved, anchor)


def rewrite_body(cur_relpath, body):
    def repl(m):
        bang, text, target = m.group(1), m.group(2), m.group(3)
        # ignore link targets wrapped in <...> or containing spaces we can't parse cleanly
        new = resolve(cur_relpath, target)
        if new is None:
            return m.group(0)
        return f"{bang}[{text}]({new})"
    return LINK.sub(repl, body)


def title_from(body, fallback):
    m = re.search(r"^\s*#\s+(.+?)\s*$", body, re.M)
    if m:
        return m.group(1).strip()
    return fallback


def yaml_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


# --- Emit -----------------------------------------------------------------------
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT, exist_ok=True)

count = 0
topics_seen = {}
for topic, relpath, abspath, is_readme, out_id, route in md_files:
    raw = open(abspath, encoding="utf-8", errors="replace").read()
    body = rewrite_body(relpath, raw)
    fallback = topic if is_readme else os.path.splitext(os.path.basename(abspath))[0]
    title = title_from(raw, fallback)
    src_url = blob_url(relpath)
    fm = (
        "---\n"
        f'title: "{yaml_escape(title)}"\n'
        f'topic: "{yaml_escape(topic)}"\n'
        f'topicSlug: "{topic_slug(topic)}"\n'
        f'sourcePath: "{yaml_escape(relpath)}"\n'
        f'sourceUrl: "{src_url}"\n'
        f'sha: "{SHA}"\n'
        f"isReadme: {'true' if is_readme else 'false'}\n"
        "---\n\n"
    )
    dst = os.path.join(OUT, out_id + ".md")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w", encoding="utf-8").write(fm + body.lstrip("\n"))
    count += 1
    topics_seen.setdefault(topic, 0)
    topics_seen[topic] += 1

# --- Vendor the license ---------------------------------------------------------
os.makedirs(VENDOR, exist_ok=True)
lic_src = None
for cand in ("LICENSE.md", "LICENSE", "LICENSE.txt"):
    p = os.path.join(SRC, cand)
    if os.path.isfile(p):
        lic_src = p
        break
if lic_src:
    shutil.copyfile(lic_src, os.path.join(VENDOR, os.path.basename(lic_src)))

# --- Manifest -------------------------------------------------------------------
manifest = {
    "upstream": UPSTREAM,
    "sha": SHA,
    "topics": len(topics_seen),
    "pages": count,
    "topicList": sorted(topics_seen.keys()),
}
open(os.path.join(REPO, "payloads-manifest.json"), "w").write(json.dumps(manifest, indent=2))

print(f"mirrored {count} pages across {len(topics_seen)} topics @ {SHA}")
print(f"license: {'copied' if lic_src else 'NOT FOUND'}")
