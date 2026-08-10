---
title: "bloodhound-ce-python"
description: "pipx install bloodhound-ce # provides bloodhound-ce-python"
category: active-directory
subcategory: "Tooling & Recon"
tags: ["active-directory", "kerberos"]
tools: ["Nmap", "Impacket", "BloodHound", "faketime"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:ActiveDirectory/bloodhound-ce-python-cheatsheet.md"
---
# BloodHound CE Python Cheat Sheet

> [!info] What this is
> `bloodhound-ce-python` is the Python (impacket-based) ingestor for **BloodHound Community Edition**. It runs remotely from Linux — no domain-joined Windows host needed — and outputs JSON/zip for upload into the BHCE web UI. Based on dirkjanm's `BloodHound.py` (the `bloodhound-ce` branch).

> [!warning] CE vs legacy output are NOT interchangeable
> BloodHound **CE** uses a different JSON schema from legacy BloodHound. Use `bloodhound-ce-python` for CE and the older `bloodhound-python` for legacy. Uploading the wrong format silently fails or mis-parses. See BloodHound-Python_Cheatsheet for the legacy tool.

```bash
pipx install bloodhound-ce      # provides bloodhound-ce-python
# or on Kali:
sudo apt install bloodhound-ce-python
```

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Authentication](#2-authentication)
3. [Collection Methods (`-c`)](#3-collection-methods--c)
4. [DNS & Nameserver](#4-dns--nameserver)
5. [Kerberos & Clock Skew](#5-kerberos--clock-skew)
6. [Ingesting into BHCE](#6-ingesting-into-bhce)
7. [Questions & Answers](#7-questions--answers)
8. [Full Flag Reference](#8-full-flag-reference)

---

## 1. Quick Start

```mermaid
%%{init: {'theme':'base','themeVariables':{'background':'#191724','primaryColor':'#26233a','primaryTextColor':'#e0def4','primaryBorderColor':'#c4a7e7','lineColor':'#9ccfd8','secondaryColor':'#1f1d2e','tertiaryColor':'#31748f'}}}%%
flowchart LR
    A[Creds or ticket] --> B[bloodhound-ce-python<br/>-c All --zip]
    B --> C[*.zip output]
    C --> D[Upload in BHCE UI<br/>Administration -> File Ingest]
    D --> E[Run Cypher / paths]
```

```bash
# Password auth, collect everything, zip the result
bloodhound-ce-python -d corp.local -u user -p 'Passw0rd!' \
  -dc dc01.corp.local -ns 10.10.10.5 -c All --zip
```

---

## 2. Authentication

```bash
# Plaintext password
bloodhound-ce-python -d corp.local -u user -p 'Passw0rd!' -ns 10.10.10.5 -c All --zip

# NTLM hash (pass-the-hash) — LM:NT or just NT
bloodhound-ce-python -d corp.local -u user --hashes :NTHASH -ns 10.10.10.5 -c All --zip

# Kerberos ticket from ccache
export KRB5CCNAME=user.ccache
bloodhound-ce-python -d corp.local -u user -k -no-pass -dc dc01.corp.local -ns 10.10.10.5 -c All --zip

# AES key
bloodhound-ce-python -d corp.local -u user -aesKey <hex> -k -ns 10.10.10.5 -c All --zip

# Prompt for password interactively (keep it off your shell history)
bloodhound-ce-python -d corp.local -u user -ns 10.10.10.5 -c All --zip     # will prompt
```

| Flag | Meaning |
| :-- | :-- |
| `-u` / `--username` | Username (no domain) |
| `-p` / `--password` | Password (omit to be prompted) |
| `--hashes LM:NT` | Pass-the-hash (use `:NT` for NT-only) |
| `-k` / `--kerberos` | Use Kerberos auth (reads `KRB5CCNAME`) |
| `-no-pass` | No password (ticket-based) |
| `-aesKey` | Kerberos AES128/256 key |
| `-d` / `--domain` | Target domain FQDN |

---

## 3. Collection Methods (`-c`)

```bash
-c Default        # Group, LocalAdmin, Session, Trusts, ACL, ObjectProps, Container
-c All            # everything except LoggedOn
-c DCOnly         # LDAP-only, no host connections — quietest, no SMB touch
-c Session,LoggedOn   # comma-separate multiple methods
```

| Method | Collects | Noise |
| :-- | :-- | :-- |
| `Group` | Group memberships | low (LDAP) |
| `LocalAdmin` | Local admin rights (SAMR/host) | med |
| `RDP` / `DCOM` / `PSRemote` | Remote-access rights | med |
| `Session` | Active user sessions | med (touches hosts) |
| `LoggedOn` | Logged-on users (needs admin) | high |
| `Trusts` | Domain trusts | low |
| `ACL` | Object ACLs / DACLs | low |
| `ObjectProps` | Attributes (descriptions, pwd age…) | low |
| `Container` | OU/GPO container structure | low |
| `DCOnly` | Everything obtainable via LDAP only | **lowest** |
| `Default` | Sensible bundle (see above) | med |
| `All` | All except LoggedOn | high |

> [!tip] Start quiet, then go loud
> On a stealth engagement run `-c DCOnly` first (pure LDAP, no SMB/host connections). Only escalate to `Session`/`All` once you accept the extra host traffic.

---

## 4. DNS & Nameserver

BloodHound resolves computer names over DNS — point it at the DC or it will fail to resolve internal hosts.

```bash
-ns 10.10.10.5                 # use the DC as nameserver (most common)
--dns-tcp                      # force DNS over TCP (some AD DNS blocks UDP)
-d corp.local                  # domain must be the FQDN, not NetBIOS
--dns-timeout 5                # bump if resolution is slow

# If /etc/resolv.conf already points at the DC you can omit -ns, but explicit is safer.
```

> [!warning] "Could not resolve" errors
> Almost always a DNS problem, not auth. Set `-ns <DC-IP>`, add `--dns-tcp`, and make sure `-d` is the full domain FQDN.

---

## 5. Kerberos & Clock Skew

When authenticating with `-k`, Kerberos is time-sensitive. If `nmap` showed clock skew, wrap the collector with `faketime` (full guide: faketime-cheatsheet).

```bash
# DC is 7h30m ahead -> +7h30m ; use -f so child processes inherit the fake clock
export KRB5CCNAME=user.ccache
faketime -f '+7h30m' bloodhound-ce-python -d corp.local -u user -k -no-pass \
  -dc dc01.corp.local -ns 10.10.10.5 -c All --zip

# Get a TGT first (impacket), then collect under faketime:
faketime -f '+7h30m' impacket-getTGT corp.local/user:'Passw0rd!' -dc-ip 10.10.10.5
export KRB5CCNAME=user.ccache
faketime -f '+7h30m' bloodhound-ce-python -d corp.local -u user -k -no-pass \
  -dc dc01.corp.local -ns 10.10.10.5 -c DCOnly --zip
```

> [!note] `-dc` should be the FQDN
> For Kerberos, pass the DC's hostname (`-dc dc01.corp.local`), not just its IP — the SPN and realm need to match. Keep `-ns <IP>` for name resolution.

---

## 6. Ingesting into BHCE

```bash
# Collector writes a zip of JSON files:
ls -1 *.zip     # e.g. 20260719_bloodhound.zip
```

Then in the BloodHound CE web UI: **Administration → File Ingest → Upload Files**, drop the zip, wait for processing, then run Cypher / pathfinding.

```bash
# CLI alternative: bhcli / API upload (if you script ingestion)
# The web UI drag-and-drop is the supported path for one-off engagements.
```

> [!tip] Timestamped output
> Rename per host/user so multiple collections don't clobber each other:
> ```bash
> bloodhound-ce-python ... --zip -op "$(date +%Y%m%d)_corp_user"
> ```

---

## 7. Questions & Answers

### Q: What's the quietest collection for a stealth run?
```bash
bloodhound-ce-python -d corp.local -u user -p 'Passw0rd!' -ns 10.10.10.5 -c DCOnly --zip
```
**Answer:** `-c DCOnly` — pure LDAP, no SMB/host connections.

### Q: I have a Kerberos ticket and the DC clock is skewed. Full command?
```bash
export KRB5CCNAME=user.ccache
faketime -f '+7h30m' bloodhound-ce-python -d corp.local -u user -k -no-pass \
  -dc dc01.corp.local -ns 10.10.10.5 -c All --zip
```
**Answer:** wrap with `faketime -f` and add `-k -no-pass`.

### Q: Collection works but hosts won't resolve. Fix?
**Answer:** DNS. Add `-ns <DC-IP>`, try `--dns-tcp`, ensure `-d` is the FQDN.

### Q: Can I pass-the-hash?
```bash
bloodhound-ce-python -d corp.local -u user --hashes :NTHASH -ns 10.10.10.5 -c All --zip
```
**Answer:** Yes — `--hashes :NT` (leave LM blank).

---

## 8. Full Flag Reference

| Flag | Purpose |
| :-- | :-- |
| `-d`, `--domain` | Domain FQDN |
| `-u`, `--username` | Username |
| `-p`, `--password` | Password (prompts if omitted) |
| `--hashes LM:NT` | Pass-the-hash |
| `-k`, `--kerberos` | Kerberos auth (uses `KRB5CCNAME`) |
| `-no-pass` | No password (ticket) |
| `-aesKey` | Kerberos AES key |
| `-c`, `--collectionmethod` | What to collect (see §3) |
| `-dc` | Domain controller hostname (FQDN) |
| `-gc` | Global catalog server |
| `-ns`, `--nameserver` | DNS server for resolution |
| `--dns-tcp` | DNS over TCP |
| `--dns-timeout` | DNS timeout (s) |
| `--zip` | Zip the JSON output |
| `-op`, `--outputprefix` | Prefix output filenames |
| `--computerfile` | Restrict to hosts in a file |
| `--exclude-dcs` | Skip DCs during host enumeration |
| `-w`, `--workers` | Parallel enumeration threads |
| `-v` | Verbose |

---

## See Also

- faketime-cheatsheet — beating Kerberos clock skew when using `-k`
- BloodHound-Python_Cheatsheet — legacy (non-CE) collector
- Kerberos — tickets, TGT/TGS, PKINIT
