---
title: "RECmd Registry Forensics"
description: "RECmd registry analysis workflow: batch files, keys of interest and evidence extraction."
category: dfir
tags: [dfir, registry, windows]
tools: [RECmd, Registry Explorer]
difficulty: advanced
updated: "2026-08-09"
source: "vault:DFIR/REDmd - Quick Cheat sheet.md"
---

# RECmd Registry Forensics

## Part 1: Quick Reference Cheat Sheet

### Essential Command Templates

```powershell
# UPDATE BATCH FILES
RECmd.exe --sync

# PARSE SINGLE HIVE
RECmd.exe -f <HIVE_PATH> --csv <OUT_DIR> --csvf <FILENAME>.csv --dt "dd/MM/yyyy HH:mm:ss"

# PARSE ALL HIVES IN DIRECTORY
RECmd.exe -d <HIVES_DIR> --csv <OUT_DIR> --dt "dd/MM/yyyy HH:mm:ss"

# RUN BATCH FILE (TRIAGE)
RECmd.exe -d <HIVES_DIR> --bn BatchExamples\DFIRBatch.reb --csv <OUT_DIR> --csvf Triage.csv --dt "dd/MM/yyyy HH:mm:ss"

# EXTRACT SPECIFIC KEY
RECmd.exe -f <HIVE_PATH> --kn "KeyPath\Here" --csv <OUT_DIR> --csvf Output.csv

# SEARCH FOR KEYWORD
RECmd.exe -f <HIVE_PATH> --sd "keyword" --csv <OUT_DIR> --csvf Search.csv

# RECOVER DELETED KEYS/VALUES (DEFAULT = ON)
RECmd.exe -f <HIVE_PATH> --recover true --csv <OUT_DIR> --csvf Recovered.csv

# REPLAY TRANSACTION LOGS (DEFAULT = ON)
RECmd.exe -f <HIVE_PATH> --nl false --csv <OUT_DIR> --csvf Clean.csv
```

---

### Critical Flags Reference

| Flag | Purpose | Example |
|------|---------|---------|
| `-f` | Single hive file | `-f C:\Evidence\SYSTEM` |
| `-d` | Directory (recursive) | `-d C:\Evidence\Hives` |
| `--bn` | Batch file | `--bn BatchExamples\DFIRBatch.reb` |
| `--csv` | Output directory | `--csv C:\Output\CSV` |
| `--csvf` | Override CSV filename | `--csvf SYSTEM_results.csv` |
| `--dt` | Date format (UK) | `--dt "dd/MM/yyyy HH:mm:ss"` |
| `--nl` | Ignore transaction logs | `--nl false` (default = replay logs) |
| `--recover` | Recover deleted data | `--recover true` (default = on) |
| `--kn` | Extract specific key | `--kn "ControlSet001\Services"` |
| `--vn` | Extract specific value | `--vn "ProductName"` |
| `--sa` | Search all | `--sa "malware.exe"` |
| `--sk` | Search key names | `--sk "Run"` |
| `--sv` | Search value names | `--sv "Path"` |
| `--sd` | Search value data | `--sd "C:\Windows"` |
| `--regex` | Enable regex search | `--regex --sd ".*\.exe$"` |
| `--vss` | Parse Volume Shadow Copies | `--vss` |
| `--q` | Quiet mode | `--q` |

---

### Batch Files Quick Reference

| Batch File | Purpose | Command |
|-----------|---------|---------|
| `DFIRBatch.reb` | Full triage (System Info, Execution, Persistence, User Activity) | `--bn BatchExamples\DFIRBatch.reb` |
| `RegistryASEPs.reb` | Persistence detection (~500 keys, ~400 values) | `--bn BatchExamples\RegistryASEPs.reb` |
| Custom `.reb` | Targeted extraction (USB, Run keys, etc.) | Create your own (see Part 6) |

---

### File Structure

```text
<CASE_DIR>/
├── Tools/
│   └── RECmd/
│       ├── RECmd.exe
│       ├── RLA.exe                 # Transaction log replayer
│       └── BatchExamples/
│           ├── DFIRBatch.reb
│           └── RegistryASEPs.reb
├── Evidence/
│   └── Hives/
│       ├── SAM
│       ├── SECURITY
│       ├── SOFTWARE
│       ├── SYSTEM
│       ├── SYSTEM.LOG1            # Transaction logs
│       ├── SYSTEM.LOG2
│       └── NTUSER.DAT
└── Output/
    └── CSV/
```

