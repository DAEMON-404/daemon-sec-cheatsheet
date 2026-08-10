---
title: "Cheatsheet - Infrastructure Enumeration Tools 1"
description: "curl -s \"https://crt.sh/?q=TARGET.com&output=json\" | jq -r '.[].name_value' | sort -u"
category: enumeration
tags: ["enumeration"]
tools: ["Gitleaks", "TruffleHog"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Enumeration/Cheatsheet - Infrastructure Enumeration Tools 1.md"
---
# Basic query — good starting point
curl -s "https://crt.sh/?q=TARGET.com&output=json" | jq -r '.[].name_value' | sort -u

# Output
*.TARGET.com
admin.TARGET.com
blog.TARGET.com
mail.TARGET.com
vpn.TARGET.com
www.TARGET.com
```

> [!info]+ Command Breakdown
> 1. **jq -r '.[].name_value'** — extracts ONLY the `name_value` field from every array entry using `-r` (raw output, no quotes)
> 2. This is cleaner than the `grep | cut | awk` chain in the original notes — fewer failure points
> 3. **sort -u** — deduplicates; wildcard entries like `*.TARGET.com` are preserved as-is

---

```bash
# Strip wildcards and get clean hostnames only
curl -s "https://crt.sh/?q=TARGET.com&output=json" \
  | jq -r '.[].name_value' \
  | sed 's/\*\.//g' \
  | sort -u \
  | grep -v "^TARGET.com$" > subdomains.txt

cat subdomains.txt
admin.TARGET.com
blog.TARGET.com
mail.TARGET.com
vpn.TARGET.com
www.TARGET.com
```

> [!info]+ Command Breakdown
> 1. **sed 's/\*\.//g'** — strips the `*.` wildcard prefix to leave a clean hostname
> 2. **grep -v "^TARGET.com$"** — removes the bare root domain from the list (you already know it)
> 3. **> subdomains.txt** — saves to file for use in the next steps (host loop, Shodan loop)
> 4. *This output feeds directly into the `host` bulk resolution loop*

---

```bash
# Query for EXPIRED certs too — these reveal old subdomains that may still be live
curl -s "https://crt.sh/?q=%25.TARGET.com&output=json" | jq -r '.[].name_value' | sort -u
```

> [!info]+ Command Breakdown
> 1. **%25.TARGET.com** — URL-encoded `%` wildcard; matches ALL subdomains ever issued a cert, including expired ones
> 2. Expired subdomains are often forgotten by admins — they may still resolve and run old, unpatched services
> 3. *Cross-reference this list against your `host` resolution output to see which old subdomains are still live*

---

> [!warning]+ crt.sh Gotchas
> 1. Results include **third-party issued certs** — a subdomain listed here is NOT guaranteed to be company-owned infrastructure
> 2. Wildcard certs (`*.TARGET.com`) confirm the domain uses wildcard SSL but don't enumerate actual subdomains — use other methods to enumerate what lives under the wildcard
> 3. **Rate limiting** — if querying many domains, add `sleep 2` between requests or use the Shodan/Subfinder pipeline instead
> 4. Results can lag by hours after a new cert is issued — not real-time

---

## curl + jq — API Querying and JSON Parsing

> [!tip]+ jq is More Powerful Than Used in the Notes
> The original notes use `jq .` (pretty print only). Here are more useful filters:

```bash
# Extract only specific fields — issuer + subdomain + expiry
curl -s "https://crt.sh/?q=TARGET.com&output=json" \
  | jq -r '.[] | [.issuer_name, .name_value, .not_after] | @tsv'

# Output (tab-separated)
C=US, O=Let's Encrypt, CN=R3    mail.TARGET.com    2025-12-01T00:00:00
C=US, O=Cloudflare, Inc.        www.TARGET.com     2026-01-15T00:00:00
```

> [!info]+ Command Breakdown
> 1. **'.[] | ...'** — iterates over every element in the array
> 2. **[.issuer_name, .name_value, .not_after]** — selects three specific fields into an array
> 3. **@tsv** — formats the array as tab-separated values — easy to `cut`, `grep`, or import into a spreadsheet
> 4. *The issuer column immediately tells you if a subdomain uses Cloudflare, Let's Encrypt, DigiCert etc. — Cloudflare = WAF/proxy likely in front*

---

```bash
# Count how many unique subdomains exist
curl -s "https://crt.sh/?q=TARGET.com&output=json" | jq '[.[].name_value] | unique | length'

# Output
47
```

> [!info]+ Command Breakdown
> 1. **[.[].name_value]** — collects all name values into a new array
> 2. **unique** — deduplicates the array
> 3. **length** — returns the count
> 4. *Use this as a quick "how big is the attack surface" indicator before diving in*

---

> [!tip]+ curl Best Practices
> 1. Always use **-s** (silent) to suppress the progress bar — it pollutes piped output
> 2. Add **-A "Mozilla/5.0"** to spoof a browser User-Agent if a service rejects `curl` requests
> 3. Use **-o /dev/null -w "%{http_code}"** to test if a URL is reachable without dumping the body
> 4. Add **--max-time 10** to prevent curl hanging indefinitely on slow hosts

---

## dig — DNS Enumeration

> [!tip]+ Query Specific Record Types — Don't Always Use ANY
> Many resolvers block or ignore `dig any` queries. Query record types directly for reliable results:

```bash
# A records — IPv4 addresses
dig A TARGET.com +short

# AAAA records — IPv6 addresses
dig AAAA TARGET.com +short

# MX records — mail servers
dig MX TARGET.com +short

# NS records — name servers
dig NS TARGET.com +short

# TXT records — the intelligence goldmine
dig TXT TARGET.com +short

# SOA record — primary DNS authority
dig SOA TARGET.com +short

# CNAME — canonical name (reveals CDN, load balancer names)
dig CNAME www.TARGET.com +short
```

> [!info]+ Command Breakdown
> 1. **+short** — suppresses all header/footer output, returns only the answer — much cleaner than default output
> 2. Query each record type **separately** — `dig any` often returns incomplete or filtered results from modern resolvers
> 3. **CNAME records** are especially useful — they often reveal the CDN or load balancer in use (e.g., `target.cloudflare.net`, `target.azurefd.net`)
> 4. *MX pointing to Google = Google Workspace. MX pointing to outlook.com = Microsoft 365. Both have implications for cloud access.*

---

```bash
# Use a specific DNS resolver — bypass internal resolver caching
dig TXT TARGET.com @8.8.8.8 +short    # Google
dig TXT TARGET.com @1.1.1.1 +short    # Cloudflare
dig TXT TARGET.com @9.9.9.9 +short    # Quad9
```

> [!info]+ Command Breakdown
> 1. **@8.8.8.8** — directs the query to a specific resolver instead of your system's default
> 2. Use this when your local resolver returns stale/cached results or when testing from behind a corporate network
> 3. Comparing responses between resolvers can reveal **split-horizon DNS** — different answers for internal vs external queries
> 4. *Split-horizon DNS is a strong indicator of an internal network — note it for the Gateway layer*

---

```bash
# Attempt a zone transfer — almost always fails externally but worth trying
dig AXFR TARGET.com @ns.TARGET.com

# If it works, output dumps ALL DNS records at once:
; <<>> DiG 9.16.1-Ubuntu <<>> AXFR TARGET.com @ns.TARGET.com
TARGET.com.        3600    IN    SOA    ns1.TARGET.com. hostmaster.TARGET.com.
admin.TARGET.com.  3600    IN    A      10.10.10.5
dev.TARGET.com.    3600    IN    A      10.10.10.12
vpn.TARGET.com.    3600    IN    A      10.10.10.1
```

> [!info]+ Command Breakdown
> 1. **AXFR** — DNS zone transfer request; asks the name server to send ALL records for the zone
> 2. Requires knowing the authoritative NS server — get this from `dig NS TARGET.com +short` first
> 3. Modern DNS servers reject AXFR from untrusted IPs, but misconfigured or older servers may allow it
> 4. *A successful zone transfer is a critical finding — it immediately hands you the entire internal DNS map*

> [!warning]+ dig vs host vs nslookup
> | Tool | Best For | Avoid When |
> |---|---|---|
> | `dig` | Full record queries, scripting, verbose output | You just need a quick IP lookup |
> | `host` | Fast bulk lookups, simple A record resolution | You need specific record types or JSON output |
> | `nslookup` | Windows environments | Scripting — its output format is inconsistent |

---

## host — Bulk Subdomain Resolution

> [!tip]+ Going Further Than the Notes

```bash
# Reverse DNS lookup — IP to hostname
host 10.129.24.93
93.24.129.10.in-addr.arpa domain name pointer blog.TARGET.com.
```

> [!info]+ Command Breakdown
> 1. Pass an **IP address** to `host` instead of a hostname for reverse lookup
> 2. Reveals hostnames you may not have found in forward DNS enumeration
> 3. *Run this on every IP returned by Shodan — you may discover additional virtual hosts pointing to the same IP*

---

```bash
# Query a specific record type with host
host -t MX TARGET.com
host -t TXT TARGET.com
host -t NS TARGET.com
```

> [!info]+ Command Breakdown
> 1. **-t [TYPE]** — specifies the record type to query
> 2. Output is simpler than `dig` — useful for quick checks but less detail
> 3. *Use `dig` for full output with TTL and authority sections; use `host -t` for fast piped workflows*

---

```bash
# Better bulk resolution loop — saves both hostname and IP, skips failed lookups
while read subdomain; do
  result=$(host "$subdomain" 2>/dev/null | grep "has address" | awk '{print $1, $4}')
  [ -n "$result" ] && echo "$result"
done < subdomains.txt | tee resolved.txt

# Output
blog.TARGET.com 10.129.24.93
mail.TARGET.com 10.129.127.22
www.TARGET.com 10.129.127.33
```

> [!info]+ Command Breakdown
> 1. **while read subdomain** — cleaner than `for i in $(cat file)` — handles spaces in lines safely
> 2. **2>/dev/null** — suppresses error output for subdomains that don't resolve
> 3. **[ -n "$result" ]** — only prints if the result is non-empty (skips dead subdomains silently)
> 4. **tee resolved.txt** — prints to terminal AND saves to file simultaneously
> 5. *`resolved.txt` becomes your definitive list of live, company-hosted targets for active testing*

---

## Shodan — Passive IP and Service Intelligence

> [!important]+ Setup First — Easy to Skip
```bash
# Install the Shodan CLI
pip3 install shodan

# Initialise with your API key (free account works for basic queries)
shodan init YOUR_API_KEY_HERE

# Verify it works
shodan info
# Output:
# Query credits available: 100
# Scan credits available: 0
```

> [!info]+ Command Breakdown
> 1. **shodan init** — stores your API key locally so you don't have to pass it every command
> 2. Free accounts get 100 query credits — enough for a standard engagement's passive recon
> 3. *Get your API key at https://account.shodan.io/ — just needs a free registration*

---

```bash
# The basic host lookup from the notes
shodan host 10.129.24.93

# Better: search by organisation name — finds ALL IPs registered to the company
shodan search --fields ip_str,port,org,hostnames "org:\"InlaneFreight\""

# Output
10.129.24.93    80      InlaneFreight   blog.inlanefreight.com
10.129.27.33    443     InlaneFreight   www.inlanefreight.com
10.129.127.22   25      InlaneFreight   matomo.inlanefreight.com
```

> [!info]+ Command Breakdown
> 1. **"org:\"InlaneFreight\""** — Shodan search filter for organisation name; quotes inside the string are escaped
> 2. **--fields ip_str,port,org,hostnames** — limits output to only the useful columns
> 3. *This finds IPs you may have missed entirely in DNS enumeration — Shodan indexes based on what it scans, not what DNS says*

---

```bash
# Find all subdomains Shodan has seen for a domain
shodan search --fields ip_str,port,hostnames "hostname:TARGET.com"

# Find only SSL-enabled services — check for weak ciphers
shodan search "hostname:TARGET.com ssl.version:TLSv1"

# Find specific open ports across the org
shodan search "org:\"InlaneFreight\" port:22"
shodan search "org:\"InlaneFreight\" port:3389"   # RDP — always worth noting
shodan search "org:\"InlaneFreight\" port:445"    # SMB — goldmine

# Find services with default/vendor credentials (Shodan tags these)
shodan search "org:\"InlaneFreight\" has_screenshot:true"
```

> [!info]+ Command Breakdown
> 1. **hostname:TARGET.com** — finds all IPs where Shodan has observed the domain in the SSL cert or reverse DNS
> 2. **ssl.version:TLSv1** — filters for hosts still running deprecated TLS 1.0 — a vulnerability
> 3. **port:3389** / **port:445** — RDP and SMB exposed to the internet are high-priority findings
> 4. **has_screenshot:true** — Shodan captures screenshots of HTTP services — you can see login panels, admin interfaces, and dashboards without sending a single packet to the target

---

> [!tip]+ Shodan Filters Quick Reference

| Filter | Example | What It Finds |
|---|---|---|
| `org:` | `org:"Target Corp"` | All IPs registered to that organisation |
| `hostname:` | `hostname:target.com` | IPs with that hostname in cert/DNS |
| `port:` | `port:22` | Services on a specific port |
| `country:` | `country:GB` | Restrict by country |
| `ssl.version:` | `ssl.version:TLSv1` | Weak SSL/TLS versions |
| `product:` | `product:Apache` | Specific software |
| `os:` | `os:"Windows Server 2016"` | Specific OS versions |
| `has_screenshot:` | `has_screenshot:true` | Services with captured screenshots |
| `http.title:` | `http.title:"Login"` | Pages with specific HTML titles |

---

## Google Dorks — Cloud and File Discovery

> [!tip]+ Beyond the Basic inurl/intext Combo
> The notes cover `inurl:` and `intext:`. Here is the full operator toolkit:

```
# Find exposed files by type on the company's domain
site:TARGET.com filetype:pdf
site:TARGET.com filetype:xlsx
site:TARGET.com filetype:docx
site:TARGET.com filetype:env
site:TARGET.com filetype:sql
site:TARGET.com filetype:log
```

> [!info]+ Command Breakdown
> 1. **site:TARGET.com** — restricts ALL results to the specified domain and its subdomains
> 2. **filetype:** — filters by file extension — find documents, spreadsheets, SQL dumps, log files
> 3. `.env` files indexed by Google are an instant win — they almost always contain secrets
> 4. `.sql` files may contain database dumps with credentials and PII

---

```
# Find login panels and admin interfaces
site:TARGET.com intitle:"login"
site:TARGET.com intitle:"admin"
site:TARGET.com inurl:"/admin"
site:TARGET.com inurl:"/wp-admin"
site:TARGET.com inurl:"/phpmyadmin"
site:TARGET.com inurl:"/dashboard"
```

> [!info]+ Command Breakdown
> 1. **intitle:** — searches the HTML `<title>` tag of pages — login panels almost always say "Login" in their title
> 2. **inurl:** — searches the URL path — admin panels follow predictable URL patterns
> 3. *Combine `site:` with `intitle:` for targeted results with zero noise*

---

```
# Cloud storage discovery — go beyond the notes
intext:"TARGET" inurl:amazonaws.com
intext:"TARGET" inurl:blob.core.windows.net
intext:"TARGET" inurl:storage.googleapis.com
intext:"TARGET" inurl:s3.amazonaws.com
intext:"TARGET" inurl:digitaloceanspaces.com

# Find cached/old versions of pages
cache:TARGET.com/admin

# Find subdomains not in DNS — Google has indexed them
site:*.TARGET.com -site:www.TARGET.com
```

> [!info]+ Command Breakdown
> 1. **storage.googleapis.com** and **digitaloceanspaces.com** — additional cloud storage providers beyond AWS/Azure that are often forgotten
> 2. **cache:TARGET.com/page** — Google's cached version of a page — may show content from before a page was taken down or secured
> 3. **site:\*.TARGET.com -site:www.TARGET.com** — the `-` operator excludes a site; this surfaces all indexed subdomains except `www` — a fast way to discover what Google has crawled

---

> [!tip]+ Google Dork Pro Tips
> 1. Use **"quotes"** around exact phrases — `"internal use only"` finds documents accidentally published
> 2. Combine multiple operators: `site:TARGET.com filetype:pdf intitle:"confidential"` 
> 3. Use the **`-`** operator to subtract noise: `site:TARGET.com -site:blog.TARGET.com`
> 4. Google limits dork results — if you hit ~30 results, rephrase or use different operators for fresh results
> 5. **Never use Google Dorks logged into your Google account** during an engagement — your search history is tied to your identity

---

## GrayHatWarfare — Cloud Bucket Enumeration

> [!tip]+ Effective Search Strategy
> The notes say "search by company name" — here is a systematic approach:

```
Search terms to try (in order):
1. Full company name:        "InlaneFreight"
2. Common abbreviation:      "ILF"
3. Domain without TLD:       "inlanefreight"
4. Product/brand names:      [any product names found on the website]
5. Internal codenames:       [any codenames found in job postings or GitHub]
```

> [!info]+ File Types to Prioritise

| Priority | File Type | Why |
|---|---|---|
| **Critical** | `id_rsa`, `id_ecdsa`, `.pem`, `.ppk` | SSH/TLS private keys — direct access |
| **Critical** | `.env`, `*.env.production` | API keys, DB passwords, secrets |
| **High** | `config.json`, `settings.py`, `web.config` | Hardcoded credentials, internal IPs |
| **High** | `*.sql`, `*.db`, `*.sqlite` | Database dumps — credentials + data |
| **Medium** | `*.xlsx`, `*.csv` | May contain employee lists, IP lists, passwords |
| **Medium** | `*.pdf` | Internal documentation, network diagrams |
| **Low** | `*.log` | May contain tokens, paths, usernames in entries |

---

> [!warning]+ GrayHatWarfare Limitations
> 1. Only indexes **publicly accessible** buckets — password-protected or private buckets won't appear
> 2. Its index is not real-time — newly exposed buckets may take days to appear
> 3. Files listed may have since been removed — always verify before reporting
> 4. **Do NOT download files without explicit written scope permission** — accessing unauthenticated cloud storage may still carry legal risk depending on jurisdiction

---

## domain.glass — Quick Infrastructure Snapshot

> [!tip]+ What to Actually Look At
> The notes mention it exists. Here is what to focus on when you open it:

```
URL: https://domain.glass/TARGET.com
```

> [!info]+ Sections That Matter

| Section | What to Extract |
|---|---|
| **IP Information** | Hosting provider, ASN, IP range — tells you who hosts the infrastructure |
| **SSL Certificate** | Issuer (Cloudflare? Let's Encrypt? Internal CA?) and listed SANs (extra subdomains) |
| **Cloudflare Status** | "Safe" = Cloudflare is proxying — real IP is hidden; direct IP scanning will hit Cloudflare, not the origin |
| **DNS Records** | Cross-reference against your `dig` output — domain.glass sometimes catches records `dig any` misses |
| **Social Media Links** | Auto-detected official accounts — cross-reference with your LinkedIn/staff OSINT |

> [!warning]+ Cloudflare Proxy Implication
> 1. If domain.glass shows Cloudflare as "Safe" — the A record IP is a **Cloudflare IP, not the origin server**
> 2. Active scanning against that IP hits Cloudflare's infrastructure — not the target
> 3. Find the real IP via: historical DNS records (SecurityTrails), SSL cert transparency, Shodan `ssl.cert.subject.cn:TARGET.com`, or email headers (MX trace)

---

## LinkedIn — Staff and Tech Stack OSINT

> [!tip]+ Search Syntax That Actually Works
> LinkedIn's search is intentionally limited for free accounts. Here is how to work around it:

```
# Use Google to search LinkedIn profiles — more powerful than LinkedIn's own search
site:linkedin.com/in "TARGET company name" "software engineer"
site:linkedin.com/in "TARGET company name" "security engineer"
site:linkedin.com/in "TARGET company name" "devops"
site:linkedin.com/in "TARGET company name" "sysadmin"
site:linkedin.com/in "TARGET company name" "AWS" OR "Azure" OR "GCP"
```

> [!info]+ Command Breakdown
> 1. **site:linkedin.com/in** — restricts Google results to LinkedIn profile pages only
> 2. Combine the company name with job titles to surface the most relevant staff
> 3. Add technology keywords (`"AWS"`, `"Kubernetes"`, `"Splunk"`) to find staff who list those skills
> 4. *Google's index of LinkedIn is deeper than LinkedIn's own search — especially useful without a Premium account*

---

> [!tip]+ What to Record from Each Profile

| Profile Section | What to Note |
|---|---|
| **Current Role + Company** | Confirms employment — verify you have the right person |
| **Tech Stack in "About"** | Programming languages, cloud platforms, tools in active use |
| **GitHub / Portfolio Links** | Jump to code search immediately — these are the highest-value leads |
| **Career History** | Technologies used at each role — older systems may still be in use |
| **Certifications** | AWS/Azure certified = likely manages cloud; OSCP/CEH = security awareness is higher |
| **Followed Companies** | May indicate vendors they use or are evaluating |
| **Activity / Posts** | Recent posts about specific tools = those tools are in active use RIGHT NOW |

---

> [!tip]+ Priority Targets on LinkedIn
> 1. **IT/Infrastructure admins** — they configure the systems you're targeting
> 2. **DevOps / SRE engineers** — they wrote the pipelines that deploy to cloud
> 3. **Security engineers** — their skills tell you what defences exist (SIEM? EDR? WAF?)
> 4. **Former employees** — may have older, potentially still-valid credentials; less cautious about what they share post-employment
> 5. **Junior developers** — more likely to have public GitHub repos with company-adjacent code

---

## GitHub — Code and Secret Hunting

> [!tip]+ GitHub Search Syntax Goes Far Beyond the Notes
> Most recon stops at "browse the repo". GitHub has a powerful search API:

```
# Search for company name in ALL public code
org:TARGET-org-name                          # All repos under a specific GitHub org
user:firstname-lastname TARGET               # Repos by a specific employee mentioning the company

# Search for secrets by filename
filename:.env TARGET
filename:config.py password
filename:settings.py SECRET_KEY
filename:application.properties datasource

# Search for secrets by content
"TARGET.com" password
"TARGET.com" api_key
"TARGET.com" BEGIN RSA PRIVATE KEY
"TARGET.com" token

# Search for internal infrastructure hints
"TARGET.com" internal
"TARGET.com" 192.168.
"TARGET.com" 10.0.
"TARGET.com" staging
"TARGET.com" production
```

> [!info]+ Command Breakdown
> 1. **org:** — restricts search to all repositories under a GitHub organisation (the company may have an official org)
> 2. **filename:** — searches ONLY in files with that specific name — highly targeted for common secret files
> 3. **"BEGIN RSA PRIVATE KEY"** — literal string that starts every RSA private key — if this appears in a repo, it's a critical finding
> 4. Internal IP ranges (`192.168.`, `10.0.`) in public repos reveal internal network addressing

---

```bash
# Check commit history for deleted secrets — CLI approach
git clone https://github.com/target-org/repo-name
cd repo-name

# Search ALL commits for the word "password"
git log --all -p | grep -i "password" | head -50

# Search for a specific string across all branches and commits
git log --all --oneline | awk '{print $1}' | xargs -I{} git grep -l "SECRET_KEY" {}
```

> [!info]+ Command Breakdown
> 1. **git log --all -p** — shows every commit across all branches WITH the full diff (added/removed lines)
> 2. **grep -i "password"** — case-insensitive search through all commit diffs
> 3. Even if a secret was removed in a later commit, `git log -p` shows the line prefixed with `+` (added) and `-` (removed) — deleted secrets are still readable in the diff
> 4. *This is how most credential leaks persist — the file is "cleaned up" but the history is never purged*

---

> [!tip]+ Automated Secret Scanning Tools (Beyond Manual Search)

| Tool | Command | What It Does |
|---|---|---|
| [trufflehog](https://github.com/trufflesecurity/trufflehog) | `trufflehog github --org=TARGET-org` | Scans all org repos + full history for 700+ secret patterns |
| [gitleaks](https://github.com/gitleaks/gitleaks) | `gitleaks detect --source=./repo` | Scans local repo for secrets using regex rules |
| [gitrob](https://github.com/michenriksen/gitrob) | `gitrob TARGET-org` | Maps org members' repos and scans for sensitive files |

> [!warning]+ GitHub OSINT Rules
> 1. Only search **public** repositories — accessing private repos without authorisation is illegal
> 2. **Do not clone or download** any repo that isn't clearly in scope — downloading may constitute unauthorised access in some jurisdictions
> 3. GitHub may rate-limit unauthenticated searches — authenticate with a **throwaway account** if needed, never your real account
> 4. Findings from GitHub (leaked keys, hardcoded passwords) must be **reported immediately** in real engagements — they are often actively exploitable

---

## References

1. [HTB Academy - Footprinting Module](https://academy.hackthebox.com/module/details/112)
2. [crt.sh - Certificate Transparency](https://crt.sh/)
3. [Shodan CLI Documentation](https://cli.shodan.io/)
4. [Shodan Search Filters Reference](https://www.shodan.io/search/filters)
5. [dig Man Page](https://linux.die.net/man/1/dig)
6. [jq Manual](https://stedolan.github.io/jq/manual/)
7. [Google Advanced Search Operators](https://support.google.com/websearch/answer/2466433)
8. [GrayHatWarfare](https://buckets.grayhatwarfare.com/)
9. [domain.glass](https://domain.glass/)
10. [TruffleHog - Secret Scanner](https://github.com/trufflesecurity/trufflehog)
11. [Gitleaks](https://github.com/gitleaks/gitleaks)
12. [HackTricks - DNS Enumeration](https://book.hacktricks.xyz/network-services-pentesting/pentesting-dns)
13. [HackTricks - External Recon Methodology](https://book.hacktricks.xyz/generic-methodologies-and-resources/external-recon-methodology)
14. [MITRE ATT&CK - Search Open Technical Databases (T1596)](https://attack.mitre.org/techniques/T1596/)
15. [MITRE ATT&CK - Search Open Websites/Domains (T1593)](https://attack.mitre.org/techniques/T1593/)

---

#HTB #Footprinting #OSINT #Cheatsheet #DNS #Shodan #GoogleDorking #CertificateTransparency #GrayHatWarfare #GitHub #LinkedIn #SubdomainEnumeration #CloudStorage #PassiveRecon
