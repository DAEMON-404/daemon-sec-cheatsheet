---
title: "ffuf"
description: "ffuf web fuzzing: directory/vhost/parameter discovery, matchers/filters, recursion and wordlists."
category: enumeration
tags: [enumeration, web, fuzzing]
tools: [ffuf]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:Enumeration/ffuf_cheat_sheet.md"
---

# ffuf

> **ffuf** — Fast web fuzzer written in Go (v2.1.0+).

## Installation

```bash
# macOS (Homebrew)
brew install ffuf

# Linux (from source)
go install github.com/ffuf/ffuf/v2@latest

# Kali Linux
sudo apt install ffuf

# Docker
docker pull ffuf/ffuf
docker run --rm ffuf/ffuf -u https://example.com/FUZZ -w /path/to/wordlist
```

## Basic Syntax

```bash
ffuf [options] -u URL -w WORDLIST
```

### Essential Options

```bash
-u URL              # Target URL (use FUZZ keyword)
-w WORDLIST         # Wordlist file path
-H "Header: value"  # Add custom headers
-X METHOD           # HTTP method (GET, POST, PUT, DELETE, etc.)
-d "data"           # POST data
-t THREADS          # Number of concurrent threads (default: 40)
-p DELAY            # Delay between requests (e.g., 0.1-2.0 seconds)
-rate RATE          # Rate of requests per second
-timeout SECONDS    # HTTP request timeout (default: 10)
-v                  # Verbose output
-s                  # Silent mode (no banner)
-c                  # Colorize output
-o FILE             # Output file
-of FORMAT          # Output format (json, ejson, html, md, csv, ecsv)
-recursion          # Enable recursive scanning
-recursion-depth N  # Maximum recursion depth (default: 0)
-e EXTENSIONS       # Comma-separated list of extensions to fuzz
```

## Fuzzing Keywords

ffuf supports multiple fuzzing positions in the same request:

```bash
FUZZ     # Primary fuzzing keyword
FUZ2Z    # Secondary fuzzing keyword
FUZ3Z    # Tertiary fuzzing keyword
# ... up to FUZ99Z
```

### Examples

```bash
# Single keyword
ffuf -u https://example.com/FUZZ -w wordlist.txt

# Multiple keywords
ffuf -u https://example.com/FUZZ/FUZ2Z -w wordlist1.txt:FUZZ -w wordlist2.txt:FUZ2Z

# Extension fuzzing
ffuf -u https://example.com/file.FUZZ -w extensions.txt
```

## FUZZ Keyword Placement Guide

This section shows **where** to place the FUZZ keyword to fuzz different parts of requests.

### 1. DNS/Subdomain Fuzzing

```bash
# Subdomain enumeration (DNS FUZZ.website.com)
ffuf -u https://FUZZ.example.com -w subdomains.txt

# Multi-level subdomain fuzzing
ffuf -u https://FUZZ.FUZ2Z.example.com \
     -w sub1.txt:FUZZ -w sub2.txt:FUZ2Z

# Real example with common wordlist
ffuf -u https://FUZZ.google.com \
     -w /opt/SecLists/Discovery/DNS/subdomains-top1million-5000.txt

# With filtering to remove false positives
ffuf -u https://FUZZ.example.com -w subdomains.txt -fs 1234

# With custom DNS server
ffuf -u https://FUZZ.example.com -w subdomains.txt -dns-server 8.8.8.8
```

### 2. URL Path/Directory Fuzzing

```bash
# Single directory level
ffuf -u https://example.com/FUZZ -w directories.txt

# Nested directory paths
ffuf -u https://example.com/api/FUZZ/users -w endpoints.txt

# Two-level directory fuzzing
ffuf -u https://example.com/FUZZ/FUZ2Z \
     -w dirs.txt:FUZZ -w subdirs.txt:FUZ2Z

# Deep path fuzzing
ffuf -u https://example.com/app/v1/FUZZ/config -w paths.txt

# Fuzz entire path
ffuf -u https://example.com/FUZZ -w full-paths.txt
# Where full-paths.txt contains: admin/login, api/v1/users, etc.
```

### 3. Filename Fuzzing

```bash
# Fuzz filename only
ffuf -u https://example.com/admin/FUZZ.php -w filenames.txt

# Fuzz filename and extension separately
ffuf -u https://example.com/FUZZ.FUZ2Z \
     -w filenames.txt:FUZZ -w extensions.txt:FUZ2Z

# Examples with filenames and extensions
ffuf -u https://example.com/FUZZ.FUZ2Z \
     -w <(echo -e "index\nadmin\nconfig") \
     -w <(echo -e "php\nhtml\nbak\nold")
```

### 4. File Extension Fuzzing

```bash
# Extension discovery
ffuf -u https://example.com/config.FUZZ -w extensions.txt

# With -e flag for automatic extension appending
ffuf -u https://example.com/FUZZ -w files.txt -e .php,.html,.txt,.bak

# Testing backup file extensions
ffuf -u https://example.com/index.php.FUZZ \
     -w <(echo -e "bak\nold\n~\nswp\ntmp\nbackup")
```

### 5. GET Parameter Fuzzing