---

## Part 2: Workflow for Your Hive Set

### Setup (One-Time)

```powershell
# 1. Create folder structure
mkdir C:\Cases\MyCase\Tools\RECmd
mkdir C:\Cases\MyCase\Evidence\Hives
mkdir C:\Cases\MyCase\Output\CSV

# 2. Download RECmd to Tools\RECmd folder
# Source: https://ericzimmerman.github.io/#!index.md

# 3. Copy your hives to Evidence\Hives:
#    - SAM
#    - SECURITY
#    - SOFTWARE
#    - SYSTEM (+ SYSTEM.LOG1, SYSTEM.LOG2 if available)
#    - NTUSER.DAT

# 4. Update batch files
cd C:\Cases\MyCase\Tools\RECmd
RECmd.exe --sync
```

---

### Workflow 1: Fast Triage (5 minutes)

**Objective:** Get high-value artefacts immediately.

```powershell
cd C:\Cases\MyCase\Tools\RECmd

# Run DFIRBatch against all hives
RECmd.exe -d C:\Cases\MyCase\Evidence\Hives --bn BatchExamples\DFIRBatch.reb --csv C:\Cases\MyCase\Output\CSV --csvf Triage.csv --q --dt "dd/MM/yyyy HH:mm:ss"
```

**Output:** Single CSV file `Triage.csv` containing:
- System info (OS version, hostname, timezone)
- User accounts (SAM)
- Program execution (ShimCache, BAM/DAM, UserAssist)
- Persistence (Run keys, services, scheduled tasks)
- USB devices (USBSTOR, mounted devices)
- User activity (RecentDocs, TypedPaths, searches)

**Review in Timeline Explorer:**
1. Open `C:\Cases\MyCase\Output\CSV\Triage.csv`
2. Filter by `Category` column: `Program Execution`, `Persistence`, `User Activity`, `Devices`

---

### Workflow 2: Hive-by-Hive Deep Dive

#### SAM Hive: User Accounts

**What you'll find:** Local user accounts (username, RID, SID), last login times, logon counts, password policies, group membership.

```powershell
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SAM --csv C:\Cases\MyCase\Output\CSV --csvf SAM.csv --dt "dd/MM/yyyy HH:mm:ss"
```

**Key artefacts to review:**

| KeyPath | What to look for |
|---------|------------------|
| `SAM\Domains\Account\Users\000001F4` | RID 500 = Built-in Administrator account |
| `SAM\Domains\Account\Users\<RID>` | Check `LastWriteTime` = account creation/modification |
| Value: `F` | Account metadata (flags, lockout) |
| Value: `V` | Username |

**Red flags:**
- New local admin accounts (RID 500 group membership)
- Accounts with zero logon count but recent `LastWriteTime` (re-enabled?)
- Disabled accounts with activity timestamps

---

#### SECURITY Hive: Audit Configuration

**What you'll find:** Security policies, audit settings, LSA secrets (structure only; data encrypted).

```powershell
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SECURITY --csv C:\Cases\MyCase\Output\CSV --csvf SECURITY.csv --dt "dd/MM/yyyy HH:mm:ss"
```

**Key artefacts:**

| KeyPath | What to look for |
|---------|------------------|
| `Policy\PolAdtEv` | Audit policy bitmask (disabled = evasion) |
| `Policy\Secrets` | LSA secrets structure (data encrypted) |

> **Note —** Limited forensic value for offline analysis; most data encrypted.

---

#### SOFTWARE Hive: System Configuration & Persistence

**What you'll find:** OS version, hostname, install date, installed software, persistence mechanisms (Run keys, scheduled tasks), user profile paths (ProfileList), network shares (MountPoints2).

```powershell
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SOFTWARE --bn BatchExamples\DFIRBatch.reb --csv C:\Cases\MyCase\Output\CSV --csvf SOFTWARE.csv --dt "dd/MM/yyyy HH:mm:ss"
```

