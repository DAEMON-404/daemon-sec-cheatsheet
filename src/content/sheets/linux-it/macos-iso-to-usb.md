---
title: "macOS-ISO-to-USB"
description: "shasum -a 256 ~/Downloads/some.iso"
category: linux-it
tags: ["linux-it", "hashing"]
tools: ["Ligolo-ng"]
difficulty: intermediate
updated: "2026-08-10"
source: "vault:macOS-ISO-to-USB-Cheatsheet.md"
---
# 💿 Burning ISOs to USB on macOS (CLI)

> [!info] TL;DR
> - **Linux / BSD / macOS / most ISOs** → `dd` just works.
> - **Windows 10/11 ISOs** → `dd` **does not work**. `install.wim` is usually >4 GB, `diskutil eraseDisk` can't do FAT32, and the Windows boot chain needs a UEFI-visible FAT32 partition. Use the **mount + rsync + wimlib-split** method.
> - **Erasing / wiping** → see the [diskutil erase section](#-diskutil--erasing--secure-erasing-drives). Secure-erase passes are for spinning HDDs; flash/SSDs need encryption-based wipes.
> - Always `diskutil list` **twice** before writing. `of=` to the wrong disk destroys your Mac in seconds.

---

## ⚠️ Before You Start

- **Identify your USB drive**: `diskutil list` — look for size, name, `external, physical`.
- **Never** write to `/dev/disk0` (internal SSD) or the disk containing `/System/Volumes/Data`.
- Use the **raw** device (`/dev/rdiskN`) for `dd` — it's ~10× faster than `/dev/diskN`.
- Apple Silicon caveat: a Windows **x64** USB will **not boot an ARM Mac**. You're making this for a PC or an ARM Windows VM.

---

## 🧪 Step 0 — Verify the ISO (always do this)

```bash
# SHA-256 — compare against the vendor's published hash
shasum -a 256 ~/Downloads/some.iso

# Or if the vendor published SHA-512
shasum -a 512 ~/Downloads/some.iso
```

---

## 🐧 General Method — Linux / BSD / macOS / Kali / Ubuntu / etc.

Works for **any hybrid ISO** (isohybrid / modern Linux / Kali / Ubuntu / FreeBSD / macOS recovery). This is the `dd` path.

```bash
# 1. List disks, find your USB
diskutil list

# 2. Unmount the whole disk (not `eject`, not a partition)
diskutil unmountDisk /dev/disk4

# 3. Write the ISO — note `rdisk`, not `disk`
sudo dd if=~/Downloads/kali-linux-2025.iso of=/dev/rdisk4 bs=4m status=progress

# 4. Eject when done
diskutil eject /dev/disk4
```

> [!tip] Speed & progress
> - `bs=4m` is a sane block size on macOS (lowercase `m`, not `M`).
> - `status=progress` works on recent macOS; if not, hit **Ctrl+T** during `dd` to print SIGINFO progress.

> [!warning] "Resource busy"
> If `dd` refuses with `Resource busy`, you forgot `diskutil unmountDisk`. Do **not** reformat the drive to fix this.

---

## 🪟 Windows 10/11 ISO — The Method That Actually Works

> [!danger] Why `dd` fails for Windows
> Windows ISOs since ~2017 ship `sources/install.wim` larger than 4 GB. A `dd` copy preserves the ISO's internal filesystem (UDF/ISO9660), which most PC firmwares won't boot as a Windows installer. The canonical fix: format USB as **FAT32 + MBR**, copy files, and **split `install.wim`** with `wimlib` so it fits FAT32's 4 GB per-file limit. Windows Setup transparently reassembles split `.swm` files.

### Prereqs

```bash
# Install wimlib (provides wimlib-imagex)
brew install wimlib
```

### Full procedure

```bash
# 1. Find the USB
diskutil list
# Assume it's /dev/disk4 — a 16 GB+ stick

# 2. Format: MS-DOS (FAT32) + MBR, label WIN11
sudo diskutil eraseDisk MS-DOS "WIN11" MBR /dev/disk4

# 3. Mount the Windows ISO
hdiutil mount ~/Downloads/Win11_English_x64.iso
# Note the mount point — usually /Volumes/CCCOMA_X64FRE_EN-US_DV9
# (name varies by build/language)

# 4. Set variables for clarity
ISO_MOUNT="/Volumes/CCCOMA_X64FRE_EN-US_DV9"
USB_MOUNT="/Volumes/WIN11"

# 5. Copy everything EXCEPT install.wim (too big for FAT32)
rsync -avh --progress --exclude='sources/install.wim' "$ISO_MOUNT/" "$USB_MOUNT/"

# 6. Split install.wim into <4 GB chunks directly onto the USB
wimlib-imagex split "$ISO_MOUNT/sources/install.wim" \
    "$USB_MOUNT/sources/install.swm" 3800

# 7. Unmount cleanly (flush buffers — this takes a minute, be patient)
hdiutil unmount "$ISO_MOUNT"
diskutil eject /dev/disk4
```

> [!note] Why `3800` MB?
> FAT32's per-file cap is 4 GiB = 4096 MB. `3800` leaves headroom; Microsoft docs suggest splitting below the limit.

> [!tip] If the target PC won't boot the USB
> - Some modern PCs want **GPT**, not MBR. Re-run step 2 with `GPT` instead of `MBR` and try again.
> - In BIOS/UEFI, disable **CSM/Legacy** and ensure **Secure Boot** is off for installation.
> - For **Windows 7** (legacy), `dd` actually works fine — the `.wim` bloat is a modern Windows problem.

### Windows ARM ISO (for Apple Silicon VMs)

Same procedure, but `install.wim` is often **under** 4 GB — try a straight `rsync` first with no split:

```bash
rsync -avh --progress "$ISO_MOUNT/" "$USB_MOUNT/"
# If it fails on install.wim, fall back to the wimlib-split step above.
```

---

## 🧹 `diskutil` — Erasing & Secure-Erasing Drives

> [!danger] Read this first
> Every `diskutil erase*` verb is **destructive and immediate** — no confirmation prompt, no undo. Always run `diskutil list` twice and target the correct `/dev/diskN`. Hitting `disk0` wipes your Mac's internal SSD.

### Verb cheat sheet

| Verb | What it does | Scope |
|---|---|---|
| `eraseDisk` | Wipe entire disk, lay down new partition scheme + one volume | Whole drive |
| `eraseVolume` | Wipe a single mounted volume, keep the disk's partition scheme | One partition |
| `partitionDisk` | Wipe disk and create multiple partitions in one shot | Whole drive |
| `zeroDisk` | Fill entire disk with zeros (single pass) | Whole drive |
| `randomDisk <passes>` | Fill entire disk with random data, N passes | Whole drive |
| `secureErase <level>` | Multi-pass overwrite wipe of a whole disk | Whole drive |
| `secureErase freespace <level>` | Overwrite only the unused space on a mounted volume | Free space only |

### Formats you'll actually use

| Format string | Real filesystem | Typical use |
|---|---|---|
| `APFS` | APFS | Modern macOS-only volumes |
| `JHFS+` | Mac OS Extended (Journaled) | macOS legacy / Time Machine on HDD |
| `MS-DOS` or `MS-DOS FAT32` | FAT32 | Windows installers, UEFI boot, BIOS flash |
| `ExFAT` | exFAT | Large files + cross-OS (no 4 GB limit) |
| `Free Space` | unformatted | Create a blank slot for later |

### Partition schemes

| String | When to use |
|---|---|
| `MBR` / `MBRFormat` | Windows installer USB (FAT32 + MBR), legacy BIOS |
| `GPT` / `GPTFormat` | Modern UEFI systems, anything >2 TB, most 2020+ PCs |
| `APM` / `APMFormat` | PowerPC-era Macs — don't use unless you need to |

### Common erase patterns

```bash
# Plain reformat a USB as exFAT + GPT (cross-OS daily-driver stick)
sudo diskutil eraseDisk ExFAT "DATA" GPT /dev/disk4

# FAT32 + MBR for a Windows installer USB
sudo diskutil eraseDisk MS-DOS "WIN11" MBR /dev/disk4

# APFS + GPT for a macOS-only stick
sudo diskutil eraseDisk APFS "MACSTICK" GPT /dev/disk4

# Wipe a single mounted volume, keep the scheme intact
sudo diskutil eraseVolume JHFS+ "Scratch" /Volumes/Scratch

# Partition a disk into two volumes in one go (exFAT + APFS, GPT)
sudo diskutil partitionDisk /dev/disk4 2 GPT \
    ExFAT "SHARED" 50% \
    APFS  "MACONLY" 0b
```

### Secure erase — `diskutil secureErase`

> [!warning] Secure erase on SSDs / USB flash is largely theatre
> Apple removed the GUI option because **overwriting doesn't reliably wipe flash**. Wear-levelling, over-provisioning, and TRIM mean the controller may silently keep copies of "erased" blocks. Use it on **spinning HDDs** where it actually works. For SSDs/flash, prefer **FileVault / encryption with a discarded key**, or the drive's own ATA Secure Erase / NVMe Sanitize (usually only accessible from Linux via `hdparm` / `nvme-cli`).

**Syntax:**

```bash
sudo diskutil secureErase <level> /dev/diskN
sudo diskutil secureErase freespace <level> /Volumes/VolumeName
```

**Levels** (yes, the numbering is bizarre):

| Level | Passes | Standard | Notes |
|---|---|---|---|
| `0` | 1 | Single-pass zero | Fast. Fine for HDDs. |
| `1` | 1 | Single-pass random | Slightly better than zeros on HDD |
| `2` | **7** | DoE 3-pass (historic: DoD 5220.22-M 7-pass) | Overkill for modern HDDs |
| `3` | **35** | Gutmann | Almost never justified; hours–days |
| `4` | **3** | US DoD 5220.22-M (3-pass) | The "sensible paranoid" option |

**Examples:**

```bash
# Single zero-pass wipe of a whole USB (HDD-era fast option)
sudo diskutil secureErase 0 /dev/disk4

# DoD 3-pass wipe of a USB stick (for pentest engagement hygiene)
sudo diskutil secureErase 4 /dev/disk4

# Scrub only the free space on a mounted volume — leaves files intact,
# tries to kill recoverable remnants of already-deleted files
sudo diskutil secureErase freespace 1 /Volumes/DATA

# Equivalent "lite" path: single-pass zero-fill of whole disk
sudo diskutil zeroDisk /dev/disk4

# Random-fill, 3 passes
sudo diskutil randomDisk 3 /dev/disk4
```

> [!tip] Ctrl+T for progress
> `secureErase`, `zeroDisk`, and `randomDisk` are quiet. Press **Ctrl+T** in the terminal to send SIGINFO and get a one-line progress update.

### Pentest-engagement hygiene recipe

For reusable installer/tooling USBs between clients (bearing in mind flash-memory caveats above):

```bash
# 1. Identify
diskutil list external physical

# 2. Unmount (just in case)
diskutil unmountDisk /dev/disk4

# 3. Single random-pass (good enough for flash; don't waste cycles on 7/35)
sudo diskutil randomDisk 1 /dev/disk4

# 4. Reformat ready for the next client
sudo diskutil eraseDisk ExFAT "ENGAGEMENT" GPT /dev/disk4
```

For genuinely sensitive data on flash, **encrypt from day one** (APFS encrypted volume or LUKS from Linux) and destroy the passphrase at end-of-life — that's the only reliable "secure erase" for modern flash.

---

## 🔁 Quick Reference Table

| Scenario                      | Tool               | Target filesystem | Partition | Notes                         |
| ----------------------------- | ------------------ | ----------------- | --------- | ----------------------------- |
| Kali / Ubuntu / Linux live    | `dd`               | (raw write)       | n/a       | `bs=4m`, use `rdiskN`         |
| FreeBSD / OpenBSD             | `dd`               | (raw write)       | n/a       | Same as above                 |
| macOS installer (DMG→ISO)     | `createinstallmedia` | HFS+            | GPT       | Apple's own tool, not `dd`    |
| Windows 7                     | `dd`               | (raw write)       | n/a       | Legacy — works                |
| **Windows 10 / 11 (x64)**     | `rsync` + `wimlib` | FAT32             | MBR (GPT fallback) | **Do not use `dd`**  |
| Windows 11 ARM                | `rsync` (+ wimlib if >4GB) | FAT32     | MBR/GPT   | Check `install.wim` size first |

---

## 🧰 Handy One-Liners

```bash
# Identify only external physical disks (less scary than plain `diskutil list`)
diskutil list external physical

# Check install.wim size before deciding split vs direct copy
ls -lh /Volumes/CCCOMA_*/sources/install.wim

# Watch dd progress without status=progress (send SIGINFO)
# During dd, press Ctrl+T

# Unmount every partition of a disk at once
diskutil unmountDisk force /dev/disk4

# Verify what's actually on the stick after burning
diskutil info /dev/disk4
```

---

## 🧯 Troubleshooting

| Symptom | Fix |
|---|---|
| `dd: /dev/rdisk4: Resource busy` | `diskutil unmountDisk /dev/disk4` first |
| `dd: Permission denied` | Prefix with `sudo`; on Sonoma+ grant Terminal **Full Disk Access** in System Settings → Privacy |
| Windows USB not listed in PC boot menu | Likely booted ISO raw with `dd` — redo with the rsync+wimlib method |
| `rsync: failed: Read-only file system` | macOS mounted the FAT32 stick read-only (seen on some Sonoma builds). Re-plug, or erase again with `diskutil eraseDisk MS-DOS "WIN11" MBR /dev/disk4` |
| Windows installer says "can't find drivers" mid-install | Try a **USB 2.0 port** — some Win10 media lacks USB 3.x xHCI drivers |
| `hdiutil: mount failed` | ISO may be corrupt — re-verify the SHA-256 |
| Secure Boot rejects the USB | Disable Secure Boot during install, re-enable after |

---

## 🔐 Security-Adjacent Notes (relevant for pentest lab work)

- **Always verify ISO hashes** — pre-poisoned ISOs (e.g. backdoored Kali mirrors) have happened. Cross-check against multiple sources for release signing keys.
- For a clean **evidence-grade write**, follow `dd` with `sync; sync` and a hash of the source ISO vs `dd if=/dev/rdisk4 bs=4m count=<iso_blocks> | shasum -a 256` (read back and compare).
- Throwaway installer sticks for engagements: consider `shred` / `diskutil secureErase` between clients to avoid cross-contamination of tooling.

---

## 🔗 Related

- ligolo-ng Cheatsheet
- Kali on Parallels M1 Setup
- NetHydra VM Provisioning
