---
title: "RustScan"
description: "RustScan fast port discovery, scripting engine, config and Nmap hand-off patterns."
category: enumeration
tags: [enumeration, port-scanning, network]
tools: [RustScan, Nmap]
difficulty: beginner
updated: "2026-08-09"
source: "vault:Enumeration/rustscan.md"
---

# RustScan

## What is RustScan

RustScan is a modern, high-speed port scanner written in Rust. It can scan all 65,535 ports in as little as **3 seconds** and automatically pipes results to Nmap for detailed analysis. Key features:

* **Speed** — scans all ports in seconds (vs minutes with Nmap)
* **Adaptive Learning** — automatically fine-tunes batch size based on your usage patterns
* **Scripting Engine** — supports Python, Lua, Perl, and Shell scripts
* **Nmap Integration** — automatically passes discovered ports to Nmap
* **IPv6, CIDR, and file input support**

---

## Installation Methods

### Docker (Recommended)
```bash
# Pull the latest image
docker pull rustscan/rustscan:latest

# Run a scan
docker run -it --rm --name rustscan rustscan/rustscan:latest -a 192.168.1.1

# Create an alias for convenience
alias rustscan='docker run -it --rm --name rustscan rustscan/rustscan:latest'

# With increased file descriptor limit
docker run -it --rm --ulimit nofile=5000:5000 --name rustscan rustscan/rustscan:latest -a 192.168.1.1
```

**Why Docker?** High open-file-descriptor limit (solves most common errors), works on all systems including Windows, always the latest version, and no need to install Rust, Cargo, or Nmap.

### Cargo (Rust Package Manager)
```bash
cargo install rustscan
```

### Debian/Ubuntu (.deb package)
```bash
# Check the releases page for the current version number
wget https://github.com/RustScan/RustScan/releases/download/2.3.0/rustscan_2.3.0_amd64.deb
sudo dpkg -i rustscan_2.3.0_amd64.deb
```

### Arch Linux (AUR)
```bash
yay -S rustscan
# or
paru -S rustscan
```

### Homebrew (macOS)
```bash
brew install rustscan
```

---

## Basic Syntax & Flags Reference

```bash
rustscan [FLAGS] [OPTIONS] -a <addresses> [-- <nmap_args>...]
```

### Flags Table

| Flag | Long Form | Description | Default |
|------|-----------|-------------|---------|
| `-a` | `--addresses` | Target IP(s), hostname(s), CIDR, or file | Required |
| `-p` | `--ports` | Specific ports to scan | All ports |
| `-r` | `--range` | Port range (e.g. 1-1000) | 1-65535 |
| `-e` | `--exclude-ports` | Ports to exclude | None |
| `-x` | `--exclude-addresses` | Addresses to exclude | None |
| `-b` | `--batch-size` | Concurrent connections | 4500 |
| `-t` | `--timeout` | Timeout per port (ms) | 1500 |
| `-u` | `--ulimit` | Set file descriptor limit | OS default |
| | `--tries` | Number of retries | 1 |
| | `--scan-order` | Order: `serial` or `random` | serial |
| | `--scripts` | Script level: `none`, `default`, `custom` | default |
| | `--top` | Scan top 1000 ports only | false |
| | `--udp` | Enable UDP scanning | false |
| `-q` | `--quiet` | Quiet mode — ports only | false |
| `-g` | `--greppable` | Greppable output format | false |
| | `--accessible` | Screen reader friendly mode | false |
| `-n` | `--no-config` | Ignore config file | false |
| `-h` | `--help` | Show help | |
| `-V` | `--version` | Show version | |

---

## Target Specification

### Single Target
```bash
rustscan -a 192.168.1.1
rustscan -a scanme.nmap.org
```

### Multiple Targets
```bash
# Comma-separated
rustscan -a 192.168.1.1,192.168.1.2,192.168.1.3

# Mixed IPs and hostnames
rustscan -a google.com,192.168.1.1,example.com
```