**Key artefacts to review:**

| KeyPath | What to look for |
|---------|------------------|
| `Microsoft\Windows NT\CurrentVersion` | `ProductName`, `ReleaseId`, `InstallDate` |
| `Microsoft\Windows\CurrentVersion\Run` | Machine-wide auto-start entries |
| `Microsoft\Windows\CurrentVersion\RunOnce` | One-time execution entries |
| `Wow6432Node\Microsoft\Windows\CurrentVersion\Run` | 32-bit persistence on 64-bit systems |
| `Microsoft\Windows NT\CurrentVersion\ProfileList` | User SIDs → Profile paths (e.g., `C:\Users\JohnDoe`) |
| `Microsoft\Windows\CurrentVersion\Uninstall` | Installed software (`DisplayName`, `InstallDate`) |
| `Microsoft\Windows\CurrentVersion\Explorer\MountPoints2` | Mapped drives, UNC shares |

**Persistence hunt:**

```powershell
# Extract all Run keys
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SOFTWARE --kn "Microsoft\Windows\CurrentVersion\Run" --csv C:\Cases\MyCase\Output\CSV --csvf Run_keys.csv --dt "dd/MM/yyyy HH:mm:ss"

# Search for suspect paths
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SOFTWARE --sd "AppData\Roaming" --csv C:\Cases\MyCase\Output\CSV --csvf Suspect_paths.csv
```

**Red flags:**
- Obfuscated Run key values (Base64, PowerShell encoded commands)
- Non-standard paths (`C:\Temp`, `C:\ProgramData`, user AppData)
- Recently modified Run keys (check `LastWriteTime`)

---

#### SYSTEM Hive: Hardware, Services, USB Devices, Execution

**What you'll find:** Services, USB device history (USBSTOR, mounted devices), ShimCache (file existence, NOT execution proof), BAM/DAM (execution evidence with timestamps), network configuration, timezone.

```powershell
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SYSTEM --bn BatchExamples\DFIRBatch.reb --csv C:\Cases\MyCase\Output\CSV --csvf SYSTEM.csv --dt "dd/MM/yyyy HH:mm:ss"
```

**Key artefacts to review:**

| KeyPath | What to look for |
|---------|------------------|
| `ControlSet001\Enum\USBSTOR` | USB storage devices (VID, PID, serial number) |
| `ControlSet001\Enum\USB` | All USB devices (including non-storage) |
| `MountedDevices` | Drive letters → Device serial numbers |
| `ControlSet001\Services` | Service binaries (check `ImagePath`, `Start` type) |
| `ControlSet001\Control\Session Manager\AppCompatCache` | ShimCache: file paths, modified times, sizes |
| `ControlSet001\Services\bam\State\UserSettings\<SID>` | BAM: execution timestamps (Win10 1709+) |
| `ControlSet001\Services\dam\State\UserSettings\<SID>` | DAM: Desktop Activity Moderator |
| `ControlSet001\Control\TimeZoneInformation` | Timezone, DST settings |
| `Select` | `Current` = active ControlSet number |

**USB device extraction:**

```powershell
# Extract USB storage devices
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SYSTEM --kn "ControlSet001\Enum\USBSTOR" --csv C:\Cases\MyCase\Output\CSV --csvf USB_STOR.csv

# Extract all USB devices
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SYSTEM --kn "ControlSet001\Enum\USB" --csv C:\Cases\MyCase\Output\CSV --csvf USB_all.csv

# Extract mounted devices
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SYSTEM --kn "MountedDevices" --csv C:\Cases\MyCase\Output\CSV --csvf Mounted.csv
```

**Execution evidence (BAM/DAM):**

```powershell
# Extract BAM (Win10 1709+)
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SYSTEM --kn "ControlSet001\Services\bam\State\UserSettings" --csv C:\Cases\MyCase\Output\CSV --csvf BAM.csv --dt "dd/MM/yyyy HH:mm:ss"

# Extract DAM
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SYSTEM --kn "ControlSet001\Services\dam\State\UserSettings" --csv C:\Cases\MyCase\Output\CSV --csvf DAM.csv --dt "dd/MM/yyyy HH:mm:ss"
```

