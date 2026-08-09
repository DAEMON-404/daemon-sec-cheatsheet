---
title: "Phishing Identification"
description: "Identify phishing sites and malicious links: URL/domain analysis, indicators and triage workflow."
category: web
tags: [web, phishing, osint, defense]
tools: [urlscan, VirusTotal]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:Web/Phishing Site & Link Identification - Cheat Sheet.md"
---

# Phishing Identification

### Defensive triage for suspicious URLs, domains and landing pages

Covers: URL anatomy, lookalike domains, punycode/IDN, redirect chains, header and SPF/DKIM/DMARC checks, WHOIS and DNS, certificate transparency, safe fetching and detonation.

---

## Golden Rules

> **Warning — Handle every unverified URL as live malware.**
> - Never open a suspicious link in your daily-driver browser or on a host with credentials on it. Use a disposable VM, and route through a network you do not mind burning.
> - Fetching a URL leaks your IP and often a unique token embedded in the link, which confirms to the operator that the target is live. Prefer passive lookups first.
> - Judge the registrable domain, never the display text, the path, the favicon or the branding.
> - HTTPS and a padlock prove nothing. Free DV certificates mean the overwhelming majority of phishing sites are served over TLS.
> - If a page asks for credentials, MFA codes or a card number, navigate to the service yourself from a known-good bookmark instead.

---

## 1. URL Anatomy — Where to Actually Look

```text
https://accounts.google.com.verify-login.ru:8443/signin?token=abc#/
└─┬─┘   └──────────────┬──────────────────────┘└─┬┘└──┬─┘└───┬───┘
scheme          host (read RIGHT to LEFT)      port path   query
```

The only part that matters for identity is the registrable domain, the last two labels before the public suffix. Read the host from right to left, stopping at the first `/`.

| URL | Registrable domain | Verdict |
|---|---|---|
| `https://accounts.google.com/signin` | `google.com` | Legitimate |
| `https://accounts.google.com.verify-login.ru/` | `verify-login.ru` | Phish — brand is a subdomain |
| `https://google.com.evil.co/` | `evil.co` | Phish |
| `https://secure-google.com/` | `secure-google.com` | Phish — hyphenated lookalike |
| `https://google.com@evil.co/` | `evil.co` | Phish — everything before `@` is userinfo |
| `https://sites.google.com/view/login-x` | `google.com` | Legitimate host, abused hosting |

Extract the host programmatically rather than trusting your eyes:

```bash
# Pull scheme, host, path out of a URL without fetching it
print -r 'https://accounts.google.com.verify-login.ru/signin' | \
  python3 -c 'import sys,urllib.parse as u; p=u.urlparse(sys.stdin.read().strip()); print("host:",p.hostname,"\nport:",p.port,"\npath:",p.path,"\nuser:",p.username)'
```

```bash
# Registrable domain (eTLD+1) using the public suffix list
uv venv .venv && source .venv/bin/activate
uv pip install tldextract
python3 -c 'import tldextract,sys; e=tldextract.extract(sys.argv[1]); print(e.registered_domain)' \
  'https://accounts.google.com.verify-login.ru/signin'
```

> **Tip — Common obfuscations**
> - `@` userinfo trick: browser goes to whatever follows the `@`.
> - Decimal, octal or hex IPs: `http://2130706433/` is `127.0.0.1`.
> - Percent-encoding of the host or path to hide keywords.
> - Very long paths padding the real domain off the end of a mobile URL bar.
> - Data URIs and `blob:` URLs rendering a login form with no remote host at all.

---

## 2. Domain Red Flags

| Signal | Why it matters | How to check |
|---|---|---|
| Registered in the last 30 days | Phishing infra is disposable and short-lived | `whois` creation date |
| Brand name as a subdomain or in the path | Legitimate brands own their apex | Read host right to left |
| Hyphenated brand combos (`paypal-secure-login`) | Cheap way to look plausible | Visual |
| Unusual TLD for the brand (`.zip`, `.mov`, `.top`, `.cf`, `.xyz`) | Cheap or free registration | Visual |
| Free hosting or dev platform subdomains | Abused for zero-cost hosting with valid TLS | Check apex against known SaaS |
| Privacy-shielded WHOIS on a "corporate" login page | Real brands do not hide registrant data | `whois` |
| Wildcard DNS answering every subdomain | Per-victim subdomains | `dig random.$domain` |
| Hosting ASN mismatched with the brand | Bulletproof or cheap VPS ranges | `whois <ip>` |
| Open directory listing or `/.git` exposed | Sloppy kit deployment | Manual, in a VM |

