---
title: "Nmap"
description: "Nmap host discovery, port/service/version scanning, timing, output formats and common scan recipes."
category: enumeration
tags: [enumeration, port-scanning, network]
tools: [Nmap]
difficulty: beginner
updated: "2026-08-09"
source: "vault:Enumeration/Nmap Cheatsheet 2026.md"
---

# Nmap

> **Important — Why This Sheet Exists.** Most people stop at `nmap -sC -sV -oA scan <target>`. That's maybe 20% of what Nmap can actually do. This sheet covers the flags, workflows, and interactive tricks that rarely show up in beginner guides — the stuff that separates "ran a scan" from "understood the target and its defences." Pairs with Awesome NMAP grep (post-processing greppable output) and the NSE Guide (script-level enumeration per port).

---

## Live Runtime Control

> **Tip — Interactive Keys While a Scan Is Running.** Nmap has a **runtime keyboard interface** — you don't need `--stats-every` or a second terminal to check progress on a long `-p-` scan.
> 1. Press **`v`** — increase verbosity live, mid-scan
> 2. Press **`V`** — decrease verbosity
> 3. Press **`d`** — increase debug level live
> 4. Press **`D`** — decrease debug level
> 5. Press **any other key** (e.g. spacebar) — print an immediate status line: % complete, ETA, current probe
>
> No flag needed — it works on any running scan in an interactive terminal. Combine with `--stats-every 10s` to also get automatic periodic updates without touching the keyboard.

```bash
nmap -p- -T4 --stats-every 15s 10.10.10.5
# Then just tap spacebar anytime to force an immediate progress line
```

---

## Precision Timing — Beyond `-T0`–`-T5`

> **Important — `-T` Is a Preset, Not a Real Setting.** `-T0`–`-T5` are just bundles of the real underlying timing flags below. Most people never touch the real knobs — but that's where actual control lives.

| Flag | Controls | Why It Matters |
|---|---|---|
| `--min-rate <num>` | Minimum packets sent per second | Forces a floor speed — use to stop Nmap self-throttling on a fast link |
| `--max-rate <num>` | Maximum packets sent per second | Hard ceiling — essential for not knocking over fragile embedded/IoT/ICS devices |
| `--min-rtt-timeout` / `--max-rtt-timeout` / `--initial-rtt-timeout` | RTT probe timeout bounds | Tune for high-latency links (VPN pivots, satellite, Tor) instead of accepting false "filtered" results |
| `--host-timeout <time>` | Skip a host entirely after this long | Stops one dead/firewalled host from eating your whole scan window |
| `--scan-delay` / `--max-scan-delay` | Forced delay between probes | Real stealth — evades simple rate-based IDS thresholds far better than `-T1` alone |
| `--min-parallelism` / `--max-parallelism` | Probes in flight simultaneously | Fine-grained alternative to timing templates on congested or lossy networks |

```bash
# Fast internal network, but don't crash the one flaky IoT device on it
sudo nmap -p- --min-rate 2000 --max-rate 5000 --host-timeout 5m 10.0.0.0/24

# Scanning over a slow VPN pivot — stop false "filtered" results from RTT timeouts
sudo nmap -sS --initial-rtt-timeout 500ms --max-rtt-timeout 4s -p 1-1000 172.16.5.10
```

> **Tip — The Rate-Limit Bypass Almost Nobody Uses.** Many Linux hosts and firewalls **rate-limit RST/ICMP unreachable responses** — this makes closed/filtered ports look identical and skews your results without you realising it.
> ```bash
> sudo nmap -sS --defeat-rst-ratelimit -p- 10.10.10.5
> sudo nmap -sU --defeat-icmp-ratelimit --top-ports 200 10.10.10.5
> ```
> 1. **`--defeat-rst-ratelimit`** — keeps probing past a detected RST rate limit instead of assuming "filtered"
> 2. **`--defeat-icmp-ratelimit`** — same idea for UDP scans relying on ICMP port-unreachable
> 3. Without these, a rate-limited Linux target can make an open UDP port look closed/filtered — a classic source of false negatives

---

## Firewall & IDS Evasion

> **Danger — Authorisation Required.** Every technique below changes how your traffic looks to defensive tooling. Only use these within signed RoE scope — evasion outside authorised engagements is a fast way to turn a pentest into a criminal case.

### Non-Standard Scan Types (Exploit RFC 793 Gaps)

