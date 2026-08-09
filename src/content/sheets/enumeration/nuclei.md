---
title: "Nuclei"
description: "Nuclei template-based vulnerability scanning: template selection, tags, severity and workflows."
category: enumeration
tags: [enumeration, scanning, vulnerabilities]
tools: [Nuclei]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:Tools/Nuclei-Cheatsheet.md"
---

# Nuclei

Fast, template-driven vulnerability scanner from ProjectDiscovery (v3.x). Nuclei sends requests defined in community-maintained YAML **templates** and matches responses to confirm vulnerabilities with near-zero false positives. It supports HTTP, DNS, TCP, SSL, WHOIS, headless-browser, JavaScript and code protocols. The typical workflow is a recon pipeline — enumerate subdomains with subfinder, probe live hosts with httpx, then pipe the live URLs into `nuclei`. It clusters similar requests and runs templates in parallel, so it is fast, but that same speed can trip WAFs and rate limits on fragile CTF/lab targets — tune `-rl` and `-c` accordingly.

> **Important — Version note:**
> 1. Nuclei is in **active development** — flags change between minor releases. Always confirm with `nuclei -h`.
> 2. Requires **Go >= 1.24.2** to build from source.
> 3. This note targets **v3.x**. A few flag names people commonly assume do **not** exist (see Troubleshooting).

## Quick-Reference Flag Table

| Flag (short / long) | Purpose |
|---|---|
| `-u` / `-target` | Target URL(s)/host(s), comma-separated |
| `-l` / `-list` | File of targets, one per line |
| `-im` / `-input-mode` | Input file mode: `list`, `burp`, `jsonl`, `yaml`, `openapi`, `swagger` |
| `-t` / `-templates` | Template file/dir to run |
| `-turl` / `-template-url` | Run template(s) from a URL |
| `-w` / `-workflows` | Run a workflow (ordered template chain) |
| `-et` / `-exclude-templates` | Exclude template file/dir |
| `-tags` / `-etags` | Include / exclude by tag |
| `-itags` / `-include-tags` | Force-run tags even if excluded by default |
| `-s` / `-severity` | Filter by severity: `info,low,medium,high,critical,unknown` |
| `-es` / `-exclude-severity` | Exclude by severity |
| `-a` / `-author` | Filter by template author |
| `-id` / `-eid` | Include / exclude by template ID |
| `-tc` / `-template-condition` | Run templates matching an expression |
| `-as` / `-automatic-scan` | Wappalyzer tech-detection → tag mapping |
| `-nt` / `-new-templates` | Only templates new in latest release |
| `-o` / `-output` | Write findings to file |
| `-j` / `-jsonl` | JSONL output |
| `-je` / `-json-export` | Export results as JSON file |
| `-jle` / `-jsonl-export` | Export results as JSONL file |
| `-se` / `-sarif-export` | Export results as SARIF file |
| `-me` / `-markdown-export` | Export results as Markdown dir |
| `-silent` | Findings only, no banners/logs |
| `-nc` / `-no-color` | Disable ANSI colour |
| `-v` / `-vv` | Verbose / show loaded templates |
| `-debug` | Show all requests + responses |
| `-sresp` / `-store-resp` | Save all req/resp to disk |
| `-rl` / `-rate-limit` | Requests per second (default 150) |
| `-bs` / `-bulk-size` | Hosts analysed in parallel per template (default 25) |
| `-c` / `-concurrency` | Templates run in parallel (default 25) |
| `-timeout` | Per-request timeout seconds (default 10) |
| `-retries` | Retries per failed request (default 1) |
| `-mhe` / `-max-host-error` | Errors before skipping a host (default 30) |
| `-p` / `-proxy` | HTTP/SOCKS5 proxy |
| `-H` / `-header` | Custom header/cookie `key:value` |
| `-sni` | TLS SNI hostname |
| `-i` / `-interface` | Network interface for network scans |
| `-sip` / `-source-ip` | Source IP for network scans |
| `-r` / `-resolvers` | Resolver list file |
| `-sr` / `-system-resolvers` | Use system DNS as fallback |
| `-iserver` / `-itoken` | Self-hosted Interactsh server / token |
| `-ni` / `-no-interactsh` | Disable OAST, skip OAST templates |
| `-sf` / `-secret-file` | Secrets/auth config file |
| `-dast` | Enable DAST (fuzzing) templates |
| `-ft` / `-fuzzing-type` | Override fuzz type: `replace,prefix,postfix,infix` |
| `-fm` / `-fuzzing-mode` | Override fuzz mode: `multiple,single` |
| `-validate` | Validate templates |
| `-up` / `-update` | Update the engine |
| `-ut` / `-update-templates` | Update templates |
| `-headless` | Enable headless-browser templates |
| `-page-timeout` | Seconds to wait per page in headless (default 20) |

