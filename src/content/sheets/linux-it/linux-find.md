---
title: "Linux find Command"
description: "find recipes: by name/type/time/perm/size, SUID hunting, exec actions and pruning noisy paths."
category: linux-it
tags: [linux, cli, search]
tools: [find]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:Linux/Find Command.md"
---

# Linux find Command

## Overview

`find` recursively searches directory trees for files and directories matching specified criteria (name, type, size, time, permissions, ownership) and optionally executes actions on results. Part of GNU findutils, it's essential for system enumeration, privilege escalation reconnaissance, and incident response.

**Key capabilities:**
1. Pattern-based file and directory matching
2. Time-based searches (modification, access, inode change)
3. Permission-based filtering (SUID/SGID, world-writable)
4. Command execution on matched files via `-exec` or pipe to `xargs`
5. Minimal overhead with powerful filtering capabilities

> **Prerequisites**
> 1. GNU findutils installed (standard on all major Linux distributions).
> 2. Read permission on target directories; root/sudo required for full system scans.
> 3. Current stable version: GNU findutils 4.10.0 (4.9.x widely deployed).
> 4. Understand Linux permission octal notation: SUID=4000, SGID=2000, world-writable=0002.
> 5. Timestamps depend on filesystem and mount options (`noatime`, `relatime`).

---

## General File Search

### Basic Syntax

```bash
find [starting-point...] [expression]
```

- **starting-point**: Directory path(s) to begin search (default: current directory)
- **expression**: Combination of tests, actions, and operators (evaluated left-to-right with implicit AND)

### Search Criteria Options

| Flag | Description | Example |
|:---|:---|:---|
| `-name "pattern"` | Match filename (case-sensitive, wildcards `*`, `?`) | `find . -name "*.conf"` |
| `-iname "pattern"` | Case-insensitive `-name` | `find . -iname "*.PHP"` |
| `-type f/d/l/s/p` | File type: `f`=file, `d`=dir, `l`=symlink, `s`=socket, `p`=named pipe | `find / -type f` |
| `-size [+/-]n[cwbkMG]` | File size; `+`=greater, `-`=less; units `c`/`k`/`M`/`G` | `find / -size +100M` |
| `-user / -group` | Owner / group name or UID/GID | `find /home -user john` |
| `-perm mode` | Exact permissions match | `find . -perm 0644` |
| `-perm -mode` | All permission bits set | `find / -perm -4000` |
| `-perm /mode` | Any permission bit set | `find / -perm /6000` |
| `-maxdepth n` | Limit traversal depth | `find /etc -maxdepth 2` |
| `-mindepth n` | Start traversal at depth n | `find / -mindepth 2` |
| `-xdev` | Stay on same filesystem (do not descend into other mounts) | `find / -xdev` |
| `-empty` | Empty files or directories | `find /tmp -empty` |

### Output Control Options

| Flag | Description | Use Case |
|:---|:---|:---|
| `-print` | Print full path (default) | Standard output |
| `-print0` | Null-delimit output | Safe piping to `xargs -0` |
| `-printf "format"` | Custom output format | `%M` mode, `%u` user, `%T+` timestamp |
| `-ls` | Long listing format | Permissions, owner, size, date |

### Basic Search Examples

```bash
# Find files by name (case-insensitive)
find /home -iname "*.conf" -type f

# Find files larger than 100MB
find / -type f -size +100M 2>/dev/null

# Find files modified between two dates
find /data -newermt "2025-12-01" ! -newermt "2026-01-01"

# Find and delete empty directories
find /tmp -type d -empty -delete
```

> **Warning —** `-delete` is immediate and irreversible. Test with `-print` before using `-delete` to verify targets. `-delete` implies `-depth` traversal.

---

## SUID/SGID and World-Writable File Discovery

Files with SUID/SGID bits or world-writable permissions are high-value targets for privilege escalation:

