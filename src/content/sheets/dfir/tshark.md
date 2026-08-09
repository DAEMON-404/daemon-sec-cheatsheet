---
title: "TShark"
description: "TShark CLI packet capture and analysis: filters, fields, follow streams and extraction for triage."
category: dfir
tags: [dfir, network-forensics, pcap]
tools: [TShark, Wireshark]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:Tools/Tshark.md"
---

# TShark

## Overview

TShark is the command-line version of Wireshark, a powerful network protocol analyzer. It can capture packet data from a live network or read packets from a previously saved capture file.

---

## Basic Capture Commands

### List Available Interfaces

```bash
tshark -D
```

### Capture Traffic from Specific Interface

```bash
tshark -i eth0
tshark -i en0  # macOS
tshark -i 1    # Interface number from -D
```

### Capture with Packet Count Limit

```bash
tshark -i eth0 -c 100  # Capture 100 packets
```

### Capture and Save to File

```bash
tshark -i eth0 -w capture.pcap
tshark -i eth0 -w capture.pcap -c 1000
```

### Capture with Time Limit

```bash
tshark -i eth0 -a duration:60 -w capture.pcap  # 60 seconds
```

### Capture with File Size Limit

```bash
tshark -i eth0 -a filesize:100000 -w capture.pcap  # 100MB
```

---

## Reading and Analyzing Captured Data

### Read from Capture File

```bash
tshark -r capture.pcap
```

### Read with Specific Protocol Display

```bash
tshark -r capture.pcap -Y "http"
tshark -r capture.pcap -Y "dns"
```

### Display Specific Fields

```bash
tshark -r capture.pcap -T fields -e ip.src -e ip.dst -e tcp.port
```

### Export to Different Formats

```bash
tshark -r capture.pcap -T json > output.json
tshark -r capture.pcap -T ek > output.ek     # Elastic-compatible JSON
tshark -r capture.pcap -T pdml > output.xml
tshark -r capture.pcap -T psml > output.xml
tshark -r capture.pcap -T text > output.txt
```

---

## Capturing Clear-Text Passwords and Credentials

### HTTP Authentication (Basic Auth)

```bash
# Capture HTTP Basic Authentication
tshark -i eth0 -Y "http.authorization"
tshark -r capture.pcap -Y "http.authorization" -T fields -e http.authorization

# Filter HTTP POST requests (often contain credentials)
tshark -r capture.pcap -Y "http.request.method == POST"
tshark -r capture.pcap -Y "http.request.method == POST" -T fields -e http.host -e http.request.uri -e http.file_data
```

### FTP Credentials

```bash
# FTP USER and PASS commands
tshark -i eth0 -Y "ftp.request.command == USER || ftp.request.command == PASS"
tshark -r capture.pcap -Y "ftp" -T fields -e ftp.request.command -e ftp.request.arg
```

### Telnet Credentials

```bash
# Capture telnet traffic (all clear-text)
tshark -i eth0 -Y "telnet"
tshark -r capture.pcap -Y "telnet" -T fields -e telnet.data
```

### POP3/IMAP Credentials

```bash
# POP3 credentials
tshark -r capture.pcap -Y "pop.request.command == USER || pop.request.command == PASS"
tshark -r capture.pcap -Y "pop" -T fields -e pop.request.command -e pop.request.parameter

# IMAP credentials
tshark -r capture.pcap -Y "imap.request contains LOGIN"
```

### SMTP Authentication

```bash
tshark -r capture.pcap -Y "smtp.req.command == AUTH"
tshark -r capture.pcap -Y "smtp" -T fields -e smtp.req.command -e smtp.req.parameter
```

### Extract HTTP Form Data

```bash
# Extract POST data containing passwords
tshark -r capture.pcap -Y "http.request.method == POST && urlencoded-form" -T fields -e http.file_data

# Look for specific keywords
tshark -r capture.pcap -Y 'http.file_data contains "password"'
```

### Follow TCP Stream for Credentials

```bash
# Follow specific TCP stream
tshark -r capture.pcap -z follow,tcp,ascii,0  # Stream 0
tshark -r capture.pcap -q -z follow,tcp,ascii,0 | grep -i "password\|user"
```

---

## Essential Display Filters

### By Protocol

```bash
tshark -r capture.pcap -Y "http"
tshark -r capture.pcap -Y "dns"
tshark -r capture.pcap -Y "tcp"
tshark -r capture.pcap -Y "udp"
tshark -r capture.pcap -Y "ssl"
tshark -r capture.pcap -Y "ssh"
```

