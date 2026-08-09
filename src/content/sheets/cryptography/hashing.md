---
title: "Hashing & Hash Identification"
description: "Compute and identify hashes (md5/sha/NTLM), encodings, and pick the right cracking mode."
category: cryptography
tags: [cryptography, hashing, identification]
tools: [hashid, hash-identifier, openssl]
difficulty: beginner
updated: "2026-08-09"
source: "vault:HashingAndEncrypting/Hashing cheat sheet .md"
---

# Hashing & Hash Identification

CLI tools only, no Python scripts.

> Covers: `sha*sum` · `md5sum` · `b2sum` · `openssl dgst` · `openssl kdf` · `argon2` · `htpasswd` (bcrypt) · `john` · `hashcat` · `openssl rand` · `pwgen` · `/dev/urandom`

## Table of Contents

1. [Generating Secure Passwords & Random Data](#1-generating-secure-passwords--random-data)
2. [SHA Family](#2-sha-family)
3. [MD5](#3-md5)
4. [BLAKE2](#4-blake2)
5. [OpenSSL — All-in-One Digests](#5-openssl--all-in-one-digests)
6. [PBKDF2 via OpenSSL](#6-pbkdf2-via-openssl)
7. [scrypt via OpenSSL](#7-scrypt-via-openssl)
8. [Argon2 CLI](#8-argon2-cli)
9. [bcrypt via htpasswd](#9-bcrypt-via-htpasswd)
10. [Comparing & Verifying Hashes](#10-comparing--verifying-hashes)
11. [Cracking — hashcat & john](#11-cracking--hashcat--john)
12. [Quick Reference Table](#12-quick-reference-table)
13. [Which Algorithm Should I Use?](#13-which-algorithm-should-i-use)

---

## 1. Generating Secure Passwords & Random Data

All entropy sources below read from the kernel's CSPRNG (`/dev/urandom` on Linux, `getentropy()` on modern systems). These are cryptographically secure — suitable for tokens, API keys, salts, and passphrases.

### openssl rand — the go-to tool

`openssl rand` is available everywhere OpenSSL is installed and is the simplest way to generate raw random bytes in hex or base64.

```bash
# 32 random bytes as hex (64 hex chars — good for tokens/API keys)
openssl rand -hex 32

# 32 random bytes as base64 (~44 chars)
openssl rand -base64 32

# 16 bytes as base64 (compact token, ~24 chars)
openssl rand -base64 16

# 64 bytes as base64 (long-form secret key)
openssl rand -base64 64

# Raw binary (pipe into xxd for inspection)
openssl rand 16 | xxd

# Strip base64 padding and newline (clean single-line output)
openssl rand -base64 32 | tr -d '=\n'

# URL-safe base64 (replace +/ with -_)
openssl rand -base64 32 | tr '+/' '-_' | tr -d '=\n'
```

### /dev/urandom — low-level, no dependencies

Direct reads from the kernel CSPRNG. Useful in minimal environments or scripts where you need precise character filtering.

```bash
# 20 alphanumeric characters
cat /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 20; echo

# 32-char password with symbols
cat /dev/urandom | tr -dc 'a-zA-Z0-9!@#$%^&*()-_=+' | head -c 32; echo

# Lowercase hex (like a short UUID fragment)
cat /dev/urandom | tr -dc '0-9a-f' | head -c 32; echo

# 5-word passphrase from the system dictionary (diceware-style)
shuf -n 5 /usr/share/dict/words | tr '\n' '-' | sed 's/-$/\n/'

# Generate a random salt (16 bytes hex) for use with argon2/scrypt
cat /dev/urandom | head -c 16 | xxd -p | tr -d '\n'; echo
```

### gpg --gen-random — NIST-quality randomness

`gpg` exposes three "quality levels" of randomness. Level 1 uses `/dev/urandom`, level 2 uses `/dev/random` (may block), level 0 is pseudo-random.

```bash
# 20 bytes of strong random data as base64 (quality level 1)
gpg --gen-random 1 20 | base64

# 32 bytes (quality level 2 — strongest, may block waiting for entropy)
gpg --gen-random 2 32 | base64

# Hex output via xxd
gpg --gen-random 1 16 | xxd -p | tr -d '\n'; echo
```

### pwgen — human-memorable passwords

`pwgen` is purpose-built for generating pronounceable, human-friendly passwords.

```bash
# Install
sudo apt install pwgen        # Debian/Ubuntu
sudo dnf install pwgen        # Fedora/RHEL
brew install pwgen            # macOS

# 20-character password, 1 result
pwgen 20 1

# 32-character, fully random (not pronounceable), 1 result
pwgen -s 32 1

# Include at least 1 capital, 1 number, 1 symbol
pwgen -cnys 20 1

# Generate 10 passwords of length 16
pwgen 16 10

# No vowels (avoids accidental rude words — useful for generated usernames)
pwgen -v 12 5
```

| Flag | Meaning |
|---|---|
| `-s` | Fully random (not pronounceable) |
| `-c` | Include uppercase |
| `-n` | Include numbers |
| `-y` | Include symbols |
| `-v` | No vowels |
| `-B` | Avoid ambiguous chars (0/O, 1/l/I) |

### apg — advanced password generator

`apg` generates pronounceable or random passwords with fine-grained rules.

```bash
# Install
sudo apt install apg

# 6 pronounceable passwords of length 12
apg -n 6 -m 12

# Random passwords (not pronounceable), length 20
apg -a 1 -n 5 -m 20 -M SNCL   # S=symbols N=numbers C=caps L=lowercase

# Exclude ambiguous characters (no 0/O/l/1)
apg -a 1 -n 3 -m 16 -E 0O1lI
```

### Diceware / EFF wordlist passphrase

A proper diceware passphrase from the EFF large wordlist gives ~12.9 bits of entropy per word. 6 words = ~77 bits — stronger than most random passwords.

```bash
# Download the EFF large wordlist (one-time)
curl -sO https://www.eff.org/files/2016/07/18/eff_large_wordlist.txt

# Simulate 5 dice rolls and look up words (manual diceware)
for i in {1..5}; do
  roll=$(( ( RANDOM % 6 + 1 ) * 10000 + ( RANDOM % 6 + 1 ) * 1000 + \
           ( RANDOM % 6 + 1 ) * 100  + ( RANDOM % 6 + 1 ) * 10   + \
           ( RANDOM % 6 + 1 ) ))
  grep "^${roll}" eff_large_wordlist.txt | awk '{print $2}'
done | tr '\n' '-' | sed 's/-$/\n/'

# Alternatively: pick 6 random words from the system dictionary
shuf -n 6 /usr/share/dict/words | paste -sd '-'
```

### Quick comparison — which generator to use?

| Tool | Best for | Entropy source | Notes |
|---|---|---|---|
| `openssl rand` | Tokens, API keys, salts | CSPRNG | Available everywhere |
| `/dev/urandom` | Scripting, custom charsets | Kernel CSPRNG | Filter with `tr` |
| `gpg --gen-random` | Highest-quality randomness | `/dev/random` | May block |
| `pwgen` | Human-typed passwords | CSPRNG | Pronounceable option |
| `apg` | Policy-enforced passwords | CSPRNG | Fine-grained rules |
| Diceware | Memorable passphrases | Physical dice / RANDOM | Highest memorability |

> **OPSEC —** `openssl rand -base64 32 | tr -d '=\n'` is the one-liner to remember. It works on every system with OpenSSL, outputs URL-safe-ish base64, and requires zero extra packages. Use it for salts, CSRF tokens, session secrets, and API keys.

---

## 2. SHA Family

The `sha*sum` utilities ship with every Linux distro (`coreutils`). They're fast, UNIX-native, and output `<hash> <filename>` or `<hash> -` when reading from stdin.

### Hash a string

```bash
# SHA-256
echo -n "Password123" | sha256sum
# -n strips the trailing newline — ALWAYS use it, or your hash will be wrong

# SHA-512
echo -n "Password123" | sha512sum

# SHA-1 (legacy — avoid for passwords)
echo -n "Password123" | sha1sum

# SHA-224 / SHA-384
echo -n "Password123" | sha224sum
echo -n "Password123" | sha384sum
```

### Hash a file

```bash
sha256sum /etc/passwd
sha512sum secret.txt
```

### Strip the filename from output (hash only)

```bash
echo -n "Password123" | sha256sum | cut -d' ' -f1
```

### Verify a file against a known hash

```bash
# Create a checksum file
sha256sum important.iso > important.iso.sha256

# Verify later
sha256sum -c important.iso.sha256
# Output: important.iso: OK
```

### Hash multiple files at once

```bash
sha256sum file1.txt file2.txt file3.txt > checksums.txt
sha256sum -c checksums.txt
```

> **Note —** SHA-256/512 are **cryptographic digests**, not password hashing functions. They have no salt and no work factor — never store passwords with them directly.

---

## 3. MD5

```bash
# Hash a string
echo -n "Password123" | md5sum

# Hash a file
md5sum /etc/shadow

# macOS equivalent (if you're on a Mac)
md5 -s "Password123"
md5 /etc/shadow
```

> **Warning —** MD5 is **broken** for security purposes. Collisions are trivially found. Use it only for file integrity checks where you trust the source. Never for passwords.

---

## 4. BLAKE2

BLAKE2 is faster than SHA-3 and SHA-2, still cryptographically secure, and built into modern Linux (`coreutils >= 8.25`).

```bash
# BLAKE2b-512 (default b2sum)
echo -n "Password123" | b2sum

# Hash a file
b2sum firmware.bin

# BLAKE2s-256 — use openssl for this variant (see section 5)
openssl dgst -blake2s256 firmware.bin
```

---

## 5. OpenSSL — All-in-One Digests

`openssl dgst` supports every digest OpenSSL knows about. Useful when you need a specific algorithm not covered by `*sum` tools.

### Basic usage

```bash
openssl dgst -sha256 file.txt
openssl dgst -sha512 file.txt
openssl dgst -sha3-256 file.txt
openssl dgst -sha3-512 file.txt
openssl dgst -blake2b512 file.txt
openssl dgst -blake2s256 file.txt
openssl dgst -sm3 file.txt              # Chinese national standard
```

### Hash a string (no file)

```bash
echo -n "Password123" | openssl dgst -sha256
echo -n "Password123" | openssl dgst -sha3-512
```

### Output raw hex only (no label)

```bash
echo -n "Password123" | openssl dgst -sha256 | awk '{print $2}'
```

### HMAC (keyed hash — authentication)

```bash
echo -n "message" | openssl dgst -sha256 -hmac "supersecretkey"
```

### List all available digest algorithms

```bash
openssl list -digest-commands
openssl list -digest-algorithms        # more complete list
```

---

## 6. PBKDF2 via OpenSSL

PBKDF2 (Password-Based Key Derivation Function 2) is a proper password KDF — it adds salt and stretching via a configurable iteration count. Used in WPA2-PSK, LUKS, iOS keychain, and many more.

```bash
# Basic: PBKDF2-HMAC-SHA256, 100000 iterations, 32-byte key
echo -n "Password123" | openssl kdf \
  -kdfopt digest:SHA256 \
  -kdfopt pass:Password123 \
  -kdfopt salt:$(openssl rand -hex 16) \
  -kdfopt iter:100000 \
  -keylen 32 \
  PBKDF2

# With a fixed known salt (for reproducibility in testing)
openssl kdf \
  -kdfopt digest:SHA256 \
  -kdfopt pass:Password123 \
  -kdfopt salt:deadbeefcafe1234 \
  -kdfopt iter:600000 \
  -keylen 32 \
  PBKDF2
```

### PBKDF2 the classic way (enc -pbkdf2, outputs base64-wrapped)

```bash
# Encrypt (also derives a key from the password using PBKDF2)
echo "secret data" | openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -pass pass:Password123 | base64

# The openssl enc route is more for encryption than storing a password hash,
# but it demonstrates PBKDF2 key derivation in action.
```

> **Recommended iterations (2024):** 600,000+ for SHA-256, 210,000 for SHA-512 (OWASP).

---

## 7. scrypt via OpenSSL

scrypt is a memory-hard KDF. It's deliberately expensive in both CPU **and** RAM, making GPU/ASIC attacks much harder. Used in Litecoin, LUKS2, and many modern password stores.

### Parameters

| Param | Meaning | Typical value |
|---|---|---|
| `N` (cpu-count) | CPU/memory cost (must be power of 2) | 32768–1048576 |
| `r` (block-size) | Block size | 8 |
| `p` (parallel) | Parallelisation | 1 |

Memory used ≈ `128 × N × r` bytes. At N=32768, r=8: ~32 MB.

```bash
# Generate a scrypt-derived key (32 bytes)
openssl kdf \
  -kdfopt pass:Password123 \
  -kdfopt salt:$(openssl rand -hex 16) \
  -kdfopt n:32768 \
  -kdfopt r:8 \
  -kdfopt p:1 \
  -keylen 32 \
  scrypt

# Higher security (128 MB RAM, slower)
openssl kdf \
  -kdfopt pass:Password123 \
  -kdfopt salt:randomsalthere \
  -kdfopt n:1048576 \
  -kdfopt r:8 \
  -kdfopt p:1 \
  -keylen 64 \
  scrypt
```

> **Tip —** Always generate a random salt per-password with `openssl rand -hex 16` and store it alongside the hash. Without the salt you can't re-derive the hash.

---

## 8. Argon2 CLI

Argon2 is the **winner of the 2015 Password Hashing Competition** and the current gold standard for password hashing. Three variants:

| Variant | Use case |
|---|---|
| `argon2d` | GPU-resistance, not side-channel safe |
| `argon2i` | Side-channel safe (filling stations, enclaves) |
| `argon2id` | Hybrid — **recommended for general use** |

### Install

```bash
# Debian/Ubuntu
sudo apt install argon2

# Fedora/RHEL
sudo dnf install argon2

# Arch
sudo pacman -S argon2

# macOS
brew install argon2
```

### Basic usage

```bash
# Hash using argon2id (recommended)
echo -n "Password123" | argon2 "somesalt16bytes!" -id

# Output looks like:
# Type:          Argon2id
# Iterations:    3
# Memory:        65536 KB
# Parallelism:   4
# Hash:          <hex>
# Encoded:       $argon2id$v=19$m=65536,t=3,p=4$...
# Verification ok
```

### With custom parameters

```bash
# -t = time cost (iterations), -m = memory (2^m KB), -p = threads, -l = output length
echo -n "Password123" | argon2 "$(openssl rand -hex 8)" -id -t 3 -m 17 -p 4 -l 32

# Paranoid settings (512 MB RAM, 10 iterations)
echo -n "Password123" | argon2 "mysalt12345678!!" -id -t 10 -m 19 -p 8 -l 64
```

### Parameter guide (OWASP 2024)

| Profile | `-t` | `-m` | `-p` | RAM |
|---|---|---|---|---|
| Minimum | 1 | 19 | 1 | 512 MB |
| Balanced | 3 | 17 | 4 | 128 MB |
| Low-memory | 5 | 14 | 2 | 16 MB |

### Get only the encoded hash (PHC string format)

```bash
echo -n "Password123" | argon2 "mysalt12345678!!" -id -e
# Output: $argon2id$v=19$m=65536,t=3,p=4$<base64salt>$<base64hash>
```

### Verify a password against a stored hash

```bash
echo -n "Password123" | argon2 "mysalt12345678!!" -id -v \
  '$argon2id$v=19$m=65536,t=3,p=4$bXlzYWx0MTIzNDU2NzgheA$<hash>'
# Output: Verification ok  (exit 0)  or  Verification failed  (exit 1)
```

---

## 9. bcrypt via htpasswd

The standalone `bcrypt` CLI is rarely packaged by distros. The easiest way to use bcrypt from the command line is `htpasswd` (from the `apache2-utils` package), which natively outputs `$2y$` bcrypt hashes.

### Install

```bash
sudo apt install apache2-utils   # Debian/Ubuntu
sudo dnf install httpd-tools     # Fedora/RHEL
brew install httpd               # macOS
```

### Hash a password (bcrypt, cost 12)

```bash
htpasswd -bnBC 12 "" "Password123" | tr -d ':\n'
# -b = batch mode (password on CLI)
# -n = print to stdout (don't write a file)
# -B = force bcrypt
# -C = cost factor (4–31, default 5, use >=12 in production)
# The "" is a dummy username; tr strips it and the trailing newline
```

### Output looks like

```text
$2y$12$GiY13p14H9JQ3jHn3/XCDO6XuIBMH6PetA8SFO3T0d2EqLRUDtL7.
```

The `$2y$` prefix identifies this as a bcrypt hash. `$12$` is the cost factor.

### Verify (htpasswd can't verify standalone — use python3 one-liner)

```bash
python3 -c "
import bcrypt, sys
h = b'\$2y\$12\$...'   # paste your stored hash here
p = b'Password123'
print('MATCH' if bcrypt.checkpw(p, h) else 'NO MATCH')
"
```

### Cost factor timing guide

```bash
# Benchmark: how long does cost 12 take on your machine?
time htpasswd -bnBC 12 "" "benchmark" > /dev/null
# Aim for 250ms–1s per hash in production
```

| Cost | Approx time (modern CPU) |
|---|---|
| 10 | ~100 ms |
| 12 | ~400 ms |
| 14 | ~1.5 s |
| 16 | ~6 s |

> **Note —** bcrypt hard limit: bcrypt only hashes the first **72 bytes** of input. Passwords longer than 72 chars are silently truncated. Pre-hash with SHA-256 if you need to support longer passphrases.

---

## 10. Comparing & Verifying Hashes

### Constant-time comparison (avoid timing attacks in scripts)

```bash
# Never use == in bash for hash comparison — it's not constant-time.
# Use python3 for safe comparison:
python3 -c "
import hmac
a = 'aabbcc112233'
b = 'aabbcc112233'
print('MATCH' if hmac.compare_digest(a, b) else 'NO MATCH')
"
```

### Verify a SHA-256 checksum manually

```bash
EXPECTED="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
ACTUAL=$(echo -n "" | sha256sum | cut -d' ' -f1)
[ "$EXPECTED" = "$ACTUAL" ] && echo "OK" || echo "MISMATCH"
```

### Check if a file has been tampered with

```bash
# Store hash before sending/storing
sha256sum important.bin > important.bin.sha256

# Verify on the other end
sha256sum -c important.bin.sha256
```

---

## 11. Cracking — hashcat & john

### hashcat — GPU-accelerated

```bash
# Identify hash type: https://hashcat.net/wiki/doku.php?id=hashcat
hashcat --identify hash.txt

# Dictionary attack
hashcat -m 0    hash.txt wordlist.txt          # MD5
hashcat -m 100  hash.txt wordlist.txt          # SHA-1
hashcat -m 1400 hash.txt wordlist.txt          # SHA-256
hashcat -m 1800 hash.txt wordlist.txt          # sha512crypt ($6$)
hashcat -m 3200 hash.txt wordlist.txt          # bcrypt ($2*)
hashcat -m 13400 hash.txt wordlist.txt         # KeePass
hashcat -m 16300 hash.txt wordlist.txt         # Ethereum Pre-Sale Wallet

# Rules (mangling) — -r applies transformation rules
hashcat -m 0 hash.txt wordlist.txt -r /usr/share/hashcat/rules/best64.rule

# Brute force (mask attack) — ?l=lowercase, ?u=upper, ?d=digit, ?s=special
hashcat -m 0 hash.txt -a 3 ?l?l?l?l?l?l?l?l  # 8 lowercase chars
hashcat -m 0 hash.txt -a 3 ?u?l?l?l?d?d?d?d  # Password1234 pattern

# Combination attack (combine two wordlists)
hashcat -m 0 hash.txt -a 1 wordlist1.txt wordlist2.txt

# Show cracked passwords
hashcat -m 0 hash.txt --show

# Resume a session
hashcat --session mysession --restore
```

### john the ripper — CPU-based

```bash
# Auto-detect format and crack
john hash.txt

# With a wordlist
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt

# Specify format explicitly
john --format=bcrypt   hash.txt --wordlist=rockyou.txt
john --format=sha512crypt hash.txt --wordlist=rockyou.txt
john --format=argon2   hash.txt --wordlist=rockyou.txt   # needs jumbo build

# Rules
john --wordlist=rockyou.txt --rules=best64 hash.txt

# Incremental (brute force)
john --incremental hash.txt

# Show cracked passwords
john --show hash.txt

# List supported formats
john --list=formats | grep -i bcrypt
john --list=formats | grep -i argon
```

### Hash format quick reference for hashcat `-m`

| Algorithm | `-m` value |
|---|---|
| MD5 | 0 |
| SHA-1 | 100 |
| SHA-256 | 1400 |
| SHA-512 | 1700 |
| BLAKE2b-512 | 600 |
| bcrypt `$2*$` | 3200 |
| sha256crypt `$5$` | 7400 |
| sha512crypt `$6$` | 1800 |
| PBKDF2-HMAC-SHA256 | 10900 |
| scrypt | 8900 |
| Argon2id | 35700 |
| Argon2i | 35600 |
| Argon2d | 35500 |

---

## 12. Quick Reference Table

| Algorithm | CLI Tool | Install | Salt | Work Factor | Password Safe? |
|---|---|---|---|---|---|
| MD5 | `md5sum` | coreutils | No | No | Never |
| SHA-256 | `sha256sum` | coreutils | No | No | Never |
| SHA-512 | `sha512sum` | coreutils | No | No | Never |
| BLAKE2b | `b2sum` | coreutils | No | No | Never |
| PBKDF2 | `openssl kdf` | openssl | Yes | iterations | OK if tuned |
| scrypt | `openssl kdf` | openssl | Yes | N, r, p | Good |
| bcrypt | `htpasswd -B` | apache2-utils | Yes (built-in) | cost 4–31 | Good |
| Argon2id | `argon2` | argon2 pkg | Yes | t, m, p | Best |

---

## 13. Which Algorithm Should I Use?

```text
Storing passwords?
    └─ Use Argon2id (first choice) or bcrypt (widely supported)
    └─ PBKDF2 only if FIPS compliance is required

File integrity / checksums?
    └─ SHA-256 or SHA-512 (standard)
    └─ BLAKE2b if you want faster with same security level

HMAC / message authentication?
    └─ HMAC-SHA256 or HMAC-SHA512 (openssl dgst -hmac)

Key derivation from a password (e.g. for encryption)?
    └─ scrypt or Argon2id
    └─ PBKDF2 (FIPS environments)

Never use MD5 or SHA-1 for security-sensitive work.
```

> **OPSEC reminder —** Avoid passing passwords as CLI arguments (`-pass pass:...`) on shared/production systems — they appear in `ps aux` and shell history. Use `stdin`, env vars, or a secure prompt where possible.