```bash
# Fuzz parameter NAME
ffuf -u "https://example.com/search?FUZZ=value" -w parameters.txt

# Fuzz parameter VALUE
ffuf -u "https://example.com/search?id=FUZZ" -w values.txt

# Fuzz multiple parameters
ffuf -u "https://example.com/api?FUZZ=1&FUZ2Z=2" \
     -w params1.txt:FUZZ -w params2.txt:FUZ2Z

# Fuzz both parameter name AND value
ffuf -u "https://example.com?FUZZ=FUZ2Z" \
     -w param-names.txt:FUZZ -w param-values.txt:FUZ2Z

# Multiple existing parameters with one fuzzed
ffuf -u "https://example.com/search?user=admin&id=FUZZ&page=1" \
     -w ids.txt

# Testing for hidden parameters
ffuf -u "https://example.com/profile?user=john&FUZZ=test" \
     -w param-names.txt -fw 100
```

### 6. Virtual Host (VHOST) Header Fuzzing

```bash
# Basic VHOST fuzzing (subdomain in Host header)
ffuf -u http://10.10.10.10 -H "Host: FUZZ.example.com" -w vhosts.txt

# Fuzz entire hostname
ffuf -u http://192.168.1.100 -H "Host: FUZZ" -w hostnames.txt

# VHOST with port
ffuf -u http://example.com -H "Host: FUZZ.example.com:8080" -w vhosts.txt

# Filter false positives by response size
ffuf -u http://10.10.10.10 -H "Host: FUZZ.local" -w vhosts.txt -fs 1234
```

### 7. HTTP Header Fuzzing

```bash
# Fuzz header VALUE
ffuf -u https://example.com -H "X-Custom-Header: FUZZ" -w values.txt

# Fuzz header NAME
ffuf -u https://example.com -H "FUZZ: testvalue" -w header-names.txt

# Fuzz User-Agent
ffuf -u https://example.com -H "User-Agent: FUZZ" -w user-agents.txt

# Fuzz X-Forwarded-For (IP spoofing)
ffuf -u https://example.com -H "X-Forwarded-For: FUZZ" -w ips.txt

# Multiple header fuzzing
ffuf -u https://example.com \
     -H "X-Forwarded-For: FUZZ" \
     -H "X-Real-IP: FUZ2Z" \
     -w ips.txt:FUZZ -w ips.txt:FUZ2Z

# Authorization header fuzzing
ffuf -u https://example.com/admin -H "Authorization: Bearer FUZZ" \
     -w tokens.txt

# Custom API key header
ffuf -u https://api.example.com -H "X-API-Key: FUZZ" -w api-keys.txt
```

### 8. POST Data Fuzzing

```bash
# Fuzz POST parameter VALUE (form data)
ffuf -u https://example.com/login -X POST \
     -d "username=admin&password=FUZZ" \
     -w passwords.txt \
     -H "Content-Type: application/x-www-form-urlencoded"

# Fuzz POST parameter NAME
ffuf -u https://example.com/api -X POST \
     -d "FUZZ=testvalue" \
     -w param-names.txt \
     -H "Content-Type: application/x-www-form-urlencoded"

# Fuzz both username AND password
ffuf -u https://example.com/login -X POST \
     -d "username=FUZZ&password=FUZ2Z" \
     -w usernames.txt:FUZZ -w passwords.txt:FUZ2Z

# Fuzz multiple POST fields
ffuf -u https://example.com/register -X POST \
     -d "email=FUZZ@example.com&username=FUZ2Z&role=FUZ3Z" \
     -w emails.txt:FUZZ -w users.txt:FUZ2Z -w roles.txt:FUZ3Z
```

### 9. JSON Data Fuzzing

```bash
# Fuzz JSON field VALUE
ffuf -u https://api.example.com/auth -X POST \
     -d '{"username":"admin","password":"FUZZ"}' \
     -w passwords.txt \
     -H "Content-Type: application/json"

# Fuzz JSON field NAME
ffuf -u https://api.example.com/data -X POST \
     -d '{"FUZZ":"value"}' \
     -w field-names.txt \
     -H "Content-Type: application/json"

# Fuzz nested JSON values
ffuf -u https://api.example.com/user -X POST \
     -d '{"user":{"name":"admin","role":"FUZZ"}}' \
     -w roles.txt \
     -H "Content-Type: application/json"

# Fuzz array elements in JSON
ffuf -u https://api.example.com/permissions -X POST \
     -d '{"permissions":["read","FUZZ"]}' \
     -w permissions.txt \
     -H "Content-Type: application/json"
```

### 10. Cookie Fuzzing

```bash
# Fuzz cookie VALUE
ffuf -u https://example.com -b "session=FUZZ" -w sessions.txt

# Fuzz cookie NAME
ffuf -u https://example.com -b "FUZZ=value123" -w cookie-names.txt

# Multiple cookies with one fuzzed
ffuf -u https://example.com -b "session=abc123; token=FUZZ; user=john" \
     -w tokens.txt

# Fuzz multiple cookies simultaneously
ffuf -u https://example.com -b "session=FUZZ; userid=FUZ2Z" \
     -w sessions.txt:FUZZ -w userids.txt:FUZ2Z

# Using -H header instead of -b
ffuf -u https://example.com \
     -H "Cookie: session=FUZZ; token=xyz" \
     -w sessions.txt
```

### 11. Protocol & Port Fuzzing

```bash
# Fuzz protocol (http vs https)
ffuf -u FUZZ://api.example.com -w <(echo -e "http\nhttps")

# Fuzz port numbers
ffuf -u https://example.com:FUZZ -w ports.txt
# Where ports.txt: 80, 443, 8080, 8443, 3000, 8000, etc.

# Fuzz subdomain and port together
ffuf -u https://FUZZ.example.com:FUZ2Z \
     -w subdomains.txt:FUZZ -w ports.txt:FUZ2Z
```

### 12. Username in URL Path

