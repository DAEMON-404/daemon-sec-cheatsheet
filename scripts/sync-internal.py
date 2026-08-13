#!/usr/bin/env python3
"""Mirror InternalAllTheThings (swisskyrepo) into the site as the `internal`
content collection. Faithful markdown mirror; images + non-md assets hotlink to
upstream GitHub. Deterministic + re-runnable. IATT ships no LICENSE, so the
`sourceUrl` attribution on every page is the standing credit to the upstream.

Usage: python3 scripts/sync-internal.py /path/to/iatt-clone <sha>
"""
import json, os, re, shutil, sys
from urllib.parse import quote, unquote

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(REPO, "src", "content", "internal")
UPSTREAM = "https://github.com/swisskyrepo/InternalAllTheThings"
LIVE = "swisskyrepo.github.io/InternalAllTheThings"

SRC = sys.argv[1] if len(sys.argv) > 1 else None
SHA = sys.argv[2] if len(sys.argv) > 2 else "master"
if not SRC or not os.path.isdir(SRC):
    sys.exit("usage: sync-internal.py <iatt-clone-dir> <sha>")
DOCS = os.path.join(SRC, "docs")
if not os.path.isdir(DOCS):
    sys.exit(f"no docs/ under {SRC}")

# Human section titles keyed by the docs/<dir> name. Anything unmapped falls
# back to a title-cased dir name (hyphens -> spaces).
SECTION_TITLES = {
    "active-directory": "Active Directory",
    "cheatsheets": "Cheatsheets",
    "cloud": "Cloud",
    "command-control": "Command & Control",
    "containers": "Containers",
    "databases": "Databases",
    "devops": "DevOps",
    "methodology": "Methodology",
    "redteam": "Red Team",
}


def slugify(s):
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-") or "x"


def section_title(name):
    return SECTION_TITLES.get(name, name.replace("-", " ").title())


def blob_url(relpath):  # repo-relative path -> pinned GitHub blob URL
    return f"{UPSTREAM}/blob/{SHA}/{quote(relpath)}"


def raw_url(relpath):  # repo-relative path -> pinned raw.githubusercontent URL
    return f"https://raw.githubusercontent.com/swisskyrepo/InternalAllTheThings/{SHA}/{quote(relpath)}"


def tree_url(relpath):  # repo-relative dir -> pinned GitHub tree URL
    return f"{UPSTREAM}/tree/{SHA}/{quote(relpath)}"


# --- Discover mirrored markdown, build path->route maps before any rewrite -----
# mkdocs.yml declares no `nav`, so mkdocs publishes every .md under docs/ —
# including DISCLAIMER.md, the liability notice for everything else here. Only
# docs/README.md is repo chrome rather than a page.
ROOT_SKIP = {"readme.md"}

sections = sorted(
    d for d in os.listdir(DOCS) if os.path.isdir(os.path.join(DOCS, d))
)

route_of_md = {}   # repo-relative md path (lowercased) -> internal route
route_of_dir = {}  # repo-relative section dir (lowercased) -> section root route
routes = set()     # every emitted route, for R1 resolution + verification
pages = []         # (section, rel, abspath, is_index, out_id, route)
root_pages = []    # (rel, abspath, slug, route) for docs/*.md outside a section

# Section roots resolve even for README-less sections (a synthesized index is
# emitted below), so register them up front — R1 links may target them.
for section in sections:
    sec_route = f"/internal/{slugify(section)}"
    route_of_dir[f"docs/{section}".lower()] = sec_route
    routes.add(sec_route)

for section in sections:
    sdir = os.path.join(DOCS, section)
    for root, dirs, files in os.walk(sdir):
        dirs.sort()
        for f in sorted(files):
            if not f.lower().endswith(".md"):
                continue
            abspath = os.path.join(root, f)
            rel = os.path.relpath(abspath, SRC).replace(os.sep, "/")  # docs/<...>.md
            inner = os.path.relpath(abspath, sdir).replace(os.sep, "/")
            sslug = slugify(section)
            # A README.md directly in the section dir is that section's index.
            is_index = inner.lower() == "readme.md"
            if is_index:
                out_id = f"{sslug}/index"
                route = f"/internal/{sslug}"
            else:
                seg = "/".join(slugify(p) for p in inner[:-3].split("/"))
                out_id = f"{sslug}/{seg}"
                route = f"/internal/{sslug}/{seg}"
            route_of_md[rel.lower()] = route
            routes.add(route)
            pages.append((section, rel, abspath, is_index, out_id, route))

