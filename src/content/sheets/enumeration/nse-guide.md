---
title: "NSE Guide"
description: "nmap -sV -p21 --script=ftp-anon,ftp-bounce,ftp-syst <target>"
category: enumeration
tags: ["enumeration"]
tools: ["Nmap"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Enumeration/NSE Guide.md"
---
# Safe FTP enumeration
nmap -sV -p21 --script=ftp-anon,ftp-bounce,ftp-syst <target>

# Check for anonymous access and list files
nmap -p21 --script=ftp-anon --script-args ftp-anon.maxlist=-1 <target>

# FTP vulnerability assessment
nmap -p21 --script=ftp-vuln-* <target>

# Check for backdoors
nmap -p21 --script=ftp-proftpd-backdoor,ftp-vsftpd-backdoor <target>

# FTP brute force (noisy)
nmap -p21 --script=ftp-brute --script-args userdb=/usr/share/seclists/Usernames/top-usernames-shortlist.txt,passdb=/usr/share/seclists/Passwords/Common-Credentials/10-million-password-list-top-100.txt <target>

# FTP brute force with timeout control
nmap -p21 --script=ftp-brute --script-args ftp-brute.timeout=10s,brute.threads=2 <target>

# Comprehensive FTP assessment
nmap -sV -p21 --script="ftp-* and not brute" <target>
```

> [!info]+ Command Breakdown: FTP Enumeration
> 1. **ftp-anon**: Attempts login with username "anonymous" and email as password
> 2. **ftp-anon.maxlist**: Controls how many directory entries to list (-1 for unlimited)
> 3. **ftp-bounce**: Tests if FTP server allows bounce attacks (proxy port scans)
> 4. **ftp-vsftpd-backdoor**: Checks for backdoor in vsftpd 2.3.4 (smiley face backdoor)
> 5. **ftp-brute.timeout**: Delay between connection attempts to avoid blocking

> [!success]+ Expected FTP Output
> ```
> PORT   STATE SERVICE VERSION
> 21/tcp open  ftp     vsftpd 2.3.4
> | ftp-anon: Anonymous FTP login allowed (FTP code 230)
> |_drwxr-xr-x    2 0        0            4096 Mar 17  2010 pub
> | ftp-vsftpd-backdoor:
> |   VULNERABLE:
> |   vsFTPd version 2.3.4 backdoor
> |     State: VULNERABLE (Exploitable)
> |     IDs:  CVE:CVE-2011-2523  BID:48539
> |       vsFTPd version 2.3.4 backdoor, this was reported on 2011-07-04.
> |     Disclosure date: 2011-07-03
> |     Exploit results:
> |       Shell command: id
> |       Results: uid=0(root) gid=0(root)
> |     References:
> |       https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2011-2523
> ```

> [!warning]+ FTP OPSEC Considerations
> 6. **Anonymous login attempts**: Logged in FTP server logs
> 7. **ftp-brute detection**: Extremely noisy, triggers fail2ban and IDS
> 8. **Backdoor checks**: May trigger AV/EDR alerts
> 9. **Safe scripts**: ftp-anon, ftp-syst generate normal FTP traffic
> 10. **Directory listing**: Large directories cause extended connection time

> [!failure]+ Common FTP Issues
> 11. **Connection timeout**: FTP firewall filtering or passive mode issues
>    - Solution: Verify port 21 accessible, some scripts need port 20 open
> 12. **Anonymous access denied**: Expected on secure configurations
>    - Solution: Not an error - indicates proper security
> 13. **ftp-brute IP blocking**: fail2ban blocks source IP after failed attempts
>    - Solution: Reduce threads and add delays with `ftp-brute.timeout`

---

## Port 22 - SSH (Secure Shell)

> [!info]+ [SSH Service Overview](https://www.openssh.com/)
> Secure Shell provides encrypted remote access and file transfer. Critical service for Linux/Unix administration. Version detection, algorithm enumeration, and authentication testing reveal security posture.

**Key NSE Scripts for SSH**:

> [!info]+ SSH Enumeration Scripts
> 1. **[ssh-hostkey](https://nmap.org/nsedoc/scripts/ssh-hostkey.html)**: Retrieves SSH host keys and fingerprints
> 2. **[ssh-auth-methods](https://nmap.org/nsedoc/scripts/ssh-auth-methods.html)**: Lists supported authentication methods
> 3. **[ssh2-enum-algos](https://nmap.org/nsedoc/scripts/ssh2-enum-algos.html)**: Enumerates encryption algorithms and ciphers
> 4. **[sshv1](https://nmap.org/nsedoc/scripts/sshv1.html)**: Checks for deprecated SSHv1 support
> 5. **[ssh-brute](https://nmap.org/nsedoc/scripts/ssh-brute.html)**: Credential brute forcing
> 6. **[ssh-publickey-acceptance](https://nmap.org/nsedoc/scripts/ssh-publickey-acceptance.html)**: Tests public key authentication
> 7. **[ssh-run](https://nmap.org/nsedoc/scripts/ssh-run.html)**: Runs commands via SSH with credentials

```bash
# Safe SSH enumeration
nmap -sV -p22 --script=ssh-hostkey,ssh-auth-methods,ssh2-enum-algos <target>

# Check for SSHv1 (insecure)
nmap -p22 --script=sshv1 <target>

# SSH host key fingerprinting
nmap -p22 --script=ssh-hostkey --script-args ssh_hostkey=full <target>

# Enumerate supported authentication methods
nmap -p22 --script=ssh-auth-methods <target>

# Enumerate encryption algorithms
nmap -p22 --script=ssh2-enum-algos <target>

# Check public key acceptance
nmap -p22 --script=ssh-publickey-acceptance <target>

# SSH brute force (VERY NOISY - triggers fail2ban)
nmap -p22 --script=ssh-brute --script-args userdb=users.txt,passdb=pass.txt <target>

# Slow SSH brute force to avoid blocking
nmap -p22 --script=ssh-brute --script-args ssh-brute.timeout=4m,brute.threads=1,brute.firstOnly=true <target>

# Execute command with known credentials
nmap -p22 --script=ssh-run --script-args ssh-run.cmd="uname -a",ssh-run.username=root,ssh-run.password=toor <target>

# Comprehensive SSH assessment
nmap -sV -p22 --script="ssh-* and not brute" <target>
```

> [!info]+ Command Breakdown: SSH Enumeration
> 1. **ssh-hostkey**: Extracts RSA, DSA, ECDSA, ED25519 public keys
> 2. **ssh_hostkey=full**: Shows complete public key, not just fingerprint
> 3. **ssh2-enum-algos**: Lists key exchange, encryption, MAC, compression algorithms
> 4. **ssh-brute.timeout**: Critical - delay between attempts (fail2ban typically bans after 3-5 failures)
> 5. **brute.firstOnly**: Stops after finding first valid credential (faster, less noisy)

> [!success]+ Expected SSH Output
> ```
> PORT   STATE SERVICE VERSION
> 22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
> | ssh-hostkey:
> |   2048 8a:d3:22:e4:76:4e:6e:77:9f:8b:3e:3c:9f:2e:8c:3a (RSA)
> |   256 31:7d:99:2f:1f:2e:8e:6e:8f:9e:2e:3f:7e:8e:2f:3e (ECDSA)
> |_  256 8e:2f:3e:7e:8e:2f:3e:7e:8e:2f:3e:7e:8e:2f:3e:7e (ED25519)
> | ssh-auth-methods:
> |   Supported authentication methods:
> |     publickey
> |     password
> |_    keyboard-interactive
> | ssh2-enum-algos:
> |   kex_algorithms: (6)
> |       curve25519-sha256
> |       curve25519-sha256@libssh.org
> |       ecdh-sha2-nistp256
> |       ecdh-sha2-nistp384
> |       ecdh-sha2-nistp521
> |       diffie-hellman-group-exchange-sha256
> |   encryption_algorithms: (9)
> |       chacha20-poly1305@openssh.com
> |       aes128-ctr
> |       aes192-ctr
> |       aes256-ctr
> |       aes128-gcm@openssh.com
> |       aes256-gcm@openssh.com
> ```

> [!warning]+ SSH OPSEC Considerations
> 6. **ssh-brute**: Extremely noisy - fail2ban typically bans after 3-5 failed attempts
> 7. **Failed auth logging**: All failed attempts logged in /var/log/auth.log
> 8. **Safe enumeration**: hostkey, auth-methods, algorithms are normal SSH handshake
> 9. **Detection**: Multiple connections from same IP triggers automated blocking
> 10. **Modern defenses**: Ubuntu/Debian commonly run fail2ban by default

> [!failure]+ Common SSH Issues
> 11. **IP banned after 3-5 attempts**: fail2ban or similar IPS blocking
>    - Solution: Use `ssh-brute.timeout=4m` for 4-minute delays between attempts
> 12. **Connection reset**: Too many rapid connections
>    - Solution: Reduce threads to 1, increase timeouts
> 13. **Public key scripts require proper key format**: PEM or OpenSSH format
>    - Solution: Generate keys with `ssh-keygen -t rsa`

> [!tip]+ SSH Security Assessment Best Practices
> 14. **Check for SSHv1**: Ancient protocol with known vulnerabilities
> 15. **Weak algorithms**: Look for CBC ciphers, MD5 MACs, weak KEX
> 16. **Authentication methods**: Password auth less secure than publickey
> 17. **Host key analysis**: Same key across multiple servers may indicate cloning
> 18. **Version detection**: Older OpenSSH versions have known CVEs

---

## Port 23 - Telnet

> [!info]+ [Telnet Service Overview](https://en.wikipedia.org/wiki/Telnet)
> Unencrypted remote access protocol. Credentials transmitted in cleartext. Presence indicates legacy systems or IoT devices. Highly insecure and should be replaced with SSH.

**Key NSE Scripts for Telnet**:

> [!info]+ Telnet Enumeration Scripts
> 1. **[telnet-brute](https://nmap.org/nsedoc/scripts/telnet-brute.html)**: Credential brute forcing
> 2. **[telnet-encryption](https://nmap.org/nsedoc/scripts/telnet-encryption.html)**: Checks for encryption support
> 3. **[telnet-ntlm-info](https://nmap.org/nsedoc/scripts/telnet-ntlm-info.html)**: Extracts Windows domain info via NTLM
> 4. **[tn3270-screen](https://nmap.org/nsedoc/scripts/tn3270-screen.html)**: Captures mainframe TN3270 screens

```bash
# Basic Telnet enumeration
nmap -sV -p23 --script=telnet-encryption <target>

# Telnet NTLM information disclosure
nmap -p23 --script=telnet-ntlm-info <target>

# TN3270 mainframe enumeration
nmap -p23 --script=tn3270-screen <target>

# Telnet brute force (cleartext credentials)
nmap -p23 --script=telnet-brute --script-args userdb=users.txt,passdb=pass.txt <target>

# IoT device default credential testing
nmap -p23,2323 --script=telnet-brute --script-args userdb=/usr/share/seclists/Usernames/top-usernames-shortlist.txt,passdb=/usr/share/seclists/Passwords/Default-Credentials/telnet-betterdefaultpasslist.txt <target>

# Comprehensive Telnet assessment
nmap -sV -p23 --script="telnet-*" <target>
```

> [!info]+ Command Breakdown: Telnet Enumeration
> 1. **telnet-encryption**: Tests if Telnet supports encryption extensions (rare)
> 2. **telnet-ntlm-info**: Forces NTLM authentication to leak domain/workgroup names
> 3. **tn3270-screen**: Captures IBM mainframe login screens
> 4. **telnet-brute**: Tests credentials over cleartext connection
> 5. *Telnet on IoT devices often on non-standard ports like 2323, 8023*

> [!success]+ Expected Telnet Output
> ```
> PORT   STATE SERVICE VERSION
> 23/tcp open  telnet  Linux telnetd
> | telnet-encryption:
> |_  Telnet server does not support encryption
> | telnet-ntlm-info:
> |   Target_Name: WORKGROUP
> |   NetBIOS_Domain_Name: WORKGROUP
> |   NetBIOS_Computer_Name: SERVER01
> |   DNS_Domain_Name: localdomain
> |   DNS_Computer_Name: server01.localdomain
> |_  Product_Version: 5.0.2195
> ```

> [!danger]+ Telnet Security Warnings
> 6. **Cleartext transmission**: All data including credentials sent unencrypted
> 7. **Network sniffing**: Wireshark/tcpdump can capture passwords
> 8. **No security**: Telnet provides no authentication security or confidentiality
> 9. **Replace with SSH**: Telnet should never be used on production systems
> 10. **IoT prevalence**: Routers, cameras, printers commonly have Telnet enabled

> [!warning]+ Telnet OPSEC Considerations
> 11. **Brute force highly visible**: Cleartext passwords logged on network
> 12. **Network monitoring**: Easily detected by IDS/packet analysis
> 13. **Authentication failures**: Logged in system logs
> 14. **Safe enumeration**: telnet-encryption, telnet-ntlm-info low risk

---

## Port 25/465/587 - SMTP (Simple Mail Transfer Protocol)

> [!info]+ [SMTP Service Overview](https://en.wikipedia.org/wiki/Simple_Mail_Transfer_Protocol)
> Email transmission protocol. Port 25 for unencrypted SMTP, 465 for SMTPS (deprecated), 587 for submission with STARTTLS. User enumeration via VRFY/EXPN commands, open relay testing, and vulnerability assessment.

**Key NSE Scripts for SMTP**:

> [!info]+ SMTP Enumeration Scripts
> 1. **[smtp-commands](https://nmap.org/nsedoc/scripts/smtp-commands.html)**: Lists supported SMTP commands
> 2. **[smtp-enum-users](https://nmap.org/nsedoc/scripts/smtp-enum-users.html)**: Enumerates users via VRFY/EXPN/RCPT
> 3. **[smtp-open-relay](https://nmap.org/nsedoc/scripts/smtp-open-relay.html)**: Tests for open relay misconfiguration
> 4. **[smtp-brute](https://nmap.org/nsedoc/scripts/smtp-brute.html)**: Credential brute forcing
> 5. **[smtp-vuln-cve2010-4344](https://nmap.org/nsedoc/scripts/smtp-vuln-cve2010-4344.html)**: Exim heap overflow
> 6. **[smtp-vuln-cve2011-1720](https://nmap.org/nsedoc/scripts/smtp-vuln-cve2011-1720.html)**: Postfix STARTTLS plaintext injection
> 7. **[smtp-vuln-cve2011-1764](https://nmap.org/nsedoc/scripts/smtp-vuln-cve2011-1764.html)**: Exim DKIM denial of service
> 8. **[smtp-ntlm-info](https://nmap.org/nsedoc/scripts/smtp-ntlm-info.html)**: Extracts Windows domain info via NTLM
> 9. **[smtp-strangeport](https://nmap.org/nsedoc/scripts/smtp-strangeport.html)**: Detects SMTP on unusual ports (malware indicator)

```bash
# Safe SMTP enumeration
nmap -sV -p25,465,587 --script=smtp-commands,smtp-ntlm-info <target>

# Test for open relay
nmap -p25 --script=smtp-open-relay <target>

# User enumeration via VRFY and EXPN
nmap -p25 --script=smtp-enum-users --script-args smtp-enum-users.methods={VRFY,EXPN} <target>

# User enumeration with custom wordlist
nmap -p25 --script=smtp-enum-users --script-args userdb=/usr/share/seclists/Usernames/top-usernames-shortlist.txt,smtp-enum-users.methods={VRFY,EXPN,RCPT} <target>

# SMTP NTLM information disclosure
nmap -p25,587 --script=smtp-ntlm-info <target>

# SMTP vulnerability assessment
nmap -p25 --script=smtp-vuln-* <target>

# SMTP brute force authentication
nmap -p25,587 --script=smtp-brute --script-args userdb=users.txt,passdb=pass.txt <target>

# Comprehensive SMTP assessment
nmap -sV -p25,465,587 --script="smtp-* and not brute" <target>

# Test multiple SMTP ports including submissions
nmap -sV -p25,465,587,2525 --script=smtp-commands,smtp-open-relay <target>
```

> [!info]+ Command Breakdown: SMTP Enumeration
> 1. **smtp-enum-users.methods**: Specifies enumeration technique (VRFY, EXPN, RCPT TO)
> 2. **smtp-open-relay**: Attempts to send email through server to external domain
> 3. **smtp-ntlm-info**: Forces NTLM auth to disclose domain/computer names
> 4. **smtp-commands**: Issues EHLO/HELO to enumerate extended commands
> 5. **VRFY**: Verifies if user exists (often disabled)
> 6. **EXPN**: Expands mailing list (rarely enabled)
> 7. **RCPT TO**: Tests email acceptance (slower but works when VRFY/EXPN blocked)

> [!success]+ Expected SMTP Output
> ```
> PORT   STATE SERVICE VERSION
> 25/tcp open  smtp    Postfix smtpd
> | smtp-commands: mail.example.com, PIPELINING, SIZE 10240000, VRFY, ETRN, STARTTLS, ENHANCEDSTATUSCODES, 8BITMIME, DSN
> |_ This server supports the following commands: HELO EHLO STARTTLS RCPT DATA RSET MAIL QUIT HELP AUTH NOOP
> | smtp-enum-users:
> |   Accounts found:
> |     admin - Valid user
> |     user1 - Valid user
> |     webmaster - Valid user
> |   Statistics: Performed 50 guesses in 12 seconds
> | smtp-ntlm-info:
> |   Target_Name: MAIL
> |   NetBIOS_Domain_Name: CONTOSO
> |   NetBIOS_Computer_Name: MAIL01
> |   DNS_Domain_Name: contoso.local
> |   DNS_Computer_Name: mail01.contoso.local
> |_  Product_Version: 6.1.7601
> | smtp-open-relay: Server is an open relay (16/16 tests)
> |  MAIL FROM:<antispam@insecure.org> -> RCPT TO:<relaytest@insecure.org>
> |  MAIL FROM:<antispam@insecure.org> -> RCPT TO:<relaytest%insecure.org@example.com>
> ```

> [!warning]+ SMTP OPSEC Considerations
> 8. **User enumeration**: VRFY/EXPN attempts logged in mail server logs
> 9. **Open relay testing**: May generate email to external addresses (logged)
> 10. **Modern mail servers**: VRFY/EXPN commonly disabled on Exchange, Postfix
> 11. **RCPT TO enumeration**: Slower but more reliable, generates more logs
> 12. **smtp-brute**: Extremely noisy, triggers fail2ban and rate limiting

> [!failure]+ Common SMTP Issues
> 13. **VRFY/EXPN disabled**: Modern security practice blocks these commands
>    - Solution: Use RCPT TO method with `smtp-enum-users.methods={RCPT}`
> 14. **Connection rate limiting**: Multiple connections blocked
>    - Solution: Reduce threads and add delays
> 15. **TLS required**: Port 25 may require STARTTLS before allowing commands
>    - Solution: Use port 587 for modern submission protocol
> 16. **False positives on user enum**: Some servers return "User unknown" for all users
>    - Solution: Verify results manually with test account

> [!tip]+ SMTP Security Assessment Best Practices
> 17. **Open relay**: Critical misconfiguration allowing spam relay
> 18. **User enumeration**: Reveals valid email addresses for phishing
> 19. **NTLM info disclosure**: Leaks internal domain names
> 20. **Version detection**: Outdated Postfix/Exim/Sendmail may be vulnerable
> 21. **Strange ports**: SMTP on non-standard ports may indicate malware

---

## Port 53 - DNS (Domain Name System)

> [!info]+ [DNS Service Overview](https://www.cloudflare.com/learning/dns/what-is-dns/)
> Domain Name System translates domain names to IP addresses. Critical infrastructure service. Zone transfers, subdomain enumeration, recursion testing, and cache snooping reveal network topology and misconfigurations.

**Key NSE Scripts for DNS**:

> [!info]+ DNS Enumeration Scripts
> 1. **[dns-zone-transfer](https://nmap.org/nsedoc/scripts/dns-zone-transfer.html)**: Attempts AXFR zone transfer
> 2. **[dns-brute](https://nmap.org/nsedoc/scripts/dns-brute.html)**: Subdomain brute forcing
> 3. **[dns-recursion](https://nmap.org/nsedoc/scripts/dns-recursion.html)**: Tests for open DNS resolver
> 4. **[dns-service-discovery](https://nmap.org/nsedoc/scripts/dns-service-discovery.html)**: Discovers services via DNS-SD/mDNS
> 5. **[dns-nsid](https://nmap.org/nsedoc/scripts/dns-nsid.html)**: Retrieves DNS server identity
> 6. **[dns-cache-snoop](https://nmap.org/nsedoc/scripts/dns-cache-snoop.html)**: Checks DNS cache for specific domains
> 7. **[dns-nsec-enum](https://nmap.org/nsedoc/scripts/dns-nsec-enum.html)**: Enumerates DNSSEC NSEC records
> 8. **[dns-nsec3-enum](https://nmap.org/nsedoc/scripts/dns-nsec3-enum.html)**: Enumerates DNSSEC NSEC3 records
> 9. **[dns-random-srcport](https://nmap.org/nsedoc/scripts/dns-random-srcport.html)**: Checks for source port randomization
> 10. **[dns-random-txid](https://nmap.org/nsedoc/scripts/dns-random-txid.html)**: Checks for transaction ID randomization

```bash
# Attempt DNS zone transfer
nmap -p53 --script=dns-zone-transfer --script-args dns-zone-transfer.domain=example.com <target>

# Subdomain brute force
nmap --script=dns-brute --script-args dns-brute.domain=example.com <target>

# Subdomain brute with custom wordlist
nmap --script=dns-brute --script-args dns-brute.domain=example.com,dns-brute.hostlist=/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt <target>

# Subdomain brute with thread control
nmap --script=dns-brute --script-args dns-brute.domain=example.com,dns-brute.threads=10 --script-timeout=30m <target>

# Check for open DNS resolver
nmap -sU -p53 --script=dns-recursion <target>

# DNS service discovery (multicast DNS)
nmap -p53 --script=dns-service-discovery <target>

# DNS server identification
nmap -p53 --script=dns-nsid <target>

# DNS cache snooping
nmap -sU -p53 --script=dns-cache-snoop --script-args 'dns-cache-snoop.mode=timed,dns-cache-snoop.domains={google.com,facebook.com,example.com}' <target>

# DNSSEC NSEC enumeration
nmap -p53 --script=dns-nsec-enum --script-args dns-nsec-enum.domains=example.com <target>

# Check DNS security (randomization)
nmap -sU -p53 --script=dns-random-srcport,dns-random-txid <target>

# Comprehensive DNS assessment (both UDP and TCP)
nmap -sU -sS -p53 --script="dns-* and not brute" <target>

# Internal DNS server enumeration
nmap -sU -p53 --script=dns-recursion,dns-nsid --script-args dns-nsid.identifier=version.bind <target>
```

> [!info]+ Command Breakdown: DNS Enumeration
> 1. **dns-zone-transfer.domain**: Target domain for AXFR request
> 2. **dns-brute.threads**: Parallelization (default 5, increase for speed, decrease for stealth)
> 3. **dns-brute.hostlist**: Custom subdomain wordlist path
> 4. **dns-cache-snoop.mode=timed**: Uses timing to detect cached vs uncached queries
> 5. **DNS requires both UDP and TCP**: Use `-sU -sS` for comprehensive scanning
> 6. **dns-nsid.identifier**: Custom NSID query (version.bind reveals BIND version)

> [!success]+ Expected DNS Output
> ```
> PORT   STATE SERVICE
> 53/udp open  domain
> | dns-zone-transfer:
> |   example.com.      SOA     ns1.example.com. admin.example.com.
> |   example.com.      NS      ns1.example.com.
> |   example.com.      NS      ns2.example.com.
> |   example.com.      A       192.0.2.1
> |   www.example.com.  A       192.0.2.2
> |   mail.example.com. A       192.0.2.3
> |   ftp.example.com.  A       192.0.2.4
> |   dev.example.com.  A       192.0.2.10
> |   admin.example.com. A      192.0.2.11
> |_  vpn.example.com.  A       192.0.2.20
> | dns-brute:
> |   DNS Brute-force hostnames:
> |     www.example.com - 192.0.2.2
> |     mail.example.com - 192.0.2.3
> |     ftp.example.com - 192.0.2.4
> |     dev.example.com - 192.0.2.10
> |     admin.example.com - 192.0.2.11
> |     vpn.example.com - 192.0.2.20
> |     staging.example.com - 192.0.2.30
> |_    test.example.com - 192.0.2.40
> | dns-recursion: Recursion appears to be enabled
> ```

> [!warning]+ DNS OPSEC Considerations
> 1. **Zone transfer attempts**: Always logged by DNS servers, often triggers security alerts
> 2. **dns-brute visibility**: Generates hundreds to thousands of queries, extremely obvious
> 3. **Query logging**: All DNS servers log queries (standard operational practice)
> 4. **Rate limiting**: Excessive queries trigger rate limiting or blocking
> 5. **Sequential patterns**: Brute force creates distinctive sequential query patterns

> [!failure]+ Common DNS Issues
> 6. **Zone transfer denied**: Expected result on properly configured servers
>    - Solution: Modern DNS security best practice restricts AXFR to authorized secondaries
> 7. **dns-brute timeout**: Large wordlists timeout on default 5-minute script timeout
>    - Solution: Increase with `--script-timeout=30m`, reduce threads
> 8. **UDP packet loss**: DNS over UDP may drop packets on congested networks
>    - Solution: Reduce threads, try TCP zone transfer
> 9. **No response**: Firewall blocking UDP 53 or DNS server not recursive
>    - Solution: Verify port accessibility with basic UDP scan

> [!tip]+ DNS Security Assessment Best Practices
> 10. **Zone transfer**: Exposes complete DNS zone (all subdomains, internal IPs)
> 11. **Open resolver**: Allows DNS amplification DDoS attacks
> 12. **Cache snooping**: Privacy violation, reveals browsing history
> 13. **Subdomain discovery**: Reveals dev/staging/admin environments
> 14. **DNSSEC validation**: Modern security feature, enumerate with NSEC/NSEC3

> [!example]+ DNS Wordlists for Subdomain Enumeration
> 15. `/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt` - Top 5000 common subdomains
> 16. `/usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt` - Top 20000 subdomains
> 17. `/usr/share/seclists/Discovery/DNS/fierce-hostlist.txt` - Fierce DNS scanner default wordlist
> 18. `/usr/share/seclists/Discovery/DNS/bitquark-subdomains-top100000.txt` - Comprehensive 100k list
> 19. `/usr/share/seclists/Discovery/DNS/dns-Jhaddix.txt` - Jason Haddix's all-sources wordlist

---

## Port 80/443/8080/8443 - HTTP/HTTPS (Web Services)

> [!info]+ [HTTP/HTTPS Service Overview](https://developer.mozilla.org/en-US/docs/Web/HTTP)
> Hypertext Transfer Protocol and its encrypted variant HTTPS. Most common internet protocol. Web application enumeration, vulnerability detection, SSL/TLS analysis. Ports 8080/8443 commonly used for alternative web services, proxies, or application servers.

**Key NSE Scripts for HTTP/HTTPS**:

> [!info]+ HTTP/HTTPS Enumeration Scripts
> **Information Gathering**:
> 1. **[http-enum](https://nmap.org/nsedoc/scripts/http-enum.html)**: Directory and file enumeration
> 2. **[http-headers](https://nmap.org/nsedoc/scripts/http-headers.html)**: HTTP response headers
> 3. **[http-methods](https://nmap.org/nsedoc/scripts/http-methods.html)**: Supported HTTP methods
> 4. **[http-title](https://nmap.org/nsedoc/scripts/http-title.html)**: HTML page title extraction
> 5. **[http-robots.txt](https://nmap.org/nsedoc/scripts/http-robots.txt.html)**: Robots.txt retrieval
> 6. **[http-sitemap-generator](https://nmap.org/nsedoc/scripts/http-sitemap-generator.html)**: Crawls and generates sitemap
> 7. **[http-server-header](https://nmap.org/nsedoc/scripts/http-server-header.html)**: Server header extraction
> 8. **[http-generator](https://nmap.org/nsedoc/scripts/http-generator.html)**: Detects CMS/framework from meta generator tag
> 
> **Authentication Testing**:
> 1. **[http-auth](https://nmap.org/nsedoc/scripts/http-auth.html)**: Authentication scheme enumeration
> 2. **[http-brute](https://nmap.org/nsedoc/scripts/http-brute.html)**: HTTP Basic/Digest brute force
> 3. **[http-default-accounts](https://nmap.org/nsedoc/scripts/http-default-accounts.html)**: Default credential testing
> 4. **[http-form-brute](https://nmap.org/nsedoc/scripts/http-form-brute.html)**: HTML form brute force
> 5. **[http-wordpress-brute](https://nmap.org/nsedoc/scripts/http-wordpress-brute.html)**: WordPress credential brute force
> 
> **Vulnerability Detection**:
> 6. **[http-shellshock](https://nmap.org/nsedoc/scripts/http-shellshock.html)**: CVE-2014-6271 Bash vulnerability
> 7. **[http-sql-injection](https://nmap.org/nsedoc/scripts/http-sql-injection.html)**: SQL injection detection
> 8. **[http-stored-xss](https://nmap.org/nsedoc/scripts/http-stored-xss.html)**: Stored XSS detection
> 9. **[http-csrf](https://nmap.org/nsedoc/scripts/http-csrf.html)**: CSRF vulnerability detection
> 10. **[http-phpself-xss](https://nmap.org/nsedoc/scripts/http-phpself-xss.html)**: PHP_SELF XSS
> 11. **[http-vuln-cve2017-5638](https://nmap.org/nsedoc/scripts/http-vuln-cve2017-5638.html)**: Apache Struts2 RCE
> 12. **[http-vuln-cve2015-1635](https://nmap.org/nsedoc/scripts/http-vuln-cve2015-1635.html)**: IIS RCE
> 13. **[http-vuln-cve2013-7091](https://nmap.org/nsedoc/scripts/http-vuln-cve2013-7091.html)**: Zimbra LFI
> 14. **[http-vuln-cve2014-3704](https://nmap.org/nsedoc/scripts/http-vuln-cve2014-3704.html)**: Drupal SQL injection
> 15. **[http-vuln-cve2017-1001000](https://nmap.org/nsedoc/scripts/http-vuln-cve2017-1001000.html)**: WordPress 4.7.0/4.7.1 privilege escalation
> 
> **Configuration Analysis**:
> 16. **[http-security-headers](https://nmap.org/nsedoc/scripts/http-security-headers.html)**: Security header analysis
> 17. **[http-config-backup](https://nmap.org/nsedoc/scripts/http-config-backup.html)**: Backup file detection
> 18. **[http-apache-server-status](https://nmap.org/nsedoc/scripts/http-apache-server-status.html)**: Apache status page access
> 19. **[http-apache-negotiation](https://nmap.org/nsedoc/scripts/http-apache-negotiation.html)**: Apache content negotiation
> 20. **[http-git](https://nmap.org/nsedoc/scripts/http-git.html)**: Exposed .git directory detection
> 21. **[http-svn-enum](https://nmap.org/nsedoc/scripts/http-svn-enum.html)**: SVN repository enumeration
> 22. **[http-backup-finder](https://nmap.org/nsedoc/scripts/http-backup-finder.html)**: Backup file discovery
> 
> **CMS/Application Specific**:
> 23. **[http-wordpress-enum](https://nmap.org/nsedoc/scripts/http-wordpress-enum.html)**: WordPress enumeration
> 24. **[http-wordpress-users](https://nmap.org/nsedoc/scripts/http-wordpress-users.html)**: WordPress user enumeration
> 25. **[http-joomla-brute](https://nmap.org/nsedoc/scripts/http-joomla-brute.html)**: Joomla brute force
> 26. **[http-drupal-enum](https://nmap.org/nsedoc/scripts/http-drupal-enum.html)**: Drupal enumeration
> 27. **[http-frontpage-login](https://nmap.org/nsedoc/scripts/http-frontpage-login.html)**: FrontPage admin interface
> 
> **Cloud/SSRF**:
> 28. **[http-aws-metadata](https://nmap.org/nsedoc/scripts/http-aws-metadata.html)**: AWS metadata SSRF
> 29. **[http-azure-metadata](https://nmap.org/nsedoc/scripts/http-azure-metadata.html)**: Azure metadata SSRF

> [!info]+ SSL/TLS Specific Scripts (Port 443/8443)
> 30. **[ssl-cert](https://nmap.org/nsedoc/scripts/ssl-cert.html)**: SSL certificate details
> 31. **[ssl-enum-ciphers](https://nmap.org/nsedoc/scripts/ssl-enum-ciphers.html)**: Cipher suite enumeration and grading
> 32. **[ssl-heartbleed](https://nmap.org/nsedoc/scripts/ssl-heartbleed.html)**: CVE-2014-0160 Heartbleed
> 33. **[ssl-poodle](https://nmap.org/nsedoc/scripts/ssl-poodle.html)**: CVE-2014-3566 POODLE
> 34. **[ssl-ccs-injection](https://nmap.org/nsedoc/scripts/ssl-ccs-injection.html)**: CVE-2014-0224 CCS injection
> 35. **[ssl-dh-params](https://nmap.org/nsedoc/scripts/ssl-dh-params.html)**: Diffie-Hellman parameter analysis
> 36. **[ssl-known-key](https://nmap.org/nsedoc/scripts/ssl-known-key.html)**: Compromised key detection
> 37. **[ssl-date](https://nmap.org/nsedoc/scripts/ssl-date.html)**: System time from TLS handshake

```bash
# Safe HTTP enumeration
nmap -sV -p80,443,8080,8443 --script=http-title,http-headers,http-methods,http-robots.txt,http-server-header <target>

# Directory and file enumeration (noisy)
nmap -p80,443 --script=http-enum <target>

# HTTP enumeration with virtual host
nmap -p80 --script=http-enum --script-args http.host=example.com <target>

# Security headers analysis
nmap -p443 --script=http-security-headers <target>

# HTTP methods testing (PUT, DELETE, TRACE)
nmap -p80 --script=http-methods --script-args http-methods.url-path=/upload <target>

# Shellshock vulnerability
nmap -p80 --script=http-shellshock --script-args uri=/cgi-bin/status,cmd=ls <target>

# SQL injection detection
nmap -p80 --script=http-sql-injection --script-args http-sql-injection.maxdepth=3 <target>

# XSS vulnerability detection
nmap -p80 --script=http-stored-xss,http-phpself-xss <target>

# Web application vulnerability scan
nmap -p80,443 --script=http-vuln-* <target>

# Default credential testing
nmap -p80 --script=http-default-accounts <target>

# HTTP Basic/Digest brute force
nmap -p80 --script=http-brute --script-args http-brute.path=/admin/ <target>

# WordPress enumeration
nmap -p80,443 --script=http-wordpress-enum --script-args search-limit=100 <target>

# WordPress user enumeration
nmap -p80 --script=http-wordpress-users <target>

# Exposed Git repository
nmap -p80,443 --script=http-git <target>

# Backup file discovery
nmap -p80 --script=http-backup-finder,http-config-backup <target>

# Apache server-status page
nmap -p80 --script=http-apache-server-status <target>

# AWS metadata SSRF
nmap -p80 --script=http-aws-metadata --script-args http-aws-metadata.uri=/redirect?url= <target>

# SSL/TLS certificate extraction
nmap -p443,8443 --script=ssl-cert <target>

# SSL/TLS cipher enumeration and grading
nmap -p443 --script=ssl-enum-ciphers <target>

# SSL/TLS vulnerability assessment
nmap -p443 --script=ssl-heartbleed,ssl-poodle,ssl-ccs-injection,ssl-dh-params <target>

# Comprehensive HTTP enumeration (safe)
nmap -sV -p80,443,8080,8443 --script="http-* and safe" <target>

# Comprehensive HTTPS assessment
nmap -sV -p443,8443 --script="(http-* or ssl-*) and not brute" <target>

# Web application security audit
nmap -sV -p80,443 --script="http-enum,http-vuln-*,http-config-backup,http-git,http-security-headers" <target>

# Custom user agent
nmap -p80 --script=http-enum --script-args http.useragent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)" <target>