```bash
# Fuzz username/userid in path
ffuf -u https://example.com/users/FUZZ -w usernames.txt

# Fuzz numeric user IDs
seq 1 1000 | ffuf -u https://example.com/profile/FUZZ -w -

# Fuzz UUID format IDs
ffuf -u https://api.example.com/document/FUZZ -w uuids.txt
```

### 13. Fragment/Anchor Fuzzing

```bash
# Fuzz URL fragment (after #)
ffuf -u https://example.com/page#FUZZ -w fragments.txt
# Note: Fragments are typically client-side, but can reveal info
```

### 14. File Upload Parameter Fuzzing

```bash
# Fuzz file upload field name
ffuf -u https://example.com/upload -X POST \
     -F "FUZZ=@/path/to/file.txt" \
     -w field-names.txt

# Fuzz file content type
ffuf -u https://example.com/upload -X POST \
     -F "file=@test.txt;type=FUZZ" \
     -w content-types.txt
```

### 15. Authentication Fuzzing

```bash
# Basic Auth username fuzzing
echo -n "FUZZ:password" | base64 | \
    ffuf -u https://example.com -H "Authorization: Basic $(cat -)" -w usernames.txt

# Bearer token fuzzing
ffuf -u https://api.example.com/admin \
     -H "Authorization: Bearer FUZZ" \
     -w tokens.txt

# API key in URL parameter
ffuf -u "https://api.example.com/data?apikey=FUZZ" -w keys.txt
```

### 16. Query String Injection Points

```bash
# Fuzz inside existing query value (SQL injection testing)
ffuf -u "https://example.com/search?id=1FUZZ" -w sqli-payloads.txt

# Fuzz before parameter (path confusion)
ffuf -u "https://example.com/FUZZ?id=123" -w paths.txt

# Multiple injection points in same URL
ffuf -u "https://example.com/FUZZ?param=FUZ2Z&data=FUZ3Z" \
     -w paths.txt:FUZZ -w values.txt:FUZ2Z -w data.txt:FUZ3Z
```

### 17. GraphQL Fuzzing

```bash
# Fuzz GraphQL query
ffuf -u https://api.example.com/graphql -X POST \
     -d '{"query":"{ FUZZ { id name } }"}' \
     -w graphql-types.txt \
     -H "Content-Type: application/json"

# Fuzz GraphQL field
ffuf -u https://api.example.com/graphql -X POST \
     -d '{"query":"{ users { FUZZ } }"}' \
     -w field-names.txt \
     -H "Content-Type: application/json"
```

### 18. REST API Resource Fuzzing

```bash
# Fuzz API version
ffuf -u https://api.example.com/FUZZ/users -w api-versions.txt
# Where api-versions.txt: v1, v2, v3, api/v1, etc.

# Fuzz API resource type
ffuf -u https://api.example.com/api/v1/FUZZ -w resources.txt
# Where resources.txt: users, posts, comments, products, etc.

# Fuzz resource ID
ffuf -u https://api.example.com/api/v1/users/FUZZ -w ids.txt
```

### 19. Advanced Multi-Position Fuzzing

```bash
# Clusterbomb mode - ALL combinations (file.ext)
ffuf -mode clusterbomb \
     -u https://example.com/FUZZ.FUZ2Z \
     -w filenames.txt:FUZZ \
     -w extensions.txt:FUZ2Z

# Pitchfork mode - Parallel iteration (line by line)
ffuf -mode pitchfork \
     -u https://example.com/FUZZ \
     -w urls.txt:FUZZ \
     -w specific-values.txt:FUZ2Z

# Three fuzzing positions
ffuf -u https://FUZZ.example.com/FUZ2Z/FUZ3Z \
     -w subdomains.txt:FUZZ \
     -w dirs.txt:FUZ2Z \
     -w files.txt:FUZ3Z
```

### 20. Special Characters & Encoding

```bash
# URL-encoded fuzzing
ffuf -u "https://example.com/search?q=FUZZ" -w encoded-payloads.txt

# Double URL encoding
ffuf -u "https://example.com/path/FUZZ" -w double-encoded.txt

# Base64 encoded values
ffuf -u https://example.com/data/FUZZ -w base64-values.txt

# Fuzz with special characters (testing WAF bypass)
ffuf -u "https://example.com/FUZZ" -w special-chars.txt
```

### FUZZ Placement Quick Reference Table

| Target | Example | Wordlist Type |
|--------|---------|---------------|
| **Subdomain** | `https://FUZZ.example.com` | subdomains.txt |
| **Directory** | `https://example.com/FUZZ` | directories.txt |
| **File** | `https://example.com/admin/FUZZ.php` | filenames.txt |
| **Extension** | `https://example.com/config.FUZZ` | extensions.txt |
| **GET Param Name** | `https://example.com?FUZZ=value` | parameters.txt |
| **GET Param Value** | `https://example.com?id=FUZZ` | values.txt |
| **POST Data** | `-d "user=admin&pass=FUZZ"` | passwords.txt |
| **JSON Value** | `-d '{"user":"FUZZ"}'` | usernames.txt |
| **Header Value** | `-H "X-Auth: FUZZ"` | tokens.txt |
| **Cookie Value** | `-b "session=FUZZ"` | sessions.txt |
| **VHOST** | `-H "Host: FUZZ.local"` | vhosts.txt |
| **Port** | `https://example.com:FUZZ` | ports.txt |
| **User ID** | `https://site.com/user/FUZZ` | userids.txt |

## Common Use Cases

### 1. Directory & File Fuzzing

