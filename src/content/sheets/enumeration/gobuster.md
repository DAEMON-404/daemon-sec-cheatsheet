---
title: "Gobuster"
description: "Gobuster dir, dns, vhost and s3 brute-forcing modes with wordlist and status-code options."
category: enumeration
tags: [enumeration, web, brute-force]
tools: [Gobuster]
difficulty: beginner
updated: "2026-08-09"
source: "vault:Tools/gobuster.md"
---

# Gobuster

> **Gobuster** — Fast brute-force enumeration tool written in Go (v3.8.2, Sep 2025). Authors: OJ Reeves (`@TheColonial`) & Christian Mehlmauer (`@firefart`).
> Capabilities: directory/file, DNS subdomain, virtual host, S3 bucket, GCS bucket, TFTP, and generic fuzzing enumeration.

## Installation

```bash
# Kali Linux (pre-installed in default metapackage)
sudo apt install gobuster

# Go install (requires Go 1.24+)
go install github.com/OJ/gobuster/v3@latest

# Build from source
git clone https://github.com/OJ/gobuster.git
cd gobuster
go mod tidy
go build

# Docker
docker pull ghcr.io/oj/gobuster:latest
docker run --rm -it ghcr.io/oj/gobuster:latest dir -u https://target.com -w /usr/share/wordlists/dirb/common.txt
```

## Modes Overview

| Mode | Command | Purpose |
|------|---------|---------|
| `dir` | `gobuster dir` | Directory & file brute-forcing on web servers |
| `dns` | `gobuster dns` | DNS subdomain enumeration |
| `vhost` | `gobuster vhost` | Virtual host discovery via `Host` header manipulation |
| `fuzz` | `gobuster fuzz` | Generic fuzzing — replaces `FUZZ` keyword in URL, headers, and request body |
| `s3` | `gobuster s3` | AWS S3 bucket enumeration |
| `gcs` | `gobuster gcs` | Google Cloud Storage bucket enumeration |
| `tftp` | `gobuster tftp` | TFTP file enumeration |

```bash
# Getting help
gobuster -h                  # General help
gobuster help dir            # Help for a specific mode
gobuster dir --help          # Alternative help syntax
```

## Global Flags (Apply to All Modes)

| Flag | Short | Description |
|------|-------|-------------|
| `--wordlist <path>` | `-w` | Path to the wordlist (set to `-` to read from STDIN) |
| `--threads <int>` | `-t` | Number of concurrent threads (default: `10`) |
| `--output <file>` | `-o` | Write results to a file |
| `--delay <duration>` | | Delay between requests per thread (e.g. `500ms`, `1s`, `1500ms`) |
| `--pattern <file>` | `-p` | File containing replacement patterns using `{GOBUSTER}` placeholder |
| `--wordlist-offset <int>` | | Resume from a given position in the wordlist |
| `--debug` | | Enable debug output (replaces the old `--verbose` flag in v3.7+) |
| `--quiet` | `-q` | Suppress banner and noise |
| `--no-progress` | `-z` | Don't display progress indicator |
| `--no-error` | | Suppress error messages |
| `--no-color` | | Disable colour output |

> **Note — v3.7+ CLI changes:** From v3.7 onwards, Gobuster switched to a new CLI library. The `--verbose` flag was replaced by `--debug`. Some short flags were also reassigned. Always check `gobuster <mode> --help` on your installed version.

## 1. Directory & File Enumeration (`dir`)

The most commonly used mode. Brute-forces URIs (directories and files) on web servers.

