---
title: "2.4 - Cheatsheet - Gitleaks"
description: "brew install gitleaks"
category: enumeration
tags: ["enumeration"]
tools: ["Gitleaks"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Enumeration/GitHub-Enum/2.4 - Cheatsheet - Gitleaks.md"
---
# macOS — Homebrew
brew install gitleaks

# Linux — direct binary download (always check latest release)
wget https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_8.30.1_linux_x64.tar.gz
tar -xzf gitleaks_8.30.1_linux_x64.tar.gz
mv gitleaks /usr/local/bin/

# Verify install
gitleaks version
# Output:
# v8.30.1
```

> [!info]+ Command Breakdown
> 1. Gitleaks ships as a **single static binary** — no dependencies, no runtime needed
> 2. Always check the [releases page](https://github.com/gitleaks/gitleaks/releases) for the latest version before downloading
> 3. **v8.19.0+** deprecated `detect` and `protect` — replaced by `git`, `dir`, and `stdin` subcommands

---

## Subcommands at a Glance

| Subcommand | What It Scans | Typical Use Case |
|---|---|---|
| `git` | Git repository — full commit history | Cloned public repos, any local git repo |
| `dir` | Directories and individual files | Non-git folders, downloaded archives, local files |
| `stdin` | Piped data stream | Scanning output of another command, log files |
| `version` | N/A | Verify installed version |

> [!warning]+ v8.19.0 Command Change
> 1. `gitleaks detect` → replaced by `gitleaks git`
> 2. `gitleaks protect` → replaced by `gitleaks git --pre-commit` / `gitleaks git --staged`
> 3. The old commands still work but are **hidden from `--help`** — don't rely on them in scripts

---

## Core Scan Commands

### Scan a Cloned Repo (Most Common — OSINT Use)

```bash
# Clone the target repo first
git clone https://github.com/target-org/target-repo.git
cd target-repo

# Scan the full git history — verbose output
gitleaks git -v .

# Output example:
# ○
#     ○
#         ○
# ○       ○
#     ○
#
# Finding:     AWS Access Key detected
# Secret:      AKIAIOSFODNN7EXAMPLE
# RuleID:      aws-access-key-id
# Entropy:     3.88
# File:        config/aws.py
# Line:        12
# Commit:      a3f2c1d9e8b74561...
# Author:      dev@target.com
# Date:        2023-04-18T14:22:01Z
# Fingerprint: a3f2c1d9:config/aws.py:aws-access-key-id:12
```

> [!info]+ Command Breakdown
> 1. **git** — subcommand that scans using `git log -p` under the hood — reads every commit diff
> 2. **-v** — verbose mode; prints each finding as it is discovered in real time
> 3. **.** — target path; current directory (must be a git repo); can be an absolute path to any git repo
> 4. **Finding** — the rule that matched
> 5. **Secret** — the actual leaked value (may be redacted with `--redact`)
> 6. **RuleID** — the specific detection rule that triggered (useful for filtering false positives)
> 7. **Entropy** — Shannon entropy score of the matched string — higher = more likely to be a real secret
> 8. **Commit** — the exact commit hash where the secret exists or existed
> 9. **Fingerprint** — unique identifier for this finding — used in `.gitleaksignore` to suppress it

---

```bash
# Scan a remote repo without cloning manually
gitleaks git -v https://github.com/target-org/target-repo.git
```

> [!info]+ Command Breakdown
> 1. Gitleaks can accept a **remote URL** directly — it clones to a temp directory, scans, then cleans up
> 2. Faster than manual clone for quick checks — but no persistent copy of the repo
> 3. *For offensive recon, clone manually first so you can inspect files directly after gitleaks surfaces findings*

---

### Scan a Specific Commit Range

```bash
# Scan only the last 50 commits
gitleaks git -v --log-opts="-n 50" .

# Scan between two specific commits
gitleaks git -v --log-opts="commitA..commitB" .

# Scan all branches (not just current branch)
gitleaks git -v --log-opts="--all" .

# Scan commits since a specific date
gitleaks git -v --log-opts="--since=2024-01-01" .

# Combine — all branches, last 1000 commits
gitleaks git -v --log-opts="--all -n 1000" .
```

> [!info]+ Command Breakdown
> 1. **--log-opts** — passes options directly to `git log -p` — accepts any valid `git log` flag
> 2. **-n 50** — limits to the last 50 commits — useful for CI pipelines or quick checks
> 3. **commitA..commitB** — scans only commits between two hashes — useful for PR/MR scanning
> 4. **--all** — scans ALL branches and tags, not just the checked-out branch — critical for OSINT; devs often push secrets to feature branches they forget about
> 5. **--since=** — date filter; ISO format (`2024-01-01`) or relative (`6months`)

> [!tip]+ OSINT Best Practice
> 1. Always run with **--log-opts="--all"** first — the current branch is rarely where secrets live
> 2. Feature branches, hotfix branches, and old release branches are where rushed, careless commits accumulate
> 3. Combine **--all** with **-n 1000** to catch the breadth without waiting on repos with 10,000+ commits

---

### Scan a Directory (No Git Required)

```bash
# Scan a directory of downloaded files
gitleaks dir -v /path/to/downloaded/files/

# Scan a single file
gitleaks dir -v /path/to/suspicious/file.env

# Scan current directory
gitleaks dir -v .

# Scan and include archives (zip, tar.gz, etc.) — disabled by default
gitleaks dir -v --max-archive-depth=3 /path/to/directory/
```

> [!info]+ Command Breakdown
> 1. **dir** — scans the filesystem directly; no git history, no `git log` — just raw file contents
> 2. Useful when you have downloaded files, extracted archives, or scraped content that isn't a git repo
> 3. **--max-archive-depth=3** — tells gitleaks to open and scan inside `.zip`, `.tar.gz`, `.tar`, `.7z`, etc., up to 3 levels deep; default is 0 (disabled)
> 4. *Archive scanning is critical for buckets and file shares — secrets are often in zip archives employees assumed were "safe"*

---

### Scan via stdin (Piped Input)

```bash
# Scan a file piped through stdin
cat suspicious_config.py | gitleaks -v stdin

# Scan output of another command
curl -s https://raw.githubusercontent.com/target-org/repo/main/config.py | gitleaks -v stdin

# Scan an env file from a URL
curl -s https://target-bucket.s3.amazonaws.com/.env | gitleaks -v stdin
```

> [!info]+ Command Breakdown
> 1. **stdin** — accepts raw text piped from any source — anything that produces output can be scanned
> 2. Combine with `curl` to scan files directly from URLs **without saving them locally**
> 3. *This is the fastest way to triage a suspicious file found via GrayHatWarfare or Google Dork — pipe it straight through gitleaks*

---

## Output and Reporting

### Save Results to a File

```bash
# JSON report (default and most useful)
gitleaks git -v . --report-path=findings.json --report-format=json

# CSV report — easy to open in a spreadsheet
gitleaks git -v . --report-path=findings.csv --report-format=csv

# SARIF — standard format for integration with SIEMs and security dashboards
gitleaks git -v . --report-path=findings.sarif --report-format=sarif

# JUnit XML — for CI/CD pipeline integration
gitleaks git -v . --report-path=findings.xml --report-format=junit
```

> [!info]+ Command Breakdown
> 1. **--report-path** — file path to write the report to; gitleaks still prints to terminal alongside writing
> 2. **--report-format** — output format: `json` | `csv` | `junit` | `sarif`
> 3. **json** — best format for OSINT work — easy to parse with `jq`, import into tools, or read manually
> 4. **sarif** — industry-standard static analysis format — importable into GitHub Security, Burp, and SIEMs

---

```bash
# Parse JSON output with jq — extract only the secret values and their files
cat findings.json | jq -r '.[] | "\(.File):\(.Line) → \(.Secret)"'

# Output:
# config/aws.py:12 → AKIAIOSFODNN7EXAMPLE
# .env:3 → ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456

# Get a summary count of findings by rule
cat findings.json | jq 'group_by(.RuleID) | map({rule: ..RuleID, count: length}) | sort_by(-.count)'

# Output:
# [
#   { "rule": "generic-api-key", "count": 14 },
#   { "rule": "aws-access-key-id", "count": 3 },
#   { "rule": "github-pat", "count": 1 }
# ]
```

> [!info]+ Command Breakdown
> 1. **jq -r '.[] | ...'** — iterates every finding in the JSON array
> 2. **\(.File):\(.Line) → \(.Secret)** — formats each finding as `filename:linenumber → secretvalue`
> 3. The **group_by + count** query gives an instant triage view — which secret types appeared most often
> 4. *Start triage with the count summary — AWS keys and GitHub PATs are the highest-value findings to investigate first*

---

### Redact Secrets from Output

```bash
# Redact actual secret values in terminal output and reports
gitleaks git -v --redact .
```

> [!info]+ Command Breakdown
> 1. **--redact** — replaces the actual secret value with `REDACTED` in all output
> 2. Use this when **sharing output** with a client, team, or in a report — never paste raw secrets into documents
> 3. The finding is still reported with file, line, commit, and rule — just not the actual value

---

## Exit Codes

| Exit Code | Meaning | What to Do |
|---|---|---|
| `0` | No secrets found | Clean — move on |
| `1` | Secrets detected | Review findings — escalate critical ones |
| `126` | Unknown flag or bad argument | Check your command syntax |
| `2` | Unexpected error during scan | Check file permissions or repo state |

```bash
# Use exit code in a shell script to branch on findings
gitleaks git . --report-path=findings.json
if [ $? -eq 1 ]; then
    echo "[!] Secrets found — review findings.json immediately"
fi
```

---

## Suppressing False Positives

### Inline Ignore (Single Line)

```bash
# In the source file — add this comment on the line with a known false positive
api_key = "test_key_not_real"  # gitleaks:allow
```

> [!info]+ Command Breakdown
> 1. Adding `# gitleaks:allow` as a comment on the same line tells gitleaks to skip that match
> 2. Useful for **test files**, mock data, or example values that pattern-match but are not real secrets
> 3. *When scanning target repos during OSINT — if you see `gitleaks:allow` on a line, the dev was aware of gitleaks; look harder at nearby lines for real secrets they may have missed*

---

### .gitleaksignore File (Persistent Suppression)

```bash
# Step 1 — Run a scan and save a baseline
gitleaks git . --report-path=baseline.json

# Step 2 — Create a .gitleaksignore file from known false positives
# Add the fingerprint of each false positive — one per line
echo "a3f2c1d9:config/test.py:generic-api-key:45" >> .gitleaksignore

# Step 3 — Future scans will skip anything in .gitleaksignore
gitleaks git . --report-path=new-findings.json
```

> [!info]+ Command Breakdown
> 1. **Fingerprint** format: `commit_hash:file:rule_id:line` — uniquely identifies a specific finding
> 2. The fingerprint is shown in gitleaks output for every finding
> 3. *During OSINT scanning of a target repo — ignore the `.gitleaksignore` file found in the repo; it tells you exactly which findings the devs already knew about and tried to hide from gitleaks*

---

### Baseline Scan (Only Report New Secrets)

```bash
# Step 1 — Scan and save the current state as a baseline
gitleaks git . --report-path=baseline.json

# Step 2 — Run a future scan referencing the baseline
gitleaks git . --report-path=new-findings.json --baseline-path=baseline.json

# Only NEW findings (not in baseline) appear in new-findings.json
```

> [!info]+ Command Breakdown
> 1. **--baseline-path** — provides a previous report; any findings already in it are suppressed in the new report
> 2. Useful for **monitoring** a target repo over time — run weekly and only see what has changed
> 3. *Set up a cron job to scan high-value target repos weekly and alert only on new findings — a passive, ongoing intelligence feed*

---

## Custom Detection Rules

> [!tip]+ Write Rules for Target-Specific Patterns
> The default ruleset catches generic secrets. For targeted OSINT, add custom rules for company-specific patterns — internal tokens, system names discovered in job postings, or API formats unique to the target's stack.

```toml
# custom-rules.toml
# Place this file anywhere — reference it with --config

rules
id = "target-internal-token"
description = "Target Corp internal API token format"
regex = '''TGT-[a-zA-Z0-9]{32}'''
tags = ["api", "target-corp"]

rules
id = "target-jwt-secret"
description = "Hardcoded JWT secret matching target's known format"
regex = '''jwt_secret\s*=\s*["'][a-zA-Z0-9+/=]{40,}["']'''
tags = ["jwt", "target-corp"]
```

```bash
# Use custom rules alongside the defaults
gitleaks git -v --config=custom-rules.toml .

# Use ONLY custom rules (ignore default ruleset)
gitleaks git -v -c custom-rules.toml --no-banner .
```

> [!info]+ Command Breakdown
> 1. **--config / -c** — path to a custom `.toml` config file containing your own rules
> 2. Custom rules **add to** the default ruleset — they don't replace it unless you explicitly override
> 3. **regex** — standard Go regex syntax; test your patterns at [regex101.com](https://regex101.com/) with the Go flavour selected
> 4. **tags** — metadata only; useful for filtering output later with `jq`
> 5. *Build custom rules based on intelligence gathered from job postings and GitHub — if you know the company uses a custom auth token format, write a rule for it*

---

## Decoded and Encoded Secret Scanning

```bash
# Scan for secrets hidden inside Base64, URL-encoded, or other encoded strings
gitleaks git -v --max-decode-depth=5 .
```

> [!info]+ Command Breakdown
> 1. **--max-decode-depth** — enables recursive decoding of encoded content; default is 0 (disabled)
> 2. Gitleaks will attempt to decode Base64, URL encoding, and other common formats, then scan the decoded output
> 3. Setting depth to `5` means it will decode up to 5 layers deep (e.g., Base64 inside Base64)
> 4. *Developers sometimes Base64-encode secrets thinking it obscures them — this flag catches that anti-pattern*
> 5. *Setting a very high depth doesn't slow things down significantly — gitleaks stops as soon as there's nothing left to decode*

---

## Full OSINT Workflow

```bash
# 1. Clone the target repo
git clone https://github.com/target-org/target-repo.git
cd target-repo

# 2. Full scan — all branches, all history, verbose, save JSON
gitleaks git -v \
  --log-opts="--all" \
  --report-path=target-repo-findings.json \
  --report-format=json \
  --max-decode-depth=3 \
  .

# 3. Quick triage — count findings by rule type
cat target-repo-findings.json | jq 'group_by(.RuleID) | map({rule: ..RuleID, count: length}) | sort_by(-.count)'

# 4. Extract highest-value findings — AWS keys, GitHub tokens, private keys
cat target-repo-findings.json | jq '.[] | select(.RuleID == "aws-access-key-id" or .RuleID == "github-pat" or .RuleID == "rsa-private-key") | {file: .File, line: .Line, commit: .Commit, author: .Author, date: .Date}'

# 5. For each high-value finding, check the exact commit for context
git show <commit_hash>

# 6. Check if the secret is still present in the current HEAD
grep -r "AKIAIOSFODNN7EXAMPLE" .
```

> [!info]+ Workflow Breakdown
> 1. **Step 2** — `--all` ensures all branches are included; `--max-decode-depth=3` catches encoded secrets; JSON output enables scripted triage
> 2. **Step 3** — group by RuleID first; triage by secret type, not by file — AWS keys and GitHub PATs are worth more than generic API keys
> 3. **Step 4** — `select()` filter in jq isolates the highest-priority findings immediately
> 4. **Step 5** — `git show <hash>` shows the full diff for that commit — gives context (what else changed, who committed, what the surrounding code does)
> 5. **Step 6** — `grep -r` confirms whether the secret still exists in current files or was only in history

---

> [!success]+ What to Do with a Finding
> 1. **Record** the secret value, file path, commit hash, author email, and date
> 2. **Check if still active** — grep current files; if still present, it is likely live and exploitable
> 3. **Identify the service** — AWS key? Try `aws sts get-caller-identity`. GitHub PAT? Try `curl -H "Authorization: token <PAT>" https://api.github.com/user`
> 4. **Document in your report** — include rule ID, file, commit hash, author, and date discovered
> 5. **Do not use the credential** beyond confirming it is valid — exploitation beyond scope verification is out of bounds

---

## References

1. [Gitleaks GitHub Repository](https://github.com/gitleaks/gitleaks)
2. [Gitleaks Releases Page](https://github.com/gitleaks/gitleaks/releases)
3. [Gitleaks Default Rules Config (gitleaks.toml)](https://github.com/gitleaks/gitleaks/blob/master/config/gitleaks.toml)
4. [Gitleaks Playground](https://gitleaks.io/playground)
5. [v8.19.0 Command Translation Gist](https://gist.github.com/zricethezav/b325bb93ebf41b9c0b0507acf12810d2)
6. [HTB Academy - Footprinting Module](https://academy.hackthebox.com/module/details/112)
7. [Gitleaks Blog — Advanced Configuration](https://blog.gitleaks.io/stop-leaking-secrets-configuration-2-3-aeed293b1fbf)
8. [HackTricks - OSINT](https://book.hacktricks.xyz/generic-methodologies-and-resources/external-recon-methodology)
9. [MITRE ATT&CK - Search Open Technical Databases (T1596)](https://attack.mitre.org/techniques/T1596/)
10. [Source: 2.0 - Cheatsheet - Infrastructure Enumeration Tools](2.0%20-%20Cheatsheet%20-%20Infrastructure%20Enumeration%20Tools.md)
11. [Source: 2.3 - Theory Staff](2.3%20-%20Theory%20Staff.md)

---

#HTB #Footprinting #OSINT #Gitleaks #SecretScanning #GitHistory #CredentialLeak #Cheatsheet #GitHub #PassiveRecon
