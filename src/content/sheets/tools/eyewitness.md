---
title: "EyeWitness"
description: "EyeWitness bulk web/RDP/VNC screenshotting and reporting for rapid visual recon."
category: tools
tags: [recon, screenshots, web]
tools: [EyeWitness]
difficulty: beginner
updated: "2026-08-09"
source: "vault:Tools/EyeWitness-Cheatsheet.md"
---

# EyeWitness Cheatsheet

> **Author**: Netrunner | **Last Updated**: 2026-08-06 | **Context**: HTB Pro Labs, CTF, authorised pentesting | **Tool**: [EyeWitness](https://github.com/RedSiege/EyeWitness) (CLI reference)

Web screenshot / recon CLI reference for authorised assessments. Flags below were checked against the [RedSiege/EyeWitness](https://github.com/RedSiege/EyeWitness) README and `Python/EyeWitness.py` argument parser — nothing invented.

Related notes: Nuclei-Cheatsheet · Ffuf-Cheatsheet · webfuzz · NetExec-Cheatsheet

---

## Table of Contents

1. [Summary](#summary)
2. [Project Status & Alternatives](#project-status--alternatives)
3. [Quick-Reference Flag Table](#quick-reference-flag-table)
4. [Installation](#installation)
5. [Basic Usage](#basic-usage)
6. [Input Formats](#input-formats)
7. [Timing, Proxy & Browser Options](#timing-proxy--browser-options)
8. [Resume & Config](#resume--config)
9. [Output Layout](#output-layout)
10. [Practical Recipes](#practical-recipes)
11. [Alternatives (gowitness / aquatone / httpx)](#alternatives-gowitness--aquatone--httpx)
12. [Troubleshooting & Gotchas](#troubleshooting--gotchas)
13. [Lessons Learned](#lessons-learned)
14. [References](#references)

---

## Summary `ris:Eye`

[EyeWitness](https://github.com/RedSiege/EyeWitness) takes screenshots of HTTP(S) targets, records response headers/source, and attempts to flag known default credentials. It is useful after host/URL discovery (nmap, httpx, masscan) when you need a visual triage of large web attack surfaces. Modern builds use **Chromium/Chrome + Selenium**, install into an isolated **Python venv**, and support text URL lists, Nmap/Nessus XML, single-URL mode, and resume via SQLite (`ew.db`).

> **Note —** + Authorised-use framing
> `fas:TriangleExclamation`
> 1. Only run against systems you own or have written authorisation to assess.
> 2. Screenshot tools generate significant browser/CPU load — tune `--threads` and timeouts on fragile lab targets.
> 3. Proxy through Burp/ZAP when you need request inspection (`--proxy-ip` / `--proxy-port`).

---

## Project Status & Alternatives `ris:Radar`

| Tool | Status (as of 2026) | Notes |
|---|---|---|
| **EyeWitness** (RedSiege) | **Actively maintained** | Formerly FortyNorthSecurity; Chromium-powered rewrite with venv install |
| **gowitness** | Actively maintained | Go, fast, good for large lists |
| **aquatone** | **Archived / unmaintained** | Still seen in older writeups; prefer gowitness or EyeWitness |
| **httpx `-screenshot`** | Actively maintained | Lightweight screenshots in the ProjectDiscovery pipeline |

> **Note —** + When to pick what
> `fas:Lightbulb`
> 1. **EyeWitness**: HTML report + default-cred hints + Nmap/Nessus XML ingest.
> 2. **gowitness**: speed and Go single-binary ops on large host lists.
> 3. **httpx -screenshot**: already in a `subfinder → httpx → nuclei` chain and only need quick PNGs.
> 4. **aquatone**: legacy labs only — project is archived.

---

## Quick-Reference Flag Table `fas:ClipboardList`

| Flag | Purpose |
|---|---|
| `--web` | HTTP screenshot via Selenium (default action) |
| `-f <file>` | Line-separated URL/host file |
| `-x <file.xml>` | Nmap XML or Nessus file |
| `--single <URL>` | Single URL/host |
| `--no-dns` | Skip DNS resolution |
| `-d <dir>` | Output directory for screenshots/report |
| `--timeout <sec>` | Page request timeout (default 7) |
| `--jitter <sec>` | Randomise order + random delay |
| `--delay <sec>` | Delay after navigator open before screenshot |
| `--threads <n>` | Worker threads (default ≈ 2×CPU, max 20) |
| `--max-retries <n>` | Retries on timeout (default 1) |
| `--results <n>` | Results per report page (default 25) |
| `--no-prompt` | Skip “open report?” prompt |
| `--user-agent <UA>` | Custom User-Agent |
| `--proxy-ip` / `--proxy-port` | HTTP/SOCKS proxy |
| `--proxy-type` | `http` (default) or `socks5` |
| `--show-selenium` | Show browser UI (debug) |
| `--resolve` | Resolve IP/hostname for targets |
| `--add-http-ports` / `--add-https-ports` | Extra ports treated as http/https |
| `--only-ports` | Exclusive port list |
| `--prepend-https` | Prepend `http://` and `https://` when scheme missing |
| `--validate-urls` | Validate only, no screenshots |
| `--skip-validation` | Skip URL validation |
| `--cookies key=val,...` | Extra cookies |
| `--width` / `--height` | Screenshot size (width 600–7680, height 400–4320) |
| `--resume <ew.db>` | Resume from DB |
| `--config <json>` | Load config file |
| `--create-config` | Write sample config |

---

## Installation `fas:Screwdriver`

> **Note —** + [EyeWitness](https://github.com/RedSiege/EyeWitness) Overview
> `ris:GlobalLine`
> Chromium-based HTTP screenshot and reporting tool with default-credential categorisation.
> 1. Accepts URL lists and Nmap/Nessus XML.
> 2. Isolates Python deps in `eyewitness-venv/`.
> 3. Writes searchable HTML report + `ew.db` for resume.

```bash
# Clone
git clone https://github.com/RedSiege/EyeWitness.git
cd EyeWitness/setup

# Linux / Kali / macOS (needs sudo for system packages + venv)
sudo ./setup.sh

# Activate venv (required before every run)
cd ..
source eyewitness-venv/bin/activate

# Smoke test
python Python/EyeWitness.py --single https://example.com
```

> **Note —** + Install Breakdown
> `ris:FileList`
> 1. **setup.sh / setup.ps1**: creates `eyewitness-venv/`, installs Selenium stack, pulls Chromium/ChromeDriver.
> 2. **Always activate the venv** — running system Python will miss deps / hit PEP 668 errors.
> 3. **Docker**: still marked “in development” upstream — prefer native install for labs.
> 4. **Cleanup**: delete `eyewitness-venv/` and re-run setup if the env breaks.

---

## Basic Usage `ris:Command`

```bash
source eyewitness-venv/bin/activate

# Single target
python Python/EyeWitness.py --web --single https://app.target.lab

# URL list
python Python/EyeWitness.py --web -f urls.txt -d ./ew-out --no-prompt

# From Nmap XML
python Python/EyeWitness.py --web -x nmap_http.xml -d ./ew-nmap --threads 8 --timeout 15
```

> **Note —** + Command Breakdown
> `ris:FileList`
> 1. **--web**: Selenium HTTP screenshot engine (required action).
> 2. **-f / -x / --single**: mutually exclusive-style inputs — provide at least one.
> 3. **-d**: fixed output path; omit to get a timestamped folder in CWD.
> 4. **--no-prompt**: automation-friendly (CI / headless SSH).

---

## Input Formats `ris:FileList`

```bash
# urls.txt — one URL or host per line
https://intranet.target.lab
http://10.10.10.50:8080
target.lab

# Nmap XML (open http/https services)
nmap -p 80,443,8080,8443 -sV -oX nmap_http.xml 10.10.10.0/24
python Python/EyeWitness.py --web -x nmap_http.xml -d ./ew-scan --prepend-https

# Validate URLs only
python Python/EyeWitness.py -f urls.txt --validate-urls -d ./ew-validate
```

> **Note —** + Prepend schemes carefully
> `fas:Lightbulb`
> 1. Bare hostnames need `--prepend-https` (or explicit schemes in the list).
> 2. Combine with `--only-ports 80,443,8080` when XML contains noisy services.
> 3. `--add-http-ports 8000,8888` for non-standard HTTP listeners.

---

## Timing, Proxy & Browser Options `ris:Global`

```bash
python Python/EyeWitness.py --web -f urls.txt -d ./ew-slow \
  --threads 5 --timeout 30 --delay 2 --jitter 5 \
  --proxy-ip 127.0.0.1 --proxy-port 8080 --proxy-type http \
  --user-agent "Mozilla/5.0 (authorised-assessment)" \
  --width 1920 --height 1080 \
  --cookies "SESSIONID=abc123"
```

> **Note —** + Tuning Breakdown
> `ris:FileList`
> 1. **--threads**: lower on low-RAM boxes; EyeWitness may auto-reduce based on memory.
> 2. **--timeout / --max-retries**: slow lab links and flaky VPN paths.
> 3. **--proxy-***: send browser traffic through Burp (`http`) or SOCKS.
> 4. **--width/--height**: must stay inside documented ranges or the parser exits.

---

## Resume & Config `fas:ClipboardList`

```bash
# Sample config
python Python/EyeWitness.py --create-config

# Use config
python Python/EyeWitness.py --web -f urls.txt --config ~/.eyewitness/config.json

# Resume interrupted run
python Python/EyeWitness.py --resume ./ew-out/ew.db
```

Example config keys (from upstream README):

```json
{
    "threads": 10,
    "timeout": 30,
    "delay": 0,
    "jitter": 0,
    "user_agent": "Custom User Agent",
    "proxy_ip": "127.0.0.1",
    "proxy_port": 8080,
    "output_dir": "./sessions",
    "prepend_https": false,
    "show_selenium": false,
    "resolve": false,
    "skip_validation": false,
    "results_per_page": 25,
    "max_retries": 2
}
```

---

## Output Layout `ris:FileList`

| Path | Contents |
|---|---|
| `report.html` | Main categorised report |
| `screens/` | Screenshot images |
| `source/` | Saved page source |
| `ew.db` | SQLite DB for resume |
| `logfile.log` | Run log |

Categories commonly include High Value, CMS, network devices, etc., plus default-credential hints when signatures match.

---

## Practical Recipes `ris:Command`

```bash
# 1) httpx live hosts → EyeWitness
httpx -l hosts.txt -ports 80,443,8080,8443 -o live.txt -silent
python Python/EyeWitness.py --web -f live.txt -d ./ew-live --threads 10 --no-prompt

# 2) Full TCP discover → XML → screenshots
nmap -p- --min-rate 2000 -oX full.xml 10.10.10.5
python Python/EyeWitness.py --web -x full.xml -d ./ew-full --prepend-https --timeout 20

# 3) Authenticated cookie session (lab app)
python Python/EyeWitness.py --web --single https://app.target.lab/admin \
  --cookies "auth=TOKEN" -d ./ew-auth --no-prompt
```

---

## Alternatives (gowitness / aquatone / httpx) `fas:Screwdriver`

### gowitness

```bash
go install github.com/sensepost/gowitness@latest
# single
gowitness single https://example.com
# file
gowitness file -f urls.txt
# scan CIDR / ports (check gowitness -h for current subcommands)
gowitness scan --cidr 10.10.10.0/24 --ports 80,443,8080
```

### aquatone (archived)

```bash
# Legacy pattern — prefer gowitness for new work
cat hosts.txt | aquatone -ports large -out ./aqua-out
cat nmap.xml | aquatone -nmap -out ./aqua-nmap
```

### httpx screenshots

```bash
httpx -l hosts.txt -screenshot -screenshot-timeout 10 -o httpx-live.txt
# screenshots land under ./screenshot/ (path may vary by httpx version — confirm with httpx -h)
```

> **Note —** + Aquatone maintenance
> `fas:TriangleExclamation`
> 1. [michenriksen/aquatone](https://github.com/michenriksen/aquatone) is archived.
> 2. Chrome/chromedp breakage is common on modern Kali.
> 3. Keep it only for reproducing old lab steps.

---

## Troubleshooting & Gotchas `fas:CircleXmark`

> **Note —** + Common failures
> `fas:CircleXmark`
> 1. **ChromeDriver missing** → re-run `setup/setup.sh` inside the project.
> 2. **PEP 668 / missing modules** → you forgot `source eyewitness-venv/bin/activate`.
> 3. **Timeouts over VPN** → raise `--timeout`, lower `--threads`.
> 4. **Low disk** → EyeWitness warns when free space is low; prune `source/` if needed.
> 5. **Width/height rejected** → stay within 600–7680 × 400–4320.

---

## Lessons Learned `fas:Lightbulb`

1. Treat EyeWitness as a **triage** step after httpx/nmap — not a replacement for content discovery (Ffuf-Cheatsheet, Nuclei-Cheatsheet).
2. Prefer **RedSiege** EyeWitness or **gowitness** over aquatone for new engagements.
3. Always **activate the venv**; most “broken install” tickets are path/Python confusion.
4. Use `--resume` after VPN drops — `ew.db` saves a lot of rework.
5. Screenshot noise is high; filter input with httpx status/title first.

---

## References `fas:BookOpen`

1. [RedSiege/EyeWitness](https://github.com/RedSiege/EyeWitness)
2. [EyeWitness README](https://github.com/RedSiege/EyeWitness/blob/master/README.md)
3. [sensepost/gowitness](https://github.com/sensepost/gowitness)
4. [michenriksen/aquatone (archived)](https://github.com/michenriksen/aquatone)
5. [ProjectDiscovery httpx](https://github.com/projectdiscovery/httpx)
6. [HackTricks — Web Discovery](https://book.hacktricks.xyz/)

---

#Tool #EyeWitness #gowitness #aquatone #httpx #WebTesting #Recon #Screenshots