| Flag | Scan Type | Why It Evades Simple Filters |
|---|---|---|
| `-sN` | NULL scan (no flags set) | Many stateless ACLs only match SYN/ACK patterns — a flagless packet slips through unnoticed |
| `-sF` | FIN scan | Same idea — closed ports RST, open/filtered stay silent, and it isn't a "connection attempt" to naive logging |
| `-sX` | Xmas scan (FIN+PSH+URG set) | "Lights up like a Christmas tree" — again exploits RFC 793 behaviour most firewalls never account for |
| `-sA` | ACK scan | Doesn't determine open/closed — determines **filtered vs unfiltered**, i.e. maps firewall rule sets directly |
| `-sW` | Window scan | Variant of ACK scan using TCP window size quirks to infer open ports on some stacks |
| `-sM` | Maimon scan | FIN/ACK combo — exploits certain BSD-derived stack behaviour |
| `-sY` / `-sZ` | SCTP INIT / COOKIE-ECHO scan | Almost nobody scans [SCTP](https://en.wikipedia.org/wiki/Stream_Control_Transmission_Protocol) — telecom/signalling and some VoIP infra runs on it and is rarely monitored |
| `-sO` | IP protocol scan | Finds *which protocols* (not ports) a host speaks — reveals hidden GRE tunnels, ESP/IPsec, OSPF |

> **Warning — These Scan Types Need Root and Have Blind Spots.**
> 1. All of `-sN`/`-sF`/`-sX`/`-sM` **require raw socket access** (root/sudo) and only work reliably against Unix-like TCP stacks per RFC 793 — Windows targets typically respond with RST to everything, making results useless there
> 2. These scans **cannot distinguish "open" from "filtered"** — silence means either. Confirm with a normal `-sS` or targeted service probe afterward

### Packet Manipulation

```bash
# Fragment packets — splits the TCP header across multiple IP fragments
sudo nmap -f 10.10.10.5              # 8-byte fragments
sudo nmap -ff 10.10.10.5             # 16-byte fragments (double fragmentation)
sudo nmap --mtu 24 10.10.10.5        # custom fragment size (must be multiple of 8)

# Pad probes with junk data to break simple length-based IDS signatures
sudo nmap --data-length 25 -p 80,443 10.10.10.5

# Set a custom TTL to blend in with expected regional/hop-count profiles
sudo nmap --ttl 128 10.10.10.5

# Spoof or randomise your MAC address on local segments
sudo nmap --spoof-mac 00:11:22:33:44:55 -e eth0 10.10.10.5
sudo nmap --spoof-mac Apple -e eth0 10.10.10.5     # vendor-prefix randomisation
sudo nmap --spoof-mac 0 -e eth0 10.10.10.5         # fully random MAC

# Bad checksum probe — see how the firewall/IDS reacts to intentionally invalid packets
sudo nmap --badsum 10.10.10.5
```

> **Info — Command Breakdown.**
> 1. **`-f` / `-ff` / `--mtu`** — fragmentation defeats older/simple IDS that fail to reassemble packets before signature matching; modern IDS mostly handles this correctly now, but it's a zero-cost addition to an evasion profile
> 2. **`--data-length`** — randomises payload size so probes don't match a fixed-length scan signature
> 3. **`--spoof-mac`** — useful on internal segments where MAC-based NAC/allowlisting exists, or simply to avoid leaving your real NIC vendor fingerprint in switch logs
> 4. **`--badsum`** — a genuine target silently drops these; a host that *does* respond may indicate a security device doing packet processing in a naive way

### Decoys and Source Manipulation

```bash
# Hide your real scan among decoy source IPs
sudo nmap -D RND:10 10.10.10.5
sudo nmap -D decoy1.com,decoy2.com,ME,decoy3.com 10.10.10.5

# Scan from a "trusted" source port — some legacy firewalls allow traffic FROM port 53/20/88
sudo nmap --source-port 53 -p- 10.10.10.5
sudo nmap -g 88 -p 1-1000 10.10.10.5

# Force a specific egress interface on a multi-homed attack box (common on pivots)
sudo nmap -e tun0 10.10.10.5
```

> **Warning — Decoys Are Weaker Than They Used to Be.**
> 1. Modern IDS/SIEM correlates **behaviour and timing patterns**, not just source-IP counts — decoys mainly slow down manual log review now, not automated detection
> 2. Decoy IPs must actually be **up and reachable**, or the target's SYN-ACKs to them generate RSTs that can reveal which "decoy" is fake
> 3. `--source-port` only works against firewalls with genuinely naive "allow if source port = X" rules — increasingly rare but still found on legacy/embedded gear

---

## Idle (Zombie) Scanning

> **Important — How Idle Scan Actually Works.** [Idle scanning (`-sI`)](https://nmap.org/book/idlescan.html) spoofs your source IP as a third-party "zombie" host, then infers port state purely by watching the **zombie's IP ID sequence** increment. The target only ever sees traffic from the zombie — never from you.
> 1. Find a zombie: an idle host with a **predictable, incrementing global IPID sequence** (old printers, embedded devices, unpatched legacy boxes are common candidates)
> 2. Nmap's own `ipidseq` NSE script screens hosts for IPID predictability

```bash
# Step 1: Find a usable zombie on the network
nmap -p80 --script ipidseq 192.168.1.0/24

# Step 2: Run the idle scan through the identified zombie
sudo nmap -sI 192.168.1.50 -p- 10.10.10.5
```

> **Success — When This Is Worth the Setup Effort.**
> 1. Fully deniable scanning — logs on the actual target show the **zombie's** IP, never yours
> 2. Useful for mapping firewall rules from a "trusted internal" vantage point without routing through it directly
> 3. Slow and fragile — busy or NAT'd zombies break the technique; treat it as a specialty tool, not a default workflow

---

## Host Discovery Tricks Beyond a Basic Ping

> **Info — Custom Discovery Probes.** Default `-sn` ping discovery relies on ICMP echo, which is blocked by almost every modern firewall. These flags let you build a discovery probe firewalls don't expect:

```bash
# TCP SYN discovery to specific "probably open" ports instead of ICMP
sudo nmap -sn -PS22,80,443,3389 10.10.10.0/24

# TCP ACK discovery — some stateless firewalls pass ACK packets through
sudo nmap -sn -PA80,443 10.10.10.0/24

# UDP discovery probe (DNS/NTP/SNMP ports often get a response even when ICMP is dead)
sudo nmap -sn -PU53,161 10.10.10.0/24

# SCTP INIT discovery
sudo nmap -sn -PY 10.10.10.0/24

# ICMP variants beyond plain echo
sudo nmap -sn -PE -PP -PM 10.10.10.0/24    # echo, timestamp, netmask requests

# IP protocol ping — useful when ICMP/TCP/UDP are all filtered but other IP protocols aren't
sudo nmap -sn -PO 10.10.10.0/24

# Skip ARP ping on local segments (ARP is usually more reliable, but sometimes you want raw IP-layer behaviour)
sudo nmap -sn --disable-arp-ping 10.10.10.0/24

# Resolve names via a specific DNS server instead of the system resolver
nmap --dns-servers 8.8.8.8,1.1.1.1 -sn 10.10.10.0/24

# Pure target enumeration — resolves/lists targets without sending a single packet to them
nmap -sL 10.10.10.0/24
```

> **Tip — `-sL` Is a Free Sanity Check.** Run `-sL` first on any new CIDR range before touching it with a real scan — it just does reverse-DNS/target-list resolution with **zero packets sent to the targets themselves**. Perfect for validating a scope file has no typos before you burn scan time on it.

---

## Scan Resume, Diffing & Continuous Recon

> **Tip — Resume an Interrupted Scan.** A `-p-` scan against a large range that gets killed (SSH drop, laptop sleep, Ctrl+C) doesn't have to restart from zero:
> ```bash
> nmap -p- -oA big_scan 10.0.0.0/16
> # ...interrupted...
> nmap --resume big_scan.nmap
> ```

> **Example — Diffing Scans Over Time With `ndiff`.** [ndiff](https://nmap.org/ndiff/) ships with Nmap and compares two XML scan results — essential for continuous recon on long engagements or bug bounty monitoring.
> ```bash
> nmap -oX scan_day1.xml 10.10.10.5
> # ...next day...
> nmap -oX scan_day2.xml 10.10.10.5
> ndiff scan_day1.xml scan_day2.xml
> ```
> 1. Highlights newly opened/closed ports, changed service versions, new hosts appearing on a range
> 2. Run this on a cron job against in-scope external ranges during a multi-week engagement to catch new attack surface the moment it appears

### HTML Reporting

```bash
nmap -oX scan.xml 10.10.10.5
xsltproc scan.xml -o scan_report.html
```

> **Info — Command Breakdown.**
> 1. Nmap's XML output ships with a built-in XSL stylesheet reference — `xsltproc` (or any XSLT processor) turns it into a **clickable HTML report** with zero extra tooling
> 2. Great for handing raw scan evidence to a non-technical stakeholder without teaching them to read `.nmap` text output

---

## NSE Tricks Beyond `--script=default,vuln`

> **Info — Debugging and Extending NSE.**
> ```bash
> # See the raw NSE network traffic a script generates — invaluable when a script "hangs" or gives odd results
> nmap --script-trace --script=http-enum -p80 10.10.10.5
>
> # After adding/editing a custom .nse script, refresh Nmap's script database
> nmap --script-updatedb
>
> # Cross-reference every detected service version against a CVE database directly
> nmap -sV --script=vulners 10.10.10.5
> ```
> 1. **`--script-trace`** — shows every packet sent/received by the NSE engine; the fastest way to debug "why is this script timing out"
> 2. **`vulners`** — turns plain version detection into an instant CVE list with CVSS scores; massively underused compared to the generic `vuln` category

> **Example — Scripts That Need NO Target At All.** Several NSE scripts operate purely on **broadcast/multicast traffic** on your local segment — no IP argument required:
> ```bash
> nmap --script broadcast-dhcp-discover
> nmap --script broadcast-ping
> nmap --script llmnr-resolve --script-args 'newtargets,llmnr-resolve.hostname=printer'
> ```
> 1. `broadcast-dhcp-discover` — requests a DHCP lease to reveal DHCP server, gateway, DNS, and lease policy, before you even have an IP configuration
> 2. `broadcast-ping` — finds live hosts via broadcast ping where individual host discovery is filtered
> 3. This category is a goldmine on internal engagements before you've even set a static IP

---

## IPv6 and Protocol-Level Recon

> **Warning — IPv6 Is the Overlooked Attack Surface.**
> 1. Enterprise firewalls and monitoring are frequently **tuned only for IPv4** — the same host can have a wide-open IPv6 stack nobody is watching
> 2. Always test both stacks explicitly:
> ```bash
> nmap -6 -sV fe80::1%eth0
> nmap -6 -sV 2001:db8::1
> ```
> 3. `-sO` (IP protocol scan, shown above) is the easiest way to find **GRE tunnels, IPsec (ESP/AH), OSPF** — infrastructure most port-based scanning never reveals

---

## Companion Tool: Nping

> **Info — [Nping](https://nmap.org/nping/) Overview.** Ships with Nmap. Built for crafting arbitrary raw packets — useful when Nmap's own flags don't give enough control.
> 1. Custom TCP/UDP/ICMP/ARP packet crafting for testing specific firewall rules in isolation
> 2. Can run in `--echo-client`/`--echo-server` mode to test round-trip packet mangling across a path
> 3. Good for building a repeatable, minimal test case to hand to a network team ("this exact packet gets dropped here")

```bash
# Craft a single custom TCP SYN packet to a specific port with custom flags/TTL
nping --tcp -p 443 --flags syn --ttl 64 -c 1 10.10.10.5

# ARP ping a local subnet (faster and more reliable than ICMP on local segments)
sudo nping --arp -c 1 10.10.10.0/24
```

---

## Quick Reference — Flags Almost Nobody Uses

| Flag | Purpose |
|---|---|
| `--stats-every 10s` + spacebar | Live progress without guessing if a scan has hung |
| `--defeat-rst-ratelimit` / `--defeat-icmp-ratelimit` | Fix false "filtered" results from rate-limited targets |
| `--host-timeout` | Don't let one dead host stall an entire range scan |
| `-sO` | Find protocols (GRE/ESP/OSPF), not just ports |
| `-sI` + `ipidseq` | Fully deniable scanning via a zombie host |
| `-sL` | Zero-packet scope/target-list sanity check |
| `--resume` | Never lose progress on a killed `-p-` scan again |
| `ndiff` | Detect new attack surface across long engagements automatically |
| `--script-trace` | Debug NSE scripts that hang or misbehave |
| `--script=vulners` | Instant CVE/CVSS mapping from version detection |
| `broadcast-*` NSE scripts | Enumerate before you even have an IP address |
| `-6` | Test the IPv6 stack nobody else is monitoring |
| `nping` | Craft the one exact packet you need when Nmap's flags aren't granular enough |

---

## References

1. [Nmap Reference Guide](https://nmap.org/book/man.html)
2. [Nmap — Idle Scan (-sI) Documentation](https://nmap.org/book/idlescan.html)
3. [Nmap — Firewall/IDS Evasion and Spoofing](https://nmap.org/book/man-bypass-firewalls-ids.html)
4. [ndiff — Nmap Scan Comparison Tool](https://nmap.org/ndiff/)
5. [Nping Reference Guide](https://nmap.org/nping/)
6. [NSE Documentation Portal](https://nmap.org/nsedoc/)
7. [Vulners NSE Script](https://nmap.org/nsedoc/scripts/vulners.html)
