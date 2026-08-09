#!/usr/bin/env python3
"""Mechanically port vault markdown -> site content for the 13 missing 'port' sheets.
Strips Obsidian syntax, drops any existing frontmatter, prepends normalized frontmatter.
Deterministic, content preserved (no LLM rewrite)."""
import json, os, re

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
VAULT = "/Volumes/bmdrbeKUVgvV/NetrunnerVault/02Cybersecurity/Cheatsheets"
SHEETS = os.path.join(REPO, "src", "content", "sheets")
UPDATED = "2026-08-09"

# (category, slug, title, rel, tools, tags, difficulty, description)
ITEMS = [
 ("exploitation","sqlmap","SQLMap","Exploitation/sqlmap.md",["SQLMap"],["exploitation","sql-injection","web"],"intermediate","SQLMap automated SQL injection: target flags, techniques, enumeration, dumping and tamper scripts."),
 ("exploitation","shell-stabilization","Shell Stabilization & TTY Upgrades","Exploitation/Jailbreak - TTY Upgrade.md",["python","socat","stty"],["exploitation","shells","post-exploitation"],"intermediate","Upgrade dumb shells to full TTYs and escape restricted shells (rbash, jails) with many techniques."),
 ("exploitation","metasploit","Metasploit Framework","Tools/meterpreter.md",["Metasploit","msfconsole","Meterpreter"],["exploitation","framework","post-exploitation"],"intermediate","msfconsole and Meterpreter workflow: search, exploits, payloads, sessions, post modules, pivoting."),
 ("privilege-escalation","windows-privesc","Windows Privilege Escalation","PrivEsc/PrivEsc - Windows.md",["winPEAS","PowerUp","JuicyPotato"],["privilege-escalation","windows","post-exploitation"],"advanced","Windows privesc master guide: token/privilege abuse, services, registry, AlwaysInstallElevated, potatoes."),
 ("tunneling-pivoting","tunneling-tools","Tunneling Tools","Misc/Tunneling.md",["Chisel","socat","plink","SSH"],["pivoting","tunneling","port-forwarding"],"advanced","Chisel, socat, plink and SSH tunneling patterns for port forwarding and pivoting through hosts."),
 ("tunneling-pivoting","ssh-tunneling","SSH Tunneling & Port Forwarding","Misc/SSH Portfwding with metasploit .md",["SSH","Metasploit"],["pivoting","ssh","port-forwarding"],"intermediate","SSH local/remote/dynamic forwarding and Metasploit route/portfwd pivoting, worked end to end."),
 ("cryptography","gpg","GPG","Cryptography/GPG - Cheatsheet markdown.md",["GPG","GnuPG"],["cryptography","encryption","pgp"],"intermediate","GnuPG keys, encryption/decryption, signing/verification, keyservers, trust and revocation."),
 ("dfir","forensics","Digital Forensics","DFIR/Forensics Cheatsheet.md",["Autopsy","Sleuth Kit","plaso"],["dfir","forensics","incident-response"],"intermediate","Cross-platform DFIR reference: acquisition, triage, artifacts, timelines and analysis commands."),
 ("tools","windows-cmd-powershell","Windows CMD & PowerShell","Tools/CMD-Powershell Cheat Sheet.md",["cmd","PowerShell"],["windows","post-exploitation","commands"],"intermediate","Windows pentest command reference: recon, users/groups, networking, downloads and PowerShell one-liners."),
 ("tools","fscan","fscan","Tools/fscan.md",["fscan"],["scanning","enumeration","internal"],"intermediate","fscan all-in-one intranet scanner: host/port discovery, service brute-forcing and vuln checks."),
 ("tools","eyewitness","EyeWitness","Tools/EyeWitness-Cheatsheet.md",["EyeWitness"],["recon","screenshots","web"],"beginner","EyeWitness bulk web/RDP/VNC screenshotting and reporting for rapid visual recon."),
 ("tools","snaffler","Snaffler","ActiveDirectory/Snaffler.md",["Snaffler"],["credentials","shares","enumeration"],"intermediate","Snaffler share-crawling for credentials, keys and sensitive files across SMB with tuning rules."),
 ("tools","sharpsploit","SharpSploit","ActiveDirectory/SharpSploit.md",["SharpSploit"],["post-exploitation","dotnet","offensive"],"advanced","SharpSploit .NET post-exploitation library: execution, credentials, enumeration and evasion APIs."),
]

def strip_frontmatter(txt):
    if txt.startswith("---"):
        end = txt.find("\n---", 3)
        if end != -1:
            nl = txt.find("\n", end + 1)
            return txt[nl+1:] if nl != -1 else ""
    return txt

def clean_obsidian(body):
    # ![[embed]] -> drop line-inline: keep alt-less removal
    body = re.sub(r"!\[\[[^\]]*\]\]", "", body)
    # [[link|alias]] -> alias ; [[link]] -> link (last path segment)
    def wl(m):
        inner = m.group(1)
        if "|" in inner:
            return inner.split("|",1)[1]
        return inner.split("/")[-1].split("#")[0] or inner
    body = re.sub(r"\[\[([^\]]+)\]\]", wl, body)
    # %%comments%%
    body = re.sub(r"%%.*?%%", "", body, flags=re.S)
    # obsidian callout markers -> blockquote note
    body = re.sub(r"^>\s*\[!(\w+)\]\s*", r"> **Note —** ", body, flags=re.M)
    return body

def yaml_list(xs):
    return "[" + ", ".join(xs) + "]"

def fm(cat, slug, title, tools, tags, diff, desc, rel):
    d = desc.replace('"', "'")
    t = title.replace('"', "'")
    return (f"---\ntitle: \"{t}\"\ndescription: \"{d}\"\ncategory: {cat}\n"
            f"tags: {yaml_list(tags)}\ntools: {yaml_list(tools)}\n"
            f"difficulty: {diff}\nupdated: \"{UPDATED}\"\n"
            f"source: \"vault:{rel}\"\n---\n")

def demote_h1(body, title):
    # ensure a single top H1 matching title; site hides first h1
    lines = body.split("\n")
    # find first non-empty
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and lines[i].startswith("# "):
        return "\n".join(lines[i:])  # already has H1
    return f"# {title}\n\n" + "\n".join(lines[i:])

def main():
    for cat, slug, title, rel, tools, tags, diff, desc in ITEMS:
        src = os.path.join(VAULT, rel)
        raw = open(src, encoding="utf-8", errors="replace").read()
        body = clean_obsidian(strip_frontmatter(raw)).strip()
        body = demote_h1(body, title)
        out = fm(cat, slug, title, tools, tags, diff, desc, rel) + "\n" + body + "\n"
        dst = os.path.join(SHEETS, cat, slug + ".md")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "w", encoding="utf-8").write(out)
        print(f"wrote {cat}/{slug}.md  ({len(body)} chars)")

if __name__ == "__main__":
    main()
