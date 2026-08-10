---
title: "2.5 - Cheatsheet - TruffleHog"
description: "brew install trufflehog"
category: enumeration
tags: ["enumeration"]
tools: ["Gitleaks", "TruffleHog"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Enumeration/GitHub-Enum/2.5 - Cheatsheet - TruffleHog.md"
---
# macOS — Homebrew
brew install trufflehog

# Linux — install script (always fetches latest)
curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh \
  | sh -s -- -b /usr/local/bin

# Docker (no install required — pull and run)
docker pull trufflesecurity/trufflehog:latest

# Verify install
trufflehog --version
# Output:
# trufflehog 3.88.1
```

> [!info]+ Command Breakdown
> 1. The **install script** always pulls the latest release binary — no need to track version numbers manually
> 2. **-b /usr/local/bin** — places the binary in your PATH; change to `~/bin` if you don't have sudo
> 3. The **Docker** option is useful on systems where you can't install binaries — swap any command below using `docker run --rm trufflesecurity/trufflehog:latest [subcommand]`

---

## Subcommands at a Glance

| Subcommand | What It Scans | OSINT Use Case |
|---|---|---|
| `git` | Single git repository — full commit history | Cloned public repos, any local git repo |
| `github` | Entire GitHub org or specific repo — including issues and PRs | Scan all of a company's public repos at once |
| `gitlab` | GitLab org or specific project | European/self-hosted company repos |
| `filesystem` | Local directories and files | Downloaded files, extracted archives, scraped content |
| `s3` | AWS S3 buckets | Misconfigured public buckets found via GrayHatWarfare/Dorks |
| `gcs` | Google Cloud Storage buckets | GCP-hosted company storage |
| `docker` | Docker image layers | Find secrets baked into company Docker images |
| `stdin` | Piped data stream | Scan any streamed content |
| `circleci` | CircleCI build logs | CI/CD pipeline secret exposure |
| `travisci` | Travis CI build logs | CI/CD pipeline secret exposure |
| `jenkins` | Jenkins build logs | Self-hosted CI secret exposure |
| `postman` | Postman workspaces | API collection secrets |
| `elasticsearch` | Elasticsearch indices | Database-stored secrets |

---

## Understanding Results — The Verification Model

> [!important]+ Result Types — Know These Before You Scan
> TruffleHog classifies every finding into one of four result types. Use `--results=` to control what is shown:

| Result Type | Meaning | What to Do |
|---|---|---|
| `verified` | Secret found AND confirmed live by API call | **Highest priority** — escalate immediately |
| `unknown` | Secret found, API call inconclusive (no clear pass/fail) | Investigate manually — still worth reporting |
| `unverified` | Secret found BUT API call confirmed it is invalid/expired | Lower priority — may still be useful for password reuse |
| `filtered_unverified` | Duplicate unverified results filtered out | Noise reduction only |

```bash
# Default — shows ALL result types (noisy but complete)
trufflehog git https://github.com/target-org/target-repo.git

# Focused — only show confirmed live secrets (fastest triage)
trufflehog git https://github.com/target-org/target-repo.git --results=verified,unknown

# Passive mode — no API verification calls at all (safest for engagements)
trufflehog git https://github.com/target-org/target-repo.git --no-verification
```

> [!info]+ Command Breakdown
> 1. **--results=verified,unknown** — the most useful filter for OSINT; catches live secrets and anything the API couldn't definitively reject
> 2. **--no-verification** — disables all outbound API calls; TruffleHog acts like a pattern matcher only; use this when you want passive-only operation during an engagement
> 3. *Start every scan with `--results=verified,unknown` — if nothing comes back, broaden to all results*

---

## Exit Codes

| Exit Code | Meaning |
|---|---|
| `0` | No errors, no results found |
| `1` | An error was encountered — scan may be incomplete |
| `183` | No errors, but **results were found** — only returned when `--fail` flag is used |

```bash
# Use --fail to get exit code 183 on findings — useful in scripts
trufflehog git . --results=verified,unknown --fail
echo "Exit: $?"
# Exit: 183   ← secrets found
```

---

## Core Scan Commands

### Scan a Single Git Repository

```bash
# Scan a remote repo directly (no manual clone needed)
trufflehog git https://github.com/target-org/target-repo.git \
  --results=verified,unknown \
  --json

# Scan a locally cloned repo
trufflehog git file:///home/user/target-repo \
  --results=verified,unknown \
  --json

# Output example:
{
  "SourceMetadata": {
    "Data": {
      "Git": {
        "commit": "a3f2c1d9e8b74561...",
        "file": "config/settings.py",
        "email": "dev@target.com",
        "repository": "https://github.com/target-org/target-repo.git",
        "timestamp": "2023-04-18 14:22:01 +0000",
        "line": 12
      }
    }
  },
  "SourceID": 1,
  "SourceType": 16,
  "SourceName": "trufflehog - git",
  "DetectorType": 2,
  "DetectorName": "AWS",
  "DecoderName": "PLAIN",
  "Verified": true,
  "Raw": "AKIAIOSFODNN7EXAMPLE",
  "RawV2": "AKIAIOSFODNN7EXAMPLEwJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "Redacted": "AKIAIOSFODNN7EXAMPLE",
  "ExtraData": {
    "account": "123456789012",
    "arn": "arn:aws:iam::123456789012:user/dev",
    "user_id": "AIDA..."
  },
  "StructuredData": null
}
```

> [!info]+ Command Breakdown
> 1. **file://** — URI scheme for local paths; TruffleHog requires an explicit scheme (`https://`, `file://`, or `ssh://`)
> 2. **--json** — outputs each finding as a JSON object — one per line (NDJSON format) — essential for piping to `jq`
> 3. **Verified: true** — TruffleHog called the AWS API and confirmed this key is live
> 4. **ExtraData** — for verified AWS keys, TruffleHog returns the account ID, ARN, and user ID — you know exactly whose account was compromised without touching the infrastructure
> 5. **RawV2** — for credentials with two parts (key ID + secret), both values are shown
> 6. *The `email` field in `SourceMetadata` gives you the committer's email — direct attribution*

---

### Scan a Specific Branch or Commit Depth

```bash
# Scan a specific branch only
trufflehog git https://github.com/target-org/target-repo.git \
  --branch=develop \
  --results=verified,unknown \
  --json

# Limit to the last N commits
trufflehog git https://github.com/target-org/target-repo.git \
  --max-depth=100 \
  --results=verified,unknown

# Start scan from a specific commit (scan everything after this hash)
trufflehog git https://github.com/target-org/target-repo.git \
  --since-commit=a3f2c1d9e8b74561 \
  --results=verified,unknown
```

> [!info]+ Command Breakdown
> 1. **--branch** — restricts scan to one branch; combine with multiple runs to cover all branches
> 2. **--max-depth** — limits how many commits deep to scan from HEAD; useful for large repos where you only care about recent history
> 3. **--since-commit** — start scanning from after this commit hash; useful for delta scans (only check what changed since last run)
> 4. *Unlike Gitleaks, TruffleHog does NOT have an `--all` flag for all branches — run it per branch or use the `github` subcommand to cover all branches automatically*

---

### Scan an Entire GitHub Organisation

```bash
# Unauthenticated — public repos only (rate-limited to ~60 req/hr)
trufflehog github --org=target-org \
  --results=verified,unknown \
  --json

# Authenticated — public + private repos (rate-limited to ~5000 req/hr)
trufflehog github --org=target-org \
  --token=ghp_YourGitHubPAThere \
  --results=verified,unknown \
  --json

# Scan a specific repo via the github subcommand (also scans issues + PRs)
trufflehog github \
  --repo=https://github.com/target-org/target-repo \
  --issue-comments \
  --pr-comments \
  --results=verified,unknown \
  --json
```

> [!info]+ Command Breakdown
> 1. **--org** — scans ALL repositories belonging to the organisation — the most powerful single-command recon capability TruffleHog has over Gitleaks
> 2. **--token** — GitHub PAT; use a throwaway account's PAT for OSINT — never your real account
> 3. **--issue-comments** — scans issue comment text — devs frequently paste credentials into issue comments ("here's the key to reproduce this bug: `sk-...`")
> 4. **--pr-comments** — scans pull request comments and review threads — another common accidental paste location
> 5. *The org-level scan is the single most impactful command for OSINT — one command, every repo, all history, verified results*

---

### Scan a Filesystem or Directory

```bash
# Scan a downloaded directory
trufflehog filesystem /path/to/downloaded/files \
  --results=verified,unknown \
  --json

# Scan a single file
trufflehog filesystem /path/to/suspicious/.env \
  --results=verified,unknown

# Scan current directory
trufflehog filesystem . --results=verified,unknown --json

# Scan with archive extraction (zip, tar.gz, etc.)
trufflehog filesystem /path/to/directory \
  --results=verified,unknown \
  --archive-max-depth=5 \
  --archive-max-size=100MB \
  --json
```

> [!info]+ Command Breakdown
> 1. **filesystem** — no git context required; scans raw file contents; useful for downloaded cloud bucket files, scraped web content, or extracted archives
> 2. **--archive-max-depth** — how many levels of nested archives to open and scan (e.g., a `.zip` inside a `.tar.gz`); default is disabled
> 3. **--archive-max-size** — caps how large an archive can be before TruffleHog skips it; prevents memory exhaustion on large files
> 4. *Pair with GrayHatWarfare — download files from public buckets, then run TruffleHog filesystem over the download folder with archive scanning enabled*

---

### Scan an S3 Bucket

```bash
# Scan a public or accessible bucket (uses ~/.aws/credentials automatically)
trufflehog s3 --bucket=target-company-assets \
  --results=verified,unknown \
  --json

# Scan using an assumed IAM role (for cross-account scanning)
trufflehog s3 --bucket=target-bucket \
  --role-arn=arn:aws:iam::123456789012:role/ScannerRole \
  --results=verified,unknown

# Scan ALL buckets accessible via multiple roles
trufflehog s3 \
  --role-arn=arn:aws:iam::111111111111:role/Role1 \
  --role-arn=arn:aws:iam::222222222222:role/Role2 \
  --results=verified,unknown
```

> [!info]+ Command Breakdown
> 1. TruffleHog uses the **AWS SDK** — it automatically picks up credentials from `~/.aws/credentials`, environment variables, or EC2 instance metadata
> 2. **--role-arn** — assume an IAM role before scanning; useful if you have a role ARN from a leaked key and want to enumerate what that role can access
> 3. Multiple **--role-arn** flags — TruffleHog scans all buckets each role has `s3:ListBucket` permissions on — one command enumerates and scans everything reachable
> 4. *If you find an AWS key via git scanning, verify it with `aws sts get-caller-identity`, then pivot: use the same key to run TruffleHog against all accessible S3 buckets*

---

### Scan a Docker Image

```bash
# Scan a public Docker image from Docker Hub
trufflehog docker --image=target-org/target-app:latest \
  --results=verified,unknown \
  --json

# Scan a specific image by digest (for precise version targeting)
trufflehog docker --image=target-org/app@sha256:abc123... \
  --results=verified,unknown \
  --json
```

> [!info]+ Command Breakdown
> 1. TruffleHog scans **each layer** of the Docker image — secrets baked in during build (e.g., `RUN curl -H "Authorization: Bearer $TOKEN"`) survive in image layers even if later layers delete them
> 2. Uses Docker Hub's public API — no authentication needed for public images
> 3. **Image digest scanning** allows scanning a specific build — if a company publishes versioned images, older versions may contain secrets removed in newer builds
> 4. *Company Docker images are often on Docker Hub or GitHub Container Registry — search `docker.io/[company-name]` or `ghcr.io/[org-name]` for public images*

---

### Scan via stdin

```bash
# Scan a file piped from curl — no local save needed
curl -s https://target-bucket.s3.amazonaws.com/.env \
  | trufflehog stdin --results=verified,unknown --json

# Scan any command output
cat suspicious_config.py | trufflehog stdin --results=verified,unknown
```

> [!info]+ Command Breakdown
> 1. **stdin** — accepts raw streamed content; anything that produces output can be scanned
> 2. Combine with `curl` to triage a suspicious file from a public URL instantly
> 3. *Fastest initial triage method — pipe before deciding whether to fully download a file*

---

## Output and Triage

### JSON Output with jq Triage

```bash
# Save all findings to a file
trufflehog github --org=target-org \
  --results=verified,unknown \
  --json > findings.json 2>/dev/null

# Show only verified findings — simplest triage
cat findings.json | jq 'select(.Verified == true)'

# Extract key fields for a clean summary
cat findings.json | jq -r '
  select(.Verified == true) |
  "\(.DetectorName) | \(.SourceMetadata.Data.Git.file) | \(.SourceMetadata.Data.Git.email) | \(.Raw[0:20])..."
'
# Output:
# AWS | config/settings.py | dev@target.com | AKIAIOSFODNN7EXAMPL...
# GitHub | scripts/deploy.sh | ci@target.com | ghp_aBcDeFgHiJkLmN...

# Count findings by detector type
cat findings.json | jq -r '.DetectorName' | sort | uniq -c | sort -rn
# Output:
#  14 GenericAPIKey
#   3 AWS
#   1 GitHub

# Get ExtraData for verified AWS keys (account ID, ARN, user)
cat findings.json | jq 'select(.DetectorName == "AWS" and .Verified == true) | .ExtraData'
# Output:
# {
#   "account": "123456789012",
#   "arn": "arn:aws:iam::123456789012:user/ci-deploy",
#   "user_id": "AIDA4EXAMPLE"
# }
```

> [!info]+ Command Breakdown
> 1. **2>/dev/null** — suppresses TruffleHog's progress logs; keeps the JSON output clean for piping
> 2. **select(.Verified == true)** — jq filter that only returns verified findings
> 3. **\(.Raw[0:20])...** — shows only the first 20 chars of the secret — enough to identify it without printing the full value in terminal history
> 4. **uniq -c | sort -rn** — counts and sorts by frequency — tells you which secret type is most prevalent
> 5. **ExtraData** — the intelligence goldmine for AWS findings — account ID tells you the AWS account; ARN tells you the user; these confirm the blast radius of the leak

---

### Controlling Noise — Entropy and Detector Filters

```bash
# Filter low-entropy unverified results (reduces generic false positives)
# Start at 3.0 and increase if still too noisy
trufflehog git https://github.com/target-org/repo.git \
  --results=unverified \
  --filter-entropy=3.5 \
  --json

# Scan ONLY specific detector types (focus on high-value targets)
trufflehog git https://github.com/target-org/repo.git \
  --include-detectors="AWS,GitHub,GitLab,Slack,Stripe,OpenAI" \
  --results=verified,unknown \
  --json

# Exclude noisy low-value detectors
trufflehog git https://github.com/target-org/repo.git \
  --exclude-detectors="GenericAPIKey,URI" \
  --results=verified,unknown \
  --json
```

> [!info]+ Command Breakdown
> 1. **--filter-entropy** — [Shannon entropy](https://en.wikipedia.org/wiki/Entropy_(information_theory)) score threshold; only show unverified results above this score; higher entropy = more random = more likely to be a real secret; `3.5` is a good starting value
> 2. **--include-detectors** — comma-separated list; restrict to only the detectors you care about; eliminates entire categories of noise
> 3. **--exclude-detectors** — `GenericAPIKey` and `URI` are the noisiest detectors; excluding them dramatically reduces false positives when you just want high-confidence results
> 4. *For OSINT triage: start with `--include-detectors="AWS,GitHub,GitLab,Slack,Stripe,OpenAI,Twilio"` — these are the highest-impact credentials*

---

> [!tip]+ High-Value Detector Priority List
> | Priority | Detector | Why |
> |---|---|---|
> | **Critical** | `AWS` | Direct cloud infrastructure access — account takeover |
> | **Critical** | `GitHub` | Access to code, Actions secrets, repo admin |
> | **Critical** | `GitLab` | Same as GitHub for GitLab-hosted companies |
> | **High** | `Slack` | Internal comms — further OSINT, social engineering |
> | **High** | `Stripe` | Financial API — direct monetary impact |
> | **High** | `OpenAI` | AI API access — often expensive, reveals internal tooling |
> | **High** | `Twilio` | SMS/voice API — phishing pivot, account takeover via 2FA |
> | **Medium** | `Sendgrid` / `Mailgun` | Email sending — phishing infrastructure |
> | **Medium** | `Postman` | Reveals internal API structure and endpoints |
> | **Medium** | `HuggingFace` | ML model access — internal AI tooling |

---

## The `analyze` Subcommand — Key Permission Enumeration

```bash
# Interactively analyse a found key — TruffleHog auto-detects the type
trufflehog analyze --token=AKIAIOSFODNN7EXAMPLEwJalrXUtnFEMI

# Specify key type explicitly
trufflehog analyze github --token=ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456

# JSON output for scripting
trufflehog analyze github \
  --token=ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456 \
  --json

# Output:
# {
#   "token_type": "GitHub",
#   "permissions": {
#     "repo": "write",
#     "admin:org": "none",
#     "read:user": "read",
#     "workflow": "write"
#   },
#   "scopes": ["repo", "read:user", "workflow"],
#   "username": "ci-deploy-bot",
#   "org_memberships": ["target-org"]
# }
```

> [!info]+ Command Breakdown
> 1. **analyze** — TruffleHog's unique capability; takes a found credential and enumerates exactly what permissions it has, without you having to manually test each API endpoint
> 2. Supported key types: AWS, GitHub, GitLab, Slack, Stripe, Twilio, OpenAI, Postman, Shopify, Sendgrid, Mailchimp, Mailgun, Bitbucket, HuggingFace, and more
> 3. **permissions** output — tells you exactly what the key can do: read-only? Write access? Admin? — determines the blast radius before you even make a decision
> 4. **org_memberships** — for GitHub tokens, reveals which organisations the token has access to — one leaked personal token can expose multiple organisations
> 5. *This replaces manually calling `aws sts get-caller-identity`, `curl https://api.github.com/user`, etc. — TruffleHog does it all in one command*

> [!warning]+ analyze Makes Live API Calls
> 1. Every `analyze` run makes real API calls to the target service
> 2. These calls may be logged by the service — AWS CloudTrail, GitHub audit logs, etc.
> 3. In an engagement: get written approval to verify credentials before running `analyze`
> 4. Use `--no-verification` during scanning and `analyze` only on the highest-confidence findings after scope confirmation

---

## Custom Detectors — Target-Specific Patterns

```yaml
# custom-detectors.yaml
# Reference with --config=custom-detectors.yaml

detectors:
  - name: TargetCorpInternalToken
    keywords:
      - "TGT-"
    regex:
      secret: "TGT-[a-zA-Z0-9]{32}"
    verify:
      - endpoint: "https://api.target-internal.com/v1/auth/verify"
        unsafe: true
        headers:
          - "Authorization: Bearer $secret"
        successRanges:
          - "200-299"

  - name: TargetCorpJWTSecret
    keywords:
      - "jwt_secret"
      - "JWT_SECRET"
    regex:
      secret: '(?i)jwt_secret\s*[=:]\s*["'']([a-zA-Z0-9+/=]{40,})["'']'
```

```bash
# Run with custom detectors alongside default ruleset
trufflehog git https://github.com/target-org/repo.git \
  --config=custom-detectors.yaml \
  --results=verified,unknown \
  --json
```

> [!info]+ Command Breakdown
> 1. **keywords** — pre-filter strings TruffleHog looks for before applying the regex; improves scan performance
> 2. **regex.secret** — the capture group that extracts the actual secret value
> 3. **verify.endpoint** — TruffleHog will call this URL with the found secret to verify it — returns `verified: true` if the response is in `successRanges`
> 4. **unsafe: true** — required for non-HTTPS endpoints (internal APIs); omit for public HTTPS endpoints
> 5. *Custom detectors give TruffleHog's verification power to company-specific secrets discovered through job posting and LinkedIn OSINT*

---

## Full OSINT Workflow

```bash
# ── PHASE 1: Org-Level Sweep ──────────────────────────────────────────
# Scan the entire GitHub org — all repos, all history, verify everything
trufflehog github \
  --org=target-org \
  --results=verified,unknown \
  --json \
  --no-update \
  2>/dev/null | tee org-findings.json

# ── PHASE 2: Triage ───────────────────────────────────────────────────
# Count by detector type — identify the biggest wins
cat org-findings.json | jq -r '.DetectorName' | sort | uniq -c | sort -rn

# Pull all verified findings with attribution
cat org-findings.json | jq -r '
  select(.Verified == true) |
  [.DetectorName, .SourceMetadata.Data.Git.repository, .SourceMetadata.Data.Git.file,
   .SourceMetadata.Data.Git.email, .SourceMetadata.Data.Git.commit] | @tsv
' | column -t

# ── PHASE 3: Deep Dive High-Value Repos ───────────────────────────────
# For repos with findings — run Gitleaks for full history depth
git clone https://github.com/target-org/high-value-repo.git
gitleaks git -v --log-opts="--all" --report-path=repo-findings.json ./high-value-repo

# ── PHASE 4: Expand to Cloud ──────────────────────────────────────────
# If AWS keys were found — scan all accessible S3 buckets with them
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
trufflehog s3 --results=verified,unknown --json 2>/dev/null | tee s3-findings.json

# ── PHASE 5: Analyse Key Permissions ──────────────────────────────────
# For each high-value verified credential
trufflehog analyze github --token=ghp_FoundToken --json
trufflehog analyze aws --token=AKIAIOSFODNN7EXAMPLE:wJalrXUtnFEMI/K7MDENG --json

# ── PHASE 6: Docker Images ────────────────────────────────────────────
# Check public Docker images for the org
trufflehog docker \
  --image=target-org/main-app:latest \
  --results=verified,unknown \
  --json 2>/dev/null | tee docker-findings.json
```

> [!info]+ Workflow Breakdown
> 1. **Phase 1** — `tee` writes to file AND shows on terminal simultaneously; `2>/dev/null` suppresses progress noise; `--no-update` skips the version check for speed
> 2. **Phase 2** — the `@tsv | column -t` combination produces a clean aligned table of all verified findings with repo, file, email, and commit — copy-paste ready for a report
> 3. **Phase 3** — TruffleHog catches live secrets; Gitleaks catches historical patterns — they complement each other; use both on high-value repos
> 4. **Phase 4** — a verified AWS key is the bridge from code recon to cloud infrastructure recon; TruffleHog can enumerate all buckets that key has access to automatically
> 5. **Phase 5** — `analyze` tells you the blast radius before you escalate — no manual API testing required
> 6. **Phase 6** — Docker layers frequently contain secrets from build-time environment variables and RUN commands that were never intended to persist

---

> [!success]+ What to Do with a Verified Finding
> 1. **Record** — detector name, raw value (first 20 chars only), file, commit hash, author email, repository, timestamp
> 2. **Analyse** — run `trufflehog analyze [type] --token=[value] --json` to enumerate permissions and blast radius
> 3. **Confirm scope** — verify the credential's service is within your engagement scope before proceeding
> 4. **Document** — include verification status, `ExtraData` (account IDs, ARNs, usernames), and permissions in your report
> 5. **Do not exploit** beyond confirming the credential is valid — accessing systems, exfiltrating data, or making changes is out of bounds

---

## References

1. [TruffleHog GitHub Repository](https://github.com/trufflesecurity/trufflehog)
2. [TruffleHog Official Documentation](https://docs.trufflesecurity.com/)
3. [TruffleHog Scanning Git — 2024 Comprehensive Guide](https://trufflesecurity.com/blog/scanning-git-for-secrets-the-2024-comprehensive-guide)
4. [TruffleHog Analyze — Key Permissions Blog Post](https://trufflesecurity.com/blog/trufflehog-now-analyzes-permissions-of-api-keys-and-passwords)
5. [TruffleHog Git vs Filesystem Commands](https://trufflesecurity.com/blog/trufflehog-commands-git-vs-filesystem)
6. [Driftwood — Private Key Verification](https://trufflesecurity.com/blog/driftwood)
7. [TruffleHog Custom Detectors](https://github.com/trufflesecurity/trufflehog/blob/main/pkg/custom_detectors/CUSTOM_DETECTORS.md)
8. [Shannon Entropy — Wikipedia](https://en.wikipedia.org/wiki/Entropy_(information_theory))
9. [HTB Academy - Footprinting Module](https://academy.hackthebox.com/module/details/112)
10. [HackTricks - OSINT](https://book.hacktricks.xyz/generic-methodologies-and-resources/external-recon-methodology)
11. [MITRE ATT&CK - Search Open Technical Databases (T1596)](https://attack.mitre.org/techniques/T1596/)
12. [Source: 2.4 - Cheatsheet - Gitleaks](02Cybersecurity/Cheatsheets/Enumeration/GitHub-Enum/2.4%20-%20Cheatsheet%20-%20Gitleaks.md)
13. [Source: 2.3 - Theory Staff](2.3%20-%20Theory%20Staff.md)
14. [Source: 2.0 - Cheatsheet - Infrastructure Enumeration Tools](2.0%20-%20Cheatsheet%20-%20Infrastructure%20Enumeration%20Tools.md)

---

#HTB #Footprinting #OSINT #TruffleHog #SecretScanning #CredentialVerification #GitHistory #AWS #GitHub #Cheatsheet #PassiveRecon
