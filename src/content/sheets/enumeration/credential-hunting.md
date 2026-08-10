---
title: "Credential Hunting"
description: "grep -r password /path 2>/dev/null"
category: enumeration
tags: ["enumeration"]
tools: []
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Enumeration/Credential Hunting.md"
---
# Basic recursive search (case-insensitive, whole word, suppress errors)
grep -r password /path 2>/dev/null

# Best practice: case-insensitive, line numbers, skip binaries, with color
grep -rnIi --color=auto 'password' /etc 2>/dev/null

# Multiple patterns (OR logic)
grep -rnIi -E 'password|api_key|secret|token' /var/www 2>/dev/null
```

### Options and Flags

1. **-r** — Recursive search through directories
2. **-i** — Case-insensitive matching
3. **-n** — Show line numbers in output
4. **-I** — Skip binary files (prevents "Binary file matches" messages)
5. **-w** — Match whole word only (prevents false positives like "password_protected")
6. **-l** — List filenames only (no content; faster for large result sets)
7. **-H** — Always print filename with matches (default for multiple files)
8. **-o** — Print only matching part of line (useful for extracting values)
9. **-E** — Extended regex (enables `|` for OR, `+`, `?`)
10. **--color=auto** — Highlight matches (always use this)
11. **--include='*.ext'** — Search only specific file types
12. **--exclude-dir='dir'** — Skip directories (e.g., node_modules, .git)
13. **2>/dev/null** — Suppress permission denied errors

### Practical Examples

```bash
# Search all config files for password strings
grep -rnIi --include='*.conf' --include='*.config' --include='*.cnf' 'password' /etc 2>/dev/null

# Find database credentials in web apps
grep -rnIi -E 'DB_PASS|DATABASE_PASSWORD|dbpass' /var/www 2>/dev/null

# Extract values after "password=" pattern
grep -roIi 'password=' /opt | cut -d= -f2

# Search with multiple keywords across targeted directories
grep -rnIi -E 'pass=|pwd=|api_key=|secret=' /etc /opt /var/www /home 2>/dev/null | tee creds.txt

# Find SSH private keys
grep -rnI 'BEGIN.*PRIVATE KEY' /home /root 2>/dev/null