### By IP Address

```bash
tshark -r capture.pcap -Y "ip.addr == 192.168.1.100"
tshark -r capture.pcap -Y "ip.src == 192.168.1.100"
tshark -r capture.pcap -Y "ip.dst == 192.168.1.100"
```

### By Port

```bash
tshark -r capture.pcap -Y "tcp.port == 80"
tshark -r capture.pcap -Y "tcp.dstport == 443"
tshark -r capture.pcap -Y "udp.port == 53"
```

### By MAC Address

```bash
tshark -r capture.pcap -Y "eth.addr == aa:bb:cc:dd:ee:ff"
```

### Combining Filters

```bash
tshark -r capture.pcap -Y "ip.src == 192.168.1.100 && tcp.port == 80"
tshark -r capture.pcap -Y "http && ip.addr == 192.168.1.100"
tshark -r capture.pcap -Y "tcp.port == 80 || tcp.port == 443"
```

### Contains and Matches

```bash
tshark -r capture.pcap -Y 'http.host contains "example.com"'
tshark -r capture.pcap -Y 'frame contains "password"'
tshark -r capture.pcap -Y 'http.request.uri matches "login"'
```

---

## Statistics and Analysis

### Protocol Hierarchy Statistics

```bash
tshark -r capture.pcap -q -z io,phs
```

### Conversation Statistics

```bash
tshark -r capture.pcap -q -z conv,tcp
tshark -r capture.pcap -q -z conv,udp
tshark -r capture.pcap -q -z conv,ip
```

### HTTP Statistics

```bash
tshark -r capture.pcap -q -z http,tree
tshark -r capture.pcap -q -z http_req,tree
tshark -r capture.pcap -q -z http_srv,tree
```

### DNS Statistics

```bash
tshark -r capture.pcap -q -z dns,tree
```

### Endpoints

```bash
tshark -r capture.pcap -q -z endpoints,tcp
tshark -r capture.pcap -q -z endpoints,ip
```

### Export HTTP Objects

```bash
tshark -r capture.pcap --export-objects http,/path/to/output/
```

---

## Reference Table: Common Options and Filters

| Option | Description | Example |
|:---|:---|:---|
| `-D` | List available capture interfaces | `tshark -D` |
| `-i <interface>` | Specify capture interface | `tshark -i eth0` |
| `-r <file>` | Read from capture file | `tshark -r capture.pcap` |
| `-w <file>` | Write to capture file | `tshark -w output.pcap` |
| `-c <count>` | Capture n packets then stop | `tshark -c 1000` |
| `-a <criterion>` | Stop capture on condition | `tshark -a duration:60` |
| `-Y <filter>` | Display filter (Wireshark syntax) | `tshark -Y "http"` |
| `-f <filter>` | Capture filter (BPF syntax) | `tshark -f "port 80"` |
| `-T <format>` | Output format | `tshark -T json` |
| `-e <field>` | Display specific field | `tshark -e ip.src` |
| `-q` | Quiet mode (for statistics) | `tshark -q -z io,phs` |
| `-z <statistics>` | Print statistics | `tshark -z http,tree` |
| `-V` | Verbose packet details | `tshark -V` |
| `-x` | Print hex dump | `tshark -x` |
| `-n` | Disable name resolution | `tshark -n` |
| `-N <name>` | Enable name resolution | `tshark -N mntC` |
| `-E` | Field output options | `tshark -T fields -E separator=,` |

---

## Capture Filters (BPF Syntax)

| Filter | Description | Example |
|:---|:---|:---|
| `host <ip>` | Traffic to/from host | `tshark -f "host 192.168.1.100"` |
| `src host <ip>` | Traffic from host | `tshark -f "src host 192.168.1.100"` |
| `dst host <ip>` | Traffic to host | `tshark -f "dst host 192.168.1.100"` |
| `port <port>` | Traffic on port | `tshark -f "port 80"` |
| `src port <port>` | Source port | `tshark -f "src port 1234"` |
| `dst port <port>` | Destination port | `tshark -f "dst port 443"` |
| `tcp` | TCP traffic only | `tshark -f "tcp"` |
| `udp` | UDP traffic only | `tshark -f "udp"` |
| `net <network>` | Traffic to/from network | `tshark -f "net 192.168.1.0/24"` |
| `portrange <p1>-<p2>` | Port range | `tshark -f "portrange 1-1024"` |

---

## Display Filters for Common Protocols

