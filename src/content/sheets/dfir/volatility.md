---
title: "Volatility 3"
description: "Volatility 3 Windows memory forensics: processes, network, injection, hashes and plugin workflow."
category: dfir
tags: [dfir, memory-forensics, malware]
tools: [Volatility 3]
difficulty: advanced
updated: "2026-08-09"
source: "vault:DFIR/Volitility3 .md"
---

# Volatility 3

Windows memory forensics cheat sheet.

## Basic Command Structure

```bash
# Standard syntax
vol -f <memory.raw> <plugin>

# With options
vol -f memory.raw -o output/ -r json windows.pslist

# Plugin-specific help
vol windows.pslist -h
```

### Key Differences from Volatility 2

- NO `--profile` needed (auto-detection)
- Plugin namespace: `windows.plugin_name`
- Faster execution
- Python 3.8+ required
- Unified output formats

---

## Complete Plugin Enumeration Workflow

### Phase 1: System Identification

```bash
# Verify image and get OS info
vol -f memory.raw windows.info

# Output: OS version, architecture, kernel base, system time
```

### Phase 2: Process Analysis

#### Process Enumeration (Multiple Methods)

```bash
# Active processes (linked list traversal)
vol -f memory.raw windows.pslist

# Hidden/terminated processes (pool scanning)
vol -f memory.raw windows.psscan

# Process hierarchy tree
vol -f memory.raw windows.pstree

# Cross-reference detection (rootkit hunting)
vol -f memory.raw windows.psxview
```

#### Process Details

```bash
# Command-line arguments
vol -f memory.raw windows.cmdline
vol -f memory.raw windows.cmdline --pid 1234

# Command history from cmd.exe
vol -f memory.raw windows.cmdscan

# Console buffers
vol -f memory.raw windows.consoles

# Environment variables
vol -f memory.raw windows.envars --pid 1234

# Process privileges
vol -f memory.raw windows.privileges.Privs

# Process SIDs
vol -f memory.raw windows.getsids

# Process threads
vol -f memory.raw windows.threads
vol -f memory.raw windows.threads --pid 1234

# Suspended threads
vol -f memory.raw windows.suspended_threads

# Suspicious threads
vol -f memory.raw windows.suspicious_threads

# Debug registers
vol -f memory.raw windows.debugregisters

# Orphaned kernel threads
vol -f memory.raw windows.orphan_kernel_threads
```

#### DLL Analysis

```bash
# Loaded DLLs per process
vol -f memory.raw windows.dlllist
vol -f memory.raw windows.dlllist --pid 1234

# DLL load verification (detect DLL injection)
vol -f memory.raw windows.ldrmodules

# Unloaded modules
vol -f memory.raw windows.unloadedmodules
```

#### Handles

```bash
# Open handles (files, registry, mutexes, etc.)
vol -f memory.raw windows.handles
vol -f memory.raw windows.handles --pid 1234
```

### Phase 3: Network Analysis

```bash
# Network connections (TCP/UDP) - Vista+
vol -f memory.raw windows.netscan

# Alternative: netstat (Vista+)
vol -f memory.raw windows.netstat
```

**Output:** Local/Remote addresses, PIDs, state, protocol, timestamps.

### Phase 4: File System Analysis

```bash
# Scan for FILE_OBJECT structures
vol -f memory.raw windows.filescan

# Dump cached files
vol -f memory.raw -o output/ windows.dumpfiles
vol -f memory.raw -o output/ windows.dumpfiles --pid 1234
vol -f memory.raw -o output/ windows.dumpfiles --virtaddr 0x12345678
vol -f memory.raw -o output/ windows.dumpfiles --physaddr 0xabcdef

# MFT entries scanning
vol -f memory.raw windows.mftscan.MFTScan

# Alternate Data Streams (ADS)
vol -f memory.raw windows.mftscan.ADS

# Symbolic links
vol -f memory.raw windows.symlinkscan
```

### Phase 5: Registry Analysis

```bash
# List registry hives
vol -f memory.raw windows.registry.hivelist

# Scan for hives
vol -f memory.raw windows.registry.hivescan

# Print registry keys
vol -f memory.raw windows.registry.printkey
vol -f memory.raw windows.registry.printkey --key "Software\\Microsoft\\Windows\\CurrentVersion\\Run"

# UserAssist (tracks executed programs)
vol -f memory.raw windows.registry.userassist

# Certificates
vol -f memory.raw windows.registry.certificates.Certificates

# Hooked registry handlers
vol -f memory.raw windows.registry.getcellroutine
```

### Phase 6: Malware Detection

#### Code Injection Detection

```bash
# Find injected code
vol -f memory.raw windows.malfind

# Hollow processes
vol -f memory.raw windows.hollowprocesses

# Process ghosting
vol -f memory.raw windows.processghosting

# Direct system calls (EDR bypass)
vol -f memory.raw windows.direct_system_calls

# Indirect system calls (EDR bypass)
vol -f memory.raw windows.indirect_system_calls

# Unhooked system calls (EDR bypass)
vol -f memory.raw windows.unhooked_system_calls
```

