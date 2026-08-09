---
title: "WPScan"
description: "WPScan WordPress enumeration: plugins/themes/users, vuln API tokens and password attacks."
category: enumeration
tags: [enumeration, web, wordpress]
tools: [WPScan]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:Enumeration/WPScan.md"
---

# WPScan

WordPress security scanner. Enumerates core version, plugins, themes, users and other components, and (with an API token) reports known vulnerabilities. Pre-installed on Kali, Parrot, BlackArch, etc.

## Basic Scanning

Initial WordPress scan with default enumeration.

```bash
wpscan --url https://target.com
wpscan --url https://target.com --api-token YOUR_TOKEN
wpscan --url https://target.com --api-token YOUR_TOKEN --no-update
```

**Key options:**
- `--url` (required): Target WordPress URL
- `--api-token TOKEN`: WPScan API token for vulnerability data (25 free requests/day)
- `--no-update`: Skip database update check at scan start
- `--force`: Ignore robots.txt disallow rules
- `--verbose` / `-v`: Debug output
- `--no-banner`: Suppress banner
- `--random-user-agent` / `--rua`: Randomize User-Agent
- `--disable-tls-checks`: Ignore TLS/SSL errors (lab/testing only)

```bash
# Basic scan with API token
wpscan --url https://example.com --api-token abcd1234efgh5678

# Scan without updating database (faster)
wpscan --url https://example.com --api-token abcd1234efgh5678 --no-update

# Force scan even if robots.txt disallows
wpscan --url https://example.com --force

# Use environment variable for API token
export WPSCAN_API_TOKEN=abcd1234efgh5678
wpscan --url https://example.com
```

Default enumeration runs: vulnerable plugins (`vp`), vulnerable themes (`vt`), timthumbs (`tt`), config backups (`cb`), database exports (`dbe`), users (`u1-10`), media (`m1-10`). Vulnerabilities are only shown if an API token is provided. Output colours: green = low, yellow = medium, red = high/critical.

> **Note — Common errors.** `does not seem to be running WordPress` → try `--random-user-agent` or `--disable-tls-checks`. `403`/timeout on DB update → firewall blocking `data.wpscan.org`. No vulns shown → token missing or daily limit (25) exceeded.

**OPSEC:** default User-Agent `WPScan vX.X.X (...)` is logged; default scans generate 50-200+ HTTP requests (many 404s); rapid `wp-content/plugins/*` enumeration may trip IDS/IPS.

## Plugin Enumeration

Enumerate installed plugins (popular, all, or vulnerable only).

```bash
wpscan --url https://target.com -e vp    # vulnerable plugins only (default)
wpscan --url https://target.com -e p     # popular plugins (~6000 in DB)
wpscan --url https://target.com -e ap    # ALL plugins (aggressive, slow)
wpscan --url https://target.com -e vp,ap --plugins-detection mixed
```

**Options:**
- `--plugins-detection MODE`: passive (default), mixed, aggressive
- `--plugins-version-detection MODE`: mixed (default), passive, aggressive
- `--plugins-list FILE`: Custom plugin list to check
- `--exclude-content-based 'REGEX'`: Filter false positives (use when 100+ plugins detected)

```bash
# Enumerate vulnerable plugins only (default)
wpscan --url https://example.com -e vp --api-token TOKEN

# Enumerate all plugins aggressively (noisy)
wpscan --url https://example.com -e ap --plugins-detection aggressive --plugins-version-detection aggressive

# Combine with other enumerations
wpscan --url https://example.com -e vp,u1-20 --api-token TOKEN

# Filter false positives when 100+ plugins detected
wpscan --url https://example.com -e ap --exclude-content-based 'Error 404'

# Stealthy plugin enumeration
wpscan --url https://example.com -e p --plugins-detection passive --random-user-agent --throttle 2000
```

Detection modes: **passive** checks `readme.txt`/`changelog.txt` (~1-3 req/plugin, lowest noise); **mixed** adds Last-Modified header checks (~2-5 req/plugin); **aggressive** checks multiple version files (10+ req/plugin, many 404s). A full `-e ap` scan can generate tens of thousands of requests; WAFs may block aggressive enumeration ("no plugins found").

## Theme Enumeration

```bash
wpscan --url https://target.com -e vt    # vulnerable themes only (default)
wpscan --url https://target.com -e t     # popular themes (~2000 in DB)
wpscan --url https://target.com -e at     # ALL themes (aggressive)
wpscan --url https://target.com -e vt,at --themes-detection mixed
```