# A docs-root page belongs to no section, so it takes the top of the collection.
for f in sorted(os.listdir(DOCS)):
    if not f.lower().endswith(".md") or f.lower() in ROOT_SKIP:
        continue
    abspath = os.path.join(DOCS, f)
    rel = f"docs/{f}"
    slug = slugify(os.path.splitext(f)[0])
    route = f"/internal/{slug}"
    route_of_md[rel.lower()] = route
    routes.add(route)
    root_pages.append((rel, abspath, slug, route))

# --- Link rewriting (rules R1-R5) ----------------------------------------------
LINK = re.compile(r"(!?)\[([^\]]*)\]\(([^)]+)\)")
FENCE = re.compile(r"^\s*(```|~~~)")

# R1: the mkdocs live site — every link here must come home to /internal.
LIVE_URL = re.compile(
    r"^https?://swisskyrepo\.github\.io/InternalAllTheThings/(.*)$", re.I
)
# R2: GitHub source URLs that point back into the repo (two hosts).
UPSTREAM_URL = re.compile(
    r"^https?://(?:www\.)?github\.com/swisskyrepo/InternalAllTheThings/(?:blob|tree|raw)/[^/]+/(.*)$"
    r"|^https?://raw\.githubusercontent\.com/swisskyrepo/InternalAllTheThings/[^/]+/(.*)$",
    re.I,
)


def route_for_live_path(path, anchor):
    """R1: map a live-site <path> to an internal route, else the section index,
    else None (leave the original URL untouched)."""
    path = unquote(path).split("?", 1)[0].strip("/")
    if path == "":
        return "/internal" + anchor  # the collection root
    cand = "/internal/" + "/".join(slugify(p) for p in path.split("/"))
    if cand in routes:
        return cand + anchor
    sec = f"/internal/{slugify(path.split('/')[0])}"  # fall back to the section
    if sec in routes:
        return sec + anchor
    return None


def route_for_repo_path(resolved, anchor, pin):
    """Map a repo-relative path to an internal route or a pinned upstream URL.
    `pin` picks the fallback when nothing is mirrored: absolute GitHub links
    (R2) always pin to raw upstream; relative links (R3/R4) only rewrite a path
    that actually exists in the checkout, otherwise return None (R5)."""
    resolved = resolved.strip("/")
    low = resolved.lower()
    if low.endswith(".md"):
        r = route_of_md.get(low)
        if r:
            return r + anchor
        if pin or os.path.isfile(os.path.join(SRC, resolved)):
            return raw_url(resolved) + anchor
        return None
    # mkdocs omits the .md extension when linking a sibling page.
    r = route_of_md.get(low + ".md")
    if r:
        return r + anchor
    idx = route_of_dir.get(low) or route_of_md.get(low + "/readme.md")
    if idx:
        return idx + anchor
    if pin or os.path.isfile(os.path.join(SRC, resolved)):
        return raw_url(resolved) + anchor  # image / script / other asset
    return None


def resolve(cur_relpath, target):
    """Return the rewritten URL for a markdown link target, or None to keep it."""
    t = target.strip().strip("<>").strip()
    anchor = ""

    m = LIVE_URL.match(t)  # R1
    if m:
        path = m.group(1)
        if "#" in path:
            path, a = path.split("#", 1); anchor = "#" + a
        return route_for_live_path(path, anchor)

    m = UPSTREAM_URL.match(t)  # R2
    if m:
        path = (m.group(1) or m.group(2) or "").split("?", 1)[0]
        if "#" in path:
            path, a = path.split("#", 1); anchor = "#" + a
        return route_for_repo_path(unquote(path), anchor, pin=True)

    # R5: other hosts, protocol-relative, bare anchors, mailto: -> leave.
    if re.match(r"^([a-z][a-z0-9+.-]*:|//|#)", t, re.I):
        return None

    # R3/R4: relative in-repo link, resolved against the current file's dir.
    if "#" in t:
        t, a = t.split("#", 1); anchor = "#" + a
    if not t:
        return None
    cur_dir = os.path.dirname(cur_relpath)
    resolved = os.path.normpath(os.path.join(cur_dir, unquote(t))).replace(os.sep, "/")
    return route_for_repo_path(resolved, anchor, pin=False)


