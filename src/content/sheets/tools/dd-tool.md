---
title: "dd tool"
description: "⚠️ Warning: dd can permanently destroy data if used incorrectly. Always double-check your commands, especially the if= (input) and of= (output) parameters."
category: tools
tags: ["tools", "adcs", "forensics"]
tools: []
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Tools/dd tool.md"
---
# Linux `dd` Command: Complete Guide and Cheat Sheet

## Reference Table

| Topic | Description | Reference Type |
|:---|:---|:---|
| GNU Coreutils dd | Official documentation for dd utility | Official Documentation |
| Linux man pages | Complete dd manual page | Manual/Documentation |
| Disk cloning and imaging | Techniques for full disk backup and restoration | Tutorial/Guide |
| Bootable USB creation | Creating bootable media from ISO images | Practical Guide |
| Data recovery and forensics | Using dd for data recovery operations | Advanced Guide |
| Security and data wiping | Secure deletion and data sanitization | Security Guide |
| Performance optimization | Block size tuning and I/O optimization | Performance Guide |
| Network backups | Remote backup using SSH and compression | Network Administration |

---

## Overview

**dd** is a powerful low-level data copying and conversion utility in Linux, nicknamed both "**data duplicator**" and "**data destroyer**" (due to its potential for catastrophic data loss if used incorrectly). It performs bit-by-bit copies of files, devices, and partitions.

⚠️ **Warning**: dd can permanently destroy data if used incorrectly. Always double-check your commands, especially the `if=` (input) and `of=` (output) parameters.

---

## Basic Syntax

```bash
dd if=[input] of=[output] [options]
```

**Note**: dd uses unique `option=value` syntax instead of standard `-option` or `--option` format.

---

## Core Options Reference

| Option | Description | Example |
|:---|:---|:---|
| `if=FILE` | Input file/device (source) | `if=/dev/sda` |
| `of=FILE` | Output file/device (destination) | `of=/dev/sdb` |
| `bs=SIZE` | Block size (read and write) | `bs=4M` |
| `ibs=SIZE` | Input block size | `ibs=512` |
| `obs=SIZE` | Output block size | `obs=4096` |
| `count=N` | Copy only N input blocks | `count=100` |
| `skip=N` | Skip N blocks at input start | `skip=10` |
| `seek=N` | Skip N blocks at output start | `seek=5` |
| `status=LEVEL` | Transfer information display | `status=progress` |
| `conv=CONV` | Conversion options (comma-separated) | `conv=noerror,sync` |
| `iflag=FLAGS` | Input flags (comma-separated) | `iflag=direct,fullblock` |
| `oflag=FLAGS` | Output flags (comma-separated) | `oflag=sync,direct` |

---

## Block Size Guide

| Block Size | Use Case | Performance |
|:---|:---|:---|
| `512` | Default (legacy compatibility) | Slow ⚠️ |
| `4K` (4096) | Standard sector size | Moderate |
| `64K` | Network transfers, older HDDs | Good |
| `1M` | General purpose, HDDs | Very Good ✓ |
| `4M` | SSDs, modern drives | Excellent ✓✓ |

**Recommendations**:
* **SSDs**: Use `bs=4M` for optimal performance
* **HDDs**: Use `bs=1M` or `bs=64K`
* **Network transfers**: Use `bs=64K` for reliability
* **Always use** `conv=fsync` or `oflag=direct` with block sizes ≥ 4096 for proper error detection

---

## Common Conversion Options (conv=)

| Option | Description |
|:---|:---|
| `noerror` | Continue operation on read errors (essential for recovery) |
| `sync` | Pad input blocks with nulls to match block size |
| `fsync` | Physically write output data before finishing |
| `notrunc` | Do not truncate the output file |
| `sparse` | Try to seek rather than write null blocks (saves space) |
| `ucase` | Convert lowercase to uppercase |
| `lcase` | Convert uppercase to lowercase |
| `ascii` | Convert EBCDIC to ASCII |
| `ebcdic` | Convert ASCII to EBCDIC |
| `block` | Pad newline-terminated records with spaces |
| `unblock` | Replace trailing spaces with newline |

**Most Important**: `conv=noerror,sync` for recovering data from failing drives

---

## Input/Output Flags

| iflag/oflag | Description |
|:---|:---|
| `direct` | Use direct I/O (bypass cache) |
| `sync` | Use synchronized I/O |
| `fullblock` | Accumulate full blocks of input (iflag only) |
| `append` | Append mode (oflag only) |
| `nonblock` | Use non-blocking I/O |
| `count_bytes` | Treat count as bytes, not blocks |
| `skip_bytes` | Treat skip as bytes, not blocks (iflag) |
| `seek_bytes` | Treat seek as bytes, not blocks (oflag) |