# Exclude irrelevant directories to reduce noise
grep -rnIi --exclude-dir={proc,sys,dev,run,boot} 'password' / 2>/dev/null
```

### Output Interpretation

**Format:** `filename:line_number:matching_line`

**Look for:**
1. Plaintext credentials
2. Connection strings
3. API keys
4. Environment variable assignments

**False positives:** Documentation, comments, variable names without values

### OPSEC and Detection Notes

1. **HIGH NOISE**: Recursive grep from `/` generates massive I/O and CPU load; detectable by performance monitoring
2. **LOGGED**: [auditd](https://linux-audit.com/) file watches on `/etc/shadow`, `/etc/passwd`, `~/.ssh/*` will log read attempts to `/var/log/audit/audit.log`
3. **EDR DETECTION**: Rapid sequential file reads across multiple sensitive directories trigger anomaly alerts
4. **MITIGATION**: Use targeted directory searches (`/var/www`, `/opt`, `/home/user`) instead of whole filesystem; use `--exclude-dir` liberally
5. Permission denied errors flood terminal without `2>/dev/null`; also hides potential targets

### Common Errors

1. `Binary file (standard input) matches` — File contains null bytes or UTF-16 encoding; use `-I` to skip or `-a` to force text treatment
2. Hangs with no output — grep waiting for stdin when no file argument given; use Ctrl+D to exit
3. `grep: memory exhausted` — Pattern too complex or file too large; narrow search scope or use simpler regex
4. No matches found — Check case sensitivity (`-i`), file permissions, [SELinux](https://www.redhat.com/en/topics/linux/what-is-selinux) denials (`ls -Z`, `sestatus`)
5. Shell glob expansion — Quote patterns with wildcards: `'pass*'` not `pass*`

### Version and Platform Notes

1. [GNU grep](https://www.gnu.org/software/grep/) (Linux default): supports lazy matching, `-P` for Perl regex
2. [BSD grep](https://www.freebsd.org/cgi/man.cgi?query=grep) (macOS default): limited regex features, no lazy matching
3. GNU grep 3.0+ includes performance optimizations for large files

---

## Phase 1: Fast Filename Enumeration

**Purpose:** Quickly locate files with password-related names before content searching

**Prerequisites:** Standard user access; [locate](https://man7.org/linux/man-pages/man1/locate.1.html) database (`updatedb`) ideally current

### Core Commands

```bash
# Fastest: locate database search (requires updated database)
locate -i password
locate -i 'pass'
locate -r '\.conf$'

# Filename-only find (case-insensitive)
find / -iname '*password*' 2>/dev/null
find / -iname '*pass*' -o -iname '*pwd*' -o -iname '*credential*' 2>/dev/null
```

### Options and Flags

1. **locate -i** — Case-insensitive filename search
2. **locate -r** — Regex pattern matching
3. **find -iname** — Case-insensitive name pattern
4. **-o** — OR operator for multiple find conditions
5. **updatedb** — Refresh locate database (requires root; runs daily via cron)

### Practical Examples

```bash
# Search for password-related filenames (super fast)
locate -i password | grep -v 'lib\|share\|fonts\|doc'
locate -i pwd | grep -v 'lib\|share\|fonts\|doc'

# Find config files by name
locate '.conf' | grep -i 'password\|mysql\|db\|api'

# Find with name patterns
find /var/www /opt /home -type f \( -iname '*pass*' -o -iname '*secret*' -o -iname '*.pem' \) 2>/dev/null

# Find files modified in last 7 days
find /var/www /tmp -type f -mtime -7 -iname '*config*' 2>/dev/null
```

### Output Interpretation

1. Full file paths; manually inspect high-value targets (`.conf`, `.cnf`, `.sh`, `.env`, `.bak`)
2. **Prioritize:** `/etc`, `/var/www`, `/opt`, `/home`, `/root/.ssh`, `/tmp`

### OPSEC and Detection Notes

1. **LOW NOISE**: locate reads pre-built database (no filesystem traversal; very fast)
2. **MODERATE NOISE**: `find /` traverses filesystem; detectable via I/O monitoring
3. Target specific directories to minimize footprint: `find /var/www /opt /home` not `find /`

### Common Errors

1. `locate: can not stat` — Database stale; run `updatedb` (requires root) or use find
2. `find: permission denied` — Normal for non-root user; redirect stderr with `2>/dev/null`

### Version and Platform Notes

1. locate database location varies: `/var/lib/mlocate/mlocate.db` (Debian/Ubuntu), `/var/db/locate.database` (BSD)
2. updatedb runs daily via `/etc/cron.daily/mlocate` on modern Linux

---

## Phase 2: Targeted File Type Enumeration

**Purpose:** Enumerate high-value file types (configs, DBs, scripts, backups) before content search

**Prerequisites:** Standard user access; bash shell

### Core Commands

```bash
# Find all config files
find /etc /opt /var/www -type f \( -name '*.conf' -o -name '*.config' -o -name '*.cnf' \) 2>/dev/null

# Find database files
find / -type f \( -name '*.sql' -o -name '*.db' -o -name '*.sqlite*' \) 2>/dev/null

# Find scripts and environment files
find /var/www /opt /home -type f \( -name '*.sh' -o -name '*.env' -o -name '.env' \) 2>/dev/null
```

### Options and Flags

1. **find -type f** — Regular files only (excludes directories, links)
2. **-name 'pattern'** — Case-sensitive name matching
3. **-iname 'pattern'** — Case-insensitive name matching
4. **-o** — OR operator for multiple name conditions
5. **\( \)** — Group multiple conditions

### Practical Examples

```bash
# Configuration file loop (clean output)
for ext in conf config cnf; do 
  echo -e "\n=== Files with .$ext extension ==="; 
  find /etc /opt /var/www -name "*.$ext" 2>/dev/null | grep -v 'lib\|fonts\|share\|doc'; 
done

# Database file loop with filtering
for ext in sql db sqlite sqlite3; do 
  echo -e "\n=== Files with .$ext extension ==="; 
  find / -name "*.$ext" 2>/dev/null | grep -v 'lib\|share\|man\|doc'; 
done

# Backup and archive files (high-value targets)
find / -type f \( -name '*.bak' -o -name '*.backup' -o -name '*.old' -o -name '*~' \) 2>/dev/null | head -50

# SSH keys and certificates
find / -type f \( -name 'id_rsa' -o -name 'id_dsa' -o -name 'id_ed25519' -o -name '*.pem' -o -name '*.key' \) 2>/dev/null

# World-readable files (permission misconfiguration)
find / -type f -perm -004 -ls 2>/dev/null | grep -v 'proc\|sys\|usr/share'

# SUID/SGID binaries (potential privilege escalation)
find / -type f \( -perm -4000 -o -perm -2000 \) -ls 2>/dev/null
```

### Output Interpretation

1. Paths to files; next step is content search with grep
2. Prioritize small files (`-size -100k`) for faster manual inspection
3. Large `.sql` or `.db` files may require [strings](https://man7.org/linux/man-pages/man1/strings.1.html) or specialized tools

### OPSEC and Detection Notes

1. **MODERATE NOISE**: Filesystem traversal generates I/O; EDR may flag rapid enumeration
2. Target specific directories first (`/var/www`, `/opt`, `/etc`, `/home`) before whole filesystem
3. Exclude noisy system paths with `grep -v` to reduce output volume

### Common Errors

1. `find: missing argument to '-name'` — Quote patterns: `-name '*.conf'` not `-name *.conf`
2. Too many results — Add size filters (`-size -10M`), time filters (`-mtime -30`), or path restrictions

---

## Phase 3: Content Search in Targeted Files

**Purpose:** Search file contents for credential patterns after identifying target files

**Prerequisites:** List of target files (from Phase 2); standard user or root access

### Core Commands

```bash
# Pipe find results to grep with xargs (handles spaces)
find /etc /opt /var/www -type f -name '*.conf' -print0 | xargs -0 grep -nIi 'password' 2>/dev/null

# Execute grep on each find result
find /var/www -type f \( -name '*.conf' -o -name '*.php' -o -name '*.env' \) -exec grep -HnIi 'password\|api_key' {} \; 2>/dev/null
```

### Options and Flags

1. **find -print0** — Null-separated output (handles filenames with spaces)
2. **xargs -0** — Read null-separated input
3. **find -exec grep {} \;** — Execute grep on each file individually
4. **grep -H** — Always show filename (critical for multi-file searches)

### Practical Examples

```bash
# Search config files for database credentials
find /etc /opt -name '*.conf' -exec grep -HnIi -E 'password|user|host|dbname' {} \; 2>/dev/null

# Search web app files for API keys
find /var/www -type f \( -name '*.php' -o -name '*.py' -o -name '*.js' -o -name '.env' \) -print0 | \
  xargs -0 grep -nIi -E 'api[_-]?key|secret|token|auth' 2>/dev/null

# Search scripts for embedded credentials
find /home /opt -name '*.sh' -exec grep -HnIi -E 'export.*PASS|PASSWORD=' {} \; 2>/dev/null

# Combined file type + content search one-liner
find /etc /opt /var/www -type f \( -name '*.conf' -o -name '*.config' -o -name '*.cnf' \) \
  -exec grep -Hn 'password\|pass=' {} \; 2>/dev/null | tee config-creds.txt

# Search only recently modified files (last 30 days)
find /var/www -type f -mtime -30 -name '*.conf' -print0 | \
  xargs -0 grep -nIi 'password' 2>/dev/null
```

### Output Interpretation

**Format:** `filename:line_number:matching_line`

1. Extract values: pipe to `cut`, `awk`, or `sed` for parsing
2. Context: use `grep -A 2 -B 2` to see surrounding lines

### OPSEC and Detection Notes

1. **HIGH NOISE**: Reading many files rapidly triggers I/O alerts and auditd logging
2. Target smallest file set possible; use Phase 2 filtering aggressively
3. Sensitive file access (e.g., `/etc/shadow`, `~/.ssh/id_rsa`) logged by auditd to `/var/log/audit/audit.log`

### Common Errors

1. `xargs: argument line too long` — Large result sets exceed buffer; use `find -exec` instead
2. Binary files slow search — Always use `-I` flag with grep to skip binaries
3. No output despite known credentials — Check file encoding (`file filename`), SELinux contexts

---

## Phase 4: History and Environment Inspection

**Purpose:** Check command history, environment variables, and process memory for credentials

**Prerequisites:** Standard user or root shell access

### Core Commands

```bash
# Check command history files
cat ~/.bash_history ~/.zsh_history 2>/dev/null | grep -i 'pass\|user\|key\|secret'

# Check current environment variables
env | grep -i 'pass\|key\|secret\|token\|api'

# Check process command lines
ps auxww | grep -E 'mysql|psql|ssh|ftp' | grep -v grep
```

### Practical Examples

```bash
# History files across all users (requires root)
find /home /root -type f \( -name '.bash_history' -o -name '.zsh_history' -o -name '.mysql_history' \) \
  -exec grep -HnIi -E 'password|pass=|--password' {} \; 2>/dev/null

# Additional history files
cat ~/.lesshst ~/.viminfo ~/.python_history 2>/dev/null | grep -i 'pass'

# Environment variables from specific process
cat /proc/[PID]/environ | tr '\0' '\n' | grep -i 'pass\|key'

# All process environments (requires root)
for pid in $(ls /proc | grep '^[0-9]'); do 
  echo "=== PID $pid ==="; 
  cat /proc/$pid/environ 2>/dev/null | tr '\0' '\n' | grep -iE 'pass|key|secret'; 
done

# Database connection strings in process memory (requires root)
ps aux | grep -E 'mysql|postgres' | awk '{print $2}' | \
  xargs -I {} sh -c 'strings /proc/{}/environ 2>/dev/null | grep -i password'

# Check systemd service files for credentials
grep -rnIi 'Environment=' /etc/systemd/system /usr/lib/systemd/system 2>/dev/null | \
  grep -iE 'pass|key|secret'
```

### Output Interpretation

1. History files may contain credentials passed as CLI arguments
2. Environment variables often store DB passwords, API keys, tokens
3. Process command lines expose credentials in `--password=value` style arguments
4. `/proc/[pid]/environ` contains environment at process launch time

### OPSEC and Detection Notes

1. **LOW NOISE**: Reading history files and env variables minimal impact
2. **MODERATE NOISE**: Iterating over all `/proc/[pid]/environ` may trigger EDR alerts
3. auditd may log access to specific users' history files if watched

### Common Errors

1. `/proc/[pid]/environ` access denied — Processes owned by other users unreadable without root
2. Empty output from `cat /proc/[pid]/environ` — Process exited or no environment variables
3. History file not found — User using different shell or history disabled (`HISTFILE=`)

### Version and Platform Notes

1. `/proc` filesystem standard on Linux; not available on BSD/macOS (use `ps e` instead)

---

## Phase 5: Log File Analysis

**Purpose:** Search system and application logs for credentials, authentication events, and errors exposing secrets

**Prerequisites:** Read access to `/var/log` (many logs require root)

### Core Commands

```bash
# Search all log files for password strings
grep -rnIi 'password' /var/log 2>/dev/null

# Search compressed logs with zgrep
zgrep -ai 'password\|credential\|secret' /var/log/*.gz 2>/dev/null

# Loop through logs for authentication events
for log in /var/log/*; do 
  grep -iE 'accepted|password|failure' "$log" 2>/dev/null && echo "=== $log ==="; 
done
```

### Options and Flags

1. **[zgrep](https://linux.die.net/man/1/zgrep)** — Search compressed files (`.gz`, `.bz2`)
2. **zgrep -a** — Treat all files as text (avoids binary detection)
3. Standard grep flags apply: `-i`, `-n`, `-E`, `-r`

### Practical Examples

```bash
# SSH authentication logs
grep -i 'accepted\|failed' /var/log/auth.log /var/log/secure 2>/dev/null | tail -50

# Application error logs (may expose DB connection strings)
grep -rnIi -E 'error.*password|exception.*credential' /var/log 2>/dev/null

# Web server logs for API keys in URLs (bad practice but happens)
grep -rE 'api_key=|token=' /var/log/apache2 /var/log/nginx 2>/dev/null | head -20

# Database logs
grep -rnIi 'password' /var/log/mysql /var/log/postgresql 2>/dev/null

# Search compressed logs (older rotated logs)
zgrep -aiE 'password=|api_key=|secret=' /var/log/*.gz /var/log/*/*.gz 2>/dev/null | less

