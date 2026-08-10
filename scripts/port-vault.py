#!/usr/bin/env python3
"""
Port the NetrunnerVault Cheatsheets tree into the site's `sheets` collection.

Mechanical, no rewriting: content is preserved verbatim apart from four
deterministic clean-ups that only remove vault-local scaffolding —
  1. Obsidian frontmatter (aliases/tags) is dropped and replaced with the
     site's normalized frontmatter.
  2. A chatbot preamble before the first H1 ("Right on cue, Netrunner…")
     is trimmed — everything up to the first `# ` line goes.
  3. `[[wikilinks]]` are flattened to their text (they point at vault pages
     that don't exist on-site); `![[embeds]]` are dropped.
  4. `[1][2]`-style citation markers are stripped OUTSIDE code fences.

Frontmatter (title/description/category/tags/tools/difficulty) is derived
from the filename, path and body. Nothing is paraphrased.

Dedup: a file whose canonical topic key already exists in the site (either
in the current sheets or earlier in this run) is SKIPPED, so the curated 60
are never clobbered and rustscan×3 collapses to the one already shipped.

Usage:
  python3 scripts/port-vault.py --dry     # decide only, write a manifest
  python3 scripts/port-vault.py           # apply (writes src/content/sheets)
"""
import json, os, re, sys, unicodedata

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC = "/Volumes/bmdrbeKUVgvV/NetrunnerVault/02Cybersecurity/Cheatsheets"
SHEETS = os.path.join(REPO, "src", "content", "sheets")
MANIFEST = os.path.join(REPO, "port-vault-decisions.tsv")
UPDATED = "2026-08-10"
DRY = "--dry" in sys.argv

# ── Category: source top-level folder → site domain ─────────────────────────
TOP_MAP = {
    "ActiveDirectory": "active-directory",
    "Cryptography": "cryptography",
    "HashingAndEncrypting": "cryptography",
    "DFIR": "dfir",
    "Enumeration": "enumeration",
    "Exploitation": "exploitation",
    "Git": "git-workflow",
    "Linux": "linux-it",
    "macOS": "linux-it",
    "PasswordAttacks": "password-attacks",
    "PrivEsc": "privilege-escalation",
    "Tools": "tools",
    "TunnelingAndPivoting": "tunneling-pivoting",
    "Web": "web",
}

def category_for(rel):
    parts = rel.split("/")
    top = parts[0]
    if top in TOP_MAP:
        return TOP_MAP[top]
    name = parts[-1].lower()
    if top == "Misc":
        if "tmux" in name:
            return "linux-it"
        if any(k in name for k in ("tunnel", "pivot", "portfw")):
            return "tunneling-pivoting"
        return "tools"
    # Root-level strays (most are skipped as non-sheets before reaching here)
    if "macos" in name:
        return "linux-it"
    if "git" in name:
        return "git-workflow"
    if "forensic" in name:
        return "dfir"
    return "tools"

# ── Skip: navigation / meta, not copy-ready cheatsheets ─────────────────────
SKIP_RE = re.compile(r"(roadmap|dashboard|attack-flow|most-used-commands|esc attack index|adcs dashboard)", re.I)

def is_non_sheet(rel):
    base = rel.split("/")[-1]
    stem = base[:-3] if base.lower().endswith(".md") else base
    if not stem.strip():
        return True                       # Git/.md — empty stub
    if stem.startswith("_"):
        return True                       # _ADCS Dashboard / _index files
    if base.lower() in ("attack.md", "readme.md"):
        return True                       # category cover / scripts readme
    return bool(SKIP_RE.search(stem))

# ── Slug / title / canonical key ────────────────────────────────────────────
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF\U00002B00-\U00002BFF️‍]"
)

def strip_emoji(s):
    return EMOJI_RE.sub("", s)