```bash
# Basic directory enumeration
ffuf -u https://example.com/FUZZ -w /usr/share/wordlists/dirb/common.txt

# Directory fuzzing with extensions
ffuf -u https://example.com/FUZZ -w wordlist.txt -e .php,.html,.txt,.bak

# File extension enumeration
ffuf -u https://example.com/admin.FUZZ -w extensions.txt

# Recursive directory scanning
ffuf -u https://example.com/FUZZ -w wordlist.txt -recursion -recursion-depth 2

# Only show 200 responses
ffuf -u https://example.com/FUZZ -w wordlist.txt -mc 200
```

### 2. Subdomain Enumeration

```bash
# Basic subdomain fuzzing
ffuf -u https://FUZZ.example.com -w subdomains.txt

# With custom DNS server
ffuf -u https://FUZZ.example.com -w subdomains.txt -dns-server 8.8.8.8

# Filtering by response size
ffuf -u https://FUZZ.example.com -w subdomains.txt -fs 4242
```

### 3. Virtual Host Discovery

```bash
# VHOST enumeration
ffuf -u https://example.com -H "Host: FUZZ.example.com" -w wordlist.txt

# Filter false positives by size
ffuf -u https://10.10.10.10 -H "Host: FUZZ.example.local" -w wordlist.txt -fs 1234

# Multiple header fuzzing
ffuf -u https://example.com -H "Host: FUZZ" -H "X-Forwarded-For: FUZ2Z" \
     -w vhosts.txt:FUZZ -w ips.txt:FUZ2Z
```

### 4. Parameter Fuzzing (GET)

```bash
# GET parameter discovery
ffuf -u https://example.com?FUZZ=test -w params.txt

# Multiple parameters
ffuf -u https://example.com?FUZZ=FUZ2Z -w params.txt:FUZZ -w values.txt:FUZ2Z

# Parameter value fuzzing
ffuf -u https://example.com?id=FUZZ -w numbers.txt

# Filter by response size
ffuf -u https://example.com?page=FUZZ -w wordlist.txt -fs 0
```

### 5. POST Data Fuzzing

```bash
# POST parameter fuzzing
ffuf -u https://example.com/login -X POST -d "username=admin&password=FUZZ" \
     -w passwords.txt -H "Content-Type: application/x-www-form-urlencoded"

# JSON POST fuzzing
ffuf -u https://example.com/api -X POST \
     -d '{"username":"admin","password":"FUZZ"}' \
     -w passwords.txt -H "Content-Type: application/json"

# Username and password fuzzing
ffuf -u https://example.com/login -X POST \
     -d "username=FUZZ&password=FUZ2Z" \
     -w usernames.txt:FUZZ -w passwords.txt:FUZ2Z
```

### 6. API Endpoint Fuzzing

```bash
# API endpoint discovery
ffuf -u https://api.example.com/v1/FUZZ -w api-endpoints.txt

# API version fuzzing
ffuf -u https://api.example.com/FUZZ/users -w versions.txt

# RESTful API fuzzing
ffuf -u https://api.example.com/api/FUZZ -w wordlist.txt \
     -H "Authorization: Bearer TOKEN"
```

### 7. Username Enumeration

```bash
# Login form username enumeration
ffuf -u https://example.com/login -X POST \
     -d "username=FUZZ&password=invalid" \
     -w usernames.txt -mr "Invalid password"

# User profile enumeration
ffuf -u https://example.com/users/FUZZ -w usernames.txt -mc 200

# Email enumeration
ffuf -u https://example.com/forgot-password -X POST \
     -d "email=FUZZ@example.com" -w wordlist.txt -mr "sent"
```

### 8. File Backup Enumeration

```bash
# Common backup extensions
ffuf -u https://example.com/admin.FUZZ -w backup-extensions.txt

# Backup file patterns
ffuf -u https://example.com/FUZZ -w backup-patterns.txt
# Where backup-patterns.txt contains: index.php.bak, index.php~, index.php.old, etc.

# Combined filename and extension fuzzing
ffuf -u https://example.com/FUZZ.FUZ2Z \
     -w filenames.txt:FUZZ -w extensions.txt:FUZ2Z
```

## Filter Options

Filters HIDE matching responses (exclude from results):

```bash
-fc CODE1,CODE2     # Filter HTTP status codes
-fs SIZE1,SIZE2     # Filter response size (bytes)
-fw WORDS1,WORDS2   # Filter word count
-fl LINES1,LINES2   # Filter line count
-fr REGEX           # Filter responses matching regex
-ft TIME            # Filter response time (milliseconds)
```

### Filter Examples

```bash
# Hide 404 and 403 responses
ffuf -u https://example.com/FUZZ -w wordlist.txt -fc 404,403

# Hide responses of specific size
ffuf -u https://example.com/FUZZ -w wordlist.txt -fs 4242

# Hide responses with specific word count
ffuf -u https://FUZZ.example.com -w subdomains.txt -fw 1337

# Hide responses matching "Not Found"
ffuf -u https://example.com/FUZZ -w wordlist.txt -fr "Not Found"

# Combine multiple filters
ffuf -u https://example.com/FUZZ -w wordlist.txt -fc 404,403 -fs 0 -fw 1
```

## Matcher Options

Matchers SHOW matching responses (include in results):

```bash
-mc CODE1,CODE2     # Match HTTP status codes
-ms SIZE1,SIZE2     # Match response size (bytes)
-mw WORDS1,WORDS2   # Match word count
-ml LINES1,LINES2   # Match line count
-mr REGEX           # Match responses containing regex
-mt TIME            # Match response time (milliseconds)
```

### Matcher Examples