#### Kernel Hooks & Rootkits

```bash
# Kernel callbacks
vol -f memory.raw windows.callbacks.Callbacks

# SSDT (System Service Descriptor Table)
vol -f memory.raw windows.ssdt.SSDT

# Driver IRP hooks
vol -f memory.raw windows.driverirp.DriverIrp

# Hidden drivers
vol -f memory.raw windows.drivermodule.DriverModule

# Skeleton Key malware detection
vol -f memory.raw windows.skeleton_key_check.Skeleton_Key_Check

# Kernel timers
vol -f memory.raw windows.timers.Timers
```

#### YARA Scanning

```bash
# Scan process memory with YARA
vol -f memory.raw windows.vadyarascan --yara-file rules.yar
vol -f memory.raw windows.vadyarascan --yara-rules "rule test { strings: $a = \"malware\" condition: $a }"

# Scan entire memory
vol -f memory.raw yarascan.YaraScan --yara-file rules.yar

# Regex scanning
vol -f memory.raw windows.vadregexscan --pattern "https?://[a-zA-Z0-9]+"
```

#### Import Address Table (IAT) Analysis

```bash
vol -f memory.raw windows.iat.IAT --pid 1234
```

### Phase 7: Memory Dumps

```bash
# Dump process memory
vol -f memory.raw -o output/ windows.memmap --dump --pid 1234

# Dump PE executables
vol -f memory.raw -o output/ windows.pedump.PEDump --pid 1234

# Memory map
vol -f memory.raw windows.memmap --pid 1234

# VAD (Virtual Address Descriptor) information
vol -f memory.raw windows.vadinfo --pid 1234

# Walk VAD tree
vol -f memory.raw windows.vadwalk --pid 1234
```

### Phase 8: Windows Services

```bash
# List services (doubly-linked list)
vol -f memory.raw windows.svclist.SvcList

# Scan for services (pool scanning)
vol -f memory.raw windows.svcscan.SvcScan

# Compare methods (rootkit detection)
vol -f memory.raw windows.svcdiff.SvcDiff

# Service SIDs
vol -f memory.raw windows.getservicesids.GetServiceSIDs
```

### Phase 9: Scheduled Tasks

```bash
vol -f memory.raw windows.scheduled_tasks.ScheduledTasks
```

### Phase 10: Credential Extraction

```bash
# Password hashes
vol -f memory.raw windows.hashdump.Hashdump

# LSA secrets
vol -f memory.raw windows.lsadump.Lsadump

# Cached domain credentials
vol -f memory.raw windows.cachedump.Cachedump

# TrueCrypt passphrases
vol -f memory.raw windows.truecrypt.Passphrase
```

### Phase 11: Driver Analysis

```bash
# Loaded kernel modules
vol -f memory.raw windows.modules.Modules

# Scan for drivers (finds hidden)
vol -f memory.raw windows.driverscan.DriverScan

# Module scanning
vol -f memory.raw windows.modscan.ModScan

# Device tree
vol -f memory.raw windows.devicetree.DeviceTree

# KPCR structures
vol -f memory.raw windows.kpcrs.KPCRs
```

### Phase 12: Forensic Artifacts

```bash
# AmCache
vol -f memory.raw windows.amcache.Amcache

# ShimCache
vol -f memory.raw windows.shimcachemem.ShimcacheMem

# Big page pools
vol -f memory.raw windows.bigpools.BigPools

# Master Boot Record scanning
vol -f memory.raw windows.mbrscan.MBRScan

# Job links
vol -f memory.raw windows.joblinks.JobLinks

# Sessions
vol -f memory.raw windows.sessions.Sessions

# Crash dump info
vol -f memory.raw windows.crashinfo.Crashinfo

# PE symbols
vol -f memory.raw windows.pe_symbols.PESymbols

# Version info
vol -f memory.raw windows.verinfo.VerInfo

# Statistics
vol -f memory.raw windows.statistics.Statistics
```

### Phase 13: Mutexes & Synchronization

```bash
# Scan for mutexes
vol -f memory.raw windows.mutantscan.MutantScan
```

### Phase 14: Timeline Analysis

```bash
# Generate timeline from all plugins
vol -f memory.raw timeliner.Timeliner
```

---

## New Plugins in Volatility 3 (v2.7–2.26)

### EDR Bypass Detection

```bash
windows.direct_system_calls       # Direct syscall technique
windows.indirect_system_calls     # Indirect syscall technique
windows.unhooked_system_calls     # Unhooked syscall detection
```

### Advanced Malware Detection

```bash
windows.hollowprocesses           # Process hollowing detection
windows.processghosting           # Process ghosting technique
windows.suspended_threads         # Find suspended threads
windows.suspicious_threads        # Identify suspicious threads
windows.orphan_kernel_threads     # Orphaned kernel threads
```