**Options:** `--themes-detection MODE` (passive default), `--themes-version-detection MODE`, `--themes-list FILE`.

```bash
# Popular themes with mixed detection
wpscan --url https://example.com -e t --themes-detection mixed

# Stealthy theme enumeration
wpscan --url https://example.com -e t --themes-detection passive --random-user-agent

# Combine theme and plugin enumeration
wpscan --url https://example.com -e vt,vp,u --api-token TOKEN
```

The active theme is usually detected automatically in a basic scan; inactive themes require `-e t`/`-e at`. Enumeration pattern: `wp-content/themes/THEME/style.css`, `readme.txt`.

## User Enumeration

```bash
wpscan --url https://target.com -e u          # default range 1-10
wpscan --url https://target.com -e u1-100
wpscan --url https://target.com -e u1-5,10,15-20
wpscan --url https://target.com -e u --users-detection mixed
```

**Options:** `--users-detection MODE` (passive default), `--users-list FILE`.

```bash
# Enumerate specific users
wpscan --url https://example.com -e u1,2,5,10

# Stealthy user enumeration with throttling
wpscan --url https://example.com -e u1-20 --users-detection passive --throttle 2000
```

Output shows username, display name, user ID. User ID 1 is often the site administrator; display names may leak real names (OSINT value).

**OPSEC:** passive mode queries `/wp-json/wp/v2/users` (REST API, single request); mixed adds `/?author=ID` archive enumeration; aggressive adds login error messages. WordPress ≥ 4.7.1 may restrict the REST API via plugins.

## Other Enumerations (timthumbs, config backups, DB exports, media)

```bash
wpscan --url https://target.com -e tt        # timthumb files (vulnerable image resizer)
wpscan --url https://target.com -e cb        # config backups (wp-config.php.bak, ~, .old)
wpscan --url https://target.com -e dbe       # database exports (.sql in web root)
wpscan --url https://target.com -e m1-15     # media files (requires Plain permalinks)
wpscan --url https://target.com -e tt,cb,dbe,m1-10
```

**Options:** `--timthumbs-detection`, `--config-backups-detection`, `--db-exports-detection`, `--medias-detection` (each passive/mixed/aggressive), plus matching `--*-list FILE` overrides.

```bash
# Config backups (information disclosure)
wpscan --url https://example.com -e cb --config-backups-detection aggressive

# Database exports (critical if found)
wpscan --url https://example.com -e dbe --db-exports-detection aggressive

# Stealthy combined enumeration
wpscan --url https://example.com -e tt,cb,dbe --throttle 1500
```

- **Timthumbs:** old image resizer with known RCE (high severity if found; mostly pre-2014).
- **Config backups:** `wp-config.php.bak`, `~`, `.old` — contain DB creds and salt keys (critical if accessible).
- **Database exports:** `.sql`, `.sql.gz`, `.sql.bak` — full site compromise if accessible.
- **Media:** uploaded files via `/?attachment_id=N` (needs Plain permalinks).

## Vulnerability Detection

Identify known vulnerabilities in core, plugins, and themes. Requires a WPScan API token.

```bash
wpscan --url https://target.com --api-token TOKEN
wpscan --url https://target.com --api-token TOKEN -e vp,vt
wpscan --url https://target.com --api-token TOKEN -e ap,at
export WPSCAN_API_TOKEN=TOKEN && wpscan --url https://target.com
```

**Options:** `--api-token TOKEN` (25 req/day free, 250/day paid), `--wp-version-all` (check all known core versions).

```bash
# Vulnerability scan with all plugins/themes and users
wpscan --url https://example.com --api-token TOKEN -e ap,at,u

# Check specific WordPress version vulnerabilities
wpscan --url https://example.com --api-token TOKEN --wp-version-all
```

Each vulnerability includes CVE/reference ID, description, affected/`Fixed in:` versions and a link. Vulnerability lookups are DB queries against WPScan's servers — **no extra HTTP requests to the target** (no OPSEC impact on the target). Token registration: register at wpscan.com, confirm email, retrieve the token from your profile.

## Password Attacks

Brute-force WordPress user passwords (authorized testing only).