**Review BAM/DAM output:**
- Each subkey = User SID (cross-reference with SOFTWARE\ProfileList)
- Value names = Hex timestamps
- Value data = Executable full path
- **This is STRONG execution evidence**

**ShimCache extraction:**

```powershell
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SYSTEM --kn "ControlSet001\Control\Session Manager\AppCompatCache" --csv C:\Cases\MyCase\Output\CSV --csvf ShimCache.csv --dt "dd/MM/yyyy HH:mm:ss"
```

**ShimCache caveats:**
- **Does NOT prove execution**, only file existence
- `LastModified` = file timestamp, NOT execution time
- Useful for: identifying suspect file paths, confirming file presence (even if deleted)

**Red flags:**
- Unusual service binaries (non-System32 paths, renamed system tools)
- USB devices connected during incident timeframe (check `LastWriteTime` on USBSTOR keys)
- BAM/DAM entries for known malware paths
- ShimCache entries for staging directories (`C:\Temp`, `C:\Users\Public`)

---

#### NTUSER.DAT Hive: User Activity

**What you'll find:** Recently opened files (RecentDocs), program execution (UserAssist), folder access history (ShellBags), typed paths, search terms (WordWheelQuery), Office documents with macros enabled (TrustRecords).

```powershell
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\NTUSER.DAT --bn BatchExamples\DFIRBatch.reb --csv C:\Cases\MyCase\Output\CSV --csvf NTUSER.csv --dt "dd/MM/yyyy HH:mm:ss"
```

**Key artefacts to review:**

| KeyPath | What to look for |
|---------|------------------|
| `Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist\<GUID>\Count` | GUI program execution (ROT13 encoded) |
| `Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs` | Recently opened files by extension |
| `Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSavePidlMRU` | Open/Save dialog history |
| `Software\Microsoft\Windows\Shell\BagMRU` | Folder access history (ShellBags) |
| `Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths` | Paths typed into Explorer address bar |
| `Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU` | Commands in Win+R Run dialog |
| `Software\Microsoft\Windows\CurrentVersion\Explorer\WordWheelQuery` | Windows Search queries |
| `Software\Microsoft\Office\<Version>\<App>\Security\Trusted Documents\TrustRecords` | Office files with macros enabled |

**UserAssist extraction:**

```powershell
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\NTUSER.DAT --kn "Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist" --csv C:\Cases\MyCase\Output\CSV --csvf UserAssist.csv
```

**UserAssist decoding:**
- Value names are ROT13 encoded (e.g., `HRZR_PGYFRFFVATF` = `UEME_PGULESSFVATS`)
- Timeline Explorer auto-decodes
- Manual: use an online ROT13 decoder
- Value data contains: execution count, last execution timestamp

**RecentDocs extraction:**

```powershell
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\NTUSER.DAT --kn "Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs" --csv C:\Cases\MyCase\Output\CSV --csvf RecentDocs.csv
```

**ShellBags extraction:**

```powershell
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\NTUSER.DAT --kn "Software\Microsoft\Windows\Shell\BagMRU" --csv C:\Cases\MyCase\Output\CSV --csvf ShellBags.csv
```

**Search terms extraction:**

```powershell
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\NTUSER.DAT --kn "Software\Microsoft\Windows\CurrentVersion\Explorer\WordWheelQuery" --csv C:\Cases\MyCase\Output\CSV --csvf Searches.csv
```

**Red flags:**
- Searches for anti-forensics tools ("delete logs", "wipe files")
- Execution of tools from USB/external drives (UserAssist)
- Recently opened files with suspect extensions (`.exe`, `.bat`, `.ps1` in RecentDocs)
- Office TrustRecords for phishing document paths (e.g., `Downloads\invoice.docm`)
- TypedPaths/RunMRU containing attacker commands (e.g., `powershell.exe -enc <Base64>`)

**Multiple NTUSER.DAT files (multi-user system):**