---

## Status Display Options

| Status Level | Description |
|:---|:---|
| `none` | No output at all |
| `noxfer` | Suppress final transfer statistics |
| `progress` | Show periodic transfer statistics (recommended ✓) |

**Example**: `status=progress` shows real-time progress like:
```
524288000 bytes (524 MB, 500 MiB) copied, 10 s, 52.4 MB/s
```

---

## Common Use Cases with Examples

### 1. Full Disk Cloning

Clone entire disk (including all partitions and boot sectors):

```bash
# Identify source and destination
lsblk

# Unmount all partitions on destination
sudo umount /dev/sdb*

# Clone disk
sudo dd if=/dev/sda of=/dev/sdb bs=4M status=progress conv=fsync

# Flush cache
sync
```

**Verification**:
```bash
# Hash both disks and compare
sudo md5sum /dev/sda
sudo md5sum /dev/sdb
```

---

### 2. Create Bootable USB from ISO

```bash
# Verify ISO integrity first
sha256sum ubuntu-22.04.iso

# Identify USB device (NOT partition!)
lsblk

# Unmount USB
sudo umount /dev/sdb*

# Write ISO to USB (use device /dev/sdb, NOT /dev/sdb1)
sudo dd if=ubuntu-22.04.iso of=/dev/sdb bs=4M status=progress oflag=sync

# Verify USB
sudo file -s /dev/sdb
```

**Important Notes**:
* Write to the device (`/dev/sdb`), NOT to a partition (`/dev/sdb1`)
* No need to format USB beforehand—dd overwrites everything
* To reuse USB after: `sudo fdisk /dev/sdb` then `sudo mkfs.vfat /dev/sdb1`

---

### 3. Create Disk Image (Backup)

```bash
# Backup entire disk to image file
sudo dd if=/dev/sda of=~/backup_disk.img bs=4M status=progress

# Backup single partition
sudo dd if=/dev/sda1 of=~/backup_partition.img bs=4M status=progress

# Compressed backup (saves space)
sudo dd if=/dev/sda bs=4M status=progress | gzip > backup_disk.img.gz

# Backup with progress using pv
sudo dd if=/dev/sda bs=4M | pv | gzip > backup_disk.img.gz
```

---

### 4. Restore from Disk Image

```bash
# Restore from image
sudo dd if=backup_disk.img of=/dev/sda bs=4M status=progress

# Restore from compressed backup
gunzip -dc backup_disk.img.gz | sudo dd of=/dev/sda bs=4M status=progress

# Alternative decompression
zcat backup_disk.img.gz | sudo dd of=/dev/sda bs=4M status=progress
```

---

### 5. MBR (Master Boot Record) Backup/Restore

```bash
# Backup entire MBR (512 bytes: boot code + partition table)
sudo dd if=/dev/sda of=mbr_backup.img bs=512 count=1

# Backup only boot code (446 bytes, excluding partition table)
sudo dd if=/dev/sda of=mbr_boot.img bs=446 count=1

# Restore MBR
sudo dd if=mbr_backup.img of=/dev/sda bs=512 count=1
```

---

### 6. GPT Partition Table Backup/Restore

For GPT disks, use `sgdisk` (not dd):

```bash
# Backup GPT
sudo sgdisk --backup=/path/to/backup.gpt /dev/sda

# Restore GPT
sudo sgdisk --load-backup=backup.gpt /dev/sda
```

---

### 7. Secure Data Wiping

**Method 1: Fill with zeros (fastest)**
```bash
sudo dd if=/dev/zero of=/dev/sda bs=4M status=progress
```

**Method 2: Fill with random data (more secure)**
```bash
sudo dd if=/dev/urandom of=/dev/sda bs=4M status=progress
```

**Method 3: Using shred (multiple passes)**
```bash
sudo shred -vfz -n 3 /dev/sda
```

**Wipe specific partition**:
```bash
sudo dd if=/dev/zero of=/dev/sda1 bs=4M status=progress
```

---

### 8. Create Fixed-Size File

```bash
# Create 100MB file filled with zeros
dd if=/dev/zero of=testfile.dat bs=1M count=100

# Create 1GB file
dd if=/dev/zero of=largefile.dat bs=1M count=1024

# Create sparse file (faster, uses less disk space)
dd if=/dev/zero of=sparse.dat bs=1M count=1024 conv=sparse
```

---

### 9. Data Recovery from Failing Drive