### All `dir` Mode Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--url <url>` | `-u` | **Required.** Target URL |
| `--extensions <exts>` | `-x` | File extensions to search for (comma-separated, e.g. `php,html,txt`) |
| `--extensions-file <file>` | `-X` | Read extensions from a file |
| `--status-codes <codes>` | `-s` | Positive status codes to include. Supports ranges (e.g. `200,300-400,404`) |
| `--status-codes-blacklist <codes>` | `-b` | Negative status codes to exclude. Supports ranges. (default: `404`) |
| `--exclude-length <lengths>` | | Exclude responses by content length. Supports comma-separated values and ranges (e.g. `0,203-206,1234`) |
| `--method <method>` | `-m` | HTTP method to use (default: `GET`) |
| `--cookies <string>` | `-c` | Cookies to include in requests |
| `--headers <header>` | `-H` | Custom HTTP headers (repeatable: `-H 'Header1: val1' -H 'Header2: val2'`) |
| `--useragent <string>` | `-a` | Set the User-Agent string |
| `--random-agent` | | Use a random User-Agent string per request |
| `--username <user>` | `-U` | Username for HTTP Basic Auth |
| `--password <pass>` | `-P` | Password for HTTP Basic Auth |
| `--proxy <url>` | | Proxy to use (`http(s)://host:port` or `socks5://host:port`) |
| `--follow-redirect` | `-r` | Follow HTTP redirects |
| `--no-tls-validation` | `-k` | Skip TLS certificate verification |
| `--timeout <duration>` | | HTTP request timeout (default: `10s`) |
| `--add-slash` | `-f` | Append `/` to each request |
| `--expanded` | `-e` | Print full URLs in output |
| `--no-status` | `-n` | Don't print status codes |
| `--hide-length` | | Hide the body length in output |
| `--discover-backup` | `-d` | On finding a file, also search for backup file variations |
| `--no-canonicalize-headers` | | Send HTTP header names as-is (don't canonicalize) |
| `--retry` | | Retry on request timeout |
| `--retry-attempts <int>` | | Number of retries (default: `3`) |
| `--force` | | Continue execution even if precheck errors occur (v3.8+) |
| `--client-cert-p12 <file>` | | P12 file for mTLS client certificates |
| `--client-cert-p12-password <pass>` | | Password for the P12 file |
| `--client-cert-pem <file>` | | PEM public key for mTLS |
| `--client-cert-pem-key <file>` | | PEM private key for mTLS (must have no password) |

### Practical Examples

```bash
# Basic directory enumeration
gobuster dir -u http://10.10.10.100 -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt

# Search for specific file extensions
gobuster dir -u http://10.10.10.100 -w /usr/share/seclists/Discovery/Web-Content/raft-medium-files.txt \
  -x php,html,txt,bak,old,conf,xml,json

# Extensions loaded from a file
gobuster dir -u http://10.10.10.100 -w /usr/share/wordlists/dirb/common.txt \
  -X /home/kali/extensions.txt

# With authentication cookie (e.g. post-login enumeration)
gobuster dir -u http://10.10.10.100 -w /usr/share/wordlists/dirb/big.txt \
  -c "PHPSESSID=abc123def456" -x php

# HTTP Basic Auth
gobuster dir -u http://10.10.10.100 -w /usr/share/wordlists/dirb/common.txt \
  -U admin -P password123

# Custom header (e.g. JWT / Bearer token)
gobuster dir -u http://10.10.10.100/api -w /usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# Follow redirects and skip TLS errors
gobuster dir -u https://10.10.10.100 -w /usr/share/wordlists/dirb/common.txt -r -k

# Proxy through Burp Suite
gobuster dir -u http://10.10.10.100 -w /usr/share/wordlists/dirb/common.txt \
  --proxy http://127.0.0.1:8080

# SOCKS5 proxy (e.g. through ligolo-ng or SSH tunnel)
gobuster dir -u http://172.16.1.10 -w /usr/share/wordlists/dirb/common.txt \
  --proxy socks5://127.0.0.1:1080

# Filter false positives by excluding response lengths
gobuster dir -u http://10.10.10.100 -w /usr/share/wordlists/dirb/common.txt \
  --exclude-length 0,4523

# Only show specific status codes (supports ranges)
gobuster dir -u http://10.10.10.100 -w /usr/share/wordlists/dirb/common.txt \
  -s 200,301,302

# Blacklist status codes
gobuster dir -u http://10.10.10.100 -w /usr/share/wordlists/dirb/common.txt \
  -b 403,404

# Random user agent to evade basic fingerprinting
gobuster dir -u http://10.10.10.100 -w /usr/share/wordlists/dirb/common.txt \
  --random-agent

# High threads with rate limiting
gobuster dir -u http://10.10.10.100 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt \
  -t 50 --delay 100ms

# Auto-discover backup files alongside regular enumeration
gobuster dir -u http://10.10.10.100 -w /usr/share/wordlists/dirb/common.txt -d

# POST method enumeration
gobuster dir -u http://10.10.10.100 -w /usr/share/wordlists/dirb/common.txt -m POST

# Resume a scan from a specific wordlist offset
gobuster dir -u http://10.10.10.100 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt \
  --wordlist-offset 5000

# Force continue even if precheck fails (v3.8+)
gobuster dir -u http://10.10.10.100 -w /usr/share/wordlists/dirb/common.txt --force

# Read wordlist from STDIN (piping)
cat custom_wordlist.txt | gobuster dir -u http://10.10.10.100 -w -

# mTLS client certificate authentication
gobuster dir -u https://10.10.10.100 -w /usr/share/wordlists/dirb/common.txt \
  --client-cert-pem client.pem --client-cert-pem-key client-key.pem

# Save output to file
gobuster dir -u http://10.10.10.100 -w /usr/share/wordlists/dirb/common.txt -o results.txt
```

## 2. DNS Subdomain Enumeration (`dns`)

Discovers subdomains via DNS resolution. Requires the target domain to be resolvable.

### All `dns` Mode Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--domain <domain>` | `-d` | **Required.** Target domain |
| `--resolver <server>` | `-r` | Custom DNS resolver (e.g. `8.8.8.8` or `8.8.8.8:53`) |
| `--show-ips` | `-i` | Show resolved IP addresses in results |
| `--show-cname` / `--check-cname` | `-c` | Show CNAME records (cannot be combined with `-i`). Renamed to `--check-cname` in v3.7+ |
| `--timeout <duration>` | | DNS resolver timeout (default: `1s`) |
| `--wildcard` | | Force continued operation when a wildcard DNS record is detected |
| `--no-fqdn` | | Don't automatically append a trailing dot — disables system search domains (can speed up scans, v3.6+) |

### Practical Examples

```bash
# Basic subdomain enumeration
gobuster dns -d target.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt

# Show resolved IP addresses alongside subdomains
gobuster dns -d target.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt -i

# Use a custom DNS resolver (bypass internal/split-horizon DNS)
gobuster dns -d target.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  -r 1.1.1.1

# Show CNAME records (useful for subdomain takeover identification)
gobuster dns -d target.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -c

# Force operation on wildcard domains
gobuster dns -d target.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt --wildcard

# High thread count for large wordlists
gobuster dns -d target.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt -t 50

# Disable FQDN trailing dot (skip system search domains for speed)
gobuster dns -d target.com -w /usr/share/seclists/Discovery/DNS/bitquark-subdomains-top100000.txt \
  --no-fqdn -t 50

# Save results
gobuster dns -d target.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  -i -o subdomains.txt
```

> **Tip — DNS enumeration pre-requisite:** Ensure the target domain actually resolves. If behind a firewall or using split-horizon DNS, you may need to specify a resolver (`-r`) that has visibility into the target's DNS zone.

## 3. Virtual Host Discovery (`vhost`)

Sends HTTP requests with different `Host:` headers to find virtual hosts on a web server. Unlike DNS mode, this does **not** require DNS resolution — it works directly against the server IP.

### All `vhost` Mode Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--url <url>` | `-u` | **Required.** Target URL (typically use the IP address) |
| `--domain <domain>` | | Domain to append to wordlist entries |
| `--append-domain` | | Append the main domain from the URL to each wordlist word |
| `--exclude-length <lengths>` | | Exclude responses by content length (comma-separated, supports ranges) |
| `--method <method>` | `-m` | HTTP method (default: `GET`) |
| `--cookies <string>` | `-c` | Cookies for requests |
| `--headers <header>` | `-H` | Custom headers (repeatable) |
| `--follow-redirect` | `-r` | Follow redirects |
| `--no-tls-validation` | `-k` | Skip TLS verification |
| `--proxy <url>` | | Proxy to use |
| `--random-agent` | | Use random User-Agent |
| `--useragent <string>` | `-a` | Set User-Agent |
| `--username <user>` | `-U` | HTTP Basic Auth username |
| `--password <pass>` | `-P` | HTTP Basic Auth password |
| `--timeout <duration>` | | HTTP timeout (default: `10s`) |
| `--retry` | | Retry on timeout |
| `--retry-attempts <int>` | | Number of retries (default: `3`) |
| `--no-canonicalize-headers` | | Don't canonicalize header names |
| `--client-cert-*` | | mTLS client certificate options (same as dir mode) |

### Practical Examples

```bash
# Basic vhost discovery — with --append-domain to build FQDN Host headers
gobuster vhost -u http://10.10.10.100 \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --domain target.htb --append-domain

# Filter false positives by excluding a known baseline response length
gobuster vhost -u http://10.10.10.100 \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --domain target.htb --append-domain --exclude-length 301

# Over HTTPS with TLS skip
gobuster vhost -u https://10.10.10.100 \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --domain target.htb --append-domain -k

# High thread count
gobuster vhost -u http://10.10.10.100 \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt \
  --domain target.htb --append-domain -t 50
```

> **Important — VHost vs DNS mode:**
> - Use **DNS mode** to discover subdomains via actual DNS resolution.
> - Use **VHost mode** when the server hosts multiple sites on the same IP and you need to discover them by manipulating the `Host` header.
> - **VHost is the go-to for HTB/CTF targets** where you've added the base domain to `/etc/hosts` and want to find additional virtual hosts.
> - From v3.7+, Gobuster warns you if `--append-domain` might have been forgotten.

## 4. Fuzz Mode (`fuzz`)

The most flexible mode. Replaces the keyword `FUZZ` in the URL, headers, and request body with wordlist entries.

### Key `fuzz` Mode Flags

Fuzz mode shares most HTTP flags with `dir` mode, plus:

| Feature | Flag | Description |
|---------|------|-------------|
| URL fuzzing | `-u` | Include `FUZZ` in the URL |
| Header fuzzing | `-H` | Include `FUZZ` in header values |
| Body fuzzing | `-d` | Include `FUZZ` in POST body data (v3.3+) |
| Host header fuzzing | `-H "Host: FUZZ.domain"` | Supported natively in v3.7+ |
| Exclude lengths | `--exclude-length` | Filter false positives |
| Blacklist codes | `-b` | Exclude status codes |

### Practical Examples

```bash
# Fuzz URL paths
gobuster fuzz -u http://10.10.10.100/FUZZ -w /usr/share/wordlists/dirb/common.txt

# Fuzz API endpoints
gobuster fuzz -u http://10.10.10.100/api/v1/FUZZ \
  -w /usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt

# Fuzz URL parameters (parameter name discovery)
gobuster fuzz -u "http://10.10.10.100/page?FUZZ=test" \
  -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt

# Fuzz parameter values
gobuster fuzz -u "http://10.10.10.100/page?id=FUZZ" \
  -w /usr/share/seclists/Fuzzing/4-digits-0000-9999.txt

# Fuzz the Host header (alternative to vhost mode, more control)
gobuster fuzz -u http://10.10.10.100 \
  -H "Host: FUZZ.target.htb" \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --exclude-length 1234

# Fuzz POST body data (v3.3+)
gobuster fuzz -u http://10.10.10.100/login \
  -d "username=admin&password=FUZZ" \
  -w /usr/share/seclists/Passwords/Common-Credentials/10k-most-common.txt

# Fuzz custom headers
gobuster fuzz -u http://10.10.10.100 \
  -H "X-Custom-Header: FUZZ" -w /usr/share/wordlists/dirb/common.txt

# Fuzz with status code and length filtering
gobuster fuzz -u http://10.10.10.100/FUZZ -w /usr/share/wordlists/dirb/common.txt \
  -b 404,403 --exclude-length 0
```

## 5. Cloud Storage Enumeration

### AWS S3 Buckets

```bash
# Basic S3 bucket enumeration
gobuster s3 -w /usr/share/seclists/Discovery/Web-Content/bucket-names.txt

# With debug output
gobuster s3 -w /usr/share/seclists/Discovery/Web-Content/bucket-names.txt --debug
```

### Google Cloud Storage Buckets

```bash
# Basic GCS enumeration
gobuster gcs -w /usr/share/seclists/Discovery/Web-Content/bucket-names.txt

# With debug
gobuster gcs -w /usr/share/seclists/Discovery/Web-Content/bucket-names.txt --debug
```

> **Note —** Both modes check for publicly accessible buckets by name. They don't confirm read/write access — just existence. Useful during OSINT and external reconnaissance.

## 6. TFTP Enumeration

```bash
gobuster tftp -s 10.10.10.100 -w /usr/share/seclists/Discovery/TFTP/common.txt
```

| Flag | Short | Description |
|------|-------|-------------|
| `--server <ip>` | `-s` | TFTP server address |
| `--wordlist <file>` | `-w` | Wordlist of filenames to check |

## Pattern Files

Pattern files multiply each wordlist entry with templated variations. Create a file with `{GOBUSTER}` as the placeholder:

```text
# patterns.txt
{GOBUSTER}/v1
{GOBUSTER}/v2
{GOBUSTER}/v3
```

```bash
gobuster dir -u http://10.10.10.100 -w /usr/share/wordlists/dirb/common.txt -p patterns.txt
```

If the wordlist contains `api`, Gobuster tests `/api/v1`, `/api/v2`, `/api/v3`. Use with caution — this multiplies the total number of requests.

## Recommended Wordlists

### SecLists (`sudo apt install seclists`)

| Purpose | Path |
|---------|------|
| General directories | `/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt` |
| General files | `/usr/share/seclists/Discovery/Web-Content/raft-medium-files.txt` |
| Large directory list | `/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt` |
| Common (small/fast) | `/usr/share/seclists/Discovery/Web-Content/common.txt` |
| API endpoints | `/usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt` |
| Subdomains — top 5k | `/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt` |
| Subdomains — top 20k | `/usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt` |
| Subdomains — top 110k | `/usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt` |
| Subdomains — bitquark 100k | `/usr/share/seclists/Discovery/DNS/bitquark-subdomains-top100000.txt` |
| Parameter names | `/usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt` |
| Bucket names | `/usr/share/seclists/Discovery/Web-Content/bucket-names.txt` |
| CGI scripts | `/usr/share/seclists/Discovery/Web-Content/CGIs.txt` |
| IIS-specific | `/usr/share/seclists/Discovery/Web-Content/IIS.fuzz.txt` |

### Dirb (built-in on Kali)

| Purpose | Path |
|---------|------|
| Common | `/usr/share/wordlists/dirb/common.txt` |
| Big | `/usr/share/wordlists/dirb/big.txt` |
| Small | `/usr/share/wordlists/dirb/small.txt` |
| Vulns — Apache | `/usr/share/wordlists/dirb/vulns/apache.txt` |
| Vulns — IIS | `/usr/share/wordlists/dirb/vulns/iis.txt` |
| Vulns — Tomcat | `/usr/share/wordlists/dirb/vulns/tomcat.txt` |

### Dirbuster

| Purpose | Path |
|---------|------|
| Small | `/usr/share/wordlists/dirbuster/directory-list-2.3-small.txt` |
| Medium | `/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt` |
| Lowercase medium | `/usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt` |

## Extension Stacking by Tech Stack

When enumerating files, match extensions to the target technology:

```bash
# PHP stack
-x php,phps,php5,phtml,phar,inc,bak

# ASP/.NET stack
-x asp,aspx,ashx,asmx,config,dll

# Java stack
-x jsp,jspx,do,action,jsf,faces

# Node/JS stack
-x js,json,ts,mjs

# Python stack
-x py,pyc,wsgi

# General backup/config files (always worth trying)
-x bak,old,orig,save,swp,txt,conf,config,xml,yml,yaml,env,log,sql,db,zip,tar.gz
```

## Advanced Tips & Tricks

### Wildcard Handling

If the target returns valid responses for every request (wildcard), Gobuster will detect this and stop. To override:

```bash
# Force continue on wildcard (dir mode v3.8+)
gobuster dir -u http://10.10.10.100 -w wordlist.txt --force

# Better approach: filter by the wildcard response size
gobuster dir -u http://10.10.10.100 -w wordlist.txt --exclude-length 4523
```

### Combining with Other Tools

```bash
# Generate a custom wordlist from the target using cewl, then feed to gobuster
cewl http://10.10.10.100 -d 2 -m 5 -w custom_wordlist.txt
gobuster dir -u http://10.10.10.100 -w custom_wordlist.txt -x php,html

# Pipe found URLs to httpx for probing
gobuster dir -u http://10.10.10.100 -w wordlist.txt -q --no-error | httpx -silent

# Chain with nuclei for vulnerability scanning on discovered paths
gobuster dir -u http://10.10.10.100 -w wordlist.txt -q -o paths.txt
cat paths.txt | nuclei -t cves/
```

### Rate Limiting & Stealth

```bash
# Slow and quiet (2 threads, 1 second delay)
gobuster dir -u http://10.10.10.100 -w wordlist.txt -t 2 --delay 1s

# Random user agent to evade basic fingerprinting
gobuster dir -u http://10.10.10.100 -w wordlist.txt --random-agent

# Custom user agent to blend in
gobuster dir -u http://10.10.10.100 -w wordlist.txt \
  -a "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
```

### Recursive Enumeration

Gobuster does **not** natively support recursion. Chain scans manually:

```bash
# Step 1: Initial sweep
gobuster dir -u http://10.10.10.100 -w /usr/share/wordlists/dirb/common.txt -o initial.txt

# Step 2: Drill into discovered directories
gobuster dir -u http://10.10.10.100/admin -w /usr/share/wordlists/dirb/common.txt -o admin_results.txt
gobuster dir -u http://10.10.10.100/uploads -w /usr/share/wordlists/dirb/common.txt -o uploads_results.txt
```

> **Tip — If you need native recursion:** Use **feroxbuster** (Rust-based, recursive by default) or **dirsearch** (Python, built-in recursion).

### mTLS / Client Certificates

For targets requiring mutual TLS authentication (v3.3+):

```bash
# Using PEM files
gobuster dir -u https://10.10.10.100 -w wordlist.txt \
  --client-cert-pem client.pem \
  --client-cert-pem-key client-key.pem

# Using P12 file (v3.7+ supports SHA256 HMAC P12s from openssl3)
gobuster dir -u https://10.10.10.100 -w wordlist.txt \
  --client-cert-p12 client.p12 \
  --client-cert-p12-password 'P@ssw0rd'
```

## Quick Reference — Common Workflows

### HTB / CTF Initial Enumeration

```bash
# Step 1: Quick directory sweep
gobuster dir -u http://target.htb -w /usr/share/seclists/Discovery/Web-Content/common.txt \
  -x php,html,txt -t 40 -o initial_scan.txt

# Step 2: VHost discovery (get a baseline response length first, then exclude it)
gobuster vhost -u http://target.htb \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --domain target.htb --append-domain -t 40 \
  --exclude-length <baseline_length>

# Step 3: Deeper scan on interesting paths
gobuster dir -u http://target.htb/app \
  -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt \
  -x php -t 40 -o deep_scan.txt

# Step 4: API enumeration if applicable
gobuster dir -u http://target.htb/api \
  -w /usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt \
  -x json -t 40
```

### Web Application Pentest

```bash
# Admin panel hunting
gobuster dir -u http://target.com \
  -w /usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt \
  -x php,html -s 200,301,302 -t 30 -o admin_hunt.txt

# Backup and config file discovery
gobuster dir -u http://target.com \
  -w /usr/share/seclists/Discovery/Web-Content/raft-medium-files.txt \
  -x bak,old,conf,config,env,sql,zip,tar.gz,swp -t 30

# Parameter fuzzing
gobuster fuzz -u "http://target.com/page.php?FUZZ=1" \
  -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt \
  -b 404 --exclude-length 0
```

### Bug Bounty Recon

```bash
# Subdomain discovery with IP resolution
gobuster dns -d target.com \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt \
  -t 50 -i -o subdomains.txt

# Vhost sweep against discovered infrastructure
gobuster vhost -u http://<target-ip> \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt \
  --domain target.com --append-domain -t 40

# S3 bucket enumeration with company-related names
gobuster s3 -w company_wordlist.txt --debug
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Wildcard detected, scan aborts | Use `--force` (v3.8+) or `--exclude-length` to filter the wildcard response |
| Flooded with 403 responses | Blacklist with `-b 403`, try `--random-agent`, or adjust User-Agent |
| Scan is too slow | Increase `-t 50` (or higher — test what the target handles) |
| TLS / certificate errors | Add `-k` to skip verification |
| Connection refused / timeout | Increase `--timeout`, reduce `-t`, add `--delay` |
| No results found | Try different wordlists, add `-x` extensions, verify the base URL |
| False positives everywhere | Use `--exclude-length` to filter by response body size |
| Progress bar garbled in piped output | v3.7+ auto-disables progress on redirect; or use `-z` manually |
| "Permission Denied" from target | Reduce thread count, add `--delay`, use `--random-agent` |

## Version History (Notable Changes)

| Version | Key Changes |
|---------|-------------|
| **v3.8.2** | Fix expanded mode showing full URL |
| **v3.8** | `--exclude-hostname-length` flag, `--force` flag in dir mode, fix query parameter fuzzing |
| **v3.7** | New CLI library, `--debug` replaces `--verbose`, `--interface`/`--local-ip` params, TLS renegotiation support, TCP DNS protocol, Host header fuzzing in fuzz mode, auto-disable progress on redirected output, proxy+vhost warning, `--check-cname` replaces `--show-cname` |
| **v3.6** | `--wordlist-offset`, `--exclude-length` supports ranges, `--no-fqdn` in DNS mode |
| **v3.5** | Status code ranges (e.g. `200,300-305,404`) |
| **v3.4** | TLS 1.0/1.1 support, TFTP mode added |
| **v3.3** | mTLS client certificates, extensions from file (`-X`), fuzz POST body/headers/basic auth, `--no-canonicalize-headers` |
| **v3.2** | GCS bucket enumeration, `--retry` on timeout, colour output |
| **v3.1** | S3 bucket enumeration, fuzz mode, pattern files, `--method` flag |

## See Also

| Tool | Language | Key Advantage |
|------|----------|---------------|
| **feroxbuster** | Rust | Native recursion, auto-filtering, content-based deduplication |
| **ffuf** | Go | Multiple `FUZZ` keywords, advanced filtering (size/words/lines/regex), matcher chaining |
| **dirsearch** | Python | Built-in recursion, smart wordlist handling, extension substitution |
| **wfuzz** | Python | Versatile fuzzer, encoders/decoders, complex filtering |

Based on Gobuster v3.8.2 — https://github.com/OJ/gobuster