## Installation

```bash
# 1) Go install (needs Go >= 1.24.2) — installs to $GOPATH/bin
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# 2) Homebrew (macOS / Linux)
brew install nuclei

# 3) Docker
docker pull projectdiscovery/nuclei:latest
docker run --rm projectdiscovery/nuclei:latest -u https://example.com

# 4) Binary release — download from GitHub releases, unzip, move to PATH
# https://github.com/projectdiscovery/nuclei/releases
unzip nuclei_3.x.x_linux_amd64.zip
sudo mv nuclei /usr/local/bin/

# Verify
nuclei -version
```

> **Install breakdown:**
> 1. **go install** — pulls latest tagged source; keep Go updated or the build fails.
> 2. **brew** — easiest on Kali/macOS; may lag a release behind.
> 3. **docker** — mount a volume for templates/output; the container has no persistent template store by default.
> 4. **binary** — fastest for air-gapped/offline lab boxes; grab the matching arch.

## Template Management

Templates live in **`~/nuclei-templates/`** by default. Override with the `NUCLEI_TEMPLATES_DIR` environment variable or the `-ud` flag. On first run nuclei auto-downloads templates.

```bash
# Update the nuclei engine itself
nuclei -up
nuclei -update

# Update templates to the latest release
nuclei -ut
nuclei -update-templates

# Install/update templates into a custom directory
nuclei -ut -ud /opt/nuclei-templates

# Disable the automatic update check (useful in CI / offline labs)
nuclei -u https://target -duc

# Show installed templates version
nuclei -tv

# List all templates matching current filters (dry run, no scan)
nuclei -tl -tags cve -severity critical

# List all available tags
nuclei -tgl

# Run only templates added in the latest templates release
nuclei -u https://target -nt

# Reset ALL nuclei config + data (including templates)
nuclei -reset
```

> **Warning — Template staleness:**
> 1. Run `-ut` before every engagement — new CVEs land daily.
> 2. `-nt` (new-templates) is great for re-scanning known targets for freshly-published CVEs only.
> 3. There is **no `-tlds` flag** in nuclei — see Gotchas.

## Target Input

```bash
# Single / multiple targets (comma-separated)
nuclei -u https://example.com
nuclei -u https://a.com,https://b.com

# File of targets (one per line) — this is the "target file" flag
nuclei -l urls.txt

# Pipe from other ProjectDiscovery tools (the classic pipeline)
subfinder -d example.com -silent | httpx -silent | nuclei -silent

# Read a raw HTTP request (e.g. a Burp saved request) as input
nuclei -l request.txt -im burp

# Scan an entire subnet for network issues
nuclei -u 192.168.110.0/24

# Exclude hosts from the input list
nuclei -l urls.txt -eh 10.10.10.5,10.10.10.6
```

> **Input breakdown:**
> 1. **-u / -target** — inline targets; accepts URLs, hosts, IPs, CIDRs.
> 2. **-l / -list** — the file-based equivalent (this is what "target file" means — there is no `-target-file` flag).
> 3. **stdin** — nuclei auto-reads piped input; disable with `-no-stdin`.
> 4. **-im burp** — parse a saved Burp/HTTP request file instead of a plain URL list. (There is no standalone `-request` flag; use `-im burp` / `-im jsonl` / `-im openapi`.)

## Template Selection & Filtering

```bash
# Run a specific template file, directory, or category
nuclei -u https://target -t http/cves/
nuclei -u https://target -t http/cves/ -t ssl/

# Run a template straight from a URL
nuclei -u https://target -turl https://example.com/my-template.yaml

# Run a workflow (ordered, conditional template chain)
nuclei -u https://target -w workflows/wordpress-workflow.yaml

# Exclude a template file/dir
nuclei -u https://target -et http/miscellaneous/

# Tag-based include / exclude
nuclei -u https://target -tags cve,rce
nuclei -u https://target -etags dos,fuzz,intrusive

# Force-run tags even if excluded by default config
nuclei -u https://target -itags fuzz

# Severity include / exclude
nuclei -u https://target -s critical,high
nuclei -u https://target -es info,low

# Author filter
nuclei -u https://target -a pdteam,geeknik

# Template ID include / exclude (supports wildcards)
nuclei -u https://target -id CVE-2021-44228
nuclei -u https://target -id 'apache-*' -eid apache-detect

# Expression-based template condition
nuclei -u https://target -tc 'contains(tags,"cve") && severity=="critical"'

# Only newly-added templates
nuclei -u https://target -nt

# Automatic scan: Wappalyzer tech detection → maps to matching template tags
nuclei -u https://target -as
```