```bash
# Use conv=noerror,sync to skip bad sectors
sudo dd if=/dev/sda of=recovery.img bs=4M conv=noerror,sync status=progress

# Better: Use ddrescue for recovery (not standard dd)
sudo ddrescue /dev/sda recovery.img recovery.log
```

**Why `conv=noerror,sync`?**
* `noerror`: Don't stop on read errors
* `sync`: Pad failed blocks with zeros to maintain alignment

**Note**: For serious data recovery, use `ddrescue` instead—it's specifically designed for this purpose with features like:
* Log file to track progress
* Resume capability
* Multiple retry attempts with varying block sizes

---

### 10. Network Backup via SSH

**Remote backup (local to remote)**:
```bash
# Basic remote backup
sudo dd if=/dev/sda bs=4M | ssh user@remote 'dd of=backup.img'

# With compression (faster transfer)
sudo dd if=/dev/sda bs=4M | gzip | ssh user@remote 'gunzip | dd of=backup.img'

# With progress monitoring
sudo dd if=/dev/sda bs=4M | pv | gzip | ssh user@remote 'gunzip | dd of=backup.img'
```

**Remote restore (remote to local)**:
```bash
ssh user@remote 'dd if=backup.img' | sudo dd of=/dev/sda bs=4M status=progress
```

---

### 11. Copy Partial Data

**Skip first 100 blocks, copy 50 blocks**:
```bash
dd if=input.dat of=output.dat bs=1M skip=100 count=50
```

**Write at specific offset (seek)**:
```bash
dd if=data.bin of=output.dat bs=1M seek=10 conv=notrunc
```

**Byte-level precision**:
```bash
dd if=input.dat of=output.dat bs=1 skip=1024 count=512 iflag=skip_bytes,count_bytes
```

---

### 12. Benchmarking Disk Performance

**Write performance**:
```bash
dd if=/dev/zero of=testfile bs=1M count=1024 oflag=direct
```

**Read performance**:
```bash
dd if=testfile of=/dev/null bs=1M count=1024 iflag=direct
```

**Test different block sizes**:
```bash
for bs in 512 4K 64K 1M 4M; do
  echo "Block size: $bs"
  dd if=/dev/zero of=testfile bs=$bs count=10000 oflag=direct 2>&1 | grep copied
done
```

---

## Progress Monitoring Techniques

### 1. Built-in Progress (Recommended)

```bash
dd if=/dev/sda of=/dev/sdb bs=4M status=progress
```

### 2. Send Signal to Running dd

Find the dd process ID:
```bash
ps aux | grep dd
```

Send USR1 signal to show progress:
```bash
kill -USR1 [dd_pid]
```

Or use `watch`:
```bash
watch -n 5 'kill -USR1 [dd_pid]'
```

### 3. Using pv (Pipe Viewer)

Install pv first: `sudo apt install pv` or `sudo yum install pv`

```bash
# With size known
dd if=/dev/sda bs=4M | pv -s 500G | dd of=/dev/sdb bs=4M

# Without knowing size
dd if=/dev/sda bs=4M | pv | dd of=/dev/sdb bs=4M
```

### 4. Using dcfldd (Enhanced dd)

`dcfldd` is an enhanced version with built-in progress and hashing:

```bash
dcfldd if=/dev/sda of=/dev/sdb bs=4M hash=md5,sha256 hashwindow=1G
```

---

## Verification Methods

### Before and After Checksums

```bash
# Before operation
sudo md5sum /dev/sda > checksum_before.txt
# or
sudo sha256sum /dev/sda > checksum_before.txt

# After operation
sudo md5sum /dev/sdb > checksum_after.txt

# Compare
diff checksum_before.txt checksum_after.txt
```

### Verify ISO Integrity

```bash
# Check ISO before creating bootable USB
sha256sum ubuntu-22.04.iso

# Compare with official checksum from download page
```

### Verify Bootable USB

```bash
sudo file -s /dev/sdb
```

Expected output: Should show filesystem or ISO 9660 information

---

## Safety Checklist ⚠️

Before running dd, **ALWAYS**:

1. ✓ **Identify devices correctly**:
   ```bash
   lsblk
   sudo fdisk -l
   ```

2. ✓ **Unmount target device**:
   ```bash
   sudo umount /dev/sdb*
   ```

3. ✓ **Double-check if= (source) and of= (destination)**
   * `if=` is what you're copying FROM (source)
   * `of=` is what you're copying TO (destination)
   * Reversing these will destroy your data!

4. ✓ **Verify you have correct device names**:
   * `/dev/sda` vs `/dev/sdb` confusion is common
   * `/dev/sdb` (device) vs `/dev/sdb1` (partition)

5. ✓ **Ensure sufficient space on destination**