```powershell
# 1. Get user list from SOFTWARE hive
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SOFTWARE --kn "Microsoft\Windows NT\CurrentVersion\ProfileList" --csv C:\Cases\MyCase\Output\CSV --csvf Users.csv

# 2. Process each user's NTUSER.DAT (example for JohnDoe)
RECmd.exe -f "C:\Users\JohnDoe\NTUSER.DAT" --bn BatchExamples\DFIRBatch.reb --csv C:\Cases\MyCase\Output\CSV --csvf NTUSER_JohnDoe.csv

# 3. Repeat for additional users
RECmd.exe -f "C:\Users\JaneSmith\NTUSER.DAT" --bn BatchExamples\DFIRBatch.reb --csv C:\Cases\MyCase\Output\CSV --csvf NTUSER_JaneSmith.csv
```

---

### Workflow 3: Persistence Hunting

**Objective:** Identify all auto-start locations (ASEPs).

```powershell
# Run RegistryASEPs batch (Troy Larson)
RECmd.exe -d C:\Cases\MyCase\Evidence\Hives --bn BatchExamples\RegistryASEPs.reb --csv C:\Cases\MyCase\Output\CSV --csvf Persistence.csv --dt "dd/MM/yyyy HH:mm:ss"
```

**Output:** ~500 registry keys, ~400 values covering Run/RunOnce keys (machine + user), services, scheduled tasks, Winlogon entries, Image File Execution Options, AppInit_DLLs, browser helper objects (BHOs), startup folder paths.

**Timeline Explorer review:**
1. Open `Persistence.csv`
2. Filter by `Category` = "Persistence" or "Autoruns"
3. Sort by `LastWriteTime` (most recent first)
4. Focus on: unknown/unsigned binaries, non-standard paths, Base64/encoded commands, timestamps matching incident timeframe

---

### Workflow 4: Keyword Search Across All Hives

**Scenario:** Search for specific IOC (e.g., `malware.exe`).

```powershell
# Search all value data for keyword
RECmd.exe -d C:\Cases\MyCase\Evidence\Hives --sd "malware.exe" --csv C:\Cases\MyCase\Output\CSV --csvf Search_malware.csv

# Search with regex (all .exe files in Temp)
RECmd.exe -d C:\Cases\MyCase\Evidence\Hives --regex --sd "C:\\\\Temp\\\\.*\\.exe" --csv C:\Cases\MyCase\Output\CSV --csvf Search_Temp_EXE.csv

# Search key names
RECmd.exe -d C:\Cases\MyCase\Evidence\Hives --sk "Run" --csv C:\Cases\MyCase\Output\CSV --csvf Search_Run_keys.csv

# Search value names
RECmd.exe -d C:\Cases\MyCase\Evidence\Hives --sv "ImagePath" --csv C:\Cases\MyCase\Output\CSV --csvf Search_ImagePath.csv
```

---

## Part 3: Recovering Deleted Registry Data

### Understanding Deleted Data

Registry deletion behaviour:
- Deleted keys/values are NOT immediately removed from hive file
- Marked as "deleted" in hive structure but data remains until overwritten
- RECmd can recover deleted entries using `--recover` switch (DEFAULT = ON)

What can be recovered: deleted registry keys, deleted values, slack space (residual data in unused hive blocks).

---

### Method 1: Automatic Recovery (Default)

```powershell
# Recovery is ON by default
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SOFTWARE --csv C:\Cases\MyCase\Output\CSV --csvf SOFTWARE_recovered.csv

# Explicitly enable (same as default)
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SOFTWARE --recover true --csv C:\Cases\MyCase\Output\CSV --csvf SOFTWARE_recovered.csv
```

Identifying recovered data in CSV output: check `IsDeleted` column (if present in plugin output); deleted keys show in output with timestamps but marked as removed.

---

### Method 2: Search Slack Space

Slack space = unused portions of hive file blocks containing residual deleted data.

```powershell
# Search slack space for keyword
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SOFTWARE --ss --sd "deleted_value" --csv C:\Cases\MyCase\Output\CSV --csvf Slack_search.csv

# Search all (keys + values + data + slack)
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SOFTWARE --sa "keyword" --csv C:\Cases\MyCase\Output\CSV --csvf All_search.csv
```

---

### Method 3: Transaction Log Replay (Clean Dirty Hives)

**Scenario:** Hive is "dirty" (not cleanly shut down) and transaction logs exist.

Transaction logs: `*.LOG1`, `*.LOG2` files contain uncommitted changes.

