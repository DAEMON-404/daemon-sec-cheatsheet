---
title: "OpenSSL"
description: "OpenSSL: keys, CSRs, certs, x509 inspection, PEM/DER conversion, s_client and encryption."
category: cryptography
tags: [cryptography, tls, certificates]
tools: [OpenSSL]
difficulty: intermediate
updated: "2026-08-09"
source: "repo:Misc/openssl-cheatsheet.pdf"
---

# OpenSSL

Full-featured toolkit for SSL/TLS and general-purpose cryptography. In pentesting it is essential for certificate manipulation, TLS reconnaissance, and cryptographic operations.

> **Note —** Pre-installed on most Linux distros. Invaluable for extracting credentials from certificates, testing SSL configs, and manipulating cryptographic data during engagements.

```bash
# Install (Debian/Kali)
sudo apt update && sudo apt install openssl

# Version + build info
openssl version -a
```

---

## PKCS12 / PFX Operations

PKCS#12 (`.pfx`, `.p12`) files bundle certificates and private keys. Frequently found during pentests — often carrying auth credentials.

> **Warning —** PFX files from Windows environments often contain domain authentication certificates. Extracting these can give direct access via Evil-WinRM or SSH.

```bash
# Extract private key (prompts for password)
openssl pkcs12 -in cert.pfx -nocerts -out key.pem

# Extract private key unencrypted (-nodes = no DES)
openssl pkcs12 -in cert.pfx -nocerts -out key.pem -nodes

# Extract certificate only (no keys)
openssl pkcs12 -in cert.pfx -nokeys -out cert.pem

# Extract full certificate chain
openssl pkcs12 -in cert.pfx -nokeys -chain -out fullchain.pem

# Extract everything to a single file
openssl pkcs12 -in cert.pfx -out all.pem -nodes

# Extract CA certificates
openssl pkcs12 -in cert.pfx -cacerts -out ca.pem -nokeys
```

> **Tip —** Common PFX passwords to try: empty (just press Enter), `password`, `changeit`, `123456`, `mimikatz`.

```bash
# Create PFX from separate key + cert
openssl pkcs12 -export -out certificate.pfx \
  -inkey private.key -in certificate.crt

# Include CA chain
openssl pkcs12 -export -out certificate.pfx \
  -inkey private.key -in certificate.crt \
  -certfile ca-chain.crt
```

---

## Certificate Operations

```bash
# View certificate in human-readable form
openssl x509 -in cert.pem -text -noout

# View specific fields
openssl x509 -in cert.pem -subject -noout
openssl x509 -in cert.pem -issuer  -noout
openssl x509 -in cert.pem -dates   -noout
openssl x509 -in cert.pem -serial  -noout

# View Subject Alternative Names (SANs)
openssl x509 -in cert.pem -text -noout | grep -A1 "Subject Alternative Name"
```

### Convert formats

```bash
# PEM <-> DER
openssl x509 -in cert.pem -outform DER -out cert.der
openssl x509 -in cert.der -inform DER  -out cert.pem

# PEM -> PKCS7
openssl crl2pkcs7 -nocrl -certfile cert.pem -out cert.p7b

# PKCS7 -> PEM
openssl pkcs7 -in cert.p7b -print_certs -out cert.pem
```

### Verify

```bash
# Verify certificate against CA
openssl verify -CAfile ca.pem cert.pem

# Verify with intermediate chain
openssl verify -CAfile ca.pem -untrusted intermediate.pem cert.pem

# Check whether a key matches a certificate (MD5 of moduli must match)
openssl x509 -noout -modulus -in cert.pem | openssl md5
openssl rsa  -noout -modulus -in key.pem  | openssl md5
```

---

## Key Operations

```bash
# RSA private key (2048-bit)
openssl genrsa -out private.key 2048

# RSA key with passphrase (4096-bit)
openssl genrsa -aes256 -out private.key 4096

# EC private key
openssl ecparam -genkey -name secp384r1 -out ec_private.key

# ED25519 key
openssl genpkey -algorithm ED25519 -out ed25519.key

# View RSA private key
openssl rsa -in private.key -text -noout

# Extract public key
openssl rsa -in private.key -pubout -out public.key

# Check key validity
openssl rsa -in private.key -check

# Remove passphrase from key
openssl rsa -in encrypted.key -out decrypted.key
openssl ec  -in encrypted_ec.key -out decrypted_ec.key
```

> **Warning —** Removing passphrases creates unprotected keys. Handle with care and delete when no longer needed.

---

## SSL/TLS Testing

```bash
# Basic SSL connection
openssl s_client -connect host:443

# Show full certificate chain
openssl s_client -connect host:443 -showcerts

# Specify SNI
openssl s_client -connect host:443 -servername hostname

# Force a TLS version
openssl s_client -connect host:443 -tls1_2
openssl s_client -connect host:443 -tls1_3
```

### Certificate reconnaissance

```bash
# Extract server certificate details
echo | openssl s_client -connect host:443 2>/dev/null | openssl x509 -text -noout

# Expiration dates
echo | openssl s_client -connect host:443 2>/dev/null | openssl x509 -noout -dates

# Extract SANs (find additional hostnames)
echo | openssl s_client -connect host:443 2>/dev/null | \
  openssl x509 -noout -text | grep -A1 "Subject Alternative"

# Save the server certificate to disk
echo | openssl s_client -connect host:443 2>/dev/null | \
  sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' > server.crt
```

