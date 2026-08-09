---
title: "Digital Forensics"
description: "Cross-platform DFIR reference: acquisition, triage, artifacts, timelines and analysis commands."
category: dfir
tags: [dfir, forensics, incident-response]
tools: [Autopsy, Sleuth Kit, plaso]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:DFIR/Forensics Cheatsheet.md"
---

# Digital Forensics

---

> **Note —** - 📋 Quick Reference Cheat Sheet
> 
> **Comprehensive forensic tool commands and workflows for Windows incident response.**
> 
> | # | Tool | Primary Use Case | Key Command | Notes |
> |:--|:---|:---|:---|:---|
> | 1 | **Volatility 3** | Memory forensics | `vol3 -f mem.bin windows.malfind` | Code injection detection |
> | 2 | **MemProcFS** | Memory virtual filesystem | `memprocfs.exe -device mem.bin -forensic 1` | Browse memory as files |
> | 3 | **CAPA** | Malware capability detection | `capa malware.exe` | Identifies malware behaviours |
> | 4 | **YARA** | Pattern matching | `yara -r rules.yar directory/` | Signature-based detection |
> | 5 | **PECmd** | Prefetch parsing | `PECmd.exe -d prefetch_dir --csv output/` | Execution evidence |
> | 6 | **EvtxECmd** | Event log parsing | `EvtxECmd.exe -f Security.evtx --csv output/` | Windows event logs |
> | 7 | **RECmd** | Registry parsing | `RECmd.exe -f SOFTWARE --bn batch.reb --csv output/` | Registry hive analysis |
> | 8 | **AppCompatCacheParser** | ShimCache parsing | `AppCompatCacheParser.exe -f SYSTEM --csv output/` | Execution history |
> | 9 | **AmcacheParser** | Amcache parsing | `AmcacheParser.exe -f Amcache.hve --csv output/` | SHA1 hashes + paths |
> | 10 | **Hayabusa** | SIGMA threat hunting | `hayabusa csv-timeline -d evtx_dir -o timeline.csv` | Rapid log analysis |
> | 11 | **Chainsaw** | Log hunting | `chainsaw hunt evtx_dir -s sigma_rules/` | SIGMA-based detection |
> | 12 | **KAPE** | Artifact collection | `kape.exe --tsource C: --tdest D:\Evidence --target KapeTriage` | Rapid triage |
> | 13 | **Timeline Explorer** | CSV visualization | GUI application | Large CSV analysis |
> | 14 | **CertUtil** | Hash calculation | `certutil -hashfile file SHA256` | Evidence integrity |
> 
> ---
> 
> **Key Definitions:**
> 1. **Prefetch**: Windows execution tracking files storing program run history and file access patterns
> 2. **ShimCache**: Application Compatibility Cache tracking executed programs in SYSTEM registry
> 3. **Amcache**: Registry hive containing program execution metadata including SHA1 hashes
> 4. **Malfind**: Volatility plugin detecting code injection via memory protection anomalies
> 5. **SIGMA Rules**: Generic signature format for log events translated to multiple SIEM formats
> 6. **RWX Memory**: Read-Write-Execute memory regions indicating potential code injection
> 7. **YARA**: Pattern matching tool using rules to identify malware families
> 8. **DFIR**: Digital Forensics and Incident Response
> 9. **EZ Tools**: Suite of forensic parsers by Eric Zimmerman (SANS)
> 10. **Triage**: Rapid evidence collection and initial analysis

---

## Tool Source Credibility

