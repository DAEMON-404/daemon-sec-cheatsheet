---
title: "Mercurial"
topic: "Insecure Source Code Management"
topicSlug: "insecure-source-code-management"
sourcePath: "Insecure Source Code Management/Mercurial.md"
sourceUrl: "https://github.com/swisskyrepo/PayloadsAllTheThings/blob/3bff425aca2b/Insecure%20Source%20Code%20Management/Mercurial.md"
sha: "3bff425aca2b"
isReadme: false
---

# Mercurial

> Mercurial  (also known as hg  from the chemical symbol for mercury) is a distributed version control system (DVCS) designed for efficiency and scalability. Developed by Matt Mackall and first released in 2005, Mercurial is known for its speed, simplicity, and ability to handle large codebases.

## Summary

* [Tools](#tools)
    * [rip-hg.pl](#rip-hgpl)
* [References](#references)

## Tools

### rip-hg.pl

* [kost/dvcs-ripper/master/rip-hg.pl](https://raw.githubusercontent.com/kost/dvcs-ripper/master/rip-hg.pl) - Rip web accessible (distributed) version control systems: SVN/GIT/HG...

    ```powershell
    docker run --rm -it -v /path/to/host/work:/work:rw k0st/alpine-dvcs-ripper rip-hg.pl -v -u
    ```

## References

* [my-chemical-romance - siunam - February 13, 2023](https://web.archive.org/web/20250712102012/https://siunam321.github.io/ctf/LA-CTF-2023/Web/my-chemical-romance/)
