---
title: "LDAP Search"
description: "Here's the updated cheat sheet using the specific credentials from the Support box:"
category: active-directory
tags: ["active-directory"]
tools: ["NetExec", "BloodHound", "ldapsearch"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:ActiveDirectory/LDAP Search.md"
---
# LDAP Enumeration Cheat Sheet for HTB Support

Here's the updated cheat sheet using the specific credentials from the Support box:

**Credentials:**
- Username: `ldap@support.htb`
- Password: `nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz`
- Domain: `support.htb`
- Base DN: `DC=support,DC=htb`

## Basic ldapsearch Syntax (Modern)

### Initial Reconnaissance

#### Get Naming Contexts (Anonymous)
```bash
ldapsearch -x -H ldap://support.htb -b "" -s base namingContexts
```

#### Test Authentication
```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  -s base
```

#### Full Domain Dump
```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" | less
```

#### Clean Output (Recommended)
```bash
ldapsearch -LLL -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb"
```

## User Enumeration

#### All Users
```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(objectClass=person)" cn mail
```

#### All AD User Objects
```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(&(objectClass=user)(objectCategory=person))" \
  sAMAccountName mail displayName
```

#### Users with Extended Attributes
```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(objectClass=user)" \
  sAMAccountName mail userAccountControl description info memberOf
```

#### Search for Passwords in Description/Info Fields
```bash
# Check description fields
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(description=*)" description cn | grep -i "pass\|pwd"

# Check info field (critical for this box!)
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(info=*)" info cn sAMAccountName
```

#### Find the Support User Specifically
```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(cn=support)" \
  cn info memberOf distinguishedName
```

#### Active Users Only (Exclude Disabled)
```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  '(&(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))' \
  sAMAccountName cn
```

#### Service Accounts (Kerberoastable)
```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(&(objectClass=user)(servicePrincipalName=*))" \
  sAMAccountName servicePrincipalName
```

## Group Enumeration

#### All Groups
```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(objectClass=group)" cn description member
```

#### Groups with "Admin" in Name
```bash
ldapsearch -LLL -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(&(objectClass=group)(name=*admin*))" name sAMAccountName member
```

#### Shared Support Accounts Group
```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(cn=Shared Support Accounts)" member
```

#### Remote Management Users Group
```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(cn=Remote Management Users)" member
```

#### Domain Admins
```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(cn=Domain Admins)" member
```

#### User's Group Memberships
```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(sAMAccountName=support)" memberOf
```

## Computer Enumeration

#### All Computers
```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(objectClass=computer)" cn operatingSystem dNSHostName
```

#### Domain Controllers Only
```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(userAccountControl:1.2.840.113556.1.4.803:=8192)" cn dNSHostName
```

#### Computers with Unconstrained Delegation
```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(userAccountControl:1.2.840.113556.1.4.803:=524288)" cn
```

## Organizational Units

```bash
ldapsearch -x -LLL -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  -s sub \
  "(|(objectClass=organizationalUnit)(objectClass=group))"
```

## Operational Attributes

```bash
# Get all operational attributes
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(objectClass=*)" '+'

# Specific operational attributes
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb" \
  "(objectClass=*)" \
  creatorsName createTimestamp modifiersName modifyTimestamp
```

## Modern Tools

### ldapdomaindump
```bash
# Comprehensive domain dump
ldapdomaindump -u 'support.htb\ldap' \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  support.htb \
  -o ldap_output

# Output creates:
# - domain_users.json/html
# - domain_groups.json/html
# - domain_computers.json/html
# - domain_trusts.json/html
# - domain_policy.json/html
```

### BloodHound Python
```bash
bloodhound-python -c All \
  -u ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -d support.htb \
  -ns 10.10.11.174
```

### CrackMapExec / NetExec
```bash
# Verify credentials
crackmapexec smb support.htb \
  -u ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz'

# LDAP enumeration
netexec ldap support.htb \
  -u ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  --users --groups --computers
```

## Secure Alternative (Password Prompt)

Instead of putting the password in the command, use `-W` for a prompt:

```bash
ldapsearch -x -H ldap://support.htb \
  -D 'ldap@support.htb' \
  -W \
  -b "DC=support,DC=htb"
```

## LDAPS (Secure LDAP)

```bash
ldapsearch -x -H ldaps://support.htb:636 \
  -D 'ldap@support.htb' \
  -w 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  -b "DC=support,DC=htb"
```

## Key Takeaways

1. **Always use `-H ldap://`** instead of deprecated `-h` hostname
2. **Add `-x`** for simple authentication in modern versions
3. **Use `-LLL`** for cleaner output
4. **The `info` field** contained the password for the support user in this box
5. **Check group memberships** - support user was in "Remote Management Users"

***

## Command-Line Flags Reference Table

| Flag | Long Form | Description | Example |
|------|-----------|-------------|---------|
| `-H` | `--uri` | LDAP URI to connect to (replaces deprecated `-h`) | `-H ldap://support.htb` |
| `-h` | `--host` | **DEPRECATED** Hostname (use `-H` instead) | ~~`-h support.htb`~~ |
| `-p` | `--port` | Port number (default: 389 for LDAP, 636 for LDAPS) | `-p 389` |
| `-D` | `--binddn` | Bind Distinguished Name for authentication | `-D 'ldap@support.htb'` |
| `-w` | `--bindpw` | Bind password (plaintext - visible in process list) | `-w 'password'` |
| `-W` | `--bindpw-prompt` | Prompt for bind password (more secure) | `-W` |
| `-y` | `--bindpw-file` | Read password from file | `-y /path/to/passfile` |
| `-b` | `--basedn` | Base Distinguished Name for search | `-b "DC=support,DC=htb"` |
| `-s` | `--scope` | Search scope: `base`, `one`, `sub`, `children` | `-s sub` |
| `-x` | `--simple` | Use simple authentication instead of SASL | `-x` |
| `-Z` | `--starttls` | Issue StartTLS extended operation | `-Z` |
| `-L` | N/A | LDIFv1 format (one `-L`) | `-L` |
| `-LL` | N/A | Disable comments in output (two `-L`) | `-LL` |
| `-LLL` | N/A | Disable comments and version (three `-L`, cleanest) | `-LLL` |
| `-v` | `--verbose` | Verbose output | `-v` |
| `-d` | `--debug` | Debug level (0-9, higher = more verbose) | `-d 1` |
| `-A` | N/A | Retrieve attribute names only (no values) | `-A` |
| `-l` | `--timelimit` | Time limit for search in seconds | `-l 30` |
| `-z` | `--sizelimit` | Size limit for number of entries returned | `-z 100` |
| `-S` | N/A | Sort results by specified attribute | `-S cn` |
| `-E` | `--extensions` | LDAP extensions (e.g., paging) | `-E pr=1000/noprompt` |
| `-o` | N/A | Set general options | `-o ldif-wrap=no` |
| `-n` | N/A | Show what would be done (dry run) | `-n` |
| `-u` | N/A | Include User Friendly names in output | `-u` |
| `-t` | N/A | Write binary values to temp files | `-t` |
| `-T` | N/A | Directory for temp files (use with `-t`) | `-T /tmp` |
| `-F` | N/A | URL prefix for temp files | `-F file:///tmp/` |
| `-M` | N/A | Enable Manage DSA IT control | `-M` |
| `-C` | N/A | Chase referrals | `-C` |
| `-c` | N/A | Continuous operation mode (ignore errors) | `-c` |

### Search Scope Values

| Scope | Description |
|-------|-------------|
| `base` | Search only the base DN itself |
| `one` | Search immediate children of base DN only (one level) |
| `sub` | Search base DN and all descendants (subtree - most common) |
| `children` | Search all descendants but not the base DN itself |

### Common Attribute Shortcuts

| Shortcut | Meaning |
|----------|---------|
| `*` | All regular (non-operational) attributes |
| `+` | All operational attributes |
| `1.1` | No attributes (DN only) |
| `*` `+` | All attributes (regular + operational) |

### LDAP URI Format

| Format | Description |
|--------|-------------|
| `ldap://host` | Standard LDAP on port 389 |
| `ldap://host:port` | LDAP on custom port |
| `ldaps://host` | LDAP over SSL/TLS on port 636 |
| `ldaps://host:port` | LDAPS on custom port |
| `ldapi://` | LDAP over Unix domain socket (local) |

### Common Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Operations error |
| `2` | Protocol error |
| `32` | No such object |
| `49` | Invalid credentials |
| `50` | Insufficient access rights |

***

## Pro Tips

1. **Always use `-LLL`** for clean, parseable output
2. **Use `-W`** instead of `-w` to avoid password in shell history
3. **The `info` field** in AD often contains sensitive data
4. **Check group memberships** - Remote Management Users = WinRM access
5. **Operational attributes** (`+`) reveal creation/modification metadata
6. **Use `sub` scope** for comprehensive searches
7. **Combine filters** with `&` (AND) and `|` (OR) for precise queries
8. **Save output** to files for offline analysis with `> output.txt`