```bash
wpscan --url https://target.com -U userlist.txt -P passwords.txt
wpscan --url https://target.com -U admin -P rockyou.txt --password-attack xmlrpc
wpscan --url https://target.com -P passwords.txt --password-attack wp-login
wpscan --url https://target.com -U admin,editor -P passwords.txt --password-attack xmlrpc-multicall
```

**Options:**
- `-U LIST`: Username(s) — single, comma-separated, or file path (auto-enumerates u1-10 if omitted)
- `-P FILE`: Password wordlist (required)
- `--password-attack MODE`: `wp-login` (default), `xmlrpc`, `xmlrpc-multicall`
- `--multicall-max-passwords N`: Max passwords per xmlrpc multicall (default 500)
- `--login-uri PATH`: Custom login URI (default `/wp-login.php`)

```bash
# Brute-force single user with wordlist
wpscan --url https://example.com -U admin -P /usr/share/wordlists/rockyou.txt

# Force xmlrpc-multicall (fastest, WP <4.4 only)
wpscan --url https://example.com -U admin -P passwords.txt --password-attack xmlrpc-multicall --multicall-max-passwords 1000

# Force wp-login mode (always works, slower)
wpscan --url https://example.com -U admin -P passwords.txt --password-attack wp-login

# Stealthy password attack
wpscan --url https://example.com -U admin -P short-list.txt --throttle 5000 --random-user-agent
```

Attack modes by speed: **xmlrpc-multicall** (500 passwords per POST, WP <4.4 only, removed in 4.4+) → **xmlrpc** (1/POST to `/xmlrpc.php`, often disabled) → **wp-login** (1/POST to `/wp-login.php`, always available). Valid creds print as `[+] Valid Credentials Found`.

> **Warning — OPSEC.** Failed logins are recorded in the WP dashboard and server auth logs. WAF/security plugins (Wordfence, iThemes) block xmlrpc by default; lockout plugins block after N failures. High-volume attacks leave large log evidence.

## Stealth Scanning

Minimize detection footprint during recon.

```bash
wpscan --url https://target.com --stealthy
wpscan --url https://target.com --random-user-agent --detection-mode passive --plugins-version-detection passive
wpscan --url https://target.com --stealthy --throttle 2000 --max-threads 1
wpscan --url https://target.com --stealthy -e p,u1-10 --throttle 3000 --no-banner
```

`--stealthy` is an alias for `--random-user-agent --detection-mode passive --plugins-version-detection passive`.

**Options:** `--user-agent VALUE`, `--user-agents-list FILE`, `--detection-mode passive`, `--throttle MILLISECONDS` (auto-sets `--max-threads 1`), `--max-threads 1`, `--no-banner`.

```bash
# Maximum stealth configuration
wpscan --url https://example.com --random-user-agent --detection-mode passive --plugins-detection passive --plugins-version-detection passive --themes-detection passive --throttle 5000 --max-threads 1 --no-banner

# Stealthy over Tor
wpscan --url https://example.com --stealthy --proxy socks5h://127.0.0.1:9050 --throttle 2000
```

Throttle guide: `--throttle 1000` ≈ 60 req/min, `--throttle 5000` ≈ 12 req/min. Stealthy mode drops a scan from 100-200 to ~20-50 requests but passive detection may fail to identify component versions. All requests are still logged even with stealth.

## Authentication, Cookies & Headers

Scan authenticated areas or pass custom HTTP headers/cookies.

```bash
wpscan --url https://target.com --http-auth username:password
wpscan --url https://target.com --cookie-string "wordpress_logged_in=value; wp_session=value"
wpscan --url https://target.com --cookie-jar /path/to/cookies.txt
wpscan --url https://target.com --headers "Authorization: Bearer TOKEN; X-Custom: value"
```

**Options:** `--http-auth username:password` (Basic/Digest), `--cookie-string "n=v; n2=v2"`, `--cookie-jar FILE` (Netscape/Mozilla format), `--headers "H1: v1; H2: v2"` (semicolon-separated).

```bash
# HTTP Basic auth with special characters (single-quote to prevent shell expansion)
wpscan --url https://example.com --http-auth 'user:p@$$w0rd!'

# Scan with WordPress session cookies (logged-in user)
wpscan --url https://example.com --cookie-string "wordpress_logged_in_abc123=admin%7C123456%7Chash"

# Authenticated enumeration
wpscan --url https://example.com --cookie-string "wordpress_logged_in=value" -e ap,at,u1-100
```

