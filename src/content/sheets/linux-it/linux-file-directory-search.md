---
title: "Linux File & Directory Search"
description: "A comprehensive guide to find, grep, fd, and rg (ripgrep) for locating files and searching content."
category: linux-it
tags: ["linux-it"]
tools: ["PowerShell"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Linux/Linux File & Directory Search Cheat Sheet.md"
---
# Linux File & Directory Search Cheat Sheet

A comprehensive guide to `find`, `grep`, `fd`, and `rg` (ripgrep) for locating files and searching content.

---

## Table of Contents
1. [find - Classic File Search](#find)
2. [grep - Content Search](#grep)
3. [fd - Modern find Alternative](#fd)
4. [rg (ripgrep) - Modern grep Alternative](#rg)
5. [Combined Patterns & Workflows](#combined)
6. [Windows findstr Equivalents](#windows-equivalents)

---

## <a name="find"></a>1. `find` - Classic File Search

### Basic Syntax
```bash
find [path] [options] [expression]
```

### Finding Files by Name
```bash
# Find by exact name
find /path -name "filename.txt"

# Case-insensitive search
find /path -iname "filename.txt"

# Wildcards (must be quoted)
find . -name "*.ps1"
find . -name "*.log"
find . -name "Password_File*"

# Multiple patterns (OR logic)
find . -name "*.ps1" -o -name "*.sh" -o -name "*.py"

# Regex matching (full path)
find . -regex ".*\(\.ps1\|\.sh\)$"

# Extended regex
find . -regextype posix-extended -regex ".*(POWERSHELL_SCRIPT|Password_File|.*\.ps1)"
```

### Finding by Type

```bash
# Files only
find . -type f

# Directories only
find . -type d

# Symbolic links
find . -type l

# Empty files
find . -type f -empty

# Empty directories
find . -type d -empty
```

### Finding by Size

```bash
# Exactly 50MB
find . -size 50M

# Greater than 100MB
find . -size +100M

# Less than 1KB
find . -size -1k

# Between 1MB and 100MB
find . -size +1M -size -100M

# Size units: c(bytes), k(KB), M(MB), G(GB)
```

### Finding by Time

```bash
# Modified in last 7 days
find . -mtime -7

# Modified more than 30 days ago
find . -mtime +30

# Modified exactly 1 day ago
find . -mtime 1

# Accessed in last 60 minutes
find . -amin -60

# Changed in last 24 hours (metadata)
find . -ctime -1

# Modified after a reference file
find . -newer reference_file.txt

# Modified between two dates
find . -newermt "2024-01-01" ! -newermt "2024-12-31"
```

### Finding by Permissions & Ownership

```bash
# Exact permissions
find . -perm 644
find . -perm 755

# At least these permissions (all bits set)
find . -perm -644

# Any of these permissions (any bit set)
find . -perm /644

# World-writable files (security audit)
find . -perm -o=w -type f

# SUID/SGID files
find . -perm /4000    # SUID
find . -perm /2000    # SGID
find . -perm /6000    # Either

# By owner
find . -user username
find . -group groupname

# Files without owner (orphaned)
find . -nouser
find . -nogroup
```

### Depth Control

```bash
# Maximum depth (don't go deeper than 2 levels)
find . -maxdepth 2 -name "*.txt"

# Minimum depth (skip current directory)
find . -mindepth 1 -name "*.txt"

# Exact depth (only level 3)
find . -mindepth 3 -maxdepth 3 -name "*.txt"
```

### Excluding Paths

```bash
# Exclude a directory
find . -path "./node_modules" -prune -o -name "*.js" -print

# Exclude multiple directories
find . \( -path "./node_modules" -o -path "./.git" \) -prune -o -name "*.js" -print

# Using -not
find . -not -path "*/\.git/*" -name "*.py"
```

### Actions

```bash
# Delete found files (DANGEROUS - test with -print first!)
find . -name "*.tmp" -delete

# Execute command on each file
find . -name "*.txt" -exec cat {} \;

# Execute with confirmation
find . -name "*.log" -ok rm {} \;

# More efficient execution (batched)
find . -name "*.txt" -exec cat {} +

# Print with null separator (for xargs)
find . -name "*.txt" -print0 | xargs -0 cat

# Custom output format
find . -name "*.txt" -printf "%p %s %T+\n"
# %p=path, %s=size, %T+=modification time
```

### Complex Expressions

```bash
# AND (implicit)
find . -name "*.txt" -size +1M

# AND (explicit)
find . -name "*.txt" -a -size +1M

# OR
find . -name "*.txt" -o -name "*.md"

# NOT
find . ! -name "*.txt"
find . -not -name "*.txt"

# Grouping with parentheses
find . \( -name "*.txt" -o -name "*.md" \) -mtime -7
```

---

## <a name="grep"></a>2. `grep` - Content Search

### Basic Syntax
```bash
grep [options] pattern [file...]
```

### Basic Pattern Matching

```bash
# Simple string search
grep "password" file.txt

# Search in multiple files
grep "password" *.txt

# Recursive search in directory
grep -r "password" /path/to/dir

# Case-insensitive
grep -i "password" file.txt

# Whole word only
grep -w "password" file.txt

# Fixed string (no regex interpretation)
grep -F "exact.string" file.txt
```

### Regular Expressions

```bash
# Extended regex
grep -E "POWERSHELL_SCRIPT|Password_File|.*\.ps1" .

# Perl-compatible regex (PCRE)
grep -P "password\d{3}" file.txt

# Match beginning of line
grep "^start" file.txt

# Match end of line
grep "end$" file.txt

# Match any character
grep "p.ssword" file.txt

# Character class
grep "[Pp]assword" file.txt

# Negated character class
grep "[^0-9]" file.txt

# Quantifiers
grep -E "ab+" file.txt      # One or more
grep -E "ab*" file.txt      # Zero or more
grep -E "ab?" file.txt      # Zero or one
grep -E "a{3}" file.txt     # Exactly 3
grep -E "a{2,5}" file.txt   # 2 to 5 times
```

### Output Control

```bash
# Show line numbers
grep -n "pattern" file.txt

# Show only matching part
grep -o "pattern" file.txt

# Count matches
grep -c "pattern" file.txt

# Show filename only
grep -l "pattern" *.txt

# Show files without matches
grep -L "pattern" *.txt

# Show context (before/after/both)
grep -B 3 "pattern" file.txt  # 3 lines before
grep -A 3 "pattern" file.txt  # 3 lines after
grep -C 3 "pattern" file.txt  # 3 lines both sides

# Suppress errors
grep -s "pattern" file.txt

# Quiet mode (exit code only)
grep -q "pattern" file.txt && echo "Found"
```

### Recursive & File Filtering

```bash
# Recursive search
grep -r "pattern" /path

# Recursive following symlinks
grep -R "pattern" /path

# Include only certain files
grep -r --include="*.py" "pattern" .

# Exclude files
grep -r --exclude="*.log" "pattern" .

# Exclude directories
grep -r --exclude-dir=".git" "pattern" .
grep -r --exclude-dir={.git,node_modules,vendor} "pattern" .
```

### Inverting & Combining

```bash
# Invert match (lines NOT matching)
grep -v "pattern" file.txt

# Multiple patterns (OR)
grep -E "pattern1|pattern2" file.txt
grep -e "pattern1" -e "pattern2" file.txt

# Multiple patterns from file
grep -f patterns.txt file.txt

# AND logic (all patterns must match)
grep "pattern1" file.txt | grep "pattern2"
grep -P "(?=.*pattern1)(?=.*pattern2)" file.txt
```

### Binary & Special Files

```bash
# Treat binary as text
grep -a "pattern" binary_file

# Skip binary files
grep -I "pattern" *

# Search compressed files
zgrep "pattern" file.gz
bzgrep "pattern" file.bz2
xzgrep "pattern" file.xz
```

---

## <a name="fd"></a>3. `fd` - Modern find Alternative

> **Installation**: `apt install fd-find` (Debian/Ubuntu), `brew install fd` (macOS), `cargo install fd-find`
> Note: On Debian/Ubuntu, the binary is `fdfind`

### Basic Usage

```bash
# Simple search (case-insensitive by default)
fd pattern

# Search in specific directory
fd pattern /path/to/dir

# Case-sensitive search
fd -s Pattern

# Exact match
fd -g "exact_filename.txt"

# Show full path
fd -a pattern
```

### File Type Filtering

```bash
# Files only
fd -t f pattern

# Directories only
fd -t d pattern

# Symbolic links
fd -t l pattern

# Executables
fd -t x pattern

# Empty files/directories
fd -t e pattern

# Specific extension
fd -e txt
fd -e py
fd -e ps1

# Multiple extensions
fd -e txt -e md -e rst
```

### Advanced Patterns

```bash
# Regex (default)
fd ".*\.(ps1|sh|py)$"

# Glob pattern
fd -g "*.ps1"
fd -g "Password_File*"

# Multiple patterns (Windows findstr equivalent)
fd -g "POWERSHELL_SCRIPT" . && fd -g "Password_File*" . && fd -e ps1
# Or using regex:
fd "(POWERSHELL_SCRIPT|Password_File|.*\.ps1)"

# Hidden files included
fd -H pattern

# Ignored files included (.gitignore)
fd -I pattern

# Both hidden and ignored
fd -HI pattern
```

### Filtering & Exclusions

```bash
# Exclude pattern
fd -E "*.log" pattern
fd -E node_modules pattern

# Multiple exclusions
fd -E node_modules -E .git -E target pattern

# Use .gitignore rules (default)
fd pattern

# Ignore .gitignore
fd -I pattern

# Exclude directories
fd -E ".git/" -E "node_modules/" pattern
```

### Size & Time Filters

```bash
# Size filters
fd -S +1M           # Larger than 1MB
fd -S -100k         # Smaller than 100KB
fd -S +1M -S -100M  # Between 1MB and 100MB

# Time filters
fd --changed-within 1d    # Changed in last day
fd --changed-within 2h    # Changed in last 2 hours
fd --changed-before 1w    # Changed more than 1 week ago
```

### Depth Control

```bash
# Maximum depth
fd -d 2 pattern

# Exact depth
fd --min-depth 2 --max-depth 2 pattern
```

### Execution

```bash
# Execute command on each result
fd -e txt -x cat {}

# Execute with placeholders
fd -e txt -x echo "File: {}" "Dir: {//}" "Name: {/}" "Base: {.}"
# {} = full path
# {//} = parent directory
# {/} = filename
# {.} = filename without extension
# {/.} = filename without extension, no path

# Parallel execution (default)
fd -e txt -x wc -l {}

# Batch execution
fd -e txt -X cat {}

# Delete files
fd -e tmp -X rm {}
```

### Output Formatting

```bash
# Null separator (for xargs)
fd -0 pattern | xargs -0 command

# Absolute paths
fd -a pattern

# Color control
fd --color=always pattern | less -R
fd --color=never pattern
```

---

## <a name="rg"></a>4. `rg` (ripgrep) - Modern grep Alternative

> **Installation**: `apt install ripgrep` (Debian/Ubuntu), `brew install ripgrep` (macOS), `cargo install ripgrep`

### Basic Usage

```bash
# Simple search (recursive by default)
rg "pattern"

# Search specific file
rg "pattern" file.txt

# Search specific directory
rg "pattern" /path/to/dir

# Case-insensitive
rg -i "pattern"

# Case-sensitive (default)
rg -s "pattern"

# Smart case (insensitive unless uppercase present)
rg -S "pattern"
```

### Pattern Types

```bash
# Regex (default)
rg "POWERSHELL_SCRIPT|Password_File|.*\.ps1"

# Fixed string (literal)
rg -F "exact.string"

# Word boundary
rg -w "word"

# Whole line
rg -x "entire line must match"

# Multiline
rg -U "pattern\nacross\nlines"

# PCRE2 regex
rg -P "(?i)password(?=.*\d)"
```

### File Type Filtering

```bash
# By type
rg -t py "pattern"        # Python files
rg -t js "pattern"        # JavaScript files
rg -t sh "pattern"        # Shell scripts

# Multiple types
rg -t py -t js "pattern"

# List available types
rg --type-list

# Exclude type
rg -T js "pattern"

# Custom type definition
rg --type-add 'config:*.{conf,cfg,ini}' -t config "pattern"

# By glob
rg -g "*.py" "pattern"
rg -g "*.{py,js,ts}" "pattern"

# Exclude by glob
rg -g "!*.log" "pattern"
rg -g "!node_modules/**" "pattern"
```

### Output Control

```bash
# Line numbers (default on)
rg -n "pattern"

# No line numbers
rg -N "pattern"

# Show only filenames
rg -l "pattern"

# Show files without matches
rg --files-without-match "pattern"

# Count matches per file
rg -c "pattern"

# Only matching text
rg -o "pattern"

# Context lines
rg -B 3 "pattern"  # 3 before
rg -A 3 "pattern"  # 3 after
rg -C 3 "pattern"  # 3 both

# Replace matches
rg "pattern" -r "replacement"

# Show column number
rg --column "pattern"
```

### Hidden & Ignored Files

```bash
# Search hidden files
rg --hidden "pattern"

# Ignore .gitignore
rg --no-ignore "pattern"

# Ignore .ignore and .gitignore
rg --no-ignore-vcs "pattern"

# Everything (hidden + all ignore files)
rg -uuu "pattern"
# -u = --no-ignore
# -uu = --no-ignore --hidden
# -uuu = --no-ignore --hidden --binary
```

### Performance Options

```bash
# Follow symlinks
rg -L "pattern"

# Limit results
rg -m 5 "pattern"

# Memory map (faster for large files)
rg --mmap "pattern"

# Thread count
rg -j 4 "pattern"
```

### Advanced Features

```bash
# JSON output
rg --json "pattern"

# Null separator
rg -0 -l "pattern" | xargs -0 command

# Stats
rg --stats "pattern"

# Debug regex
rg --debug "pattern"

# Trace file searching
rg --trace "pattern"

# Search binary files
rg -a "pattern"

# Search compressed files (requires preprocessing)
zcat file.gz | rg "pattern"
```

---

## <a name="combined"></a>5. Combined Patterns & Workflows

### Find Files Then Search Content

```bash
# Using find + grep
find . -name "*.py" -exec grep -l "import os" {} \;

# Using find + xargs (more efficient)
find . -name "*.py" -print0 | xargs -0 grep -l "import os"

# Using fd + rg
fd -e py -x rg -l "import os" {}

# Find and search in one command
fd -e py --exec rg "import os" {}
```

### Complex Search Scenarios

```bash
# Find large log files modified today
find . -name "*.log" -size +10M -mtime 0
fd -e log -S +10M --changed-within 1d

# Find all scripts and search for passwords
find . \( -name "*.sh" -o -name "*.py" -o -name "*.ps1" \) -exec grep -i "password" {} +
fd -e sh -e py -e ps1 -x rg -i "password" {}

# Find empty directories and delete
find . -type d -empty -delete
fd -t d -t e -X rmdir {}

# Find duplicate filenames
find . -type f -printf "%f\n" | sort | uniq -d

# Security audit: world-writable files
find / -type f -perm -o=w 2>/dev/null
```

### Creating File Lists

```bash
# All Python files to a list
find . -name "*.py" > python_files.txt
fd -e py > python_files.txt

# Files with specific content
grep -r -l "TODO" . > todo_files.txt
rg -l "TODO" > todo_files.txt

# Sorted by modification time
find . -type f -printf "%T@ %p\n" | sort -n | cut -d' ' -f2-
```

---

## <a name="windows-equivalents"></a>6. Windows `findstr` Equivalents

The Windows command:
```cmd
findstr "POWERSHELL_SCRIPT|Password_File|*.ps1"
```

### Equivalent in Linux Tools

| Task | Linux Command |
|:-----|:--------------|
| **Search file names** | `find . -regex ".*\(POWERSHELL_SCRIPT\|Password_File\|.*\.ps1\)"` |
| **Search file names (fd)** | `fd "(POWERSHELL_SCRIPT\|Password_File\|.*\.ps1)"` |
| **Search file content** | `grep -rE "POWERSHELL_SCRIPT\|Password_File" --include="*.ps1" .` |
| **Search file content (rg)** | `rg "POWERSHELL_SCRIPT\|Password_File" -t ps1` |
| **Combined (names + content)** | See below |

### Combined Search (Names AND Content)

```bash
# Find files matching name patterns, then search inside them
find . \( -name "*POWERSHELL*" -o -name "*Password_File*" -o -name "*.ps1" \) \
  -exec grep -l "sensitive_pattern" {} \;

# Using fd + rg
fd "(POWERSHELL_SCRIPT|Password_File|.*\.ps1)" -x rg -l "sensitive_pattern" {}

# Find .ps1 files containing specific patterns
rg -t ps1 "POWERSHELL_SCRIPT|Password_File"
```

---

## Quick Reference Card

| Task | find | fd | grep | rg |
|:-----|:-----|:---|:-----|:---|
| Find by name | `find . -name "*.txt"` | `fd -e txt` | N/A | N/A |
| Find files only | `find . -type f` | `fd -t f` | N/A | N/A |
| Case insensitive | `find . -iname` | default | `grep -i` | `rg -i` |
| Regex | `-regex` | default | `grep -E` | default |
| Recursive | default | default | `grep -r` | default |
| Exclude dir | `-path X -prune` | `-E dir/` | `--exclude-dir` | `-g "!dir/"` |
| Execute | `-exec cmd {} \;` | `-x cmd {}` | N/A | N/A |
| Hidden files | default | `-H` | default | `--hidden` |
| Size filter | `-size +10M` | `-S +10M` | N/A | N/A |
| Time filter | `-mtime -7` | `--changed-within 7d` | N/A | N/A |

---

## Pro Tips

1. **Always quote patterns** with wildcards to prevent shell expansion
2. **Use `-print0` / `-0`** for filenames with spaces
3. **Test destructive commands** with `-print` or `echo` first
4. **`fd` and `rg` respect `.gitignore`** by default - use `-I`/`--no-ignore` to override
5. **Combine tools** for complex workflows: `fd ... | xargs rg ...`
6. **Use `--` to separate** options from patterns starting with `-`
