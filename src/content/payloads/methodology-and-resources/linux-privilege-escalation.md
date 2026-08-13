---
title: "Linux - Privilege Escalation"
topic: "Methodology and Resources"
topicSlug: "methodology-and-resources"
sourcePath: "Methodology and Resources/Linux - Privilege Escalation.md"
sourceUrl: "https://github.com/swisskyrepo/PayloadsAllTheThings/blob/3bff425aca2b/Methodology%20and%20Resources/Linux%20-%20Privilege%20Escalation.md"
sha: "3bff425aca2b"
isReadme: false
---

# Linux - Privilege Escalation

:warning: Content of this page has been moved to [InternalAllTheThings/redteam/persistence/linux-persistence](/internal/redteam/escalation/linux-privilege-escalation)

- [Tools](/internal/redteam/escalation/linux-privilege-escalation#tools)
- [Checklist](/internal/redteam/escalation/linux-privilege-escalation#checklists)
- [Looting for passwords](/internal/redteam/escalation/linux-privilege-escalation#looting-for-passwords)
    - [Files containing passwords](/internal/redteam/escalation/linux-privilege-escalation#files-containing-passwords)
    - [Old passwords in /etc/security/opasswd](/internal/redteam/escalation/linux-privilege-escalation#old-passwords-in-etcsecurityopasswd)
    - [Last edited files](/internal/redteam/escalation/linux-privilege-escalation#last-edited-files)
    - [In memory passwords](/internal/redteam/escalation/linux-privilege-escalation#in-memory-passwords)
    - [Find sensitive files](/internal/redteam/escalation/linux-privilege-escalation#find-sensitive-files)
- [SSH Key](/internal/redteam/escalation/linux-privilege-escalation#ssh-key)
    - [Sensitive files](/internal/redteam/escalation/linux-privilege-escalation#sensitive-files)
    - [SSH Key Predictable PRNG (Authorized_Keys) Process](/internal/redteam/escalation/linux-privilege-escalation#ssh-key-predictable-prng-authorized_keys-process)
- [Scheduled tasks](/internal/redteam/escalation/linux-privilege-escalation#scheduled-tasks)
    - [Cron jobs](/internal/redteam/escalation/linux-privilege-escalation#cron-jobs)
    - [Systemd timers](/internal/redteam/escalation/linux-privilege-escalation#systemd-timers)
- [SUID](/internal/redteam/escalation/linux-privilege-escalation#suid)
    - [Find SUID binaries](/internal/redteam/escalation/linux-privilege-escalation#find-suid-binaries)
    - [Create a SUID binary](/internal/redteam/escalation/linux-privilege-escalation#create-a-suid-binary)
- [Capabilities](/internal/redteam/escalation/linux-privilege-escalation#capabilities)
    - [List capabilities of binaries](/internal/redteam/escalation/linux-privilege-escalation#list-capabilities-of-binaries)
    - [Edit capabilities](/internal/redteam/escalation/linux-privilege-escalation#edit-capabilities)
    - [Interesting capabilities](/internal/redteam/escalation/linux-privilege-escalation#interesting-capabilities)
- [SUDO](/internal/redteam/escalation/linux-privilege-escalation#sudo)
    - [NOPASSWD](/internal/redteam/escalation/linux-privilege-escalation#nopasswd)
    - [LD_PRELOAD and NOPASSWD](/internal/redteam/escalation/linux-privilege-escalation#ld_preload-and-nopasswd)
    - [Doas](/internal/redteam/escalation/linux-privilege-escalation#doas)
    - [sudo_inject](/internal/redteam/escalation/linux-privilege-escalation#sudo_inject)
    - [CVE-2019-14287](/internal/redteam/escalation/linux-privilege-escalation#cve-2019-14287)
- [GTFOBins](/internal/redteam/escalation/linux-privilege-escalation#gtfobins)
- [Wildcard](/internal/redteam/escalation/linux-privilege-escalation#wildcard)
- [Writable files](/internal/redteam/escalation/linux-privilege-escalation#writable-files)
    - [Writable /etc/passwd](/internal/redteam/escalation/linux-privilege-escalation#writable-etcpasswd)
    - [Writable /etc/sudoers](/internal/redteam/escalation/linux-privilege-escalation#writable-etcsudoers)
- [NFS Root Squashing](/internal/redteam/escalation/linux-privilege-escalation#nfs-root-squashing)
- [Shared Library](/internal/redteam/escalation/linux-privilege-escalation#shared-library)
    - [ldconfig](/internal/redteam/escalation/linux-privilege-escalation#ldconfig)
    - [RPATH](/internal/redteam/escalation/linux-privilege-escalation#rpath)
- [Groups](/internal/redteam/escalation/linux-privilege-escalation#groups)
    - [Docker](/internal/redteam/escalation/linux-privilege-escalation#docker)
    - [LXC/LXD](/internal/redteam/escalation/linux-privilege-escalation#lxclxd)
- [Hijack TMUX session](/internal/redteam/escalation/linux-privilege-escalation#hijack-tmux-session)
- [Kernel Exploits](/internal/redteam/escalation/linux-privilege-escalation#kernel-exploits)
    - [CVE-2022-0847 (DirtyPipe)](/internal/redteam/escalation/linux-privilege-escalation#cve-2022-0847-dirtypipe)
    - [CVE-2016-5195 (DirtyCow)](/internal/redteam/escalation/linux-privilege-escalation#cve-2016-5195-dirtycow)
    - [CVE-2010-3904 (RDS)](/internal/redteam/escalation/linux-privilege-escalation#cve-2010-3904-rds)
    - [CVE-2010-4258 (Full Nelson)](/internal/redteam/escalation/linux-privilege-escalation#cve-2010-4258-full-nelson)
    - [CVE-2012-0056 (Mempodipper)](/internal/redteam/escalation/linux-privilege-escalation#cve-2012-0056-mempodipper)