6. ✓ **Run with sudo/root permissions** (most operations require it)

7. ✓ **Use `status=progress`** to monitor operation

8. ✓ **Run `sync` after dd** to flush cached writes:
   ```bash
   sync
   ```

9. ✓ **Verify with checksums** after critical operations

10. ✓ **Have backups** before overwriting any device

---

## Common Errors and Troubleshooting

| Error | Cause | Solution |
|:---|:---|:---|
| `Permission denied` | Insufficient privileges | Use `sudo` |
| `Device or resource busy` | Device is mounted | `sudo umount /dev/sdX*` |
| `No space left on device` | Destination too small | Use larger destination or compress |
| `Input/output error` | Failing drive or bad sectors | Use `conv=noerror,sync` or `ddrescue` |
| `dd: invalid number` | Wrong syntax for size | Use correct format: `1M`, `4K`, `512` |

### Check for Errors

```bash
# View kernel-level errors
dmesg | grep -i error

# Check SMART data on drives
sudo smartctl -a /dev/sda
```

---

## Performance Optimization Tips

1. **Use appropriate block size**:
   * SSDs: `bs=4M`
   * HDDs: `bs=1M` or `bs=64K`
   * Network: `bs=64K`

2. **Use direct I/O for benchmarking**:
   ```bash
   oflag=direct iflag=direct
   ```

3. **Ensure physical writes with**:
   ```bash
   conv=fsync
   # or
   oflag=sync
   ```

4. **Minimize system load**:
   * Close unnecessary applications
   * Avoid running multiple disk operations simultaneously

5. **Use compression for network transfers**:
   ```bash
   dd if=/dev/sda bs=4M | gzip | ssh user@remote 'gunzip > backup.img'
   ```

6. **Consider hardware factors**:
   * Check cables and ports (intermittent errors)
   * USB 2.0 vs 3.0 speed differences
   * SATA II vs III capabilities

---

## Advanced Features

### Create Sparse Files

```bash
dd if=/dev/zero of=sparse.dat bs=1M count=1024 conv=sparse
```

### Append to Existing File

```bash
dd if=new_data.bin of=existing_file.dat bs=1M oflag=append conv=notrunc
```

### Read Special System Files

```bash
# Read first 1KB of RAM (requires root)
sudo dd if=/dev/mem of=mem_sample.bin bs=1K count=1

# Note: Modern systems may restrict /dev/mem access for security
```

### Network Transfer with Netcat

**Sender (server)**:
```bash
nc -l 9999 | dd of=/dev/sdb bs=4M
```

**Receiver (client)**:
```bash
dd if=/dev/sda bs=4M | nc server_ip 9999
```

---

## Alternative Tools

| Tool | Purpose | When to Use |
|:---|:---|:---|
| `ddrescue` | Data recovery | Failing drives, bad sectors |
| `dcfldd` | Enhanced dd | Need built-in hashing, better progress |
| `partclone` | Partition cloning | Only copy used blocks, faster backups |
| `rsync` | File synchronization | File-level backups, incremental updates |
| `clonezilla` | Disk imaging GUI | User-friendly disk cloning |
| `shred` | Secure deletion | Multi-pass overwriting for security |

---

## Quick Reference Card

### Most Common Commands

```bash
# Full disk clone with progress
sudo dd if=/dev/sda of=/dev/sdb bs=4M status=progress conv=fsync

# Create bootable USB from ISO
sudo dd if=linux.iso of=/dev/sdb bs=4M status=progress oflag=sync

# Backup disk to compressed image
sudo dd if=/dev/sda bs=4M status=progress | gzip > backup.img.gz

# Restore from compressed image
gunzip -dc backup.img.gz | sudo dd of=/dev/sda bs=4M status=progress

# Backup MBR
sudo dd if=/dev/sda of=mbr_backup.img bs=512 count=1

# Secure wipe
sudo dd if=/dev/zero of=/dev/sda bs=4M status=progress

# Check device list
lsblk
sudo fdisk -l
```

---

## Final Notes

* **dd** is an extremely powerful tool—respect its capabilities
* **Always double-check** your commands before pressing Enter
* **Test on non-critical data** first if you're learning
* **Keep backups** of important data before any dd operation
* **Use `status=progress`** to avoid blind operations
* **Verify operations** with checksums when possible
* Consider **alternatives** like `ddrescue` for data recovery scenarios
* **dd** stands for "data duplicator" (or "disk dump"), not "destroy disk"—but it can do both!

---

*This guide covers dd usage as of GNU Coreutils 8.x and later. Older versions may lack some features like `status=progress`. Check your version with: `dd --version`*