This guide integrates tools from **[SANS Institute](https://www.sans.org/tools)**, containing 100+ cybersecurity utilities maintained by recognized experts.

**[Eric Zimmerman](https://ericzimmerman.github.io)** (former FBI Special Agent, SANS Principal Instructor) authored the majority of Windows artifact parsers referenced herein. **[Rob T. Lee](https://www.sans.org/profiles/robert-lee/)** (SANS Chief AI Officer) created the **[SIFT Workstation](https://www.sans.org/tools/sift-workstation)**, a comprehensive Ubuntu-based forensic distribution.

**Tool Selection Criteria**:
1. Active maintenance by recognized DFIR experts
2. Wide adoption by law enforcement and enterprise security teams
3. Free and open-source architecture enabling verification
4. Designed for forensic soundness and court-admissible evidence
5. Cross-platform compatibility where applicable

---

## Memory Forensics Fundamentals

**Memory forensics** extracts digital artifacts from volatile memory (**[RAM](https://en.wikipedia.org/wiki/Random-access_memory)**) snapshots captured during or after incidents. Memory contains evidence unavailable on disk: running processes, network connections, injected code, decrypted data, and cryptographic keys.

**Process injection** techniques (**[MITRE T1055](https://attack.mitre.org/techniques/T1055/)**) hide malicious code within legitimate processes, detectable via memory analysis. **[Cobalt Strike](https://www.cobaltstrike.com/)** Beacons commonly use reflective DLL injection into legitimate Windows processes (explorer.exe, svchost.exe).

Memory analysis requires acquisition tools like **[WinPMEM](https://github.com/Velocidex/WinPmem)**, **[DumpIt](https://www.magnetforensics.com/)**, or **[FTK Imager](https://www.exterro.com/ftk-imager)** to create forensically sound memory dumps. Memory dumps range from 4GB to 64GB+ depending on system RAM, requiring sufficient storage and processing capacity.

---

## Memory Analysis Tools

### Volatility 3

**Purpose:** Advanced memory forensics framework for extracting digital artifacts from volatile memory (RAM) dumps. Industry-standard tool supporting Windows, Linux, and macOS.

**Source:** [Volatility Foundation](https://github.com/volatilityfoundation/volatility3)

**Platforms:** Windows, Linux, macOS

**Installation:**
```bash
# Linux/macOS
pip3 install volatility3

# Windows
pip install volatility3

# From source
git clone https://github.com/volatilityfoundation/volatility3.git
cd volatility3
pip3 install -r requirements.txt
python3 setup.py install
```

**Usage:**
```bash
# Identify memory image profile (auto-detection in Vol3)
vol3 -f <memory.bin> windows.info

# Process enumeration
vol3 -f <memory.bin> windows.pslist
vol3 -f <memory.bin> windows.pstree
vol3 -f <memory.bin> windows.cmdline

# Code injection detection (critical for Cobalt Strike detection)
vol3 -f <memory.bin> windows.malfind
vol3 -f <memory.bin> windows.malfind --pid <PID>

# Dump suspicious memory regions
vol3 -f <memory.bin> -o <output_dir> windows.malfind --dump

# Network connections
vol3 -f <memory.bin> windows.netscan
vol3 -f <memory.bin> windows.netstat

# DLL analysis
vol3 -f <memory.bin> windows.dlllist --pid <PID>
vol3 -f <memory.bin> windows.ldrmodules

# Handle analysis
vol3 -f <memory.bin> windows.handles --pid <PID>

# YARA scanning integration
vol3 -f <memory.bin> windows.vadyarascan --yara-file <rules.yar>
```

**Use Cases:**
1. Detect process injection techniques (reflective DLL injection, process hollowing)
2. Identify Cobalt Strike Beacons via malfind RWX memory regions
3. Extract network connections to C2 infrastructure
4. Recover command-line arguments revealing encoded payloads
5. Identify loaded drivers and kernel modules

**Integration:**
1. Output can be piped to `grep`, `awk`, or Timeline Explorer
2. Combine with YARA rules for signature-based detection
3. Results can feed into timeline analysis with Plaso

---

> **Note —** - Practical Application: Volatility 3 Memory Analysis
> 
> **Context**: Initial triage of memory dump to identify suspicious processes and code injection.
> 
> ```bash
> # Step 1: Verify memory dump and identify system profile
> vol3 -f memory.bin windows.info
> ```
> 
> ```plaintext
> Volatility 3 Framework 2.5.0
> 
> Variable        Value
> Kernel Base     0xf8000xxxxx
> DTB             0x1ab000
> Symbols         ntkrnlmp.pdb
> Is64Bit         True
> IsPAE           False
> layer_name      0 WindowsIntel32e
> memory_layer    1 FileLayer
> KdVersionBlock  0xf80002xxxxxx
> Major/Minor     15.19041
> MachineType     34404
> KeNumberProcessors      4
> SystemTime      2024-01-15 14:23:45
> ```
> 
> **Output Analysis:**
> 1. **Kernel Base**: Memory address of Windows kernel—validates dump integrity
> 2. **DTB (Directory Table Base)**: Physical address of page directory for virtual memory translation
> 3. **Is64Bit**: Confirms architecture (x64 vs x86)
> 4. **Major/Minor 15.19041**: Windows 10 Build 19041 (Version 2004)
> 5. **SystemTime**: Timestamp when memory dump was created

---

**Process Enumeration:**

```bash
# List all processes
vol3 -f memory.bin windows.pslist > pslist.txt

# Generate process tree showing parent-child relationships
vol3 -f memory.bin windows.pstree > pstree.txt

# Extract command-line arguments (reveals PowerShell encoded commands)
vol3 -f memory.bin windows.cmdline > cmdline.txt
```

**Example Output:**
```plaintext
PID     PPID    ImageFileName   Offset(V)       Threads Handles SessionId       Wow64   CreateTime      ExitTime

4       0       System          0x8a0ba1c0      152     -       N/A     False   2024-01-15 08:00:00.000000      N/A
392     4       smss.exe        0x8b3c4040      2       -       N/A     False   2024-01-15 08:00:01.000000      N/A
512     504     csrss.exe       0x8e2a8580      9       -       0       False   2024-01-15 08:00:03.000000      N/A
1432    1424    explorer.exe    0x8f1a2080      45      -       1       False   2024-01-15 08:05:12.000000      N/A
2856    1432    powershell.exe  0x9a4b3580      12      -       1       False   2024-01-15 14:15:33.000000      N/A
3104    2856    whoami.exe      0x9c2e1040      0       -       1       False   2024-01-15 14:15:41.000000      2024-01-15 14:15:42
```

**Key Fields:**
- **PID**: Process ID—unique identifier
- **PPID**: Parent Process ID—reveals process spawning relationships
- **ImageFileName**: Executable name
- **CreateTime**: Process start timestamp
- **SessionId**: User session (0=System, 1+=User sessions)

**Red Flags:**
1. Single-character executable names (a.exe, x.exe)
2. Processes spawning from temp directories
3. PowerShell spawned by unexpected parents (winword.exe, excel.exe)
4. Multiple PowerShell instances with short lifespans

---

**Code Injection Detection:**

```bash
# Detect injected code via memory protection anomalies
vol3 -f memory.bin windows.malfind > malfind.txt

# Dump suspicious memory regions for analysis
vol3 -f memory.bin -o dumps/ windows.malfind --dump

# Target specific suspicious process
vol3 -f memory.bin windows.malfind --pid 2856
```

**Example Output:**
```plaintext
PID     Process         Start VPN       End VPN         Tag     Protection      CommitCharge    PrivateMemory   File output     Hexdump Disasm

2856    powershell.exe  0x2a40000       0x2a70000       VadS    PAGE_EXECUTE_READWRITE  192     1       Disabled        
4d 5a 90 00 03 00 00 00 04 00 00 00 ff ff 00 00 MZ..............
b8 00 00 00 00 00 00 00 40 00 00 00 00 00 00 00 ........@.......
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ................
00 00 00 00 00 00 00 00 00 00 00 00 f8 00 00 00 ................

0x2a40000:      MZ      ; PE header signature
0x2a40040:      PUSH RBP
0x2a40041:      MOV RBP, RSP
0x2a40044:      SUB RSP, 0x20
```

**Indicators of Compromise:**
1. **PAGE_EXECUTE_READWRITE**: RWX permissions—rare in legitimate code, common in injected payloads
2. **MZ header (0x4d5a)**: PE file signature indicating reflective DLL injection
3. **VadS tag**: Private memory allocation via VirtualAlloc—common injection technique
4. **Disassembly shows prologue**: Standard x64 function prologue suggesting shellcode

**Next Steps:**
1. Dump flagged regions: `vol3 -f mem.bin -o dumps/ windows.malfind --dump`
2. Analyze with CAPA: `capa dumps/pid.2856.vad.0x2a40000-0x2a70000.dmp`
3. Scan with YARA: `yara cobalt_strike.yar dumps/`
4. Extract strings: `strings -el dumps/*.dmp | grep -i "http\|sleep\|pipe"`

---

**Network Connection Analysis:**

```bash
# Extract all network connections (TCP/UDP)
vol3 -f memory.bin windows.netscan > netscan.txt

# Alternative plugin for different Windows versions
vol3 -f memory.bin windows.netstat > netstat.txt
```

**Example Output:**
```plaintext
Offset          Proto   LocalAddr       LocalPort       ForeignAddr     ForeignPort     State           PID     Owner   Created

0x9b2a4580      TCPv4   192.168.1.135   49823           185.220.101.5   443             ESTABLISHED     2856    powershell.exe  2024-01-15 14:15:35.000000
0x9c1e3040      TCPv4   192.168.1.135   49824           10.10.10.100    445             ESTABLISHED     4       System  2024-01-15 14:18:12.000000
0x9d4f1280      UDPv4   0.0.0.0         53              *               0                               1024    svchost.exe     2024-01-15 08:05:00.000000
```

**Investigation Actions:**
1. **185.220.101.5:443 from powershell.exe**: Suspicious HTTPS connection—potential C2 communication
2. **10.10.10.100:445 from System**: SMB connection indicating lateral movement or file sharing
3. Correlate foreign IPs with threat intelligence ([VirusTotal](https://www.virustotal.com/), [AbuseIPDB](https://www.abuseipdb.com/))
4. Check **Event ID 3** ([Sysmon](https://docs.microsoft.com/en-us/sysinternals/downloads/sysmon) Network Connection) for additional context

---

### MemProcFS

**Purpose:** Revolutionary memory forensics tool mounting physical memory as a virtual file system, enabling intuitive navigation of memory artifacts using standard file browsers and command-line tools.

**Source:** [MemProcFS GitHub](https://github.com/ufrisk/MemProcFS)

**Platforms:** Windows (primary), Linux (partial support)

**Prerequisites:**
- Dokany File System Library (Windows): [Dokany Releases](https://github.com/dokan-dev/dokany/releases)

**Installation:**
```bash
# Windows - Download pre-compiled binaries
# https://github.com/ufrisk/MemProcFS/releases

# Install Dokany first (required for mounting)
# Download DokanSetup.exe from Dokany releases

# Extract MemProcFS and run from directory
```

**Usage:**
```cmd
:: Basic mount (default M: drive)
memprocfs.exe -device <memory.bin>

:: Mount with forensic mode (enables timeline, MFT extraction, NTFS analysis)
memprocfs.exe -device <memory.bin> -forensic 1

:: Mount with Elastic YARA rules
memprocfs.exe -device <memory.bin> -forensic 1 -license-accept-elastic-license-2.0

:: Custom YARA rules
memprocfs.exe -device <memory.bin> -forensic 1 -forensic-yara-rules <rules.yar>

:: With pagefile support
memprocfs.exe -device <memory.bin> -pagefile0 pagefile.sys -pagefile1 swapfile.sys

:: Live memory analysis (with WinPMEM driver)
memprocfs.exe -device pmem
```

---

> **Note —** - Virtual File System Structure
> 
> **Key Directories After Mounting:**
> 
> | Directory Path | Contents | Forensic Value |
> |:--|:--|:--|
> | `M:\forensic\csv\` | CSV exports (pslist, findevil, ntfs) | Import to Timeline Explorer |
> | `M:\forensic\findevil\` | Automated malware detection results | Quick IOC identification |
> | `M:\forensic\timeline\` | Process and activity timelines | Temporal analysis |
> | `M:\forensic\yara\` | YARA scan results | Signature-based detection |
> | `M:\forensic\ntfs\` | Reconstructed NTFS from memory | File system artifacts |
> | `M:\name\<process.exe-PID>\` | Process-specific artifacts | Per-process deep dive |
> | `M:\name\<process>\vmemd\` | Virtual memory dumps | Extract injected code |
> | `M:\registry\hive_files\` | Extracted registry hives | Offline registry analysis |
> | `M:\registry\HKLM\` | HKEY_LOCAL_MACHINE keys | System-wide settings |
> | `M:\registry\HKCU\` | HKEY_CURRENT_USER keys | User-specific settings |
> | `M:\sys\net\netstat.txt` | Network connections | C2 detection |
> | `M:\sys\proc\pslist.txt` | Process list | Quick process review |
> | `M:\pid\<PID>\` | Process by PID | Direct PID access |

**Workflow Example:**
1. Review `M:\forensic\findevil\findevil.txt` for automated IOC hits
2. Open `M:\forensic\csv\findevil.csv` in Timeline Explorer
3. Navigate to flagged process: `M:\name\powershell.exe-2856\`
4. Review `cmdline.txt` for command-line arguments
5. Check `M:\sys\net\netstat.txt` for network connections from PID 2856
6. Copy registry hives from `M:\registry\hive_files\` to working directory
7. Analyze with `RECmd.exe -f M:\registry\hive_files\SOFTWARE --bn batch.reb`

---

### CAPA

**Purpose:** Automated malware capability identification tool by Mandiant/FLARE team. Identifies program capabilities by analyzing code against a rule set of known malicious behaviors, mapping findings to [MITRE ATT&CK](https://attack.mitre.org/).

**Source:** [CAPA GitHub](https://github.com/mandiant/capa)

**Platforms:** Windows, Linux, macOS

**Installation:**
```bash
# Python installation
pip install flare-capa

# Download standalone executable
# https://github.com/mandiant/capa/releases
```

**Usage:**
```bash
# Basic analysis of executable
capa <malware.exe>

# Verbose output showing matched rules
capa -v <malware.exe>

# Very verbose (shows matched code locations)
capa -vv <malware.exe>

# Output as JSON for parsing
capa -j <malware.exe> > capa_results.json

# Analyse shellcode
capa -f sc32 <shellcode.bin>    # 32-bit shellcode
capa -f sc64 <shellcode.bin>    # 64-bit shellcode

# Analyse memory dump regions extracted from malfind
capa <malfind_dump.dmp>

# Specify rules directory
capa -r <rules_directory> <sample.exe>
```

**Example Output:**
```
+------------------------+----------------------------+
| ATT&CK Tactic          | ATT&CK Technique           |
|------------------------+----------------------------|
| DEFENSE EVASION        | Obfuscated Files or Info   |
| EXECUTION              | Command and Scripting      |
| PERSISTENCE            | Registry Run Keys          |
| PRIVILEGE ESCALATION   | Process Injection          |
| COLLECTION             | Screen Capture             |
| COMMAND AND CONTROL    | Encrypted Channel          |
+------------------------+----------------------------+

+-----------------------------+------------------------------+
| Capability                  | Namespace                    |
|-----------------------------+------------------------------|
| encode data using XOR       | data-manipulation/encoding   |
| receive data on TCP socket  | communication/tcp/receive    |
| create process              | host-interaction/process     |
| inject code into remote     | host-interaction/process/    |
| process                     | inject                       |
| create registry key         | host-interaction/registry    |
| capture screenshot          | collection/screenshot        |
| contain PE file             | executable/pe                |
+-----------------------------+------------------------------+
```

**Cobalt Strike Indicators:**
1. Network socket creation (TCP/UDP)
2. Process injection capabilities
3. Named pipe creation (`\\.\pipe\msagent_*`)
4. XOR encoding
5. Sleep/jitter implementation

---

### YARA

**Purpose:** Pattern matching tool for identifying and classifying malware based on textual or binary patterns. De facto standard for malware signature creation used by VirusTotal, AV vendors, and DFIR teams.

**Source:** [YARA GitHub](https://github.com/VirusTotal/yara)

**Platforms:** Windows, Linux, macOS

**Installation:**
```bash
# Linux
sudo apt install yara

# macOS
brew install yara

# Windows - Download from releases
# https://github.com/VirusTotal/yara/releases

# Python bindings
pip install yara-python
```

**Usage:**
```bash
# Scan file with single rule
yara <rules.yar> <target_file>

# Scan directory recursively
yara -r <rules.yar> <target_directory>

# Scan with multiple rule files
yara <rules1.yar> <rules2.yar> <target>

# Print matching strings
yara -s <rules.yar> <target>

# Print metadata
yara -m <rules.yar> <target>

# Scan process memory (Linux)
yara <rules.yar> -p <PID>

# Fast mode (skip expensive scans)
yara -f <rules.yar> <target>
```

---

> **Note —** - Sample YARA Rule: Cobalt Strike Beacon Detection
> 
> ```yara
> rule CobaltStrike_Beacon_x64
> {
>     meta:
>         description = "Detects Cobalt Strike Beacon x64"
>         author = "SANS DFIR Team"
>         reference = "https://www.cobaltstrike.com"
>         severity = "high"
>         mitre_attack = "T1055, T1071"
>         
>     strings:
>         // x64 shellcode prologue
>         $magic_x64 = { FC 48 83 E4 F0 E8 }
>         
>         // Beacon configuration markers
>         $config_marker = { 00 01 00 01 00 02 }
>         
>         // Configuration strings
>         $sleeptime = "sleeptime" ascii
>         $jitter = "jitter" ascii
>         $watermark = "watermark" ascii
>         $spawnto_x86 = "spawnto_x86" ascii
>         $spawnto_x64 = "spawnto_x64" ascii
>         
>         // Named pipe pattern
>         $pipe = "\\\\.\\pipe\\" ascii
>         $msagent_pipe = "msagent_" ascii
>         
>         // HTTP headers
>         $http_header = "User-Agent:" ascii
>         $http_header2 = "Accept:" ascii
>         
>         // Beacon DLL names
>         $beacon_dll = "beacon.dll" ascii nocase
>         $beacon_x64 = "beacon.x64.dll" ascii nocase
>         
>     condition:
>         uint16(0) == 0x5A4D and  // MZ header
>         (
>             $magic_x64 or
>             (2 of ($config_marker, $sleeptime, $jitter, $watermark)) or
>             (all of ($pipe, $msagent_pipe)) or
>             any of ($beacon_dll, $beacon_x64)
>         )
> }
> 
> rule Reflective_DLL_Injection
> {
>     meta:
>         description = "Detects reflective DLL injection"
>         author = "SANS DFIR"
>         mitre_attack = "T1055.001"
>         
>     strings:
>         $mz = { 4D 5A }
>         
>         // Reflective loader signatures
>         $reflective_loader1 = { 48 8B C4 48 89 58 08 48 89 68 10 48 89 70 18 }
>         $reflective_loader2 = { 64 48 8B 04 25 60 00 00 00 }  // GS segment access
>         
>         // API resolution patterns
>         $getprocaddress = "GetProcAddress" ascii
>         $loadlibrary = "LoadLibraryA" ascii
>         $virtualalloc = "VirtualAlloc" ascii
>         
>     condition:
>         $mz at 0 and
>         (
>             any of ($reflective_loader*) or
>             (all of ($getprocaddress, $loadlibrary, $virtualalloc))
>         )
> }
> ```

**YARA Rule Best Practices:**
1. Always include metadata with ATT&CK mappings and severity
2. Test rules against benign software to minimize false positives
3. Use multiple string conditions for robustness
4. Include both specific and generic indicators
5. Document rule rationale in comments

**Integration with Volatility 3:**
```bash
# Scan all memory with YARA rules
vol3 -f memory.bin windows.vadyarascan --yara-file cobalt_strike.yar

# Scan specific process by PID
vol3 -f memory.bin windows.vadyarascan --yara-file rules.yar --pid 2856

# Multiple rule files
vol3 -f memory.bin yarascan.YaraScan --yara-file combined_rules.yar

# Output to file for analysis
vol3 -f memory.bin windows.vadyarascan --yara-file rules.yar > yara_hits.txt
```

---

## Prefetch Analysis Tools

### PECmd (Prefetch Explorer Command Line) 🔵 SANS Tool

**Purpose:** Parse Windows Prefetch files to extract program execution evidence, including run counts, timestamps, and accessed files/directories.

**Source:** [SANS PECmd](https://www.sans.org/tools/pecmd) | [Eric Zimmerman Tools](https://ericzimmerman.github.io)

**Author:** Eric Zimmerman (SANS Principal Instructor)

**Platforms:** Windows (native), Linux (via Wine/.NET)

**Installation:**
```powershell
# Windows - Download from Eric Zimmerman's GitHub
# https://ericzimmerman.github.io/#!index.md

# Use Get-ZimmermanTools PowerShell script for automated download
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri "https://f001.backblazeb2.com/file/EricZimmermanTools/Get-ZimmermanTools.zip" -OutFile Get-ZimmermanTools.zip
Expand-Archive Get-ZimmermanTools.zip
.\Get-ZimmermanTools.ps1 -Dest "C:\Tools\Zimmerman"

# Linux (requires .NET 6 runtime)
wget https://dot.net/v1/dotnet-install.sh
chmod +x dotnet-install.sh
./dotnet-install.sh --runtime dotnet --version 6.0.0
```

**Usage:**
```cmd
:: Parse single prefetch file
PECmd.exe -f <file.pf>

:: Parse directory of prefetch files with CSV output
PECmd.exe -d <prefetch_directory> --csv <output_dir> --csvf Prefetch_Results.csv

:: UK date formatting (dd/MM/yyyy HH:mm:ss)
PECmd.exe -d <prefetch_directory> --csv <output_dir> --csvf Prefetch.csv --dt "dd/MM/yyyy HH:mm:ss"

:: JSON output
PECmd.exe -d <prefetch_directory> --json <output_dir>

:: Quiet mode (faster processing)
PECmd.exe -d <prefetch_directory> --csv <output_dir> -q

:: Custom keyword highlighting (temp directories)
PECmd.exe -d <prefetch_directory> -k "temp,appdata,downloads"
```

**Expected Output:**
- `*_Prefetch.csv` - Main results with executable name, run count, last 8 run times
- `*_Prefetch_Timeline.csv` - Execution timeline for temporal analysis

**Key CSV Fields:**

|                |                                       |                               |
| -------------- | ------------------------------------- | ----------------------------- |
| Field          | Description                           | Forensic Value                |
| ExecutableName | Name of executed program              | Identify reconnaissance tools |
| RunCount       | Number of times program executed      | Frequency analysis            |
| LastRun        | Most recent execution timestamp       | Timeline correlation          |
| PreviousRun0-7 | Previous 7 execution timestamps       | Execution history             |
| SourceFilename | Full path to executable               | Location analysis             |
| FilesLoaded    | Files accessed during execution       | Payload identification        |
| Directories    | Directories accessed during execution | Drop location discovery       |

**Forensic Significance:**
1. Windows 10 stores last 8 execution times
2. Files/directories referenced reveal payload locations
3. Single-character executable names often indicate malware
4. Prefetch files survive across reboots

---

## Registry Analysis Tools

### RECmd (Registry Explorer Command Line) 🔵 SANS Tool

**Purpose:** Command-line registry parser with batch processing capabilities for extracting forensically significant data from Windows registry hive files.

**Source:** [SANS RECmd](https://www.sans.org/tools/recmd) | [Eric Zimmerman Tools](https://ericzimmerman.github.io)

**Author:** Eric Zimmerman

**Platforms:** Windows (native), Linux (via .NET)

**Usage:**
```cmd
:: Parse with batch file (recommended for comprehensive analysis)
RECmd.exe -f <registry_hive> --bn <batch_file.reb> --csv <output_dir> --csvf Results.csv

:: Common batch files:
:: - RECmd_Batch_MC.reb (Most Common artifacts)
:: - RegistryASEPs.reb (Auto-Start Extensibility Points)

:: Parse specific registry key
RECmd.exe -f SOFTWARE --kn "Microsoft\Windows\CurrentVersion\Run" --csv <output_dir>

:: Recover deleted entries
RECmd.exe -f <hive> --recover --csv <output_dir>

:: UK date format
RECmd.exe -f <hive> --bn <batch.reb> --csv <output_dir> --dt "dd/MM/yyyy HH:mm:ss"

:: Parse directory of hives
RECmd.exe -d <hive_directory> --bn <batch.reb> --csv <output_dir>
```

---

> **Note —** - Critical Registry Locations for DFIR
> 
> **Persistence Mechanisms (HKLM\SOFTWARE & NTUSER.DAT):**
> 
> | Registry Key | Hive | Purpose | Malware Usage |
> |:--|:--|:--|:--|
> | `Microsoft\Windows\CurrentVersion\Run` | SOFTWARE, NTUSER | Auto-start executables | **Primary persistence location** |
> | `Microsoft\Windows\CurrentVersion\RunOnce` | SOFTWARE, NTUSER | Run once then delete entry | Single-execution payloads |
> | `Microsoft\Windows\CurrentVersion\RunServices` | SOFTWARE | Run as service | Service-based persistence |
> | `Microsoft\Windows\CurrentVersion\Policies\Explorer\Run` | SOFTWARE, NTUSER | Policy-based execution | Policy enforcement bypass |
> | `Microsoft\Windows NT\CurrentVersion\Winlogon\Userinit` | SOFTWARE | Userinit override | Replace userinit.exe |
> | `Microsoft\Windows NT\CurrentVersion\Winlogon\Shell` | SOFTWARE | Shell override | Replace explorer.exe |
> | `Microsoft\Windows NT\CurrentVersion\Image File Execution Options` | SOFTWARE | Debugger attachment | IFEO persistence |
> 
> **Services (HKLM\SYSTEM):**
> 
> | Registry Key | Purpose |
> |:--|:--|
> | `ControlSet001\Services` | Installed services |
> | `ControlSet001\Services\<ServiceName>\ImagePath` | Service executable path |
> | `ControlSet001\Services\<ServiceName>\Start` | Start type (2=Auto, 3=Manual, 4=Disabled) |
> 
> **System Information (HKLM\SYSTEM):**
> 
> | Registry Key | Information |
> |:--|:--|
> | `ControlSet001\Control\ComputerName\ComputerName` | Computer name |
> | `ControlSet001\Control\TimeZoneInformation` | Timezone |
> | `ControlSet001\Services\Tcpip\Parameters\Interfaces` | Network interfaces |

---

### Registry Explorer 🔵 SANS Tool

**Purpose:** GUI-based registry hive viewer and editor with advanced parsing capabilities, plugin support, and deleted entry recovery.

**Source:** [Eric Zimmerman Tools](https://ericzimmerman.github.io)

**Author:** Eric Zimmerman

**Platforms:** Windows

**Usage:**
1. Launch Registry Explorer
2. File → Load Hive → Select registry hive file
3. Navigate to keys of interest
4. Use Bookmarks for common forensic locations
5. Export findings via File → Export

**Key Features:**
1. Handles dirty/corrupt hives from memory extraction
2. Shows deleted keys and values
3. Timestamps on all keys
4. Plugin support for specialized parsing
5. Bookmark system for common forensic keys

---

### AppCompatCacheParser 🔵 SANS Tool

**Purpose:** Parse Application Compatibility Cache (ShimCache) from SYSTEM registry hive to extract program execution evidence.

**Source:** [SANS AppCompatCacheParser](https://www.sans.org/tools/appcompatcacheparser) | [Eric Zimmerman Tools](https://ericzimmerman.github.io)

**Author:** Eric Zimmerman

**Usage:**
```cmd
:: Parse SYSTEM hive
AppCompatCacheParser.exe -f <SYSTEM_hive> --csv <output_dir> --csvf ShimCache.csv

:: UK date format
AppCompatCacheParser.exe -f <SYSTEM_hive> --csv <output_dir> --dt "dd/MM/yyyy HH:mm:ss"
```

**Forensic Significance:**
1. Contains executable path and last modification timestamp
2. Entry order reflects approximate execution order
3. Survives reboots (unlike prefetch which can be disabled)
4. Windows 7+ includes executed flag

**CSV Output Fields:**

|                        |                                     |                                             |
| ---------------------- | ----------------------------------- | ------------------------------------------- |
| Field                  | Description                         | Forensic Value                              |
| **CacheEntryPosition** | Position in cache (1 = most recent) | Relative execution order                    |
| **Path**               | Full executable path                | Identify execution location                 |
| **LastModified**       | File last modification timestamp    | File modification time (NOT execution time) |
| **Executed**           | Executed flag (Windows 7+)          | Confirms execution vs touched by Explorer   |
| **ControlSet**         | ControlSet number (001, 002)        | Validate active ControlSet                  |


---

### AmcacheParser 🔵 SANS Tool

**Purpose:** Parse Amcache.hve to extract program execution metadata including SHA1 hashes, file paths, and execution timestamps.

**Source:** [SANS AmcacheParser](https://www.sans.org/tools/amcacheparser) | [Eric Zimmerman Tools](https://ericzimmerman.github.io)

**Author:** Eric Zimmerman

**Usage:**
```cmd
:: Parse Amcache.hve
AmcacheParser.exe -f <Amcache.hve> --csv <output_dir> --csvf Amcache.csv

:: Include unassociated file entries
AmcacheParser.exe -f <Amcache.hve> --csv <output_dir> -i

:: UK date format
AmcacheParser.exe -f <Amcache.hve> --csv <output_dir> --dt "dd/MM/yyyy HH:mm:ss"
```

**Key Output Fields:**
1. SHA1 hash (for VirusTotal lookup)
2. File path
3. First execution timestamp
4. File size
5. Publisher information

**VirusTotal Batch Lookup:**
```powershell
# Extract SHA1 hashes from CSV
Import-Csv Amcache.csv | Select-Object -Unique SHA1 | Export-Csv -Path hashes_only.csv

# Lookup on VirusTotal (requires API key)
# Use vt-cli or web interface batch upload
```

---

## Event Log Analysis Tools

### EvtxECmd 🔵 SANS Tool

**Purpose:** Parse Windows Event Log files (.evtx) to CSV/JSON with extensive event mapping and filtering capabilities.

**Source:** [SANS EvtxECmd](https://www.sans.org/tools/evtxecmd) | [Eric Zimmerman Tools](https://ericzimmerman.github.io)

**Author:** Eric Zimmerman

**Usage:**
```cmd
:: Parse single event log
EvtxECmd.exe -f <Security.evtx> --csv <output_dir> --csvf Security.csv

:: Parse with UK date format
EvtxECmd.exe -f <Security.evtx> --csv <output_dir> --csvf Security.csv --dt "dd/MM/yyyy HH:mm:ss"

:: Parse directory of logs
EvtxECmd.exe -d <EventLogs_directory> --csv <output_dir>

:: JSON output
EvtxECmd.exe -f <Security.evtx> --json <output_dir>

:: Include maps for enriched parsing
EvtxECmd.exe -f <Security.evtx> --csv <output_dir> --maps <maps_directory>
```

---

> **Note —** - Critical Windows Event IDs Reference
> 
> **Security Log Events:**
> 
> | Event ID | Category | Description | Forensic Value |
> |:--|:--|:--|:--|
> | **4624** | Authentication | Successful logon | Identify user sessions, Type 3=Network, Type 10=RDP |
> | **4625** | Authentication | Failed logon | Brute force attempts, credential spraying |
> | **4672** | Privilege | Special privileges assigned | Administrator logon, SYSTEM access |
> | **4688** | Execution | Process creation | Command lines (if auditing enabled) |
> | **4648** | Authentication | Explicit credentials used | Lateral movement with `runas` or Pass-the-Hash |
> | **4768** | Kerberos | TGT requested | Initial authentication to domain controller |
> | **4769** | Kerberos | Service ticket requested | Kerberoasting detection |
> | **4776** | Authentication | NTLM authentication | Identify NTLM usage for lateral movement |
> | **1102** | Audit | Security log cleared | Anti-forensics, tampering |
> | **4720** | Account Management | User account created | Persistence, privilege escalation |
> | **4732** | Group Management | User added to local group | Privilege escalation (Administrators group) |
> 
> **System Log Events:**
> 
> | Event ID | Category | Description | Forensic Value |
> |:--|:--|:--|:--|
> | **7045** | Service | New service installed | Malware persistence, lateral movement tools |
> | **7040** | Service | Service start type changed | Persistence mechanism modification |
> | **104** | Audit | System log cleared | Anti-forensics |
> | **1** | Kernel | System boot | Establish system uptime, reboot timeline |
> | **6005** | Event Log | Event Log service started | System boot confirmation |
> | **6006** | Event Log | Event Log service stopped | System shutdown |
> 
> **PowerShell Operational Log:**
> 
> | Event ID | Category | Description | Forensic Value |
> |:--|:--|:--|:--|
> | **4103** | Pipeline | Module logging | Commands executed via PowerShell |
> | **4104** | Script Block | Script block logging | Full PowerShell script content |
> | **4105** | Script Start | Script execution started | Script start timestamp |
> | **4106** | Script Stop | Script execution stopped | Script end timestamp |

**Logon Type Reference (Event ID 4624):**

| Type | Name | Description | Attack Relevance |
|:--|:--|:--|:--|
| **2** | Interactive | Local console logon | Physical or console access |
| **3** | Network | Network logon (SMB, file shares) | **Lateral movement primary indicator** |
| **4** | Batch | Scheduled task | Persistence via scheduled tasks |
| **5** | Service | Service logon | Malicious service installation |
| **7** | Unlock | Workstation unlock | User activity tracking |
| **10** | RemoteInteractive | RDP/Terminal Services | **Remote access, lateral movement** |
| **11** | CachedInteractive | Logon with cached credentials | Offline authentication |

---

### Hayabusa

**Purpose:** SIGMA-based threat hunting and fast forensics timeline generator for Windows event logs.

**Source:** [Hayabusa GitHub](https://github.com/Yamato-Security/hayabusa)

**Platforms:** Windows, Linux, macOS

**Installation:**
```bash
# Download pre-compiled binary
# https://github.com/Yamato-Security/hayabusa/releases

# Or compile from source
git clone https://github.com/Yamato-Security/hayabusa.git
cd hayabusa
cargo build --release
```

**Usage:**
```bash
# Run against event logs directory
hayabusa csv-timeline -d <evtx_directory> -o timeline.csv

# With SIGMA rules
hayabusa csv-timeline -d <evtx_directory> -o timeline.csv --enable-all-rules

# JSON output
hayabusa json-timeline -d <evtx_directory> -o timeline.json

# Metrics summary
hayabusa metrics -d <evtx_directory>
```

**Example Output:**
```plaintext
Hayabusa v2.7.0 - Fast Windows Event Log Forensics Timeline Generator

Loading detection rules...
Loaded 3,245 SIGMA rules

Processing event logs in D:\Evidence\EventLogs\LAPTOP-135

Found event logs:
  Security.evtx (15,234 events)
  System.evtx (8,456 events)
  Microsoft-Windows-PowerShell%4Operational.evtx (1,234 events)
  Microsoft-Windows-Sysmon%4Operational.evtx (3,456 events)

Processing events... ████████████████████ 100%

Detection Summary:
  Total events processed: 28,380
  Detections: 127
    Critical: 5
    High: 23
    Medium: 67
    Low: 32

Timeline saved to: D:\Output\hayabusa_timeline.csv

Top 5 Detections:
  1. PowerShell Base64 Encoded Command (12 hits)
  2. Suspicious Process Creation Chain (8 hits)
  3. Network Connection to Suspicious IP (5 hits)
  4. Credential Dumping via LSASS Access (3 hits)
  5. Lateral Movement via PSExec (2 hits)
```

**Key Detections for Cobalt Strike:**
1. **PowerShell Base64 Encoded Command**: Encoded payload execution
2. **Process Creation with Suspicious Command Line**: Reconnaissance tools
3. **Network Connection from Script Host**: C2 beaconing from PowerShell
4. **Suspicious Named Pipe Creation**: Beacon named pipes (`\\.\pipe\msagent_*`)
5. **LSASS Memory Access**: Credential dumping
6. **PSExec Service Installation**: Lateral movement

---

### Chainsaw

**Purpose:** Rapidly search and hunt through Windows event logs using SIGMA detection rules and custom Chainsaw queries.

**Source:** [Chainsaw GitHub](https://github.com/WithSecureLabs/chainsaw)

**Platforms:** Windows, Linux, macOS

**Installation:**
```bash
# Download from releases
# https://github.com/WithSecureLabs/chainsaw/releases

# Or cargo install
cargo install chainsaw
```

**Usage:**
```bash
# Hunt with SIGMA rules
chainsaw hunt <evtx_directory> -s <sigma_rules> --mapping <mapping.yml>

# Search for specific strings
chainsaw search <evtx_directory> -s "powershell" -s "mimikatz"

# Dump all events to JSON
chainsaw dump <evtx_directory> -o output.json
```

---

## Cross-Platform Supporting Tools

### SIFT Workstation 🔵 SANS Tool

**Purpose:** Complete Ubuntu-based forensic distribution with pre-installed tools for incident response and digital forensics.

**Source:** [SANS SIFT Workstation](https://www.sans.org/tools/sift-workstation)

**Author:** Rob T. Lee (SANS Chief AI Officer)

**Platforms:** Ubuntu Linux (VM recommended)

**Installation:**
```bash
# Method 1: Download OVA/VMware image from SANS
# https://www.sans.org/tools/sift-workstation

# Method 2: Install on existing Ubuntu
wget https://github.com/teamdfir/sift-cli/releases/download/v1.14.0/sift-cli-linux
chmod +x sift-cli-linux
sudo ./sift-cli-linux install

# Default credentials
# Username: sansforensics
# Password: forensics
```

**Included Tools:**
1. Volatility Framework
2. The Sleuth Kit & Autopsy
3. Eric Zimmerman's Tools
4. Plaso/Log2Timeline
5. RegRipper
6. Bulk Extractor
7. And 100+ additional forensic utilities

---

### KAPE (Kroll Artifact Parser and Extractor) 🔵 SANS Tool

**Purpose:** Triage tool for rapid collection and processing of forensic artifacts. Combines targeted collection (Targets) with automated processing (Modules).

**Source:** [SANS KAPE](https://www.sans.org/tools/kape) | [Kroll KAPE](https://www.kroll.com/en/services/cyber-risk/incident-response-litigation-support/kroll-artifact-parser-extractor-kape)

**Author:** Eric Zimmerman

**Platforms:** Windows

**Installation:**
```powershell
# Download from Kroll website (requires registration)
# https://www.kroll.com/en/services/cyber-risk/kape

# Sync with GitHub for latest targets/modules
kape.exe --sync
```

**Usage:**
```cmd
:: Collect common triage artifacts
kape.exe --tsource C: --tdest D:\Evidence --target KapeTriage

:: Process collected artifacts
kape.exe --msource D:\Evidence --mdest D:\Processed --module !EZParser

:: Collect and process in one command
kape.exe --tsource C: --tdest D:\Evidence --target KapeTriage --mdest D:\Processed --module !EZParser

:: Specific target collection
kape.exe --tsource C: --tdest D:\Evidence --target Prefetch,EventLogs,Registry
```

**Common Targets:**
1. `KapeTriage` - Comprehensive triage collection
2. `Prefetch` - Prefetch files
3. `EventLogs` - Windows Event Logs
4. `Registry` - Registry hives
5. `AmcacheAndShimcache` - Execution evidence

---

### Timeline Explorer 🔵 SANS Tool

**Purpose:** Advanced CSV and Excel viewer designed for forensic timeline analysis with filtering, grouping, and visualization capabilities.

**Source:** [Eric Zimmerman Tools](https://ericzimmerman.github.io)

**Author:** Eric Zimmerman

**Platforms:** Windows

**Usage:**
1. Launch Timeline Explorer
2. Open CSV file (supports drag-and-drop)
3. Use column filters to narrow results
4. Group by columns for pattern identification
5. Tag interesting rows with Ctrl+T
6. Export filtered results

**Key Features:**
1. Handles very large CSV files
2. Column-based filtering
3. Row grouping and expansion
4. Conditional formatting
5. Persistent column configurations
6. Native date/time parsing

---

### Plaso/Log2Timeline 🔵 SANS Tool

**Purpose:** Super timeline creation tool that extracts timestamps from various artifact sources and aggregates them into a unified timeline.

**Source:** [Plaso GitHub](https://github.com/log2timeline/plaso)

**Platforms:** Linux, Windows, macOS

**Installation:**
```bash
# Linux (Ubuntu/Debian)
sudo add-apt-repository ppa:gift/stable
sudo apt update
sudo apt install plaso-tools

# Docker
docker pull log2timeline/plaso

# pip
pip install plaso
```

**Usage:**
```bash
# Create timeline from disk image
log2timeline.py --parsers win7 timeline.plaso <evidence_image>

# Process to CSV
psort.py -o l2tcsv timeline.plaso -w supertimeline.csv

# Filter by date range
psort.py timeline.plaso "date > '2024-01-01' AND date < '2024-01-31'" -w filtered.csv
```

---

### CertUtil (Windows Built-in)

**Purpose:** Windows certificate utility that includes hash calculation capabilities for evidence integrity verification.

**Platforms:** Windows (built-in)

**Usage:**
```cmd
:: Generate SHA-256 hash
certutil -hashfile <file> SHA256

:: Generate MD5 hash
certutil -hashfile <file> MD5

:: Batch hash all files recursively
forfiles /s /c "cmd /c certutil -hashfile @path SHA256 >> all_hashes.txt"
```

---

## Investigation Workflows

### Workflow 1: Memory Dump Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEMORY DUMP ANALYSIS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. EVIDENCE INTEGRITY                                         │
│     ├── certutil -hashfile memory.bin SHA256                   │
│     └── Document hash in chain of custody                      │
│                                                                 │
│  2. INITIAL TRIAGE (Choose One)                                │
│     ├── MemProcFS: memprocfs.exe -device memory.bin -forensic 1│
│     │   └── Browse M:\forensic\findevil.txt for quick IOCs     │
│     └── Volatility: vol3 -f memory.bin windows.info            │
│                                                                 │
│  3. PROCESS ANALYSIS                                           │
│     ├── vol3 -f memory.bin windows.pslist > pslist.txt         │
│     ├── vol3 -f memory.bin windows.pstree > pstree.txt         │
│     └── vol3 -f memory.bin windows.cmdline > cmdline.txt       │
│                                                                 │
│  4. CODE INJECTION DETECTION                                   │
│     ├── vol3 -f memory.bin windows.malfind > malfind.txt       │
│     ├── vol3 -f memory.bin -o dumps windows.malfind --dump     │
│     └── Look for: RWX permissions, MZ headers, shellcode       │
│                                                                 │
│  5. NETWORK ANALYSIS                                           │
│     ├── vol3 -f memory.bin windows.netscan > netscan.txt       │
│     └── Correlate connections with suspicious processes        │
│                                                                 │
│  6. MALWARE CAPABILITY ANALYSIS                                │
│     ├── capa <malfind_dump.bin> > capabilities.txt             │
│     └── yara cobalt_strike.yar <malfind_dump.bin>              │
│                                                                 │
│  7. DLL & HANDLE ANALYSIS                                      │
│     ├── vol3 -f memory.bin windows.dlllist --pid <suspicious>  │
│     └── vol3 -f memory.bin windows.handles --pid <suspicious>  │
│                                                                 │
│  8. TIMELINE CORRELATION                                       │
│     └── Cross-reference findings with prefetch, evtx, network  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**IOC Indicators to Look For:**
1. PowerShell with `-enc` or `-encodedcommand` parameters
2. Processes spawning from unusual parents (e.g., Excel → cmd.exe)
3. RWX memory regions in legitimate processes (e.g., MsMpEng.exe)
4. Connections to known bad IPs or unusual ports
5. Single-character executable names
6. Processes running from temp directories

---

### Workflow 2: Event Log Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVENT LOG ANALYSIS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. PARSE LOGS TO CSV                                          │
│     ├── EvtxECmd.exe -f Security.evtx --csv <output>           │
│     ├── EvtxECmd.exe -f System.evtx --csv <output>             │
│     └── EvtxECmd.exe -f *PowerShell*.evtx --csv <output>       │
│                                                                 │
│  2. THREAT HUNTING                                             │
│     ├── Hayabusa: hayabusa csv-timeline -d <logs> -o timeline  │
│     └── Chainsaw: chainsaw hunt <logs> -s <sigma_rules>        │
│                                                                 │
│  3. AUTHENTICATION ANALYSIS                                    │
│     ├── Filter EventID 4624 (Successful logons)                │
│     ├── Filter EventID 4625 (Failed logons)                    │
│     ├── Look for Type 3 logons (network) between hosts         │
│     └── Identify 4672 events (special privileges)              │
│                                                                 │
│  4. PROCESS CREATION (if auditing enabled)                     │
│     └── Filter EventID 4688 for command lines                  │
│                                                                 │
│  5. POWERSHELL ANALYSIS                                        │
│     ├── Filter EventID 4104 (Script Block Logging)             │
│     └── Search for: -enc, FromBase64, DownloadString, IEX      │
│                                                                 │
│  6. SERVICE INSTALLATION                                       │
│     ├── Filter EventID 7045 (New service installed)            │
│     └── Look for unusual service names/paths                   │
│                                                                 │
│  7. LOG CLEARING DETECTION                                     │
│     ├── Filter EventID 1102 (Security log cleared)             │
│     └── Filter EventID 104 (System log cleared)                │
│                                                                 │
│  8. VISUALISE IN TIMELINE EXPLORER                             │
│     └── Open CSVs, group by EventID, filter by timeframe       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Workflow 3: Registry Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│                    REGISTRY ANALYSIS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. PERSISTENCE MECHANISMS                                     │
│     ├── RECmd.exe -f SOFTWARE --kn "...\\CurrentVersion\\Run"    │
│     ├── RECmd.exe -f NTUSER.DAT --kn "...\\CurrentVersion\\Run"  │
│     └── Check RunOnce, RunServices, Userinit                   │
│                                                                 │
│  2. SERVICE ANALYSIS                                           │
│     ├── RECmd.exe -f SYSTEM --kn "ControlSet001\\Services"      │
│     └── Look for unusual ImagePath values                      │
│                                                                 │
│  3. EXECUTION EVIDENCE                                         │
│     ├── AppCompatCacheParser.exe -f SYSTEM --csv <output>      │
│     ├── AmcacheParser.exe -f Amcache.hve --csv <output>        │
│     └── Cross-reference with Prefetch                          │
│                                                                 │
│  4. DELETED ENTRY RECOVERY                                     │
│     └── RECmd.exe -f <hive> --recover --csv <output>           │
│                                                                 │
│  5. BATCH PROCESSING                                           │
│     └── RECmd.exe -f <hive> --bn RECmd_Batch_MC.reb --csv      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Workflow 4: Complete Investigation Timeline

```
┌─────────────────────────────────────────────────────────────────┐
│               MASTER TIMELINE CREATION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. COLLECT TIMESTAMPS FROM ALL SOURCES                        │
│     ├── Prefetch: PECmd -d <dir> --csv <output>                │
│     ├── Event Logs: EvtxECmd -d <dir> --csv <output>           │
│     ├── Registry: AppCompatCacheParser, AmcacheParser          │
│     ├── Memory: vol3 timeline, MemProcFS forensic              │
│     └── Network: tshark extraction                             │
│                                                                 │
│  2. NORMALISE TIMESTAMPS                                       │
│     ├── Ensure consistent timezone (UTC recommended)           │
│     └── Use consistent date format (--dt "dd/MM/yyyy HH:mm:ss")│
│                                                                 │
│  3. MERGE INTO UNIFIED TIMELINE                                │
│     ├── Option A: PowerShell script to combine CSVs            │
│     └── Option B: Plaso for automatic super timeline           │
│                                                                 │
│  4. ANALYSE IN TIMELINE EXPLORER                               │
│     ├── Sort by timestamp                                      │
│     ├── Filter by timeframe of interest                        │
│     ├── Group by source for pattern identification             │
│     └── Tag key events with Ctrl+T                             │
│                                                                 │
│  5. VALIDATE AGAINST KNOWN FACTS                               │
│     ├── Confirm initial access timestamp                       │
│     ├── Verify lateral movement timing                         │
│     └── Document discrepancies                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Advanced Integration Techniques

### YARA Rules with Volatility

```bash
# Create comprehensive rule file
cat << 'EOF' > cobalt_strike_memory.yar
rule CobaltStrike_Beacon_x64
{
    meta:
        description = "Cobalt Strike Beacon x64"
        author = "DFIR Team"
    strings:
        $a1 = { 4C 8B DC 49 89 5B 08 49 89 6B 10 49 89 73 18 }
        $a2 = { 48 89 5C 24 08 48 89 74 24 10 57 48 83 EC 20 }
        $s1 = "beacon.dll" ascii
        $s2 = "beacon.x64.dll" ascii
    condition:
        any of them
}

rule Reflective_Loader
{
    meta:
        description = "Reflective DLL Loader"
    strings:
        $mz = { 4D 5A }
        $reflective = { 48 8B C4 48 89 58 08 48 89 68 10 48 89 70 18 }
    condition:
        $mz at 0 and $reflective
}
EOF

# Run against memory dump
vol3 -f memory.bin windows.vadyarascan --yara-file cobalt_strike_memory.yar
```

---

### Automated Multi-Host Processing

```powershell
# Process multiple hosts with EZ Tools
$hosts = @("LAPTOP-135", "WORKSTATION-969", "DESKTOP-841")
$evidencePath = "D:\Evidence\ForensicsLab_S1\Working"
$outputPath = "D:\Output"

foreach ($host in $hosts) {
    # Create output directory
    New-Item -ItemType Directory -Force -Path "$outputPath\$host\Memory"
    New-Item -ItemType Directory -Force -Path "$outputPath\$host\EventLogs"
    New-Item -ItemType Directory -Force -Path "$outputPath\$host\Prefetch"
    New-Item -ItemType Directory -Force -Path "$outputPath\$host\Registry"
    
    # Process Prefetch
    PECmd.exe -d "$evidencePath\Prefetch\$host" --csv "$outputPath\$host\Prefetch" `
        --csvf "Prefetch_$host.csv" --dt "dd/MM/yyyy HH:mm:ss"
    
    # Process Event Logs
    EvtxECmd.exe -d "$evidencePath\EventLogs\$host" --csv "$outputPath\$host\EventLogs" `
        --dt "dd/MM/yyyy HH:mm:ss"
    
    # Process Registry
    RECmd.exe -f "$evidencePath\Registry\$host\SOFTWARE" `
        --bn "RECmd_Batch_MC.reb" --csv "$outputPath\$host\Registry" `
        --dt "dd/MM/yyyy HH:mm:ss"
    
    # Process ShimCache
    AppCompatCacheParser.exe -f "$evidencePath\Registry\$host\SYSTEM" `
        --csv "$outputPath\$host\Registry" --csvf "ShimCache_$host.csv" `
        --dt "dd/MM/yyyy HH:mm:ss"
    
    # Process Amcache
    AmcacheParser.exe -f "$evidencePath\Registry\$host\Amcache.hve" `
        --csv "$outputPath\$host\Registry" --csvf "Amcache_$host.csv" `
        --dt "dd/MM/yyyy HH:mm:ss"
}

Write-Host "Processing complete for all hosts."
```

---

### Handling Corrupted Artifacts

```powershell
# Memory dumps may be incomplete - use Volatility recovery options
vol3 -f <corrupted_memory.bin> windows.pslist 2>&1 | Tee-Object -FilePath error_log.txt

# For corrupted registry hives - use Registry Explorer (tolerant of dirty hives)
# Or use RECmd with --recover flag
RECmd.exe -f <dirty_hive> --recover --csv <output>

# For truncated prefetch files
PECmd.exe -f <file.pf> 2>&1 | Tee-Object -FilePath pf_errors.txt
# PECmd will process what it can and report errors

# Validate evidence integrity before and after analysis
certutil -hashfile <evidence_file> SHA256 > pre_analysis_hash.txt
# After analysis
certutil -hashfile <evidence_file> SHA256 > post_analysis_hash.txt
fc pre_analysis_hash.txt post_analysis_hash.txt
```

---

## SANS Tools Quick Reference

| Tool | Purpose | Author | Download |
|------|---------|--------|----------|
| **SIFT Workstation** | Complete forensic Linux distro | Rob T. Lee | https://www.sans.org/tools/sift-workstation |
| **KAPE** | Artifact collection & processing | Eric Zimmerman | https://www.sans.org/tools/kape |
| **PECmd** | Prefetch parser | Eric Zimmerman | https://ericzimmerman.github.io |
| **EvtxECmd** | Event log parser | Eric Zimmerman | https://ericzimmerman.github.io |
| **RECmd** | Registry command-line parser | Eric Zimmerman | https://ericzimmerman.github.io |
| **Registry Explorer** | Registry GUI viewer | Eric Zimmerman | https://ericzimmerman.github.io |
| **AppCompatCacheParser** | ShimCache parser | Eric Zimmerman | https://ericzimmerman.github.io |
| **AmcacheParser** | Amcache parser with hashes | Eric Zimmerman | https://ericzimmerman.github.io |
| **Timeline Explorer** | CSV/Excel forensic viewer | Eric Zimmerman | https://ericzimmerman.github.io |
| **MFTECmd** | MFT parser | Eric Zimmerman | https://ericzimmerman.github.io |
| **JLECmd** | Jump List parser | Eric Zimmerman | https://ericzimmerman.github.io |
| **LECmd** | LNK file parser | Eric Zimmerman | https://ericzimmerman.github.io |
| **SBECmd** | ShellBags parser | Eric Zimmerman | https://ericzimmerman.github.io |
| **APOLLO** | iOS/macOS artefact parser | Sarah Edwards | https://www.sans.org/tools/apollo |
| **Android Triage** | Android artefact collection | Mattia Epifani | https://www.sans.org/tools/android-triage |

---

## Additional Industry-Standard Tools

**Memory Analysis (Beyond Volatility):**

| Tool | Purpose | Source |
|------|---------|--------|
| **Rekall** | Memory forensics framework (deprecated but useful for older images) | https://github.com/google/rekall |
| **WinDbg** | Microsoft debugger for crash dump analysis | Microsoft Store |
| **Redline** | Memory and IOC analysis (FireEye/Mandiant) | https://www.fireeye.com/services/freeware/redline.html |

**Event Log Analysis (Beyond EvtxECmd):**

| Tool | Purpose | Source |
|------|---------|--------|
| **Zircolite** | SIGMA-based EVTX detection | https://github.com/wagga40/Zircolite |
| **DeepBlueCLI** | PowerShell-based threat hunting | https://github.com/sans-blue-team/DeepBlueCLI |
| **LogParser** | SQL-like queries on logs | Microsoft |

**Network Forensics:**

| Tool | Purpose | Source |
|------|---------|--------|
| **Wireshark/tshark** | Packet capture and analysis | https://www.wireshark.org |
| **NetworkMiner** | Network forensic analysis | https://www.netresec.com |
| **Zeek (Bro)** | Network security monitoring | https://zeek.org |

**Timeline Analysis:**

| Tool | Purpose | Source |
|------|---------|--------|
| **Plaso/Log2Timeline** | Super timeline creation | https://github.com/log2timeline/plaso |
| **Timesketch** | Collaborative timeline analysis | https://timesketch.org |

---

## Command Reference Card

### Hash Verification
```cmd
certutil -hashfile <file> SHA256
certutil -hashfile <file> MD5
```

### Volatility 3 Essential Commands
```bash
vol3 -f <mem> windows.info
vol3 -f <mem> windows.pslist
vol3 -f <mem> windows.pstree
vol3 -f <mem> windows.cmdline
vol3 -f <mem> windows.malfind
vol3 -f <mem> windows.netscan
vol3 -f <mem> windows.dlllist --pid <PID>
vol3 -f <mem> windows.handles --pid <PID>
vol3 -f <mem> windows.vadyarascan --yara-file <rules.yar>
```

### MemProcFS
```cmd
memprocfs.exe -device <mem> -forensic 1
memprocfs.exe -device <mem> -forensic 1 -license-accept-elastic-license-2.0
```

### Eric Zimmerman Tools
```cmd
PECmd.exe -d <prefetch_dir> --csv <out> --dt "dd/MM/yyyy HH:mm:ss"
EvtxECmd.exe -f <evtx> --csv <out> --dt "dd/MM/yyyy HH:mm:ss"
RECmd.exe -f <hive> --bn RECmd_Batch_MC.reb --csv <out>
AppCompatCacheParser.exe -f <SYSTEM> --csv <out>
AmcacheParser.exe -f <Amcache.hve> --csv <out>
```

### YARA
```bash
yara -r <rules.yar> <target_directory>
yara -s <rules.yar> <file>  # Print matching strings
```

### CAPA
```bash
capa <executable>
capa -vv <executable>  # Very verbose
capa -j <executable> > results.json
```

---

## References & Further Reading

**Official Documentation:**
1. [SANS Tools Repository](https://www.sans.org/tools) — Complete collection of SANS forensic tools
2. [Eric Zimmerman's Tools](https://ericzimmerman.github.io) — Complete EZ Tools suite
3. [Volatility Foundation](https://github.com/volatilityfoundation/volatility3) — Volatility 3 framework
4. [MemProcFS GitHub](https://github.com/ufrisk/MemProcFS) — Memory process file system
5. [CAPA GitHub](https://github.com/mandiant/capa) — Mandiant malware capability detector
6. [YARA Documentation](https://yara.readthedocs.io/) — Official YARA docs
7. [Hayabusa GitHub](https://github.com/Yamato-Security/hayabusa) — SIGMA-based threat hunting
8. [Chainsaw GitHub](https://github.com/WithSecureLabs/chainsaw) — Log hunting tool

**DFIR Learning Resources:**
1. [SANS DFIR Blog](https://www.sans.org/blog/?focus-area=digital-forensics) — Latest DFIR techniques
2. [13Cubed YouTube](https://www.youtube.com/c/13Cubed) — Forensic tool tutorials
3. [HackTricks](https://book.hacktricks.xyz/) — Penetration testing and forensics
4. [Ultimate Windows Security](https://www.ultimatewindowssecurity.com/securitylog/encyclopedia/) — Event ID encyclopedia

**MITRE ATT&CK:**
1. [MITRE ATT&CK Framework](https://attack.mitre.org/) — Adversary tactics and techniques
2. [T1055: Process Injection](https://attack.mitre.org/techniques/T1055/) — Process injection techniques
3. [T1059: Command and Scripting Interpreter](https://attack.mitre.org/techniques/T1059/) — PowerShell, cmd.exe

**Cobalt Strike Detection:**
1. [Cobalt Strike Detection](https://thedfirreport.com/category/cobalt-strike/) — Real-world Beacon analysis
2. [Detecting Cobalt Strike with Memory Forensics](https://www.volexity.com/blog/2021/12/09/detecting-cobalt-strike-with-memory-forensics/) — Volexity research

---

#HTB-Academy #DFIR #Digital-Forensics #Incident-Response #Memory-Analysis #Volatility #MemProcFS #CAPA #YARA #SANS-Tools #EZ-Tools #PECmd #EvtxECmd #RECmd #AppCompatCacheParser #AmcacheParser #Prefetch #Registry #Event-Logs #Hayabusa #Chainsaw #KAPE #Timeline-Explorer #Plaso #Malware-Analysis #Windows-Forensics #SIFT-Workstation #MITRE-T1055 #MITRE-T1059 #MITRE-T1547 #Cobalt-Strike #Process-Injection #Timeline-Analysis #Artifact-Parsing #CPTS #CDSA #Medium


------

# Running MemprocFS on mac with FUSE
   1. Navigate to the `files` directory:
```bash
cd /Users/daemon1/DigitalForensics/Tools/memprocfs/files
```
   2. Ensure the mount point exists:
```bash
mkdir -p mnt
```
   3. Run `memprocfs`:
```bash
./memprocfs -device ../../../Working/CMP416-2202336-CW2/WORKSTATION-969/memory/memory.bin -forensic 1 -forensic-yara-rules ../../yara-rules/index.yar -mount mnt/
```
`-disable-python -v` if you need to

---

## Key Updates & Enhancements to Add

### **Volatility 3 Updates (v2.26.0 - Feature Parity Release, May 2025)**

**Major Changes:**
- **Volatility 2 is now officially deprecated** - The GitHub repository has been archived
- **No more `--profile` argument required** - Volatility 3 automatically detects OS versions
- **New `--filters` flag** - Column-specific filtering without grep/awk
- **Unified output formats** - All plugins support csv, json, jsonl, pretty output via `-r` option
- **Consistent data extraction** - All plugins use `-o` for output directory and `--dump` option

**New Plugins (Add to your commands):**

```bash
# New Windows plugins (v2.26.0)
vol3 -f <mem> windows.hollowprocesses      # Detect process hollowing
vol3 -f <mem> windows.psxview              # Cross-reference process lists (hidden process detection)
vol3 -f <mem> windows.suspicious_threads   # Find suspicious userland threads
vol3 -f <mem> windows.suspended_threads    # Enumerate suspended threads
vol3 -f <mem> windows.direct_system_calls  # Detect direct syscalls (EDR bypass)
vol3 -f <mem> windows.indirect_system_calls # Detect indirect syscalls
vol3 -f <mem> windows.shimcachemem         # ShimCache from memory
vol3 -f <mem> windows.scheduled_tasks      # Decode scheduled tasks from registry
vol3 -f <mem> windows.svclist              # List services from doubly-linked list
vol3 -f <mem> windows.svcdiff              # Compare services (walking vs scanning) for rootkit detection
vol3 -f <mem> windows.processghosting      # Detect process ghosting technique
vol3 -f <mem> windows.pedump               # Extract PE files from specific addresses

# New filtering example
vol3 -f <mem> --filters "ImageFileName=powershell" windows.pslist
vol3 -f <mem> --filters "Start VPN=0x1000000" windows.vadinfo

# Pretty output (aligned tables)
vol3 -f <mem> -r pretty windows.pslist
```

---

### **MemProcFS Updates (v5.15 - Latest, June 2025)**

**New Features to Add:**

| Version | Key Features |
|---------|-------------|
| v5.15 | Linux LeechAgent support (gRPC), **High Entropy detection** in FindEvil, DNS cache parsing |
| v5.14 | **macOS support**, Linux clang compilation |
| v5.13 | Console module, File recovery improvements, **Callstack parsing for x64 processes** |
| v5.12 | New APIs for Kernel Objects, Drivers and Devices |
| v5.10 | Windows 11 24H2 support, **Hibernation file support**, Prefetch parsing, Sysinfo module, Eventlog module |
| v5.9 | FindEvil shows Windows Defender AV detections, Proxmox dump support |

**Updated Commands:**

```cmd
:: New sysinfo module for easy system info
memprocfs.exe -device <mem> -forensic 1
:: Then browse M:\forensic\sysinfo\

:: DNS cache parsing (new in v5.15)
:: Available at M:\forensic\dns\

:: Eventlog module (v5.10+)
:: Available at M:\forensic\eventlog\

:: Console module (v5.13+)
:: Available at M:\name\<process>\console\

:: High entropy detection
:: FindEvil now flags high entropy regions (potential packed/encrypted code)
```

**New Virtual File System Directories:**

| Directory | Contents | Version Added |
|-----------|----------|---------------|
| `M:\forensic\sysinfo\` | Easy-to-read system information | v5.10 |
| `M:\forensic\eventlog\` | Convenient event log access | v5.10 |
| `M:\forensic\dns\` | DNS cache entries | v5.15 |
| `M:\name\<proc>\console\` | Console buffer contents | v5.13 |
| `M:\name\<proc>\callstack\` | x64 user-mode callstacks | v5.13 |

---

### **Hayabusa Updates (v3.3.0 - Latest, May 2025)**

**Major New Features:**

```bash
# New "Emergency" alert level for critical systems (v3.1.0+)
# Add critical system names to config/critical_systems.txt
# Alerts are automatically elevated one level on those systems

# Auto-detect domain controllers and file servers
hayabusa config-critical-systems -d <evtx_dir>

# Extract and decode Base64 strings (v3.0.0+)
hayabusa extract-base64 -d <evtx_dir> -o base64_decoded.csv

# Log metrics command (v2.19.0+)
hayabusa log-metrics -d <evtx_dir> -o log_metrics.csv

# Tab-separated output for field info
hayabusa csv-timeline -d <evtx_dir> -o timeline.csv -S

# Sigma V2 correlation rules support (v3.0.0+)
# - temporal (Temporal Proximity)
# - temporal_ordered (Temporal Ordered Proximity)
# - expand field modifiers

# XOR-encoded rules to bypass AV false positives (v2.18.0+)
# Use live-response packages from releases
```

**New Command Summary:**

| Command | Purpose | Version |
|---------|---------|---------|
| `extract-base64` | Extract and decode Base64 from events | v3.0.0 |
| `expand-list` | List placeholder names for expand rules | v3.0.0 |
| `log-metrics` | Get .evtx file information | v2.19.0 |
| `config-critical-systems` | Auto-find DCs and file servers | v3.1.0 |

**Performance Improvements:**
- Low memory mode enabled by default
- Significantly faster `logon-summary` with channel filtering
- `search` command no longer sorts by default (use `-s` to sort)

---

### **KAPE Updates (2024-2025)**

**Key Compound Targets:**

| Target | Description |
|--------|-------------|
| `KapeTriage` | Comprehensive triage - Registry, Event Logs, Prefetch, Amcache, etc. |
| `!BasicCollection` | Essential forensic artifacts |
| `!SANS_Triage` | SANS-recommended artifact set |
| `EvidenceOfExecution` | Prefetch, RecentFileCache, AmCache, SysCache |

**Key Compound Modules:**

| Module | Description |
|--------|-------------|
| `!EZParser` | All Eric Zimmerman tools against collected artifacts |
| `Mini_Timeline` | Generate timeline using TLN tools |

**New Command Examples:**

```cmd
:: Collect with KapeTriage and process with EZParser
kape.exe --tsource C: --tdest D:\Evidence --target KapeTriage --mdest D:\Processed --module !EZParser

:: Output to VHDX container
kape.exe --tsource C: --tdest D:\Evidence --target KapeTriage --vhdx Evidence_Container

:: Include Volume Shadow Copies
kape.exe --tsource C: --tdest D:\Evidence --target KapeTriage --vss

:: Sync targets and modules to latest
kape.exe --sync
```

---

### **New Tools to Add**

#### **Velociraptor**
**Purpose:** Enterprise-wide endpoint visibility and DFIR platform. Integrates with Hayabusa for scalable threat hunting.

**Source:** [Velociraptor](https://docs.velociraptor.app/)

```yaml
# Hayabusa artifact for Velociraptor
# Allows enterprise-wide Windows event log analysis
# Retroactively creates SIEM-like visibility
```

#### **Zircolite**
**Purpose:** Standalone SIGMA-based detection tool for EVTX, Auditd, Sysmon for Linux, and more.

**Source:** [Zircolite GitHub](https://github.com/wagga40/Zircolite)

```bash
# Scan with SIGMA rules
python3 zircolite.py --evtx <evtx_dir> --ruleset rules/rules_windows_generic.json
```

#### **DeepBlueCLI**
**Purpose:** PowerShell-based threat hunting in Windows event logs.

**Source:** [DeepBlueCLI GitHub](https://github.com/sans-blue-team/DeepBlueCLI)

```powershell
# Analyze Security log
.\DeepBlue.ps1 .\Security.evtx
```

---

### **Updated MITRE ATT&CK Techniques**

Add these commonly detected techniques:

| Technique ID | Name | Detection Method |
|-------------|------|------------------|
| **T1055.012** | Process Hollowing | `windows.hollowprocesses` (Vol3) |
| **T1055.001** | DLL Injection | `windows.malfind` + `windows.ldrmodules` |
| **T1134** | Access Token Manipulation | `windows.privileges` |
| **T1218** | System Binary Proxy Execution | Hayabusa SIGMA rules |
| **T1562.001** | Disable Security Tools | Event ID 1102, 7045 |

---

### **Updated Quick Reference Table**

Replace your existing table with this expanded version:

| # | Tool | Primary Use | Key Command | Notes |
|:--|:-----|:------------|:------------|:------|
| 1 | **Volatility 3** (v2.26) | Memory forensics | `vol3 -f mem.bin windows.hollowprocesses` | Process hollowing detection |
| 2 | **MemProcFS** (v5.15) | Memory VFS | `memprocfs.exe -device mem.