RECmd behaviour:
- `--nl false` (DEFAULT) = replays transaction logs → clean hive data
- `--nl true` = ignores transaction logs → may miss recent data

**Check for transaction logs:**

```powershell
# Example: SYSTEM hive
dir C:\Cases\MyCase\Evidence\Hives\SYSTEM*
# Expected files: SYSTEM, SYSTEM.LOG1, SYSTEM.LOG2
```

**Parse with transaction log replay:**

```powershell
# Ensure .LOG1 and .LOG2 are in same directory as hive
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SYSTEM --nl false --csv C:\Cases\MyCase\Output\CSV --csvf SYSTEM_clean.csv
```

**If transaction logs are missing:**

```powershell
# Parse without transaction logs (may be incomplete)
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SYSTEM --nl true --csv C:\Cases\MyCase\Output\CSV --csvf SYSTEM_dirty.csv
```

**Alternative: Use RLA.exe to create clean hive** (RLA.exe = Registry Log Analyser, included with RECmd).

```powershell
# Replay transaction logs and output clean hive
cd C:\Cases\MyCase\Tools\RECmd
RLA.exe -f C:\Cases\MyCase\Evidence\Hives\SYSTEM --out C:\Cases\MyCase\Evidence\Hives\Clean

# Output: C:\Cases\MyCase\Evidence\Hives\Clean\SYSTEM (clean copy)

# Now parse clean hive with RECmd
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\Clean\SYSTEM --csv C:\Cases\MyCase\Output\CSV --csvf SYSTEM_clean.csv

# RLA for entire directory
RLA.exe -d C:\Cases\MyCase\Evidence\Hives --out C:\Cases\MyCase\Evidence\Hives\Clean
```

---

### Method 4: Volume Shadow Copy Analysis

**Scenario:** Recover historical registry states from VSS snapshots. Prerequisite: VSS snapshots must exist on evidence drive.

```powershell
# Parse hive + all VSS snapshots
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SOFTWARE --vss --csv C:\Cases\MyCase\Output\CSV --csvf SOFTWARE_VSS.csv --dt "dd/MM/yyyy HH:mm:ss"

# Or entire directory with VSS
RECmd.exe -d C:\Cases\MyCase\Evidence\Hives --vss --csv C:\Cases\MyCase\Output\CSV --csvf All_VSS.csv
```

Output: separate entries for each VSS snapshot; timestamped filenames show VSS creation date; compare current hive vs historical snapshots to identify deleted/modified keys.

---

### Recovery Checklist

- [ ] **Transaction logs present?** If YES: run with `--nl false` (default). If NO: run with `--nl true` (accept incomplete data), or use RLA.exe to attempt recovery.
- [ ] **Recover deleted keys/values** — run with `--recover true` (default); review CSV output for deleted entries.
- [ ] **Search slack space** — use `--ss` flag with search keywords; look for residual deleted data.
- [ ] **Volume Shadow Copies available?** — use `--vss` to parse historical snapshots; compare current vs historical states.
- [ ] **Output verification** — check CSV row count (compare with/without `--recover`); review `LastWriteTime` timestamps for anomalies; cross-reference with known-good baselines.

---

## Part 4: Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `Unable to open file` | File locked, wrong path, permissions | Run as Administrator, verify path, close Registry Editor |
| `Hive is dirty` | Missing transaction logs | Supply `.LOG1`/`.LOG2` files OR use RLA.exe OR run with `--nl true` |
| Empty CSV output | Batch HiveType mismatch | Check batch file `HiveType` matches hive (e.g., NTUSER batch on NTUSER.DAT) |
| ROT13 encoded values | Raw UserAssist output | Open CSV in Timeline Explorer (auto-decodes) |
| `Out of memory` | Large hive + `--details` | Remove `--details`, use `--q`, increase system RAM |
| Fewer rows without `--nl false` | Missing transaction log data | Ensure `.LOG1`/`.LOG2` present and `--nl false` used |

### Quick Fixes

```powershell
# Check hive file is readable
icacls C:\Cases\MyCase\Evidence\Hives\SYSTEM

# Verify batch file exists
dir C:\Cases\MyCase\Tools\RECmd\BatchExamples\DFIRBatch.reb

# Test single key extraction (troubleshooting)
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SOFTWARE --kn "Microsoft\Windows NT\CurrentVersion" --csv C:\Cases\MyCase\Output\CSV --csvf Test.csv
```

