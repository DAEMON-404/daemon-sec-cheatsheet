---
title: "RDP"
description: "export RDP=sdl-freerdp"
category: linux-it
tags: ["linux-it", "adcs"]
tools: []
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Linux/RDP CheatSheet.md"
---
# macOS: native SDL client (recommended)
export RDP=sdl-freerdp

# Linux examples:
# export RDP=xfreerdp3
# export RDP=xfreerdp

export TARGET='10.10.10.10'
export DOMAIN='DOMAIN'
export USER='username'
```

> [!tip]+ Secure baseline `ris:ShieldCheck`
> `ris:Command`
> 1. `/from-stdin:force` prompts before connecting, keeping the password out of shell history and process arguments.
> 2. `/cert:tofu` trusts a certificate on the first connection, then rejects an unexpected change.
> 3. `+dynamic-resolution` keeps the session usable when the client window is resized.

```bash
"$RDP" /v:"$TARGET" /d:"$DOMAIN" /u:"$USER" \
  /from-stdin:force /cert:tofu +dynamic-resolution
```

---

## // CONNECTION_&_AUTHENTICATION `ris:LockPassword`

### 1. Identity formats

| Identity type | Example |
|---|---|
| Local account | `/u:Administrator` |
| Domain account | `/d:DOMAIN /u:username` |
| Down-level domain name | `/u:'DOMAIN\username'` |
| User principal name | `/u:'user@domain.example'` |

```bash
# Local account
"$RDP" /v:"$TARGET" /u:Administrator /from-stdin:force /cert:tofu

# Domain account
"$RDP" /v:"$TARGET" /d:"$DOMAIN" /u:"$USER" /from-stdin:force /cert:tofu

# UPN
"$RDP" /v:"$TARGET" /u:'user@domain.example' /from-stdin:force /cert:tofu
```

> [!warning]+ Avoid inline passwords `fas:TriangleExclamation`
> `/p:<password>` is supported, but the password can end up in shell history, terminal scrollback, process listings, screenshots, and copied commands. Use `/from-stdin:force` unless a disposable authorised lab requires otherwise.

### 2. Kerberos and smart-card authentication

```bash
# Use an existing Kerberos ticket cache
kinit 'user@DOMAIN.EXAMPLE'
"$RDP" /v:"$TARGET" /u:'user@DOMAIN.EXAMPLE' \
  /sec:nla /kerberos:cache:"$KRB5CCNAME" /cert:tofu

# Smart-card logon (the reader/card must be available locally)
"$RDP" /v:"$TARGET" /smartcard-logon /sec:nla /cert:tofu
```

> [!info]+ Authentication notes `ris:FileList`
> `ris:LockPassword`
> 1. `/sec:nla` explicitly requires Network Level Authentication and disables weaker alternatives.
> 2. Kerberos depends on DNS, realm configuration, and clock alignment; inspect the ticket with `klist` before troubleshooting RDP itself.
> 3. Smart-card logon activates the local reader; it is distinct from `/smartcard`, which redirects a smart card into an already authenticated remote session.

### 3. Pass-the-hash — authorised lab/admin use only

```bash
export NT_HASH='0123456789ABCDEF0123456789ABCDEF'
"$RDP" /v:"$TARGET" /u:Administrator /pth:"$NT_HASH" \
  +restricted-admin /cert:tofu
```

> [!danger]+ Credential material `fas:Skull`
> A hash is credential material. Use this only with explicit authority, do not save it in the note, and clear the variable with `unset NT_HASH` when finished. Restricted Admin mode must be permitted by the target policy.

---

## // TRANSPORT_&_CERTIFICATE_SECURITY `ris:ShieldCheck`

| Goal | Option | When to use it |
|---|---|---|
| Secure default | `/cert:tofu` | First connection to a known target; detects later certificate changes |
| Pin known certificate | `/cert:fingerprint:sha256:<hex>` | You have a verified SHA-256 fingerprint from a trusted channel |
| Fail on mismatch | `/cert:deny` | Strict environments that should never prompt |
| Require NLA | `/sec:nla` | Normal domain or local-account RDP |
| TLS without NLA | `/sec:tls` | Only when the target intentionally does not require NLA |
| Legacy RDP security | `/sec:rdp` | Legacy, authorised compatibility testing only |

```bash
# Pin a certificate fingerprint received through a trusted channel
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force \
  /cert:fingerprint:sha256:<hex_fingerprint>

