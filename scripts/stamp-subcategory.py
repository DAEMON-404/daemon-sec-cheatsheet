#!/usr/bin/env python3
"""
Stamp a `subcategory` onto Active Directory sheets so the category page can
group its 130+ entries instead of listing them flat.

The grouping is not invented — it is the taxonomy the source vault already
uses. Every sheet carries a `source: "vault:…"` path, and the AD-Attack set
is filed under Category-One … Category-Ten, the ADCS work under
ACL-ESC-Techniques, the ticket work under Kerberos. This maps those source
folders to kill-chain-ordered names; anything loose in ActiveDirectory/ is
tooling and recon.

Idempotent: re-running rewrites the same `subcategory:` line. Only sheets
under src/content/sheets/active-directory are touched.

Usage: python3 scripts/stamp-subcategory.py
"""
import os, re

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
AD = os.path.join(REPO, "src", "content", "sheets", "active-directory")

# Source folder → subcategory. The AD-Attack categories collapse a couple of
# ways: Category-Four (ESC attacks) merges with the ACL-ESC-Techniques folder,
# and Category-Two (tickets/delegation) merges with the Kerberos folder, so a
# reader sees one "ADCS & Certificates" section rather than two half-sections.
def subcat_for(source):
    s = source.replace("vault:", "")
    m = re.search(r"AD-Attack/Category-(\w+)", s)
    if m:
        return {
            "One": "Credential Access",
            "Two": "Kerberos & Delegation",
            "Three": "ACL Abuse",
            "Four": "ADCS & Certificates",
            "Five": "Domain Controller Attacks",
            "Six": "Privilege & Group Abuse",
            "Seven": "Lateral Movement",
            "Eight": "Persistence",
            "Nine": "Trust Abuse",
            "Ten": "Advanced & Post-Exploitation",
        }.get(m.group(1), "Advanced & Post-Exploitation")
    if "ACL-ESC-Techniques" in s:
        return "ADCS & Certificates"
    if "/Kerberos/" in s:
        return "Kerberos & Delegation"
    return "Tooling & Recon"

def read_source(fm):
    m = re.search(r'^source:\s*"?(?:source:\s*)?"?([^"\n]+)"?\s*$', fm, flags=re.M)
    # Some early files double-wrote the key ("source: source: \"vault:…\"");
    # this tolerates both. Fall back to a looser grab of the vault path.
    if m and "vault:" in m.group(0):
        vm = re.search(r"vault:[^\"\n]+", m.group(0))
        if vm:
            return vm.group(0)
    vm = re.search(r"vault:[^\"\n]+", fm)
    return vm.group(0) if vm else ""

def main():
    changed = 0
    counts = {}
    for f in sorted(os.listdir(AD)):
        if not f.endswith(".md"):
            continue
        path = os.path.join(AD, f)
        txt = open(path, encoding="utf-8").read()
        if not txt.startswith("---"):
            continue
        end = txt.find("\n---", 3)
        if end == -1:
            continue
        fm, body = txt[:end], txt[end:]

        source = read_source(fm)
        sub = subcat_for(source) if source else "Tooling & Recon"
        counts[sub] = counts.get(sub, 0) + 1

        line = f'subcategory: "{sub}"'
        if re.search(r"^subcategory:.*$", fm, flags=re.M):
            fm = re.sub(r"^subcategory:.*$", line, fm, count=1, flags=re.M)
        else:
            # Insert right after the category line so frontmatter stays tidy.
            fm = re.sub(r"^(category:.*)$", r"\1\n" + line, fm, count=1, flags=re.M)

        new = fm + body
        if new != txt:
            open(path, "w", encoding="utf-8").write(new)
            changed += 1

    print(f"stamped {changed} AD sheets")
    for k in sorted(counts):
        print(f"  {k:32} {counts[k]}")

if __name__ == "__main__":
    main()