```bash
# Only show 200 and 301 responses
ffuf -u https://example.com/FUZZ -w wordlist.txt -mc 200,301

# Match specific response size
ffuf -u https://example.com/FUZZ -w wordlist.txt -ms 1337

# Match responses containing "success"
ffuf -u https://example.com/login -X POST -d "user=admin&pass=FUZZ" \
     -w passwords.txt -mr "success"

# Match slow responses (potential SQL injection)
ffuf -u https://example.com/search?q=FUZZ -w sqli-payloads.txt -mt ">3000"

# Combine matchers
ffuf -u https://example.com/FUZZ -w wordlist.txt -mc 200 -ms 1000-5000
```

## Rate Limiting & Performance

```bash
# Set number of threads (default: 40)
ffuf -u https://example.com/FUZZ -w wordlist.txt -t 100

# Rate limiting (requests per second)
ffuf -u https://example.com/FUZZ -w wordlist.txt -rate 10

# Add delay between requests (seconds)
ffuf -u https://example.com/FUZZ -w wordlist.txt -p 0.5

# Set timeout (default: 10s)
ffuf -u https://example.com/FUZZ -w wordlist.txt -timeout 30

# Max execution time (seconds)
ffuf -u https://example.com/FUZZ -w wordlist.txt -maxtime 600

# Stop after errors
ffuf -u https://example.com/FUZZ -w wordlist.txt -se
```

### Performance Tips

```bash
# Fast scan (more threads, higher rate)
ffuf -u https://example.com/FUZZ -w wordlist.txt -t 200 -rate 100

# Stealth scan (slower, less noise)
ffuf -u https://example.com/FUZZ -w wordlist.txt -t 5 -rate 2 -p 1

# Balanced scan
ffuf -u https://example.com/FUZZ -w wordlist.txt -t 40 -rate 50
```

## Output Formats

```bash
# Save output to file
ffuf -u https://example.com/FUZZ -w wordlist.txt -o results.txt

# JSON output
ffuf -u https://example.com/FUZZ -w wordlist.txt -o results.json -of json

# HTML report
ffuf -u https://example.com/FUZZ -w wordlist.txt -o report.html -of html

# Markdown output
ffuf -u https://example.com/FUZZ -w wordlist.txt -o results.md -of md

# CSV output
ffuf -u https://example.com/FUZZ -w wordlist.txt -o results.csv -of csv

# eJSON (one JSON per line - easy to parse)
ffuf -u https://example.com/FUZZ -w wordlist.txt -o results.ejson -of ejson

# CSV with base64 (includes response body)
ffuf -u https://example.com/FUZZ -w wordlist.txt -o results.csv -of ecsv
```

### Output Parsing Examples

```bash
# Parse JSON output with jq
cat results.json | jq '.results[] | select(.status == 200) | .url'

# Extract URLs from eJSON
cat results.ejson | jq -r '.url'

# Filter by status code
cat results.ejson | jq -r 'select(.status == 200) | .url'
```

## Authentication

### Basic Authentication

```bash
# Basic auth
ffuf -u https://example.com/FUZZ -w wordlist.txt -H "Authorization: Basic dXNlcjpwYXNz"

# Or use base64 directly
echo -n "username:password" | base64
ffuf -u https://example.com/FUZZ -w wordlist.txt -H "Authorization: Basic BASE64_HERE"
```

### Bearer Token

```bash
# JWT/Bearer token
ffuf -u https://api.example.com/FUZZ -w wordlist.txt \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Cookie-Based Authentication

```bash
# Using cookies
ffuf -u https://example.com/FUZZ -w wordlist.txt \
     -b "session=abc123; token=xyz789"

# Or with header
ffuf -u https://example.com/FUZZ -w wordlist.txt \
     -H "Cookie: session=abc123; token=xyz789"
```

### Custom Authentication Header

```bash
# API key
ffuf -u https://api.example.com/FUZZ -w wordlist.txt \
     -H "X-API-Key: your-api-key-here"

# Multiple auth headers
ffuf -u https://example.com/FUZZ -w wordlist.txt \
     -H "X-API-Key: key123" \
     -H "X-Auth-Token: token456"
```

## HTTP Methods

```bash
# GET (default)
ffuf -u https://example.com/FUZZ -w wordlist.txt

# POST
ffuf -u https://example.com/api/FUZZ -X POST -w wordlist.txt

# PUT
ffuf -u https://example.com/api/users/FUZZ -X PUT \
     -d '{"data":"value"}' -w wordlist.txt

# DELETE
ffuf -u https://example.com/api/users/FUZZ -X DELETE -w wordlist.txt

# HEAD (faster for discovery)
ffuf -u https://example.com/FUZZ -X HEAD -w wordlist.txt

# OPTIONS (enumerate HTTP methods)
ffuf -u https://example.com/FUZZ -X OPTIONS -w wordlist.txt

# PATCH
ffuf -u https://example.com/api/users/FUZZ -X PATCH \
     -d '{"field":"value"}' -w wordlist.txt
```

## Advanced Techniques

### 1. Recursive Scanning

```bash
# Enable recursion
ffuf -u https://example.com/FUZZ -w wordlist.txt -recursion

# Set recursion depth
ffuf -u https://example.com/FUZZ -w wordlist.txt -recursion -recursion-depth 3

# Recursion with custom strategy
ffuf -u https://example.com/FUZZ -w wordlist.txt \
     -recursion -recursion-depth 2 -recursion-strategy greedy
```

### 2. Replay Proxy (for Burp Suite/OWASP ZAP)

```bash
# Send requests through proxy
ffuf -u https://example.com/FUZZ -w wordlist.txt \
     -replay-proxy http://127.0.0.1:8080

