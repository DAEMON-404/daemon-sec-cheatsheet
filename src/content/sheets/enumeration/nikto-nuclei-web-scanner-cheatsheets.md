---
title: "Nikto & Nuclei - Web Scanner Cheatsheets"
description: "sudo apt-get install nikto"
category: enumeration
tags: ["enumeration"]
tools: ["Nmap", "Nuclei", "Nikto", "Metasploit"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Enumeration/Nikto & Nuclei - Web Scanner Cheatsheets.md"
---
# Nikto

---

## Install & Update

```bash
# Kali / Debian / Ubuntu
sudo apt-get install nikto

# Git clone — latest code (v2.5.0+)
git clone https://github.com/sullo/nikto
cd nikto/program && perl nikto.pl -Help

# Docker — no local Perl required
docker pull sullo/nikto
docker run --rm sullo/nikto -h <target>

# Update plugin/signature database
nikto -update

# Verify installation and check DB integrity
nikto -Version
nikto -dbcheck
```

> [!info]+ Command Breakdown
> 1. **apt-get install nikto** — installs the packaged version; may lag behind upstream releases
> 2. **git clone** — always pulls the latest v2.5.0+ code; preferred for up-to-date signatures
> 3. **docker pull/run** — fully self-contained; no Perl dependency on the host
> 4. **-update** — syncs the vulnerability plugin and signature database; run before every engagement
> 5. **-dbcheck** — syntax-validates DB files; run after updates to confirm integrity

---

## Basic Web Scan

```bash
# Standard HTTP scan
nikto -h http://192.168.1.10

# Specify port
nikto -h <host> -p <port>

# Force HTTPS
nikto -h <host> -ssl

# Multiple ports
nikto -h <host> -p 80,443,8080

# Bulk scan from file (one host per line)
nikto -h hosts.txt

# HTTPS on non-standard port
nikto -h 192.168.1.10 -p 8443 -ssl

# Authenticated scan with virtual host override
nikto -h http://192.168.1.10 -id admin:admin -vhost internal.corp.local

# Scan host list with 2s delay, abort after 10 min
nikto -h hosts.txt -Pause 2 -maxtime 600s

# Route all traffic through Burp Suite
nikto -h http://10.10.10.10 -useproxy http://127.0.0.1:8080

# Spoof User-Agent
nikto -h http://10.10.10.10 -useragent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
```

> [!info]+ Key Flags Reference

| Flag | Description | Default |
|---|---|---|
| `-h` | Target host / IP / URL | — |
| `-p` | Port(s), comma-sep or range | 80 |
| `-ssl` | Force HTTPS | off |
| `-nossl` | Force HTTP | off |
| `-id user:pass[:realm]` | HTTP Basic / NTLM auth | — |
| `-vhost HOSTNAME` | Override `Host:` header | — |
| `-useproxy http://IP:PORT` | Route via HTTP proxy | off |
| `-useragent "STRING"` | Spoof User-Agent | Nikto/version |
| `-root /path/` | Prepend path to all requests | — |
| `-timeout N` | Per-request timeout (seconds) | 10 |
| `-Pause N` | Delay between tests (seconds) | 0 |
| `-maxtime Ns` | Abort entire scan after N seconds | none |
| `-no404` | Disable 404 page guessing | off |
| `-nointeractive` | Suppress interactive prompts | off |
| `-nolookup` | Skip DNS lookups | off |
| `-Plugins "all"` | Run all plugins | ALL |
| `-list-plugins` | List available plugins | — |
| `-update` | Update plugins/signatures | — |
| `-dbcheck` | Syntax-check DB files | — |

> [!info]+ Output Interpretation
> 1. **`+ OSVDB-XXXX`** — known vulnerability reference; always verify before reporting
> 2. **`+ Server: Apache/2.2.x`** — outdated version detected; cross-check [NVD](https://nvd.nist.gov/)/CVE
> 3. **`+ /admin/` returning 200** — exposed panel; investigate access controls
> 4. **`+ OPTIONS: PUT, DELETE`** — dangerous HTTP methods enabled; test for write access
> 5. **`+ X-Frame-Options header not set`** — potential [clickjacking](https://owasp.org/www-community/attacks/Clickjacking); note for report

> [!warning]+ OPSEC / Detection Notes
> 6. Default UA `Mozilla/5.00 (Nikto/2.x.x)` is trivially flagged by any WAF — always spoof with `-useragent`
> 7. Even with UA spoofing, the sequential probe pattern (`/.git`, `/admin`, `/cgi-bin` etc.) is a strong fingerprint
> 8. Every request appears in `access.log` and `error.log`; WAF rules will trigger
> 9. `-Pause` adds delay but does **not** randomise order — rate-based detection still fires
> 10. **No stealth mode exists** — treat all Nikto scans as loud/noisy
> 11. Use `-Tuning b` (software ID only) for the lowest-footprint option

> [!failure]+ Common Errors

| Error | Fix |
|---|---|
| `ERROR: Cannot open db_tests` | Re-clone repo or run as root; run `-update` |
| SSL handshake failure | Explicitly add `-ssl` or `-nossl` |
| Scan completes with 0 findings | Target unreachable; verify with `curl` first |
| `No plugin found` | Run `nikto -list-plugins` to confirm name |
| Perl module missing | `cpan install Net::SSLeay` for SSL support |
| IPv6 target not resolving | Add `-ipv6` flag explicitly |

---

## Tuning & Targeted Checks

> [!faq]+ What is Tuning?
> Tuning narrows scans to specific vulnerability classes — reduces noise, cuts scan time, and lowers detection surface. Combine multiple codes in a single string (e.g. `-Tuning 49` = XSS + SQLi).

> [!info]+ Tuning Code Reference

| Code | Check Type |
|---|---|
| `0` | File upload |
| `1` | Interesting files / seen in logs |
| `2` | Misconfiguration / default files |
| `3` | Information disclosure |
| `4` | Injection (XSS / Script / HTML) |
| `5` | Remote file retrieval (inside web root) |
| `6` | Denial of service ⚠️ may break services |
| `7` | Remote file retrieval (server-wide) |
| `8` | Command execution / remote shell |
| `9` | SQL injection |
| `a` | Authentication bypass |
| `b` | Software identification |
| `c` | Remote source inclusion |
| `x` | Reverse — run ALL except listed codes |

```bash
# XSS + SQLi only
nikto -h http://10.10.10.10 -Tuning 49

# Info disclosure + misconfiguration
nikto -h http://10.10.10.10 -Tuning 23

# Auth bypass + command execution
nikto -h http://10.10.10.10 -Tuning a8

# All checks EXCEPT denial of service
nikto -h http://10.10.10.10 -Tuning x6

# Software ID only — lowest footprint
nikto -h http://10.10.10.10 -Tuning b

# Full sweep minus DoS, save as JSON
nikto -h http://10.10.10.10 -Tuning x6 -o results.json -Format json
```

> [!info]+ Command Breakdown
> 1. **Tuning codes are combined as a string** — `-Tuning 49` runs codes `4` AND `9` simultaneously
> 2. **`x` reversal prefix** — `-Tuning x6` runs everything *except* DoS; safest full-scan option
> 3. **`b` alone** — software identification only; quietest possible scan; good for initial fingerprinting
> 4. *Combining `-Tuning` with `-o` and `-Format json` captures structured results for later analysis*

> [!danger]+ Tuning Code 6 — Denial of Service
> Code `6` can cause **service disruption** on the target. Exclude with `-Tuning x6` unless DoS testing is explicitly authorised in your scope agreement.

> [!warning]+ OPSEC Note
> Multiple tuning codes still execute many sequential requests — the pattern remains recognisable to IDS/WAF regardless of which codes are selected.

---

## Evasion Techniques

> [!warning]+ Effectiveness Warning
> Nikto evasion codes provide **very limited bypass** against modern WAFs (Cloudflare, ModSecurity v3). Request volume is unchanged — rate/volume-based detection still fires. Best combined with `-Pause`, narrow `-Tuning`, and UA spoofing.

> [!info]+ Evasion Code Reference

| Code | Technique |
|---|---|
| `1` | Random URI encoding (non-UTF8) |
| `2` | Directory self-reference `/./` |
| `3` | Premature URL ending |
| `4` | Prepend long random string |
| `5` | Fake URL parameter |
| `6` | TAB as request spacer |
| `7` | Change case of URL |
| `8` | Windows path separator `\` |
| `A` | Carriage return as request spacer |
| `B` | Binary value `0x0b` as request spacer |

```bash
# Random URI encoding
nikto -h http://10.10.10.10 -evasion 1

# URI encoding + case change combined
nikto -h http://10.10.10.10 -evasion 17

# Targeted scan + evasion combo + slow down
nikto -h http://10.10.10.10 -Tuning 49 -evasion 12 -Pause 1
```

> [!info]+ Command Breakdown
> 1. **Evasion codes combine as a string** — `-evasion 17` applies codes `1` AND `7` simultaneously
> 2. **`-evasion 12 -Pause 1`** — encoding + directory self-reference with 1s delay; reduces scan velocity
> 3. *Pairing narrow `-Tuning` with evasion codes and UA spoofing is the closest Nikto gets to low-noise operation*

---

## Output Formats & Nmap Integration

> [!info]+ Supported Output Formats (`-Format`)

| Code | Type | Notes |
|---|---|---|
| `txt` | Plain text | Default if no extension match |
| `csv` | Comma-separated | Good for spreadsheet / Splunk import |
| `json` | JSON | v2.5.0+ native; best for pipelines |
| `xml` | XML | Vuln management tool import |
| `htm` | HTML | Human-readable client report |
| `nbe` | Nessus NBE | Import into Nessus / legacy tools |
| `msf+` | Metasploit log | Direct log to Metasploit DB |

```bash
# JSON output
nikto -h http://10.10.10.10 -o scan.json -Format json

# HTML report for client delivery
nikto -h http://10.10.10.10 -p 443 -ssl -o report.htm -Format htm

# XML for vulnerability management import
nikto -h http://10.10.10.10 -o nikto_out.xml -Format xml

# Multiple formats from one scan (comma-separated)
nikto -h http://10.10.10.10 -o results.csv -Format csv,xml

# nmap greppable output piped directly to Nikto
# (discovers HTTP ports then scans each automatically)
nmap -p80,443,8080,8443 192.168.1.0/24 -oG - | nikto -h -

# nmap XML output fed to Nikto directly
nmap -sV -p80,443 192.168.1.0/24 -oX nmap_out.xml
nikto -h nmap_out.xml -o nikto_results.xml -Format xml

# Live output to stdout AND file simultaneously
nikto -h http://10.10.10.10 -Display P | tee nikto_live.txt
```

> [!info]+ Command Breakdown
> 1. **`-Format json`** requires v2.5.0+; older apt packages may not support it — use git clone if missing
> 2. **`-oG - | nikto -h -`** — nmap pipes greppable output directly; Nikto reads host list from stdin; efficient for subnet sweeps
> 3. **`-h nmap_out.xml`** — Nikto natively parses nmap XML; automatically extracts hosts and ports
> 4. **`-Display P | tee`** — streams live findings to terminal and writes to file simultaneously
> 5. **`msf+` / `nbe`** formats require additional DB configuration in `nikto.conf`
> 6. *Format is auto-detected from file extension if `-Format` is omitted*

---
---

# Nuclei

---

## Install & Template Management

```bash
# Option 1 — Go install (always latest)
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Option 2 — Pre-built binary (Linux x64)
wget https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip
unzip nuclei_linux_amd64.zip && mv nuclei /usr/local/bin/

# Option 3 — Docker
docker pull projectdiscovery/nuclei:latest
docker run --rm projectdiscovery/nuclei -u https://example.com

# Option 4 — Kali apt (may lag upstream; prefer binary)
sudo apt-get install nuclei

# Verify installation
nuclei -version
nuclei -health-check
```

> [!info]+ Template Management Commands
```bash
# First run auto-downloads templates to ~/.local/nuclei-templates/
nuclei -u example.com

# Update templates to latest release
nuclei -ut

# Update nuclei engine binary
nuclei -up

# Use custom template directory
nuclei -ud /opt/nuclei-templates -ut

# Show installed template version
nuclei -tv

# List all available templates
nuclei -tl

# List all available tags
nuclei -tgl

# Validate a template before use
nuclei -t /path/to/template.yaml -validate

# Disable auto-update check (OPSEC — suppresses outbound to GitHub on start)
nuclei -u example.com -duc
```

> [!info]+ Template Source Reference

| Source | URL | Notes |
|---|---|---|
| Official | [nuclei-templates](https://github.com/projectdiscovery/nuclei-templates) | 10,000+ templates; primary source |
| Official Labs | [nuclei-templates-labs](https://github.com/projectdiscovery/nuclei-templates-labs) | PoC / learning templates |
| Official Fuzzing | [fuzzing-templates](https://github.com/projectdiscovery/fuzzing-templates) | DAST fuzzing templates |
| Community collection | [Nuclei-Templates-Collection](https://github.com/emadshanab/Nuclei-Templates-Collection) | Curated community set |
| Aggregator (600+ repos) | [nucleihub-templates](https://github.com/rix4uni/nucleihub-templates) | Auto-synced every 6 hours |
| Browse all | [GitHub topic](https://github.com/topics/nuclei-templates) | All public template repos |

> [!info]+ Official Template Directory Layout
```
nuclei-templates/
├── http/cves/              # CVE-specific (1,400+)
├── http/exposures/         # Info disclosure (275+)
├── http/misconfiguration/  # Misconfigs (237+)
├── http/exposed-panels/    # Admin panels (662+)
├── http/default-logins/    # Default credentials (103+)
├── http/technologies/      # Tech fingerprint (282+)
├── http/vulnerabilities/   # General vulns (509+)
├── workflows/              # Multi-step chains (189+)
├── ssl/                    # TLS/cert checks
├── dns/                    # DNS checks
├── network/                # TCP/UDP checks
└── file/                   # Local file checks
```

---

## Basic Vulnerability Scan

```bash
# All templates, single target
nuclei -u https://example.com

# Scan from target list
nuclei -l targets.txt

# Specific template or directory
nuclei -u https://example.com -t http/cves/

# Multiple template directories
nuclei -u https://example.com -t http/cves/ -t ssl -t http/exposures/

# High/critical severity only
nuclei -l targets.txt -s high,critical

# Tag-based — WordPress checks
nuclei -u https://example.com -tags wordpress

# Exclude info noise
nuclei -u https://example.com -es info

# Auto-scan — tech detection drives template selection
nuclei -u https://example.com -as

# New templates only (latest release delta)
nuclei -u https://example.com -nt

# Specific CVE by template ID
nuclei -u https://example.com -id CVE-2021-44228

# Load template directly from URL
nuclei -u https://example.com -turl https://raw.githubusercontent.com/.../template.yaml
```

> [!info]+ Key Flags — Target

| Flag | Description | Default |
|---|---|---|
| `-u` | Single URL/host | — |
| `-l` | File of targets (one per line) | — |
| `-eh` | Exclude hosts (IP/CIDR/hostname) | — |
| `-resume` | Resume from `resume.cfg` | off |
| `-sa` | Scan all IPs for a hostname | off |
| `-iv` | IP version (4 or 6) | 4 |

> [!info]+ Key Flags — Templates & Filtering

| Flag | Description | Default |
|---|---|---|
| `-t` | Template file or directory | all |
| `-turl` | Load template from URL | — |
| `-w` | Workflow file or directory | — |
| `-nt` | New templates in latest release only | off |
| `-as` | Auto-scan via Wappalyzer tag mapping | off |
| `-tags` | Filter by tag(s), comma-separated | — |
| `-etags` | Exclude tags | — |
| `-id` | Filter by template ID(s) | — |
| `-eid` | Exclude template ID(s) | — |
| `-s` | Severity: `info,low,medium,high,critical` | all |
| `-es` | Exclude severity levels | — |
| `-pt` | Protocol type: `dns,http,ssl,tcp,file,headless...` | all |
| `-a` | Filter by template author | — |
| `-tl` | List all installed templates | — |
| `-tgl` | List all available tags | — |
| `-validate` | Validate template syntax | — |
| `-code` | Enable code-protocol templates (explicit opt-in) | off |
| `-dut` | Block unsigned/mismatched templates | off |

> [!info]+ Common Tags Reference

| Tag | Coverage |
|---|---|
| `cve` | All CVE templates |
| `exposure` | Info/credential disclosure |
| `misconfiguration` | Server/app misconfigs |
| `default-login` | Default credentials |
| `exposed-panel` | Admin/management panels |
| `rce` | Remote code execution |
| `sqli` | SQL injection |
| `xss` | Cross-site scripting |
| `ssrf` | Server-side request forgery |
| `lfi` | Local file inclusion |
| `wp-plugin` | WordPress plugin vulns |
| `tech` | Technology detection |
| `ssl` | TLS / certificate issues |
| `dns` | DNS misconfigs |
| `login` | Auth-related |

> [!info]+ Output Interpretation
> 1. **`[INF]`** — Tech/version detected; low operational priority
> 2. **`[LOW]` / `[MED]`** — Misconfigs, disclosures; assess contextual risk
> 3. **`[HIGH]` / `[CRIT]`** — Confirmed or likely exploitable; investigate immediately
> 4. **Template ID shown inline** (e.g. `CVE-2021-44228`) — map to [NVD](https://nvd.nist.gov/) for full CVSS score
> 5. **`[matcher-status]` lines with `-ms`** — shows failed matches; useful for false-positive tuning

> [!failure]+ Common Errors

| Error | Fix |
|---|---|
| `No templates found` | Run `nuclei -ut`; check `~/.local/nuclei-templates/` exists |
| Template parse error | Run `nuclei -t template.yaml -validate` |
| OAST interaction timeout | Add `-ni` or use `-iserver` with self-hosted Interactsh |
| OOM / high memory on large scans | Reduce `-c 10 -bs 10`; lower `-timeout 5` |
| `host skipped (max errors)` | Target unstable; raise `-mhe` or check connectivity |
| Templates not updating | Check outbound HTTPS; try `nuclei -ut -v` |
| Unsigned template blocked | Sign template or remove `-dut` restriction (not recommended) |

---

## Output Formats & Reporting

> [!info]+ Output Flag Reference

| Flag | Format | Best Use |
|---|---|---|
| `-o <file>` | Plain text | Quick review |
| `-j` / `-jsonl` | JSONL to stdout | Pipeline / `jq` |
| `-json-export <file>` | JSON array | Structured import |
| `-jsonl-export <file>` | JSONL file | Splunk / ELK ingestion |
| `-markdown-export <dir>` | Markdown per template | Client-ready report |
| `-sarif-export <file>` | SARIF | GitHub / Azure DevOps CI gate |
| `-rdb <file>` | SQLite DB | Persistent multi-run reporting |
| `-silent` | Suppress banner | Findings-only stdout |
| `-nm` | No metadata | Cleaner pipe output |
| `-ts` | Add timestamps | Audit log |
| `-or` | Omit raw req/resp | Smaller output files |
| `-store-resp` | Store all req/resp | Full traffic archive |
| `-nc` | No ANSI colour | Log files / CI output |

```bash
# JSONL with timestamps, no raw payloads
nuclei -l targets.txt -s high,critical -jsonl-export findings.jsonl -ts -or

# Markdown report — full req/resp included
nuclei -u https://example.com -markdown-export ./report/

# SARIF for GitHub Actions CI gate
nuclei -u https://example.com -sarif-export nuclei.sarif

# Filter JSONL with jq — critical findings only
nuclei -u https://example.com -json-export out.json
cat out.json | jq '.[] | select(.info.severity=="critical")'

# Silent mode — print findings only, no banner
nuclei -l targets.txt -s high,critical -silent -o findings.txt

# Persistent report database across multiple scans
nuclei -l targets.txt -rdb nuclei_results.db

# Store every request/response as evidence
nuclei -u https://example.com -store-resp -srd ./traffic_archive/
```

> [!info]+ Command Breakdown
> 1. **`-ts -or`** — timestamps every finding and omits raw payloads; keeps files compact for audit logs
> 2. **`-markdown-export`** — generates one Markdown file per template match; ideal for client deliverables
> 3. **`-sarif-export`** — SARIF format integrates with GitHub Security tab and Azure DevOps pipeline gates
> 4. **`jq '.[] | select(.info.severity=="critical")'`** — filters JSON export to critical findings only; powerful for triage
> 5. **`-rdb`** — SQLite database accumulates results across multiple scan runs; enables trend tracking
> 6. **`-store-resp -srd`** — archives every raw HTTP request/response for evidence and replay

---

## Rate Limiting & OPSEC

> [!info]+ Rate / Concurrency Flags

| Flag | Description | Default |
|---|---|---|
| `-rl` | Max requests per second | 150 |
| `-c` | Templates executed in parallel | 25 |
| `-bs` | Hosts per template in parallel | 25 |
| `-timeout` | Request timeout (seconds) | 10 |
| `-retries` | Retries per failed request | 1 |
| `-mhe` | Max errors before host is skipped | 30 |
| `-project` | Deduplicate requests across runs | off |

> [!info]+ OPSEC Flags

| Flag | Effect |
|---|---|
| `-ni` | Disable Interactsh / OAST callbacks entirely |
| `-iserver` | Use self-hosted Interactsh (no PD infrastructure) |
| `-p` | Proxy all traffic (http/socks5) |
| `-H` | Inject custom headers (e.g. UA spoof) |
| `-tlsi` | Randomise TLS JA3 fingerprint (experimental) |
| `-passive` | Process existing responses only; zero active requests |
| `-duc` | Disable auto-update check; no outbound to GitHub on start |
| `-config` | Load settings from file; avoids CLI exposure in process list |

```bash
# Low-and-slow stealth scan — high/critical only
nuclei -l targets.txt -rl 5 -c 5 -bs 5 -timeout 15 -s high,critical

# No OAST, proxied, spoofed UA, throttled
nuclei -u https://example.com \
  -ni \
  -p http://127.0.0.1:8080 \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
  -rl 10 -c 5

# Passive mode — zero active requests (feed Burp export)
nuclei -l burp_responses.txt -im jsonl -passive

# TLS fingerprint randomisation
nuclei -u https://example.com -tlsi

# Resume a large interrupted scan
nuclei -l targets.txt -resume resume.cfg

# Disable update telemetry entirely
nuclei -u https://example.com -duc -ni
```

> [!info]+ Command Breakdown
> 1. **`-rl 5 -c 5 -bs 5`** — throttles to 5 req/s, 5 parallel templates, 5 hosts at once; drastically reduces noise
> 2. **`-ni`** — the single most important OPSEC flag; stops DNS/HTTP callbacks to `oast.pro`, `oast.live`, `oast.me` which are **externally observable**
> 3. **`-passive -im jsonl`** — feeds pre-captured responses (e.g. Burp export); zero new requests sent to target
> 4. **`-tlsi`** — randomises TLS JA3 fingerprint; experimental but reduces tool-specific TLS detection
> 5. **`-duc`** — prevents version-check HTTP request to GitHub on every invocation; relevant in air-gapped or monitored environments

> [!warning]+ OPSEC / Detection Notes
> 6. **`-ni` is the single most important OPSEC flag** — OAST callbacks to `oast.pro`/`oast.live`/`oast.me` are externally observable and will expose the scan
> 7. Default 150 req/s across 25 parallel templates is very loud; reduce to ≤10 req/s for stealth operations
> 8. All requests still appear in web server `access.log` — no flag prevents server-side logging
> 9. **`-duc`** prevents a version-check HTTP request to GitHub on every invocation
> 10. Self-host [Interactsh](https://github.com/projectdiscovery/interactsh) for OOB testing with zero external callbacks
> 11. Prefer narrow template sets (`-t http/cves/ -s high,critical`) over all-templates runs — cuts request count by 90%+
> 12. **`-as`** auto-scan fires a Wappalyzer fingerprint probe first — adds one visible pre-scan request

---

## DAST / Fuzzing

> [!danger]+ Authorisation Warning
> DAST mode sends **modified/injected payloads** — highly detectable by WAF/IDS. Only use on explicitly authorised scope. Combine with `-rl 5 -ni -p http://127.0.0.1:8080` for proxied, throttled fuzzing.

```bash
# Clone fuzzing templates
git clone https://github.com/projectdiscovery/fuzzing-templates

# Enable DAST mode — all fuzzing templates
nuclei -list endpoints.txt -dast

# Fuzz query parameters only
nuclei -list endpoints.txt -dast -tags fuzzing-req-query

# Fuzz request body only
nuclei -list endpoints.txt -dast -tags fuzzing-req-body

# Fuzz cookies
nuclei -list endpoints.txt -dast -tags fuzzing-req-cookie

# Fuzz request headers
nuclei -list endpoints.txt -dast -tags fuzzing-req-header

# Fuzz URL path segments
nuclei -list endpoints.txt -dast -tags fuzzing-req-path

# Skip header + cookie fuzzing to reduce noise
nuclei -list endpoints.txt -dast -etags fuzzing-req-header,fuzzing-req-cookie

# Katana crawl → Nuclei DAST pipeline
katana -u https://example.com -jc -aff -o endpoints.txt
nuclei -list endpoints.txt -dast -s high,critical -rl 10

# Feed Katana JSONL output directly
nuclei -l katana.jsonl -im jsonl -dast
```

> [!info]+ DAST Fuzzing Flags

| Flag | Description | Default |
|---|---|---|
| `-dast` | Enable DAST / fuzzing templates | off |
| `-ft` | Override fuzzing type: `replace,prefix,postfix,infix` | template default |
| `-fm` | Override fuzzing mode: `multiple,single` | template default |
| `-fa` | Aggression level: `low,medium,high` | `low` |
| `-fuzz-param-frequency` | Skip param after N uninteresting hits | 10 |

> [!info]+ Command Breakdown
> 1. **`-dast`** — activates DAST engine; requires fuzzing-templates to be present
> 2. **`-tags fuzzing-req-query`** — restricts fuzzing to URL query parameters; lowest-noise DAST option
> 3. **`-etags fuzzing-req-header,fuzzing-req-cookie`** — excludes header and cookie fuzzing; reduces detection surface
> 4. **`katana -jc -aff`** — JavaScript crawling with form filling; produces comprehensive endpoint list for DAST input
> 5. **`-im jsonl`** — tells Nuclei the input file is JSONL format (Katana's native output format)

---

## Workflows & Chaining

> [!faq]+ What are Workflows?
> Workflows run multi-step conditional scans — detect technology first, then automatically select and run relevant templates. Defined in YAML; avoids running irrelevant templates against every target.

```bash
# Run a specific workflow
nuclei -u https://example.com -w workflows/cms-detect.yaml

# Run all workflows in a directory
nuclei -u <target> -w workflows/

# Run all official workflows
nuclei -u https://example.com -w ~/.local/nuclei-templates/workflows/

# Combine workflow + structured output
nuclei -u https://example.com -w workflows/cms-detect.yaml \
  -markdown-export ./report/ -s medium,high,critical
```

> [!example]+ CMS Detection Workflow YAML
```yaml
id: example-workflow
info:
  name: CMS Detection + Targeted Scan
  author: operator
  severity: info
workflows:
  - template: http/technologies/cms-detection.yaml
    matchers:
      - name: wordpress
        subtemplates:
          - tags: wp-plugin,wp-theme
          - template: http/cves/2021/    # WordPress CVEs
      - name: drupal
        subtemplates:
          - tags: drupal
      - name: joomla
        subtemplates:
          - tags: joomla
```

> [!example]+ Auth Bypass Workflow YAML
```yaml
id: auth-bypass-workflow
info:
  name: Auth Bypass Assessment
  author: operator
  severity: critical
workflows:
  - template: http/technologies/tech-detect.yaml
  - template: http/default-logins/
    matchers:
      - name: login-successful
        subtemplates:
          - template: http/exposures/
          - tags: exposure,rce
```

> [!info]+ Workflow Structure Breakdown
> 1. **`id`** — unique identifier used in output and reporting
> 2. **`workflows > template`** — first template to execute (detection step)
> 3. **`matchers > name`** — matches a specific result from the detection template
> 4. **`subtemplates`** — templates/tags to run **only if** the matcher fires; conditional chaining
> 5. *Workflows eliminate wasted requests — e.g. WordPress CVEs only run if WordPress is confirmed*

---

## Recon Pipeline Integration

> [!important]+ Install the Full ProjectDiscovery Stack
```bash
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/katana/cmd/katana@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
```

```bash
# Subdomain → live hosts → Nuclei (high/critical CVEs)
subfinder -d example.com -silent | \
  httpx -silent | \
  nuclei -s high,critical -t http/cves/ -ni -rl 20

# Full pipeline: subdomains → live hosts → Nuclei with exclusions
subfinder -d example.com -silent | \
  httpx -silent | \
  tee alive.txt | \
  nuclei -l alive.txt -es info -ept ssl -s medium,high,critical \
    -ni -rl 15 -o findings.txt

# Crawl endpoints then DAST fuzz
katana -u https://example.com -jc -aff -silent -o endpoints.txt
nuclei -list endpoints.txt -dast -tags fuzzing-req-query,fuzzing-req-body \
  -s high,critical -rl 5 -ni

# Full automated recon pipeline (single command)
subfinder -d example.com -all -silent | \
  httpx -silent | \
  katana -list - -silent -nc -jc -aff -ef woff,css,png,svg,jpg -aff | \
  nuclei -im jsonl -es info,unknown -ept ssl -ss template-spray \
    -ni -rl 10 -o nuclei_out.txt

# Scan from nmap XML output
nmap -sV -p80,443,8080,8443 192.168.1.0/24 -oG - | \
  grep "open" | awk '{print $2}' | \
  httpx -silent | \
  nuclei -s high,critical -ni -rl 10
```

> [!info]+ Key httpx Pipeline Flags

| Flag | Effect |
|---|---|
| `-silent` | Output URLs only |
| `-status-code` | Include HTTP status in output |
| `-title` | Include page title in output |
| `-tech-detect` | Detect technologies |
| `-mc 200,301,302` | Filter by status codes |

> [!info]+ Command Breakdown
> 1. **`subfinder -silent | httpx -silent`** — passive subdomain enumeration feeds into live host probing; httpx filters unreachable hosts
> 2. **`tee alive.txt`** — splits the pipe; writes live hosts to file AND continues the pipeline simultaneously
> 3. **`-ept ssl`** — excludes SSL protocol templates; avoids noisy cert-expiry findings in mixed pipelines
> 4. **`-ss template-spray`** — sprays one template across ALL hosts before moving to the next; spreads load and avoids per-host detection thresholds
> 5. **`-ef woff,css,png,svg,jpg`** — Katana excludes static asset extensions; keeps endpoint list clean for Nuclei
> 6. **`-im jsonl`** — instructs Nuclei to parse input as JSONL (Katana's native output); preserves full request context

> [!warning]+ OPSEC / Detection Notes
> 1. Always include **`-ni`** in automated pipelines — prevents uncontrolled OAST callbacks
> 2. Use **`-ss template-spray`** to spread load and avoid per-host detection thresholds
> 3. `subfinder` performs **passive enumeration only**; `katana` and `nuclei` are **active** — scope accordingly
> 4. Add **`-duc`** to suppress update checks in CI/CD pipelines

---

## Writing Custom Templates

> [!faq]+ When to Write a Custom Template
> Write custom templates when: a specific behaviour has no existing template; you need to detect a proprietary application's endpoints; you want to check for a custom misconfiguration; or you are adapting a PoC exploit for templated scanning.

> [!example]+ Minimal HTTP Template Skeleton
```yaml
id: custom-template-id               # unique; used in output

info:
  name: Example Exposed Debug Page
  author: operator
  severity: medium                   # info / low / medium / high / critical
  description: Detects exposed debug endpoint
  tags: exposure,custom

http:
  - method: GET
    path:
      - "{{BaseURL}}/debug"          # {{BaseURL}} = scheme://host:port

    matchers-condition: and          # and / or
    matchers:
      - type: word                   # word / regex / status / size / binary / dsl
        part: body                   # body / header / all / interactsh_protocol
        words:
          - "debug mode"
          - "stack trace"
        condition: or                # or / and

      - type: status
        status:
          - 200
```

> [!example]+ Template with Extractor + Multiple Paths
```yaml
id: version-disclosure

info:
  name: App Version Disclosure
  author: operator
  severity: info
  tags: tech,exposure

http:
  - method: GET
    path:
      - "{{BaseURL}}/version"
      - "{{BaseURL}}/api/version"
      - "{{BaseURL}}/status"

    matchers:
      - type: regex
        part: body
        regex:
          - '([0-9]+\.[0-9]+\.[0-9]+)'

    extractors:
      - type: regex
        part: body
        regex:
          - '([0-9]+\.[0-9]+\.[0-9]+)'
```

> [!example]+ OOB / OAST Template (requires Interactsh)
```yaml
id: ssrf-oob-check

info:
  name: SSRF OOB Detection
  author: operator
  severity: high
  tags: ssrf

http:
  - method: GET
    path:
      - "{{BaseURL}}/?url={{interactsh-url}}"

    matchers:
      - type: word
        part: interactsh_protocol
        words:
          - "http"
```

```bash
# Validate template syntax
nuclei -t custom-template.yaml -validate

# Test against single target with debug output
nuclei -u https://example.com -t custom-template.yaml -debug

# Run with verbose output
nuclei -u https://example.com -t custom-template.yaml -v

# Run against target list
nuclei -l targets.txt -t ./custom-templates/ -s medium,high -ni
```

> [!info]+ Command Breakdown
> 1. **`-validate`** — parses YAML and checks template syntax before running; always validate before deploying
> 2. **`-debug`** — prints full raw HTTP request and response for every template probe; essential for development
> 3. **`{{BaseURL}}`** — Nuclei variable automatically populated with `scheme://host:port` from the target
> 4. **`{{interactsh-url}}`** — automatically generates an OOB callback URL; match fires when the callback is received
> 5. **`matchers-condition: and`** — ALL matchers must fire for a finding to be reported; reduces false positives

> [!info]+ Matcher Types Reference

| Type | Matches On |
|---|---|
| `word` | Exact string presence |
| `regex` | Regular expression |
| `status` | HTTP status code |
| `size` | Response body size |
| `binary` | Binary content |
| `dsl` | DSL expression (flexible boolean logic) |
| `xpath` | XPath on HTML/XML body |

---

## References

1. [Nikto — GitHub](https://github.com/sullo/nikto)
2. [Nikto — Official Site](https://cirt.net/nikto2)
3. [Nikto — Official Documentation](https://cirt.net/nikto2-docs/)
4. [Nikto — Usage Documentation](https://www.cirt.net/nikto2-docs/usage.html)
5. [Nikto — Arch Linux Man Page](https://man.archlinux.org/man/extra/nikto/nikto.1.en)
6. [Nikto — HighOn.Coffee Cheat Sheet](https://highon.coffee/blog/nikto-cheat-sheet/)
7. [Nikto — Terminal Guide](https://www.terminal.guide/linux/security-tools/nikto/)
8. [Nuclei — GitHub](https://github.com/projectdiscovery/nuclei)
9. [Nuclei — Install Docs](https://docs.projectdiscovery.io/opensource/nuclei/install)
10. [Nuclei — Running Docs](https://docs.projectdiscovery.io/opensource/nuclei/running)
11. [Nuclei — Template Structure Docs](https://docs.projectdiscovery.io/templates/structure)
12. [Nuclei — README](https://github.com/projectdiscovery/nuclei/blob/main/README.md)
13. [Nuclei — Workflows Documentation](https://www.mintlify.com/projectdiscovery/nuclei/concepts/workflows)
14. [Nuclei — kb.offsec.nl Reference](https://kb.offsec.nl/tools/framework/projectdiscovery/nuclei/)
15. [Nuclei — Mass Scale Usage](https://ott3rly.com/using-nuclei-at-mass-scale/)
16. [Nuclei — Beginner's Guide (Bugcrowd)](https://www.bugcrowd.com/blog/the-ultimate-beginners-guide-to-nuclei/)
17. [Nuclei Templates — Official](https://github.com/projectdiscovery/nuclei-templates)
18. [Nuclei Templates — Fuzzing](https://github.com/projectdiscovery/fuzzing-templates)
19. [Nuclei Templates — DAST Templates](https://github.com/reewardius/nuclei-dast-templates)
20. [Nuclei Templates — Template Guide](https://github.com/rootklt/nuclei-template-guide/blob/main/template-guide.md)
21. [Interactsh — Self-hosted OOB](https://github.com/projectdiscovery/interactsh)
22. [Pipeline One-Liners — 0xPugal](https://github.com/0xPugal/One-Liners)
23. [ProjectDiscovery Blog](https://projectdiscovery.io/blog/uncover)

---

#WebScan #Nikto #Nuclei #DAST #Fuzzing #ReconPipeline #WebAppTesting #VulnerabilityScanning #OPSEC #ProjectDiscovery