# HTTP proxy through specific port
nmap -p8080 --script=http-open-proxy <target>
```

> [!info]+ Command Breakdown: HTTP/HTTPS Enumeration
> 1. **http.host**: Virtual host specification for shared hosting environments
> 2. **http.useragent**: Custom User-Agent header (WAF evasion, mobile testing)
> 3. **http-methods.url-path**: Specific path to test methods (upload directories)
> 4. **http-sql-injection.maxdepth**: How many links deep to crawl
> 5. **http-brute.path**: Authentication endpoint path
> 6. **http-aws-metadata.uri**: SSRF-vulnerable parameter or endpoint
> 7. **tls.servername**: SNI for HTTPS virtual hosting

> [!success]+ Expected HTTP/HTTPS Output
> ```
> PORT    STATE SERVICE  VERSION
> 80/tcp  open  http     Apache httpd 2.4.29 ((Ubuntu))
> |_http-title: Welcome to Example.com
> | http-headers:
> |   Date: Sat, 25 Jan 2026 14:30:00 GMT
> |   Server: Apache/2.4.29 (Ubuntu)
> |   X-Powered-By: PHP/7.2.24
> |   Content-Type: text/html; charset=UTF-8
> |_  Connection: Keep-Alive
> | http-methods:
> |   Supported Methods: GET HEAD POST OPTIONS
> |_  Potentially risky methods: PUT DELETE TRACE
> | http-enum:
> |   /admin/: Admin login page
> |   /backup/: Backup directory
> |   /config.php.bak: Configuration backup file
> |   /test.php: Test file
> |   /.git/: Git repository
> |_  /phpmyadmin/: phpMyAdmin
> | http-robots.txt: 5 disallowed entries
> |_/admin/ /backup/ /private/ /test/ /uploads/
> 
> 443/tcp open  ssl/http Apache httpd 2.4.29
> | ssl-cert: Subject: commonName=*.example.com/organizationName=Example Inc
> | Subject Alternative Name: DNS:*.example.com, DNS:example.com
> | Not valid before: 2025-01-01T00:00:00
> |_Not valid after:  2026-01-01T00:00:00
> | ssl-enum-ciphers:
> |   TLSv1.2:
> |     ciphers:
> |       TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384 (secp256r1) - A
> |       TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 (secp256r1) - A
> |     compressors:
> |       NULL
> |     cipher preference: server
> |   least strength: A
> | http-security-headers:
> |   Strict-Transport-Security: max-age=31536000; includeSubDomains
> |   X-Frame-Options: DENY
> |   X-Content-Type-Options: nosniff
> |_  Missing headers: Content-Security-Policy, X-XSS-Protection
> | http-shellshock:
> |   VULNERABLE:
> |   HTTP Shellshock vulnerability
> |     State: VULNERABLE (Exploitable)
> |     IDs:  CVE:CVE-2014-6271
> |     Check results:
> |       Vulnerable CGI script: /cgi-bin/status
> ```

> [!warning]+ HTTP/HTTPS OPSEC Considerations
> 8. **http-enum**: Generates hundreds of 404 errors, extremely visible in access logs
> 9. **Vulnerability scripts**: Trigger WAF/IDS signatures for attack patterns
> 10. **http-brute**: Massively noisy, causes authentication failures, may lock accounts
> 11. **http-sql-injection**: Injects SQL syntax, triggers WAF blocks
> 12. **Safe scripts**: headers, methods, title, robots.txt appear as normal browsing
> 13. **Modern WAFs**: Cloudflare, AWS WAF, Imperva block most vulnerability scripts

> [!failure]+ Common HTTP/HTTPS Issues
> 14. **WAF blocking**: HTTP 403/429 responses or connection resets
>    - Solution: Reduce timing (`-T2`), customize user agent, add delays
> 15. **Virtual hosting**: Wrong Host header returns default site
>    - Solution: Use `--script-args http.host=example.com`
> 16. **SSL/TLS errors**: HTTPS scripts fail without proper handshake
>    - Solution: Use `-sV` or `--script-args http.ssl=true` for non-standard ports
> 17. **Timeouts**: Slow applications or WAF delays timeout scripts
>    - Solution: Increase `--script-timeout=120s`
> 18. **Authentication required**: Scripts return empty results on protected resources
>    - Solution: Provide credentials with http.username/http.password arguments
> 19. **http-enum false positives**: WAF may fake directory responses
>    - Solution: Manually verify findings with browser or curl

> [!tip]+ HTTP/HTTPS Security Assessment Best Practices
> 20. **Security headers**: Missing HSTS, CSP, X-Frame-Options indicate weaknesses
> 21. **Dangerous methods**: PUT, DELETE, TRACE should be disabled
> 22. **Directory listing**: Exposed directories reveal sensitive files
> 23. **Backup files**: .bak, .old, .backup files contain credentials/configs
> 24. **Version disclosure**: Server/X-Powered-By headers aid vulnerability research
> 25. **SSL/TLS grading**: Grade B or below indicates weak cryptography
> 26. **WordPress/CMS**: Outdated versions have known RCE vulnerabilities
> 27. **Git exposure**: /.git/ directory allows source code download

> [!example]+ HTTP Script Arguments Reference
> 28. **http.host=<hostname>**: Virtual host specification
> 29. **http.useragent=<string>**: Custom User-Agent header
> 30. **http.max-pipeline=<num>**: HTTP pipelining depth
> 31. **http-brute.path=<path>**: Authentication endpoint
> 32. **http-brute.method=POST**: HTTP method for auth
> 33. **http-enum.displayall=true**: Show all tested paths
> 34. **http-sql-injection.maxdepth=<num>**: Crawl depth
> 35. **uri=<path>**: Script-specific URI path
> 36. **tls.servername=<name>**: SNI for virtual HTTPS hosts

---

## Port 88 - Kerberos

> [!info]+ [Kerberos Service Overview](https://web.mit.edu/kerberos/)
> Authentication protocol used by Active Directory and Unix systems. Port 88 TCP/UDP for Kerberos authentication. User enumeration reveals valid domain accounts without authentication.

**Key NSE Scripts for Kerberos**:

> [!info]+ Kerberos Enumeration Scripts
> 1. **[krb5-enum-users](https://nmap.org/nsedoc/scripts/krb5-enum-users.html)**: User account enumeration via Kerberos pre-authentication

```bash
# Kerberos user enumeration
nmap -p88 --script=krb5-enum-users --script-args krb5-enum-users.realm=DOMAIN.COM <dc-ip>