| Protocol | Filter Examples |
|:---|:---|
| **HTTP** | `http` |
|  | `http.request.method == "GET"` |
|  | `http.response.code == 200` |
|  | `http.host == "example.com"` |
| **HTTPS/TLS** | `ssl` or `tls` |
|  | `ssl.handshake.type == 1` (Client Hello) |
| **DNS** | `dns` |
|  | `dns.qry.name == "example.com"` |
| **FTP** | `ftp` |
|  | `ftp.request.command == "USER"` |
| **SSH** | `ssh` |
| **Telnet** | `telnet` |
| **SMB** | `smb` or `smb2` |
| **SMTP** | `smtp` |
| **POP3** | `pop` |
| **IMAP** | `imap` |
| **ARP** | `arp` |
| **ICMP** | `icmp` |

---

## Advanced Examples

### Capture Only Unencrypted HTTP Traffic

```bash
tshark -i eth0 -f "tcp port 80" -Y "http"
```

### Find All Passwords in Capture

```bash
tshark -r capture.pcap -Y 'frame contains "password" || frame contains "passwd" || frame contains "pwd"' -T fields -e frame.number -e ip.src -e ip.dst -e text
```

### Extract All URLs

```bash
tshark -r capture.pcap -Y "http.request" -T fields -e http.host -e http.request.uri | sed 's/\t//'
```

### Monitor Live Traffic with Filters

```bash
tshark -i eth0 -Y "http.request || dns.qry.name" -T fields -e frame.time -e ip.src -e http.host -e dns.qry.name
```

### Capture Credentials from Multiple Protocols

```bash
tshark -i eth0 -Y "ftp || telnet || http.authorization || pop || imap" -w credentials.pcap
```

### Ring Buffer Capture (Rotating Files)

```bash
tshark -i eth0 -b filesize:50000 -b files:5 -w capture.pcap
# Creates capture_00001.pcap, capture_00002.pcap, etc.
```

### Capture with Verbose Output

```bash
tshark -i eth0 -V -c 10
```

### Filter Non-Encrypted Web Traffic

```bash
tshark -r capture.pcap -Y "http && !ssl" -T fields -e ip.src -e ip.dst -e http.host -e http.request.uri
```

---

## Credential Extraction Examples

### Extract FTP Credentials

```bash
tshark -r capture.pcap -Y "ftp.request.command == USER" -T fields -e ip.src -e ftp.request.arg > ftp_users.txt
tshark -r capture.pcap -Y "ftp.request.command == PASS" -T fields -e ip.src -e ftp.request.arg > ftp_passwords.txt
```

### Extract HTTP Basic Auth

```bash
tshark -r capture.pcap -Y "http.authorization" -T fields -e ip.src -e http.host -e http.authorization
```

### Extract HTTP POST Data

```bash
tshark -r capture.pcap -Y "http.request.method == POST" -T fields -e ip.src -e http.host -e http.file_data | grep -i "username\|password"
```

### Monitor for Credentials in Real-Time

```bash
tshark -i eth0 -Y "ftp || http.authorization || telnet || pop || smtp.req.command == AUTH" -T fields -e frame.time -e ip.src -e ip.dst -e tcp.port
```

---

## Tips and Best Practices

1. **Use Capture Filters** (`-f`) to reduce captured data size
2. **Use Display Filters** (`-Y`) for analysis after capture
3. **Root/Admin Required** for capturing on most interfaces
4. **Promiscuous Mode** is enabled by default (capture all traffic on network segment)
5. **Name Resolution** can slow down capture; use `-n` to disable
6. **Large Captures** should be split using `-b` option
7. **Combine with grep/awk** for advanced text processing
8. **Export Objects** to extract files from capture

---

## Security and Legal Considerations

> **Important —** Only capture traffic on networks you own or have explicit permission to monitor. Capturing credentials without authorization may be illegal. Use for legitimate security testing, education, and network troubleshooting only. Be aware of privacy laws and regulations in your jurisdiction. Encrypted traffic (HTTPS, SSH, etc.) will not reveal passwords without additional steps.

---

## Quick Start Example Workflow

```bash
# 1. List interfaces
tshark -D

# 2. Capture 1000 packets from eth0
tshark -i eth0 -c 1000 -w capture.pcap

# 3. Analyze for HTTP traffic
tshark -r capture.pcap -Y "http"

# 4. Look for credentials
tshark -r capture.pcap -Y "ftp || http.authorization"

# 5. Extract specific fields
tshark -r capture.pcap -Y "http.request" -T fields -e ip.src -e http.host -e http.request.uri
```
