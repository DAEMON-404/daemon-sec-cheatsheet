---
title: "Anonymous Null Testing"
description: "nxc smb <IP> -u '' -p '' # Test anonymous access nxc smb <IP> -u 'guest' -p '' # Test guest account nxc smb <IP> -u='' -p='' # Windows syntax"
category: enumeration
tags: ["enumeration", "privilege-escalation"]
tools: ["smbmap", "NetExec", "ldapsearch"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Enumeration/Anonymous  Null Testing.md"
---
# Test null session
nxc smb <IP> -u '' -p ''                                    # Test anonymous access
nxc smb <IP> -u 'guest' -p ''                               # Test guest account
nxc smb <IP> -u='' -p=''                                    # Windows syntax
```

**Output interpretation**:

1. Green **[+]**: Authentication succeeded
2. Red **[-]**: Authentication failed
3. **Pwn3d!**: Administrative privileges obtained
4. **STATUS_LOGON_FAILURE**: Null session blocked
5. **STATUS_ACCESS_DENIED**: Authenticated but no privileges

```bash
# Basic enumeration
nxc smb <IP> -u '' -p '' --shares                           # List shares
nxc smb <IP> -u '' -p '' --users                            # List users
nxc smb <IP> -u '' -p '' --groups                           # List groups
nxc smb <IP> -u '' -p '' --pass-pol                         # Password policy
nxc smb <IP> -u '' -p '' --sessions                         # Active sessions
nxc smb <IP> -u '' -p '' --loggedon-users                   # Logged on users
nxc smb <IP> -u '' -p '' --rid-brute                        # RID brute force (noisy)
nxc smb <IP> -u '' -p '' --disks                            # List disks
```

**RID brute force warning**: Generates hundreds of Windows Event ID 4625 (failed logon) events—extremely noisy

---

### SMB File Operations

```bash
# List files in share
nxc smb <IP> -u '' -p '' --ls SHARENAME                     # List root of share
nxc smb <IP> -u '' -p '' --ls 'SHARENAME/folder'            # List subdirectory
```

```bash
# Download files
nxc smb <IP> -u '' -p '' --get-file 'SHARE\file.txt' ./local.txt        # Download file
nxc smb <IP> -u '' -p '' --get-file 'C$\Windows\System32\drivers\etc\hosts' ./hosts    # Download specific file
```

```bash
# Upload files
nxc smb <IP> -u '' -p '' --put-file local.txt 'SHARE\remote.txt'        # Upload file
```

```bash
# Spider shares (search files)
nxc smb <IP> -u '' -p '' --spider SHARENAME                              # List all files
nxc smb <IP> -u '' -p '' --spider SHARENAME --pattern txt                # Search by extension
nxc smb <IP> -u '' -p '' --spider SHARENAME --pattern 'password|secret'  # Search by keyword
nxc smb <IP> -u '' -p '' --spider SHARENAME --regex '.*\.config'         # Regex search
nxc smb <IP> -u '' -p '' --spider SHARENAME --depth 3                    # Limit depth
nxc smb <IP> -u '' -p '' --spider SHARENAME --only-files                 # Files only
nxc smb <IP> -u '' -p '' --spider SHARENAME --content --pattern password # Search file content
```

**Spider options**:

1. **--pattern**: Match file names by keyword or extension
2. **--regex**: Match file names by regular expression
3. **--depth**: Limit recursion depth (reduces noise)
4. **--only-files**: Skip directories in output
5. **--content**: Search inside file contents (requires read access)

---

### SMB spider_plus Module

The spider_plus module provides advanced recursive file enumeration with JSON output for parsing and filtering.

**Output location**: `~/.nxc/logs/` or `/tmp/nxc_spider_plus/<IP>.json`

**Module requirements**: NetExec 1.0.0+

```bash
# List all files (creates JSON output)
nxc smb <IP> -u '' -p '' -M spider_plus                                  # List files
nxc smb <IP> -u '' -p '' -M spider_plus -o DOWNLOAD_FLAG=True            # Download all files
nxc smb <IP> -u '' -p '' -M spider_plus -o PATTERN='*.txt,*.xml,*.config' # Filter extensions
nxc smb <IP> -u '' -p '' -M spider_plus -o DEPTH=3                       # Limit depth
nxc smb <IP> -u '' -p '' -M spider_plus -o EXCLUDE_EXTS='exe,dll'        # Exclude types
```

**Module options**:

1. **DOWNLOAD_FLAG=True**: Download all enumerated files
2. **PATTERN='*.ext1,*.ext2'**: Filter by file extensions (comma-separated)
3. **DEPTH=<n>**: Control recursion depth
4. **EXCLUDE_EXTS='ext1,ext2'**: Exclude specific file types

```bash
# Parse JSON output
cat /tmp/nxc_spider_plus/<IP>.json | jq '.'                              # Pretty print
cat ~/.nxc/logs/<output>.json | jq '.[] | select(.name | endswith(".txt"))'  # Filter .txt files
cat ~/.nxc/logs/<output>.json | jq '.[] | select(.size > 10000)'         # Filter by size
```

**JSON structure**: Array of objects with fields: `name`, `path`, `size`, `atime` (access time), `ctime` (creation time), `mtime` (modification time)

---

### SMB Vulnerability Checks

```bash
nxc smb <IP> -u '' -p '' -M ms17-010                        # Check EternalBlue (CVE-2017-0144)
nxc smb <IP> -u '' -p '' -M zerologon                       # Check ZeroLogon (CVE-2020-1472)
nxc smb <IP> -u '' -p '' -M petitpotam                      # Check PetitPotam
nxc smb <IP> -u '' -p '' -M printnightmare                  # Check PrintNightmare (CVE-2021-34527)
nxc smb <IP> -u '' -p '' -M nopac                           # Check noPac (CVE-2021-42278/42287)
nxc smb <IP> -u '' -p '' -M spooler                         # Check print spooler status
nxc smb <IP> -u '' -p '' -M enum_av                         # Enumerate antivirus
nxc smb <IP> -u '' -p '' -M enum_ca                         # Enumerate ADCS (Certificate Authority)
nxc smb <IP> -u '' -p '' --gen-relay-list relay.txt         # Check SMB signing (relay attacks)
```

**Vulnerability module notes**:

1. Modules check for vulnerability presence—do not exploit
2. **--gen-relay-list**: Identifies hosts without SMB signing (vulnerable to relay attacks)
3. Some modules require valid credentials (not anonymous)

---

### LDAP Anonymous Bind Testing

**Port**: 389/tcp (LDAP) or 636/tcp (LDAPS)

**Anonymous bind**: Authenticates with empty credentials to query directory information

```bash
# Test anonymous bind
nxc ldap <IP> -u '' -p ''                                   # Test anonymous LDAP
```

**Result codes**:

1. **LDAP Result Code 0 (success)**: Anonymous bind allowed
2. **LDAP Result Code 49 (invalidCredentials)**: Anonymous bind blocked

```bash
# Basic enumeration
nxc ldap <IP> -u '' -p '' --users                           # List users
nxc ldap <IP> -u '' -p '' --groups                          # List groups
nxc ldap <IP> -u '' -p '' --computers                       # List computers
nxc ldap <IP> -u '' -p '' --get-sid                         # Get domain SID
```

```bash
# LDAP modules
nxc ldap <IP> -u '' -p '' -M get-desc-users                 # Get user descriptions
nxc ldap <IP> -u '' -p '' -M maq                            # Machine Account Quota
nxc ldap <IP> -u '' -p '' -M ldap-checker                   # LDAP signing check
nxc ldap <IP> -u '' -p '' -M enum_trusts                    # Enumerate trusts
nxc ldap <IP> -u '' -p '' -M whoami                         # Current context
```

```bash
# Custom LDAP queries
nxc ldap <IP> -u '' -p '' --query "(objectClass=user)" "sAMAccountName,description"
nxc ldap <IP> -u '' -p '' --query "(objectClass=group)" "name,member"
nxc ldap <IP> -u '' -p '' --query "(servicePrincipalName=*)" "servicePrincipalName"
nxc ldap <IP> -u '' -p '' --query "(adminCount=1)" "sAMAccountName"
```

**Custom query format**: `--query "<LDAP_FILTER>" "<ATTRIBUTES>"`

**Common LDAP filters**:

1. **(objectClass=user)**: All user objects
2. **(objectClass=group)**: All group objects
3. **(servicePrincipalName=*)**: Users with SPNs (Kerberoastable)
4. **(adminCount=1)**: Protected admin accounts
5. **(userAccountControl:1.2.840.113556.1.4.803:=8192)**: Domain controllers

---

### FTP Anonymous Access

**Port**: 21/tcp

**Anonymous credentials**: Username `anonymous` or empty; password empty or email address

```bash
# Test anonymous login
nxc ftp <IP> -u '' -p ''                                    # Empty credentials
nxc ftp <IP> -u 'anonymous' -p ''                           # Anonymous user
nxc ftp <IP> -u 'anonymous' -p 'user@example.com'           # With email
```

**FTP response codes**:

1. **230 Login successful**: Anonymous login allowed
2. **530 Login incorrect**: Anonymous login blocked

```bash
# List files
nxc ftp <IP> -u 'anonymous' -p '' --ls                      # List root
nxc ftp <IP> -u 'anonymous' -p '' --ls /pub                 # List directory
```

```bash
# Download files
nxc ftp <IP> -u 'anonymous' -p '' --get file.txt            # Download file
nxc ftp <IP> -u 'anonymous' -p '' --get /pub/data.txt       # Download from path
```

---

### MSSQL Blank Password Testing

**Port**: 1433/tcp (default instance) or dynamic ports (named instances)

**Default accounts**: `sa` (system administrator), `MSSQLSERVER`, `admin`

```bash
# Test blank passwords
nxc mssql <IP> -u 'sa' -p ''                                # Test sa account
nxc mssql <IP> -u users.txt -p ''                           # Test multiple users
```

```bash
# Execute queries
nxc mssql <IP> -u 'sa' -p '' -q "SELECT @@version"          # Version
nxc mssql <IP> -u 'sa' -p '' -q "SELECT name FROM sys.databases"  # List databases
nxc mssql <IP> -u 'sa' -p '' -q "SELECT * FROM information_schema.tables"  # List tables
```

```bash
# File operations
nxc mssql <IP> -u 'sa' -p '' --get-file 'C:\backup\db.bak' ./db.bak  # Download file
nxc mssql <IP> -u 'sa' -p '' --put-file payload.txt 'C:\temp\payload.txt'  # Upload file
```

**File operations**: Require `xp_cmdshell` enabled or bulk insert privileges

---

### List NetExec Modules

```bash
nxc smb -L                                                  # List SMB modules
nxc ldap -L                                                 # List LDAP modules
nxc mssql -L                                                # List MSSQL modules
nxc ftp -L                                                  # List FTP modules
nxc winrm -L                                                # List WinRM modules
nxc ssh -L                                                  # List SSH modules
nxc rdp -L                                                  # List RDP modules

nxc smb -M spider_plus --options                            # View module options
```

---

## Alternative Tools - Anonymous Access & Enumeration

### smbclient - SMB File Operations

[smbclient](https://www.samba.org/samba/docs/current/man-html/smbclient.1.html) is the native SMB client from Samba. Pre-installed on most Linux distributions.

**UNC path syntax**: `\\\\IP\\SHARE` (Windows) or `//IP/SHARE` (Linux/macOS)

**List shares**:

```bash
smbclient -N -L //<IP>                                      # List shares (null session)
smbclient -N -U '' -L //<IP>                                # List shares (explicit)
smbclient -L //<IP> -U 'guest%'                             # List shares (guest)
```

**Options**:

1. **-N**: No password prompt (null session)
2. **-L**: List shares
3. **-U 'user%pass'**: Specify username and password

**Connect and browse files**:

```bash
# Connect to share
smbclient -N //<IP>/SHARENAME                               # Connect with null session
smbclient //<IP>/SHARENAME -U 'guest%'                      # Connect as guest
```

**Interactive commands** (inside `smb: \>` prompt):

```bash
smb: \> ls                                                  # List files
smb: \> cd folder                                           # Change directory
smb: \> pwd                                                 # Print working directory
smb: \> dir                                                 # List files (alternative)
smb: \> get file.txt                                        # Download single file
smb: \> mget *.txt                                          # Download multiple files
smb: \> prompt OFF                                          # Disable prompts
smb: \> recurse ON                                          # Enable recursion
smb: \> mget *                                              # Download everything
smb: \> put localfile.txt                                   # Upload file
smb: \> mput *.txt                                          # Upload multiple
smb: \> del file.txt                                        # Delete file
smb: \> rm file.txt                                         # Delete file (alternative)
smb: \> mkdir newfolder                                     # Create directory
smb: \> rmdir oldfolder                                     # Remove directory
smb: \> exit                                                # Disconnect
```

**Non-interactive commands**:

```bash
# List files in share
smbclient -N //<IP>/SHARENAME -c 'ls'                       # List files
smbclient -N //<IP>/SHARENAME -c 'cd Documents; ls'         # List subdirectory
```

```bash
# Download files
smbclient -N //<IP>/SHARENAME -c 'get file.txt'             # Download file
smbclient -N //<IP>/SHARENAME -c 'cd backup; get db.bak'    # Download from subdir
```

```bash
# Recursive download all files
smbclient -N //<IP>/SHARENAME -c 'prompt OFF; recurse ON; mget *'
```

```bash
# Download specific file types
smbclient -N //<IP>/SHARENAME -c 'prompt OFF; mget *.txt'
```

```bash
# Upload file
smbclient -N //<IP>/SHARENAME -c 'put local.txt remote.txt'
```

```bash
# Multiple commands
smbclient -N //<IP>/SHARENAME -c 'cd folder; ls; get file.txt'
```

**Command chaining**: Use `;` to separate multiple commands in `-c` flag

---

### rpcclient - RPC Enumeration

[rpcclient](https://www.samba.org/samba/docs/current/man-html/rpcclient.1.html) enumerates domain information via MS-RPC with null session. Part of Samba suite.

**Connect**:

```bash
rpcclient -N -U '' <IP>                                     # Connect with null session
rpcclient -U 'guest%' <IP>                                  # Connect as guest
```

**Interactive commands** (inside `rpcclient $>` prompt):

```bash
rpcclient $> srvinfo                                        # Server info
rpcclient $> enumdomusers                                   # List users
rpcclient $> enumdomgroups                                  # List groups
rpcclient $> querydominfo                                   # Domain info
rpcclient $> getdompwinfo                                   # Password policy
rpcclient $> querydispinfo                                  # User details
rpcclient $> netshareenumall                                # List all shares
rpcclient $> netshareenum                                   # List shares
rpcclient $> queryuser 500                                  # Query user by RID (500=Administrator)
rpcclient $> querygroup 512                                 # Query group by RID (512=Domain Admins)
rpcclient $> querygroupmem 512                              # List group members
rpcclient $> enumalsgroups builtin                          # List local groups
rpcclient $> queryaliasmem builtin 0x220                    # List admin group members
rpcclient $> lookupnames Administrator                      # Get SID from name
rpcclient $> lookupsids S-1-5-21-...-500                    # Get name from SID
rpcclient $> enumprinters                                   # List printers
rpcclient $> enumtrust                                      # List domain trusts
rpcclient $> enumprivs                                      # List privileges
```

**Common RIDs**:

1. **500**: Administrator
2. **501**: Guest
3. **512**: Domain Admins
4. **513**: Domain Users
5. **514**: Domain Guests
6. **515**: Domain Computers
7. **516**: Domain Controllers
8. **544**: Administrators (local)
9. **1000+**: Domain user accounts

**One-liner commands**:

```bash
rpcclient -N -U '' <IP> -c 'enumdomusers'                   # List users
rpcclient -N -U '' <IP> -c 'enumdomgroups'                  # List groups
rpcclient -N -U '' <IP> -c 'querydominfo'                   # Domain info
rpcclient -N -U '' <IP> -c 'netshareenumall'                # List shares
rpcclient -N -U '' <IP> -c 'getdompwinfo'                   # Password policy
rpcclient -N -U '' <IP> -c 'querydispinfo'                  # User details
rpcclient -N -U '' <IP> -c 'srvinfo'                        # Server info
```

```bash
# Chain multiple commands
rpcclient -N -U '' <IP> -c 'enumdomusers;enumdomgroups;netshareenumall'
```

**Command chaining**: Use `;` separator to execute multiple commands in single connection

---

### smbmap - File Enumeration

[smbmap](https://github.com/ShawnDEvans/smbmap) is a Python-based SMB enumeration tool with recursive file listing and pattern-based auto-download.

**List shares**:

```bash
smbmap -u '' -p '' -H <IP>                                  # List shares (null session)
smbmap -u 'guest' -p '' -H <IP>                             # List shares (guest)
```

**Permissions displayed**: `READ ONLY`, `READ, WRITE`, `NO ACCESS`

**List files**:

```bash
smbmap -u '' -p '' -H <IP> -R                               # List all files recursively
smbmap -u '' -p '' -H <IP> -r SHARENAME                     # List files in share
smbmap -u '' -p '' -H <IP> -R -A '.*\.txt'                  # Auto-download .txt files
smbmap -u '' -p '' -H <IP> -R -A '.*\.xml|.*\.config'       # Auto-download config files
smbmap -u '' -p '' -H <IP> -R --depth 2                     # Limit recursion depth
smbmap -u '' -p '' -H <IP> -R --exclude ADMIN$ C$           # Exclude shares
smbmap -u '' -p '' -H <IP> -R --dir-only                    # List directories only
```

**Options**:

1. **-R**: Recursive listing (all shares)
2. **-r SHARENAME**: Target specific share
3. **-A <pattern>**: Auto-download files matching regex
4. **--depth <n>**: Limit recursion depth
5. **--exclude <shares>**: Exclude specific shares
6. **--dir-only**: List directories only (no files)

**Download files**:

```bash
smbmap -u '' -p '' -H <IP> --download 'SHARE\file.txt'      # Download file
smbmap -u '' -p '' -H <IP> --download 'C$\Windows\System32\drivers\etc\hosts'  # Download specific file
```

**Upload files**:

```bash
smbmap -u '' -p '' -H <IP> --upload 'local.txt' 'SHARE\remote.txt'  # Upload file
```

**Search file content** (requires admin rights):

```bash
smbmap -u '' -p '' -H <IP> -R -F 'password'                 # Search file content
```

---

### enum4linux - Comprehensive Enumeration

[enum4linux](https://github.com/CiscoCXSecurity/enum4linux) is a Perl-based wrapper around smbclient, rpcclient, and other tools. [enum4linux-ng](https://github.com/cddmp/enum4linux-ng) is the newer Python rewrite.

**Basic usage**:

```bash
enum4linux <IP>                                             # Basic enumeration
enum4linux -a <IP>                                          # All enumeration (noisy)
```

**Warning**: `-a` flag includes RID cycling which generates hundreds of Event ID 4625 (failed logon) events

**Targeted enumeration**:

```bash
enum4linux -U <IP>                                          # Users only
enum4linux -S <IP>                                          # Shares only
enum4linux -G <IP>                                          # Groups only
enum4linux -P <IP>                                          # Password policy only
enum4linux -o <IP>                                          # OS info only
enum4linux -i <IP>                                          # Printer info only
enum4linux -n <IP>                                          # NetBIOS info only
```

```bash
# Combination
enum4linux -U -S -P <IP>                                    # Users, shares, password policy
```

**RID cycling** (noisy):

```bash
enum4linux -r <IP>                                          # RID cycling (default range)
enum4linux -R 500-600 <IP>                                  # RID cycling (custom range)
enum4linux -R 500-550,1000-1050 <IP>                        # Multiple ranges
```

**Verbose output**:

```bash
enum4linux -v -a <IP>                                       # Verbose all enumeration
```

---

### FTP Client - Anonymous Access

Native `ftp` command pre-installed on Linux/macOS/BSD/Windows.

**Connect**:

```bash
ftp <IP>                                                    # Connect (will prompt for credentials)
# Username: anonymous
# Password: (press Enter or type email)
```

**Interactive commands** (inside `ftp>` prompt):

```bash
ftp> ls                                                     # List files
ftp> dir                                                    # List files (detailed)
ftp> cd directory                                           # Change directory
ftp> pwd                                                    # Print working directory
ftp> binary                                                 # Binary mode (for non-text files)
ftp> ascii                                                  # ASCII mode (for text files)
ftp> get file.txt                                           # Download file
ftp> mget *.txt                                             # Download multiple files
ftp> prompt OFF                                             # Disable prompts
ftp> mget *                                                 # Download all files
ftp> put local.txt                                          # Upload file
ftp> mput *.txt                                             # Upload multiple files
ftp> delete file.txt                                        # Delete file
ftp> mkdir newfolder                                        # Create directory
ftp> rmdir oldfolder                                        # Remove directory
ftp> bye                                                    # Disconnect
ftp> quit                                                   # Disconnect (alternative)
```

**Transfer modes**:

1. **binary**: For executables, images, archives (prevents corruption)
2. **ascii**: For text files (handles line ending conversions)

**Non-interactive**:

```bash
# List files
echo -e "user anonymous\npass\nls\nquit" | ftp -n <IP>
```

```bash
# Download file
echo -e "user anonymous\npass\nbinary\nget file.txt\nquit" | ftp -n <IP>
```

```bash
# Download all files
echo -e "user anonymous\npass\nprompt OFF\nmget *\nquit" | ftp -n <IP>
```

**-n flag**: Disables auto-login (required for scripting with piped commands)

---

### ldapsearch - LDAP Anonymous Queries

[ldapsearch](https://linux.die.net/man/1/ldapsearch) is the native LDAP client from OpenLDAP. Pre-installed on most Linux distributions.

**Test anonymous bind**:

```bash
ldapsearch -x -H ldap://<IP> -b '' -s base                  # Test anonymous bind
ldapsearch -x -H ldap://<IP> -b '' -s base namingContexts   # Get base DN
```

**Options**:

1. **-x**: Simple authentication (required)
2. **-H ldap://<IP>**: LDAP URI (use `ldaps://` for SSL on port 636)
3. **-b 'base DN'**: Base DN to search
4. **-s base**: Search scope = base object only
5. **-LLL**: Reduce output verbosity

**Enumerate users**:

```bash
# All users
ldapsearch -x -H ldap://<IP> -b 'dc=example,dc=com' '(objectClass=user)' -LLL
```

```bash
# Users with descriptions
ldapsearch -x -H ldap://<IP> -b 'dc=example,dc=com' '(objectClass=user)' sAMAccountName,description -LLL
```

```bash
# Admin users
ldapsearch -x -H ldap://<IP> -b 'dc=example,dc=com' '(&(objectClass=user)(adminCount=1))' -LLL
```

```bash
# Users with SPNs (Kerberoastable)
ldapsearch -x -H ldap://<IP> -b 'dc=example,dc=com' '(&(objectClass=user)(servicePrincipalName=*))' -LLL
```

```bash
# Specific user
ldapsearch -x -H ldap://<IP> -b 'dc=example,dc=com' '(sAMAccountName=Administrator)' -LLL
```

**Enumerate groups**:

```bash
# All groups
ldapsearch -x -H ldap://<IP> -b 'dc=example,dc=com' '(objectClass=group)' -LLL
```

```bash
# Domain Admins
ldapsearch -x -H ldap://<IP> -b 'dc=example,dc=com' '(cn=Domain Admins)' member -LLL
```

```bash
# Privileged groups
ldapsearch -x -H ldap://<IP> -b 'dc=example,dc=com' '(&(objectClass=group)(adminCount=1))' -LLL
```

**Enumerate computers**:

```bash
# All computers
ldapsearch -x -H ldap://<IP> -b 'dc=example,dc=com' '(objectClass=computer)' -LLL
```

```bash
# Domain controllers
ldapsearch -x -H ldap://<IP> -b 'dc=example,dc=com' '(userAccountControl:1.2.840.113556.1.4.803:=8192)' -LLL
```

```bash
# Servers
ldapsearch -x -H ldap://<IP> -b 'dc=example,dc=com' '(&(objectClass=computer)(operatingSystem=*Server*))' -LLL
```

**LDAP filter operators**:

1. **&**: AND operator (all conditions must match)
2. **|**: OR operator (any condition matches)
3. **!**: NOT operator (condition must not match)
4. **=**: Equality match
5. **~=**: Approximate match
6. **>=**, **<=**: Greater/less than or equal
7. **=***: Presence check (attribute exists)

---

### NFS - Mount and Browse

[NFS](https://en.wikipedia.org/wiki/Network_File_System) typically has no authentication—access control based solely on IP restrictions.

**List exports**:

```bash
showmount -e <IP>                                           # List NFS exports
showmount -a <IP>                                           # List mounted clients
```

**Export format**: `/path (allowed_hosts)` where allowed_hosts can be `*` (all), `IP/subnet`, or specific hostnames

**Mount and access**:

```bash
# Mount share
sudo mount -t nfs <IP>:/export /mnt/nfs                     # Mount NFS share
sudo mount -t nfs -o vers=3 <IP>:/export /mnt/nfs           # Mount with NFSv3
```

**Mount options**:

1. **vers=3**: Force NFSv3
2. **vers=4**: Force NFSv4
3. **ro**: Read-only mount
4. **rw**: Read-write mount
5. **soft**: Soft mount (timeout on errors)
6. **hard**: Hard mount (retry indefinitely)

```bash
# Browse files
cd /mnt/nfs                                                 # Change to mount point
ls -la                                                      # List files
find . -type f -name "*.txt"                                # Find files
cat file.txt                                                # Read file
cp file.txt /tmp/                                           # Copy file
```

```bash
# Unmount
sudo umount /mnt/nfs                                        # Unmount share
```

**Create mount point** (if doesn't exist):

```bash
sudo mkdir -p /mnt/nfs                                      # Create directory
```

---

### SNMP - Community String Testing

[SNMP](https://en.wikipedia.org/wiki/Simple_Network_Management_Protocol) versions 1 and 2c use plaintext community strings. Default strings: `public` (read-only), `private` (read-write).

**Test with onesixtyone**:

[onesixtyone](https://github.com/trailofbits/onesixtyone) is a fast SNMP scanner for brute forcing community strings.

```bash
onesixtyone <IP>                                            # Test default communities
onesixtyone -c /usr/share/seclists/Discovery/SNMP/common-snmp-community-strings.txt <IP>
onesixtyone -c community.txt -i targets.txt                 # Multiple hosts
```

**Options**:

1. **-c <file>**: Community string wordlist
2. **-i <file>**: IP address list file
3. **-w <n>**: Wait time in milliseconds (default 10)

**Walk with snmpwalk**:

[snmpwalk](https://linux.die.net/man/1/snmpwalk) queries SNMP MIB tree using valid community string.

```bash
# Full walk (noisy - thousands of queries)
snmpwalk -v2c -c public <IP>                                # Walk entire tree
```

**Specific OIDs**:

```bash
snmpwalk -v2c -c public <IP> 1.3.6.1.2.1.1                  # System info
snmpwalk -v2c -c public <IP> 1.3.6.1.2.1.2                  # Network interfaces
snmpwalk -v2c -c public <IP> 1.3.6.1.2.1.25.4.2             # Running processes
snmpwalk -v2c -c public <IP> 1.3.6.1.2.1.25.6.3             # Installed software
snmpwalk -v2c -c public <IP> 1.3.6.1.4.1.77.1.2.25          # User accounts (Windows)
snmpwalk -v2c -c public <IP> 1.3.6.1.2.1.25.2.3             # Storage info
```

**Common OIDs**:

1. **1.3.6.1.2.1.1**: System (hostname, description, uptime, contact, location)
2. **1.3.6.1.2.1.2**: Interfaces (names, MACs, IPs, statistics)
3. **1.3.6.1.2.1.25.4.2**: Running processes
4. **1.3.6.1.2.1.25.6.3**: Installed software
5. **1.3.6.1.2.1.6.13**: TCP connections
6. **1.3.6.1.2.1.7.5**: UDP endpoints

---

### Redis - Anonymous Access

[Redis](https://redis.io/) is an in-memory data structure store. Default installations often have no authentication.

**Port**: 6379/tcp

**Connect and enumerate**:

```bash
redis-cli -h <IP>                                           # Connect to Redis
```

**Commands** (inside `<IP>:6379>` prompt):

```bash
<IP>:6379> INFO                                             # Server info
<IP>:6379> CONFIG GET *                                     # Get config
<IP>:6379> KEYS *                                           # List all keys
<IP>:6379> GET keyname                                      # Get key value
<IP>:6379> DBSIZE                                           # Database size
<IP>:6379> CLIENT LIST                                      # Connected clients
<IP>:6379> SCAN 0                                           # Scan keys (non-blocking)
```

**Authentication check**:

1. If `INFO` succeeds: No authentication required
2. If `(error) NOAUTH Authentication required`: Authentication enabled

**Other data type commands**:

1. **HGETALL <key>**: Get all hash fields
2. **LRANGE <key> 0 -1**: Get all list elements
3. **SMEMBERS <key>**: Get all set members
4. **ZRANGE <key> 0 -1**: Get all sorted set members

---

### MongoDB - Anonymous Access

[MongoDB](https://www.mongodb.com/) is a NoSQL document database. Older versions often allow anonymous access.

**Port**: 27017/tcp

**Connect and enumerate**:

```bash
mongo <IP>                                                  # Connect (legacy shell)
mongosh <IP>                                                # Connect (new shell)
```

**Commands** (inside `>` prompt):

```bash
> show dbs                                                  # List databases
> use admin                                                 # Select database
> show collections                                          # List collections
> db.users.find()                                           # Query collection
> db.users.find().limit(10)                                 # Limit results
> db.getUsers()                                             # List users
> db.stats()                                                # Database stats
```

**Authentication check**:

1. If `show dbs` succeeds: No authentication required
2. If `MongoServerError: command listDatabases requires authentication`: Authentication enabled

**Common databases**:

1. **admin**: Authentication/authorization data
2. **config**: Sharding configuration
3. **local**: Replication data
4. Custom application databases

---

### PostgreSQL - Trust Auth

[PostgreSQL](https://www.postgresql.org/) is a relational database. Trust authentication allows connections without password.

**Port**: 5432/tcp

**Default superuser**: `postgres`

**Connect and enumerate**:

```bash
psql -U postgres -h <IP>                                    # Connect with trust auth
```

**Commands** (inside `postgres=#` prompt):

```bash
postgres=# \l                                               # List databases
postgres=# \c dbname                                        # Connect to database
postgres=# \dt                                              # List tables
postgres=# \du                                              # List users
postgres=# SELECT version();                                # Version
postgres=# SELECT * FROM users;                             # Query table
postgres=# \q                                               # Quit
```

**One-liner**:

```bash
psql -U postgres -h <IP> -c "\l"                            # List databases
psql -U postgres -h <IP> -d dbname -c "SELECT * FROM users;" # Query table
```

**Psql meta-commands**:

1. **\l**: List databases
2. **\c <database>**: Connect to database
3. **\dt**: List tables
4. **\dt+**: List tables with sizes
5. **\du**: List users/roles
6. **\dn**: List schemas
7. **\df**: List functions
8. **\dv**: List views

---

### MySQL/MariaDB - No Password

[MySQL](https://www.mysql.com/) and [MariaDB](https://mariadb.com/) are relational databases. Root account without password is a critical misconfiguration.

**Port**: 3306/tcp

**Default root account**: `root@localhost` (often restricted to localhost, but may allow remote)

**Connect and enumerate**:

```bash
mysql -h <IP> -u root                                       # Connect with no password
```

**Commands** (inside `mysql>` prompt):

```bash
mysql> SHOW DATABASES;                                      # List databases
mysql> USE mysql;                                           # Select database
mysql> SHOW TABLES;                                         # List tables
mysql> SELECT user,host FROM mysql.user;                    # List users
mysql> SELECT version();                                    # Version
mysql> SELECT * FROM users;                                 # Query table
mysql> exit;                                                # Quit
```

**One-liner**:

```bash
mysql -h <IP> -u root -e "SHOW DATABASES;"                  # List databases
mysql -h <IP> -u root -e "USE mysql; SELECT user,host FROM mysql.user;"  # List users
```

**Common databases**:

1. **mysql**: System database (users, privileges)
2. **information_schema**: Metadata (tables, columns, constraints)
3. **performance_schema**: Performance metrics
4. **sys**: System views (MySQL 5.7+)

---

### Elasticsearch - Anonymous API Access

[Elasticsearch](https://www.elastic.co/) is a distributed search and analytics engine. Default installations often allow anonymous HTTP API access.

**Port**: 9200/tcp (HTTP API)

**Query with curl**:

```bash
curl http://<IP>:9200/                                      # Cluster info
curl http://<IP>:9200/_cat/indices?v                        # List indices
curl http://<IP>:9200/_search?pretty                        # Search all
curl http://<IP>:9200/index_name/_search?pretty             # Search index
curl http://<IP>:9200/index_name/_mapping?pretty            # Index mapping
curl http://<IP>:9200/_cluster/health?pretty                # Cluster health
curl http://<IP>:9200/_nodes?pretty                         # Node info
curl http://<IP>:9200/_count?pretty                         # Count documents
```

**Search with query**:

```bash
curl -X POST http://<IP>:9200/_search?pretty -H 'Content-Type: application/json' -d '
{
  "query": {"match_all": {}}
}'
```

**Authentication check**:

1. If cluster info returns: Anonymous access allowed
2. If `401 Unauthorized` or `security_exception`: Authentication enabled (X-Pack Security)

**Common indices**: `.kibana`, application-specific indices

**API endpoints**:

1. **/**: Cluster information
2. **/_cat/indices**: List indices (human-readable)
3. **/_search**: Search all indices
4. **/<index>/_search**: Search specific index
5. **/<index>/_mapping**: Index schema
6. **/_cluster/health**: Cluster status
7. **/_cluster/settings**: Cluster settings

---

## References

1. [NetExec GitHub Repository](https://github.com/Pennyw0rth/NetExec)
2. [NetExec Wiki Documentation](https://www.netexec.wiki/)
3. [Samba smbclient Manual](https://www.samba.org/samba/docs/current/man-html/smbclient.1.html)
4. [Samba rpcclient Manual](https://www.samba.org/samba/docs/current/man-html/rpcclient.1.html)
5. [smbmap GitHub Repository](https://github.com/ShawnDEvans/smbmap)
6. [enum4linux GitHub Repository](https://github.com/CiscoCXSecurity/enum4linux)
7. [enum4linux-ng GitHub Repository](https://github.com/cddmp/enum4linux-ng)
8. [HackTricks - rpcclient Enumeration](https://book.hacktricks.xyz/network-services-pentesting/pentesting-smb/rpcclient-enumeration)
9. [HackTricks - LDAP Pentesting](https://book.hacktricks.xyz/network-services-pentesting/pentesting-ldap)
10. [OpenLDAP ldapsearch Manual](https://linux.die.net/man/1/ldapsearch)
11. [onesixtyone GitHub Repository](https://github.com/trailofbits/onesixtyone)
12. [snmpwalk Manual](https://linux.die.net/man/1/snmpwalk)
13. [Redis Security Guide](https://redis.io/docs/manual/security/)
14. [MongoDB Authentication Documentation](https://www.mongodb.com/docs/manual/core/authentication/)
15. [PostgreSQL pg_hba.conf Documentation](https://www.postgresql.org/docs/current/auth-pg-hba-conf.html)
16. [MySQL Connection Documentation](https://dev.mysql.com/doc/refman/8.0/en/connecting.html)
17. [Elasticsearch REST APIs](https://www.elastic.co/guide/en/elasticsearch/reference/current/rest-apis.html)

---

#HTB #enumeration #NetExec #SMB #LDAP #FTP #SNMP #NFS #Redis #MongoDB #Elasticsearch #PostgreSQL #MySQL #null-session #anonymous-access #smbclient #rpcclient #smbmap #enum4linux #ldapsearch #pentesting #OSCP