Legitimate-but-abused hosting worth recognising: `*.web.app`, `*.firebaseapp.com`, `*.pages.dev`, `*.workers.dev`, `*.r2.dev`, `*.blob.core.windows.net`, `*.s3.amazonaws.com`, `*.weeblysite.com`, `*.glitch.me`, `sites.google.com/view/...`, `*.notion.site`, IPFS gateways. The apex is genuine, so reputation feeds often miss them.

---

## 3. Homoglyph & Punycode Detection

Internationalised domains let attackers register visually identical names. Browsers show punycode as `xn--` only in some cases, so decode explicitly.

```bash
# Decode punycode to the real Unicode label
python3 -c 'print("xn--80ak6aa92e".encode().decode("idna"))'      # -> аррӏе (Cyrillic)

# Encode a suspect Unicode host to see its punycode form
python3 -c 'print("аррӏе.com".encode("idna").decode())'
```

```bash
# Flag any non-ASCII characters in a host, and name the script of each
python3 - <<'PY'
import unicodedata
host = "аррӏе.com"
for ch in host:
    if ord(ch) > 127:
        print(f"{ch!r} U+{ord(ch):04X} {unicodedata.name(ch)}")
PY
```

Mixed-script hosts (Latin plus Cyrillic or Greek in one label) are almost always hostile. Classic swaps to watch for:

| Looks like | Actually | Codepoint |
|---|---|---|
| `a` | Cyrillic а | U+0430 |
| `e` | Cyrillic е | U+0435 |
| `o` | Cyrillic о | U+043E |
| `p` | Cyrillic р | U+0440 |
| `i` / `l` | Cyrillic ӏ, Turkish ı | U+04CF, U+0131 |
| `rn` | reads as `m` at small sizes | ASCII only |
| `vv` | reads as `w` | ASCII only |
| `1` / `l` / `I` | font-dependent confusion | ASCII only |

Generate and check typosquats around a brand you protect:

```bash
# dnstwist enumerates permutations and resolves the live ones
uv pip install dnstwist
dnstwist --registered --mx --format cli example.com
```

---

## 4. Unwrapping Redirects & Shorteners

Resolve the chain without executing anything. Prefer `HEAD` and never follow blindly into a download.

```bash
# Show every hop, headers only, no body, no auto-follow of unsafe schemes
curl -sIL --max-redirs 10 --max-time 15 -A 'Mozilla/5.0' 'https://short.link/abc' \
  | grep -Ei '^(HTTP/|location:)'
```

```bash
# One hop at a time, so you can bail out
curl -sI 'https://short.link/abc' | grep -i '^location:'
```

Many shorteners expose a preview or API that avoids touching attacker infra at all:

| Service | Preview method |
|---|---|
| bit.ly | append `+` to the URL |
| tinyurl.com | `https://preview.tinyurl.com/<code>` |
| ow.ly, buff.ly | Bitly-family, `+` often works |
| t.co | `curl -sI` returns `location` without rendering |

Unwrap corporate link-rewriting so you see the real destination:

```bash
# Proofpoint URLDefense v3, Microsoft Safe Links, Barracuda etc. all URL-encode the original
python3 -c 'import sys,urllib.parse as u; q=u.parse_qs(u.urlparse(sys.argv[1]).query); print(q.get("url",[""])[0])' \
  'https://eur01.safelinks.protection.outlook.com/?url=https%3A%2F%2Fevil.co%2Flogin&data=...'
```

> **Warning —** Every link in a phish is usually unique per recipient. Fetching it tells the operator your address is live and may burn the sample before analysis.

---

## 5. Email Header & Auth Triage

Get the original headers, not a forward. In Gmail use "Show original", in Outlook "View source", and save the `.eml` intact.

What to read, in order:

1. `From:` display name versus the actual address in angle brackets.
2. `Return-Path:` / envelope sender. A mismatch with `From:` is normal for mailing lists but suspicious for a bank.
3. `Reply-To:` pointing somewhere unrelated is a strong lure signal.
4. `Authentication-Results:` for SPF, DKIM and DMARC verdicts.
5. Earliest `Received:` hop, which shows the true origin before the receiving infra.
6. `Message-ID` domain matching the sending domain.

```bash
# Pull the auth verdicts and the sender fields out of a saved .eml
grep -Ei '^(authentication-results|received-spf|dkim-signature|from|reply-to|return-path|message-id):' sample.eml
```