def rewrite_body(cur_relpath, body):
    """Rewrite link targets outside fenced code blocks; code stays verbatim."""
    def repl(m):
        new = resolve(cur_relpath, m.group(3))
        return m.group(0) if new is None else f"{m.group(1)}[{m.group(2)}]({new})"

    out, fenced = [], False
    for line in body.split("\n"):
        if FENCE.match(line):
            fenced = not fenced
        out.append(line if fenced else LINK.sub(repl, line))
    return "\n".join(out)


def title_from(body, fallback):
    m = re.search(r"^\s*#\s+(.+?)\s*$", body, re.M)
    return m.group(1).strip() if m else fallback


def yaml_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def frontmatter(title, section, sslug, source_path, source_url, is_index):
    return (
        "---\n"
        f'title: "{yaml_escape(title)}"\n'
        f'section: "{yaml_escape(section)}"\n'
        f'sectionSlug: "{sslug}"\n'
        f'sourcePath: "{yaml_escape(source_path)}"\n'
        f'sourceUrl: "{source_url}"\n'
        f'sha: "{SHA}"\n'
        f"isIndex: {'true' if is_index else 'false'}\n"
        "---\n\n"
    )


# --- Emit -----------------------------------------------------------------------
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT, exist_ok=True)

count = 0
section_seen = {}
sections_with_index = set()
section_pages = {}  # section -> [(route, title)] for non-index pages
for section, rel, abspath, is_index, out_id, route in pages:
    raw = open(abspath, encoding="utf-8", errors="replace").read()
    body = rewrite_body(rel, raw)
    stitle = section_title(section)
    fallback = stitle if is_index else os.path.splitext(os.path.basename(abspath))[0]
    title = title_from(raw, fallback)
    if is_index:
        sections_with_index.add(section)
    else:
        section_pages.setdefault(section, []).append((route, title))
    fm = frontmatter(title, stitle, slugify(section), rel, blob_url(rel), is_index)
    dst = os.path.join(OUT, out_id + ".md")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w", encoding="utf-8").write(fm + body.lstrip("\n"))
    count += 1
    section_seen[section] = section_seen.get(section, 0) + 1

for rel, abspath, slug, route in root_pages:
    raw = open(abspath, encoding="utf-8", errors="replace").read()
    body = rewrite_body(rel, raw)
    stitle = section_title(slug)
    title = title_from(raw, stitle)
    fm = frontmatter(title, stitle, slug, rel, blob_url(rel), True)
    open(os.path.join(OUT, slug + ".md"), "w", encoding="utf-8").write(
        fm + body.lstrip("\n")
    )
    count += 1

# --- Synthesize a section index for any section lacking a README.md -------------
# Most IATT sections are a flat/nested set of pages with no README, so no
# `{slug}/index` root gets emitted and the collection index would link to a 404.
# Generate a listing page for each so its root route resolves + enumerates pages.
for section in sections:
    if section in sections_with_index:
        continue
    sslug = slugify(section)
    stitle = section_title(section)
    pgs = sorted(section_pages.get(section, []), key=lambda p: (p[1].lower(), p[0]))
    listing = "\n".join(f"* [{title}]({route})" for route, title in pgs)
    fm = frontmatter(
        stitle, stitle, sslug, f"docs/{section}", tree_url(f"docs/{section}"), True
    )
    intro = (
        f"# {stitle}\n\n"
        f"> {len(pgs)} pages in this section, mirrored from InternalAllTheThings.\n\n"
        "## Pages\n\n"
    )
    dst = os.path.join(OUT, sslug, "index.md")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w", encoding="utf-8").write(fm + intro + listing + "\n")
    count += 1
    section_seen[section] = section_seen.get(section, 0) + 1

# --- Manifest -------------------------------------------------------------------
manifest = {
    "upstream": UPSTREAM,
    "sha": SHA,
    "sections": len(section_seen),
    "pages": count,
    "sectionList": sorted(section_seen.keys()),
}
open(os.path.join(REPO, "internal-manifest.json"), "w").write(
    json.dumps(manifest, indent=2) + "\n"
)

print(f"mirrored {count} pages across {len(section_seen)} sections @ {SHA}")