---

## Part 5: Integration with Prefetch (PECmd)

**Scenario:** Confirm program execution using multiple artefacts.

```powershell
# Step 1: Extract prefetch with PECmd
PECmd.exe -d C:\Cases\MyCase\Evidence\Prefetch --csv C:\Cases\MyCase\Output\CSV --csvf Prefetch.csv

# Step 2: Extract BAM/DAM from SYSTEM hive
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SYSTEM --kn "ControlSet001\Services\bam\State\UserSettings" --csv C:\Cases\MyCase\Output\CSV --csvf BAM.csv

# Step 3: Extract ShimCache from SYSTEM hive
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SYSTEM --kn "ControlSet001\Control\Session Manager\AppCompatCache" --csv C:\Cases\MyCase\Output\CSV --csvf ShimCache.csv

# Step 4: Extract UserAssist from NTUSER.DAT
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\NTUSER.DAT --kn "Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist" --csv C:\Cases\MyCase\Output\CSV --csvf UserAssist.csv
```

**Step 5: Correlate in Timeline Explorer**

| Artefact | Evidence Type | Timestamp Meaning | Correlation Key |
|---------|---------------|-------------------|----------------|
| **Prefetch** | Execution | Last 8 run times | `ExecutableName` |
| **BAM/DAM** | Execution | Last execution time (per user SID) | Full path + SID |
| **ShimCache** | File existence | File modified time (NOT execution) | Full path |
| **UserAssist** | Execution (GUI apps) | Last execution time + run count | Executable name (ROT13 decoded) |

Cross-referencing ShimCache (file created/modified), BAM (execution + SID), Prefetch (execution + run count), and UserAssist (execution + run count) around the same timestamp yields strong corroboration of execution by a specific user.

---

## Part 6: Custom Batch File Creation

### USB-Only Batch File

Create `USB_Triage.reb`:

```yaml
Description: USB device history extraction
Author: YourName
Version: 1.0
Id: USB_Triage_001
Keys:
  - Description: USB storage devices
    HiveType: SYSTEM
    Category: Devices
    KeyPath: ControlSet001\Enum\USBSTOR
    Recursive: true
    Comment: "VID, PID, serial number, FriendlyName"

  - Description: All USB devices
    HiveType: SYSTEM
    Category: Devices
    KeyPath: ControlSet001\Enum\USB
    Recursive: true
    Comment: "Includes non-storage USB devices"

  - Description: Mounted devices
    HiveType: SYSTEM
    Category: Devices
    KeyPath: MountedDevices
    Recursive: false
    Comment: "Drive letter to device mapping"
```

```powershell
RECmd.exe -f C:\Cases\MyCase\Evidence\Hives\SYSTEM --bn USB_Triage.reb --csv C:\Cases\MyCase\Output\CSV --csvf USB.csv
```

---

### Persistence-Only Batch File

Create `Persistence_Triage.reb`:

```yaml
Description: Persistence triage (Run keys + Services)
Author: YourName
Version: 1.0
Id: Persistence_Triage_001
Keys:
  - Description: Run keys (machine)
    HiveType: SOFTWARE
    Category: Persistence
    KeyPath: Microsoft\Windows\CurrentVersion\Run
    Recursive: false

  - Description: RunOnce keys (machine)
    HiveType: SOFTWARE
    Category: Persistence
    KeyPath: Microsoft\Windows\CurrentVersion\RunOnce
    Recursive: false

  - Description: Run keys (user)
    HiveType: NTUSER
    Category: Persistence
    KeyPath: Software\Microsoft\Windows\CurrentVersion\Run
    Recursive: false

  - Description: Services
    HiveType: SYSTEM
    Category: Persistence
    KeyPath: ControlSet001\Services
    Recursive: true
    Comment: "Check ImagePath for unusual binaries"
```

```powershell
RECmd.exe -d C:\Cases\MyCase\Evidence\Hives --bn Persistence_Triage.reb --csv C:\Cases\MyCase\Output\CSV --csvf Persistence_Quick.csv
```

