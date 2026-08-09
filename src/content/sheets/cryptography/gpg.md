---
title: "GPG"
description: "GnuPG keys, encryption/decryption, signing/verification, keyservers, trust and revocation."
category: cryptography
tags: [cryptography, encryption, pgp]
tools: [GPG, GnuPG]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:Cryptography/GPG - Cheatsheet markdown.md"
---

# GPG

```dataviewjs
await dv.view("00Meta/Views/NoteBanner");
```

---

> **Note —** + `> ABOUT_THIS_NOTE`
> Advanced, copy-ready [GnuPG](https://www.gnupg.org/) reference for local key management, signing, encryption, verification, and automation. Examples favour full fingerprints, explicit signing identities, and deliberate recipient lists. Commands were checked against the installed **GnuPG 2.5.21** client.

> **Note —** + `> SAFETY_BOUNDARY`
> `ris:ShieldCheck`
> 1. A fingerprint identifies a key; it is safe to share after independent verification. A private key, passphrase, decrypted data, and private-key backup are not.
> 2. Never delete a secret key before an encrypted offline backup and revocation certificate exist.
> 3. Keyservers are effectively append-only. Revoking a compromised published key is possible; reliably removing it from all keyservers is not.

---

## // ADVANCED_OPERATOR_QUICKSTART `fas:ClipboardList`

### 1. Use full fingerprints and explicit identities

```bash
# Replace every placeholder with a full 40-hex-character OpenPGP fingerprint.
export YOUR_FPR='0123456789ABCDEF0123456789ABCDEF01234567'
export RECIPIENT_FPR='89ABCDEF0123456789ABCDEF0123456789ABCDEF'

# Show the secret keys that can sign and public keys that can encrypt.
gpg --list-secret-keys --keyid-format LONG --with-fingerprint
gpg --list-keys --keyid-format LONG --with-fingerprint
```

> **Note —** + Why fingerprints matter `fas:Lightbulb`
> `ris:LockPassword`
> A short key ID is not a unique trust anchor. Verify a full fingerprint through an independent channel, then use that fingerprint with `--local-user` (`-u`) and `--recipient` (`-r`).

### 2. Sign with a non-default private key

```bash
# Detached, ASCII-armored signature: creates file.pdf.asc
gpg --local-user "$YOUR_FPR" --detach-sign --armor file.pdf

# Detached binary signature: creates file.pdf.sig
gpg --local-user "$YOUR_FPR" --detach-sign file.pdf

# Embedded binary signature: creates file.pdf.gpg
gpg --local-user "$YOUR_FPR" --sign file.pdf

# Human-readable cleartext signature: creates message.txt.asc
gpg --local-user "$YOUR_FPR" --clearsign message.txt
```

> **Note —** + Signing selection `ris:FileList`
> `ris:Command`
> 1. `--local-user` / `-u` chooses the signing identity and overrides `default-key`.
> 2. `--detach-sign` keeps the original file unchanged and is the normal choice for software artifacts.
> 3. `--armor` produces portable text output; omit it for compact binary output.

### 3. Encrypt to explicit public keys

```bash
# Binary encrypted output: creates file.pdf.gpg
gpg --recipient "$RECIPIENT_FPR" --encrypt file.pdf

# ASCII-armored encrypted output: creates file.pdf.asc
gpg --recipient "$RECIPIENT_FPR" --armor --encrypt file.pdf

# Encrypt to several people; each listed recipient can decrypt.
gpg --recipient "$RECIPIENT_FPR" \
  --recipient "$YOUR_FPR" \
  --armor --encrypt file.pdf
```

> **Note —** + Include yourself deliberately `fas:TriangleExclamation`
> Encryption only includes the recipients you specify, plus any separately configured `encrypt-to` recipient. If you encrypt only to someone else, you may be unable to decrypt your own output later. Add your verified encryption-capable key as another `--recipient` when you need future access.

### 4. Encrypt and sign with different keys

```bash
# Sign as YOUR_FPR; encrypt only for the recipient.
gpg --local-user "$YOUR_FPR" \
  --recipient "$RECIPIENT_FPR" \
  --sign --encrypt file.pdf

# Sign as YOUR_FPR; encrypt for the recipient and yourself.
gpg --local-user "$YOUR_FPR" \
  --recipient "$RECIPIENT_FPR" \
  --recipient "$YOUR_FPR" \
  --armor --sign --encrypt file.pdf
```

### 5. Verify and decrypt safely

```bash
# Verify a detached signature against its original file.
gpg --verify file.pdf.asc file.pdf

# Verify an embedded signature.
gpg --verify signed-file.gpg

# Decrypt to a deliberate output path.
gpg --output decrypted-file.pdf --decrypt file.pdf.gpg
```

> **Note —** + What a successful verification proves `ris:CheckboxCircle`
> A good signature proves that a matching private key signed the bytes you verified. It does **not** establish a real-world identity until you have independently verified the signing key’s fingerprint and trust context.

---

## // DEFAULT_KEY_&_RECIPIENT_CONTROL `ris:LockPassword`

### 1. Understand the four settings

| Setting | Effect | Prefer for intentional workflows |
|---|---|---|
| `default-key <FPR>` | Default signing identity when `--local-user` is omitted | Explicit `--local-user "$YOUR_FPR"` |
| `default-recipient <FPR>` | Encrypts to this key when `--recipient` is omitted | Explicit `--recipient "$RECIPIENT_FPR"` |
| `default-recipient-self` | Uses the default signing key as encryption recipient when recipients are omitted | Add your own `--recipient "$YOUR_FPR"` explicitly |
| `encrypt-to <FPR>` | Always adds this recipient to encryption, even when `--recipient` is supplied | Explicit recipient list when you need predictable output |

### 2. Remove a configured default key without deleting the key

```bash
# Locate the active GnuPG home and open the primary configuration file.
gpgconf --list-dirs homedir
"${EDITOR:-vi}" "$(gpgconf --list-dirs homedir)/gpg.conf"
```

Remove or comment out each directive you do not want, for example:

```conf
# default-key 0123456789ABCDEF0123456789ABCDEF01234567
# default-recipient 0123456789ABCDEF0123456789ABCDEF01234567
# default-recipient-self
# encrypt-to 0123456789ABCDEF0123456789ABCDEF01234567
```

```bash
# Inspect the defaults reported by the current configuration.
gpgconf --list-options gpg | grep -E '^(default-key|default-recipient|encrypt-to):'

# One-command override: disable recipient defaults for this invocation only.
gpg --no-default-recipient --recipient "$RECIPIENT_FPR" --encrypt file.pdf
```

> **Note —** + Removing a default is not deleting a key `fas:TriangleExclamation`
> 1. Removing `default-key` only clears the configured signing preference. If you omit `--local-user`, GnuPG can still fall back to the first usable secret key.
> 2. `--no-default-recipient` resets `default-recipient` and `default-recipient-self` for one command; do **not** put it in `gpg.conf`.
> 3. For repeatable work, always specify both the signer and every intended recipient on the command line.

### 3. Delete a key from the local keyring — separate, destructive action

```bash
# First: create an encrypted secret-key backup and an offline revocation certificate.
gpg --armor --output "${YOUR_FPR}.secret.asc" --export-secret-keys "$YOUR_FPR"
gpg --output "${YOUR_FPR}.revocation.asc" --generate-revocation "$YOUR_FPR"

# Review the exact fingerprint, then remove the local secret and public key.
gpg --fingerprint "$YOUR_FPR"
gpg --delete-secret-and-public-key "$YOUR_FPR"
```

> **Note —** + Deletion checklist `fas:Skull`
> 1. Store the exported private key and revocation certificate offline, encrypted, and separately from the passphrase.
> 2. Deletion removes the key from this local keyring; it does not retract a public key already uploaded to a keyserver.
> 3. If the key is compromised rather than simply unused, publish the revocation certificate after validating its contents.

---

## // SCRIPTING_&_ISOLATED_KEYRINGS `fas:Terminal`

### 1. Machine-readable listings and status output

```bash
# Stable machine-readable key listing; do not parse the human-facing --list-keys output.
gpg --batch --with-colons --with-fingerprint --list-keys "$RECIPIENT_FPR"

# Capture structured status lines while verifying a detached signature.
gpg --batch --status-fd 1 --verify file.pdf.asc file.pdf 2>/dev/null
```

### 2. Test an import in a disposable GnuPG home

```bash
export TEST_GNUPGHOME="$(mktemp -d)"
chmod 700 "$TEST_GNUPGHOME"

gpg --homedir "$TEST_GNUPGHOME" --import candidate-key.asc
gpg --homedir "$TEST_GNUPGHOME" --with-fingerprint --list-keys

# Remove this temporary directory only after reviewing the imported key.
if [ -n "$TEST_GNUPGHOME" ] && [ -d "$TEST_GNUPGHOME" ]; then
  rm -rf -- "$TEST_GNUPGHOME"
fi
unset TEST_GNUPGHOME
```

> **Note —** + Automation rules `ris:Radar`
> Use `--batch`, `--status-fd`, and `--with-colons` for scripts. Do not feed passphrases on the command line; use a controlled pinentry, agent, or a carefully designed file descriptor workflow instead.

---

## Quick Reference Command Matrix

**This table summarizes ALL GPG operations covered in this cheatsheet.**

> **Note —** - 📋 Quick Reference Cheat Sheet
> | # | Category | Command | Purpose | Key Flags |
> |:--|:---|:---|:---|:---|
> | 1 | Key Generation | `gpg --gen-key` | Generate new key pair (simplified) | Interactive prompts |
> | 2 | Key Generation | `gpg --full-generate-key` | Generate key with full options | Choose algorithm, size, expiry |
> | 3 | Key Generation | `gpg --quick-generate-key "Name <email>" ed25519 sign 1y` | Generate Ed25519 key programmatically | Modern algorithm |
> | 4 | Key Listing | `gpg --list-keys` | List all public keys | Alias: `gpg -k` |
> | 5 | Key Listing | `gpg --list-secret-keys` | List all private keys | Alias: `gpg -K` |
> | 6 | Key Listing | `gpg --list-keys --keyid-format long` | List keys with long IDs | Shows full key IDs |
> | 7 | Key Export | `gpg --export -a <key-id>` | Export public key (ASCII) | `-a` = armor (text format) |
> | 8 | Key Export | `gpg --export-secret-keys -a <key-id>` | Export private key (ASCII) | **Keep secure!** |
> | 9 | Key Import | `gpg --import <file>` | Import key from file | Public or private |
> | 10 | Key Import | `gpg --recv-keys <key-id>` | Download key from keyserver | Requires keyserver config |
> | 11 | Key Upload | `gpg --send-keys <key-id>` | Upload key to keyserver | Makes key discoverable |
> | 12 | Key Search | `gpg --search-keys "email@example.com"` | Search keyserver for key | Requires keyserver |
> | 13 | Key Deletion | `gpg --delete-key <key-id>` | Delete public key | Cannot have secret key |
> | 14 | Key Deletion | `gpg --delete-secret-key <key-id>` | Delete private key | Must be done first |
> | 15 | Key Editing | `gpg --edit-key <key-id>` | Interactive key editor | Commands: trust, expire, passwd |
> | 16 | Key Info | `gpg --fingerprint <key-id>` | Show key fingerprint | For verification |
> | 17 | Encryption (Asymmetric) | `gpg -e -r <recipient> <file>` | Encrypt file for recipient | Creates `.gpg` file |
> | 18 | Encryption (Asymmetric) | `gpg -e -a -r <recipient> <file>` | Encrypt with ASCII armor | Creates `.asc` file |
> | 19 | Encryption (Symmetric) | `gpg -c <file>` | Encrypt with passphrase | No keys needed |
> | 20 | Encryption (Symmetric) | `gpg -c --armor <file>` | Symmetric encryption (ASCII) | Password-based |
> | 21 | Decryption | `gpg -d <file>` | Decrypt file to stdout | Displays decrypted content |
> | 22 | Decryption | `gpg -o <output> -d <file>` | Decrypt to specific file | `-o` = output path |
> | 23 | Signing (Binary) | `gpg -s <file>` | Sign file (binary format) | Creates `.gpg` |
> | 24 | Signing (Clear) | `gpg --clearsign <file>` | Sign with readable message | Creates `.asc` |
> | 25 | Signing (Detached) | `gpg -b <file>` | Create detached signature | Creates `.sig` |
> | 26 | Signing (Detached ASCII) | `gpg -b -a <file>` | Detached signature (ASCII) | Creates `.asc` |
> | 27 | Sign + Encrypt | `gpg -se -r <recipient> <file>` | Sign then encrypt | Combined operation |
> | 28 | Verification | `gpg --verify <file>` | Verify embedded signature | Checks authenticity |
> | 29 | Verification | `gpg --verify <sig> <file>` | Verify detached signature | Two separate files |
> | 30 | Revocation | `gpg --gen-revoke --output revoke.asc <key-id>` | Generate revocation certificate | Create immediately |
> | 31 | Trust Management | `gpg --update-trustdb` | Rebuild trust database | After key changes |
> | 32 | Agent Control | `gpgconf --kill gpg-agent` | Restart GPG agent | Fix cache issues |
> | 33 | Configuration | `gpg --list-config` | Show configured options | Debugging |
> | 34 | Diagnostics | `gpg --check-trustdb` | Check trust database integrity | Troubleshooting |

**Key Terminology:**
1. **ASCII Armor**: Text-based encoding for binary GPG data (flag: `-a` or `--armor`)
2. **Key ID**: Unique identifier for a GPG key (short: 8 hex chars, long: 16 hex chars, fingerprint: 40 hex chars)
3. **Keyring**: Database storing all your GPG keys (`~/.gnupg/`)
4. **Passphrase**: Password protecting your private key
5. **Recipient**: Person you're encrypting a message for (flag: `-r`)
6. **Web of Trust**: Decentralized trust model based on key signing
7. **Subkey**: Secondary key for specific operations (can be rotated without changing master key)
8. **Revocation Certificate**: Document that invalidates a key if compromised

---

## Understanding GnuPG and Public Key Cryptography

1. [**GnuPG (GNU Privacy Guard)**](https://gnupg.org/) is a complete and free implementation of the [**OpenPGP standard**](https://www.openpgp.org/) as defined by [**RFC 4880**](https://www.rfc-editor.org/rfc/rfc4880).
2. It provides **hybrid encryption** combining the convenience of public-key cryptography with the speed of symmetric encryption.
3. [**Public-key cryptography**](https://en.wikipedia.org/wiki/Public-key_cryptography) uses two mathematically related keys:
   4. **Public key**: Shared openly, used by others to encrypt messages to you or verify your signatures
   5. **Private key**: Kept secret, used to decrypt messages sent to you or create digital signatures
6. The [**Web of Trust**](https://en.wikipedia.org/wiki/Web_of_trust) model allows users to certify each other's keys through signatures, building a decentralized trust network without central authorities.
7. **Use cases** include:
   8. Encrypting sensitive emails and documents
   9. Digitally signing code releases and Git commits
   10. Authenticating software downloads via detached signatures
   11. Securing SSH authentication using GPG keys
   12. Encrypting password manager databases
13. GPG operates on the principle of **confidentiality** (encryption prevents unauthorized reading), **authenticity** (signatures prove sender identity), and **integrity** (tampering detection).

---

## Security Model and Cryptographic Algorithms

1. GPG supports multiple **public-key algorithms**:
   2. [**RSA**](https://en.wikipedia.org/wiki/RSA_(cryptosystem)): Traditional algorithm, minimum 2048-bit (4096-bit recommended)
   3. [**Ed25519**](https://en.wikipedia.org/wiki/EdDSA): Modern elliptic curve algorithm, faster and more secure with smaller keys
   4. **DSA/ElGamal**: Legacy algorithms, no longer recommended
5. **Symmetric encryption** algorithms (for actual data encryption):
   6. [**AES256**](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard): Industry standard, recommended
   7. **AES192/AES128**: Also secure but less common
   8. **3DES**: Deprecated, should be disabled
9. **Hash algorithms** for integrity verification:
   10. [**SHA512/SHA384/SHA256**](https://en.wikipedia.org/wiki/SHA-2): Modern, secure
   11. **SHA1**: Deprecated due to collision vulnerabilities
   12. **MD5**: Completely broken, never use
13. The **encryption process** works as follows:
   14. GPG generates a random **session key** (symmetric)
   15. The message is encrypted with the session key using symmetric encryption (fast)
   16. The session key is encrypted with the recipient's **public key** (slow but small)
   17. Both the encrypted message and encrypted session key are bundled together
18. The **decryption process** reverses this:
   19. Your **private key** decrypts the session key
   20. The session key decrypts the actual message
21. **Digital signatures** provide authenticity:
   22. GPG creates a hash of the message
   23. The hash is encrypted with your **private key** (this is the signature)
   24. Recipients decrypt the signature with your **public key** and compare hashes

---

## Key Management Best Practices

**Key generation recommendations:**
1. Use **Ed25519** for new keys (modern, fast, secure)
2. If compatibility required, use **RSA 4096-bit**
3. Always set an **expiration date** (1-2 years), extend as needed
4. Use a **strong passphrase** (minimum 20 characters, store in password manager)

**Master key and subkey architecture:**
1. Keep your **master key offline** (air-gapped computer or hardware token)
2. Use **subkeys** for daily operations (signing, encryption, authentication)
3. If a subkey is compromised, revoke only the subkey, not the master key
4. Subkeys can be rotated without affecting your key identity

**Backup strategy:**
1. Export your **private key** to encrypted USB drive
2. Store revocation certificate in a separate secure location
3. Consider **paper backups** using [paperkey](https://www.jabberwocky.com/software/paperkey/)
4. Test restoration process regularly

**Trust and verification:**
1. **Always verify fingerprints** through a separate channel (phone call, in person, video chat)
2. Sign keys only after identity verification
3. Set appropriate **trust levels**: unknown, never, marginal, full, ultimate
4. Attend [**key signing parties**](https://en.wikipedia.org/wiki/Key_signing_party) to expand Web of Trust

**Key distribution:**
1. Upload public keys to **keyservers**: [keys.openpgp.org](https://keys.openpgp.org/), [keyserver.ubuntu.com](https://keyserver.ubuntu.com/)
2. Publish on personal website or GitHub
3. Include in email signatures or social media profiles
4. Use [**Keybase**](https://keybase.io/) for cryptographic identity verification

**Revocation planning:**
1. Generate revocation certificate **immediately** after key creation
2. Store offline in secure location with instructions
3. Distribute revocation certificate to keyservers if key compromised
4. Create reason-specific revocations (compromised vs. superseded)

---

## Key Generation and Initial Setup

**Simplified Key Generation (Recommended for Beginners):**

```bash
gpg --gen-key
```

```plaintext
gpg (GnuPG) 2.4.0; Copyright (C) 2021 Free Software Foundation, Inc.

Please select what kind of key you want:
   (1) RSA and RSA (default)
   (2) DSA and Elgamal
   (3) DSA (sign only)
   (4) RSA (sign only)
Your selection? 1

RSA keys may be between 1024 and 4096 bits long.
What keysize do you want? (3072) 4096

Please specify how long the key should be valid.
         0 = key does not expire
      <n>  = key expires in n days
      <n>w = key expires in n weeks
      <n>m = key expires in n months
      <n>y = key expires in n years
Key is valid for? (0) 2y

Real name: John Doe
Email address: john.doe@example.com
Comment: Work key

You selected this USER-ID:
    "John Doe (Work key) <john.doe@example.com>"

Change (N)ame, (C)omment, (E)mail or (O)kay/(Q)uit? O

[Enter passphrase when prompted]

gpg: key 0x1234567890ABCDEF marked as ultimately trusted
public and secret key created and signed.
```

**Process Overview:**
1. **Algorithm selection**: Default RSA and RSA creates both signing and encryption subkeys
2. **Key size**: 4096 bits provides strong security (2048 minimum, 3072 default)
3. **Expiration**: Setting expiry forces periodic review and prevents orphaned keys
4. **User ID**: Combines name, email, and optional comment (email most important for searches)
5. **Passphrase**: Encrypts your private key on disk using symmetric encryption

**What happens during generation:**
1. GPG collects entropy from system randomness (`/dev/random`)
2. Generates prime numbers for RSA keys
3. Creates master key and subkeys
4. Generates revocation certificate automatically (stored in `~/.gnupg/openpgp-revocs.d/`)
5. Updates local trustdb

**Alternative approaches:**
1. `gpg --full-generate-key` — Provides more algorithm options
2. `gpg --quick-generate-key` — Non-interactive, scriptable
3. `gpg --expert --full-generate-key` — Advanced options including curve selection

---

## Advanced Key Generation with Modern Algorithms

**Generate Ed25519 Key (Recommended for 2024+):**

```bash
gpg --quick-generate-key "John Doe <john.doe@example.com>" ed25519 sign 1y
```

```plaintext
gpg: key 0xABCDEF1234567890 marked as ultimately trusted
gpg: revocation certificate stored as '/home/user/.gnupg/openpgp-revocs.d/ABCDEF1234567890.rev'
public and secret key created and signed.

pub   ed25519 2025-12-30 [SC] [expires: 2026-12-30]
      ABCDEF1234567890ABCDEF1234567890ABCDEF12
uid           John Doe <john.doe@example.com>
```

**Add Encryption Subkey:**

```bash
gpg --quick-add-key ABCDEF1234567890 cv25519 encr 1y
```

```plaintext
pub   ed25519 2025-12-30 [SC] [expires: 2026-12-30]
      ABCDEF1234567890ABCDEF1234567890ABCDEF12
uid           [ultimate] John Doe <john.doe@example.com>
sub   cv25519 2025-12-30 [E] [expires: 2026-12-30]
```

**Syntax:** `gpg --quick-generate-key "<name> <email>" <algorithm> <usage> <expiry>`

| Parameter | Purpose |
|:--|:--|
| `--quick-generate-key` | Non-interactive key generation |
| `"Name <email>"` | User ID string (quoted if contains spaces) |
| `ed25519` | Modern elliptic curve signing algorithm |
| `sign` | Key usage (sign, cert, auth, encr) |
| `1y` | Expires in 1 year (also: 2m=2 months, 3w=3 weeks, 0=never) |

**Why Ed25519 is superior:**
1. **Smaller keys**: 256-bit Ed25519 ≈ 3072-bit RSA security
2. **Faster operations**: 10-100x faster than RSA
3. **Modern cryptography**: Based on Curve25519, designed by Daniel J. Bernstein
4. **Resistance to side-channel attacks**: Constant-time implementations

**Key usage flags explained:**
1. **[C]**: Certify (sign other keys, master key capability)
2. **[S]**: Sign (create digital signatures on data)
3. **[E]**: Encrypt (receive encrypted messages)
4. **[A]**: Authenticate (use for SSH authentication)

**Adding subkeys:**
1. Use `--quick-add-key` with master key ID
2. Specify algorithm (cv25519 for encryption, ed25519 for signing)
3. Different expiry dates for different subkeys is common practice
4. Authentication subkey: `gpg --quick-add-key <keyid> ed25519 auth 1y`

---

## Listing and Inspecting Keys

**List all public keys:**

```bash
gpg --list-keys --keyid-format long
```

```plaintext
/home/user/.gnupg/pubring.kbx
--------------------------------
pub   rsa4096/0x1234567890ABCDEF 2025-12-30 [SC] [expires: 2027-12-30]
      ABCDEF1234567890ABCDEF1234567890ABCDEF12
uid                   [ultimate] John Doe (Work key) <john.doe@example.com>
sub   rsa4096/0x9876543210FEDCBA 2025-12-30 [E] [expires: 2027-12-30]

pub   ed25519/0xDEADBEEFCAFEBABE 2025-12-28 [SC] [expires: 2026-12-28]
      DEADBEEFCAFEBABEDEADBEEFCAFEBABEDEADBEEF
uid                   [ unknown] Alice Smith <alice@example.com>
sub   cv25519/0xBABECAFEDEADBEEF 2025-12-28 [E] [expires: 2026-12-28]
```

**List private (secret) keys:**

```bash
gpg --list-secret-keys --keyid-format long
```

```plaintext
/home/user/.gnupg/pubring.kbx
--------------------------------
sec   rsa4096/0x1234567890ABCDEF 2025-12-30 [SC] [expires: 2027-12-30]
      ABCDEF1234567890ABCDEF1234567890ABCDEF12
uid                   [ultimate] John Doe (Work key) <john.doe@example.com>
ssb   rsa4096/0x9876543210FEDCBA 2025-12-30 [E] [expires: 2027-12-30]
```

**Show key fingerprint:**

```bash
gpg --fingerprint john.doe@example.com
```

```plaintext
pub   rsa4096 2025-12-30 [SC] [expires: 2027-12-30]
      ABCD EF12 3456 7890 ABCD  EF12 3456 7890 ABCD EF12
uid           [ultimate] John Doe (Work key) <john.doe@example.com>
sub   rsa4096 2025-12-30 [E] [expires: 2027-12-30]
```

**Understanding the output:**

| Field | Meaning |
|:--|:--|
| `pub` | Public key |
| `sec` | Secret (private) key |
| `sub` | Public subkey |
| `ssb` | Secret subkey |
| `rsa4096` | Algorithm and key size |
| `0x1234...CDEF` | Long key ID (16 hex characters) |
| `2025-12-30` | Creation date |
| `[SC]` | Key capabilities: Sign, Certify |
| `[E]` | Key capability: Encrypt |
| `[expires: 2027-12-30]` | Expiration date |
| `[ultimate]` | Trust level (your own keys) |
| `[unknown]` | Trust level (unverified keys) |

**Trust levels explained:**
1. **unknown**: No trust decision made
2. **never**: Explicitly distrusted
3. **marginal**: Some confidence in key ownership
4. **full**: High confidence in key ownership
5. **ultimate**: Your own keys (absolute trust)

**Key ID formats:**
1. **Short (8 hex chars)**: `0xABCDEF12` — Vulnerable to collisions, deprecated
2. **Long (16 hex chars)**: `0x1234567890ABCDEF` — Recommended minimum
3. **Fingerprint (40 hex chars)**: Full SHA-1 hash of public key — Most secure, use for verification

**Useful listing variations:**
1. `gpg -k` — Shorthand for `--list-keys`
2. `gpg -K` — Shorthand for `--list-secret-keys`
3. `gpg --list-keys --with-fingerprint` — Always show fingerprints
4. `gpg --list-keys --with-keygrip` — Show internal key identifiers

---

## Exporting Keys for Backup and Sharing

**Export public key (ASCII armor for sharing):**

```bash
gpg --armor --export john.doe@example.com > john-doe-public.asc
```

```plaintext
-----BEGIN PGP PUBLIC KEY BLOCK-----

mQINBGV2+8kBEADMq7YzL3p8vKYj9xJHR8nzJ+W3qTd5gFHJ2kL9xYp3qRV8sW7M
[... key material ...]
-----END PGP PUBLIC KEY BLOCK-----
```

**Export private key (keep secure!):**

```bash
gpg --armor --export-secret-keys john.doe@example.com > john-doe-private.asc
```

```plaintext
-----BEGIN PGP PRIVATE KEY BLOCK-----

lQdGBGV2+8kBEADMq7YzL3p8vKYj9xJHR8nzJ+W3qTd5gFHJ2kL9xYp3qRV8sW7M
[... encrypted private key material ...]
-----END PGP PRIVATE KEY BLOCK-----
```

**Export all keys (backup entire keyring):**

```bash
gpg --armor --export > all-public-keys.asc
gpg --armor --export-secret-keys > all-private-keys.asc
```

**Export to clipboard (macOS):**

```bash
gpg --armor --export john.doe@example.com | pbcopy
```

**Export binary format (smaller file size):**

```bash
gpg --export john.doe@example.com > john-doe-public.gpg
```

**Syntax:** `gpg [--armor] --export [--output file] <key-id>`

| Flag | Purpose |
|:--|:--|
| `--armor` / `-a` | ASCII-armored output (text instead of binary) |
| `--export` | Export public keys |
| `--export-secret-keys` | Export private keys |
| `--export-secret-subkeys` | Export only subkeys (keep master offline) |
| `--output` / `-o` | Specify output file |
| `<key-id>` | Email, key ID, or fingerprint (omit for all keys) |

**ASCII armor vs. binary:**
1. **ASCII armor** (`.asc`): Text format, email-safe, larger size (~33% overhead)
2. **Binary** (`.gpg`): Smaller, more efficient, not text-safe

**Security considerations:**
1. **Private key exports** are encrypted with your passphrase
2. Store private key exports on **encrypted USB drives** or **offline media**
3. Never email or upload private keys to cloud services
4. Use `shred` or secure deletion when removing private key backups

**Advanced export scenarios:**
1. **Export master key only**: `gpg --export-secret-keys --armor <keyid>!`
2. **Export specific subkey**: `gpg --export-secret-subkeys --armor <subkeyid>!`
3. **Export with trust database**: Also backup `~/.gnupg/trustdb.gpg`
4. **Paper backup**: Use `paperkey` tool to create printable backup

---

## Importing Keys from Others

**Import from file:**

```bash
gpg --import alice-public.asc
```

```plaintext
gpg: key 0xDEADBEEFCAFEBABE: public key "Alice Smith <alice@example.com>" imported
gpg: Total number processed: 1
gpg:               imported: 1
```

**Import from keyserver:**

```bash
gpg --keyserver hkps://keys.openpgp.org --recv-keys 0xDEADBEEFCAFEBABE
```

```plaintext
gpg: key 0xDEADBEEFCAFEBABE: public key "Alice Smith <alice@example.com>" imported
gpg: Total number processed: 1
gpg:               imported: 1
gpg: marginal needed: 3  complete needed: 1  trust model: pgp
```

**Search keyserver for a key:**

```bash
gpg --keyserver hkps://keys.openpgp.org --search-keys alice@example.com
```

```plaintext
(1) Alice Smith <alice@example.com>
      4096 bit RSA key 0xDEADBEEFCAFEBABE, created: 2025-12-28
Keys 1-1 of 1 for "alice@example.com".  Enter number(s), N)ext, or Q)uit > 1
```

**Import from URL:**

```bash
curl https://example.com/alice-key.asc | gpg --import
```

**Import and verify fingerprint:**

```bash
gpg --import alice-public.asc
gpg --fingerprint alice@example.com
```

```plaintext
pub   rsa4096 2025-12-28 [SC] [expires: 2026-12-28]
      DEAD BEEF CAFE BABE DEAD  BEEF CAFE BABE DEAD BEEF
uid           [ unknown] Alice Smith <alice@example.com>
```

**Syntax:** `gpg --import <file>` or `gpg --recv-keys <key-id>`

| Flag | Purpose |
|:--|:--|
| `--import` | Import keys from file or stdin |
| `--recv-keys` | Download and import from keyserver |
| `--search-keys` | Search keyserver interactively |
| `--keyserver <url>` | Specify keyserver to use |
| `--fingerprint` | Display key fingerprint after import |

**Post-import verification workflow:**
1. Import the key
2. Check fingerprint: `gpg --fingerprint <key-id>`
3. **Verify fingerprint out-of-band** (phone call, in person, verified website)
4. Sign the key if verified: `gpg --sign-key <key-id>`
5. Set trust level: `gpg --edit-key <key-id>` → `trust` command

**Popular keyservers:**
1. [**keys.openpgp.org**](https://keys.openpgp.org/): Modern, privacy-focused, verifies email
2. [**keyserver.ubuntu.com**](https://keyserver.ubuntu.com/): Pool of synchronized servers
3. **keys.gnupg.net**: Legacy, often used for software verification

**Keyserver operations:**
1. **Upload**: `gpg --send-keys <key-id>`
2. **Refresh all keys**: `gpg --refresh-keys` (updates signatures and expiry)
3. **Auto-retrieve**: Set `auto-key-retrieve` in `gpg.conf`

---

## Deleting Keys (Use with Caution)

**Delete public key:**

```bash
gpg --delete-key alice@example.com
```

```plaintext
gpg (GnuPG) 2.4.0; Copyright (C) 2021 Free Software Foundation, Inc.

pub  rsa4096/0xDEADBEEFCAFEBABE 2025-12-28 Alice Smith <alice@example.com>

Delete this key from the keyring? (y/N) y
```

**Delete private key (must be done before deleting public key):**

```bash
gpg --delete-secret-key john.doe@example.com
```

```plaintext
sec  rsa4096/0x1234567890ABCDEF 2025-12-30 John Doe (Work key) <john.doe@example.com>

Delete this key from the keyring? (y/N) y
This is a secret key! - really delete? (y/N) y
```

**Delete both secret and public key (shortcut):**

```bash
gpg --delete-secret-and-public-key john.doe@example.com
```

**Important Notes on Key Deletion:**

1. **Deleting a private key is permanent** — cannot decrypt past messages without backup
2. **Deleting public key doesn't remove it from keyservers** — must publish revocation certificate
3. **Order matters**: Must delete private key before public key
4. **Subkeys are deleted with master key** — cannot selectively delete subkeys via command line
5. **Before deletion**:
   6. Ensure you have backed up the private key
   7. Generate and publish revocation certificate if key is public
   8. Consider just revoking instead of deleting
9. **Use key editing for selective removal**: `gpg --edit-key <keyid>` → `key N` → `delkey`

---

## Interactive Key Editor

**Enter key editing mode:**

```bash
gpg --edit-key john.doe@example.com
```

```plaintext
gpg (GnuPG) 2.4.0; Copyright (C) 2021 Free Software Foundation, Inc.

Secret key is available.

sec  rsa4096/0x1234567890ABCDEF
     created: 2025-12-30  expires: 2027-12-30  usage: SC
     trust: ultimate      validity: ultimate
ssb  rsa4096/0x9876543210FEDCBA
     created: 2025-12-30  expires: 2027-12-30  usage: E
[ultimate] (1). John Doe (Work key) <john.doe@example.com>

gpg> help
quit        quit this menu
save        save and quit
help        show this help
fpr         show key fingerprint
grip        show the keygrip
list        list key and user IDs
uid         select user ID N
key         select subkey N
check       check signatures
sign        sign selected user IDs
adduid      add a user ID
deluid      delete selected user IDs
addkey      add a subkey
delkey      delete selected subkeys
expire      change the expiration date for the key or selected subkeys
passwd      change the passphrase
trust       change the ownertrust
revkey      revoke key or selected subkeys

gpg>
```

**Common Key Editing Tasks:**

**Change expiration date:**
1. Enter edit mode: `gpg --edit-key <key-id>`
2. Command: `expire`
3. Follow prompts to set new expiration
4. For subkeys: `key 1` to select, then `expire`
5. Save: `save`

**Change passphrase:**
1. Enter edit mode: `gpg --edit-key <key-id>`
2. Command: `passwd`
3. Enter old passphrase, then new passphrase twice
4. Save: `save`

**Set trust level:**
1. Enter edit mode: `gpg --edit-key <key-id>`
2. Command: `trust`
3. Select trust level (1-5):
   4. 1 = I don't know or won't say
   5. 2 = I do NOT trust
   6. 3 = I trust marginally
   7. 4 = I trust fully
   8. 5 = I trust ultimately (own keys only)
9. Confirm and save

**Add new user ID (email):**
1. Enter edit mode: `gpg --edit-key <key-id>`
2. Command: `adduid`
3. Enter new name, email, comment
4. Command: `uid 1` to select new UID
5. Command: `primary` to make it primary
6. Save: `save`

**Revoke a key:**
1. Enter edit mode: `gpg --edit-key <key-id>`
2. Command: `revkey`
3. Select reason: 0=No reason, 1=Key compromised, 2=Key superseded, 3=Key no longer used
4. Confirm revocation
5. Save: `save`
6. Upload to keyserver: `gpg --send-keys <key-id>`

---

## Asymmetric Encryption (Public Key)

**Encrypt file for single recipient:**

```bash
gpg --encrypt --recipient alice@example.com secret-document.txt
```

```plaintext
[No output - creates secret-document.txt.gpg]
```

**Encrypt with ASCII armor (text-safe):**

```bash
gpg --encrypt --armor --recipient alice@example.com secret-document.txt
```

```plaintext
[Creates secret-document.txt.asc]
```

**Encrypt for multiple recipients:**

```bash
gpg -e -a -r alice@example.com -r bob@example.com -r john.doe@example.com confidential.txt
```

```plaintext
[Creates confidential.txt.asc - all three recipients can decrypt]
```

**Encrypt and specify output filename:**

```bash
gpg --output encrypted-report.gpg --encrypt --recipient alice@example.com quarterly-report.pdf
```

**Encrypt stdin (terminal input):**

```bash
echo "Meeting at 3pm tomorrow" | gpg -e -a -r alice@example.com > message.asc
```

**Encrypt multiline message:**

```bash
cat <<EOF | gpg -e -a -r alice@example.com > secret-message.asc
Project Nightfall is a go.
Launch coordinates: 51.5074° N, 0.1278° W
Extraction team on standby.
EOF
```

**Syntax:** `gpg --encrypt --recipient <email> [--armor] [--output <file>] <input-file>`

| Flag | Purpose |
|:--|:--|
| `--encrypt` / `-e` | Encrypt the file |
| `--recipient` / `-r` | Specify recipient by email or key ID (repeatable) |
| `--armor` / `-a` | Output ASCII-armored text instead of binary |
| `--output` / `-o` | Specify output filename |
| `--hidden-recipient` / `-R` | Hide recipient identity in encrypted file |

**How it works:**
1. GPG looks up recipient's public key in your keyring
2. Generates random session key (symmetric)
3. Encrypts file with session key using AES-256
4. Encrypts session key with recipient's public key
5. Bundles both in output file

**Multiple recipients:**
1. Each `-r` flag adds another recipient
2. Session key is encrypted separately for each recipient's public key
3. Any recipient can decrypt using their private key
4. File size increases slightly with each recipient

**Pro tips:**
1. **Always encrypt to yourself too**: Add `-r your@email.com` so you can decrypt later
2. **Use `--encrypt-to` in config**: Automatically includes your key
3. **Hidden recipients**: Use `-R` instead of `-r` to prevent key ID leakage
4. **Trust warnings**: GPG warns if recipient key isn't trusted (use `--trust-model always` to bypass)

---

## Symmetric Encryption (Password-Based)

**Encrypt with passphrase (no keys needed):**

```bash
gpg --symmetric confidential-notes.txt
```

```plaintext
[Prompts for passphrase twice]
[Creates confidential-notes.txt.gpg]
```

**Symmetric encryption with ASCII armor:**

```bash
gpg --symmetric --armor backup-codes.txt
```

```plaintext
[Creates backup-codes.txt.asc]
```

**Specify cipher algorithm:**

```bash
gpg --symmetric --cipher-algo AES256 --armor passwords.txt
```

**Encrypt from stdin:**

```bash
echo "Quick secret note" | gpg -c --armor > note.asc
```

**Encrypt multiline content:**

```bash
cat <<EOF | gpg -c --armor > database-credentials.asc
Database: production-db-01
Username: admin
Password: Tr0ub4dor&3
Host: db.internal.company.com:5432
EOF
```

**Syntax:** `gpg --symmetric [--cipher-algo <algorithm>] [--armor] <file>`

| Flag | Purpose |
|:--|:--|
| `--symmetric` / `-c` | Symmetric encryption (password-based) |
| `--cipher-algo` | Specify encryption algorithm (default: AES-128) |
| `--armor` / `-a` | ASCII-armored output |
| `--output` / `-o` | Specify output file |

**Supported cipher algorithms:**
1. **AES256** — Recommended (strongest)
2. **AES192** — Strong
3. **AES128** — Default (still secure)
4. **CAMELLIA256** — Alternative to AES
5. **TWOFISH** — Legacy

**When to use symmetric encryption:**
1. **Personal backups**: No need for key exchange
2. **Quick encryption**: Faster than asymmetric
3. **File archives**: Password-protect sensitive files
4. **Pre-shared secrets**: When secure channel for passphrase exists

**Security considerations:**
1. Passphrase strength is critical (minimum 20 characters recommended)
2. Use password manager to generate and store passphrases
3. No forward secrecy (compromised passphrase exposes all files encrypted with it)
4. Consider [**diceware**](https://www.eff.org/dice) for memorable but strong passphrases

**Decryption is identical to asymmetric**: `gpg -d file.gpg` (prompts for passphrase instead of using private key)

---

## Decrypting Files

**Decrypt to stdout (display):**

```bash
gpg --decrypt secret-document.txt.gpg
```

```plaintext
gpg: encrypted with rsa4096 key, ID 0x9876543210FEDCBA, created 2025-12-30
      "John Doe (Work key) <john.doe@example.com>"
This is the secret document content.
Multiple lines preserved.
```

**Decrypt to specific file:**

```bash
gpg --output decrypted.txt --decrypt secret-document.txt.gpg
```

```plaintext
gpg: encrypted with rsa4096 key, ID 0x9876543210FEDCBA, created 2025-12-30
      "John Doe (Work key) <john.doe@example.com>"
```

**Decrypt ASCII armored file:**

```bash
gpg --decrypt message.asc
```

**Decrypt and pipe to another command:**

```bash
gpg -d encrypted-logs.txt.gpg | grep "ERROR" | less
```

**Decrypt from stdin (paste encrypted content):**

```bash
gpg --decrypt <<EOF
-----BEGIN PGP MESSAGE-----

hQIMA5h2VDIgzey6AQ/+K8Z3Jx4vN2M1pR7qL9...
-----END PGP MESSAGE-----
EOF
```

**Decrypt clipboard content (macOS):**

```bash
pbpaste | gpg -d
```

**Decrypt and copy result to clipboard (macOS):**

```bash
gpg -d secret.asc | pbcopy
```

**Syntax:** `gpg --decrypt [--output <file>] <encrypted-file>`

| Flag | Purpose |
|:--|:--|
| `--decrypt` / `-d` | Decrypt the file |
| `--output` / `-o` | Write decrypted content to file instead of stdout |
| `--batch` | Non-interactive mode (no prompts) |
| `--passphrase <pass>` | Supply passphrase via command line (insecure) |
| `--passphrase-file <file>` | Read passphrase from file |

**What happens during decryption:**
1. GPG reads the encrypted file header
2. Identifies which key(s) can decrypt it
3. Prompts for passphrase to unlock your private key
4. Decrypts the session key using your private key
5. Decrypts the actual content using the session key
6. Outputs plaintext to stdout or file

**Output interpretation:**
1. `encrypted with rsa4096 key` — Shows encryption algorithm and key type
2. `ID 0x...` — Key ID that encrypted the file
3. Name and email — Key owner (the recipient)

**Troubleshooting:**
1. **"decryption failed: No secret key"** — You don't have the private key
2. **"decryption failed: Bad passphrase"** — Wrong passphrase for private key
3. **"WARNING: encrypted message has been manipulated"** — File integrity compromised (possible attack)
4. **"gpg: public key decryption failed: Canceled"** — User cancelled passphrase entry

---

## Digital Signatures (Binary Format)

**Sign a file (creates compressed binary signature):**

```bash
gpg --sign important-document.txt
```

```plaintext
[Creates important-document.txt.gpg]
```

**Sign with ASCII armor:**

```bash
gpg --sign --armor report.pdf
```

```plaintext
[Creates report.pdf.asc]
```

**Sign with specific key:**

```bash
gpg --sign --local-user john.doe@example.com contract.txt
```

**Extract content from signed file:**

```bash
gpg --decrypt signed-document.gpg
```

```plaintext
gpg: Signature made Mon 30 Dec 2025 14:32:15 GMT
gpg:                using RSA key 0x1234567890ABCDEF
gpg: Good signature from "John Doe (Work key) <john.doe@example.com>" [ultimate]
[Original file content displayed]
```

**Syntax:** `gpg --sign [--local-user <key-id>] [--armor] <file>`

| Flag | Purpose |
|:--|:--|
| `--sign` / `-s` | Create binary signature |
| `--local-user` / `-u` | Specify which key to sign with |
| `--armor` / `-a` | ASCII-armored output |
| `--output` / `-o` | Specify output filename |

**What binary signing does:**
1. Compresses the original file
2. Creates hash of the compressed data
3. Encrypts hash with your private key (this is the signature)
4. Bundles original + signature in `.gpg` file

**Characteristics:**
1. Original file is embedded in the signature file
2. Smaller than clear-signing (compression applied)
3. Not human-readable (binary format)
4. To view content, must decrypt: `gpg -d file.gpg`

**Use cases:**
1. Software releases (Linux packages)
2. Binary files (executables, archives)
3. When file content doesn't need to be readable without verification

---

## Clear-Text Signatures (Human-Readable)

**Sign with readable message:**

```bash
gpg --clearsign announcement.txt
```

```plaintext
[Creates announcement.txt.asc]
```

**Content of clear-signed file:**

```plaintext
-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA512

This is the original message content.
It remains completely readable.
Anyone can see this text without GPG.
-----BEGIN PGP SIGNATURE-----

iQIzBAEBCgAdFiEErN3xKzP4yKWaLZvzEjRWeJCrze8FAmV3FNMACgkQEjRWeJCr
ze/xKRAAiJ4K3mN9pQZ7vR2XjL...
-----END PGP SIGNATURE-----
```

**Sign from terminal input:**

```bash
cat <<EOF | gpg --clearsign
Official company announcement:
Our Q4 earnings exceeded expectations.
Revenue: £12.5M (up 23% YoY)
Signed by CEO
EOF
```

**Sign and save to file:**

```bash
cat <<EOF | gpg --clearsign > announcement.asc
Security Advisory: Patch immediately
CVE-2025-12345 affects versions 1.0-2.3
Update to version 2.4 or later
EOF
```

**Sign with specific key:**

```bash
gpg --clearsign --local-user john.doe@example.com statement.txt
```

**Syntax:** `gpg --clearsign [--local-user <key-id>] <file>`

| Flag | Purpose |
|:--|:--|
| `--clearsign` | Create clear-text signature |
| `--local-user` / `-u` | Specify signing key |
| `--output` / `-o` | Specify output file |
| `--digest-algo` | Choose hash algorithm (default: SHA256) |

**Structure of clear-signed message:**
1. **Header**: `-----BEGIN PGP SIGNED MESSAGE-----` and hash algorithm
2. **Blank line**
3. **Original message**: Unmodified, human-readable
4. **Signature block**: `-----BEGIN PGP SIGNATURE-----` ... `-----END PGP SIGNATURE-----`

**Advantages:**
1. Message readable without GPG tools
2. Perfect for email, forum posts, announcements
3. Content and signature in single file
4. Easy to copy-paste

**Limitations:**
1. Only works with text files (not binary)
2. Line endings must be preserved
3. Slight size increase compared to detached signatures

**Use cases:**
1. Email announcements and statements
2. Git commit messages (when not using detached signatures)
3. Forum posts and public declarations
4. Security advisories
5. Release notes

---

## Detached Signatures (Separate Signature File)

**Create detached binary signature:**

```bash
gpg --detach-sign software-package-1.2.3.tar.gz
```

```plaintext
[Creates software-package-1.2.3.tar.gz.sig]
```

**Create detached ASCII signature:**

```bash
gpg --detach-sign --armor software-package-1.2.3.tar.gz
```

```plaintext
[Creates software-package-1.2.3.tar.gz.asc]
```

**Detached signature content (ASCII):**

```plaintext
-----BEGIN PGP SIGNATURE-----

iQIzBAABCgAdFiEErN3xKzP4yKWaLZvzEjRWeJCrze8FAmV3GDUAC gkQEjRWeJCr
ze8h9g/9FjK4pL3mN8vQ2Z...
-----END PGP SIGNATURE-----
```

**Sign with specific key:**

```bash
gpg --detach-sign --armor --local-user release@company.com product.zip
```

**Verify detached signature:**

```bash
gpg --verify software-package-1.2.3.tar.gz.asc software-package-1.2.3.tar.gz
```

```plaintext
gpg: Signature made Mon 30 Dec 2025 15:45:22 GMT
gpg:                using RSA key 0x1234567890ABCDEF
gpg: Good signature from "John Doe (Work key) <john.doe@example.com>" [ultimate]
```

**Syntax:** `gpg --detach-sign [--armor] [--local-user <key-id>] <file>`

| Flag | Purpose |
|:--|:--|
| `--detach-sign` / `-b` | Create detached signature |
| `--armor` / `-a` | ASCII-armored signature |
| `--local-user` / `-u` | Specify signing key |
| `--output` / `-o` | Specify signature filename |

**How detached signatures work:**
1. GPG creates hash of the entire file
2. Encrypts hash with your private key
3. Saves signature in separate file
4. Original file remains unmodified

**Verification process:**
1. User downloads both original file and `.sig` file
2. GPG hashes the original file
3. Decrypts signature with signer's public key
4. Compares hashes — match = authentic

**Advantages:**
1. Original file completely unchanged
2. Works with any file type (binary, text, compressed)
3. Small signature file (few KB regardless of original size)
4. Standard for software distribution

**Use cases:**
1. **Software releases**: Linux packages, tarballs, ISOs
2. **Git tags**: `git tag -s v1.0.0` creates detached signature
3. **Large files**: Signature stays small even for GB files
4. **Multiple signatures**: Different people can sign same file

**Naming conventions:**
1. Binary: `file.sig`
2. ASCII: `file.asc` or `file.sig.asc`
3. Some projects: `file.gpg` or `file.pgp`

---

## Combined Sign and Encrypt

**Sign then encrypt for recipient:**

```bash
gpg --sign --encrypt --recipient alice@example.com confidential-contract.pdf
```

```plaintext
[Creates confidential-contract.pdf.gpg]
```

**Sign and encrypt with ASCII armor:**

```bash
gpg -se -a -r alice@example.com sensitive-data.txt
```

```plaintext
[Creates sensitive-data.txt.asc]
```

**Sign and encrypt for multiple recipients:**

```bash
gpg -se -a -r alice@example.com -r bob@example.com -r john.doe@example.com report.txt
```

**Specify signing key explicitly:**

```bash
gpg -s -e -a -u john.doe@example.com -r alice@example.com message.txt
```

**Decrypt and verify in one step:**

```bash
gpg --decrypt signed-encrypted.asc
```

```plaintext
gpg: encrypted with rsa4096 key, ID 0x9876543210FEDCBA, created 2025-12-30
      "John Doe (Work key) <john.doe@example.com>"
gpg: Signature made Mon 30 Dec 2025 16:10:45 GMT
gpg:                using RSA key 0x1234567890ABCDEF
gpg: Good signature from "Alice Smith <alice@example.com>" [full]
[Decrypted message content]
```

**Syntax:** `gpg --sign --encrypt --recipient <email> [--local-user <key>] <file>`

| Flag | Purpose |
|:--|:--|
| `--sign --encrypt` / `-se` | Sign then encrypt (combined) |
| `--recipient` / `-r` | Specify recipients (repeatable) |
| `--local-user` / `-u` | Specify signing key |
| `--armor` / `-a` | ASCII-armored output |

**Order of operations:**
1. File is **signed first** (creates signature with your private key)
2. Signed data is then **encrypted** (using recipient's public key)
3. Recipient must **decrypt first**, then **verify signature**

**Security benefits:**
1. **Confidentiality**: Only recipient can read (encryption)
2. **Authenticity**: Proves you sent it (signature)
3. **Integrity**: Detects tampering (signature verification)
4. **Non-repudiation**: You cannot deny sending (your signature)

**Why this is the gold standard:**
1. Signing alone doesn't hide content
2. Encrypting alone doesn't prove sender
3. Combining both provides complete security

**Use cases:**
1. Confidential business communications
2. Legal documents requiring proof of authenticity
3. Sensitive personal correspondence
4. Financial information exchange

**Verification by recipient:**
1. Decrypt with their private key (proves they're intended recipient)
2. Verify signature with your public key (proves you sent it)
3. Both operations happen automatically with `gpg -d`

---

## Verifying Signatures

**Verify clear-signed message:**

```bash
gpg --verify announcement.asc
```

```plaintext
gpg: Signature made Mon 30 Dec 2025 16:30:12 GMT
gpg:                using RSA key 0x1234567890ABCDEF
gpg: Good signature from "John Doe (Work key) <john.doe@example.com>" [ultimate]
```

**Verify detached signature:**

```bash
gpg --verify software-1.2.3.tar.gz.asc software-1.2.3.tar.gz
```

```plaintext
gpg: Signature made Mon 30 Dec 2025 16:45:00 GMT
gpg:                using RSA key 0x1234567890ABCDEF
gpg: Good signature from "Release Team <release@company.com>" [full]
```

**Verify binary signed file:**

```bash
gpg --verify document.gpg
```

**Verify with verbose output:**

```bash
gpg --verify --verbose software.tar.gz.sig software.tar.gz
```

**Verify and extract content:**

```bash
gpg --decrypt signed-message.gpg
```

```plaintext
gpg: Signature made Mon 30 Dec 2025 17:00:00 GMT
gpg:                using RSA key 0x1234567890ABCDEF
gpg: Good signature from "Alice Smith <alice@example.com>" [full]
[Message content displayed]
```

**Test signature creation and verification (one-liner):**

```bash
echo "Test message" | gpg --clearsign | gpg --verify
```

```plaintext
gpg: Signature made Mon 30 Dec 2025 17:05:30 GMT
gpg:                using RSA key 0x1234567890ABCDEF
gpg: Good signature from "John Doe (Work key) <john.doe@example.com>" [ultimate]
```

**Syntax:** 
1. Embedded: `gpg --verify <signed-file>`
2. Detached: `gpg --verify <signature-file> <original-file>`

| Flag | Purpose |
|:--|:--|
| `--verify` | Verify signature |
| `--verbose` | Show detailed information |
| `--status-fd N` | Machine-readable status output |

**Signature verification outcomes:**

| Message | Meaning |
|:--|:--|
| `Good signature` | ✅ Signature is valid and intact |
| `BAD signature` | ❌ File has been tampered with or signature corrupt |
| `Can't check signature: No public key` | ⚠️ You don't have signer's public key |
| `Signature expired` | ⚠️ Signature was created with expired key |
| `WARNING: This key is not certified` | ⚠️ You haven't verified/signed this public key |

**Trust indicators:**
1. **[ultimate]**: Your own key
2. **[full]**: You've signed this key (verified identity)
3. **[marginal]**: Signed by someone you trust
4. **[unknown]**: No trust relationship established
5. **[expired]**: Key has passed expiration date
6. **[revoked]**: Key has been revoked by owner

**What GPG checks:**
1. Signature cryptographically matches file (integrity)
2. Signature was created with private key corresponding to claimed public key (authenticity)
3. Key hasn't been revoked
4. Key hasn't expired (warning if expired)
5. Signature timestamp (when it was created)

**Troubleshooting:**
1. **Missing public key**: Import with `gpg --recv-keys <keyid>` or `gpg --import`
2. **Untrusted key**: Verify fingerprint out-of-band, then sign: `gpg --sign-key <keyid>`
3. **BAD signature**: File corrupted or tampered — do NOT trust

---

## Shell Aliases for Enhanced Productivity

**Add these to `~/.bashrc`, `~/.zshrc`, or equivalent:**

```bash
# Key Management
alias gpg-list='gpg --list-keys --keyid-format long'
alias gpg-list-secret='gpg --list-secret-keys --keyid-format long'
alias gpg-fingerprint='gpg --fingerprint'
alias gpg-refresh='gpg --refresh-keys'

# Encryption shortcuts
alias gpg-encrypt='gpg -e -a -r'
alias gpg-encrypt-self='gpg -e -a -r $(gpg --list-keys --keyid-format long | grep -m1 "^pub" | awk "{print \$2}" | cut -d"/" -f2)'
alias gpg-symmetric='gpg -c --armor --cipher-algo AES256'

# Decryption
alias gpg-decrypt='gpg -d'
alias gpg-decrypt-file='gpg -o'

# Signing
alias gpg-sign='gpg --clearsign'
alias gpg-sign-detach='gpg -b -a'
alias gpg-sign-encrypt='gpg -se -a -r'

# Verification
alias gpg-verify='gpg --verify'

# Export
alias gpg-export-pub='gpg --armor --export'
alias gpg-export-priv='gpg --armor --export-secret-keys'

# Clipboard operations (macOS)
alias gpg-encrypt-clip='pbpaste | gpg -e -a -r'
alias gpg-decrypt-clip='pbpaste | gpg -d'
alias gpg-sign-clip='pbpaste | gpg --clearsign | pbcopy'
alias gpg-export-clip='gpg --armor --export $1 | pbcopy'

# Linux alternatives (using xclip)
# alias gpg-encrypt-clip='xclip -o | gpg -e -a -r'
# alias gpg-decrypt-clip='xclip -o | gpg -d'
# alias gpg-sign-clip='xclip -o | gpg --clearsign | xclip -selection clipboard'

# Advanced operations
alias gpg-revoke='gpg --gen-revoke --armor --output=revocation.asc'
alias gpg-edit='gpg --edit-key'
alias gpg-import='gpg --import'
alias gpg-send='gpg --send-keys'
alias gpg-recv='gpg --recv-keys'
alias gpg-search='gpg --search-keys'

# Agent management
alias gpg-restart='gpgconf --kill gpg-agent && gpg-agent --daemon'
alias gpg-agent-status='gpg-connect-agent "getinfo version" /bye'

# Quick test
alias gpg-test='echo "Test message" | gpg --clearsign | gpg --verify'
```

**Usage examples:**

```bash
# Encrypt for Alice
gpg-encrypt alice@example.com confidential.txt

# Sign and copy to clipboard
echo "Important announcement" | gpg-sign-clip

# Decrypt clipboard content
gpg-decrypt-clip

# Export public key to clipboard
gpg-export-clip john.doe@example.com

# Quick signature test
gpg-test
```

---

## GPG Configuration Files

**Configuration file locations:**

1. `~/.gnupg/gpg.conf` — Main GPG configuration
2. `~/.gnupg/gpg-agent.conf` — GPG Agent (passphrase caching, pinentry)
3. `~/.gnupg/dirmngr.conf` — Directory manager (keyserver operations)
4. `~/.gnupg/trustdb.gpg` — Trust database (binary, auto-managed)
5. `~/.gnupg/pubring.kbx` — Public keyring (binary)
6. `~/.gnupg/secring.gpg` — Secret keyring (legacy, GPG 2.1+ uses private-keys-v1.d/)

**Directory permissions (critical for security):**

```bash
chmod 700 ~/.gnupg
chmod 600 ~/.gnupg/*
```

---

## Recommended `~/.gnupg/gpg.conf` Configuration

**Production-ready configuration with security best practices:**

```conf
#-----------------------------
# Explicit Key Selection (recommended)
#-----------------------------
# Prefer --local-user <FULL_FINGERPRINT> and explicit --recipient values
# per command. Do not enable defaults unless their behaviour is intentional.
#
# Optional signing default (use a full fingerprint, never a short key ID):
# default-key 0123456789ABCDEF0123456789ABCDEF01234567
#
# Optional automatic self-encryption. This is convenient but less explicit:
# default-recipient-self
#
# Optional always-add recipient. This changes every encryption operation:
# encrypt-to 0123456789ABCDEF0123456789ABCDEF01234567

#-----------------------------
# Display and Output Behavior
#-----------------------------
# Disable copyright notice
no-greeting

# Use long key IDs (16 hex characters)
keyid-format 0xlong

# Display key fingerprints
with-fingerprint

# Show UID validity when listing keys
list-options show-uid-validity
verify-options show-uid-validity

# Show key usage capabilities
list-options show-usage

# ASCII-armored output by default (text-safe)
armor

# Remove version string from output (privacy)
no-emit-version

# Remove comments from output (privacy)
no-comments

#-----------------------------
# Cryptographic Preferences
#-----------------------------
# Preferred symmetric ciphers (strongest first)
personal-cipher-preferences AES256 AES192 AES

# Preferred digest algorithms
personal-digest-preferences SHA512 SHA384 SHA256

# Preferred compression algorithms
personal-compress-preferences ZLIB BZIP2 ZIP Uncompressed

# Default cipher for symmetric encryption
cipher-algo AES256

# Default digest for signatures
digest-algo SHA512

# Default compression
compress-algo ZLIB

# Compression level (0=none, 1=fast, 9=best)
compress-level 6

#-----------------------------
# Security Hardening
#-----------------------------
# Disable weak algorithms
disable-cipher-algo 3DES
disable-cipher-algo IDEA
disable-cipher-algo CAST5

# Mark SHA-1 as weak
weak-digest SHA1

# Require cross-certification on subkeys
require-cross-certification

# Don't merge user IDs on import
import-options import-clean

# Remove unusable signatures when cleaning keys
import-options import-minimal

#-----------------------------
# Keyserver Configuration
#-----------------------------
# Default keyserver (modern, privacy-focused)
keyserver hkps://keys.openpgp.org

# Alternative keyservers (uncomment if needed):
# keyserver hkps://keyserver.ubuntu.com
# keyserver hkps://keys.gnupg.net

# Automatically retrieve keys when verifying
auto-key-retrieve

# Include revoked keys in searches
keyserver-options include-revoked

# Don't leak key search info to keyserver
keyserver-options no-honor-keyserver-url

#-----------------------------
# User Interface
#-----------------------------
# Use UTF-8 for display
utf8-strings

# Fixed list mode (parseable output)
fixed-list-mode

# Show full timestamps
list-options show-sig-expire

#-----------------------------
# Trust and Validation
#-----------------------------
# Set trust model (pgp = Web of Trust, tofu = Trust On First Use)
trust-model pgp

# Require valid certification path (stricter)
# trust-model tofu+pgp

# Use agent for passphrases
use-agent

# Throw keyids option (privacy - hides recipients)
# throw-keyids
```

**Configuration Options Explained:**

**Key security options:**
1. **`default-recipient-self`**: Ensures you can decrypt messages you send
2. **`require-cross-certification`**: Prevents fake binding signatures on subkeys
3. **`weak-digest SHA1`**: Warns when SHA-1 is used (deprecated due to collisions)
4. **`disable-cipher-algo 3DES`**: Prevents use of weak encryption algorithms

**Privacy options:**
1. **`no-emit-version`**: Doesn't reveal your GPG version (reduces fingerprinting)
2. **`no-comments`**: Removes comment field from output
3. **`throw-keyids`**: Hides recipient key IDs (prevents traffic analysis)
4. **`keyserver-options no-honor-keyserver-url`**: Ignores keyserver URLs in keys (prevents tracking)

**Output formatting:**
1. **`armor`**: Default to ASCII output (`.asc` files)
2. **`keyid-format 0xlong`**: Shows 16-character key IDs (short IDs are insecure)
3. **`with-fingerprint`**: Always displays full 40-character fingerprint

**Algorithm preferences:**
1. Listed in order of preference (strongest first)
2. GPG negotiates with recipient's preferences
3. Falls back to next algorithm if first isn't supported

---

## Recommended `~/.gnupg/gpg-agent.conf` Configuration

```conf
#-----------------------------
# Passphrase Caching
#-----------------------------
# Cache passphrase for 1 hour (3600 seconds)
default-cache-ttl 3600

# Maximum cache time: 8 hours (28800 seconds)
max-cache-ttl 28800

# Time to cache SSH keys (if using GPG for SSH)
default-cache-ttl-ssh 3600
max-cache-ttl-ssh 28800

#-----------------------------
# Pinentry (Password Prompt)
#-----------------------------
# Graphical pinentry (choose based on your desktop environment)

# For macOS:
pinentry-program /usr/local/bin/pinentry-mac

# For GNOME/GTK:
# pinentry-program /usr/bin/pinentry-gtk-2

# For KDE/Qt:
# pinentry-program /usr/bin/pinentry-qt

# For terminal/console:
# pinentry-program /usr/bin/pinentry-curses

# For TTY (servers):
# pinentry-program /usr/bin/pinentry-tty

#-----------------------------
# SSH Support
#-----------------------------
# Enable GPG key usage for SSH authentication
enable-ssh-support

#-----------------------------
# Security
#-----------------------------
# Allow passphrase entry via loopback (for scripts)
allow-loopback-pinentry

# Enforce passphrase constraints
# min-passphrase-len 20
# min-passphrase-nonalpha 2

#-----------------------------
# Logging (Debugging)
#-----------------------------
# Uncomment for troubleshooting
# log-file /tmp/gpg-agent.log
# debug-level basic
# verbose
```

**Apply changes:**

```bash
# Restart GPG agent to load new config
gpgconf --kill gpg-agent
gpg-agent --daemon
```

---

## Recommended `~/.gnupg/dirmngr.conf` Configuration

```conf
#-----------------------------
# Keyserver Configuration
#-----------------------------
# Primary keyserver
keyserver hkps://keys.openpgp.org

# Fallback keyservers (tried if primary fails)
# keyserver hkps://keyserver.ubuntu.com
# keyserver hkps://pgp.mit.edu

#-----------------------------
# Network and Proxy
#-----------------------------
# Honor HTTP proxy environment variables
honor-http-proxy

# Use Tor for keyserver access (requires Tor running)
# use-tor

# HTTP proxy (if not using environment variables)
# http-proxy http://proxy.example.com:8080

#-----------------------------
# Certificate Validation (for HKPS)
#-----------------------------
# Path to CA certificates (for HTTPS keyservers)
# hkp-cacert /usr/share/ca-certificates/mozilla/root.crt

# Disable certificate checks (not recommended)
# disable-http

#-----------------------------
# Logging (Debugging)
#-----------------------------
# Uncomment for troubleshooting
# log-file /tmp/dirmngr.log
# debug-level basic
# verbose
```

**Apply changes:**

```bash
# Restart dirmngr
gpgconf --kill dirmngr
dirmngr --daemon
```

---

## Common Troubleshooting Issues

**Problem: "gpg: decryption failed: No secret key"**

1. **Cause**: You don't have the private key needed to decrypt
2. **Solution**:
   3. Check which key encrypted the file: `gpg --list-packets file.gpg | grep keyid`
   4. Verify you have that key: `gpg --list-secret-keys <keyid>`
   5. If missing, import backup: `gpg --import private-key-backup.asc`

**Problem: "gpg: WARNING: This key is not certified with a trusted signature"**

1. **Cause**: You haven't verified and signed the public key
2. **Solution**:
   3. Verify fingerprint out-of-band (phone, in person)
   4. Sign the key: `gpg --sign-key <keyid>`
   5. Or adjust trust: `gpg --edit-key <keyid>` → `trust` → select level

**Problem: "gpg: can't connect to the agent: IPC connect call failed"**

1. **Cause**: GPG agent not running or socket issue
2. **Solution**:
   ```bash
   # Kill existing agent
   gpgconf --kill gpg-agent
   
   # Start new agent
   gpg-agent --daemon
   
   # Verify it's running
   gpg-connect-agent 'getinfo version' /bye
   ```

**Problem: "gpg: public key decryption failed: Inappropriate ioctl for device"**

1. **Cause**: Terminal not properly configured for passphrase entry
2. **Solution**:
   ```bash
   export GPG_TTY=$(tty)
   echo "export GPG_TTY=\$(tty)" >> ~/.bashrc
   ```

**Problem: "gpg: keyserver receive failed: No keyserver available"**

1. **Cause**: Keyserver configuration issue or network problem
2. **Solution**:
   ```bash
   # Test keyserver connectivity
   gpg --keyserver hkps://keys.openpgp.org --recv-keys <keyid>
   
   # Try alternative keyserver
   gpg --keyserver hkps://keyserver.ubuntu.com --recv-keys <keyid>
   
   # Check dirmngr status
   gpgconf --check-programs
   
   # Restart dirmngr
   gpgconf --kill dirmngr
   ```

**Problem: "gpg: signing failed: Unusable secret key"**

1. **Cause**: Key expired or passphrase wrong
2. **Solution**:
   ```bash
   # Check key expiration
   gpg --list-keys <keyid>
   
   # Extend expiration
   gpg --edit-key <keyid>
   # In editor: expire → set new date → save
   
   # Upload updated key
   gpg --send-keys <keyid>
   ```

**Problem: Permission errors on `~/.gnupg`**

1. **Cause**: Incorrect file permissions (GPG requires strict permissions)
2. **Solution**:
   ```bash
   chmod 700 ~/.gnupg
   chmod 600 ~/.gnupg/*
   chmod 700 ~/.gnupg/private-keys-v1.d
   ```

**Problem: "gpg: Fatal: can't create directory"**

1. **Cause**: GPG directory doesn't exist or ownership wrong
2. **Solution**:
   ```bash
   mkdir -p ~/.gnupg
   chmod 700 ~/.gnupg
   chown -R $USER:$USER ~/.gnupg
   ```

---

## Diagnostic Commands

**Check GPG version and capabilities:**

```bash
gpg --version
```

```plaintext
gpg (GnuPG) 2.4.0
libgcrypt 1.10.1
Supported algorithms:
Pubkey: RSA, ELG, DSA, ECDH, ECDSA, EDDSA
Cipher: IDEA, 3DES, CAST5, BLOWFISH, AES, AES192, AES256, TWOFISH,
        CAMELLIA128, CAMELLIA192, CAMELLIA256
Hash: SHA1, RIPEMD160, SHA256, SHA384, SHA512, SHA224
Compression: Uncompressed, ZIP, ZLIB, BZIP2
```

**List loaded configuration options:**

```bash
gpg --list-config
```

**Check agent status:**

```bash
gpg-connect-agent 'getinfo version' /bye
```

```plaintext
D 2.4.0
OK
```

**Test key with verbose output:**

```bash
gpg -vvv --list-keys john.doe@example.com
```

**Update trust database:**

```bash
gpg --update-trustdb
```

**Check trust database integrity:**

```bash
gpg --check-trustdb
```

**List all GPG-related processes:**

```bash
ps aux | grep gpg
```

**Force passphrase re-entry (clear cache):**

```bash
echo RELOADAGENT | gpg-connect-agent
```

**Restart all GPG components:**

```bash
gpgconf --kill all
gpg-agent --daemon
```

---

## Hardware Token Integration (YubiKey, Nitrokey)

**Why use hardware tokens:**

1. **Private keys never leave the device** — cannot be copied or exfiltrated
2. **Physical presence required** — protection against remote attacks
3. **PIN protection** — additional authentication layer
4. **Tamper-resistant** — specialized security chips
5. **Portable** — use your keys on multiple computers without copying them

**Supported operations:**

1. Store GPG signing subkey
2. Store GPG encryption subkey
3. Store GPG authentication subkey (for SSH)
4. Store master key (advanced: offline master key setup)

**Check if token is detected:**

```bash
gpg --card-status
```

```plaintext
Reader: Yubico YubiKey OTP+FIDO+CCID
Application ID: D2760001240100000006123456780000
Version: 3.4
Manufacturer: Yubico
Serial number: 12345678
Name of cardholder: John Doe
Language prefs: en
Sex: male
URL of public key: https://example.com/john-doe.asc
Login data: john.doe@example.com
Signature PIN: not forced
Key attributes: rsa4096 rsa4096 rsa4096
Max. PIN lengths: 127 127 127
PIN retry counter: 3 0 3
Signature counter: 42
Signature key: ABCD EF12 3456 7890
      created: 2025-12-30
Encryption key: 1234 5678 90AB CDEF
      created: 2025-12-30
Authentication key: 9876 5432 10FE DCBA
      created: 2025-12-30
```

**Move existing subkey to token:**

```bash
gpg --edit-key john.doe@example.com
# In editor:
key 1          # Select signing subkey
keytocard      # Move to card
# Choose slot (1=signature, 2=encryption, 3=authentication)
save
```

**Generate key directly on token (cannot be backed up):**

```bash
gpg --card-edit
# In editor:
admin
generate
# Follow prompts
```

**Hardware Token Backup Strategy:**

1. **Keys moved to hardware tokens cannot be extracted** — this is by design
2. **Always keep encrypted backup of private keys** before moving to hardware
3. **Consider having two tokens** with identical keys for redundancy
4. **Store revocation certificate offline** in case token is lost
5. **Document your PINs securely** (default Admin PIN: 12345678, User PIN: 123456)
6. **Backup strategy**:
   7. Export subkeys before moving: `gpg --armor --export-secret-subkeys <keyid>`
   8. Store on encrypted USB drive in safe location
   9. Test restoration process periodically

---

## Using GPG for SSH Authentication

**Why use GPG for SSH:**

1. Single key for both GPG and SSH operations
2. Hardware token support (YubiKey, Nitrokey)
3. Centralized key management
4. Subkey rotation without changing SSH configuration

**Setup process:**

1. **Enable SSH support in `gpg-agent.conf`:**

```bash
echo "enable-ssh-support" >> ~/.gnupg/gpg-agent.conf
gpgconf --kill gpg-agent
```

2. **Configure shell environment:**

```bash
# Add to ~/.bashrc or ~/.zshrc
export GPG_TTY=$(tty)
export SSH_AUTH_SOCK=$(gpgconf --list-dirs agent-ssh-socket)
gpgconf --launch gpg-agent
```

3. **Create authentication subkey (if you don't have one):**

```bash
gpg --expert --edit-key john.doe@example.com
# In editor:
addkey
# Choose: (8) RSA (set your own capabilities)
# Toggle: S, E (to disable), toggle A (to enable authentication)
# Choose key size: 4096
# Choose expiration: 1y
save
```

4. **Add authentication subkey to SSH:**

```bash
# Get authentication subkey keygrip
gpg --list-keys --with-keygrip john.doe@example.com

# Add keygrip to sshcontrol
echo "YOUR_KEYGRIP_HERE" >> ~/.gnupg/sshcontrol
```

5. **Export SSH public key:**

```bash
gpg --export-ssh-key john.doe@example.com
```

```plaintext
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC... openpgp:0xABCDEF12
```

6. **Add to remote server:**

```bash
gpg --export-ssh-key john.doe@example.com >> ~/.ssh/authorized_keys
# Or copy-paste to remote server's ~/.ssh/authorized_keys
```

7. **Test SSH connection:**

```bash
ssh user@remote-server.com
# Should prompt for GPG passphrase (or PIN if using hardware token)
```

---

## Advanced Key Management: Master Key Offline Strategy

**Concept:**

1. Keep master key on air-gapped machine or hardware token
2. Use subkeys for daily operations
3. If subkey compromised, revoke only subkey, not entire identity

**Implementation:**

1. **Generate master key on air-gapped machine:**

```bash
gpg --expert --full-generate-key
# Choose: (1) RSA and RSA
# Size: 4096
# Capabilities: Certify only (disable Sign and Encrypt)
# Expiry: 0 (does not expire)
```

2. **Add subkeys for daily use:**

```bash
gpg --expert --edit-key <master-key-id>
# Add signing subkey:
addkey → (4) RSA (sign only) → 4096 → 1y → save

# Add encryption subkey:
addkey → (6) RSA (encrypt only) → 4096 → 1y → save

# Add authentication subkey:
addkey → (8) RSA (set capabilities) → toggle all except A → 4096 → 1y → save
```

3. **Backup master key:**

```bash
gpg --armor --export-secret-keys <master-key-id> > master-key-backup.asc
gpg --armor --export-secret-subkeys <master-key-id> > subkeys-backup.asc
gpg --gen-revoke --output revocation.asc <master-key-id>

# Store on encrypted USB drives (multiple copies)
# Consider paper backup with paperkey
```

4. **Export subkeys for daily machine:**

```bash
gpg --armor --export-secret-subkeys <master-key-id> > daily-subkeys.asc
```

5. **On daily machine, delete master key (keep subkeys):**

```bash
# Import subkeys
gpg --import daily-subkeys.asc

# Verify you have subkeys
gpg --list-secret-keys
# You should see "sec#" (hash indicates master key stub only)
```

6. **Annual subkey rotation (requires master key):**

```bash
# On air-gapped machine with master key:
gpg --edit-key <master-key-id>
key 1          # Select old subkey
expire         # Extend or revoke
addkey         # Create new subkey
save

# Export updated subkeys to daily machine
```

---

## References and Further Reading

**Official Documentation:**
1. [GnuPG Official Website](https://gnupg.org/) — Primary resource for GPG
2. [GnuPG Manual](https://gnupg.org/documentation/manuals/gnupg/) — Comprehensive reference guide
3. [RFC 4880 - OpenPGP Message Format](https://www.rfc-editor.org/rfc/rfc4880) — Protocol specification
4. [GnuPG FAQ](https://gnupg.org/faq/gnupg-faq.html) — Common questions and answers

**Security and Best Practices:**
1. [OpenPGP Best Practices](https://riseup.net/en/security/message-security/openpgp/best-practices) — Riseup security collective recommendations
2. [Debian Wiki: Using OpenPGP subkeys](https://wiki.debian.org/Subkeys) — Advanced key management
3. [Creating the Perfect GPG Keypair](https://alexcabal.com/creating-the-perfect-gpg-keypair) — Detailed walkthrough
4. [The GNU Privacy Handbook](https://gnupg.org/gph/en/manual.html) — Beginner-friendly guide

**Hardware Token Resources:**
1. [YubiKey GPG Guide](https://support.yubico.com/hc/en-us/articles/360013790259-Using-Your-YubiKey-with-OpenPGP) — Official YubiKey documentation
2. [Nitrokey Documentation](https://docs.nitrokey.com/) — Nitrokey Pro and Storage setup
3. [drduh's YubiKey Guide](https://github.com/drduh/YubiKey-Guide) — Comprehensive hardware token tutorial

**Cryptographic Background:**
1. [Public-Key Cryptography](https://en.wikipedia.org/wiki/Public-key_cryptography) — Wikipedia overview
2. [Digital Signature](https://en.wikipedia.org/wiki/Digital_signature) — Cryptographic signature concepts
3. [Web of Trust](https://en.wikipedia.org/wiki/Web_of_trust) — Trust model explanation
4. [Curve25519](https://en.wikipedia.org/wiki/Curve25519) — Modern elliptic curve cryptography

**Practical Guides:**
1. [Using GPG for Email](https://emailselfdefense.fsf.org/en/) — FSF Email Self-Defense guide
2. [Git Commit Signing](https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work) — Signing commits and tags
3. [Pass: The Standard Unix Password Manager](https://www.passwordstore.org/) — GPG-based password manager

**Keyserver Information:**
1. [keys.openpgp.org](https://keys.openpgp.org/) — Modern, privacy-focused keyserver
2. [Ubuntu Keyserver](https://keyserver.ubuntu.com/) — Popular keyserver pool
3. [SKS Keyserver Status](https://sks-keyservers.net/status/) — Legacy SKS network (deprecated)

**Community and Support:**
1. [GnuPG Mailing Lists](https://gnupg.org/documentation/mailing-lists.html) — Official support channels
2. [r/GnuPG](https://www.reddit.com/r/GnuPG/) — Reddit community
3. [Stack Exchange: Cryptography](https://crypto.stackexchange.com/) — Q&A for cryptographic topics

---

#Cryptography #GnuPG #GPG #Encryption #Digital-Signatures #OpenPGP #Key-Management #Public-Key-Cryptography #Privacy #Security #PGP #Asymmetric-Encryption #Symmetric-Encryption #Web-of-Trust #Command-Line #Linux #macOS #BSD #PKI #Ed25519 #RSA #AES #SHA512 #Keyserver #YubiKey #Hardware-Token #SSH-Authentication #Email-Encryption #Code-Signing #File-Security