> **Note —** HTTP Basic auth bypasses web-server restrictions, not WordPress auth. Use a low-privilege account for OPSEC. Cookie strings use `;` separators (not commas). `--http-auth` credentials are base64-encoded and visible in logs.

## Proxy Configuration

```bash
wpscan --url https://target.com --proxy http://proxy.example.com:8080
wpscan --url https://target.com --proxy socks5://127.0.0.1:9050
wpscan --url https://target.com --proxy socks5h://127.0.0.1:9050
wpscan --url https://target.com --proxy http://user:pass@proxy.example.com:8080
```

Supported protocols: `http://`, `socks4://`, `socks5://`, `socks5h://`. Use **`socks5h://`** for remote DNS resolution (prevents DNS leaks — recommended for Tor). Adjust `--request-timeout SECONDS` (default 60) and `--connect-timeout SECONDS` (default 30) for slow proxies.

```bash
# HTTP proxy (Burp/ZAP interception)
wpscan --url https://example.com --proxy http://127.0.0.1:8080

# SOCKS5 with remote DNS (Tor), increased timeout
wpscan --url https://example.com --proxy socks5h://127.0.0.1:9050 --request-timeout 120 --connect-timeout 60
```

> **Note — Common errors.** `407 Proxy Authentication Required` → add `http://user:pass@proxy:port`. DNS leak with Tor → use `socks5h://` not `socks5://`. SSL errors through an intercepting proxy → `--disable-tls-checks` (trust implications). Ensure the proxy allows HTTPS to wpscan.com:443 for API lookups.

## Custom WordPress Paths

Scan installs with non-standard directory structure.

```bash
wpscan --url https://target.com --wp-content-dir custom-content
wpscan --url https://target.com --wp-plugins-dir custom-content/extensions
wpscan --url https://target.com --wp-content-dir wp-core/content --wp-plugins-dir wp-core/content/plugins
```

`--wp-content-dir DIR` and `--wp-plugins-dir DIR` are relative to the WordPress root. Discover the real paths from page source, e.g. `<link rel='stylesheet' href='/custom-wp/content/themes/twentytwentyone/style.css'>` → `--wp-content-dir custom-wp/content --wp-plugins-dir custom-wp/content/plugins`. Set in wp-config.php via the `WP_CONTENT_DIR` / `WP_PLUGIN_DIR` constants.

## Output Formats

```bash
wpscan --url https://target.com -o report.txt
wpscan --url https://target.com -f json -o report.json
wpscan --url https://target.com -f cli-no-colour -o report.txt
wpscan --url https://target.com --format json --output results.json
```

**Formats:** `cli` (colored, default), `cli-no-colour`/`cli-no-color` (plain text), `json` (machine-readable).

```bash
# JSON output + parse with jq (WordPress version)
wpscan --url https://example.com -f json -o report.json && jq '.version.number' report.json

# JSON output + parse vulnerabilities
wpscan --url https://example.com --api-token TOKEN -f json -o report.json && jq '.plugins[].vulnerabilities' report.json
```

JSON top-level keys (v3.8.x): `target_url`, `version`, `interesting_findings`, `plugins`, `themes`, `users`, `vulnerabilities`. Each plugin/theme entry carries `slug`, `location`, `version`, `vulnerabilities[]`.

## Installation

```bash
# Kali / Debian / Ubuntu (apt)
sudo apt update && sudo apt install wpscan
wpscan --version

# Ruby gem (Debian/Ubuntu) — needs Ruby 3.x+
sudo apt install ruby-full ruby-dev libcurl4-openssl-dev build-essential
sudo gem install wpscan

# Fix nokogiri dependency error (common on Debian/Ubuntu)
sudo apt install ruby-dev build-essential libxml2-dev libxslt1-dev zlib1g-dev
sudo gem install nokogiri --platform=ruby
sudo gem install wpscan

# Docker (no local Ruby needed)
docker pull wpscanteam/wpscan
docker run -it --rm wpscanteam/wpscan --url https://example.com --api-token TOKEN

# Docker with output file (mount volume)
docker run -it --rm -v /tmp:/output wpscanteam/wpscan --url https://example.com -o /output/report.txt

# Git clone (development version)
git clone https://github.com/wpscanteam/wpscan.git && cd wpscan
bundle install
./bin/wpscan --url https://example.com
```

## Sources

- https://github.com/wpscanteam/wpscan
- https://wpscan.com/docs/
- https://wpscan.com/api
- https://www.kali.org/tools/wpscan/
