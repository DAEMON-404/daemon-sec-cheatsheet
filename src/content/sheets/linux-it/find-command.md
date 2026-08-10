---
title: "Find Command"
description: "find /home -iname \"*.conf\" -type f"
category: linux-it
tags: ["linux-it", "privilege-escalation"]
tools: []
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Linux/Find Command.md"
---
# Find files by name (case-insensitive)
find /home -iname "*.conf" -type f
```

> [!info]+ Command Breakdown
> 1. **-iname "*.conf"**: Case-insensitive pattern matching for files ending in `.conf`
> 2. **-type f**: Restricts results to regular files only
> 3. *Wildcard `*` matches any characters before `.conf` extension*
> 4. *Useful for locating configuration files across user directories*

```bash
# Find files larger than 100MB
find / -type f -size +100M 2>/dev/null
```

> [!info]+ Command Breakdown
> 1. **-size +100M**: Files greater than 100 megabytes
> 2. **2>/dev/null**: Redirects permission-denied errors to avoid output clutter
> 3. *Starting from root `/` requires elevated privileges for complete results*
> 4. *Useful for identifying large files consuming disk space or potential data exfiltration*

```bash
# Find files modified between two dates
find /data -newermt "2025-12-01" ! -newermt "2026-01-01"
```

> [!info]+ Command Breakdown
> 1. **-newermt "2025-12-01"**: Files modified after (newer than) December 1, 2025
> 2. **! -newermt "2026-01-01"**: `!` negates the test; files NOT newer than January 1, 2026
> 3. *Logical combination creates a date range: December 1-31, 2025*
> 4. *Critical for [incident response](https://www.sans.org/white-papers/33901/) timeline analysis*

```bash
# Find and delete empty directories
find /tmp -type d -empty -delete
```

> [!warning]+ Command Breakdown
> 1. **-type d**: Targets directories only
> 2. **-empty**: Matches directories with no contents
> 3. **-delete**: Deletes matched items (implies `-depth` traversal)
> 4. *Use with extreme caution—deletion is immediate and irreversible*
> 5. *Test with `-print` before using `-delete` to verify targets*

---

## SUID/SGID and World-Writable File Discovery

Files with [SUID/SGID](https://www.redhat.com/sysadmin/suid-sgid-sticky-bit) bits or world-writable permissions are high-value targets for privilege escalation:

1. **SUID (Set User ID)**: Executes with file owner's privileges (typically root)
2. **SGID (Set Group ID)**: Executes with file group's privileges
3. **World-writable**: Any user can modify the file
4. Cross-reference SUID binaries with [GTFOBins](https://gtfobins.github.io/) for exploitation paths
5. World-writable config files in `/etc` are critical escalation vectors

### SUID/SGID Discovery Commands

```bash
# Find SUID files
find / -type f -perm -4000 2>/dev/null
```

> [!info]+ Command Breakdown
> 1. **-perm -4000**: Files with at least the SUID bit (octal 4000) set
> 2. **-type f**: Restricts to regular files (not directories)
> 3. *The `-` prefix means "at least these permission bits"—file may have additional permissions*
> 4. *Common legitimate SUID binaries: `/usr/bin/passwd`, `/usr/bin/sudo`, `/bin/ping`*

```bash
# Find SGID files
find / -type f -perm -2000 2>/dev/null
```

**SGID characteristics:**
1. SGID on executables runs with group privileges
2. SGID on directories causes new files to inherit directory's group
3. Less common for privilege escalation than SUID but still valuable
4. Check output against system baseline for anomalies

```bash
# Find SUID or SGID files
find / -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null
```

> [!info]+ Command Breakdown
> 1. **\( ... \)**: Parentheses create logical grouping (escaped for shell)
> 2. **-o**: Logical OR operator—matches either condition
> 3. *Comprehensive search for all elevated permission binaries*
> 4. *Output should be compared against baseline for anomaly detection*

### World-Writable Discovery Commands

```bash
# Find world-writable files
find / -type f -perm -0002 2>/dev/null
```

**Security implications:**
1. Extremely dangerous if file is executed or sourced by privileged processes
2. Check ownership—writable files owned by root are highest priority
3. Common in web directories due to misconfigurations
4. Potential for code injection or configuration tampering

```bash
# Find world-writable directories (sticky bit often expected)
find / -type d -perm -0002 2>/dev/null
```

**Expected vs. dangerous:**
1. World-writable directories like `/tmp` typically have sticky bit (1000) set
2. Sticky bit prevents users from deleting others' files
3. Missing sticky bit on writable directory is a misconfiguration
4. Check `/var/www`, `/var/tmp`, `/dev/shm` for anomalies

### Advanced Privilege Escalation Enumeration

```bash
# SUID binaries owned by root (common priv-esc targets)
find / -type f -perm -4000 -user root 2>/dev/null
```

**Analysis approach:**
1. Root-owned SUID binaries execute with root privileges
2. Focus on non-standard binaries not in `/usr/bin` or `/bin`
3. Test discovered binaries against [GTFOBins](https://gtfobins.github.io/) for known exploits
4. Document custom SUID binaries for deeper analysis

```bash
# SUID/SGID with detailed output
find / -type f \( -perm -4000 -o -perm -2000 \) -exec ls -la {} \; 2>/dev/null
```

> [!info]+ Command Breakdown
> 1. **-exec ls -la {} \;**: Executes `ls -la` on each matched file
> 2. **{}**: Placeholder replaced with found filename
> 3. **\;**: Required terminator for `-exec` (escaped for shell)
> 4. *Provides full permission string, owner, group, size, and modification date*

```bash
# World-writable files excluding /proc and /sys
find / -path /proc -prune -o -path /sys -prune -o -type f -perm -0002 -print 2>/dev/null
```

> [!info]+ Command Breakdown
> 1. **-path /proc -prune**: Excludes `/proc` directory from traversal
> 2. **-o**: OR operator—chains pruning and search logic
> 3. **-prune**: Prevents descending into matched directory
> 4. *`/proc` and `/sys` are pseudo-filesystems with world-writable entries by design*
> 5. *Excluding them reduces noise and improves performance*

```bash
# World-writable directories without sticky bit (dangerous)
find / -type d \( -perm -0002 -a ! -perm -1000 \) 2>/dev/null
```

> [!danger]+ Command Breakdown
> 1. **-a**: Logical AND operator—both conditions must be true
> 2. **! -perm -1000**: Negates sticky bit check (octal 1000)
> 3. *World-writable directory without sticky bit allows any user to delete any file*
> 4. *Severe misconfiguration—often found in poorly configured web directories*

**OPSEC considerations:**
1. Full system scans generate high I/O and may trigger file integrity monitoring ([AIDE](https://aide.github.io/), [OSSEC](https://www.ossec.net/))
2. Redirect stderr (`2>/dev/null`) to avoid logging permission-denied paths in shell history
3. Consider running during high-activity periods to blend with baseline noise
4. Use `-maxdepth` to limit scope and reduce detection surface
5. Combine with `-xdev` to avoid traversing network mounts (reduces latency and external logs)

---

## Command Execution with `-exec` and `xargs`

Three primary methods exist for executing commands on found files, each with distinct performance and safety characteristics:

1. **-exec cmd {} \;**: Forks command once per file (slower, more visible)
2. **-exec cmd {} +**: Batches files into single command invocation (faster, less visible)
3. **find | xargs**: Batches via pipe, respects ARG_MAX, supports parallelism

### Execution Method Comparison

| Method | Behaviour | Performance | Use Case | OPSEC Impact |
|:---|:---|:---|:---|:---|
| `-exec cmd {} \;` | Forks cmd once per file | Slow | Small sets, complex per-file logic | High (many processes) |
| `-exec cmd {} +` | Batches files into one cmd | Fast | Large sets, simple commands | Low (few processes) |
| `find \| xargs` | Batches via pipe | Fast | Very large sets, custom batching | Low (few processes) |
| `find -print0 \| xargs -0` | Null-delimited batching | Fast | Filenames with spaces/newlines | Low (safe handling) |
| `xargs -P N` | Parallel execution | Fastest | CPU-bound operations | Medium (multiple concurrent processes) |

### `-exec` Examples

```bash
# -exec with \; (one command per file – slower)
find . -type f -name "*.log" -exec rm {} \;
```

> [!info]+ Command Breakdown
> 1. **-exec rm {}**: Executes `rm` command with `{}` replaced by filename
> 2. **\;**: Terminator indicating end of command (backslash escapes semicolon from shell)
> 3. *Spawns one `rm` process per file—thousands of files = thousands of processes*
> 4. *High overhead but allows per-file command customization*

```bash
# -exec with + (batched arguments – faster)
find . -type f -name "*.log" -exec rm {} +
```

**Batching behaviour:**
1. Combines multiple filenames into single command invocation
2. Example: `rm file1.log file2.log file3.log` instead of three separate `rm` calls
3. Respects system ARG_MAX limit—automatically splits into multiple batches if needed
4. Preferred method for large-scale operations

```bash
# Grep for pattern in PHP files (batched)
find /var/www -type f -name "*.php" -exec grep -l "eval(" {} +
```

> [!info]+ Command Breakdown
> 1. **grep -l "eval("**: Lists filenames containing the string `eval(` (potential [web shell](https://www.acunetix.com/blog/articles/web-shells-101-using-php-introduction-web-shells-part-2/) indicator)
> 2. **-exec ... +**: Batches PHP files into single `grep` invocation for efficiency
> 3. *Useful for web application security audits and malware hunting*
> 4. *Consider escaping parentheses in grep pattern depending on shell context*

```bash
# Change ownership in batches
find /data -type f -exec chown appuser:appgroup {} +
```

**Performance notes:**
1. Changes file owner to `appuser` and group to `appgroup`
2. Batching significantly reduces execution time on large directory trees
3. Common post-deployment task or privilege management operation
4. Requires appropriate permissions (typically root/sudo)

### `xargs` Examples

```bash
# Pipe to xargs (batched, handles large sets)
find . -type f -name "*.log" -print0 | xargs -0 rm
```

> [!info]+ Command Breakdown
> 1. **-print0**: Outputs null-delimited filenames (handles spaces, newlines, special characters)
> 2. **xargs -0**: Reads null-delimited input from stdin
> 3. *The `-0` pairing is **critical** for safe handling of unusual filenames*
> 4. *[xargs](https://man7.org/linux/man-pages/man1/xargs.1.html) automatically batches arguments respecting ARG_MAX*

```bash
# xargs with parallelism
find . -type f -name "*.log" -print0 | xargs -0 -P 4 rm
```

**Parallelism considerations:**
1. **-P 4**: Runs up to 4 parallel `rm` processes simultaneously
2. Significantly faster for CPU-bound operations (compression, checksumming)
3. Use `-P 1` to force serial execution if parallelism causes detection
4. Monitor system load—excessive parallelism can overwhelm resources

```bash
# Safe delete with confirmation (interactive)
find . -name "*.tmp" -print0 | xargs -0 -p rm
```

**Interactive mode:**
1. **-p**: Prompts user before executing each command
2. Safety mechanism for destructive operations
3. User must type `y` to confirm each deletion
4. Not suitable for automated scripts—use only for manual operations

```bash
# Compress logs older than 30 days (parallel)
find /var/log -type f -mtime +30 -name "*.log" -print0 | xargs -0 -P 4 gzip
```

> [!info]+ Command Breakdown
> 1. **-mtime +30**: Files modified more than 30 days ago
> 2. **gzip**: Compresses each file (replaces original with `.gz` version)
> 3. **-P 4**: Compresses 4 files simultaneously
> 4. *Common log rotation cleanup task*
> 5. *Parallelism ideal for CPU-intensive compression workloads*

### Additional `xargs` Options

| Flag | Description | Example Use |
|:---|:---|:---|
| `-n N` | Max N arguments per invocation | `xargs -n 1` processes one file at a time |
| `-r` | Don't run if input is empty | Prevents errors when find returns nothing |
| `-I {}` | Replace string placeholder | `xargs -I {} mv {} /backup/` |
| `-t` | Print command before executing | Debugging and logging |
| `--show-limits` | Display ARG_MAX and buffer sizes | System capability check |

> [!warning]+ Common Errors
> 1. **Missing `-0` with xargs when filenames contain spaces**: Command breaks or acts on wrong files—always use `-print0 | xargs -0` pairing
> 2. **Forgetting `\;` or `+` at end of `-exec`**: Syntax error—required terminator
> 3. **Using `-delete` before other predicates**: Evaluation order matters; `-delete` implies `-depth` traversal
> 4. **Forgetting `-r` with xargs when find returns nothing**: Unexpected command execution with no arguments
> 5. **Exceeding ARG_MAX with `-exec {} +`**: Rare on modern systems—xargs auto-splits, but find may fail on ancient systems

---

## Time-Based File Searches

[find](https://man7.org/linux/man-pages/man1/find.1.html) supports three timestamp types for file matching:

1. **mtime**: File modification time (content changed)
2. **atime**: File access time (content read)
3. **ctime**: Inode change time (metadata changed—permissions, ownership, name)
4. Each has day-based (`-mtime`) and minute-based (`-mmin`) variants
5. Critical for [incident response](https://www.sans.org/white-papers/33901/), forensic analysis, and log management

### Time Predicate Syntax

| Predicate | Meaning | Measurement Unit |
|:---|:---|:---|
| `-mtime n` | Modified exactly n days ago | 24-hour periods |
| `-mtime +n` | Modified more than n days ago | 24-hour periods |
| `-mtime -n` | Modified within last n days | 24-hour periods |
| `-atime n/+n/-n` | Access time variants | 24-hour periods |
| `-ctime n/+n/-n` | Inode change time variants | 24-hour periods |
| `-mmin n/+n/-n` | Modification time | Minutes |
| `-amin n/+n/-n` | Access time | Minutes |
| `-cmin n/+n/-n` | Inode change time | Minutes |
| `-newermt "date"` | Modified after specified date | ISO 8601 format |
| `-newer reference` | Modified more recently than file | File comparison |
| `-daystart` | Measure from start of today | Changes reference point |

### Time-Based Search Examples

```bash
# Files modified in the last 24 hours
find /var/log -type f -mtime 0
```

**Interpretation:**
1. **-mtime 0**: Files modified between now and 24 hours ago
2. `0` represents the current 24-hour period from now
3. Useful for identifying recently changed logs during incident investigation
4. Does not mean "modified today"—use `-daystart -mtime 0` for that

```bash
# Files modified more than 30 days ago
find /tmp -type f -mtime +30
```

**Interpretation:**
1. **-mtime +30**: Files with modification time older than 30 days
2. **+** prefix means "more than"—excludes files at exactly 30 days
3. Common cleanup pattern for temporary directories
4. Combine with `-delete` or `-exec rm` for automated maintenance

```bash
# Files modified in the last 60 minutes
find /home -type f -mmin -60
```

**Interpretation:**
1. **-mmin -60**: Files modified within the last 60 minutes
2. **-** prefix means "less than"—within the specified timeframe
3. Higher resolution than day-based predicates
4. Essential for real-time security monitoring and breach detection

```bash
# Files modified yesterday (using -daystart)
find /data -daystart -mtime 1 -type f
```

> [!info]+ Command Breakdown
> 1. **-daystart**: Changes reference point to midnight today (00:00) instead of current time
> 2. **-mtime 1**: Exactly 1 day ago from reference point
> 3. *Without `-daystart`, `1` means "24-48 hours ago from now"*
> 4. *Order matters: `-daystart` must appear **before** `-mtime` in expression*

```bash
# Files modified between two dates
find /logs -newermt "2025-12-01" ! -newermt "2025-12-31"
```

> [!info]+ Command Breakdown
> 1. **-newermt "2025-12-01"**: Modified after (newer than) December 1, 2025 00:00:00
> 2. **! -newermt "2025-12-31"**: `!` negates—NOT newer than December 31, 2025 00:00:00
> 3. *Creates inclusive date range: December 1-30, 2025*
> 4. *Requires quotes around dates; supports ISO 8601 format with time: `"2025-12-01 14:30:00"`*

```bash
# Files accessed more recently than a reference file
find /app -newer /app/deploy.timestamp
```

**Use cases:**
1. **-newer /app/deploy.timestamp**: Files modified more recently than reference file's mtime
2. Useful for identifying files changed since last deployment
3. Create timestamp files with `touch` to mark events
4. Variant: `-anewer` for atime comparison, `-cnewer` for ctime

### Advanced Time-Based Queries

```bash
# Files modified today (calendar day, not 24 hours)
find /var/log -type f -daystart -mtime 0 -printf "%T+ %p\n"
```

> [!info]+ Command Breakdown
> 1. **-daystart -mtime 0**: Files modified since midnight today
> 2. **-printf "%T+ %p\n"**: Custom format—`%T+` is ISO timestamp, `%p` is path
> 3. *Output format: `2026-01-18+09:30:15.0000000000 /var/log/auth.log`*
> 4. *Pipe to `sort` for chronological ordering*

```bash
# Files NOT accessed in the last 90 days (candidates for archival)
find /archive -type f -atime +90 -ls
```

**Archival workflow:**
1. **-atime +90**: Access time older than 90 days
2. **-ls**: Long listing output with timestamps
3. Identifies stale files for archival or deletion
4. Warning: atime may be unreliable on filesystems with `noatime` or `relatime` mount options

**OPSEC and forensic considerations:**
1. **Access time queries may update atime on some filesystems**: Recursive find can modify the evidence you're searching for
2. **`noatime` or `relatime` mount options**: Access time may be stale or not updated—verify mount options with `mount | grep atime`
3. **Timestomping**: Adversaries can modify file timestamps—time-based queries less reliable if attacker has touched files
4. **Timezone considerations**: Timestamps in UTC vs local time—use `%T+` printf format for ISO 8601 with timezone
5. **Inode change time (ctime) cannot be modified by standard tools**: More forensically reliable than mtime/atime

> [!tip]+ Performance Optimization
> 1. Combine time predicates with `-type` early in expression for faster evaluation
> 2. Use `-maxdepth` to limit search scope when possible
> 3. Redirect stderr (`2>/dev/null`) to avoid permission-denied overhead
> 4. Consider `locate` database for name-based searches if time constraints allow
> 5. Use `-xdev` to avoid crossing mount points and network filesystems

---

## References

1. [GNU findutils Manual](https://www.gnu.org/software/findutils/manual/html_mono/find.html)
2. [Linux find Man Page](https://man7.org/linux/man-pages/man1/find.1.html)
3. [Red Hat: Linux find Command](https://www.redhat.com/en/blog/linux-find-command)
4. [Cyberciti: Finding Files by Date](https://www.cyberciti.biz/faq/howto-finding-files-by-date/)
5. [Red Hat: Audit Permissions with find](https://www.redhat.com/en/blog/audit-permissions-find)
6. [Baeldung: Find Modified Date](https://www.baeldung.com/linux/find-modified-date)
7. [Endpoint Dev: Efficiency of find -exec vs xargs](https://www.endpointdev.com/blog/2010/07/efficiency-of-find-exec-vs-find-xargs/)
8. [CaveOps: find -exec vs find | xargs](https://caveops.com/blog/post/name/find-exec-vs-find-xargs/)
9. [GTFOBins](https://gtfobins.github.io/)
10. [MITRE ATT&CK: File and Directory Discovery](https://attack.mitre.org/techniques/T1083/)
11. [HackTricks: Linux Privilege Escalation](https://book.hacktricks.xyz/linux-hardening/privilege-escalation)
12. [SANS: Incident Response Process](https://www.sans.org/white-papers/33901/)

---

#Linux #FileSystemEnumeration #find #xargs #SUID #SGID #PrivilegeEscalation #IncidentResponse #Forensics #SystemAdministration #PenetrationTesting #Reconnaissance #GTFOBins