> **Tip — Filtering strategy:**
> 1. Start broad with `-as` to fingerprint tech, then re-run targeted `-tags`.
> 2. Combine filters — `-tags cve -s critical,high` is the highest-signal quick pass.
> 3. `-tc` (template-condition) is the power-user filter when tags/severity aren't precise enough.

## Output

```bash
# Plain text file
nuclei -u https://target -o findings.txt

# JSONL to stdout (best for piping into jq / tooling)
nuclei -u https://target -j

# Export formats (write structured report files)
nuclei -u https://target -je results.json      # JSON
nuclei -u https://target -jle results.jsonl     # JSONL
nuclei -u https://target -se results.sarif      # SARIF (for GitHub code scanning)
nuclei -u https://target -me nuclei_report/     # Markdown dir

# Clean, quiet output
nuclei -u https://target -silent -nc

# Verbose / debug
nuclei -u https://target -v          # verbose
nuclei -u https://target -vv         # show every template loaded
nuclei -u https://target -debug      # dump all requests + responses

# Save every request/response for later triage
nuclei -u https://target -sresp -srd ./resp/
```

> **Output breakdown:**
> 1. **-silent + -nc** — the combo for clean logs you can paste into a report or feed to a script.
> 2. **-je / -jle / -se / -me** — report *exports* (write a file); **-j** just changes stdout format.
> 3. **-sresp / -srd** — stores raw req/resp — invaluable for confirming a finding isn't a false positive.
> 4. **-debug** — use when a template *should* fire but doesn't; you'll see exactly what came back.

## Rate Limiting & Performance

```bash
# Slow, polite scan for a fragile lab / CTF box
nuclei -u https://target -rl 20 -c 10 -bs 10 -timeout 15 -retries 2

# Requests-per-minute window (older -rlm is DEPRECATED; use -rld for duration)
nuclei -u https://target -rl 300 -rld 1m

# Aggressive scan for a robust target you own
nuclei -l urls.txt -rl 500 -c 50 -bs 50

# Tune host-error tolerance (skip dead hosts sooner)
nuclei -l urls.txt -mhe 10
nuclei -l urls.txt -no-mhe            # never skip a host on errors

# Headless-browser scanning (DOM XSS, JS-heavy apps)
nuclei -u https://target -headless -page-timeout 30
nuclei -u https://target -headless -headc 5     # headless concurrency
```

| Flag | Meaning | Default |
|---|---|---|
| `-rl` | Requests per second | 150 |
| `-rld` | Rate-limit duration window | 1s |
| `-bs` | Hosts in parallel per template | 25 |
| `-c` | Templates in parallel | 25 |
| `-timeout` | Per-request timeout (s) | 10 |
| `-retries` | Retries per failed request | 1 |
| `-mhe` | Max errors before skipping host | 30 |
| `-headc` | Headless templates in parallel | 10 |
| `-page-timeout` | Wait per page in headless (s) | 20 |

> **Warning — Speed vs. stealth:**
> 1. High `-rl`/`-c` will trip WAFs and can crash flaky HTB/CTF services.
> 2. **`-headc` is headless concurrency** — do NOT confuse it with `-hc`, which is `-health-check`.
> 3. On labs, prefer `-rl 20 -c 10` and raise it only if the target is stable.

## Network / Proxy

```bash
# Route through Burp / a SOCKS5 pivot
nuclei -u https://target -p http://127.0.0.1:8080
nuclei -u https://target -p socks5://127.0.0.1:1080

# Custom headers / cookies injected into EVERY http request
nuclei -u https://target -H 'Authorization: Bearer eyJ...'
nuclei -u https://target -H 'Cookie: session=abc123' -H 'X-Api-Key: secret'

# TLS SNI override (virtual hosts / SNI-routed apps)
nuclei -u https://10.10.10.10 -sni app.internal.htb

# Custom resolvers + system fallback
nuclei -l urls.txt -r resolvers.txt -sr

# Network-scan interface / source IP (e.g. through a ligolo tun)
nuclei -u 192.168.110.0/24 -i ligolo -sip 192.168.110.10
```

