---
title: "pcap-credential-extraction"
description: "ldap.simple or http.authorization or ftp.request.command == PASS or ntlmssp or kerberos"
category: tools
tags: ["tools", "kerberos", "ntlm", "sql-injection"]
tools: ["Hashcat", "John", "tshark"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Tools/pcap-credential-extraction-cheatsheet.md"
---
# PCAP Credential Extraction Cheat Sheet

## Quick Reference Table

| Protocol | Port | Tool | Filter/Command |
|----------|------|------|----------------|
| LDAP Simple Bind | 389 | tshark | `tshark -r file.pcap -Y "ldap.simple" -T fields -e ldap.name -e ldap.simple` |
| HTTP Basic Auth | 80/8080 | tshark | `tshark -r file.pcap -Y "http.authorization" -T fields -e http.authorization` |
| FTP | 21 | tshark | `tshark -r file.pcap -Y "ftp.request.command == USER or ftp.request.command == PASS" -T fields -e ftp.request.arg` |
| Telnet | 23 | tshark | `tshark -r file.pcap -Y "telnet" -T fields -e telnet.data` |
| SMTP Auth | 25/587 | tshark | `tshark -r file.pcap -Y "smtp.auth.password" -T fields -e smtp.auth.username -e smtp.auth.password` |
| POP3 | 110 | tshark | `tshark -r file.pcap -Y "pop.request.command == USER or pop.request.command == PASS" -T fields -e pop.request.parameter` |
| IMAP | 143 | tshark | `tshark -r file.pcap -Y "imap.request contains LOGIN" -T fields -e imap.request` |
| SNMP | 161 | tshark | `tshark -r file.pcap -Y "snmp" -T fields -e snmp.community` |
| MySQL | 3306 | tshark | `tshark -r file.pcap -Y "mysql.passwd" -T fields -e mysql.user -e mysql.passwd` |
| NTLMSSP | Various | tshark | `tshark -r file.pcap -Y "ntlmssp.auth.username" -T fields -e ntlmssp.auth.domain -e ntlmssp.auth.username` |
| Kerberos | 88 | tshark | `tshark -r file.pcap -Y "kerberos.CNameString" -T fields -e kerberos.CNameString -e kerberos.realm` |
| HTTP POST | 80/443 | tshark | `tshark -r file.pcap -Y "http.request.method == POST" -T fields -e http.file_data` |

---

## Wireshark Display Filters

### Authentication Protocols
```bash
# All authentication-related traffic
ldap.simple or http.authorization or ftp.request.command == PASS or ntlmssp or kerberos

# LDAP bind requests with credentials
ldap.bindRequest and ldap.simple

# LDAP simple bind only
ldap.protocolOp == 0

# HTTP Basic/Digest Authentication
http.authorization

# HTTP POST requests (login forms)
http.request.method == POST

# NTLM Authentication
ntlmssp.auth.username

# Kerberos traffic
kerberos.CNameString

# FTP credentials
ftp.request.command == USER or ftp.request.command == PASS

# SMB/CIFS authentication
smb.uid or smb2.session_id
```

### By Service Port
```bash
# LDAP
tcp.port == 389 or tcp.port == 636

# HTTP/HTTPS
tcp.port == 80 or tcp.port == 443 or tcp.port == 8080

# FTP
tcp.port == 21

# SSH (encrypted, but can identify users)
tcp.port == 22

# Telnet
tcp.port == 23

# SMTP
tcp.port == 25 or tcp.port == 587

# DNS (for recon)
udp.port == 53

# Kerberos
tcp.port == 88 or udp.port == 88

# SMB
tcp.port == 445 or tcp.port == 139
```

---

## tshark Commands

### LDAP Credentials
```bash
# Extract LDAP simple bind credentials
tshark -r capture.pcap -Y "ldap.simple" -T fields -e ldap.name -e ldap.simple

# LDAP with more context
tshark -r capture.pcap -Y "ldap.bindRequest" -T fields -e ip.src -e ip.dst -e ldap.name -e ldap.simple

# All LDAP operations
tshark -r capture.pcap -Y "ldap" -T fields -e frame.number -e ldap.protocolOp -e ldap.name -e ldap.simple

# To see whole packet and info
sudo tshark -r UserInfo.exe.pcap -Y "ldap.simple" -V
```

### HTTP Credentials
```bash
# HTTP Basic Auth (base64 encoded)
tshark -r capture.pcap -Y "http.authorization" -T fields -e ip.src -e http.host -e http.authorization

# Decode Base64 inline
tshark -r capture.pcap -Y "http.authorization" -T fields -e http.authorization | cut -d' ' -f2 | base64 -d

# HTTP POST data (form submissions)
tshark -r capture.pcap -Y "http.request.method == POST" -T fields -e http.host -e http.request.uri -e http.file_data

# Look for password fields in POST
tshark -r capture.pcap -Y "http.request.method == POST" -T fields -e http.file_data | grep -iE "(pass|pwd|password|passwd)"

# HTTP cookies (session tokens)
tshark -r capture.pcap -Y "http.cookie" -T fields -e http.host -e http.cookie
```

### FTP Credentials
```bash
# FTP username and password
tshark -r capture.pcap -Y "ftp.request.command == USER or ftp.request.command == PASS" -T fields -e ip.src -e ftp.request.command -e ftp.request.arg

# All FTP commands
tshark -r capture.pcap -Y "ftp.request" -T fields -e frame.time -e ip.src -e ftp.request.command -e ftp.request.arg
```

### SMTP/Email Credentials
```bash
# SMTP AUTH credentials
tshark -r capture.pcap -Y "smtp.auth.password" -T fields -e smtp.auth.username -e smtp.auth.password

# SMTP commands
tshark -r capture.pcap -Y "smtp.req.command" -T fields -e smtp.req.command -e smtp.req.parameter
```

### SMB/Windows Authentication
```bash
# NTLMSSP usernames
tshark -r capture.pcap -Y "ntlmssp.auth.username" -T fields -e ip.src -e ntlmssp.auth.domain -e ntlmssp.auth.username

# SMB2 session setup
tshark -r capture.pcap -Y "smb2.cmd == 1" -T fields -e ip.src -e ip.dst -e smb2.acct -e smb2.domain

# Extract NTLMv2 hashes (for cracking)
tshark -r capture.pcap -Y "ntlmssp.auth.ntresponse" -T fields -e ntlmssp.auth.username -e ntlmssp.auth.domain -e ntlmssp.auth.ntresponse
```

### Kerberos
```bash
# Kerberos principals
tshark -r capture.pcap -Y "kerberos.CNameString" -T fields -e ip.src -e kerberos.CNameString -e kerberos.realm

# AS-REQ (initial auth)
tshark -r capture.pcap -Y "kerberos.msg_type == 10" -T fields -e kerberos.CNameString -e kerberos.realm
```

### SNMP Community Strings
```bash
# SNMP community strings (like passwords)
tshark -r capture.pcap -Y "snmp.community" -T fields -e ip.src -e ip.dst -e snmp.community
```

### Database Credentials
```bash
# MySQL login attempts
tshark -r capture.pcap -Y "mysql.user" -T fields -e ip.src -e mysql.user

# PostgreSQL
tshark -r capture.pcap -Y "pgsql.type == 'p'" -T fields -e pgsql.user -e pgsql.password
```

---

## Automated Tools

### PCredz
```bash
# Install
git clone https://github.com/lgandx/PCredz.git

# Run on pcap
python3 Pcredz -f capture.pcap

# Run on interface (live capture)
python3 Pcredz -i eth0
```

### NetworkMiner (GUI)
```bash
# Install on Linux
sudo apt install networkminer

# Or download from: https://www.netresec.com/?page=NetworkMiner
# Open pcap file -> Credentials tab shows extracted creds
```

### Chaosreader
```bash
# Extract all sessions and files
chaosreader capture.pcap

# Creates HTML report with extracted data
```

### ngrep
```bash
# Search for password patterns
ngrep -I capture.pcap -q "pass|pwd|password|passwd"

# Search for specific strings
ngrep -I capture.pcap -q "admin"

# Search in specific protocol
ngrep -I capture.pcap -q "PASS" port 21
```

### dsniff
```bash
# Extract passwords from pcap
dsniff -p capture.pcap
```

---

## Quick & Dirty Methods

### strings + grep
```bash
# Find all readable strings
strings capture.pcap | less

# Look for password patterns
strings capture.pcap | grep -iE "(password|passwd|pass|pwd).*[:=]"

# Look for usernames
strings capture.pcap | grep -iE "(user|username|login|uname).*[:=]"

# Find base64 strings (potential encoded creds)
strings capture.pcap | grep -E "^[A-Za-z0-9+/]{20,}={0,2}$"

# Find email addresses
strings capture.pcap | grep -oE "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

# Find IP addresses
strings capture.pcap | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b"

# Find URLs
strings capture.pcap | grep -oE "https?://[^ ]+"
```

### xxd / hexdump
```bash
# View hex dump with ASCII
xxd capture.pcap | less

# Search for string in hex
xxd capture.pcap | grep -i "password"

# Hexdump with strings highlighted
hexdump -C capture.pcap | less
```

---

## Wireshark GUI Tips

### Follow Streams
1. Right-click packet → Follow → TCP/UDP/HTTP Stream
2. Shows full conversation in readable format
3. Great for seeing complete authentication exchanges

### Export Objects
1. File → Export Objects → HTTP/SMB/TFTP/etc.
2. Extracts files transferred over network
3. May contain config files with credentials

### Useful Columns to Add
- `ldap.name` - LDAP bind DN
- `ldap.simple` - LDAP simple bind password
- `http.authorization` - HTTP auth headers
- `ftp.request.arg` - FTP command arguments

### Protocol Hierarchy
1. Statistics → Protocol Hierarchy
2. Quick overview of what protocols are in capture
3. Helps identify what to look for

---

## Hash Extraction for Cracking

### NTLMv2 Hashes
```bash
# Extract for hashcat/john
tshark -r capture.pcap -Y "ntlmssp.auth" -T fields \
  -e ntlmssp.auth.username \
  -e ntlmssp.auth.domain \
  -e ntlmssp.ntlmserverchallenge \
  -e ntlmssp.auth.ntresponse \
  -e ntlmssp.auth.lmresponse

# Format for hashcat (mode 5600):
# username::domain:ServerChallenge:NTProofStr:NTLMv2Response
```

### Kerberos Tickets (AS-REP Roasting)
```bash
# Extract AS-REP for users without pre-auth
tshark -r capture.pcap -Y "kerberos.msg_type == 11" -T fields -e kerberos.cipher
```

### HTTP Digest Auth
```bash
# Extract digest for cracking
tshark -r capture.pcap -Y "http.authbasic" -T fields -e http.authorization
```

---

## One-Liners

```bash
# Quick credential dump - tries multiple protocols
tshark -r capture.pcap -Y "ldap.simple or http.authorization or ftp.request.command == PASS or smtp.auth.password" -T fields -e frame.number -e ip.src -e ip.dst -e _ws.col.Protocol -e _ws.col.Info 2>/dev/null

# Find all cleartext passwords (broad search)
strings capture.pcap | grep -iE "^.{0,30}(password|passwd|pass|pwd)[^a-z].{0,50}$" | sort -u

# Extract and decode all HTTP Basic Auth
tshark -r capture.pcap -Y "http.authorization contains Basic" -T fields -e http.authorization | while read line; do echo "$line" | cut -d' ' -f2 | base64 -d; echo; done

# List all unique source IPs with auth attempts
tshark -r capture.pcap -Y "ldap.simple or http.authorization or ftp.request.command == PASS" -T fields -e ip.src | sort -u

# Count auth attempts by protocol
tshark -r capture.pcap -Y "ldap.simple or http.authorization or ftp.request.command == PASS" -T fields -e _ws.col.Protocol | sort | uniq -c
```

---

## Common Credential Locations by Protocol

| Protocol | Where to Look |
|----------|---------------|
| LDAP | `ldap.simple` field in bindRequest |
| HTTP Basic | `Authorization: Basic <base64>` header |
| HTTP Form | POST body, look for password/passwd/pass fields |
| FTP | USER and PASS commands in cleartext |
| Telnet | Full session in cleartext |
| SMTP | AUTH LOGIN/PLAIN commands (base64) |
| POP3 | USER and PASS commands |
| IMAP | LOGIN command arguments |
| SNMP | Community string (like a password) |
| VNC | Challenge-response (hashcat mode 7900) |
| RDP | NLA uses CredSSP/NTLMv2 |
| MySQL | mysql.passwd field |
| PostgreSQL | Startup message or password message |

---

## Tips

1. **Always check for TLS/SSL** - If traffic is encrypted, you need the private key or to perform MITM
2. **Time-based correlation** - Failed logins often followed by successful ones reveal valid creds
3. **Check both directions** - Server responses may echo back usernames
4. **Look at DNS** - Reveals internal hostnames and structure
5. **Export HTTP objects** - Config files often contain hardcoded creds
6. **Check for password reuse** - Same creds may work elsewhere
