---
title: "Reverse Shell Cheat Sheet"
topic: "Methodology and Resources"
topicSlug: "methodology-and-resources"
sourcePath: "Methodology and Resources/Reverse Shell Cheatsheet.md"
sourceUrl: "https://github.com/swisskyrepo/PayloadsAllTheThings/blob/3bff425aca2b/Methodology%20and%20Resources/Reverse%20Shell%20Cheatsheet.md"
sha: "3bff425aca2b"
isReadme: false
---

# Reverse Shell Cheat Sheet

:warning: Content of this page has been moved to [InternalAllTheThings/cheatsheet/shell-reverse](/internal/cheatsheets/shell-reverse-cheatsheet)

- [Tools](/internal/cheatsheets/shell-reverse-cheatsheet#tools)
- [Reverse Shell](/internal/cheatsheets/shell-reverse-cheatsheet#reverse-shell)
    - [Awk](/internal/cheatsheets/shell-reverse-cheatsheet#awk)
    - [Automatic Reverse Shell Generator](/internal/cheatsheets/shell-reverse-cheatsheet#revshells)
    - [Bash TCP](/internal/cheatsheets/shell-reverse-cheatsheet#bash-tcp)
    - [Bash UDP](/internal/cheatsheets/shell-reverse-cheatsheet#bash-udp)
    - [C](/internal/cheatsheets/shell-reverse-cheatsheet#c)
    - [Dart](/internal/cheatsheets/shell-reverse-cheatsheet#dart)
    - [Golang](/internal/cheatsheets/shell-reverse-cheatsheet#golang)
    - [Groovy Alternative 1](/internal/cheatsheets/shell-reverse-cheatsheet#groovy-alternative-1)
    - [Groovy](/internal/cheatsheets/shell-reverse-cheatsheet#groovy)
    - [Java Alternative 1](/internal/cheatsheets/shell-reverse-cheatsheet#java-alternative-1)
    - [Java Alternative 2](/internal/cheatsheets/shell-reverse-cheatsheet#java-alternative-2)
    - [Java](/internal/cheatsheets/shell-reverse-cheatsheet#java)
    - [Lua](/internal/cheatsheets/shell-reverse-cheatsheet#lua)
    - [Ncat](/internal/cheatsheets/shell-reverse-cheatsheet#ncat)
    - [Netcat OpenBsd](/internal/cheatsheets/shell-reverse-cheatsheet#netcat-openbsd)
    - [Netcat BusyBox](/internal/cheatsheets/shell-reverse-cheatsheet#netcat-busybox)
    - [Netcat Traditional](/internal/cheatsheets/shell-reverse-cheatsheet#netcat-traditional)
    - [NodeJS](/internal/cheatsheets/shell-reverse-cheatsheet#nodejs)
    - [OGNL](/internal/cheatsheets/shell-reverse-cheatsheet#ognl)
    - [OpenSSL](/internal/cheatsheets/shell-reverse-cheatsheet#openssl)
    - [Perl](/internal/cheatsheets/shell-reverse-cheatsheet#perl)
    - [PHP](/internal/cheatsheets/shell-reverse-cheatsheet#php)
    - [Powershell](/internal/cheatsheets/shell-reverse-cheatsheet#powershell)
    - [Python](/internal/cheatsheets/shell-reverse-cheatsheet#python)
    - [Ruby](/internal/cheatsheets/shell-reverse-cheatsheet#ruby)
    - [Rust](/internal/cheatsheets/shell-reverse-cheatsheet#rust)
    - [Socat](/internal/cheatsheets/shell-reverse-cheatsheet#socat)
    - [Telnet](/internal/cheatsheets/shell-reverse-cheatsheet#telnet)
    - [War](/internal/cheatsheets/shell-reverse-cheatsheet#war)
- [Meterpreter Shell](/internal/cheatsheets/shell-reverse-cheatsheet#meterpreter-shell)
    - [Windows Staged reverse TCP](/internal/cheatsheets/shell-reverse-cheatsheet#windows-staged-reverse-tcp)
    - [Windows Stageless reverse TCP](/internal/cheatsheets/shell-reverse-cheatsheet#windows-stageless-reverse-tcp)
    - [Linux Staged reverse TCP](/internal/cheatsheets/shell-reverse-cheatsheet#linux-staged-reverse-tcp)
    - [Linux Stageless reverse TCP](/internal/cheatsheets/shell-reverse-cheatsheet#linux-stageless-reverse-tcp)
    - [Other platforms](/internal/cheatsheets/shell-reverse-cheatsheet#other-platforms)
- [Spawn TTY Shell](/internal/cheatsheets/shell-reverse-cheatsheet#spawn-tty-shell)
- [References](/internal/cheatsheets/shell-reverse-cheatsheet#references)