# Conditional log search (only print logs with matches)
for logfile in $(ls /var/log/* 2>/dev/null); do 
  RESULT=$(grep -iE 'password|accepted|failure' "$logfile" 2>/dev/null); 
  if  $RESULT ; then 
    echo -e "\n=== $logfile ==="; 
    echo "$RESULT" | head -10; 
  fi; 
done
```

### Output Interpretation

1. **auth.log/secure:** successful/failed login attempts with usernames
2. **Application logs:** stack traces may expose credentials in connection strings
3. **Web logs:** API keys or tokens in GET parameters (insecure but common)
4. **Look for:** timestamps, usernames, source IPs, credential exposure patterns

### OPSEC and Detection Notes

1. **HIGH ALERT**: Access to `/var/log/auth.log`, `/var/log/secure`, `/var/log/audit/` triggers high-priority alerts
2. auditd logs its own file watches to `/var/log/audit/audit.log` — reading this creates recursive log entry
3. Legitimate sysadmins read logs frequently; timing and context matter for detection

### Common Errors

1. `grep: /var/log/[file]: Permission denied` — Many logs require root; run as root or use `sudo`
2. `zgrep: command not found` — Install gzip utils: `apt install gzip` or `yum install gzip`
3. Binary log formats — [systemd journal](https://www.freedesktop.org/software/systemd/man/systemd-journald.service.html) uses binary format; use `journalctl` instead of grep

### Version and Platform Notes

1. Log paths vary: `/var/log/auth.log` (Debian/Ubuntu), `/var/log/secure` (RHEL/CentOS)
2. systemd systems: use `journalctl -xe | grep -i password` for systemd journal

---

## find File Discovery and Filtering

**Purpose:** Locate files by name, type, size, permissions, modification time before content search

**Prerequisites:** Standard user access; [GNU findutils](https://www.gnu.org/software/findutils/)

### Core Commands

```bash
# Basic recursive file search
find /path -type f -name 'pattern' 2>/dev/null

# Search with multiple name patterns (OR logic)
find / -type f \( -name '*.conf' -o -name '*.config' \) 2>/dev/null

# Permission-based search
find / -type f -perm -004 2>/dev/null
```

### Options and Flags

1. **-type f** — Regular files only
2. **-type d** — Directories only
3. **-name 'pattern'** — Case-sensitive name match (shell wildcards: `*`, `?`)
4. **-iname 'pattern'** — Case-insensitive name match
5. **-perm -mode** — Files with at least these permissions set
6. **-perm /mode** — Files with any of these permissions set
7. **-user username** — Files owned by user
8. **-group groupname** — Files owned by group
9. **-size +100M** — Files larger than 100MB (`+` greater, `-` smaller, no prefix exact)
10. **-mtime -7** — Modified in last 7 days (`-` within, `+` older than)
11. **-atime** — Last access time
12. **-ctime** — Last status change time
13. **\( \)** — Group multiple expressions
14. **-o** — OR operator
15. **! or -not** — Negation

### Practical Examples

```bash
# World-writable files (security risk)
find / -type f -perm -002 2>/dev/null

# SUID binaries (privilege escalation vectors)
find / -type f -perm -4000 -ls 2>/dev/null

# Files owned by www-data user
find /var/www -user www-data -type f 2>/dev/null

# Large files (potential DB dumps)
find / -type f -size +50M -size -500M 2>/dev/null

# Recently modified config files (may contain fresh creds)
find /etc -type f -name '*.conf' -mtime -7 2>/dev/null

# SSH keys across all user home directories
find /home /root -type f \( -name 'id_rsa' -o -name 'id_dsa' -o -name 'id_ed25519' \) 2>/dev/null

# Writable directories (potential persistence locations)
find / -type d -perm -002 ! -path '/proc/*' ! -path '/sys/*' 2>/dev/null

# Files with no user ownership (orphaned files)
find / -nouser -ls 2>/dev/null
```

### Output Interpretation

1. Default: full path to matching files
2. Use `-ls` for detailed output (permissions, size, owner, timestamp)
3. Pipe results to grep, xargs, or `-exec` for further processing

### OPSEC and Detection Notes

1. **MODERATE-HIGH NOISE**: Full filesystem traversal from `/` generates significant I/O
2. Target specific directories to reduce footprint
3. SUID/permission enumeration is standard attacker behavior; may trigger alerts

### Common Errors

1. `find: missing argument to '-name'` — Quote wildcards: `-name '*.conf'`
2. `find: invalid argument '-perm 777'` — Use octal: `-perm 0777` or symbolic: `-perm -u=rwx,g=rwx,o=rwx`
3. Parentheses syntax error — Escape with backslash: `\(` `\)` or quote: `'(' ')'`
4. Slow search — Exclude large directories: `! -path '/proc/*' ! -path '/sys/*'`

### Version and Platform Notes

1. GNU find (Linux): supports `-printf`, `-regex`, extended options
2. BSD find (macOS): limited features; use `-print0` and `xargs -0` for portability

---

## strings Binary File Extraction

**Purpose:** Extract printable ASCII strings from binary files (executables, compiled code, memory dumps)

**Prerequisites:** [GNU binutils](https://www.gnu.org/software/binutils/) installed (standard on Linux)

### Core Commands

```bash
# Extract printable strings from binary
strings /path/to/binary

# Set minimum string length (default 4)
strings -n 8 /path/to/binary

# Search extracted strings for patterns
strings /path/to/binary | grep -i 'password\|api\|key'
```

### Options and Flags

1. **-n [num]** — Minimum string length (default 4; increase to reduce noise)
2. **-a** — Scan entire file (default scans only initialized/loaded sections)
3. **-t [format]** — Print offset of each string (`o` octal, `x` hex, `d` decimal)
4. **-e [encoding]** — Character encoding (`s` 7-bit, `S` 8-bit, `b` 16-bit big-endian, `l` 16-bit little-endian)

### Practical Examples

```bash
# Extract all strings and search for credentials
strings /usr/local/bin/app | grep -iE 'password|user|api_key|secret'

# Extract longer strings to reduce noise
strings -n 10 /bin/suspicious | less

# Extract strings with hex offsets
strings -t x /path/to/binary | grep -i 'config'

# Extract from memory dump or core dump
strings /proc/[PID]/mem 2>/dev/null | grep -i 'pass'

# Extract from all binaries in directory
find /usr/local/bin -type f -executable -exec sh -c 'echo "=== {} ==="; strings {} | grep -i password' \; 2>/dev/null

# Extract from libraries
strings /usr/lib/*.so | grep -iE 'password|api_key' | sort -u
```

### Output Interpretation

1. Raw printable strings; includes code, data, error messages, hardcoded credentials
2. High noise-to-signal ratio; use grep filters and increase `-n` value
3. **Look for:** connection strings, API endpoints, embedded credentials, license keys

### OPSEC and Detection Notes

1. **LOW NOISE**: strings reads files like cat; minimal detection footprint
2. Extracting strings from `/proc/[pid]/mem` requires same user or root; may log access

### Common Errors

1. `strings: [file]: file format not recognized` — File truly not a binary; use `file` to verify
2. Excessive output — Increase minimum length: `-n 8` or `-n 12`
3. Permission denied on `/proc/[pid]/mem` — Requires root or process owner

### Version and Platform Notes

1. GNU strings (Linux standard): supports all encodings and formats
2. BSD strings (macOS): limited encoding support

---

## Parsing and Filtering Output (awk, sed, cut)

**Purpose:** Extract and format specific fields from grep/find results

**Prerequisites:** Standard Linux shell (bash/sh)

### Core Commands

```bash
# awk: split by delimiter and print fields
grep 'password=' file.conf | awk -F= '{print $2}'

# cut: extract column by delimiter
grep 'user:' file | cut -d: -f2

# sed: regex extraction
sed -n 's/.*password=\([^&]*\).*/\1/p' file
```

### Options and Flags

1. **awk -F[char]** — Field separator (default whitespace)
2. **awk {print $N}** — Print field N (1-indexed; `$0` entire line)
3. **cut -d[char]** — Delimiter character
4. **cut -f[N]** — Field number(s) to extract
5. **sed -n** — Suppress default output (only print explicit `p` commands)
6. **sed s/pattern/replacement/** — Substitute (regex)

### Practical Examples

```bash
# Extract passwords from "password=value" format
grep -ri 'password=' /etc | awk -F= '{print $2}'

# Extract usernames from /etc/passwd (field 1, delimiter :)
cut -d: -f1 /etc/passwd

# Extract usernames and home directories
awk -F: '{print $1 " -> " $6}' /etc/passwd

# Extract database credentials from config
grep -E 'user|password|host' db.conf | awk -F= '{print $1 ": " $2}'

# Extract API keys from grep output (remove filename prefix)
grep -rh 'api_key=' /var/www | cut -d= -f2 | sort -u

# Extract values between quotes
sed -n 's/.*password="\([^"]*\)".*/\1/p' config.php

# Extract IP addresses from logs
grep 'Failed password' /var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn

# Parse JSON-like output (basic)
grep -o '"password":"[^"]*"' config.json | cut -d'"' -f4
```

### Output Interpretation

1. Extracted fields only; ready for further processing or reporting
2. Use `sort -u` to deduplicate, `sort | uniq -c` to count occurrences

### OPSEC and Detection Notes

**ZERO IMPACT**: awk/sed/cut operate on stdin/files; no network or unusual syscalls

### Common Errors

1. Wrong field number — Count fields carefully; awk is 1-indexed
2. Delimiter not matched — Verify with `head` first; ensure delimiter present
3. sed regex not matching — Test pattern with simpler examples; escape special chars

### Version and Platform Notes

1. POSIX-compliant awk/sed/cut work on all Linux/Unix
2. [GNU awk (gawk)](https://www.gnu.org/software/gawk/) supports advanced features (multi-char separators, arrays)

---

## OPSEC and Detection Awareness

**Purpose:** Understand what defensive tools log when searching for credentials

**Prerequisites:** Awareness of target environment (auditd, EDR, SIEM presence)

### Core Detection Mechanisms

1. **[auditd](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/security_guide/chap-system_auditing)** — File access monitoring; logs to `/var/log/audit/audit.log`
2. **EDR agents** — Behavioral detection; anomaly scoring for file enumeration patterns
3. **syslog** — General system logging; may capture bash history or command execution
4. **Process accounting (psacct)** — Logs executed commands

### Key Indicators of Compromise (IOCs) Generated

1. Recursive grep from `/` — High I/O load, CPU spike, massive file read count
2. Access to `/etc/shadow`, `/etc/passwd`, `~/.ssh/id_rsa` — High-priority alerts
3. Rapid sequential file reads across multiple directories — Anomaly detection trigger
4. Large result sets piped to output files — Unusual data exfiltration patterns

### Detection Check Commands

```bash
# Check if auditd is running
systemctl status auditd
ps aux | grep auditd

# Check existing audit watches (requires root)
auditctl -l

# Search audit logs for your own activity (requires root)
ausearch --file /etc/shadow --interpret
ausearch -k password-access -ts recent

# Check for file watches on sensitive files
auditctl -l | grep -E 'shadow|passwd|ssh'

# Generate audit summary report (requires root)
aureport -f | tail -50
aureport -u | tail -20

# Check if EDR/monitoring agent present
ps aux | grep -iE 'falcon|crowdstrike|carbon|defender|sentinel|tanium'

# Check SELinux status (may block file access)
sestatus
ls -Z /etc/shadow
```

### Output Interpretation

1. auditd file watches indicate monitored paths
2. EDR processes indicate behavioral monitoring active
3. SELinux enforcing mode may silently block reads

### OPSEC Recommendations

1. **Target scope aggressively**: Search `/var/www`, `/opt`, specific user homes instead of `/`
2. **Exclude system directories**: Use `--exclude-dir={proc,sys,dev,run,usr/share}` with grep
3. **Small result sets**: Use `-l` (filenames only) until target narrowed
4. **Blend with normal activity**: Sysadmins search logs frequently; timing and context matter
5. **Avoid high-value files initially**: Test with lower-risk directories first
6. **Throttle I/O**: Add `sleep` between operations or use `nice`/`ionice` to reduce resource impact

### Common Detection Artifacts

1. **`/var/log/audit/audit.log`** — File access records: `type=PATH msg=audit(...): item=0 name="/etc/shadow"`
2. **Bash history** — Commands logged to `~/.bash_history` (disable: `unset HISTFILE`)
3. **Process command line** — Visible in `ps auxww` output while running
4. **Network anomaly** — Large internal file reads may correlate with exfil attempts

### Mitigation Against Detection

1. **Disable history temporarily**: `unset HISTFILE` or `set +o history`
2. **Clear history**: `history -c; rm ~/.bash_history` (obvious indicator if monitored)
3. **Use absolute paths**: Avoid relative paths that expose working directory context
4. **Redirect output carefully**: Large output files in `/tmp` or home directory may trigger alerts

### Version and Platform Notes

1. auditd standard on RHEL/CentOS/Fedora; may not be enabled by default on Debian/Ubuntu
2. systemd `journalctl` also logs command execution on systemd-based systems

---

## References

1. [GNU grep Manual](https://www.gnu.org/software/grep/manual/grep.html)
2. [grep Man Page - Linux.die.net](https://linux.die.net/man/1/grep)
3. [locate Man Page](https://man7.org/linux/man-pages/man1/locate.1.html)
4. [find Man Page](https://linux.die.net/man/1/find)
5. [Linux Privilege Escalation Using Misconfigured File Permissions - Hacking Articles](https://www.hackingarticles.in/linux-privilege-escalation-using-misconfigured-file-permissions/)
6. [xargs Man Page](https://man7.org/linux/man-pages/man1/xargs.1.html)
7. [Linux find Command - Red Hat Sysadmin](https://www.redhat.com/sysadmin/linux-find-command)
8. [Linux /proc Filesystem Documentation](https://www.kernel.org/doc/Documentation/filesystems/proc.txt)
9. [ps Man Page](https://linux.die.net/man/1/ps)
10. [Linux Log Files Location and Viewing Guide - nixCraft](https://www.cyberciti.biz/faq/linux-log-files-location-and-how-do-i-view-logs-files/)
11. [journalctl Man Page](https://man7.org/linux/man-pages/man1/journalctl.1.html)
12. [GNU find Manual](https://www.gnu.org/software/findutils/manual/html_mono/find.html)
13. [strings Man Page](https://man7.org/linux/man-pages/man1/strings.1.html)
14. [awk Man Page](https://man7.org/linux/man-pages/man1/awk.1p.html)
15. [GNU sed Manual](https://www.gnu.org/software/sed/manual/sed.html)
16. [Understanding Audit Log Files - Red Hat](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/security_guide/sec-understanding_audit_log_files)
17. [Configuring and Auditing Linux Systems with auditd](https://linux-audit.com/configuring-and-auditing-linux-systems-with-auditd/)

#Linux #PrivEsc #Enumeration #Credentials #grep #find #OPSEC #Logs #FileEnumeration #PasswordHunting