# With proxy authentication
ffuf -u https://example.com/FUZZ -w wordlist.txt \
     -replay-proxy http://user:pass@127.0.0.1:8080
```

### 3. Client Certificates

```bash
# Using client certificate
ffuf -u https://example.com/FUZZ -w wordlist.txt \
     -cert /path/to/cert.pem -key /path/to/key.pem
```

### 4. Custom SNI

```bash
# Server Name Indication
ffuf -u https://10.10.10.10/FUZZ -w wordlist.txt -sni example.com
```

### 5. Follow Redirects

```bash
# Follow redirects
ffuf -u https://example.com/FUZZ -w wordlist.txt -r

# Max redirect depth
ffuf -u https://example.com/FUZZ -w wordlist.txt -r -maxredirs 5
```

### 6. Auto-Calibration

```bash
# Auto-calibrate filters (removes false positives)
ffuf -u https://example.com/FUZZ -w wordlist.txt -ac

# Auto-calibration with custom strategy
ffuf -u https://example.com/FUZZ -w wordlist.txt -ac -acc 95
```

### 7. Request/Response Inspection

```bash
# Show request/response for debugging
ffuf -u https://example.com/FUZZ -w wordlist.txt -v

# Show only specific status codes in verbose
ffuf -u https://example.com/FUZZ -w wordlist.txt -mc 200 -v
```

### 8. Custom User-Agent

```bash
# Custom User-Agent
ffuf -u https://example.com/FUZZ -w wordlist.txt \
     -H "User-Agent: Mozilla/5.0 (custom)"

# Random User-Agent per request (requires UA wordlist)
ffuf -u https://example.com/FUZZ -w dirs.txt:FUZZ -w user-agents.txt:USERAGENT \
     -H "User-Agent: USERAGENT"
```

### 9. Input Modes

```bash
# Clusterbomb mode (cartesian product)
ffuf -mode clusterbomb -u https://example.com/FUZZ/FUZ2Z \
     -w wordlist1.txt:FUZZ -w wordlist2.txt:FUZ2Z

# Pitchfork mode (parallel iteration)
ffuf -mode pitchfork -u https://example.com/FUZZ \
     -w wordlist1.txt:FUZZ -w wordlist2.txt:FUZ2Z
```

### 10. Input from stdin

```bash
# Use stdin as wordlist
cat wordlist.txt | ffuf -u https://example.com/FUZZ -w -

# Combine with other tools
cat targets.txt | httpx -silent | ffuf -u FUZZ/admin -w -
```

## Common Wordlists

### SecLists (Recommended)

```bash
# Install SecLists
git clone https://github.com/danielmiessler/SecLists.git /opt/SecLists
```

### Directory & File Discovery

```text
/usr/share/wordlists/dirb/common.txt
/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
/opt/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt
/opt/SecLists/Discovery/Web-Content/raft-large-directories.txt
/opt/SecLists/Discovery/Web-Content/big.txt
/opt/SecLists/Discovery/Web-Content/common.txt
```

### Subdomains

```text
/opt/SecLists/Discovery/DNS/subdomains-top1million-5000.txt
/opt/SecLists/Discovery/DNS/subdomains-top1million-20000.txt
/opt/SecLists/Discovery/DNS/subdomains-top1million-110000.txt
/opt/SecLists/Discovery/DNS/bitquark-subdomains-top100000.txt
```

### Parameters

```text
/opt/SecLists/Discovery/Web-Content/burp-parameter-names.txt
/opt/SecLists/Discovery/Web-Content/api/api-endpoints.txt
/opt/SecLists/Discovery/Web-Content/common-api-endpoints-mazen160.txt
```

### Usernames

```text
/opt/SecLists/Usernames/Names/names.txt
/opt/SecLists/Usernames/top-usernames-shortlist.txt
/opt/SecLists/Usernames/xato-net-10-million-usernames.txt
```

### Passwords

```text
/usr/share/wordlists/rockyou.txt
/opt/SecLists/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt
/opt/SecLists/Passwords/darkweb2017-top10000.txt
```

### Extensions

```bash
# Create custom extension list
echo -e ".php\n.html\n.js\n.json\n.xml\n.bak\n.old\n.txt\n.asp\n.aspx\n.jsp" > extensions.txt
```

## Tips & Tricks

### 1. Finding the Right Filters

```bash
# First run without filters to see baseline
ffuf -u https://example.com/FUZZ -w wordlist.txt

# Then add filters based on false positive patterns
ffuf -u https://example.com/FUZZ -w wordlist.txt -fs 4242 -fw 337

# Use auto-calibration
ffuf -u https://example.com/FUZZ -w wordlist.txt -ac
```

### 2. Speed Optimization

```bash
# Use HEAD method for faster discovery
ffuf -u https://example.com/FUZZ -w wordlist.txt -X HEAD

# Increase threads for faster scanning
ffuf -u https://example.com/FUZZ -w wordlist.txt -t 100

# Use smaller wordlists first
ffuf -u https://example.com/FUZZ -w common.txt -t 50
```

### 3. Stealth & Evasion

```bash
# Slow and steady
ffuf -u https://example.com/FUZZ -w wordlist.txt -t 5 -p 2 -rate 1

# Randomize User-Agent
ffuf -u https://example.com/FUZZ -w dirs.txt:FUZZ -w ua.txt:UA \
     -H "User-Agent: UA" -mode pitchfork

# Add random delay
ffuf -u https://example.com/FUZZ -w wordlist.txt -p 0.5-2.0
```

### 4. Finding Hidden Parameters

```bash
# GET parameter discovery with value testing
ffuf -u "https://example.com?FUZZ=test" -w params.txt -fw 100

