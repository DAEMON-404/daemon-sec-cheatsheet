---
title: "PERSIST1 — Active User Credential Theft via Certificates"
description: "The core persistence property of certificates: a certificate is valid until it expires or is revoked, independent of the account's password. If you enrol…"
category: active-directory
tags: ["active-directory", "adcs", "persistence", "hashing"]
tools: ["Certipy", "Certify", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/PERSIST1 — Active User Credential Theft via Certificates.md"
---
# PERSIST1 — Active User Credential Theft via Certificates

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | Account Persistence |
| **Difficulty** | Low |
| **Pre-requisites** | Control of (or enrolment rights as) the target user; an enabled auth template |
| **Tools** | Certipy, Certify |
| **OPSEC Noise** | Low — one normal certificate request |
| **One-liner** | Enrol a legitimate authentication certificate for a user you currently control, then keep it — it authenticates that user for the cert's whole lifetime, surviving password resets. |

***

## What Is PERSIST1?

The core persistence property of certificates: **a certificate is valid until it expires or is revoked, independent of the account's password.** If you enrol (or steal, per THEFT1 — Exporting Certificates and Keys) a cert for a user while you control them, you retain the ability to authenticate as that user even after IR resets their password. Default user templates commonly issue certs valid for **1–2 years**.

***

## Step 1 — Request a Long-Life Cert as the Target

```bash
# You currently control 'jdoe' (creds or hash). Enrol a standard auth cert.
certipy-ad req \
  -u 'jdoe@domain.htb' -p 'CurrentPassw0rd!' \
  -dc-ip $TARGET -ca 'DOMAIN-CA' -template 'User'
#   -> jdoe.pfx  (valid ~1-2 years by default)
```

```powershell
# Windows equivalent
.\Certify.exe request /ca:DC01\DOMAIN-CA /template:User
```

***

## Step 2 — Stash the PFX, Authenticate Any Time Later

```bash
# Weeks/months later — even after jdoe's password changed:
certipy-ad auth -pfx jdoe.pfx -dc-ip $TARGET      # PKINIT -> TGT + current NT hash
```

> [!tip] Persistence that self-heals your hash
> Because THEFT5 — NTLM Theft via PKINIT (UnPAC-the-Hash) returns the account's *current* NT hash each time you authenticate, this doubles as a way to continuously recover a fresh hash after resets, for as long as the cert is valid.

***

## Step 3 — Maximise Lifetime

- Prefer templates with the **longest validity** (`certipy find` shows `Validity Period`).
- Chain into PERSIST3 — Account Persistence via Certificate Renewal to renew before expiry and extend indefinitely.
- For high-value targets, enrol multiple certs across different templates/CAs for redundancy.

***

## OPSEC Considerations

| Action | Log | Noise |
| :-- | :-- | :-- |
| Certificate request | Event 4886/4887 on CA | 🟢 Low |
| Later PKINIT auth | Event 4768 on DC | 🟢 Low |

> [!note] Why IR misses it
> Standard incident response resets passwords and disables sessions but rarely reviews issued certificates. A parked `.pfx` sails through a password-reset remediation.

***

## Mitigation

- On compromise, **revoke the account's certificates** (and audit CA-issued certs), not just reset the password.
- Shorten template validity periods; require manager approval for sensitive templates.
- Monitor enrolment spikes and certs issued to accounts that never use smart cards.

***

## See Also

- _ADCS Attack Methodology Guide · PERSIST3 — Account Persistence via Certificate Renewal · THEFT5 — NTLM Theft via PKINIT (UnPAC-the-Hash)
- Sources: SpecterOps *Certified Pre-Owned*; [Certipy Wiki](https://github.com/ly4k/Certipy/wiki)
