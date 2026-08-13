---
title: "Windows - Persistence"
topic: "Methodology and Resources"
topicSlug: "methodology-and-resources"
sourcePath: "Methodology and Resources/Windows - Persistence.md"
sourceUrl: "https://github.com/swisskyrepo/PayloadsAllTheThings/blob/3bff425aca2b/Methodology%20and%20Resources/Windows%20-%20Persistence.md"
sha: "3bff425aca2b"
isReadme: false
---

# Windows - Persistence

:warning: Content of this page has been moved to [InternalAllTheThings/redteam/persistence/windows](/internal/redteam/persistence/windows-persistence)

- [Tools](/internal/redteam/persistence/windows-persistence#tools)
- [Hide Your Binary](/internal/redteam/persistence/windows-persistence#hide-your-binary)
- [Disable Antivirus and Security](/internal/redteam/persistence/windows-persistence#disable-antivirus-and-security)
    - [Antivirus Removal](/internal/redteam/persistence/windows-persistence#antivirus-removal)
    - [Disable Windows Defender](/internal/redteam/persistence/windows-persistence#disable-windows-defender)
    - [Disable Windows Firewall](/internal/redteam/persistence/windows-persistence#disable-windows-firewall)
    - [Clear System and Security Logs](/internal/redteam/persistence/windows-persistence#clear-system-and-security-logs)
- [Simple User](/internal/redteam/persistence/windows-persistence#simple-user)
    - [Registry HKCU](/internal/redteam/persistence/windows-persistence#registry-hkcu)
    - [Startup](/internal/redteam/persistence/windows-persistence#startup)
    - [Scheduled Tasks User](/internal/redteam/persistence/windows-persistence#scheduled-tasks-user)
    - [BITS Jobs](/internal/redteam/persistence/windows-persistence#bits-jobs)
- [Serviceland](/internal/redteam/persistence/windows-persistence#serviceland)
    - [IIS](/internal/redteam/persistence/windows-persistence#iis)
    - [Windows Service](/internal/redteam/persistence/windows-persistence#windows-service)
- [Elevated](/internal/redteam/persistence/windows-persistence#elevated)
    - [Registry HKLM](/internal/redteam/persistence/windows-persistence#registry-hklm)
        - [Winlogon Helper DLL](/internal/redteam/persistence/windows-persistence)
        - [GlobalFlag](/internal/redteam/persistence/windows-persistence)
    - [Startup Elevated](/internal/redteam/persistence/windows-persistence#startup-elevated)
    - [Services Elevated](/internal/redteam/persistence/windows-persistence#services-elevated)
    - [Scheduled Tasks Elevated](/internal/redteam/persistence/windows-persistence#scheduled-tasks-elevated)
    - [Binary Replacement](/internal/redteam/persistence/windows-persistence#binary-replacement)
        - [Binary Replacement on Windows XP+](/internal/redteam/persistence/windows-persistence#binary-replacement-on-windows-xp)
        - [Binary Replacement on Windows 10+](/internal/redteam/persistence/windows-persistence#binary-replacement-on-windows-10)
    - [RDP Backdoor](/internal/redteam/persistence/windows-persistence#rdp-backdoor)
        - [utilman.exe](/internal/redteam/persistence/windows-persistence#utilman.exe)
        - [sethc.exe](/internal/redteam/persistence/windows-persistence#sethc.exe)
    - [Remote Desktop Services Shadowing](/internal/redteam/persistence/windows-persistence#remote-desktop-services-shadowing)
    - [Skeleton Key](/internal/redteam/persistence/windows-persistence#skeleton-key)
    - [Virtual Machines](/internal/redteam/persistence/windows-persistence#virtual-machines)
    - [Windows Subsystem for Linux](/internal/redteam/persistence/windows-persistence#windows-subsystem-for-linux)
- [Domain](/internal/redteam/persistence/windows-persistence#domain)
    - [Golden Certificate](/internal/redteam/persistence/windows-persistence#golden-certificate)
    - [Golden Ticket](/internal/redteam/persistence/windows-persistence#golden-ticket)
- [References](/internal/redteam/persistence/windows-persistence#references)