# POST parameter discovery
ffuf -u https://example.com/search -X POST \
     -d "FUZZ=test" -w params.txt -H "Content-Type: application/x-www-form-urlencoded"

# JSON parameter discovery
ffuf -u https://api.example.com/endpoint -X POST \
     -d '{"FUZZ":"test"}' -w params.txt -H "Content-Type: application/json"
```

### 5. Combining with Other Tools

```bash
# Chain with subfinder
subfinder -d example.com -silent | ffuf -u https://FUZZ/admin -w -

# Chain with waybackurls
waybackurls example.com | grep -E "\.(js|php|asp)" | ffuf -u FUZZ -w -

# Pipe to httpx for validation
ffuf -u https://example.com/FUZZ -w wordlist.txt -mc 200 -o urls.txt -of csv | \
     awk -F, '{print $1}' | httpx -silent
```

### 6. Pattern-Based Fuzzing

```bash
# Numeric ID fuzzing
seq 1 1000 | ffuf -u https://example.com/user/FUZZ -w -

# Date-based fuzzing
for year in {2020..2024}; do
    for month in {01..12}; do
        echo "$year-$month"
    done
done | ffuf -u https://example.com/archive/FUZZ -w -

# Hex ID fuzzing
for i in {0..255}; do printf "%02x\n" $i; done | ffuf -u https://example.com/id/FUZZ -w -
```

### 7. Response Size Ranges

```bash
# Match response size ranges
ffuf -u https://example.com/FUZZ -w wordlist.txt -ms 1000-5000

# Filter size ranges
ffuf -u https://example.com/FUZZ -w wordlist.txt -fs 0-100
```

### 8. Content-Type Fuzzing

```bash
# Fuzz Content-Type header
ffuf -u https://example.com/upload -X POST \
     -d "data" -H "Content-Type: FUZZ" -w content-types.txt
# content-types.txt: application/json, application/xml, text/plain, multipart/form-data
```

### 9. Debugging Failed Scans

```bash
# Verbose output with request/response
ffuf -u https://example.com/FUZZ -w wordlist.txt -v

# Test with single word first
echo "test" | ffuf -u https://example.com/FUZZ -w - -v

# Check DNS resolution
ffuf -u https://FUZZ.example.com -w subdomain.txt -debug-log debug.log
```

### 10. Multiple Wordlist Strategies

```bash
# Clusterbomb (all combinations)
ffuf -mode clusterbomb -u https://example.com/FUZZ.FUZ2Z \
     -w files.txt:FUZZ -w extensions.txt:FUZ2Z

# Pitchfork (parallel - line by line)
ffuf -mode pitchfork -u https://example.com/FUZZ \
     -w wordlist1.txt:FUZZ -w wordlist2.txt:FUZ2Z
```

## Real-World Examples

### Example 1: Complete Web App Enumeration

```bash
# Step 1: Find directories
ffuf -u https://target.com/FUZZ -w common.txt -mc 200,301,302,401,403 -o dirs.json -of json

# Step 2: Find files in discovered directories
ffuf -u https://target.com/admin/FUZZ -w files.txt -e .php,.html,.txt,.bak -mc 200

# Step 3: Parameter discovery
ffuf -u "https://target.com/search?FUZZ=test" -w params.txt -fw 100

# Step 4: Virtual host discovery
ffuf -u https://target.com -H "Host: FUZZ.target.com" -w vhosts.txt -fs 4242
```

### Example 2: API Endpoint Discovery

```bash
# Find API endpoints
ffuf -u https://api.target.com/v1/FUZZ -w api-endpoints.txt -mc 200,401,403

# Test different API versions
ffuf -u https://api.target.com/FUZZ/users -w api-versions.txt

# Find API objects
ffuf -u https://api.target.com/api/v1/FUZZ -w api-objects.txt -H "Authorization: Bearer TOKEN"

# Numeric ID enumeration
seq 1 10000 | ffuf -u https://api.target.com/api/v1/users/FUZZ -w - -mc 200
```

### Example 3: Subdomain Takeover Check

```bash
# Find subdomains
ffuf -u https://FUZZ.target.com -w subdomains.txt -mc 200,301,302 -o subdomains.txt -of csv

# Check for CNAME records
cat subdomains.txt | awk -F, '{print $1}' | while read sub; do
    dig +short $sub CNAME
done

# Check for common takeover patterns
ffuf -u https://FUZZ.target.com -w discovered-subs.txt -mr "NoSuchBucket|Repository not found|404"
```

### Example 4: IDOR Testing

```bash
# Enumerate user IDs
seq 1 1000 | ffuf -u https://target.com/api/user/FUZZ -w - \
     -H "Authorization: Bearer YOUR_TOKEN" -mc 200

# Test UUID format
cat uuids.txt | ffuf -u https://target.com/api/document/FUZZ -w - \
     -H "Cookie: session=xyz" -mc 200 -v
```

### Example 5: SQLi & XSS Parameter Fuzzing

```bash
# Find injectable parameters (SQL injection)
ffuf -u "https://target.com/search?id=FUZZ" -w sqli-payloads.txt \
     -mr "SQL syntax|mysql_fetch|error in your SQL" -v

# XSS parameter fuzzing
ffuf -u "https://target.com/search?q=FUZZ" -w xss-payloads.txt \
     -mr "<script>|alert\(1\)" -v