```bash
# Parse an .eml properly, including nested parts and URLs in the body
python3 - <<'PY'
import email, re
from email import policy
m = email.message_from_file(open("sample.eml"), policy=policy.default)
for h in ("From","Reply-To","Return-Path","Subject","Date","Authentication-Results","Message-ID"):
    print(f"{h}: {m.get(h)}")
body = "".join(p.get_content() for p in m.walk() if p.get_content_type() in ("text/plain","text/html"))
for url in sorted(set(re.findall(r'https?://[^\s"\'<>)]+', body))):
    print("URL:", url)
PY
```

Interpreting the verdicts:

| Result | Meaning | Weight |
|---|---|---|
| `spf=fail` + `dkim=fail` + `dmarc=fail` | Spoofed sending domain | Strong |
| `spf=pass` on an attacker-owned lookalike domain | Auth passes for *their* domain, proves nothing about the brand | Neutral, common |
| `dkim=pass` with `d=` not matching the `From:` domain | Unaligned DKIM, DMARC will not pass on it | Suspicious |
| `dmarc=pass` | Aligned and authenticated for the `From:` domain | Reassuring, not conclusive if the account is compromised |

```bash
# Check what the claimed domain publishes
dig +short TXT example.com | grep -i spf
dig +short TXT _dmarc.example.com
dig +short TXT selector1._domainkey.example.com
```

> **Note —** Business email compromise sends from a genuinely owned, fully authenticated mailbox. Auth passing is not innocence. Weight the request itself: payment redirection, urgency, secrecy, out-of-band contact.

---

## 6. WHOIS & DNS Checks

```bash
# Registration age is the single highest-signal indicator
whois evil-login.co | grep -Ei 'creation|created|registered|registrar|registrant|name server'
```

```bash
# Resolution and infrastructure
dig +short A evil-login.co
dig +short NS evil-login.co
dig +short MX evil-login.co          # MX present = capable of receiving replies
dig +short TXT evil-login.co

# Wildcard test: does a random subdomain resolve? Per-victim subdomains are a kit tell
dig +short "$(openssl rand -hex 6).evil-login.co"

# Who owns the hosting
whois "$(dig +short A evil-login.co | head -1)" | grep -Ei 'orgname|netname|country|origin'
```

```text
# Passive DNS style pivot: what else is on that IP (use a service, do not scan)
# See section 11 for tooling. Shared cheap hosting will show hundreds of unrelated domains.
```

Age heuristic worth internalising: a "Microsoft account security" page on a domain created 4 days ago with a privacy-shielded registrant and a Let's Encrypt certificate issued the same day is phishing until proven otherwise.

---

## 7. TLS Certificate & CT Logs

```bash
# Inspect the presented certificate without loading the page
echo | openssl s_client -connect evil-login.co:443 -servername evil-login.co 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

What to read:

| Field | Phishing tell |
|---|---|
| `notBefore` | Issued hours or days ago |
| Issuer | Free DV CA on a page impersonating a bank |
| Subject | `CN` is the lookalike domain, no organisation details |
| SAN list | Dozens of unrelated brand-ish hostnames on one cert |

Certificate Transparency is a free, passive early-warning source for lookalikes of a domain you own:

```bash
# All certs ever issued for a domain and its subdomains, from CT logs
curl -s 'https://crt.sh/?q=%25.example.com&output=json' \
  | python3 -c 'import sys,json; [print(r["name_value"].replace("\n",","), r["not_before"]) for r in json.load(sys.stdin)]' \
  | sort -u | head -50
```

Search CT for brand permutations (`example-secure`, `examp1e`, `example-login`) to catch infrastructure before the campaign launches.

---

## 8. Safe Fetching of Page Content

Passive first. If you must fetch, do it from an isolated VM or a cloud sandbox, never your host.

```bash
# Headers only, no body executed, short timeout, no cookies stored
curl -sI --max-time 10 -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' 'https://evil-login.co/'
```

```bash
# Fetch the raw HTML to a file for offline inspection, do not open it in a browser
curl -s --max-time 15 -A 'Mozilla/5.0' 'https://evil-login.co/' -o page.html
file page.html && wc -c page.html
```

```bash
# Extract form targets, external scripts and iframes from the saved HTML
python3 - <<'PY'
import re
h = open("page.html", encoding="utf-8", errors="replace").read()
for label, pat in [("FORM ACTION", r'<form[^>]*action=["\']([^"\']+)'),
                   ("SCRIPT SRC",  r'<script[^>]*src=["\']([^"\']+)'),
                   ("IFRAME SRC",  r'<iframe[^>]*src=["\']([^"\']+)'),
                   ("INPUT NAME",  r'<input[^>]*name=["\']([^"\']+)')]:
    for m in sorted(set(re.findall(pat, h, re.I))):
        print(f"{label}: {m}")