### CIDR Notation
```bash
# Scan entire subnet
rustscan -a 192.168.1.0/24

# Smaller subnet
rustscan -a 10.0.0.0/28
```

### File Input
```bash
# targets.txt contains one IP/hostname per line
rustscan -a targets.txt
```

**targets.txt example:**
```text
192.168.1.1
192.168.1.2
scanme.nmap.org
10.0.0.5
```

### Excluding Targets
```bash
# Exclude specific IPs from scan
rustscan -a 192.168.1.0/24 -x 192.168.1.1,192.168.1.254
```

---

## Port Scanning Options

### Scan All Ports (Default)
```bash
rustscan -a 192.168.1.1
# Scans ports 1-65535
```

### Top 1000 Ports
```bash
rustscan -a 192.168.1.1 --top
```

### Specific Ports
```bash
rustscan -a 192.168.1.1 -p 22
rustscan -a 192.168.1.1 -p 22,80,443,8080
rustscan -a 192.168.1.1 -p 21,22,23,25,53,80,110,443
```

### Port Range
```bash
rustscan -a 192.168.1.1 -r 1-1000
rustscan -a 192.168.1.1 -r 8000-9000
```

### Exclude Ports
```bash
# Scan range but exclude specific ports
rustscan -a 192.168.1.1 -r 1-1000 -e 21,22,23

# Useful for avoiding honeypots or known services
rustscan -a 192.168.1.1 -e 80,443
```

### Scan Order
```bash
# Sequential (default) - ports in ascending order
rustscan -a 192.168.1.1 --scan-order serial

# Random - helps evade firewall detection
rustscan -a 192.168.1.1 --scan-order random
rustscan -a 192.168.1.1 -r 1-10000 --scan-order random
```

---

## UDP Scanning

RustScan supports UDP scanning with the `--udp` flag. Note that UDP scanning is inherently slower than TCP due to protocol differences.

```bash
# Basic UDP scan
rustscan --udp -a 192.168.1.1

# UDP on specific ports
rustscan --udp -a 192.168.1.1 -p 53,67,68,69,123,161,162,500

# UDP with port range
rustscan --udp -a 192.168.1.1 -r 1-1000
```

### Common UDP Ports to Scan
| Port | Service |
|------|---------|
| 53 | DNS |
| 67/68 | DHCP |
| 69 | TFTP |
| 123 | NTP |
| 137-139 | NetBIOS |
| 161/162 | SNMP |
| 500 | IKE/IPsec |
| 514 | Syslog |
| 1194 | OpenVPN |
| 1900 | SSDP/UPnP |

### Pass UDP Flags to Nmap
```bash
# Let Nmap handle detailed UDP analysis
rustscan -a 192.168.1.1 -- -sU

# Combined TCP and UDP via Nmap
rustscan -a 192.168.1.1 -- -sS -sU -sV
```

> **Important —** RustScan's native UDP mode (`--udp`) identifies ports that send back responses. For comprehensive UDP scanning, pipe results to Nmap with `-sU` for deeper analysis.

---

## Performance Tuning

### Key Parameters

| Parameter | Effect | Trade-off |
|-----------|--------|-----------|
| **Batch Size** (`-b`) | Ports scanned simultaneously | Higher = faster but more resource-intensive |
| **Timeout** (`-t`) | Wait time per port (ms) | Lower = faster but may miss slow ports |
| **Ulimit** (`-u`) | Open file descriptor limit | Higher = allows larger batch sizes |
| **Tries** (`--tries`) | Retry attempts | Higher = more accurate but slower |

### Speed Profiles