1. **SUID (Set User ID)**: Executes with file owner's privileges (typically root)
2. **SGID (Set Group ID)**: Executes with file group's privileges
3. **World-writable**: Any user can modify the file
4. Cross-reference SUID binaries with GTFOBins (https://gtfobins.github.io/) for exploitation paths
5. World-writable config files in `/etc` are critical escalation vectors

### SUID/SGID Discovery Commands

```bash
# Find SUID files (at least the SUID bit set)
find / -type f -perm -4000 2>/dev/null

# Find SGID files
find / -type f -perm -2000 2>/dev/null

# Find SUID or SGID files
find / -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null

# SUID binaries owned by root (common priv-esc targets)
find / -type f -perm -4000 -user root 2>/dev/null

# SUID/SGID with detailed output
find / -type f \( -perm -4000 -o -perm -2000 \) -exec ls -la {} \; 2>/dev/null
```

> **Note —** The `-` prefix on `-perm` means "at least these bits" — the file may have additional permissions. Common legitimate SUID binaries: `/usr/bin/passwd`, `/usr/bin/sudo`, `/bin/ping`. Compare output against a baseline for anomaly detection.

### World-Writable Discovery Commands

```bash
# Find world-writable files
find / -type f -perm -0002 2>/dev/null

# Find world-writable directories (sticky bit often expected)
find / -type d -perm -0002 2>/dev/null

# World-writable files excluding /proc and /sys
find / -path /proc -prune -o -path /sys -prune -o -type f -perm -0002 -print 2>/dev/null

# World-writable directories without sticky bit (dangerous)
find / -type d \( -perm -0002 -a ! -perm -1000 \) 2>/dev/null
```

> **Danger —** A world-writable directory without the sticky bit (octal 1000) allows any user to delete any file. Writable files owned by root, and writable configs sourced by privileged processes, are the highest priority. World-writable dirs like `/tmp` normally carry the sticky bit.

> **OPSEC considerations**
> 1. Full system scans generate high I/O and may trigger file-integrity monitoring (AIDE, OSSEC).
> 2. Redirect stderr (`2>/dev/null`) to avoid permission-denied noise.
> 3. Use `-maxdepth` to limit scope and reduce detection surface.
> 4. Combine with `-xdev` to avoid traversing network mounts.

---

## Command Execution with `-exec` and `xargs`

Three primary methods for executing commands on found files:

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
| `xargs -P N` | Parallel execution | Fastest | CPU-bound operations | Medium (concurrent processes) |

### `-exec` Examples

```bash
# -exec with \; (one command per file – slower)
find . -type f -name "*.log" -exec rm {} \;

# -exec with + (batched arguments – faster)
find . -type f -name "*.log" -exec rm {} +

# Grep for pattern in PHP files (batched) – potential webshell indicator
find /var/www -type f -name "*.php" -exec grep -l "eval(" {} +

# Change ownership in batches
find /data -type f -exec chown appuser:appgroup {} +
```

### `xargs` Examples

```bash
# Pipe to xargs (batched, handles large sets)
find . -type f -name "*.log" -print0 | xargs -0 rm

# xargs with parallelism (up to 4 concurrent processes)
find . -type f -name "*.log" -print0 | xargs -0 -P 4 rm

# Safe delete with confirmation (interactive)
find . -name "*.tmp" -print0 | xargs -0 -p rm

# Compress logs older than 30 days (parallel)
find /var/log -type f -mtime +30 -name "*.log" -print0 | xargs -0 -P 4 gzip
```

> **Note —** The `-print0 | xargs -0` pairing is critical for safe handling of filenames with spaces, newlines, or special characters.

### Additional `xargs` Options

| Flag | Description | Example Use |
|:---|:---|:---|
| `-n N` | Max N arguments per invocation | `xargs -n 1` processes one file at a time |
| `-r` | Don't run if input is empty | Prevents errors when find returns nothing |
| `-I {}` | Replace string placeholder | `xargs -I {} mv {} /backup/` |
| `-t` | Print command before executing | Debugging and logging |
| `--show-limits` | Display ARG_MAX and buffer sizes | System capability check |

> **Common errors**
> 1. Missing `-0` with xargs when filenames contain spaces — always use the `-print0 | xargs -0` pairing.
> 2. Forgetting `\;` or `+` at the end of `-exec` — required terminator.
> 3. Using `-delete` before other predicates — evaluation order matters; `-delete` implies `-depth`.
> 4. Forgetting `-r` with xargs when find returns nothing.

---

## Time-Based File Searches

`find` supports three timestamp types for file matching:

1. **mtime**: File modification time (content changed)
2. **atime**: File access time (content read)
3. **ctime**: Inode change time (metadata changed — permissions, ownership, name)
4. Each has day-based (`-mtime`) and minute-based (`-mmin`) variants.

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
# Files modified in the last 24 hours (rolling window from now)
find /var/log -type f -mtime 0

# Files modified more than 30 days ago
find /tmp -type f -mtime +30

# Files modified in the last 60 minutes
find /home -type f -mmin -60

# Files modified yesterday (calendar day, using -daystart)
find /data -daystart -mtime 1 -type f

# Files modified between two dates
find /logs -newermt "2025-12-01" ! -newermt "2025-12-31"

# Files modified more recently than a reference file
find /app -newer /app/deploy.timestamp
```

> **Note —** `-mtime 0` is a rolling 24-hour window, not "today". For calendar-day semantics use `-daystart -mtime 0`, and `-daystart` must appear before `-mtime` in the expression. Variants: `-anewer` (atime), `-cnewer` (ctime).

### Advanced Time-Based Queries

```bash
# Files modified today (calendar day) with ISO timestamp output
find /var/log -type f -daystart -mtime 0 -printf "%T+ %p\n"

# Files NOT accessed in the last 90 days (candidates for archival)
find /archive -type f -atime +90 -ls
```

> **Forensic considerations**
> 1. Recursive `find` on atime can update atime and modify the evidence you're searching.
> 2. `noatime` / `relatime` mounts make atime stale — verify with `mount | grep atime`.
> 3. Timestomping: adversaries modify timestamps, so mtime/atime are less reliable.
> 4. ctime cannot be modified by standard tools — more forensically reliable than mtime/atime.

> **Performance tips**
> 1. Combine time predicates with `-type` early in the expression for faster evaluation.
> 2. Use `-maxdepth` to limit search scope.
> 3. Redirect stderr (`2>/dev/null`) to avoid permission-denied overhead.
> 4. Use `-xdev` to avoid crossing mount points and network filesystems.

---

## References

1. GNU findutils Manual — https://www.gnu.org/software/findutils/manual/html_mono/find.html
2. Linux find Man Page — https://man7.org/linux/man-pages/man1/find.1.html
3. GTFOBins — https://gtfobins.github.io/
4. MITRE ATT&CK: File and Directory Discovery (T1083)
5. HackTricks: Linux Privilege Escalation