# User enumeration with custom wordlist
nmap -p88 --script=krb5-enum-users --script-args krb5-enum-users.realm=CONTOSO.LOCAL,userdb=/usr/share/seclists/Usernames/xato-net-10-million-usernames.txt <dc-ip>

# Enumerate common service accounts
nmap -p88 --script=krb5-enum-users --script-args krb5-enum-users.realm=DOMAIN.COM,userdb=/usr/share/seclists/Usernames/cirt-default-usernames.txt <dc-ip>

# Fast user enumeration (limited wordlist)
nmap -p88 --script=krb5-enum-users --script-args krb5-enum-users.realm=DOMAIN.COM,userdb=/usr/share/seclists/Usernames/top-usernames-shortlist.txt <dc-ip>
```

> [!info]+ Command Breakdown: Kerberos Enumeration
> 1. **krb5-enum-users.realm**: Active Directory domain name (FQDN)
> 2. **userdb**: Username wordlist path
> 3. *Script distinguishes valid from invalid users via Kerberos error codes*
> 4. *KRB5KDC_ERR_PREAUTH_REQUIRED = valid user*
> 5. *KRB5KDC_ERR_C_PRINCIPAL_UNKNOWN = invalid user*

> [!success]+ Expected Kerberos Output
> ```
> PORT   STATE SERVICE
> 88/tcp open  kerberos-sec
> | krb5-enum-users:
> |   Discovered Kerberos principals:
> |     administrator@CONTOSO.LOCAL
> |     Administrator@CONTOSO.LOCAL
> |     guest@CONTOSO.LOCAL
> |     krbtgt@CONTOSO.LOCAL
> |     sqlservice@CONTOSO.LOCAL
> |     webadmin@CONTOSO.LOCAL
> |_  Statistics: Performed 500 guesses in 34 seconds
> ```

> [!warning]+ Kerberos OPSEC Considerations
> 6. **Windows Event Logs**: Pre-auth failures logged (Event ID 4768, 4771)
> 7. **Detection**: Modern monitoring tools detect user enumeration patterns
> 8. **SIEM alerts**: Multiple pre-auth failures from single IP trigger alerts
> 9. **Account lockout**: Enumeration doesn't trigger lockout (pre-auth only)
> 10. **Noise level**: Moderate - generates authentication attempts but not full logins

> [!tip]+ Kerberos Security Assessment Notes
> 11. **User enumeration**: Reveals valid domain accounts for password spraying
> 12. **Service accounts**: Accounts ending in "service", "admin", "sql" are high-value
> 13. **Disabled accounts**: Script doesn't distinguish disabled from enabled accounts
> 14. **Case sensitivity**: Windows usernames case-insensitive, test lowercase variants
> 15. **Follow-up**: Valid users enable targeted password spraying attacks

---

## Port 110/995 - POP3/POP3S (Post Office Protocol)

> [!info]+ [POP3 Service Overview](https://en.wikipedia.org/wiki/Post_Office_Protocol)
> Email retrieval protocol. Port 110 for unencrypted POP3, 995 for POP3S (SSL/TLS). Commonly used for email client access to mailboxes.

**Key NSE Scripts for POP3**:

> [!info]+ POP3 Enumeration Scripts
> 1. **[pop3-capabilities](https://nmap.org/nsedoc/scripts/pop3-capabilities.html)**: Lists POP3 capabilities
> 2. **[pop3-brute](https://nmap.org/nsedoc/scripts/pop3-brute.html)**: Credential brute forcing
> 3. **[pop3-ntlm-info](https://nmap.org/nsedoc/scripts/pop3-ntlm-info.html)**: Domain disclosure via NTLM

```bash
# POP3 capability enumeration
nmap -sV -p110,995 --script=pop3-capabilities <target>