### Command History & Console

```bash
windows.cmdscan                   # Command history scanning
windows.consoles                  # Console buffer extraction
```

### Registry & Forensics

```bash
windows.amcache.Amcache           # AmCache parsing
windows.scheduled_tasks           # Scheduled tasks
windows.registry.getcellroutine   # Registry hook detection
windows.shimcachemem              # ShimCache from memory
windows.debugregisters            # Hardware breakpoint detection
```

### Import Address Table

```bash
windows.iat.IAT                   # IAT extraction and analysis
```

### Process Cross-Reference

```bash
windows.psxview                   # Multi-method process detection
```

### Regex & Advanced Scanning

```bash
windows.vadregexscan              # Regex pattern scanning in VADs
```

---

## Output Formats

```bash
# JSON output
vol -f memory.raw -r json windows.pslist > output.json

# CSV output
vol -f memory.raw -r csv windows.pslist > output.csv

# Pretty formatted
vol -f memory.raw -r pretty windows.pslist

# JSONL (line-delimited JSON)
vol -f memory.raw -r jsonl windows.netscan

# Save to file
vol -f memory.raw windows.pslist > pslist.txt
```

---

## Advanced Tips & Tricks

### 1. Filtering & Targeting

```bash
# Target specific PID
vol -f memory.raw windows.pslist --pid 1234
vol -f memory.raw windows.dlllist --pid 1234

# Multiple PIDs (plugin dependent)
vol -f memory.raw windows.handles --pid 1234 --pid 5678
```

### 2. Parallel Processing

```bash
vol -f memory.raw --parallelism processes windows.psscan
```

### 3. Verbosity for Debugging

```bash
# Increase verbosity to troubleshoot
vol -f memory.raw -vvv windows.info
```

### 4. Offline Mode

```bash
# Disable online symbol lookups
vol -f memory.raw --offline windows.pslist
```

### 5. Configuration Files

```bash
# Use config file for repeated analysis
vol -c config.json windows.pslist

# Save configuration
vol -f memory.raw --save-config analysis.json windows.pslist
```

### 6. Combining Outputs

```bash
# Run multiple plugins and save all
for plugin in pslist pstree netscan filescan; do
    vol -f memory.raw windows.$plugin > ${plugin}_output.txt
done
```

### 7. Hunting for Specific Artifacts

```bash
# Find specific string in process memory
vol -f memory.raw windows.strings | grep -i "password"

# Search for IP addresses
vol -f memory.raw windows.netscan | grep "192.168"

# Find processes without parent
vol -f memory.raw windows.pstree | grep "PPID: 0"
```

### 8. Memory Dump Extraction

```bash
# Dump specific process
vol -f memory.raw -o dumps/ windows.memmap --dump --pid 1234

# Dump all files
vol -f memory.raw -o files/ windows.dumpfiles

# Dump executable only
vol -f memory.raw -o exe/ windows.pedump --pid 1234
```

---

## Malware Analysis Workflow

### Step 1: Initial Triage

```bash
vol -f memory.raw windows.info
vol -f memory.raw windows.pslist
vol -f memory.raw windows.pstree
vol -f memory.raw windows.netscan
```

### Step 2: Identify Suspicious Processes

Look for:
- Processes with no parent (PPID: 0)
- Misspelled system processes
- Unusual paths (not in System32/Program Files)
- Processes with network connections
- Short-lived processes (in psscan but not pslist)

### Step 3: Deep Dive on Suspicious Process

```bash
PID=<suspicious_pid>
vol -f memory.raw windows.cmdline --pid $PID
vol -f memory.raw windows.dlllist --pid $PID
vol -f memory.raw windows.handles --pid $PID
vol -f memory.raw windows.envars --pid $PID
vol -f memory.raw windows.malfind --pid $PID
vol -f memory.raw windows.vadinfo --pid $PID
```

### Step 4: Code Injection Detection

```bash
vol -f memory.raw windows.malfind
vol -f memory.raw windows.hollowprocesses
vol -f memory.raw windows.ldrmodules
vol -f memory.raw windows.direct_system_calls
vol -f memory.raw windows.indirect_system_calls
```

### Step 5: Persistence Mechanisms

```bash
vol -f memory.raw windows.registry.printkey --key "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
vol -f memory.raw windows.registry.userassist
vol -f memory.raw windows.scheduled_tasks
vol -f memory.raw windows.svcscan
```

### Step 6: Dump & Analyze

```bash
vol -f memory.raw -o output/ windows.memmap --dump --pid $PID
vol -f memory.raw -o output/ windows.pedump --pid $PID
```

---

## Rootkit Detection Checklist

```bash
# 1. Hidden processes
vol -f memory.raw windows.psxview

# 2. Hidden drivers
vol -f memory.raw windows.drivermodule

# 3. Kernel hooks
vol -f memory.raw windows.ssdt
vol -f memory.raw windows.callbacks
```