```bash
# Maximum speed (aggressive - CTF/lab only)
rustscan -a 192.168.1.1 -b 65535 -t 1000
ulimit -n 70000
rustscan -a 192.168.1.1 -b 65535 -t 500

# Fast (default-ish)
rustscan -a 192.168.1.1 -b 4500 -t 1500

# Balanced (recommended for real networks)
rustscan -a 192.168.1.1 -b 2500 -t 2000 --tries 2

# Slow/stealth (avoid detection)
rustscan -a 192.168.1.1 -b 100 -t 5000
rustscan -a 192.168.1.1 -b 10 -t 10000 --scan-order random

# Reliable (high latency networks)
rustscan -a 192.168.1.1 -b 1000 -t 4000 --tries 3
```

### Setting Ulimit
```bash
# Check current limits
ulimit -a
ulimit -Hn  # Hard limit
ulimit -Sn  # Soft limit

# Temporarily increase limit
ulimit -n 5000

# Use RustScan's built-in ulimit flag
rustscan -a 192.168.1.1 -u 5000
```

### Platform-Specific Limits

| Platform | Default Limit | Recommended |
|----------|---------------|-------------|
| Ubuntu/Debian | ~8800 | 5000-10000 |
| macOS | ~255 | Increase to 1000+ |
| WSL | Not supported | Use Docker |
| Docker | High | No changes needed |

---

## Nmap Integration

RustScan automatically runs `nmap -vvv -p $PORTS $IP` after finding open ports. Use `--` to separate RustScan flags from Nmap flags:

```bash
rustscan -a <IP> -- <nmap_flags>
```

### Common Nmap Combinations

```bash
# Aggressive scan — runs: nmap -vvv -p $PORTS -A $IP
rustscan -a 192.168.1.1 -- -A

# Service version detection
rustscan -a 192.168.1.1 -- -sV
rustscan -a 192.168.1.1 -- -sV --version-intensity 5

# Default scripts + version
rustscan -a 192.168.1.1 -- -sC -sV

# OS detection
rustscan -a 192.168.1.1 -- -O

# Vulnerability scan
rustscan -a 192.168.1.1 -- --script vuln

# Single / multiple NSE scripts
rustscan -a 192.168.1.1 -- --script http-title
rustscan -a 192.168.1.1 -- --script "http-*"

# Script categories (use quotes for complex expressions)
rustscan -a 192.168.1.1 -- --script '"(vuln and safe) or default"'

# Full enumeration
rustscan -a 192.168.1.1 -- -A -sC -sV -O --script=default,vuln

# Stealth with Nmap
rustscan -a 192.168.1.1 -- -sS -T2

# Output to file
rustscan -a 192.168.1.1 -- -oN scan.txt
rustscan -a 192.168.1.1 -- -oX scan.xml
rustscan -a 192.168.1.1 -- -oA scan_results
```

---

## Scripting Engine

RustScan has a built-in scripting engine supporting **Python**, **Shell**, **Perl**, and **Lua**.

### Script Levels
```bash
# No scripts - just port discovery
rustscan -a 192.168.1.1 --scripts none

# Default scripts (includes Nmap)
rustscan -a 192.168.1.1 --scripts default

# Custom scripts
rustscan -a 192.168.1.1 --scripts custom
```

### Custom Scripts Config (`rustscan_scripts.toml`)
```toml
# Location: same directory as rustscan binary or ~/.rustscan_scripts.toml

[scripts]
ports_separator = ","
```

### Python Script Example
```python
#!/usr/bin/python3
#tags = ["core_approved", "example"]
#developer = ["yourname", "https://yoursite.com"]
#trigger_port = "80"
#call_format = "python3 {{script}} {{ip}} {{port}}"

# Code below this point runs when port 80 is found
import sys

ip = sys.argv[1]
port = sys.argv[2]

print(f'Found HTTP on {ip}:{port}')
# Add your custom logic here
```

### Shell Script Example
```bash
#!/bin/bash
#tags = ["core_approved", "recon"]
#developer = ["yourname", "https://yoursite.com"]
#trigger_port = "21"
#call_format = "bash {{script}} {{ip}} {{port}}"

IP=$1
PORT=$2

echo "FTP detected on $IP:$PORT"
# Run additional enumeration
nmap -sV -p $PORT --script=ftp-anon,ftp-bounce $IP
```

