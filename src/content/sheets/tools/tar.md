---
title: "TAR"
description: "tar [OPERATION] [OPTIONS] -f ARCHIVE [FILES...]"
category: tools
tags: ["tools"]
tools: ["GPG", "OpenSSL"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Tools/TAR.md"
---
# The Ultimate `tar` Cheat Sheet

> GNU tar 1.35 | Last updated: April 2026

---

## Core Syntax

```
tar [OPERATION] [OPTIONS] -f ARCHIVE [FILES...]
```

The `-f` flag tells tar you're working with files, not a tape device (the `f` is always required).

---

## Operations (pick one)

|Flag|Long Form|Purpose|
|---|---|---|
|`c`|`--create`|Create a new archive|
|`x`|`--extract`|Extract files from an archive|
|`t`|`--list`|List contents of an archive|
|`r`|`--append`|Append files to the end of an archive (uncompressed only)|
|`u`|`--update`|Append files newer than the copy in the archive (uncompressed only)|
|`d`|`--diff` / `--compare`|Compare archive members against the filesystem|
|`A`|`--concatenate`|Append one tar archive to another|
|`--delete`||Delete members from the archive (uncompressed only)|

---

## Common Modifier Flags

|Flag|Long Form|Purpose|
|---|---|---|
|`v`|`--verbose`|Verbose output (list files processed)|
|`vv`||Extra verbose (show permissions, ownership, size)|
|`f`|`--file`|Specify archive filename|
|`C`|`--directory`|Change to directory before performing operation|
|`p`|`--preserve-permissions`|Preserve file permissions on extraction|
|`P`|`--absolute-names`|Don't strip leading `/` from paths|
|`k`|`--keep-old-files`|Don't overwrite existing files on extraction|
|`--overwrite`||Overwrite existing files on extraction|
|`w`|`--interactive`|Ask for confirmation for every action|
|`--same-owner`||Try to extract with the same ownership|
|`--no-same-owner`||Extract as current user|
|`--numeric-owner`||Use numeric UID/GID (useful for cross-system restores)|
|`--acls`||Preserve POSIX ACLs|
|`--selinux`||Preserve SELinux contexts|
|`--xattrs`||Preserve extended attributes|
|`-h`|`--dereference`|Follow symlinks (archive the target file, not the link)|
|`--hard-dereference`||Follow hard links|
|`--one-file-system`||Stay on one filesystem (don't cross mount points)|
|`-S`|`--sparse`|Handle sparse files efficiently|
|`--totals`||Print total bytes after processing|
|`--checkpoint=N`||Print a progress message every N records|

---

## All Compression Types

GNU tar supports 8 compression filters. Each can be used with `-c` (create) or `-x` (extract).

### Quick Reference

|Algorithm|Short Flag|Long Flag|Extension|Compression Ratio|Speed|Levels|
|---|---|---|---|---|---|---|
|gzip|`-z`|`--gzip`|`.tar.gz` / `.tgz`|Good|Fast|1-9|
|bzip2|`-j`|`--bzip2`|`.tar.bz2` / `.tbz2`|Better|Slow|1-9|
|xz (LZMA2)|`-J`|`--xz`|`.tar.xz` / `.txz`|Best|Slowest|0-9 (+`-e` extreme)|
|zstd|`--zstd`|`--zstd`|`.tar.zst`|Good-Great|Very Fast|1-19 (+`--ultra` to 22)|
|lzip|`--lzip`|`--lzip`|`.tar.lz`|Best|Slow|0-9|
|lzma|`--lzma`|`--lzma`|`.tar.lzma`|Great|Slow|0-9|
|lzop|`--lzop`|`--lzop`|`.tar.lzo`|Lower|Very Fast|1-9|
|compress|`-Z`|`--compress`|`.tar.Z`|Poor|Fast|N/A (legacy)|

### Create with Each Compression Type

```bash
# gzip (most universal)
tar czf archive.tar.gz /path/to/dir

# bzip2 (legacy, still common in older tarballs)
tar cjf archive.tar.bz2 /path/to/dir

# xz (best compression, used by kernel tarballs and distro packages)
tar cJf archive.tar.xz /path/to/dir

# zstd (best speed-to-ratio balance, modern default)
tar --zstd -cf archive.tar.zst /path/to/dir

# lzip
tar --lzip -cf archive.tar.lz /path/to/dir

# lzma (predecessor to xz)
tar --lzma -cf archive.tar.lzma /path/to/dir

# lzop (ultrafast, low ratio)
tar --lzop -cf archive.tar.lzo /path/to/dir

# compress (legacy, avoid)
tar -Zcf archive.tar.Z /path/to/dir

# no compression (plain tarball)
tar cf archive.tar /path/to/dir
```

### Extract with Each Type

```bash
# gzip
tar xzf archive.tar.gz

# bzip2
tar xjf archive.tar.bz2

# xz
tar xJf archive.tar.xz

# zstd
tar --zstd -xf archive.tar.zst

# lzip
tar --lzip -xf archive.tar.lz

# auto-detect compression (GNU tar)
tar xaf archive.tar.gz    # 'a' auto-detects the compressor
tar xf archive.tar.xz     # GNU tar also auto-detects without 'a' in most cases
```

### List Contents Without Extracting

```bash
tar tzf archive.tar.gz                 # gzip
tar tjf archive.tar.bz2                # bzip2
tar tJf archive.tar.xz                 # xz
tar --zstd -tf archive.tar.zst         # zstd
tar tf archive.tar                     # uncompressed
tar tf archive.tar.gz | head -20       # preview first 20 entries
tar tf archive.tar.gz | grep '\\.conf$' # search for .conf files
```

---

## Setting Compression Levels

The `-I` flag (or `--use-compress-program`) lets you pass custom arguments to the compressor, including compression levels. This is how you control the speed/size tradeoff.

### Method 1: The `-I` Flag (Recommended)

```bash
# gzip: levels 1 (fastest) to 9 (smallest), default 6
tar -I 'gzip -1' -cf archive.tar.gz /path/to/dir     # fastest
tar -I 'gzip -6' -cf archive.tar.gz /path/to/dir     # default
tar -I 'gzip -9' -cf archive.tar.gz /path/to/dir     # smallest

# bzip2: levels 1-9, default 9
tar -I 'bzip2 -1' -cf archive.tar.bz2 /path/to/dir   # fastest
tar -I 'bzip2 -9' -cf archive.tar.bz2 /path/to/dir   # smallest (default)

# xz: levels 0-9, default 6. Add -e for extreme mode
tar -I 'xz -0' -cf archive.tar.xz /path/to/dir       # fastest
tar -I 'xz -6' -cf archive.tar.xz /path/to/dir       # default
tar -I 'xz -9' -cf archive.tar.xz /path/to/dir       # smallest
tar -I 'xz -9e' -cf archive.tar.xz /path/to/dir      # extreme (even smaller, much slower)

# zstd: levels 1-19, default 3. --ultra unlocks 20-22
tar -I 'zstd -1' -cf archive.tar.zst /path/to/dir     # fastest
tar -I 'zstd -3' -cf archive.tar.zst /path/to/dir     # default
tar -I 'zstd -19' -cf archive.tar.zst /path/to/dir    # high compression
tar -I 'zstd --ultra -22' -cf archive.tar.zst /path/to/dir  # maximum (memory heavy)

# lzip: levels 0-9, default 6
tar -I 'lzip -9' -cf archive.tar.lz /path/to/dir

# lzop: levels 1-9, default 3
tar -I 'lzop -9' -cf archive.tar.lzo /path/to/dir
```

### Method 2: Environment Variables (gzip/bzip2/xz only)

```bash
# gzip via GZIP env var (deprecated in newer gzip, but still works in most distros)
GZIP=-9 tar czf archive.tar.gz /path/to/dir

# xz via XZ_OPT
XZ_OPT='-9e' tar cJf archive.tar.xz /path/to/dir

# zstd via ZSTD_CLEVEL
ZSTD_CLEVEL=19 tar --zstd -cf archive.tar.zst /path/to/dir
```

---

## Multi-threaded / Parallel Compression

Single-threaded compression is painfully slow on large datasets. Use parallel implementations to utilise all your cores.

### Native Multi-threading

```bash
# xz with -T0 (use all available cores, supported since xz 5.2+)
tar -I 'xz -9e -T0' -cf archive.tar.xz /path/to/dir

# zstd with -T0 (native multi-threading, default since zstd 1.5.7)
tar -I 'zstd -19 -T0' -cf archive.tar.zst /path/to/dir

# zstd with explicit thread count
tar -I 'zstd -19 -T4' -cf archive.tar.zst /path/to/dir
```

### Drop-in Parallel Replacements

```bash
# pigz (parallel gzip, fully compatible output)
tar -I 'pigz -9' -cf archive.tar.gz /path/to/dir
tar -I 'pigz -9 -p 4' -cf archive.tar.gz /path/to/dir    # limit to 4 cores

# pbzip2 (parallel bzip2)
tar -I 'pbzip2 -9' -cf archive.tar.bz2 /path/to/dir
tar -I 'pbzip2 -9 -p4' -cf archive.tar.bz2 /path/to/dir

# lbzip2 (alternative parallel bzip2, often faster decompression)
tar -I lbzip2 -cf archive.tar.bz2 /path/to/dir

# plzip (parallel lzip)
tar -I 'plzip -9' -cf archive.tar.lz /path/to/dir
```

### Install Parallel Tools

```bash
# Debian/Ubuntu
sudo apt install pigz pbzip2 lbzip2 zstd

# RHEL/Fedora
sudo dnf install pigz pbzip2 lbzip2 zstd

# Arch
sudo pacman -S pigz pbzip2 lbzip2 zstd

# macOS
brew install pigz pbzip2 lbzip2 zstd
```

---

## Splitting Archives into Parts

For transferring over networks, fitting onto FAT32 drives (4GB limit), or uploading in chunks.

### Create and Split in One Pipeline

```bash
# Split a gzip archive into 100MB chunks
tar czf - /path/to/dir | split -b 100M - archive.tar.gz.part-

# Split an xz archive into 500MB chunks with numeric suffixes
tar cJf - /path/to/dir | split -b 500M -d - archive.tar.xz.part-

# Split a zstd archive into 1GB chunks
tar --zstd -cf - /path/to/dir | split -b 1G -d - archive.tar.zst.part-

# Split with a custom number of digits in suffix
tar czf - /path/to/dir | split -b 100M -d -a 3 - archive.tar.gz.part-
# produces: archive.tar.gz.part-000, archive.tar.gz.part-001, ...
```

### Split an Existing Archive

```bash
split -b 100M archive.tar.gz archive.tar.gz.part-
```

### Reassemble and Extract

```bash
# Reassemble into a single file, then extract
cat archive.tar.gz.part-* > archive.tar.gz
tar xzf archive.tar.gz

# Or pipe directly without creating the intermediate file
cat archive.tar.gz.part-* | tar xzf -

# For xz
cat archive.tar.xz.part-* | tar xJf -

# For zstd
cat archive.tar.zst.part-* | tar --zstd -xf -
```

### Verify Split Archive Integrity

```bash
# Check the reassembled archive is valid
cat archive.tar.gz.part-* | tar tzf - > /dev/null && echo "OK" || echo "CORRUPT"

# Generate checksums before transfer
sha256sum archive.tar.gz.part-* > checksums.sha256

# Verify after transfer
sha256sum -c checksums.sha256
```

### GNU tar Native Multi-Volume (`-M`)

```bash
# Create multi-volume archive (each volume max 100MB)
tar -cML 100M -f vol1.tar /path/to/dir
# tar will prompt for the next volume name when vol1 fills up

# Extract multi-volume
tar -xMf vol1.tar
# tar prompts for subsequent volumes

# Note: multi-volume archives CANNOT be compressed
# For compressed split archives, use the pipe method above
```

---

## Excluding Files and Directories

```bash
# Exclude a single file or directory
tar czf archive.tar.gz --exclude='*.log' /path/to/dir

# Exclude multiple patterns
tar czf archive.tar.gz \\
  --exclude='*.log' \\
  --exclude='*.tmp' \\
  --exclude='.git' \\
  --exclude='node_modules' \\
  --exclude='__pycache__' \\
  /path/to/dir

# Exclude from a file (one pattern per line)
tar czf archive.tar.gz --exclude-from=exclude.txt /path/to/dir

# Exclude files matching a regex (GNU tar)
tar czf archive.tar.gz --exclude='./src/*.test.js' /path/to/dir

# Exclude version control directories
tar czf archive.tar.gz --exclude-vcs /path/to/dir
# Excludes: .git, .svn, .hg, .bzr, CVS, etc.

# Exclude version control ignores too (.gitignore, .hgignore, etc.)
tar czf archive.tar.gz --exclude-vcs-ignores /path/to/dir

# Exclude backup files (*~, #*#)
tar czf archive.tar.gz --exclude-backups /path/to/dir

# Exclude files if a certain file exists in the directory
tar czf archive.tar.gz --exclude-tag='.nobackup' /path/to/dir

# Exclude caches (directories containing CACHEDIR.TAG)
tar czf archive.tar.gz --exclude-caches /path/to/dir
```

---

## Extracting Specific Files

```bash
# Extract a single file
tar xzf archive.tar.gz path/to/specific/file.txt

# Extract files matching a wildcard
tar xzf archive.tar.gz --wildcards '*.conf'
tar xzf archive.tar.gz --wildcards '*/nginx/*'

# Extract to a specific directory
tar xzf archive.tar.gz -C /opt/restore/

# Extract only newer files (don't overwrite newer existing files)
tar xzf archive.tar.gz --keep-newer-files

# Extract and strip leading path components
tar xzf archive.tar.gz --strip-components=1
# e.g. project-v1.0/src/main.c extracts as src/main.c

tar xzf archive.tar.gz --strip-components=2
# e.g. project-v1.0/src/main.c extracts as main.c
```

---

## Incremental / Differential Backups

GNU tar supports incremental backups using a snapshot file that tracks filesystem state between runs.

```bash
# Level 0: full backup (creates the snapshot file)
tar -g /backup/snapshot.snar -czf /backup/full-$(date +%F).tar.gz /home/user/

# Level 1: incremental (only files changed since the last backup)
tar -g /backup/snapshot.snar -czf /backup/inc-$(date +%F).tar.gz /home/user/

# To force a new full backup, delete or move the snapshot file
rm /backup/snapshot.snar

# Restore: apply full, then each incremental IN ORDER
tar -xzf /backup/full-2026-03-01.tar.gz -g /dev/null -C /restore/
tar -xzf /backup/inc-2026-03-02.tar.gz -g /dev/null -C /restore/
tar -xzf /backup/inc-2026-03-03.tar.gz -g /dev/null -C /restore/
# Note: -g /dev/null on extract tells tar this is an incremental restore
# and it should handle file deletions properly
```

---

## Encryption

tar has no native encryption. Pipe through `gpg` or `openssl` to encrypt.

### With GPG (Symmetric / Passphrase)

```bash
# Create encrypted archive (prompts for passphrase)
tar czf - /path/to/dir | gpg -c --cipher-algo AES256 -o archive.tar.gz.gpg

# Decrypt and extract
gpg -d archive.tar.gz.gpg | tar xzf -

# With a specific recipient's public key (asymmetric)
tar czf - /path/to/dir | gpg -e -r recipient@example.com -o archive.tar.gz.gpg

# Decrypt (requires matching private key)
gpg -d archive.tar.gz.gpg | tar xzf -
```

### With OpenSSL

```bash
# Encrypt with AES-256-CBC (prompts for password)
tar czf - /path/to/dir | openssl enc -aes-256-cbc -salt -pbkdf2 -out archive.tar.gz.enc

# Decrypt and extract
openssl enc -d -aes-256-cbc -pbkdf2 -in archive.tar.gz.enc | tar xzf -
```

### Encrypted Incremental Backup (GPG + tar)

```bash
# Full backup, encrypted
tar -g snapshot.snar -czf - /home/user/ | gpg -c --cipher-algo AES256 -o backup-full.tar.gz.gpg

# Incremental, encrypted
tar -g snapshot.snar -czf - /home/user/ | gpg -c --cipher-algo AES256 -o backup-inc.tar.gz.gpg

# Restore
gpg -d backup-full.tar.gz.gpg | tar -xzf - -g /dev/null -C /restore/
gpg -d backup-inc.tar.gz.gpg | tar -xzf - -g /dev/null -C /restore/
```

### Encrypted + Split

```bash
# Create, compress, encrypt, and split into 100MB chunks
tar czf - /path/to/dir \\
  | gpg -c --cipher-algo AES256 \\
  | split -b 100M -d - archive.tar.gz.gpg.part-

# Reassemble, decrypt, extract
cat archive.tar.gz.gpg.part-* | gpg -d | tar xzf -
```

---

## Sending Archives Over the Network

```bash
# Archive and transfer via SSH in one step
tar czf - /path/to/dir | ssh user@remote 'cat > /backup/archive.tar.gz'

# Extract remotely
tar czf - /path/to/dir | ssh user@remote 'tar xzf - -C /opt/deploy/'

# Pull from remote
ssh user@remote 'tar czf - /remote/dir' | tar xzf - -C /local/restore/

# With zstd for speed
tar --zstd -cf - /path/to/dir | ssh user@remote 'tar --zstd -xf - -C /opt/deploy/'

# With progress bar (requires pv)
tar cf - /path/to/dir | pv | gzip | ssh user@remote 'cat > /backup/archive.tar.gz'

# Encrypted transfer (belt and braces with SSH)
tar czf - /path/to/dir | gpg -c --cipher-algo AES256 | ssh user@remote 'cat > /backup/archive.tar.gz.gpg'
```

---

## Comparing and Verifying Archives

```bash
# Diff: compare archive members against the filesystem
tar dzf archive.tar.gz
# Shows files that differ between the archive and disk

# Verify archive integrity without extracting
tar tzf archive.tar.gz > /dev/null
echo $?    # 0 = OK, non-zero = corrupted

# Test a zstd archive
tar --zstd -tf archive.tar.zst > /dev/null && echo "OK" || echo "CORRUPT"

# Generate a checksum of the archive
sha256sum archive.tar.gz > archive.tar.gz.sha256

# Verify
sha256sum -c archive.tar.gz.sha256
```

---

## Archive Formats

GNU tar can produce several archive formats. Usually you don't need to worry about this, but it matters for edge cases.

```bash
# Specify format explicitly
tar --format=gnu -cf archive.tar /path/to/dir      # GNU format (default)
tar --format=posix -cf archive.tar /path/to/dir     # POSIX.1-2001 (pax) format
tar --format=ustar -cf archive.tar /path/to/dir     # POSIX.1-1988
tar --format=v7 -cf archive.tar /path/to/dir        # Old Unix V7 format
```

|Format|Long Filenames|Large Files (>8GB)|Extended Attributes|Notes|
|---|---|---|---|---|
|gnu|Yes|Yes|No|Default on Linux|
|posix (pax)|Yes|Yes|Yes|Most portable, recommended for cross-platform|
|ustar|255 chars max|No (8GB limit)|No|Older POSIX standard|
|v7|100 chars max|No|No|Legacy, avoid|

---

## Practical Combos and Recipes

### Full System Backup

```bash
tar -I 'zstd -9 -T0' -cpf /backup/system-$(date +%F).tar.zst \\
  --acls --selinux --xattrs \\
  --one-file-system \\
  --exclude='/proc/*' \\
  --exclude='/sys/*' \\
  --exclude='/dev/*' \\
  --exclude='/run/*' \\
  --exclude='/tmp/*' \\
  --exclude='/mnt/*' \\
  --exclude='/media/*' \\
  --exclude='/lost+found' \\
  --exclude='/backup/*' \\
  /
```

### Web Server Backup

```bash
tar -I 'zstd -12 -T0' -cf /backup/webserver-$(date +%F).tar.zst \\
  --exclude='*.log' \\
  --exclude='cache/*' \\
  --exclude='node_modules' \\
  /etc/nginx /etc/letsencrypt /var/www
```

### Quick Grab of Specific File Types

```bash
# Archive only .py files from a project
find /project -name '*.py' -print0 | tar czf python-files.tar.gz --null -T -

# Archive files modified in the last 24 hours
find /path -mtime -1 -print0 | tar czf recent-changes.tar.gz --null -T -

# Archive from a file list
tar czf archive.tar.gz -T filelist.txt
```

### Benchmark Compression Algorithms

```bash
for alg in 'gzip' 'bzip2' 'xz' 'zstd' 'zstd -19' 'xz -9e'; do
  echo "--- $alg ---"
  time tar -I "$alg" -cf /dev/null /path/to/test/dir 2>&1
  echo
done
```

### Disk Image Compression

```bash
# Compress a raw disk image with zstd
dd if=/dev/sda bs=4M status=progress | zstd -T0 > disk-image.zst

# Restore
zstd -d disk-image.zst | dd of=/dev/sda bs=4M status=progress
```

### Progress Bar with `pv`

```bash
# Show progress while creating
tar cf - /large/directory | pv -s $(du -sb /large/directory | cut -f1) | gzip > archive.tar.gz

# Show progress while extracting
pv archive.tar.gz | tar xzf -
```

---

## Gotchas and Limitations

- **Compressed archives cannot be modified.** You cannot use `--update`, `--append`, or `--delete` on `.tar.gz`, `.tar.xz`, etc. Only uncompressed `.tar` files support these operations.
- **Multi-volume archives cannot be compressed.** Use the `split` pipe method instead.
- **Leading `/` is stripped by default.** This is a safety feature. Use `-P` to preserve absolute paths, but be careful on extraction.
- **Sparse file handling** requires `-S` to be passed explicitly.
- **Cross-platform gotchas:** GNU tar extensions (long filenames, ACLs, xattrs) may not be understood by BSD tar or busybox tar. Use `--format=posix` for maximum portability.
- **File ordering is not guaranteed** unless you sort your input file list.
- **xz multi-threaded compression uses a lot of RAM.** Roughly single-thread memory x thread count. Watch out on memory-constrained systems.

---

## When to Use What

| Scenario                              | Algorithm       | Reasoning                                        |
| ------------------------------------- | --------------- | ------------------------------------------------ |
| Daily backups                         | zstd (`-3 -T0`) | Fast, good ratio, multi-threaded by default      |
| Long-term archival                    | xz (`-9e -T0`)  | Best compression ratio, saves storage            |
| Quick one-off / maximum compatibility | gzip            | Available everywhere, fast enough                |
| Software distribution                 | xz              | Standard for kernel tarballs, distro packages    |
| Real-time / filesystem compression    | zstd            | Used by btrfs, Fedora, Ubuntu, Arch for packages |
| Bandwidth-limited transfer            | xz or zstd -19  | Minimise bytes on the wire                       |
| Speed-critical / huge datasets        | lzop or zstd -1 | Minimal CPU overhead                             |
| Legacy systems / old tarballs         | bzip2           | Superseded but still encountered                 |

---

## Portability: `-I` vs `--use-compress-program` vs Explicit Pipes

The `-I` flag behaves **differently** between GNU tar and BSD tar (macOS default). This is one of the most common causes of confusing errors.

### The Problem

|Platform|`-I` Means|
|---|---|
|GNU tar (Linux)|`--use-compress-program` — run this external compressor|
|BSD tar / bsdtar (macOS)|`--include` — include files matching a pattern (same as `-T`)|

So on macOS: `tar -I 'xz -9e' -cf ...` will fail with `Couldn't open xz -9e: No such file or directory` because BSD tar is trying to read a **file list** called `xz -9e`.

### Three Ways to Handle It

```bash
# Method 1: --use-compress-program (works on BOTH GNU and BSD tar)
tar -c --use-compress-program='xz -9e' -f - /path/to/dir > archive.tar.xz

# Method 2: Explicit pipe (most portable, works EVERYWHERE)
tar cf - /path/to/dir | xz -9e > archive.tar.xz

# Method 3: -I flag (GNU tar ONLY — Linux, not macOS)
tar -I 'xz -9e' -cf archive.tar.xz /path/to/dir
```

### Portable Decompression (Explicit Pipe)

```bash
# These work on any system regardless of tar implementation
xz -d < archive.tar.xz | tar xf -
zstd -d < archive.tar.zst | tar xf -
gzip -d < archive.tar.gz | tar xf -
```

### Check Which tar You Have

```bash
tar --version
# GNU tar 1.35  → you have GNU tar, -I works as compress program
# bsdtar 3.x.x  → you have BSD tar, -I means --include, use pipes instead
```

> **Rule of thumb:** If your script needs to run on both Linux and macOS, always use explicit pipes (`tar cf - | compressor`) or `--use-compress-program`. Never rely on `-I`.

---

## Chained Workflows & Pipeline Recipes

The real power of tar comes from chaining it with other Unix tools via pipes. Since tar can write to stdout (`-f -`) and read from stdin (`-f -`), you can build arbitrarily complex pipelines: **compress → encrypt → split → checksum → transfer** — all in a single streaming operation with no intermediate files hitting disk.

### The Pipeline Building Blocks

```
┌──────┐    ┌────────────┐    ┌──────────┐    ┌───────┐    ┌──────────┐
│ tar  │───▶│ compressor │───▶│ encryptor│───▶│ split │───▶│ checksum │
│ -cf -│    │ zstd/xz/gz │    │ gpg/age  │    │       │    │ sha256   │
└──────┘    └────────────┘    └──────────┘    └───────┘    └──────────┘
```

Each block is optional. Mix and match depending on what you need.

---

### Compress + Split (Custom Levels)

When tar's built-in `-z`/`-J`/`--zstd` flags don't let you set a compression level, break the compressor out into its own pipe stage.

```bash
# xz extreme + multi-threaded + split into 1GB parts
tar cf - /path/to/dir \\
  | xz -9e -T0 \\
  | split -b 1G -d -a 3 - archive.tar.xz.part-

# Reassemble and extract
cat archive.tar.xz.part-* | xz -d | tar xf -

# zstd level 19 + multi-threaded + split into 500MB parts
tar cf - /path/to/dir \\
  | zstd -19 -T0 \\
  | split -b 500M -d -a 3 - archive.tar.zst.part-

# Reassemble and extract
cat archive.tar.zst.part-* | zstd -d | tar xf -

# pigz (parallel gzip) level 9 + split into 100MB parts
tar cf - /path/to/dir \\
  | pigz -9 \\
  | split -b 100M -d - archive.tar.gz.part-

# Reassemble and extract
cat archive.tar.gz.part-* | pigz -d | tar xf -
```

---

### Compress + Encrypt + Split (The Full Chain)

The order matters: **always compress before encrypting**. Encrypted data is random and cannot be compressed further.

```bash
# ── With GPG (symmetric) ──
tar cf - /path/to/dir \\
  | zstd -19 -T0 \\
  | gpg -c --cipher-algo AES256 --batch --passphrase-fd 3 3<<<'YourPassphrase' \\
  | split -b 500M -d -a 3 - archive.tar.zst.gpg.part-

# Reassemble, decrypt, decompress, extract
cat archive.tar.zst.gpg.part-* \\
  | gpg -d --batch --passphrase 'YourPassphrase' \\
  | zstd -d \\
  | tar xf -

# ── With GPG (asymmetric / public key) ──
tar cf - /path/to/dir \\
  | xz -9e -T0 \\
  | gpg -e -r recipient@example.com \\
  | split -b 1G -d -a 3 - archive.tar.xz.gpg.part-

# Recipient reassembles, decrypts, extracts
cat archive.tar.xz.gpg.part-* | gpg -d | xz -d | tar xf -

# ── With age (modern GPG alternative, simpler) ──
tar cf - /path/to/dir \\
  | zstd -19 -T0 \\
  | age -r age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p \\
  > archive.tar.zst.age

# Decrypt and extract
age -d -i key.txt archive.tar.zst.age | zstd -d | tar xf -

# ── With age + split ──
tar cf - /path/to/dir \\
  | zstd -19 -T0 \\
  | age -r age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p \\
  | split -b 500M -d -a 3 - archive.tar.zst.age.part-

cat archive.tar.zst.age.part-* | age -d -i key.txt | zstd -d | tar xf -

# ── With OpenSSL ──
tar cf - /path/to/dir \\
  | xz -9e -T0 \\
  | openssl enc -aes-256-cbc -salt -pbkdf2 \\
  | split -b 500M -d -a 3 - archive.tar.xz.enc.part-

cat archive.tar.xz.enc.part-* \\
  | openssl enc -d -aes-256-cbc -pbkdf2 \\
  | xz -d \\
  | tar xf -
```

---

### Compress + Split + Checksum (Integrity Verification)

Generate checksums for each split part so you can verify after transfer.

```bash
# Create, compress, split, then checksum
tar cf - /path/to/dir | zstd -19 -T0 | split -b 500M -d -a 3 - archive.tar.zst.part-
sha256sum archive.tar.zst.part-* > archive.tar.zst.sha256

# After transfer, verify
sha256sum -c archive.tar.zst.sha256

# Or inline: tee into sha256sum while splitting
tar cf - /path/to/dir \\
  | zstd -19 -T0 \\
  | tee >(sha256sum > archive-whole.sha256) \\
  | split -b 500M -d -a 3 - archive.tar.zst.part-
```

---

### Compress + Encrypt + Split + Checksum (Full Paranoia Pipeline)

```bash
# ── CREATE ──
tar cf - /path/to/dir \\
  | zstd -19 -T0 \\
  | gpg -c --cipher-algo AES256 \\
  | split -b 500M -d -a 3 - archive.tar.zst.gpg.part-

# Checksum all parts
sha256sum archive.tar.zst.gpg.part-* > checksums.sha256

# ── VERIFY + RESTORE ──
sha256sum -c checksums.sha256 && \\
cat archive.tar.zst.gpg.part-* | gpg -d | zstd -d | tar xf - -C /restore/
```

---

### Compress + Progress Bar + Split

Use `pv` (pipe viewer) to monitor progress at any stage of the pipeline.

```bash
# Show progress while compressing and splitting
tar cf - /path/to/dir \\
  | pv -s $(du -sb /path/to/dir | cut -f1) -N "tar" \\
  | zstd -19 -T0 \\
  | pv -N "zstd" \\
  | split -b 500M -d -a 3 - archive.tar.zst.part-

# Show progress while reassembling and extracting
cat archive.tar.zst.part-* \\
  | pv -N "reassemble" \\
  | zstd -d \\
  | tar xf - -C /restore/

# Progress bar with encryption
tar cf - /path/to/dir \\
  | pv -s $(du -sb /path/to/dir | cut -f1) \\
  | zstd -19 -T0 \\
  | gpg -c --cipher-algo AES256 \\
  > archive.tar.zst.gpg

# pv -W (wait) is useful when piping into gpg since gpg prompts for a
# passphrase before processing — -W delays the progress bar until data flows
tar cf - /path/to/dir \\
  | zstd -19 -T0 \\
  | pv -W \\
  | gpg -c --cipher-algo AES256 \\
  > archive.tar.zst.gpg
```

---

### Compress + Network Transfer (SSH)

Stream directly to a remote host — nothing touches local disk except the source.

```bash
# ── Push: local → remote (zstd, multi-threaded) ──
tar cf - /path/to/dir \\
  | zstd -19 -T0 \\
  | ssh user@remote 'zstd -d | tar xf - -C /opt/deploy/'

# ── Push: local → remote (save as file on remote) ──
tar cf - /path/to/dir \\
  | zstd -19 -T0 \\
  | ssh user@remote 'cat > /backup/archive.tar.zst'

# ── Pull: remote → local ──
ssh user@remote 'tar cf - /remote/dir | zstd -T0' \\
  | zstd -d \\
  | tar xf - -C /local/restore/

# ── Push with progress ──
tar cf - /path/to/dir \\
  | pv -s $(du -sb /path/to/dir | cut -f1) \\
  | zstd -T0 \\
  | ssh user@remote 'zstd -d | tar xf - -C /opt/deploy/'

# ── Clone directory between hosts (one-liner) ──
ssh user@source 'tar cf - /data | zstd -T0' \\
  | ssh user@dest 'zstd -d | tar xf - -C /'
```

---

### Compress + Network Transfer (Netcat — No SSH Overhead)

Fastest possible transfer on a trusted LAN. No encryption, no SSH overhead.

```bash
# ── Receiver (start first) ──
nc -l -p 9000 | zstd -d | tar xf - -C /restore/

# ── Sender ──
tar cf - /path/to/dir | zstd -T0 | nc receiver-host 9000

# ── With progress on sender side ──
tar cf - /path/to/dir \\
  | pv -s $(du -sb /path/to/dir | cut -f1) \\
  | zstd -T0 \\
  | nc receiver-host 9000

# ── With inline checksum verification ──
# Sender (prints md5 to stderr after transfer)
tar cf - /path/to/dir | zstd -T0 | tee >(md5sum >&2) | nc receiver-host 9000

# Receiver (prints md5 to stderr after receiving)
nc -l -p 9000 | tee >(md5sum >&2) | zstd -d | tar xf - -C /restore/
# Compare the two md5 hashes — they should match
```

---

### Compress + Encrypt + Network Transfer

```bash
# ── Push encrypted archive over SSH ──
tar cf - /path/to/dir \\
  | zstd -19 -T0 \\
  | gpg -c --cipher-algo AES256 \\
  | ssh user@remote 'cat > /backup/archive.tar.zst.gpg'

# ── Pull, decrypt, extract in one shot ──
ssh user@remote 'cat /backup/archive.tar.zst.gpg' \\
  | gpg -d \\
  | zstd -d \\
  | tar xf - -C /local/restore/

# ── Netcat + encryption (for untrusted networks without SSH) ──
# Receiver:
nc -l -p 9000 | gpg -d | zstd -d | tar xf - -C /restore/

# Sender:
tar cf - /path/to/dir | zstd -T0 | gpg -c --cipher-algo AES256 | nc receiver-host 9000
```

---

### Incremental Backup + Compress + Encrypt + Split

Full automated backup pipeline with incrementals.

```bash
SNAP="/backup/snapshot.snar"
DATE=$(date +%F)

# ── Full backup (first run or when snapshot is deleted) ──
tar -g "$SNAP" -cf - /home/user \\
  | zstd -19 -T0 \\
  | gpg -c --cipher-algo AES256 \\
  | split -b 1G -d -a 3 - "/backup/full-${DATE}.tar.zst.gpg.part-"
sha256sum /backup/full-${DATE}.tar.zst.gpg.part-* > "/backup/full-${DATE}.sha256"

# ── Incremental backup (subsequent runs) ──
tar -g "$SNAP" -cf - /home/user \\
  | zstd -12 -T0 \\
  | gpg -c --cipher-algo AES256 \\
  > "/backup/inc-${DATE}.tar.zst.gpg"
sha256sum "/backup/inc-${DATE}.tar.zst.gpg" >> "/backup/inc-${DATE}.sha256"

# ── Restore: full first, then each incremental in order ──
sha256sum -c /backup/full-2026-03-01.sha256 && \\
cat /backup/full-2026-03-01.tar.zst.gpg.part-* \\
  | gpg -d | zstd -d | tar xf - -g /dev/null -C /restore/

gpg -d /backup/inc-2026-03-02.tar.zst.gpg \\
  | zstd -d | tar xf - -g /dev/null -C /restore/
```

---

### Exclude + Find + Compress + Encrypt (Surgical Archives)

```bash
# Archive only files modified in last 7 days, compress with zstd, encrypt with age
find /project -mtime -7 -type f -print0 \\
  | tar cf - --null -T - \\
  | zstd -19 -T0 \\
  | age -r age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p \\
  > recent-changes.tar.zst.age

# Archive specific file types, exclude build artifacts, compress + split
find /project \begin{raycast-math} -name '*.py' -o -name '*.rs' -o -name '*.toml' \end{raycast-math} -print0 \\
  | tar cf - --null -T - \\
  --exclude='target' \\
  --exclude='__pycache__' \\
  | zstd -19 -T0 \\
  | split -b 100M -d -a 3 - source-code.tar.zst.part-
```

---

### Extract to Pipe (Process Each File)

Use `--to-command` to pipe each extracted file into a program instead of writing to disk.

```bash
# Pipe every extracted file through a processor (e.g. wc -l to count lines)
tar xf archive.tar.gz --to-command='wc -l'

# The filename is available inside --to-command as $TAR_FILENAME
tar xf archive.tar.gz --to-command='echo "Processing: $TAR_FILENAME"'

# Extract and pipe each file into a script
tar xf archive.tar.gz --to-command='/path/to/your/script.sh'
```

---

### Copy Directory Trees (Local Cloning)

The fastest way to copy a directory preserving all metadata — faster than `cp -a` or `rsync` for local copies.

```bash
# Clone a directory tree preserving permissions, ownership, timestamps
tar cf - -C /source/dir . | tar xpf - -C /dest/dir

# Same but with progress
tar cf - -C /source/dir . \\
  | pv -s $(du -sb /source/dir | cut -f1) \\
  | tar xpf - -C /dest/dir

# Clone with full metadata preservation
tar cf - --acls --xattrs --selinux -C /source/dir . \\
  | tar xpf - --acls --xattrs --selinux -C /dest/dir
```

---

### Quick Reference: Pipeline Order

When combining operations, follow this order:

```
CREATE → COMPRESS → ENCRYPT → SPLIT → CHECKSUM → TRANSFER
tar    → zstd/xz → gpg/age → split → sha256   → ssh/nc
```

And to reverse:

```
REASSEMBLE → VERIFY   → DECRYPT → DECOMPRESS → EXTRACT
cat        → sha256sum → gpg/age → zstd/xz    → tar
```

> **Key principle:** Every tool in the chain reads from stdin and writes to stdout. The pipe (`|`) connects them. Use `-f -` to tell tar to read/write stdin/stdout instead of a file.

---

### Encryption Tool Comparison for Pipelines

| Tool | Type | Pipe-friendly | Key Management | Notes |
|------|------|:---:|---|---|
| `gpg -c` | Symmetric (passphrase) | ✅ | None needed | Universal, prompts for passphrase |
| `gpg -e -r` | Asymmetric (public key) | ✅ | Keyring required | Standard for sharing with others |
| `age -p` | Symmetric (passphrase) | ✅ | None needed | Modern, simple, no config |
| `age -r` | Asymmetric (public key) | ✅ | Single key file | No keyring, just a file |
| `openssl enc` | Symmetric (passphrase) | ✅ | None needed | Always available, more flags |

Install `age`: `brew install age` / `sudo apt install age` / `sudo pacman -S age`