# POP3 NTLM information disclosure
nmap -p110,995 --script=pop3-ntlm-info <target>

# POP3 brute force (noisy)
nmap -p110 --script=pop3-brute --script-args userdb=users.txt,passdb=pass.txt <target>

# Comprehensive POP3 assessment
nmap -sV -p110,995 --script="pop3-* and not brute" <target>
```

> [!success]+ Expected POP3 Output
> ```
> PORT    STATE SERVICE VERSION
> 110/tcp open  pop3    Dovecot pop3d
> | pop3-capabilities: RESP-CODES CAPA SASL PLAIN LOGIN UIDL TOP PIPELINING
> |_  Capabilities: TOP UIDL RESP-CODES CAPA SASL(PLAIN LOGIN) PIPELINING
> | pop3-ntlm-info:
> |   Target_Name: MAIL
> |   NetBIOS_Domain_Name: CONTOSO
> |   NetBIOS_Computer_Name: MAIL01
> |   DNS_Domain_Name: contoso.local
> |   DNS_Computer_Name: mail01.contoso.local
> ```

> [!warning]+ POP3 OPSEC Considerations
> 1. **pop3-brute**: Extremely noisy, triggers fail2ban and account lockouts
> 2. **Capability queries**: Safe, normal POP3 client behavior
> 3. **NTLM info disclosure**: Reveals internal domain names without authentication

---

## Port 111 - RPCBind

> [!info]+ [RPCBind Service Overview](https://en.wikipedia.org/wiki/Portmap)
> Remote Procedure Call port mapper. Maps RPC program numbers to network ports. Common on Unix/Linux systems. Reveals running RPC services including NFS, NIS, and other distributed services.

**Key NSE Scripts for RPCBind**:

> [!info]+ RPCBind Enumeration Scripts
> 1. **[rpcinfo](https://nmap.org/nsedoc/scripts/rpcinfo.html)**: Lists registered RPC services
> 2. **[nfs-showmount](https://nmap.org/nsedoc/scripts/nfs-showmount.html)**: Lists NFS exports (if NFS available)
> 3. **[nfs-ls](https://nmap.org/nsedoc/scripts/nfs-ls.html)**: Lists NFS directory contents
> 4. **[nfs-statfs](https://nmap.org/nsedoc/scripts/nfs-statfs.html)**: NFS filesystem statistics

```bash
# RPC service enumeration
nmap -sV -p111 --script=rpcinfo <target>

