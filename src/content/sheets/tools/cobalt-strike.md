---
title: "Cobalt Strike"
description: "Cobalt Strike operator reference: beacon commands, listeners, pivoting and post-exploitation."
category: tools
tags: [c2, post-exploitation, red-team]
tools: [Cobalt Strike]
difficulty: advanced
updated: "2026-08-09"
source: "vault:Tools/Cobalt-Strike-Cheatsheet.md"
---

# Cobalt Strike

> **Context —** Authorised red-team / lab C2 reference. Tool: Cobalt Strike (operator quick-ref).

Licensed adversary-simulation / C2 framework. This note is a **high-level operator checklist** for authorised engagements and lab study — not a piracy, crack, or bypass guide. Confirm every command against your licensed build's UI help and the vendor user guide for your version.

Related notes: Mimikatz, Rubeus, NetExec, Impacket, BloodHound, NTLM & Kerberos Relay.

---

## Summary

Cobalt Strike centres on a **team server**, a GUI/client, **listeners**, and **Beacon** sessions. Operators stage payloads, manage callbacks, run post-ex jobs, and coordinate lateral movement under a shared log. Treat it as a commercial C2: licensing, Malleable C2 profiles, and infrastructure OPSEC matter as much as individual Beacon commands.

> **Danger — authorised-use framing**
> 1. Use only with a valid licence and written authorisation.
> 2. Do not distribute cracked clients/servers or "update" cracks — out of scope for this note.
> 3. Align profile, redirectors, and kill dates with ROE and deconfliction.

---

## Team Server & Client

```bash
# Typical lab pattern (paths/version-specific — verify locally)
./teamserver <teamserver_IP> <password> [malleable.profile]
# Client connects to teamserver_IP with the shared password
```

> **Infrastructure basics**
> 1. **Team server** should sit behind redirectors; do not expose it directly to the internet.
> 2. Use a strong shared password; rotate per engagement.
> 3. Load a **Malleable C2** profile appropriate to the environment before phishing/staging.
> 4. Record listener ports, domains, and kill dates in the engagement runbook.

---

## Listeners & Payloads (concepts)

| Piece | Role |
|---|---|
| Listener | Defines how Beacon calls back (HTTP/HTTPS/DNS/SMB/TCP, etc.) |
| Payload / stageless artefact | Dropper or export generated for a listener |
| Malleable profile | Shapes network indicators to match allowed patterns |
| Staging vs stageless | Staged pulls stage0→stage; stageless embeds — trade size vs flexibility |

> **Operator checklist**
> 1. Create listener → generate artefact for the right arch (x86/x64).
> 2. Prefer HTTPS + valid-looking infra over raw IP:port in hostile networks.
> 3. SMB/TCP beacons are for **egress-limited** pivots inside the estate.
> 4. Name listeners clearly (`prod-https-redir1`) so multi-operator teams do not collide.

---

## Beacon Operator Essentials

> **Common console verbs (names stable across many versions; confirm in your build)**
> 1. **Situational**: `help`, `sleep`, `ps`, `pwd`, `ls`, `cd`, `drive`.
> 2. **Jobs / inject**: `jobs`, `jobkill`, `inject`, `spawnto`, `ppid` (OPSEC-sensitive).
> 3. **Creds / tokens**: `getuid`, `steal_token`, `make_token`, `rev2self` — pair with Mimikatz tradecraft only when approved.
> 4. **Files**: `upload`, `download`, `browserpivot` (as available in your version).
> 5. **Lateral**: prefer documented built-ins / approved BOFs over random scripts; Impacket/nxc from a pivot host is often cleaner for labs.

```text
# Illustrative Beacon hygiene (not a full command bible)
sleep 60 10          # jittered callback — reduce chatty C2
getuid
ps
# run approved post-ex modules only under ROE
```

> **Warning — keep this sheet intentionally thin**
> 1. Full Beacon/Aggressor encyclopaedias belong in your licensed user guide.
> 2. Lab exams (CRTO-style) expect vendor docs + course notes — use those as source of truth.

---

## OPSEC Checklist

1. Sleep/jitter appropriate to detection risk; avoid interactive spam.
2. `spawnto` / parent PID spoofing only with a story that matches the host.
3. Long-haul vs short-haul listeners separated; burn short-haul after staging.
4. Log operator actions; attribute every lateral move to a ticket/finding.
5. Kill date / dead-man switches set before phishing.
6. Deconflict with blue team when ROE requires it.

---

## Engagement Workflow

```text
1. Build redirectors + teamserver + profile
2. Stand up listeners (long-haul / short-haul)
3. Generate artefacts for approved initial-access path
4. Establish Beacon → situational awareness
5. Credential / ticket work per ROE (Mimikatz/Rubeus/CS modules)
6. Lateral with least noise that still meets objectives
7. Capture evidence → clean up persistence → tear down infra
```

---

## Troubleshooting & Gotchas

> **Common failures**
> 1. **No callback**: profile host/URI mismatch, broken redirector, or egress filter — verify with a controlled lab implant first.
> 2. **Team server reject**: clock skew, wrong password, or version skew between client and server.
> 3. **Beacon dies after sleep change**: unrealistic sleep/jitter or network middleboxes — stage carefully.

---

## Lessons Learned

1. Infrastructure and profiles win engagements before fancy post-ex.
2. Name listeners and log everything — multiplayer C2 is a coordination problem.
3. Use CS for C2 continuity; use Impacket/nxc/Rubeus when they are quieter or clearer for a specific task.
4. Keep piracy and "cracked CS" material out entirely.
5. Version drift is real — re-check help after upgrades.

---

## References

1. Cobalt Strike (Fortra) — https://www.cobaltstrike.com/
2. Vendor user guide for your licensed version (Fortra documentation portal)
3. MITRE ATT&CK — Command and Control (TA0011)
4. SpecterOps / community OPSEC blogs — https://posts.specterops.io/