> **Tip — Proxy + pivot:**
> 1. Send nuclei through Burp with `-p` to record traffic and manually verify hits.
> 2. On internal ranges reached via a Ligolo double tunnel, set `-i <tun>` so replies route back correctly.
> 3. `-H` applies to every HTTP template — perfect for authenticated scans (see below).

## Interactsh / OOB

Nuclei uses Interactsh for out-of-band (OAST) detection — blind SSRF, blind SQLi, RCE with no direct response, etc. By default it uses the public servers (`oast.pro`, `oast.live`, ...).

```bash
# Point at your own self-hosted Interactsh server
nuclei -u https://target -iserver https://oast.mydomain.com -itoken MYTOKEN

# Disable OAST entirely (skips OAST-based templates) — offline / air-gapped labs
nuclei -u https://target -ni
```

> **Important — When to self-host or disable:**
> 1. Self-host (`-iserver`/`-itoken`) when the target can't reach public OAST domains or you need to keep callbacks private.
> 2. Use `-ni` on isolated lab networks with **no egress** — otherwise OAST templates just time out and slow the scan.

## Authentication

Two ways to authenticate: quick header/cookie injection, or a structured **secret file** for multi-target auth.

```bash
# Quick auth via headers/cookies
nuclei -u https://app.target -H 'Authorization: Bearer <token>'
nuclei -u https://app.target -H 'Cookie: PHPSESSID=<value>'

# Structured secrets/auth file (per-domain creds, headers, cookies)
nuclei -l urls.txt -sf secrets.yaml
nuclei -l urls.txt -sf secrets.yaml -ps    # prefetch secrets before scanning
```

```yaml
# secrets.yaml — example static auth strategy
static:
  - type: header
    domains:
      - app.target.htb
    headers:
      - key: Authorization
        value: Bearer eyJ...
  - type: cookie
    domains:
      - app.target.htb
    cookies:
      - key: session
        value: abcdef123456
```

> **Auth breakdown:**
> 1. **-H** — simplest for a single authenticated target; header applies to all HTTP requests.
> 2. **-sf** — scales auth across many domains and supports header/cookie/query/basic strategies.
> 3. **-ps** — prefetch fires the auth flow up front so tokens are ready before templates run.
> 4. Header casing is preserved from the secrets file — matters for case-sensitive APIs.

## Fuzzing / DAST Mode

Nuclei's DAST mode runs **fuzzing templates** that inject payloads into parameters (query, body, headers, path) to find injection-class bugs. The old `-fuzz` flag is deprecated — use `-dast`.

```bash
# Enable DAST / fuzzing templates
nuclei -u 'https://target/search?q=test' -dast

# Override the fuzzing behaviour set in the template
nuclei -u 'https://target/?id=1' -dast -ft replace -fm single

# Control fuzz aggression (payload volume) and scope
nuclei -l urls.txt -dast -fa medium -cs '.*target\.htb.*'

# Show which parameters are being fuzzed (debugging)
nuclei -u 'https://target/?id=1' -dast -dfp
```

| Flag | Meaning | Values |
|---|---|---|
| `-dast` | Enable DAST/fuzz templates | — |
| `-ft` / `-fuzzing-type` | Override injection style | `replace,prefix,postfix,infix` |
| `-fm` / `-fuzzing-mode` | Override combination mode | `multiple,single` |
| `-fa` / `-fuzz-aggression` | Payload volume | `low,medium,high` (default `low`) |
| `-cs` / `-fuzz-scope` | In-scope URL regex | regex |
| `-cos` / `-fuzz-out-scope` | Out-of-scope URL regex | regex |
| `-dfp` / `-display-fuzz-points` | Print fuzz points | — |

> **Tip — DAST tips:**
> 1. Feed DAST mode URLs **with parameters** — crawl first (e.g. with `katana`) so there's something to fuzz.
> 2. Start at `-fa low`; raise only if you need deeper coverage — high aggression is loud.
> 3. Combine with `-p` (Burp proxy) to inspect and replay interesting fuzz hits.

## Writing Custom Templates

Every template needs three parts: **`id`**, an **`info`** block, and at least one **protocol block** (usually `http`).