def slugify(s):
    s = strip_emoji(s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-") or "x"

def title_from(rel):
    base = rel.split("/")[-1][:-3]
    t = strip_emoji(base).strip()
    # Drop trailing "Cheatsheet" / "Cheat Sheet" / "markdown" noise words.
    t = re.sub(r"\s*[-–—]?\s*(cheat\s*sheet|cheatsheet|markdown)\s*$", "", t, flags=re.I)
    t = re.sub(r"\s{2,}", " ", t).strip(" -–—")
    t = t or base
    return TITLE_FIX.get(t, t)

# Suffix tokens that don't change the topic, plus explicit typo/alias fixes.
STRIP_TOKENS = {"cheatsheet", "cheat", "sheet", "guide", "usage", "full",
                "quick", "markdown", "htb", "complete", "expanded", "fullguide"}
ALIAS = {"gog": "gpg", "volitility3": "volatility", "volitility": "volatility",
         "redmd": "recmd", "emumeration": "enumeration", "nxc": "netexec",
         "crackmapexec": "netexec", "meterpreter": "metasploit"}

def canonical(slug):
    """Order-independent, de-duplicated topic key: 'privesc-windows' and
    'windows-privesc' collapse to the same thing, and 'netexec-nxc' (nxc
    aliases to netexec) to just 'netexec'. Sorting + set is what makes the
    dedup catch reorderings the raw slug would miss."""
    toks = [t for t in slug.split("-") if t and not t.isdigit() and t not in STRIP_TOKENS]
    toks = [ALIAS.get(t, t) for t in toks]
    return "-".join(sorted(set(toks)))

# Semantic near-dups the canonical key can't catch — a second PowerShell
# sheet, a reset guide already covered by git-reset, an XSS page already
# covered by web/xss. Skip-if-present, by the user's call.
SKIP_SRC = {
    "Tools/CMD-Powershell Cheat Sheet.md",       # → windows-cmd-powershell
    "Tools/Powershell.md",                       # → windows-cmd-powershell
    "Tools/Certipy-ADCS-Cheatsheet.md",          # → certipy + adcs-attack-methodology
    "Git/Resetting.md",                          # → git-reset
    "Git/Branches Expanded.md",                  # → git-branching
    "Git/Branches.md",                           # → git-branching
    "PasswordAttacks/john-cheatsheet.md",        # → john-the-ripper
    "PasswordAttacks/hashcat modes.md",          # → hashcat
    "Web/Cross-Site Scripting (XSS) - HTB Cheat Sheet.md",  # → web/xss
}

# Source filename typos, fixed only in the on-site title (content untouched).
TITLE_FIX = {"Windows Emumeration": "Windows Enumeration"}

# ── Body clean-up (verbatim apart from vault-local scaffolding) ─────────────
def strip_frontmatter(txt):
    if txt.startswith("---"):
        end = txt.find("\n---", 3)
        if end != -1:
            nl = txt.find("\n", end + 1)
            return txt[nl + 1:] if nl != -1 else ""
    return txt

def trim_preamble(txt):
    """Drop anything before the first H1 — that is where a chatbot intro,
    Obsidian separators, or stray notes sit. If there is no H1, keep all."""
    m = re.search(r"^# .+$", txt, flags=re.M)
    return txt[m.start():] if m else txt

def flatten_wikilinks(txt):
    txt = re.sub(r"!\[\[[^\]]*\]\]", "", txt)                 # embeds → gone
    txt = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", txt)  # [[a|b]] → b
    txt = re.sub(r"\[\[([^\]]+)\]\]", r"\1", txt)             # [[a]]   → a
    return txt

def strip_citations(txt):
    """Remove [1][2]-style markers, but never touch code fences (a shell
    array index or regex must survive)."""
    out, in_fence = [], False
    for line in txt.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        # Only runs of bracketed 1–3 digit numbers, i.e. citation clusters.
        out.append(re.sub(r"(?:\[\d{1,3}\])+", "", line))
    return "\n".join(out)

def clean_body(txt):
    txt = strip_frontmatter(txt)
    txt = trim_preamble(txt)
    txt = flatten_wikilinks(txt)
    txt = strip_citations(txt)
    return txt.strip() + "\n"

# ── Derived description ─────────────────────────────────────────────────────
def first_paragraph(body):
    lines = body.split("\n")
    skip_h1 = True
    buf = []
    for ln in lines:
        s = ln.strip()
        if skip_h1 and s.startswith("# "):
            skip_h1 = False
            continue
        if not s:
            if buf:
                break
            continue
        if s[0] in "#>|-*" or s.startswith("```") or s.startswith("**MITRE"):
            if buf:
                break
            continue
        buf.append(s)
    para = " ".join(buf)
    para = re.sub(r"`([^`]*)`", r"\1", para)
    para = re.sub(r"\*\*([^*]*)\*\*", r"\1", para)
    para = re.sub(r"\*([^*]*)\*", r"\1", para)
    para = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", para)
    para = re.sub(r"\s{2,}", " ", para).strip()
    if len(para) > 155:
        cut = para[:155].rsplit(" ", 1)[0]
        para = cut.rstrip(",.;:") + "…"
    return para

# ── tools / tags / difficulty ───────────────────────────────────────────────
TOOL_DB = [
    ("nmap", "Nmap"), ("rustscan", "RustScan"), ("ffuf", "ffuf"),
    ("gobuster", "Gobuster"), ("nuclei", "Nuclei"), ("nikto", "Nikto"),
    ("wpscan", "WPScan"), ("smbmap", "smbmap"), ("netexec", "NetExec"),
    ("nxc ", "NetExec"), ("crackmapexec", "NetExec"), ("impacket", "Impacket"),
    ("secretsdump", "Impacket"), ("mimikatz", "Mimikatz"), ("rubeus", "Rubeus"),
    ("certipy", "Certipy"), ("bloodhound", "BloodHound"), ("sharphound", "SharpHound"),
    ("kerbrute", "Kerbrute"), ("ldapsearch", "ldapsearch"), ("hashcat", "Hashcat"),
    ("john", "John"), ("sqlmap", "SQLMap"), ("metasploit", "Metasploit"),
    ("meterpreter", "Meterpreter"), ("evil-winrm", "Evil-WinRM"),
    ("chisel", "Chisel"), ("ligolo", "Ligolo-ng"), ("socat", "socat"),
    ("proxychains", "proxychains"), ("responder", "Responder"), ("mitm6", "mitm6"),
    ("snaffler", "Snaffler"), ("gitleaks", "Gitleaks"), ("trufflehog", "TruffleHog"),
    ("tshark", "tshark"), ("volatility", "Volatility"), ("gpg", "GPG"),
    ("openssl", "OpenSSL"), ("faketime", "faketime"), ("certify", "Certify"),
    ("powershell", "PowerShell"), ("evil-winrm", "Evil-WinRM"),
]

def tools_for(body):
    low = body.lower()
    seen, out = set(), []
    for needle, disp in TOOL_DB:
        if disp in seen:
            continue
        if needle in low:
            seen.add(disp)
            out.append(disp)
        if len(out) >= 5:
            break
    return out

TAG_MAP = [
    ("kerberos", "kerberos"), ("kerberoast", "kerberos"), ("adcs", "adcs"),
    ("esc", "adcs"), ("certificate", "adcs"), ("dcsync", "credential-access"),
    ("delegation", "delegation"), ("ntlm", "ntlm"), ("relay", "relay"),
    ("ticket", "kerberos"), ("privilege", "privilege-escalation"),
    ("persistence", "persistence"), ("lateral", "lateral-movement"),
    ("xss", "xss"), ("sql", "sql-injection"), ("lfi", "file-inclusion"),
    ("forensic", "forensics"), ("pivot", "pivoting"), ("tunnel", "tunneling"),
    ("hash", "hashing"), ("spray", "password-attacks"),
]

def tags_for(cat, slug, body):
    hay = (slug + " " + body[:1500]).lower()
    out = [cat]
    for needle, tag in TAG_MAP:
        if needle in hay and tag not in out:
            out.append(tag)
        if len(out) >= 5:
            break
    return out

ADV_HINT = re.compile(r"(esc\d|persist|theft|dcsync|delegation|golden|silver|"
                      r"diamond|sapphire|relay|adcs|zerologon|petitpotam|rbcd|"
                      r"skeleton|dsrm|sid-history|kerberoast|shadow-cred)", re.I)

def difficulty_for(rel, slug, cat):
    p = rel.lower()
    if "ad-attack" in p or "acl-esc" in p or "/kerberos/" in p:
        return "advanced"
    if cat == "privilege-escalation":
        return "advanced"
    if ADV_HINT.search(slug):
        return "advanced"
    return "intermediate"

# ── Existing sheets → canonical set (never clobber the curated 60) ──────────
def existing_canonicals():
    keys = {}
    for root, _, files in os.walk(SHEETS):
        for f in files:
            if f.endswith(".md"):
                slug = f[:-3]
                keys[canonical(slug)] = os.path.relpath(os.path.join(root, f), SHEETS)
    return keys

def yaml_scalar(s):
    return json.dumps(s, ensure_ascii=False)

def yaml_list(xs):
    return "[" + ", ".join(json.dumps(x, ensure_ascii=False) for x in xs) + "]"

def main():
    existing = existing_canonicals()
    taken = dict(existing)              # canonical → where (grows as we add)
    rows = []                           # (decision, cat, slug, title, rel, reason)
    add_plan = []                       # (dest_path, frontmatter+body)

    all_md = []
    for root, _, files in os.walk(SRC):
        for f in files:
            if f.endswith(".md"):
                all_md.append(os.path.relpath(os.path.join(root, f), SRC))
    all_md.sort()

    for rel in all_md:
        if is_non_sheet(rel):
            rows.append(("SKIP", "", "", "", rel, "non-sheet (meta/index/roadmap)"))
            continue
        if rel in SKIP_SRC:
            rows.append(("SKIP", "", "", "", rel, "semantic dup of existing sheet"))
            continue

        cat = category_for(rel)
        title = title_from(rel)
        slug = slugify(title)
        key = canonical(slug)

        if key in taken:
            rows.append(("SKIP", cat, slug, title, rel, f"dup of {taken[key]}"))
            continue

        raw = open(os.path.join(SRC, rel), encoding="utf-8", errors="replace").read()
        body = clean_body(raw)
        desc = first_paragraph(body) or f"{title} — operator reference."
        tools = tools_for(body)
        tags = tags_for(cat, slug, body)
        diff = difficulty_for(rel, slug, cat)

        fm = [
            "---",
            f"title: {yaml_scalar(title)}",
            f"description: {yaml_scalar(desc)}",
            f"category: {cat}",
            f"tags: {yaml_list(tags)}",
            f"tools: {yaml_list(tools)}",
            f"difficulty: {diff}",
            f'updated: "{UPDATED}"',
            f"source: {yaml_scalar('vault:' + rel)}",
            "---",
            "",
        ]
        dest = os.path.join(SHEETS, cat, slug + ".md")
        add_plan.append((dest, "\n".join(fm) + body))
        taken[key] = f"{cat}/{slug}.md (new)"
        rows.append(("ADD", cat, slug, title, rel, f"{diff} · {len(tools)} tools"))

    # Manifest
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        fh.write("decision\tcategory\tslug\ttitle\tsource\treason\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")

    adds = [r for r in rows if r[0] == "ADD"]
    skips = [r for r in rows if r[0] == "SKIP"]
    percat = {}
    for r in adds:
        percat[r[1]] = percat.get(r[1], 0) + 1

    print(f"scanned {len(all_md)} source .md")
    print(f"  ADD  {len(adds)}")
    print(f"  SKIP {len(skips)}  "
          f"({sum(1 for r in skips if 'non-sheet' in r[5])} meta, "
          f"{sum(1 for r in skips if r[5].startswith('dup'))} dup)")
    print("  new per category:")
    for c in sorted(percat):
        print(f"     {c:22} {percat[c]}")
    print(f"manifest → {os.path.relpath(MANIFEST, REPO)}")

    if DRY:
        print("\nDRY RUN — no files written.")
        return

    for dest, content in add_plan:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(content)
    print(f"\nwrote {len(add_plan)} sheets.")

if __name__ == "__main__":
    main()