### Script Variables
| Variable | Description |
|----------|-------------|
| `{{script}}` | Path to the script |
| `{{ip}}` | Target IP address |
| `{{port}}` | Discovered port(s) |

### Running External Tools
```bash
# GoBuster on HTTP ports
#call_format = "gobuster dir -u http://{{ip}}:{{port}} -w /usr/share/wordlists/common.txt"

# Nikto on web ports
#call_format = "nikto -h {{ip}} -p {{port}}"
```

---

## Configuration File

Create `~/.rustscan.toml` for persistent defaults:

```toml
# ~/.rustscan.toml

# Target addresses (can be overridden via CLI)
addresses = ["127.0.0.1"]

# Performance settings
batch_size = 4500
timeout = 1500
tries = 1
ulimit = 5000

# Scan settings
scan_order = "serial"  # or "random"
greppable = false
accessible = false

# Port configuration
# ports = {80 = 1, 443 = 1, 8080 = 1}
# range = { start = 1, end = 1000 }

# Nmap arguments
command = ["-sV", "-sC"]

# Script level
scripts = "default"
```

### Minimal Config (Speed Focused)
```toml
batch_size = 5000
timeout = 1000
tries = 1
ulimit = 5000
scan_order = "serial"
```

### Stealth Config
```toml
batch_size = 500
timeout = 3000
tries = 2
scan_order = "random"
```

### Ignore Config File
```bash
rustscan -n -a 192.168.1.1
```

---

## Output Options

```bash
# Quiet mode (ports only)
rustscan -a 192.168.1.1 -q
# Output: 22,80,443
rustscan -a 192.168.1.1 -q > ports.txt

# Greppable output
rustscan -a 192.168.1.1 -g

# Accessible mode (screen readers)
rustscan -a 192.168.1.1 --accessible

# Combine with Nmap output formats
rustscan -a 192.168.1.1 -- -oN results.txt
rustscan -a 192.168.1.1 -- -oX results.xml
rustscan -a 192.168.1.1 -- -oA results
```

### Pipeline Examples
```bash
# Feed ports to another tool
rustscan -a 192.168.1.1 -q | xargs -I {} echo "Port: {}"

# Use with grep
rustscan -a 192.168.1.1 -g | grep "80"
```

---

## Troubleshooting

### Error: "Too Many Open Files"

This is the **most common error**. Solutions:

```bash
# 1. Decrease batch size
rustscan -a 192.168.1.1 -b 500

# 2. Increase ulimit
ulimit -Sn  # Soft limit
ulimit -Hn  # Hard limit
ulimit -n 5000
rustscan -a 192.168.1.1
# Or use RustScan's flag
rustscan -a 192.168.1.1 -u 5000

# 3. Use Docker (best solution)
docker run -it --rm --ulimit nofile=5000:5000 rustscan/rustscan:latest -a 192.168.1.1
```

### Error: Missing Ports / Inaccurate Results
```bash
# Increase timeout
rustscan -a 192.168.1.1 -t 3000

# Increase retries
rustscan -a 192.168.1.1 --tries 3

# Both
rustscan -a 192.168.1.1 -t 3000 --tries 2 -b 2000
```

### WSL Issues
WSL doesn't support ulimit properly. Use Docker, a native Linux VM, or WSL2 with Docker.

### macOS Low Limits
```bash
# macOS default is ~255 — increase it:
sudo launchctl limit maxfiles 65535 65535
ulimit -n 5000
rustscan -a 192.168.1.1 -b 4500
```

### Nmap Not Found
```bash
# Install Nmap
sudo apt install nmap        # Debian/Ubuntu
brew install nmap            # macOS
sudo pacman -S nmap          # Arch

# Or use --scripts none to skip Nmap
rustscan -a 192.168.1.1 --scripts none
```

---

## Real-World Examples