# NFS export enumeration
nmap -p111 --script=nfs-showmount <target>

# List NFS directory contents
nmap -p111 --script=nfs-ls --script-args nfs-ls.export=/share <target>

# NFS filesystem statistics
nmap -p111 --script=nfs-statfs <target>

# Comprehensive RPC/NFS assessment
nmap -sV -p111,2049 --script="rpc*,nfs*" <target>
```

> [!success]+ Expected RPCBind Output
> ```
> PORT    STATE SERVICE VERSION
> 111/tcp open  rpcbind 2-4 (RPC #100000)
> | rpcinfo:
> |   program version    port/proto  service
> |   100000  2,3,4        111/tcp   rpcbind
> |   100000  2,3,4        111/udp   rpcbind
> |   100003  2,3,4       2049/tcp   nfs
> |   100003  2,3,4       2049/udp   nfs
> |   100005  1,2,3      20048/tcp   mountd
> |_  100005  1,2,3      20048/udp   mountd
> | nfs-showmount:
> |   /home 192.168.1.0/24
> |   /var/nfs *
> |_  /backups (everyone)
> ```

> [!tip]+ RPCBind Security Assessment Notes
> 1. **rpcinfo**: Reveals all RPC services and ports
> 2. **NFS exports**: Shows shared filesystems and access controls
> 3. **Wildcard exports**: `*` or `(everyone)` indicates world-readable shares
> 4. **Sensitive paths**: /home, /root, /etc, /backup exports critical

---

## Port 135/593 - Microsoft RPC (MSRPC)

> [!info]+ [Microsoft RPC Overview](https://docs.microsoft.com/en-us/windows/win32/rpc/rpc-start-page)
> Microsoft Remote Procedure Call endpoint mapper. Port 135 for RPC endpoint mapper, 593 for RPC over HTTP. Critical Windows service for DCOM, WMI, and distributed services.

**Key NSE Scripts for MSRPC**:

> [!info]+ MSRPC Enumeration Scripts
> 1. **[msrpc-enum](https://nmap.org/nsedoc/scripts/msrpc-enum.html)**: Enumerates MSRPC endpoints
> 2. **[smb-os-discovery](https://nmap.org/nsedoc/scripts/smb-os-discovery.html)**: OS discovery via RPC (works on 135)
> 3. **[smb-enum-domains](https://nmap.org/nsedoc/scripts/smb-enum-domains.html)**: Domain enumeration

```bash
# MSRPC endpoint enumeration
nmap -sV -p135,593 --script=msrpc-enum <target>

# OS discovery via RPC
nmap -p135 --script=smb-os-discovery <target>

# Comprehensive MSRPC assessment
nmap -sV -p135,139,445,593 --script="msrpc-enum,smb-os-discovery" <target>
```

> [!success]+ Expected MSRPC Output
> ```
> PORT    STATE SERVICE VERSION
> 135/tcp open  msrpc   Microsoft Windows RPC
> | msrpc-enum:
> |   Endpoints:
> |     uuid: 12345778-1234-abcd-ef00-0123456789ab ncacn_ip_tcp:192.168.1.10[49152]
> |     uuid: 12345778-1234-abcd-ef00-0123456789ac ncacn_ip_tcp:192.168.1.10[49153]
> |_    uuid: 12345778-1234-abcd-ef00-0123456789ad ncacn_ip_tcp:192.168.1.10[49154]
> ```

> [!tip]+ MSRPC Security Assessment Notes
> 1. **Endpoint mapper**: Reveals dynamic RPC ports
> 2. **High ports**: MSRPC services commonly on ports 49152-65535
> 3. **Authentication**: Most MSRPC services require Windows credentials
> 4. **WMI**: Uses MSRPC on port 135 for remote management

---

## Port 139/445 - SMB/NetBIOS (Covered in detail earlier, key reference)

> [!info]+ SMB/NetBIOS Quick Reference
> See **SMB/Windows Service Scripts Deep Dive** section above for comprehensive coverage. Port 139 for NetBIOS session service (legacy), 445 for SMB over TCP (modern).

**Essential SMB Commands**:
```bash
# Quick SMB enumeration
nmap -p139,445 --script=smb-os-discovery,smb-security-mode,smb-enum-shares <target>

# EternalBlue check
nmap -p445 --script=smb-vuln-ms17-010 <target>

# Comprehensive SMB assessment
nmap -sV -p139,445 --script="smb-* and not brute" <target>
```

---

## Port 143/993 - IMAP/IMAPS (Internet Message Access Protocol)

> [!info]+ [IMAP Service Overview](https://en.wikipedia.org/wiki/Internet_Message_Access_Protocol)
> Email retrieval protocol with advanced features (folders, server-side search). Port 143 for unencrypted IMAP, 993 for IMAPS (SSL/TLS). More feature-rich than POP3.

**Key NSE Scripts for IMAP**:

> [!info]+ IMAP Enumeration Scripts
> 1. **[imap-capabilities](https://nmap.org/nsedoc/scripts/imap-capabilities.html)**: Lists IMAP capabilities
> 2. **[imap-brute](https://nmap.org/nsedoc/scripts/imap-brute.html)**: Credential brute forcing
> 3. **[imap-ntlm-info](https://nmap.org/nsedoc/scripts/imap-ntlm-info.html)**: Domain disclosure via NTLM

```bash
# IMAP capability enumeration
nmap -sV -p143,993 --script=imap-capabilities <target>

# IMAP NTLM information disclosure
nmap -p143,993 --script=imap-ntlm-info <target>

# IMAP brute force (noisy)
nmap -p143 --script=imap-brute --script-args userdb=users.txt,passdb=pass.txt <target>

# Comprehensive IMAP assessment
nmap -sV -p143,993 --script="imap-* and not brute" <target>
```

> [!success]+ Expected IMAP Output
> ```
> PORT    STATE SERVICE VERSION
> 143/tcp open  imap    Dovecot imapd
> | imap-capabilities: IMAP4rev1 SASL-IR LOGIN-REFERRALS ID ENABLE LITERAL+ STARTTLS AUTH=PLAIN AUTH=LOGIN
> |_  Capabilities: IMAP4rev1 LITERAL+ SASL-IR LOGIN-REFERRALS ID ENABLE STARTTLS AUTH=PLAIN AUTH=LOGIN
> | imap-ntlm-info:
> |   Target_Name: MAIL
> |   NetBIOS_Domain_Name: CONTOSO
> |   NetBIOS_Computer_Name: MAIL01
> |   DNS_Domain_Name: contoso.local
> |   DNS_Computer_Name: mail01.contoso.local
> ```

> [!warning]+ IMAP OPSEC Considerations
> 1. **imap-brute**: Extremely noisy, triggers fail2ban and account lockouts
> 2. **Capability queries**: Safe, normal IMAP client behavior
> 3. **NTLM info disclosure**: Reveals internal domain names without authentication

---

## Port 161/162 - SNMP (Simple Network Management Protocol)

> [!info]+ SNMP Quick Reference
> See **SNMP Service Scripts Deep Dive** section above for comprehensive coverage. Port 161 for queries (UDP), 162 for traps (UDP).

**Essential SNMP Commands**:
```bash
# Quick SNMP enumeration
nmap -sU -p161 --script=snmp-info,snmp-interfaces <target>

# SNMP community string brute force
nmap -sU -p161 --script=snmp-brute <target>

# Comprehensive SNMP assessment
nmap -sU -p161 --script="snmp-* and not brute" <target>
```

---

## Port 389/636/3268/3269 - LDAP/LDAPS/Global Catalog

> [!info]+ [LDAP Service Overview](https://ldap.com/)
> Lightweight Directory Access Protocol for directory services. Port 389 for LDAP, 636 for LDAPS (SSL/TLS), 3268 for Global Catalog (AD), 3269 for Global Catalog SSL. Active Directory primary protocol.

**Key NSE Scripts for LDAP**:

> [!info]+ LDAP Enumeration Scripts
> 1. **[ldap-rootdse](https://nmap.org/nsedoc/scripts/ldap-rootdse.html)**: Anonymous directory enumeration
> 2. **[ldap-search](https://nmap.org/nsedoc/scripts/ldap-search.html)**: LDAP object search (requires auth)
> 3. **[ldap-brute](https://nmap.org/nsedoc/scripts/ldap-brute.html)**: Credential brute forcing

```bash
# Anonymous LDAP enumeration (rootDSE)
nmap -p389,636 --script=ldap-rootdse <target>

# LDAP search with credentials
nmap -p389 --script=ldap-search --script-args ldap.username="CN=user,DC=domain,DC=com",ldap.password=password <target>

# LDAP brute force (noisy)
nmap -p389 --script=ldap-brute --script-args userdb=users.txt,passdb=pass.txt <target>

# Global Catalog enumeration
nmap -p3268,3269 --script=ldap-rootdse <target>

# Comprehensive LDAP assessment
nmap -sV -p389,636,3268,3269 --script="ldap-* and not brute" <target>
```

> [!success]+ Expected LDAP Output
> ```
> PORT    STATE SERVICE VERSION
> 389/tcp open  ldap    Microsoft Windows Active Directory LDAP (Domain: contoso.local, Site: Default-First-Site-Name)
> | ldap-rootdse:
> |   LDAP Results
> |     domainFunctionality: 7
> |     forestFunctionality: 7
> |     domainControllerFunctionality: 7
> |     rootDomainNamingContext: DC=contoso,DC=local
> |     ldapServiceName: contoso.local:dc01$@CONTOSO.LOCAL
> |     isGlobalCatalogReady: TRUE
> |     supportedSASLMechanisms: GSSAPI, GSS-SPNEGO, EXTERNAL, DIGEST-MD5
> |     dnsHostName: dc01.contoso.local
> |     defaultNamingContext: DC=contoso,DC=local
> |     serverName: CN=DC01,CN=Servers,CN=Default-First-Site-Name,CN=Sites,CN=Configuration,DC=contoso,DC=local
> ```

> [!tip]+ LDAP Security Assessment Notes
> 1. **ldap-rootdse**: Reveals domain structure, forest functional level, DC names
> 2. **Anonymous binding**: Some LDAP servers allow anonymous rootDSE queries
> 3. **Functional level**: Indicates Windows Server version (7 = Server 2016+)
> 4. **Global Catalog**: Ports 3268/3269 indicate domain controller
> 5. **LDAP signing**: Modern AD enforces LDAP signing and channel binding

---

## Port 443 - HTTPS (Covered in Port 80/443 section, SSL/TLS focus)

> [!info]+ HTTPS Quick Reference
> See **Port 80/443/8080/8443 - HTTP/HTTPS** section above for comprehensive coverage.

**Essential HTTPS Commands**:
```bash
# SSL/TLS assessment
nmap -p443 --script=ssl-cert,ssl-enum-ciphers,ssl-heartbleed,ssl-poodle <target>

# Comprehensive HTTPS security audit
nmap -sV -p443 --script="(http-* or ssl-*) and not brute" <target>
```

---

## Port 514 - Syslog

> [!info]+ [Syslog Service Overview](https://en.wikipedia.org/wiki/Syslog)
> System logging protocol. Port 514 UDP for syslog. Centralized logging service commonly used by network devices and Unix/Linux systems.

**Key NSE Scripts for Syslog**:

> [!info]+ Syslog Enumeration Scripts
> 1. **[syslog-detect](https://nmap.org/nsedoc/scripts/syslog-detect.html)**: Detects syslog service

```bash
# Syslog detection
nmap -sU -p514 --script=syslog-detect <target>

# Test syslog message injection
nmap -sU -p514 --script=syslog-detect --script-args syslog-detect.facility=user,syslog-detect.severity=info <target>
```

> [!warning]+ Syslog Security Notes
> 1. **Open syslog**: Allows log injection attacks
> 2. **Information disclosure**: May reveal system details in error messages
> 3. **DoS potential**: Log flooding can fill disk space

---

## Port 873 - Rsync

> [!info]+ [Rsync Service Overview](https://rsync.samba.org/)
> File synchronization and transfer protocol. Port 873 for rsync daemon. Commonly used for backups and mirroring.

**Key NSE Scripts for Rsync**:

> [!info]+ Rsync Enumeration Scripts
> 1. **[rsync-list-modules](https://nmap.org/nsedoc/scripts/rsync-list-modules.html)**: Lists available rsync modules
> 2. **[rsync-brute](https://nmap.org/nsedoc/scripts/rsync-brute.html)**: Credential brute forcing

```bash
# List rsync modules
nmap -p873 --script=rsync-list-modules <target>

# Rsync brute force
nmap -p873 --script=rsync-brute --script-args userdb=users.txt,passdb=pass.txt <target>

# Comprehensive rsync assessment
nmap -sV -p873 --script="rsync-*" <target>
```

> [!success]+ Expected Rsync Output
> ```
> PORT    STATE SERVICE VERSION
> 873/tcp open  rsync   (protocol version 31)
> | rsync-list-modules:
> |   backup      Backup files
> |   data        Data directory
> |   home        Home directories
> |_  www         Web root
> ```

> [!tip]+ Rsync Security Assessment Notes
> 1. **Anonymous access**: Some rsync modules allow unauthenticated access
> 2. **Sensitive paths**: backup, home, www modules may contain sensitive data
> 3. **Write access**: Writable modules allow file upload/modification

---

## Port 1433/1434 - Microsoft SQL Server (MSSQL)

> [!info]+ MSSQL Quick Reference
> See **Database Service Scripts Deep Dive** section for comprehensive coverage. Port 1433 for SQL Server, 1434 UDP for SQL Server Browser.

**Essential MSSQL Commands**:
```bash
# Quick MSSQL enumeration
nmap -p1433 --script=ms-sql-info,ms-sql-ntlm-info <target>

# MSSQL brute force
nmap -p1433 --script=ms-sql-brute <target>

# Comprehensive MSSQL assessment
nmap -sV -p1433 --script="ms-sql-* and not brute" <target>
```

---

## Port 1521 - Oracle Database

> [!info]+ Oracle Database Quick Reference
> See **Database Service Scripts Deep Dive** section for comprehensive coverage.

**Essential Oracle Commands**:
```bash
# Oracle SID brute force
nmap -p1521 --script=oracle-sid-brute <target>

# Oracle credential brute force
nmap -p1521 --script=oracle-brute --script-args sid=ORCL <target>
```

---

## Port 2049 - NFS (Network File System)

> [!info]+ [NFS Service Overview](https://en.wikipedia.org/wiki/Network_File_System)
> Network File System for Unix/Linux file sharing. Port 2049 for NFSv3/v4. Requires RPCBind (port 111) for NFSv3.

**Key NSE Scripts for NFS**:

> [!info]+ NFS Enumeration Scripts
> 1. **[nfs-showmount](https://nmap.org/nsedoc/scripts/nfs-showmount.html)**: Lists NFS exports
> 2. **[nfs-ls](https://nmap.org/nsedoc/scripts/nfs-ls.html)**: Lists directory contents
> 3. **[nfs-statfs](https://nmap.org/nsedoc/scripts/nfs-statfs.html)**: Filesystem statistics

```bash
# List NFS exports
nmap -p111,2049 --script=nfs-showmount <target>

# List directory contents
nmap -p2049 --script=nfs-ls --script-args nfs.export=/share <target>

# NFS filesystem statistics
nmap -p2049 --script=nfs-statfs <target>

# Comprehensive NFS assessment
nmap -sV -p111,2049 --script="nfs-*" <target>
```

> [!success]+ Expected NFS Output
> ```
> PORT     STATE SERVICE VERSION
> 2049/tcp open  nfs     3-4 (RPC #100003)
> | nfs-showmount:
> |   /home 192.168.1.0/24
> |   /var/nfs *
> |_  /backups (everyone)
> | nfs-ls: Volume /home
> |   access: Read Lookup NoModify NoExtend NoDelete NoExecute
> |   PERMISSION  UID  GID  SIZE  TIME                 FILENAME
> |   drwxr-xr-x  1000 1000 4096  2026-01-20T10:30:00  user1
> |   drwxr-xr-x  1001 1001 4096  2026-01-21T14:15:00  user2
> |_  drwxr-xr-x  1002 1002 4096  2026-01-22T09:45:00  admin
> ```

> [!warning]+ NFS Security Considerations
> 1. **Wildcard exports**: `*` or `(everyone)` allows world access
> 2. **Sensitive paths**: /home, /root, /etc exports reveal user data
> 3. **no_root_squash**: Allows client root to be server root (critical)
> 4. **NFSv3 vs NFSv4**: NFSv4 has better security (Kerberos support)

---

## Port 3306 - MySQL/MariaDB

> [!info]+ MySQL Quick Reference
> See **Database Service Scripts Deep Dive** section for comprehensive coverage.

**Essential MySQL Commands**:
```bash
# Quick MySQL enumeration
nmap -p3306 --script=mysql-info,mysql-empty-password <target>

# MySQL brute force
nmap -p3306 --script=mysql-brute <target>

# Comprehensive MySQL assessment
nmap -sV -p3306 --script="mysql-* and not brute" <target>
```

---

## Port 3389 - RDP (Remote Desktop Protocol)

> [!info]+ [RDP Service Overview](https://docs.microsoft.com/en-us/windows-server/remote/remote-desktop-services/clients/remote-desktop-clients)
> Remote Desktop Protocol for Windows graphical remote access. Port 3389 TCP. Critical service for Windows administration.

**Key NSE Scripts for RDP**:

> [!info]+ RDP Enumeration Scripts
> 1. **[rdp-enum-encryption](https://nmap.org/nsedoc/scripts/rdp-enum-encryption.html)**: Enumerates encryption methods
> 2. **[rdp-ntlm-info](https://nmap.org/nsedoc/scripts/rdp-ntlm-info.html)**: Domain disclosure via NTLM
> 3. **[rdp-vuln-ms12-020](https://nmap.org/nsedoc/scripts/rdp-vuln-ms12-020.html)**: MS12-020 vulnerability

```bash
# RDP encryption enumeration
nmap -p3389 --script=rdp-enum-encryption <target>

# RDP NTLM information disclosure
nmap -p3389 --script=rdp-ntlm-info <target>

# RDP vulnerability assessment
nmap -p3389 --script=rdp-vuln-ms12-020 <target>

# Comprehensive RDP assessment
nmap -sV -p3389 --script="rdp-*" <target>
```

> [!success]+ Expected RDP Output
> ```
> PORT     STATE SERVICE VERSION
> 3389/tcp open  ms-wbt-server Microsoft Terminal Services
> | rdp-enum-encryption:
> |   Security layer
> |     CredSSP (NLA): SUCCESS
> |     CredSSP with Early User Auth: SUCCESS
> |     Native RDP: SUCCESS
> |     SSL: SUCCESS
> |   RDP Encryption level: High
> |     128-bit RC4: SUCCESS
> |_  FIPS 140-1: SUCCESS
> | rdp-ntlm-info:
> |   Target_Name: WORKSTATION
> |   NetBIOS_Domain_Name: CONTOSO
> |   NetBIOS_Computer_Name: WS01
> |   DNS_Domain_Name: contoso.local
> |   DNS_Computer_Name: ws01.contoso.local
> |   Product_Version: 10.0.17763
> ```

> [!tip]+ RDP Security Assessment Notes
> 1. **NLA (Network Level Authentication)**: Modern security requiring auth before session
> 2. **Encryption level**: High/FIPS better than Low/Medium
> 3. **rdp-ntlm-info**: Reveals domain and computer names without authentication
> 4. **MS12-020**: Denial of service vulnerability (Server 2008 and earlier)
> 5. **BlueKeep (CVE-2019-0708)**: RCE vulnerability (pre-patch Server 2008/Windows 7)

---

## Port 5432 - PostgreSQL

> [!info]+ PostgreSQL Quick Reference
> See **Database Service Scripts Deep Dive** section for comprehensive coverage.

**Essential PostgreSQL Commands**:
```bash
# PostgreSQL brute force
nmap -p5432 --script=pgsql-brute <target>

# PostgreSQL with credentials
nmap -p5432 --script=pgsql-brute --script-args userdb=users.txt,passdb=pass.txt <target>
```

---

## Port 5900-5909 - VNC (Virtual Network Computing)

> [!info]+ [VNC Service Overview](https://en.wikipedia.org/wiki/Virtual_Network_Computing)
> Virtual Network Computing for graphical remote access. Ports 5900-5909 (display :0-:9). Cross-platform remote desktop protocol.

**Key NSE Scripts for VNC**:

> [!info]+ VNC Enumeration Scripts
> 1. **[vnc-info](https://nmap.org/nsedoc/scripts/vnc-info.html)**: VNC server information
> 2. **[vnc-brute](https://nmap.org/nsedoc/scripts/vnc-brute.html)**: Password brute forcing
> 3. **[realvnc-auth-bypass](https://nmap.org/nsedoc/scripts/realvnc-auth-bypass.html)**: RealVNC authentication bypass

```bash
# VNC server information
nmap -sV -p5900 --script=vnc-info <target>

# VNC authentication bypass check
nmap -p5900 --script=realvnc-auth-bypass <target>

# VNC password brute force
nmap -p5900 --script=vnc-brute <target>

# Scan VNC display range
nmap -p5900-5909 --script=vnc-info <target>

# Comprehensive VNC assessment
nmap -sV -p5900-5909 --script="vnc-* and not brute" <target>
```

> [!success]+ Expected VNC Output
> ```
> PORT     STATE SERVICE VERSION
> 5900/tcp open  vnc     RealVNC 4.1.2 (protocol 3.8)
> | vnc-info:
> |   Protocol version: 3.8
> |   Security types:
> |     VNC Authentication (2)
> |_    Tight (16)
> ```

> [!warning]+ VNC Security Considerations
> 1. **No encryption**: VNC transmits data unencrypted (use SSH tunnel)
> 2. **Password-only auth**: VNC typically uses single password, no usernames
> 3. **realvnc-auth-bypass**: Critical vulnerability in RealVNC 4.1.0/4.1.1
> 4. **vnc-brute throttling**: VNC servers often throttle connection attempts
> 5. **Default passwords**: Many VNC installations use weak or default passwords

---

## Port 6379 - Redis

> [!info]+ Redis Quick Reference
> See **Database Service Scripts Deep Dive** section for comprehensive coverage.

**Essential Redis Commands**:
```bash
# Redis information gathering
nmap -p6379 --script=redis-info <target>

# Redis brute force
nmap -p6379 --script=redis-brute <target>
```

---

## Port 8080/8443 - Alternative HTTP/HTTPS

> [!info]+ Alternative HTTP Ports Quick Reference
> See **Port 80/443/8080/8443 - HTTP/HTTPS** section for comprehensive coverage. Commonly used for web application servers, proxies, management interfaces.

**Essential Commands**:
```bash
# Quick web enumeration on alternative ports
nmap -sV -p8080,8443 --script=http-title,http-headers,http-methods <target>

# Comprehensive assessment
nmap -sV -p8080,8443 --script="(http-* or ssl-*) and safe" <target>
```

---

## Port 9200/9300 - Elasticsearch

> [!info]+ Elasticsearch Quick Reference
> See **Database Service Scripts Deep Dive** section for comprehensive coverage. Port 9200 for HTTP API, 9300 for node communication.

**Essential Elasticsearch Commands**:
```bash
# Elasticsearch cluster information
nmap -p9200 --script=elasticsearch-info <target>

# Elasticsearch via HTTP enumeration
nmap -p9200 --script=http-title,http-headers <target>
```

---

## Port 27017/27018 - MongoDB

> [!info]+ MongoDB Quick Reference
> See **Database Service Scripts Deep Dive** section for comprehensive coverage. Port 27017 for MongoDB, 27018 for shard server.

**Essential MongoDB Commands**:
```bash
# MongoDB information gathering
nmap -p27017 --script=mongodb-info,mongodb-databases <target>

# MongoDB brute force
nmap -p27017 --script=mongodb-brute <target>
```

---

## Port Range Summary Table

| Port(s) | Service | Safe Scripts | Vuln Scripts | Brute Scripts | OPSEC Risk |
|:---|:---|:---|:---|:---|:---|
| 20-21 | FTP | ftp-anon, ftp-syst | ftp-vuln-*, ftp-vsftpd-backdoor | ftp-brute | Medium |
| 22 | SSH | ssh-hostkey, ssh-auth-methods, ssh2-enum-algos | sshv1 | ssh-brute | Very High |
| 23 | Telnet | telnet-encryption, telnet-ntlm-info | - | telnet-brute | High |
| 25/587 | SMTP | smtp-commands, smtp-ntlm-info | smtp-vuln-* | smtp-brute, smtp-enum-users | High |
| 53 | DNS | dns-recursion, dns-nsid | - | dns-brute, dns-zone-transfer | Very High |
| 80/443 | HTTP/S | http-title, http-headers, ssl-cert | http-vuln-*, ssl-* | http-brute | Medium-High |
| 88 | Kerberos | - | - | krb5-enum-users | Medium |
| 110/995 | POP3 | pop3-capabilities, pop3-ntlm-info | - | pop3-brute | High |
| 111 | RPCBind | rpcinfo, nfs-showmount | - | - | Low |
| 135 | MSRPC | msrpc-enum | - | - | Low |
| 139/445 | SMB | smb-os-discovery, smb-security-mode | smb-vuln-* | smb-brute | Medium |
| 143/993 | IMAP | imap-capabilities, imap-ntlm-info | - | imap-brute | High |
| 161 | SNMP | snmp-info, snmp-interfaces | - | snmp-brute | Medium |
| 389/636 | LDAP | ldap-rootdse | - | ldap-brute | Medium |
| 514 | Syslog | syslog-detect | - | - | Low |
| 873 | Rsync | rsync-list-modules | - | rsync-brute | Medium |
| 1433 | MSSQL | ms-sql-info, ms-sql-ntlm-info | ms-sql-vuln-* | ms-sql-brute | Medium |
| 1521 | Oracle | - | - | oracle-sid-brute, oracle-brute | High |
| 2049 | NFS | nfs-showmount, nfs-ls | - | - | Low |
| 3306 | MySQL | mysql-info, mysql-empty-password | - | mysql-brute | High |
| 3389 | RDP | rdp-enum-encryption, rdp-ntlm-info | rdp-vuln-ms12-020 | - | Low |
| 5432 | PostgreSQL | - | - | pgsql-brute | High |
| 5900 | VNC | vnc-info | realvnc-auth-bypass | vnc-brute | Medium |
| 6379 | Redis | redis-info | - | redis-brute | Medium |
| 8080/8443 | Alt HTTP/S | http-title, http-headers | http-vuln-*, ssl-* | http-brute | Medium-High |
| 9200 | Elasticsearch | elasticsearch-info | - | - | Low |
| 27017 | MongoDB | mongodb-info, mongodb-databases | - | mongodb-brute | Medium |

---

## Multi-Port Scanning Strategies

> [!tip]+ Efficient Multi-Service Enumeration
> Scan multiple related services simultaneously to build comprehensive target profile.

```bash
# Full TCP common port scan with default scripts
nmap -sC -sV -p- <target> -oA full_tcp_scan

# Top 1000 ports with safe enumeration
nmap -sV --script="safe and not intrusive" --top-ports 1000 <target> -oA top1000_safe

# All database ports
nmap -sV --script="(mysql-* or ms-sql-* or oracle-* or mongodb-* or redis-* or pgsql-*) and not brute" -p1433,1521,3306,5432,6379,9200,27017 <target> -oA databases

# All Windows/AD ports
nmap -sV --script="(smb-* or ldap-* or msrpc-* or rdp-* or krb5-*) and not brute" -p88,135,139,389,445,636,3268,3269,3389 <target> -oA windows_ad

# All mail ports
nmap -sV --script="(smtp-* or pop3-* or imap-*) and not brute" -p25,110,143,465,587,993,995 <target> -oA mail_services

# All web ports
nmap -sV --script="(http-* or ssl-*) and safe" -p80,443,8080,8081,8443,8888,9090 <target> -oA web_services

# Complete service enumeration (safe only, no brute)
nmap -sS -sU -sV --script="safe and not brute" -p T:21-23,25,53,80,88,110,111,135,139,143,389,443,445,636,1433,1521,2049,3306,3389,5432,5900,6379,8080,8443,9200,27017,U:53,161,514 <target> -oA complete_safe_enum
```

---

## References

1. [Nmap Official Documentation](https://nmap.org/book/)
2. [NSE Documentation Portal](https://nmap.org/nsedoc/)
3. [NSE Script Categories Reference](https://nmap.org/book/nse-usage.html)
4. [Port Number Registry (IANA)](https://www.iana.org/assignments/service-names-port-numbers/)
5. [Common Ports List](https://www.speedguide.net/ports.php)
6. [HackTricks - Network Service Pentesting](https://book.hacktricks.xyz/network-services-pentesting)
7. [MITRE ATT&CK Framework](https://attack.mitre.org/)
8. [SecLists Wordlist Repository](https://github.com/danielmiessler/SecLists)
9. [RFC Index](https://www.rfc-editor.org/rfc-index.html)
10. [CVE Database](https://cve.mitre.org/)

---

#Nmap #NSE #NetworkEnumeration #ServiceDetection #VulnerabilityScanning #Reconnaissance #Pentesting #SecurityAssessment #NetworkSecurity #InfoSec #PortScanning #FTP #SSH #HTTP #HTTPS #SMB #DNS #LDAP #MySQL #MSSQL #PostgreSQL #MongoDB #Redis #Elasticsearch #SNMP #RDP #VNC #Kerberos