---

## Part 7: Final Checklist

**Pre-Analysis:**
- [ ] RECmd.exe version verified (run `RECmd.exe` with no args)
- [ ] Batch files updated (`RECmd.exe --sync`)
- [ ] Hive files copied to evidence folder
- [ ] Transaction logs (`.LOG1`, `.LOG2`) present alongside hives
- [ ] Output directory created

**Triage Execution:**
- [ ] Run DFIRBatch against all hives
- [ ] Open CSV in Timeline Explorer
- [ ] Filter by Category: Program Execution, Persistence, User Activity, Devices
- [ ] Export high-priority findings to report

**Deep Dive:**
- [ ] SAM: User accounts, logon times, RIDs
- [ ] SECURITY: Audit policies (limited offline value)
- [ ] SOFTWARE: OS info, Run keys, ProfileList, installed software
- [ ] SYSTEM: USB devices, ShimCache, BAM/DAM, services, timezone
- [ ] NTUSER.DAT: UserAssist, RecentDocs, ShellBags, searches, typed paths

**Recovery & Correlation:**
- [ ] Verify transaction logs replayed (`--nl false`)
- [ ] Recover deleted keys/values (`--recover true`)
- [ ] Search slack space for deleted data (`--ss`)
- [ ] Parse VSS snapshots if available (`--vss`)
- [ ] Correlate with PECmd prefetch output
- [ ] Build execution timeline (Prefetch + BAM/DAM + UserAssist + ShimCache)

**Quality Assurance:**
- [ ] CSV row counts reasonable (not empty)
- [ ] Timestamps in expected range (not year 1601 or 9999)
- [ ] Timezone verified (SYSTEM\TimeZoneInformation)
- [ ] Multiple NTUSER.DAT files processed (multi-user systems)
- [ ] BAM/DAM SIDs mapped to usernames (via ProfileList)

---

## Quick Command Summary

```powershell
# TRIAGE: All hives, DFIRBatch, UK timestamps
RECmd.exe -d <HIVES_DIR> --bn BatchExamples\DFIRBatch.reb --csv <OUT_DIR> --csvf Triage.csv --q --dt "dd/MM/yyyy HH:mm:ss"

# SINGLE HIVE: SOFTWARE example
RECmd.exe -f <HIVES_DIR>\SOFTWARE --csv <OUT_DIR> --csvf SOFTWARE.csv --dt "dd/MM/yyyy HH:mm:ss"

# PERSISTENCE: RegistryASEPs batch
RECmd.exe -d <HIVES_DIR> --bn BatchExamples\RegistryASEPs.reb --csv <OUT_DIR> --csvf Persistence.csv

# USB DEVICES: Extract from SYSTEM
RECmd.exe -f <HIVES_DIR>\SYSTEM --kn "ControlSet001\Enum\USBSTOR" --csv <OUT_DIR> --csvf USB.csv

# BAM EXECUTION: Extract from SYSTEM (Win10 1709+)
RECmd.exe -f <HIVES_DIR>\SYSTEM --kn "ControlSet001\Services\bam\State\UserSettings" --csv <OUT_DIR> --csvf BAM.csv

# USERASSIST: Extract from NTUSER.DAT
RECmd.exe -f <HIVES_DIR>\NTUSER.DAT --kn "Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist" --csv <OUT_DIR> --csvf UserAssist.csv

# SEARCH: Keyword across all hives
RECmd.exe -d <HIVES_DIR> --sd "malware.exe" --csv <OUT_DIR> --csvf Search.csv

# RECOVERY: Clean dirty hive with transaction logs
RECmd.exe -f <HIVES_DIR>\SYSTEM --nl false --recover true --csv <OUT_DIR> --csvf SYSTEM_recovered.csv

# RLA: Create clean hive from transaction logs
RLA.exe -f <HIVES_DIR>\SYSTEM --out <HIVES_DIR>\Clean
```

**Sources:**
- RECmd GitHub: https://github.com/EricZimmerman/RECmd
- Eric Zimmerman Tools: https://ericzimmerman.github.io/
- SANS Windows Forensics Poster: https://www.sans.org/posters/windows-forensic-analysis/