```bash
# CTF / HackTheBox quick scan
rustscan -a 10.10.10.1 -b 500 -t 1500 -- -A -sC -sV

# Bug bounty recon — fast web discovery across subnet, then enumerate
rustscan -a 192.168.1.0/24 -p 80,443,8080,8443 -q > web_servers.txt
cat web_servers.txt | xargs -I {} rustscan -a {} -- -sV --script http-title

# Pentest - full TCP enumeration
rustscan -a target.com -r 1-65535 -b 2500 -t 2000 -- -sV -sC -O -oA full_scan

# Pentest - stealth scan
rustscan -a target.com -b 100 -t 5000 --scan-order random -- -sS -T2

# Internal network — discover hosts then full scan
rustscan -a 10.0.0.0/24 -p 22,445,3389 -q --timeout 2000
rustscan -a discovered_hosts.txt -- -A

# Web application testing
rustscan -a 192.168.1.1 -p 80,443,8000,8080,8443,9000,9443 -- -sV --script http-enum,http-headers

# Database server discovery
rustscan -a 192.168.1.0/24 -p 1433,1521,3306,5432,27017,6379,9200 -q

# SMB / Windows enumeration
rustscan -a 192.168.1.1 -p 135,139,445 -- --script smb-enum-shares,smb-enum-users,smb-os-discovery

# Multiple targets from file with full analysis
rustscan -a targets.txt -b 1000 -t 2000 -- -sV -sC -O -oA network_audit
```

---

## Advanced & Overlooked Techniques

### The #1 Mistake: Forgetting `-Pn` on the Nmap Side
```bash
rustscan -a 10.10.10.5 -- -sC -sV -Pn
```
RustScan has *already proven the port is open* via a raw TCP connect before it ever hands off to Nmap. If Nmap's own host-discovery ping then fails (ICMP blocked, which is extremely common), Nmap reports "0 hosts up" and you **lose every result RustScan just found** — despite already knowing the host is alive. Always append `-Pn` after `--` when piping to Nmap.

### Debug Logging via `RUST_LOG` (Not a CLI Flag)
```bash
RUST_LOG=trace rustscan -a 10.10.10.5
RUST_LOG=debug rustscan -a 10.10.10.5
RUST_LOG=error rustscan -a 10.10.10.5
```
RustScan is built on Rust's `env_logger` crate, so verbosity is controlled by the `RUST_LOG` **environment variable**, not a documented `-v` flag. Fastest way to see batch sizing decisions, socket errors, and retry logic when a scan behaves unexpectedly.

### What "Adaptive Learning" Actually Tunes
The marketing term "Adaptive Learning" specifically means RustScan adjusts its **batch size relative to your detected ulimit** and connection success/failure rate as the scan runs — it is not a general AI/ML feature. On your first run against a new environment, leave batch size at default and let it self-tune; only override `-b` once you've observed how the target/network behaves.

### Why Full `-A` Piped Through RustScan Is Still Fast
Running `rustscan -a <target> -- -A` looks like it should be slow because `-A` is Nmap's heaviest flag. It isn't, because RustScan only hands Nmap the **specific ports it already found open** — Nmap never re-scans the full 65535-port range. Port discovery and deep enumeration are fully decoupled, which is the entire point of the tool.

### Clean Port List Extraction for Scripting
```bash
# Extract a comma-separated port list from greppable output
rustscan -a 10.10.10.5 -g | grep -oP '\[\K[^\]]+'

# Feed straight into a raw nmap command without --scripts overhead
ports=$(rustscan -a 10.10.10.5 -g | grep -oP '\[\K[^\]]+')
nmap -sC -sV -Pn -p $ports 10.10.10.5
```
Bypasses RustScan's built-in Nmap auto-invocation entirely, useful when you want full manual control over the exact Nmap command (custom scripts, output paths, timing).