# Slow response detection (time-based SQLi)
ffuf -u "https://target.com/search?id=FUZZ" -w time-sqli.txt -mt ">3000"
```

### Example 6: WordPress Scanning

```bash
# Find WordPress plugins
ffuf -u https://target.com/wp-content/plugins/FUZZ/readme.txt -w wp-plugins.txt -mc 200

# Find WordPress themes
ffuf -u https://target.com/wp-content/themes/FUZZ/style.css -w wp-themes.txt -mc 200

# Find WordPress users
seq 1 100 | ffuf -u https://target.com/?author=FUZZ -w - -fc 404

# WordPress xmlrpc brute force
ffuf -u https://target.com/xmlrpc.php -X POST \
     -d '<methodCall><methodName>wp.getUsersBlogs</methodName><params><param><value>admin</value></param><param><value>FUZZ</value></param></params></methodCall>' \
     -w passwords.txt -mr "isAdmin"
```

### Example 7: Multi-Stage Fuzzing

```bash
# Stage 1: Find subdomains
ffuf -u https://FUZZ.target.com -w subdomains.txt -mc 200 -o stage1.json -of json

# Stage 2: Extract live hosts and fuzz paths
cat stage1.json | jq -r '.results[].url' | while read url; do
    ffuf -u $url/FUZZ -w paths.txt -mc 200,301,302
done

# Stage 3: Fuzz parameters on discovered endpoints (manual, based on Stage 2)
```

### Example 8: GraphQL Endpoint Enumeration

```bash
# Find GraphQL endpoint
ffuf -u https://target.com/FUZZ -w graphql-paths.txt -mc 200,400 -mr "graphql|query"

# GraphQL introspection query fuzzing
ffuf -u https://target.com/graphql -X POST \
     -d '{"query":"FUZZ"}' -w graphql-queries.txt \
     -H "Content-Type: application/json" -mc 200
```

### Example 9: Cloud Bucket Discovery

```bash
# S3 bucket enumeration
ffuf -u https://FUZZ.s3.amazonaws.com -w bucket-names.txt -mc 200,403

# Azure blob storage
ffuf -u https://FUZZ.blob.core.windows.net -w storage-names.txt -mc 200,403

# Google Cloud Storage
ffuf -u https://storage.googleapis.com/FUZZ -w bucket-names.txt -mc 200,403
```

### Example 10: JWT Secret Fuzzing

```bash
# Fuzz JWT secrets (generate JWTs with FUZZ as secret using a script)
ffuf -u https://target.com/api/admin -X GET \
     -H "Authorization: Bearer JWT_WITH_FUZZ_SECRET" \
     -w jwt-secrets.txt -mc 200
```

## Quick Reference Card

```bash
# Basic directory fuzzing
ffuf -u https://target.com/FUZZ -w wordlist.txt

# With extensions
ffuf -u https://target.com/FUZZ -w wordlist.txt -e .php,.html,.txt

# Subdomain enumeration
ffuf -u https://FUZZ.target.com -w subdomains.txt

# VHOST fuzzing
ffuf -u https://target.com -H "Host: FUZZ" -w vhosts.txt

# POST data fuzzing
ffuf -u https://target.com/login -X POST -d "user=admin&pass=FUZZ" -w passwords.txt

# Filter by status code
ffuf -u https://target.com/FUZZ -w wordlist.txt -fc 404,403

# Match status code
ffuf -u https://target.com/FUZZ -w wordlist.txt -mc 200,301

# Filter by size
ffuf -u https://target.com/FUZZ -w wordlist.txt -fs 4242

# Save output
ffuf -u https://target.com/FUZZ -w wordlist.txt -o results.json -of json

# Recursive scanning
ffuf -u https://target.com/FUZZ -w wordlist.txt -recursion -recursion-depth 2

# Rate limiting
ffuf -u https://target.com/FUZZ -w wordlist.txt -rate 10 -t 5

# Through proxy
ffuf -u https://target.com/FUZZ -w wordlist.txt -replay-proxy http://127.0.0.1:8080

# Auto-calibration
ffuf -u https://target.com/FUZZ -w wordlist.txt -ac
```

## Common Errors & Solutions

- **"no wordlist defined"** — Specify a wordlist with `-w`.
- **"no target url defined"** — Specify a URL with `-u`.
- **"no FUZZ keyword found"** — Your URL or data must contain the keyword `FUZZ`.
- **High false positive rate** — Use `-ac` for auto-calibration; add filters (`-fc 404 -fs 0`); use matchers (`-mc 200`).
- **Too slow** — Increase threads (`-t 100`); use smaller wordlist first; use HEAD method (`-X HEAD`).
- **Getting blocked/rate limited** — Reduce threads (`-t 5`); add delay (`-p 1`); reduce rate (`-rate 5`); rotate User-Agent; use a proxy.
- **No results showing** — Remove filters temporarily; check if site is up; use `-v`; check matcher settings.

## Comparison: ffuf vs wfuzz vs gobuster

| Feature | ffuf | wfuzz | gobuster |
|---------|------|-------|----------|
| Speed | High | Medium | High |
| Ease of Use | High | Medium | High |
| Features | High | High | Medium |
| Recursion | Yes | No | Yes |
| Multiple Keywords | Yes | Yes | No |
| Output Formats | Many | Few | Few |
| Auto-Calibration | Yes | No | No |

ffuf is generally the best all-around choice for modern web fuzzing.

## Resources

- Official repo: https://github.com/ffuf/ffuf
- Documentation: https://github.com/ffuf/ffuf/wiki
- SecLists: https://github.com/danielmiessler/SecLists
- PayloadsAllTheThings: https://github.com/swisskyrepo/PayloadsAllTheThings

> Always ensure you have proper authorization before testing any target.