# Require NLA and TLS 1.2 or newer where the target requires an explicit floor
"$RDP" /v:"$TARGET" /d:"$DOMAIN" /u:"$USER" /from-stdin:force \
  /sec:nla /tls:enforce:1.2 /cert:tofu
```

> [!danger]+ Never make this the default `fas:TriangleExclamation`
> `/cert:ignore` disables certificate validation and makes a rogue or intercepted server much harder to detect. Use it only in a disposable, explicitly authorised lab when certificate validation is the subject of the test.

---

## // DISPLAY_&_PERFORMANCE `ris:Global`

### 1. Display and window controls

```bash
# Fullscreen; Ctrl+Alt+Enter toggles back to a window
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu +f

# Fixed initial size, then allow resize-driven updates
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu \
  /size:1600x1000 +dynamic-resolution

# Use 80% of display height or scale the rendered desktop
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu /size:80%h
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu /scale:140

# Multiple displays or selected display IDs (list IDs with /list:monitor)
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu /multimon
"$RDP" /list:monitor
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu /monitors:0,1
```

### 2. Low-bandwidth profile

```bash
"$RDP" /v:"$TARGET" /d:"$DOMAIN" /u:"$USER" /from-stdin:force \
  /cert:tofu /network:modem /compression-level:2 \
  -wallpaper -themes -menu-anims -fonts /gdi:sw
```

### 3. High-quality workstation profile

```bash
"$RDP" /v:"$TARGET" /d:"$DOMAIN" /u:"$USER" /from-stdin:force \
  /cert:tofu +f +dynamic-resolution /gdi:hw \
  /gfx:progressive:on,AVC444:on /network:lan
```

> [!tip]+ Performance tuning `fas:Lightbulb`
> 1. Start with `/network:auto` or `/network:lan`; move toward `/network:modem` only when the connection is genuinely constrained.
> 2. Disable wallpaper, themes, animations, and smooth fonts before compromising authentication or certificate checks.
> 3. If hardware rendering misbehaves, use `/gdi:sw` as a compatibility fallback.

---

## // LOCAL_RESOURCE_REDIRECTION `ris:ShareBox`

### 1. Clipboard and drives

```bash
# Disable clipboard redirection for sensitive sessions
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu -clipboard

# Redirect one selected directory as a named remote share
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu \
  /drive:Share,"$PWD"

# Redirect the home directory or every mounted filesystem
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu +home-drive
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu +drives

# Permit hot-plugged removable drives
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu /drive:hotplug,*
```

### 2. Audio, printers, smart cards, and USB

```bash
# Audio output and microphone input
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu /sound /microphone

# Redirect a printer or smart card into the session
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu /printer
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu /smartcard

# Redirect a USB device by vendor and product ID
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu /usb:id:1234:5678
```

> [!warning]+ Data-boundary check `fas:TriangleExclamation`
> Clipboard, drive, USB, printer, microphone, and smart-card redirection expand the trust boundary between your machine and the remote host. Enable only the one feature you need and disable it for untrusted or assessment targets.

---

## // GATEWAYS_PROXY_&_REMOTEAPP `ris:GlobalLine`

```bash
# RD Gateway; omit /p: values so FreeRDP prompts for required credentials
export GATEWAY='rdgateway.example.com'
export GW_USER='gateway-user'
"$RDP" /v:"$TARGET" /d:"$DOMAIN" /u:"$USER" /from-stdin:force \
  /gateway:g:"$GATEWAY",u:"$GW_USER",d:"$DOMAIN",usage-method:detect \
  /cert:tofu

# HTTP or SOCKS5 proxy
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu \
  /proxy:http://proxy.example.com:8080
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu \
  /proxy:socks5://127.0.0.1:1080