```yaml
id: example-panel-detect

info:
  name: Example Admin Panel Detection
  author: netrunner
  severity: info
  description: Detects an exposed Example admin login panel.
  tags: panel,exposure,example

http:
  - method: GET
    path:
      - "{{BaseURL}}/admin/login"

    matchers-condition: and
    matchers:
      - type: status
        status:
          - 200
      - type: word
        part: body
        words:
          - "Example Admin"
          - "Sign in"
        condition: or

    extractors:
      - type: regex
        part: body
        name: version
        group: 1
        regex:
          - 'v([0-9.]+)'
```

> **Matcher types:**
> 1. **word** — literal string(s) in a response part.
> 2. **regex** — regular-expression match.
> 3. **status** — HTTP status code.
> 4. **size** — response length in bytes.
> 5. **dsl** — expression logic, e.g. `duration >= 5`, `status_code==200 && len(body)>1000`.
> 6. **binary** — hex pattern in binary responses.
> 7. **xpath** — XPath query against XML/HTML.
> 8. `matchers-condition: and|or` combines multiple matchers (default is `or`).

> **Extractor types:**
> 1. **regex** — pull data via regex (optional capture `group`).
> 2. **kval** — grab a header/cookie by key.
> 3. **json** — JQ-like extraction from JSON bodies.
> 4. **xpath** — XML/HTML extraction (optional `attribute`).
> 5. **dsl** — expression-based extraction, e.g. `len(body)`.
> 6. Extractors capture dynamic values (CSRF tokens, session IDs) for reuse in later requests.

```yaml
# Variables + payloads (fuzzing / brute) skeleton
variables:
  useragent: "Mozilla/5.0"

http:
  - method: GET
    path:
      - "{{BaseURL}}/search?q={{injection}}"
    headers:
      User-Agent: "{{useragent}}"
    attack: clusterbomb        # batteringram | pitchfork | clusterbomb
    payloads:
      injection:
        - "'"
        - "' OR '1'='1"
        - "' AND SLEEP(5)--"
    matchers:
      - type: dsl
        dsl:
          - "duration >= 5"
```

```bash
# Validate a template before running it
nuclei -validate -t my-template.yaml

# Run your local template against a target
nuclei -u https://target -t ./my-template.yaml

# Run a template hosted at a URL
nuclei -u https://target -turl https://raw.githubusercontent.com/.../my-template.yaml

# Display a template's contents / list matches without scanning
nuclei -t ./my-template.yaml -td
nuclei -t ./my-template.yaml -tl
```

> **Warning — Template gotchas:**
> 1. Always `-validate` custom templates — a bad matcher silently produces no hits.
> 2. `part:` matters (`body`, `header`, `all`, `response`) — matching the wrong part is the #1 "why won't it fire" bug.
> 3. Signed/unsigned: `-dut` disables unsigned templates; your local custom ones are unsigned, so don't set `-dut` when testing them.

## Practical Recipes

**Full recon pipeline: subfinder → httpx → nuclei** (the bread-and-butter external-recon chain):

```bash
subfinder -d example.com -silent \
  | httpx -silent \
  | nuclei -silent -tags cve,exposure -s critical,high,medium -o findings.txt
```

**Polite single-target scan (HTB / CTF box)** — slow rate, moderate concurrency, retries:

```bash
nuclei -u http://10.10.10.10 -rl 20 -c 10 -bs 10 -timeout 15 -retries 2 -o box_scan.txt
```

**CVE-only scan:**

```bash
nuclei -u https://target -tags cve -s critical,high
nuclei -u https://target -t http/cves/2024/
```

**Tech-specific scan (fingerprint first, then target):**

```bash
# Auto-detect tech and map to templates
nuclei -u https://target -as

# Or target a known stack by tag
nuclei -u https://target -tags wordpress,wp-plugin
nuclei -u https://target -tags apache,tomcat
```

**Exposed panels & subdomain takeover:**

```bash
# Login / admin panels
nuclei -l urls.txt -tags panel,exposure

# Subdomain takeover across a subdomain list
subfinder -d example.com -silent | nuclei -tags takeover -silent
```

**Scan against a saved Burp request:**

```bash
# Export the request from Burp (Copy to file), then:
nuclei -l burp_request.txt -im burp -tags cve,injection -dast
```

## Common One-Liners