### Batch Size vs Ulimit — the FD Overhead Nobody Accounts For
Setting `-b` equal to your exact ulimit (`ulimit -Sn`) still sometimes throws "Too many open files." Each scanning socket doesn't operate in isolation — stdin/stdout/stderr and other process-level file descriptors eat into the same limit. Rule of thumb: set batch size to roughly **ulimit minus 100–200** for headroom, e.g. `ulimit -n 5000` paired with `-b 4800`, not `-b 5000`.

### Docker Output Vanishes Without a Volume Mount
```bash
# WRONG — output file is inside the removed container, gone forever
docker run -it --rm rustscan/rustscan:latest -a 10.10.10.5 -- -oA scan

# RIGHT — mount the current directory so output survives container removal
docker run -it --rm -v $(pwd):/data rustscan/rustscan:latest -a 10.10.10.5 -- -oA /data/scan
```
`--rm` deletes the container (and anything written inside it) the instant the scan finishes — the single most common "why did my scan output disappear" issue with the Docker workflow.

### Config File Placement Detail
`~/.rustscan.toml` is read from your **home directory**, not the current working directory or the RustScan binary location shown in some older guides — a frequent source of "my config isn't being applied" confusion. Confirm the exact path RustScan is reading with `RUST_LOG=debug rustscan -a 127.0.0.1` and check the startup log lines.

---

## RustScan vs Nmap

| Feature | RustScan | Nmap |
|---------|----------|------|
| **Speed (all ports)** | ~3-10 seconds | 15-20+ minutes |
| **Service Detection** | Via Nmap | Native |
| **OS Fingerprinting** | Via Nmap | Native |
| **Scripting** | Python/Lua/Shell/Perl | NSE (Lua) |
| **UDP Scanning** | Basic + Nmap | Full native |
| **Stealth Options** | Limited | Extensive |
| **Output Formats** | Basic + Nmap | Many formats |
| **Learning Curve** | Easy | Moderate |

### Best Practice Workflow
```bash
# 1. Fast discovery with RustScan
rustscan -a target.com -q > ports.txt

# 2. Detailed analysis with Nmap
nmap -sV -sC -p $(cat ports.txt | tr '\n' ',') target.com -oA detailed_scan

# Or combined in one command:
rustscan -a target.com -- -sV -sC -A -oA combined_scan
```

---

## Quick Reference Card

```bash
rustscan -a <target>                                  # Basic scan
rustscan -a <target> -p 22,80,443                     # Specific ports
rustscan -a <target> -r 1-1000                        # Port range
rustscan -a <target> --top                            # Top 1000 ports
rustscan --udp -a <target>                            # UDP scan
rustscan -a <target> -b 5000 -t 1000                  # Fast scan
rustscan -a <target> -b 100 -t 5000 --scan-order random  # Stealth scan
rustscan -a <target> -- -sV -sC -A                    # With Nmap scripts
rustscan -a <target> -q                               # Quiet (ports only)
rustscan -a target1,target2,target3                   # Multiple targets
rustscan -a targets.txt                               # From file
rustscan -a 192.168.1.0/24                            # CIDR range
rustscan -a <target> -e 22,80                         # Exclude ports
rustscan -a <target> -b 2500 -t 2000 -- -A -sC -sV -O # Full enumeration
```

---

## References

1. [RustScan — GitHub](https://github.com/bee-san/RustScan)
2. [Installation Guide](https://github.com/bee-san/RustScan/wiki/Installation-Guide)
3. [Common Problems and Solutions](https://github.com/bee-san/RustScan/wiki/Common-Problems-and-their-Solutions)
4. [Nmap Custom Flags](https://github.com/bee-san/RustScan/wiki/Nmap-Custom-Flags)
5. [RustScan Scripting Engine](https://github.com/bee-san/RustScan/wiki/RustScan-Scripting-Engine)
6. [Config File](https://github.com/bee-san/RustScan/wiki/Config-File)
7. [Debugging RustScan](https://github.com/bee-san/RustScan/wiki/Debugging-RustScan)