PY
```

> **Tip —** The form `action` is the payoff. A login page whose form posts to an unrelated domain, a raw IP, a `.php` on cheap hosting, or a Telegram bot API endpoint is conclusive.

Server-side cloaking is standard, so a plain `curl` often returns a benign decoy. Attacker kits filter on User-Agent, `Referer`, geolocation, ASN (blocking known security vendors) and sometimes require the unique token from the original link. Getting a harmless page back does not clear the URL.

---

## 9. Landing Page Tells

Observed in an isolated VM, or from saved HTML.

- Form posts to a different domain than the one in the address bar.
- Credentials submitted, then a redirect to the real site's genuine login page, so the victim assumes a mistyped password.
- Password field with autocomplete disabled and no "forgot password" or account-creation flow that actually works.
- Requests for data the real service would never ask for together: password plus MFA code plus card number plus mother's maiden name.
- MFA relay kits (Evilginx, EvilProxy, Tycoon) proxy the real site live, so the page is pixel-perfect and the TLS is valid. The domain is your only reliable tell.
- Right-click, view-source or devtools disabled via JavaScript.
- Blocked or broken links for everything except the login form.
- Base64 or heavily obfuscated inline JavaScript that assembles the form at runtime.
- The brand logo hotlinked from the genuine CDN while everything else is local.
- Fake browser chrome drawn in HTML, a "browser in the browser" popup simulating an OAuth window. Try to drag it outside the page, a real window can leave, a fake one cannot.
- QR codes in the email body ("quishing") to move the click onto an unmanaged mobile device. Decode offline before scanning:

```bash
uv pip install "qreader" opencv-python-headless
python3 -c 'import cv2; d=cv2.QRCodeDetector(); print(d.detectAndDecode(cv2.imread("qr.png"))[0])'
# or
zbarimg --quiet --raw qr.png
```

---

## 10. Attachment Triage

Static inspection only, in a VM, never double-click.

```bash
file suspicious.*
sha256sum suspicious.*                 # hash first, then look it up rather than uploading
```

```bash
# Office documents: check for macros and embedded objects
uv pip install oletools
olevba -a suspicious.docm
oleid suspicious.doc
```

```bash
# PDFs: look for JavaScript, auto-actions and embedded launches
uv pip install pdfid pdf-parser
pdfid.py suspicious.pdf                # /JS /JavaScript /OpenAction /Launch /EmbeddedFile counts
```

```bash
# Archives: list contents without extracting, watch for double extensions and LNK/ISO/IMG
unzip -l suspicious.zip
7z l suspicious.iso
```

High-risk containers used to defeat mark-of-the-web: `.iso`, `.img`, `.vhd`, `.7z`, password-protected `.zip` with the password in the email body, `.lnk`, `.chm`, `.one`, `.svg` with embedded script, `.html` smuggling attachments that rebuild a payload client-side.

> **Warning —** Hash first and search the hash. Uploading a targeted sample to a public multi-scanner makes it public and tips off the operator.

---

## 11. Reputation & Sandbox Services

| Service | Use | Notes |
|---|---|---|
| urlscan.io | Renders a URL, screenshots, DOM, request chain | Set scan to private for targeted phish. Public scans are searchable by anyone, including the attacker |
| VirusTotal | URL, domain, IP and file reputation | Search by hash before uploading. Uploads are shared with vendors |
| Hybrid Analysis / Joe Sandbox / ANY.RUN | Full detonation | Free tiers make results public |
| crt.sh | Certificate transparency search | Passive, free, no attacker contact |
| Shodan / Censys | Host and cert fingerprinting, pivot on kit artefacts | Passive |
| PhishTank / OpenPhish | Community phish feeds | Good for known campaigns, weak on fresh ones |
| Google Safe Browsing / Microsoft Defender SmartScreen | Browser-level blocklists | Lag of hours to days on new infra |
| Have I Been Pwned | Assess exposure after a credential submission | Post-incident |

Absence of detections means nothing on a domain registered this morning. Reputation feeds are lagging indicators. Registration age plus form target plus domain reading beat any single verdict.

---

## 12. Triage Workflow

```text
1. PRESERVE      Save the original .eml and the raw URL. Do not click anything.
2. PARSE         Extract host, registrable domain, and every URL in the body.
3. READ DOMAIN   Right to left. Decode punycode. Check for mixed scripts.
4. AGE IT        whois creation date. Under ~30 days is a strong signal on its own.
5. AUTH          SPF / DKIM / DMARC alignment against the claimed From: domain.
6. INFRA         dig A/NS/MX, ASN owner, wildcard test, cert notBefore and issuer.
7. REPUTATION    Hash and domain lookups. Passive sources first.
8. UNWRAP        Resolve redirect chain with curl -sIL from an isolated host.
9. DETONATE      Only if needed, in a VM or private urlscan. Note cloaking.
10. VERDICT      Weight registration age + form target + domain reading above all else.
11. RESPOND      Report, block, hunt for other recipients, rotate any exposed credentials.
```

If a credential was submitted, treat it as compromised immediately: change the password from a different device, revoke active sessions and refresh tokens (MFA relay kits steal the session cookie, so a password change alone is insufficient), re-enrol MFA, and check mailbox rules and OAuth app grants for attacker persistence.

---

## 13. Quick Reference Table

| Check | Command |
|---|---|
| Extract host from URL | `python3 -c 'import sys,urllib.parse as u;print(u.urlparse(sys.argv[1]).hostname)' "$URL"` |
| Registrable domain | `python3 -c 'import tldextract,sys;print(tldextract.extract(sys.argv[1]).registered_domain)' "$URL"` |
| Decode punycode | `python3 -c 'print("xn--...".encode().decode("idna"))'` |
| Redirect chain | `curl -sIL --max-redirs 10 "$URL" \| grep -Ei '^(HTTP/\|location:)'` |
| Domain age | `whois "$DOM" \| grep -Ei 'creation\|created'` |
| DNS records | `dig +short A "$DOM"; dig +short NS "$DOM"; dig +short MX "$DOM"` |
| Wildcard DNS test | `dig +short "$(openssl rand -hex 6).$DOM"` |
| Hosting owner | `whois "$(dig +short A "$DOM" \| head -1)" \| grep -Ei 'orgname\|netname'` |
| Cert details | `echo \| openssl s_client -connect "$DOM":443 -servername "$DOM" 2>/dev/null \| openssl x509 -noout -subject -issuer -dates` |
| CT log history | `curl -s "https://crt.sh/?q=%25.$DOM&output=json" \| jq -r '.[].name_value' \| sort -u` |
| SPF / DMARC published | `dig +short TXT "$DOM" \| grep -i spf; dig +short TXT "_dmarc.$DOM"` |
| Email auth verdicts | `grep -Ei '^(authentication-results\|received-spf\|from\|reply-to\|return-path):' sample.eml` |
| Save page HTML | `curl -s --max-time 15 -A 'Mozilla/5.0' "$URL" -o page.html` |
| Form targets | `grep -oEi '<form[^>]*action="[^"]+"' page.html` |
| Typosquat sweep | `dnstwist --registered --mx example.com` |
| File type + hash | `file f; sha256sum f` |
| Macro check | `olevba -a f.docm` |
| PDF actions | `pdfid.py f.pdf` |
| Decode QR | `zbarimg --quiet --raw qr.png` |

---

## 14. Reporting & Takedown

| Where | How |
|---|---|
| UK, general public | Forward the email to `report@phishing.gov.uk` (NCSC SERS). Suspicious texts to `7726` |
| UK, financial loss | Action Fraud, `actionfraud.police.uk` or 0300 123 2040. In Scotland, report to Police Scotland on 101 |
| Google Safe Browsing | `safebrowsing.google.com/safebrowsing/report_phish/` |
| Microsoft | `microsoft.com/wdsi/support/report-unsafe-site`, or the Report Phishing add-in |
| APWG | `reportphishing@apwg.org` |
| Hosting provider | `abuse@` for the ASN owner found via `whois <ip>` |
| Registrar | Abuse contact from `whois <domain>` |
| CDN in front of the site | Cloudflare and similar have their own abuse forms, they will pass to origin |
| Impersonated brand | Most banks and large SaaS publish a phishing reporting address |

Include the full URL, the original headers, timestamps with timezone, and the file hashes. Do not include live credentials.

---

## External References

- [NCSC — Phishing attacks: defending your organisation](https://www.ncsc.gov.uk/guidance/phishing)
- [RFC 7489 — DMARC](https://datatracker.ietf.org/doc/html/rfc7489)
- [Public Suffix List](https://publicsuffix.org/)
- [crt.sh — Certificate Transparency search](https://crt.sh/)
- [urlscan.io](https://urlscan.io/)
- [dnstwist](https://github.com/elceef/dnstwist)
- [oletools](https://github.com/decalage2/oletools)