# A gateway also honours an HTTPS proxy set in the environment
export https_proxy='http://proxy.example.com:3128'
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force \
  /gateway:g:"$GATEWAY" /cert:tofu

# RemoteApp example
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu \
  /app:program:'||notepad',name:'Notepad'
```

> [!info]+ Gateway credentials `ris:LockPassword`
> A gateway can use credentials different from the target. Keep gateway passwords out of the command line too; FreeRDP prompts when the relevant `/p:` value is omitted.

---

## // SESSION_CONTROL_&_TROUBLESHOOTING `ris:Command`

| Symptom or task | Command / response |
|---|---|
| Confirm the installed version | `"$RDP" /version` |
| Inspect locally supported options | `"$RDP" /help` |
| Find available display IDs | `"$RDP" /list:monitor` |
| Test authentication without opening a desktop | Add `+auth-only` |
| Reconnect after a transient drop | Add `+auto-reconnect /auto-reconnect-max-retries:10` |
| Keep an authorised session awake | Add `/prevent-session-lock:300` |
| Release keyboard/mouse grab | Press `Right Ctrl` |
| Toggle fullscreen | Press `Ctrl+Alt+Enter` |
| Minimise the session | Press `Ctrl+Alt+M` |

```bash
# Verify credentials and transport without starting the GUI desktop
"$RDP" /v:"$TARGET" /d:"$DOMAIN" /u:"$USER" /from-stdin:force \
  /cert:tofu +auth-only

# Reconnect a flaky authorised session, up to ten times
"$RDP" /v:"$TARGET" /u:"$USER" /from-stdin:force /cert:tofu \
  +auto-reconnect /auto-reconnect-max-retries:10
```

> [!failure]+ Common fixes `fas:CircleXmark`
> 1. **`$DISPLAY` error on macOS:** use `sdl-freerdp`, or install and start XQuartz before using `xfreerdp`.
> 2. **Certificate changed:** stop and verify the server identity through a trusted channel; do not switch to `/cert:ignore` just to connect.
> 3. **NLA / Kerberos failure:** verify DNS, target time, realm configuration, and the ticket cache with `klist`.
> 4. **Option rejected:** your package may differ from this reference; use `"$RDP" /help` and update the client.

---

## // MACOS_INSTALL `fas:Apple`

```bash
# Homebrew installs FreeRDP 3.30.0, including sdl-freerdp and xfreerdp
brew update
brew install freerdp

# Only required when using the X11 client (xfreerdp)
brew install --cask xquartz
open -a XQuartz

# Verify both available clients
sdl-freerdp /version
xfreerdp /version
```

> [!success]+ macOS client choice `ris:CheckboxCircle`
> Use `sdl-freerdp` by default on macOS. The Homebrew formula builds the SDL client, while its `xfreerdp` client requires a running X11 server and otherwise produces a `$DISPLAY` error.

---

## // LESSONS_LEARNED `fas:Lightbulb`

1. Set the client, target, domain, and user once; then every recipe remains copy-ready across macOS and Linux.
2. Prefer `/from-stdin:force` and `/cert:tofu`; a convenient command should not weaken credential or server authentication.
3. Treat clipboard, drive, device, audio, and smart-card redirection as deliberate data-sharing decisions.
4. Use `+auth-only` to separate authentication and certificate failures from GUI/display problems.
5. FreeRDP packages differ by platform; `"$RDP" /help` is the local source of truth.

---

## // REFERENCES `fas:BookOpen`

1. [FreeRDP project](https://www.freerdp.com/)
2. [FreeRDP 3.30.0 release](https://github.com/FreeRDP/FreeRDP/releases/tag/3.30.0)
3. [FreeRDP macOS installation guidance](https://github.com/FreeRDP/FreeRDP/wiki/Prebuilds)
4. [Homebrew `freerdp` formula](https://formulae.brew.sh/formula/freerdp)
5. [Homebrew formula source — enabled X11 and SDL clients](https://github.com/Homebrew/homebrew-core/blob/HEAD/Formula/f/freerdp.rb)

#Cheatsheet #CommandReference #RDP #FreeRDP #RemoteAccess #Windows