> **Tip —** SANs often reveal internal hostnames, dev servers, and subdomains not publicly listed.

### Config / cipher testing

```bash
# Test a specific cipher
openssl s_client -connect host:443 -cipher 'ECDHE-RSA-AES256-SHA'

# List supported ciphers
openssl ciphers -v 'ALL:COMPLEMENTOFALL'

# Test SSLv3 (POODLE)
openssl s_client -connect host:443 -ssl3

# Probe weak ciphers
openssl s_client -connect host:443 -cipher 'NULL,EXPORT,LOW,DES'
```

### STARTTLS services

```bash
openssl s_client -connect mail.host:25   -starttls smtp
openssl s_client -connect mail.host:143  -starttls imap
openssl s_client -connect mail.host:110  -starttls pop3
openssl s_client -connect ftp.host:21    -starttls ftp
openssl s_client -connect ldap.host:389  -starttls ldap
openssl s_client -connect xmpp.host:5222 -starttls xmpp
```

---

## Encryption & Decryption

```bash
# Symmetric AES-256-CBC (use PBKDF2 for real work)
openssl enc -aes-256-cbc -salt -pbkdf2 -in file.txt  -out file.enc
openssl enc -aes-256-cbc -d    -pbkdf2 -in file.enc  -out file.txt

# Base64-armored output
openssl enc -aes-256-cbc -a -salt -pbkdf2 -in file.txt -out file.enc

# Asymmetric (pkeyutl preferred on modern OpenSSL)
openssl pkeyutl -encrypt -pubin -inkey public.key -in plaintext.txt -out encrypted.bin
openssl pkeyutl -decrypt        -inkey private.key -in encrypted.bin -out plaintext.txt
```

---

## Hashing

```bash
openssl dgst -md5    file.txt
openssl dgst -sha1   file.txt
openssl dgst -sha256 file.txt
openssl dgst -sha512 file.txt

# Hash a string
echo -n "password" | openssl dgst -sha256

# HMAC (keyed)
openssl dgst -sha256 -hmac "secret_key" file.txt
echo -n "message" | openssl dgst -sha256 -hmac "key"
```

---

## Base64

```bash
openssl base64 -in file.bin -out file.b64      # encode
openssl base64 -d -in file.b64 -out file.bin   # decode
echo -n "text" | openssl base64
openssl base64 -A -in file.bin                 # no line breaks
```

---

## Passwords & Random

```bash
# Unix crypt hashes
openssl passwd -1 "password"    # MD5
openssl passwd -5 "password"    # SHA-256
openssl passwd -6 "password"    # SHA-512
openssl passwd -6 -salt "customsalt" "password"
openssl passwd -apr1 "password" # Apache htpasswd

# Random data
openssl rand -hex 32
openssl rand -base64 32
openssl rand -out random.bin 256
```

> **Tip —** `openssl passwd` output can be injected into `/etc/passwd` or `/etc/shadow` during privilege escalation when you can write those files.

---

## CSR & Self-Signed Certificates

```bash
# CSR with a fresh key
openssl req -new -newkey rsa:2048 -nodes -keyout private.key -out request.csr

# CSR from an existing key
openssl req -new -key private.key -out request.csr

# Inspect / verify a CSR
openssl req -in request.csr -text -noout
openssl req -in request.csr -verify

# Self-signed certificate (1 year)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# One-liner with subject
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/CN=localhost/O=Test/C=US"
```

---

## HTB / Engagement Scenarios

```bash
# Windows cert auth via Evil-WinRM
openssl pkcs12 -in user_auth.pfx -nocerts -out user.key -nodes
openssl pkcs12 -in user_auth.pfx -nokeys  -out user.crt
evil-winrm -i target.htb -c user.crt -k user.key -S

# SSH key from a PFX
openssl pkcs12 -in ssh_cert.pfx -nocerts -out id_rsa -nodes
chmod 600 id_rsa
ssh -i id_rsa user@target

# ADCS recon from a certificate
openssl x509 -in cert.pem -text -noout | grep -A5  "Issuer"
openssl x509 -in cert.pem -text -noout | grep -A10 "Extensions"
openssl x509 -in cert.pem -text -noout | grep -i   "principal"   # UPN
```

---

## Common Options Reference

| Option | Description |
|---|---|
| `-in <file>` | Input file |
| `-out <file>` | Output file |
| `-text` | Human-readable text output |
| `-noout` | Suppress encoded output |
| `-nodes` | No DES (unencrypted key) |
| `-nocerts` | Don't output certificates |
| `-nokeys` | Don't output private keys |
| `-passin pass:<pwd>` | Input password |
| `-passout pass:<pwd>` | Output password |
| `-inform DER/PEM` | Input format |
| `-outform DER/PEM` | Output format |
| `-CAfile <file>` | CA certificate file |
| `-verify` | Verify signature / certificate |

---

## Resources

* Official docs: <https://www.openssl.org/docs/>
* Man pages: `man openssl`, `man openssl-x509`

> For **authorized security testing only.** Extracting credentials from certificates or testing SSL configurations without permission is illegal.