```bash
# Update engine + templates in one go
nuclei -up && nuclei -ut

# Quick high-signal pass on one target
nuclei -u https://target -tags cve -s critical,high -silent -nc

# Full pipeline, JSON export, quiet
subfinder -d target.com -silent | httpx -silent | nuclei -j -je out.json -silent

# Scan a list, exclude noisy/intrusive templates
nuclei -l urls.txt -etags dos,fuzz,intrusive -es info -o clean.txt

# Log4Shell / specific CVE across many hosts
nuclei -l urls.txt -id CVE-2021-44228 -silent

# Network subnet sweep through a ligolo tun
nuclei -u 192.168.110.0/24 -i ligolo -tags network -o net.txt

# DAST fuzz a parameterised URL through Burp
nuclei -u 'https://target/?id=1' -dast -p http://127.0.0.1:8080 -dfp

# Authenticated scan with a bearer token, save all responses
nuclei -u https://app.target -H 'Authorization: Bearer TOKEN' -sresp -srd ./resp/

# Dry-run: list which templates a filter would run
nuclei -tl -tags cve -s critical

# Re-scan known target for only newly-released templates
nuclei -u https://target -nt -silent
```

## Troubleshooting & Gotchas

> **Flags that don't exist / are easy to confuse:**
> 1. **`-tlds`** — not a nuclei flag. Nuclei doesn't take a TLD list; scope is controlled by targets, `-eh`, and fuzz scope regex (`-cs`/`-cos`).
> 2. **`-target-file`** — not a flag. The file-of-targets flag is **`-l` / `-list`**.
> 3. **`-request`** — not a flag. Parse raw HTTP/Burp requests with **`-im burp`** (or `-im jsonl`/`-im openapi`).
> 4. **`-hc`** — this is **`-health-check`**, *not* headless concurrency. Headless concurrency is **`-headc`**.
> 5. **`-json`** — the JSON stdout flag is **`-j` / `-jsonl`**; file exports are **`-je`/`-jle`/`-se`/`-me`**.
> 6. **`-template-url`** is **`-turl`** (not `-tu`).

> **Common runtime issues:**
> 1. **WAF trips / blocked mid-scan** → lower `-rl` and `-c`; add `-p` to watch the block in Burp.
> 2. **False positives** → confirm with `-sresp`/`-debug`, then exclude with `-eid <id>`.
> 3. **Stale results / missing new CVEs** → run `-ut`; use `-nt` to hit only fresh templates.
> 4. **Noisy logs** → add `-silent -nc` for clean, scriptable output.
> 5. **OAST templates hang on isolated labs** → add `-ni` to disable Interactsh.
> 6. **JS/DOM-heavy app finds nothing** → try `-headless` (root on Linux disables the Chrome sandbox).
> 7. **Host skipped early** → raise `-mhe` or use `-no-mhe` for flaky lab services.

## Lessons Learned

1. **Confirm flags against `nuclei -h`, not memory** — several "obvious" flags (`-tlds`, `-target-file`, `-request`) don't exist, and short aliases collide (`-hc` ≠ headless).
2. **Update templates before every scan** — nuclei's value is the community template feed; a stale feed misses this week's CVEs. Use `-nt` to re-check known targets cheaply.
3. **Tune rate before scanning labs** — default `-rl 150` will hammer a fragile HTB/CTF box; `-rl 20 -c 10` is a safe starting point.
4. **The `subfinder → httpx → nuclei` pipeline is the standard external-recon workflow** — pipe live hosts in via stdin and let nuclei do the detection.
5. **Verify hits before reporting** — pair `-sresp`/`-debug` with a Burp proxy (`-p`) to rule out false positives, then `-eid` to suppress known noise.

## References

- Nuclei Overview — https://docs.projectdiscovery.io/tools/nuclei/overview
- Nuclei Installation — https://docs.projectdiscovery.io/tools/nuclei/install
- Nuclei Command-Line Flags — https://docs.projectdiscovery.io/tools/nuclei/running
- Nuclei GitHub — https://github.com/projectdiscovery/nuclei
- Nuclei Templates — https://github.com/projectdiscovery/nuclei-templates
- Matchers Reference — https://docs.projectdiscovery.io/templates/reference/matchers
- Extractors Reference — https://docs.projectdiscovery.io/templates/reference/extractors
- Interactsh (OAST) — https://github.com/projectdiscovery/interactsh
- subfinder — https://github.com/projectdiscovery/subfinder
- httpx — https://github.com/projectdiscovery/httpx
