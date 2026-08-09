---
title: "macOS Terminal Tweaks"
description: "Hidden macOS terminal/defaults tweaks and productivity commands for the CLI."
category: linux-it
tags: [macos, terminal, productivity]
tools: [defaults, zsh]
difficulty: beginner
updated: "2026-08-09"
source: "vault:macOS/macOS Terminal Tweaks Cheat Sheet.md"
---

# macOS Terminal Tweaks

> **How `defaults` works —** `defaults write <domain> <key> <type> <value>` writes a preference. `defaults delete <domain> <key>` removes it (restoring the macOS default). Most changes need the affected app restarted — commands below include `killall` where needed. `killall SystemUIServer` restarts the menu bar; `killall Dock` restarts the Dock.

## Table of Contents

Dock · Finder · Desktop · Screenshots · Animations & UI Speed · Mission Control & Spaces · Keyboard · Trackpad & Mouse · Safari · Mail · TextEdit · Calendar · Spotlight · Power & Sleep (pmset) · Network · Security & Privacy · Activity Monitor · Time Machine · Launchpad · Hot Corners Reference · Miscellaneous System

---

## Dock

### Autohide Behaviour
```bash
# Delay before Dock appears on hover (0 = instant)
defaults write com.apple.dock autohide-delay -float 0; killall Dock

# Animation speed (0 = instant, 1 = default)
defaults write com.apple.dock autohide-time-modifier -float 0.2; killall Dock

# Enable autohide
defaults write com.apple.dock autohide -bool true; killall Dock

# Reset both to macOS defaults
defaults delete com.apple.dock autohide-delay
defaults delete com.apple.dock autohide-time-modifier
killall Dock
```

### Appearance & Size
```bash
# Dock icon size (pixels, default 48)
defaults write com.apple.dock tilesize -int 48; killall Dock

# Enable magnification
defaults write com.apple.dock magnification -bool true; killall Dock

# Magnification size (pixels)
defaults write com.apple.dock largesize -int 72; killall Dock

# Dock position: bottom | left | right
defaults write com.apple.dock orientation -string "bottom"; killall Dock

# Minimise window effect: genie | scale | suck
defaults write com.apple.dock mineffect -string "scale"; killall Dock

# Dim hidden app icons
defaults write com.apple.dock showhidden -bool true; killall Dock

# Show indicator dots for open apps
defaults write com.apple.dock show-process-indicators -bool true; killall Dock

# Show recent apps section
defaults write com.apple.dock show-recents -bool false; killall Dock
```

### Behaviour
```bash
# Only show apps that are open (no pinned apps)
defaults write com.apple.dock static-only -bool true; killall Dock

# Single app mode (hides all other apps when switching)
defaults write com.apple.dock single-app -bool true; killall Dock

# Scroll up on Dock icon to show Exposé for that app
defaults write com.apple.dock scroll-to-open -bool true; killall Dock

# Enable spring-loading for all Dock items
defaults write com.apple.dock enable-spring-load-actions-on-all-items -bool true; killall Dock

# Disable launch animation bounce
defaults write com.apple.dock launchanim -bool false; killall Dock

# Add a blank spacer tile to the Dock
defaults write com.apple.dock persistent-apps -array-add '{"tile-type"="spacer-tile";}'; killall Dock
```

### Launchpad / Springboard Animation Speeds
```bash
defaults write com.apple.dock springboard-show-duration -float 0.1; killall Dock
defaults write com.apple.dock springboard-hide-duration -float 0.1; killall Dock
defaults write com.apple.dock springboard-page-duration -float 0.15; killall Dock
```

---

## Finder

### Show / Hide
```bash
# Show hidden files (dotfiles)
defaults write com.apple.finder AppleShowAllFiles -bool true; killall Finder

# Show all filename extensions
defaults write NSGlobalDomain AppleShowAllExtensions -bool true; killall Finder

# Show path bar at the bottom
defaults write com.apple.finder ShowPathbar -bool true; killall Finder

# Show status bar at the bottom
defaults write com.apple.finder ShowStatusBar -bool true; killall Finder

# Show full POSIX path in title bar
defaults write com.apple.finder _FXShowPosixPathInTitle -bool true; killall Finder

# Allow quitting Finder via Cmd+Q
defaults write com.apple.finder QuitMenuItem -bool true; killall Finder

# Keep folders on top when sorting by name
defaults write com.apple.finder _FXSortFoldersFirst -bool true; killall Finder

# Keep folders on top on the Desktop too
defaults write com.apple.finder _FXSortFoldersFirstOnDesktop -bool true; killall Finder
```

### Default View
```bash
# Set default view style:
# Nlsv = List | icnv = Icon | clmv = Column | Flwv = Gallery
defaults write com.apple.finder FXPreferredViewStyle -string "Nlsv"; killall Finder
```

### Warnings & Behaviour
```bash
# Disable extension change warning
defaults write com.apple.finder FXEnableExtensionChangeWarning -bool false; killall Finder

# Disable Trash empty warning
defaults write com.apple.finder WarnOnEmptyTrash -bool false; killall Finder

# Auto-remove items from Trash after 30 days
defaults write com.apple.finder FXRemoveOldTrashItems -bool true; killall Finder

# Disable iCloud as default save location
defaults write NSGlobalDomain NSDocumentSaveNewDocumentsToCloud -bool false

# Expand save panel by default
defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode -bool true
defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode2 -bool true

# Expand print panel by default
defaults write NSGlobalDomain PMPrintingExpandedStateForPrint -bool true
defaults write NSGlobalDomain PMPrintingExpandedStateForPrint2 -bool true
```

### Search Scope
```bash
# Search current folder by default (SCcf = current folder | SCev = entire volume)
defaults write com.apple.finder FXDefaultSearchScope -string "SCcf"; killall Finder
```

### Animations
```bash
# Disable all Finder animations
defaults write com.apple.finder DisableAllAnimations -bool true; killall Finder
```

---

## Desktop

```bash
# Hide all desktop icons (useful for presentations / clean screenshots)
defaults write com.apple.finder CreateDesktop -bool false; killall Finder

# Show hard drives on Desktop
defaults write com.apple.finder ShowHardDrivesOnDesktop -bool true; killall Finder

# Show external hard drives on Desktop
defaults write com.apple.finder ShowExternalHardDrivesOnDesktop -bool true; killall Finder

# Show mounted network servers on Desktop
defaults write com.apple.finder ShowMountedServersOnDesktop -bool true; killall Finder

# Show removable media (USB, SD) on Desktop
defaults write com.apple.finder ShowRemovableMediaOnDesktop -bool true; killall Finder
```

---

## Screenshots

```bash
# Change save location (change path as needed)
defaults write com.apple.screencapture location ~/Desktop

# Change file format: png | jpg | heic | gif | pdf | tiff
defaults write com.apple.screencapture type -string "png"

# Disable shadow / drop shadow around window screenshots
defaults write com.apple.screencapture disable-shadow -bool true

# Disable floating thumbnail (the preview in corner after screenshot)
defaults write com.apple.screencapture show-thumbnail -bool false

# Don't include date in screenshot filename
defaults write com.apple.screencapture include-date -bool false

# Apply changes (no restart needed after this)
killall SystemUIServer
```

---

## Animations & UI Speed

> **Tip —** Run all blocks below for a completely snappy UI experience.

### System-Wide (NSGlobalDomain)
```bash
# Disable window open/close animations
defaults write NSGlobalDomain NSAutomaticWindowAnimationsEnabled -bool false

# Disable scroll animations
defaults write NSGlobalDomain NSScrollAnimationEnabled -bool false

# Speed up window resize time (default 0.2, lower = faster)
defaults write NSGlobalDomain NSWindowResizeTime -float 0.001

# Disable rubber-band / elastic scrolling
defaults write NSGlobalDomain NSScrollViewRubberbanding -bool false

# Speed up Quick Look panel animation
defaults write NSGlobalDomain QLPanelAnimationDuration -float 0

# Speed up toolbar full screen animation
defaults write NSGlobalDomain NSToolbarFullScreenAnimationDuration -float 0

# Speed up column browser animation
defaults write NSGlobalDomain NSBrowserColumnAnimationSpeedMultiplier -float 0.001

# Disable version browser animation
defaults write NSGlobalDomain NSDocumentRevisionsWindowTransformAnimation -bool false
```

### Dock
```bash
defaults write com.apple.dock expose-animation-duration -float 0.1; killall Dock
defaults write com.apple.dock launchanim -bool false; killall Dock
```

### Finder
```bash
defaults write com.apple.finder DisableAllAnimations -bool true; killall Finder
```

### Mail
```bash
defaults write com.apple.mail DisableReplyAnimations -bool true
defaults write com.apple.mail DisableSendAnimations -bool true
```

---

## Mission Control & Spaces

```bash
# Speed up Mission Control animation
defaults write com.apple.dock expose-animation-duration -float 0.1; killall Dock

# Don't automatically rearrange Spaces based on use
defaults write com.apple.dock mru-spaces -bool false; killall Dock

# Group windows by application in Mission Control
defaults write com.apple.dock expose-group-apps -bool true; killall Dock

# Displays have separate Spaces
defaults write com.apple.spaces spans-displays -bool false; killall Dock

# Switch to a Space with an open window when switching apps
defaults write NSGlobalDomain AppleSpacesSwitchOnActivate -bool true
```

---

## Keyboard

```bash
# Enable key repeat (disable accent popup on hold)
defaults write NSGlobalDomain ApplePressAndHoldEnabled -bool false

# Key repeat rate (lower = faster, minimum ~1)
defaults write NSGlobalDomain KeyRepeat -int 2

# Delay before key repeat starts (lower = faster, minimum ~10)
defaults write NSGlobalDomain InitialKeyRepeat -int 15

# Enable full keyboard navigation (Tab between all controls)
defaults write NSGlobalDomain AppleKeyboardUIMode -int 3

# Disable smart quotes (useful for coding)
defaults write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false

# Disable smart dashes
defaults write NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false

# Disable autocorrect
defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false

# Disable auto-capitalisation
defaults write NSGlobalDomain NSAutomaticCapitalizationEnabled -bool false

# Disable double-space period shortcut
defaults write NSGlobalDomain NSAutomaticPeriodSubstitutionEnabled -bool false
```

---

## Trackpad & Mouse

### Trackpad
```bash
# Enable tap to click
defaults write com.apple.AppleMultitouchTrackpad Clicking -bool true
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true
defaults -currentHost write NSGlobalDomain com.apple.mouse.tapBehavior -int 1

# Enable three-finger drag
defaults write com.apple.AppleMultitouchTrackpad TrackpadThreeFingerDrag -bool true
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad TrackpadThreeFingerDrag -bool true

# Disable natural scrolling
defaults write NSGlobalDomain com.apple.swipe-navigate-with-scrolls -bool false

# Enable swipe-to-navigate in browsers
defaults write NSGlobalDomain AppleEnableSwipeNavigateWithScrolls -bool true
```

### Mouse
```bash
# Disable mouse acceleration (linear movement)
defaults write .GlobalPreferences com.apple.mouse.linear -bool true

# Set mouse tracking speed (0.0–3.0)
defaults write NSGlobalDomain com.apple.mouse.scaling -float 2.5

# Set scroll speed
defaults write NSGlobalDomain com.apple.scrollwheel.scaling -float 0.6875
```

---

## Safari

```bash
# Show full URL in address bar (not just domain)
defaults write com.apple.Safari ShowFullURLInSmartSearchField -bool true

# Disable search suggestions
defaults write com.apple.Safari SuppressSearchSuggestions -bool true
defaults write com.apple.Safari UniversalSearchEnabled -bool false

# Enable Develop menu
defaults write com.apple.Safari IncludeDevelopMenu -bool true
defaults write com.apple.Safari WebKitDeveloperExtrasEnabledPreferenceKey -bool true

# Enable debug menu
defaults write com.apple.Safari IncludeInternalDebugMenu -bool true

# Disable auto-opening of downloaded "safe" files
defaults write com.apple.Safari AutoOpenSafeDownloads -bool false

# Set history limit in days (default 31)
defaults write com.apple.Safari WebKitHistoryAgeInDaysLimit -int 365

# Disable thumbnail cache for History and Top Sites
defaults write com.apple.Safari DebugSnapshotsUpdatePolicy -int 2
```

---

## Mail

```bash
# Disable send animation
defaults write com.apple.mail DisableSendAnimations -bool true

# Disable reply animation
defaults write com.apple.mail DisableReplyAnimations -bool true

# Copy email addresses as 'Name <email>' not just 'email'
defaults write com.apple.mail AddressesIncludeNameOnPasteboard -bool true

# Disable inline attachments (show as icons)
defaults write com.apple.mail DisableInlineAttachmentViewing -bool true

# Disable spell checking
defaults write com.apple.mail SpellCheckingBehavior -string "NoSpellCheckingEnabled"
```

---

## TextEdit

```bash
# Use plain text mode by default
defaults write com.apple.TextEdit RichText -int 0

# Set encoding to UTF-8
defaults write com.apple.TextEdit PlainTextEncoding -int 4
defaults write com.apple.TextEdit PlainTextEncodingForWrite -int 4

# Disable smart quotes in TextEdit
defaults write com.apple.TextEdit SmartQuotes -bool false
```

---

## Calendar

```bash
# Show week numbers
defaults write com.apple.iCal "Show Week Numbers" -bool true

# Set first day of week: 0=Sunday, 1=Monday, 2=Tuesday...
defaults write com.apple.iCal "first day of week" -int 1

# Show 24-hour clock
defaults write com.apple.iCal "number of hours displayed" -int 14
```

---

## Spotlight

```bash
# Disable Spotlight indexing for a volume
sudo mdutil -i off /

# Enable Spotlight indexing for a volume
sudo mdutil -i on /

# Rebuild Spotlight index for a volume
sudo mdutil -E /

# Disable Spotlight indexing for ALL volumes
sudo mdutil -a -i off
```

---

## Power & Sleep (pmset)

> **Warning —** These require `sudo`.

```bash
# Show current power settings
pmset -g

# Set display sleep time in minutes (0 = never)
sudo pmset -a displaysleep 10

# Set system sleep time in minutes (0 = never)
sudo pmset -a sleep 30

# Disable Power Nap (background activity while sleeping)
sudo pmset -a powernap 0

# Enable Wake on Network Access
sudo pmset -a womp 1

# Set standby delay in seconds (default 10800 = 3 hours)
sudo pmset -a standbydelay 86400

# Disable TCP keep-alive during sleep (saves battery)
sudo pmset -a tcpkeepalive 0

# Hibernate mode:
# 0 = sleep only (RAM powered, fast wake)
# 3 = default (sleep + save to disk, safe)
# 25 = hibernate only (slowest, safest for battery)
sudo pmset -a hibernatemode 0
```

### Caffeinate (prevent sleep temporarily)
```bash
# Prevent system from sleeping (Ctrl+C to stop)
caffeinate

# Prevent display from sleeping
caffeinate -d

# Prevent idle sleep
caffeinate -i

# Keep system awake for N seconds (e.g. 1 hour)
caffeinate -t 3600

# Keep system awake until a specific process finishes
caffeinate -w <PID>
```

---

## Network

```bash
# Flush DNS cache
sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder

# List all network interfaces
networksetup -listallnetworkservices

# Turn Wi-Fi off / on
networksetup -setairportpower en0 off
networksetup -setairportpower en0 on

# Show current Wi-Fi SSID
networksetup -getairportnetwork en0

# Set DNS servers
sudo networksetup -setdnsservers Wi-Fi 1.1.1.1 8.8.8.8

# Show public IP address
curl ifconfig.me

# List open network connections
lsof -i

# List listening ports
sudo lsof -i -P | grep LISTEN
```

---

## Security & Privacy

```bash
# Disable Gatekeeper quarantine warning ("App can't be opened")
defaults write com.apple.LaunchServices LSQuarantine -bool false

# Re-enable quarantine warning
defaults write com.apple.LaunchServices LSQuarantine -bool true

# Disable crash reporter dialog (reports still sent)
defaults write com.apple.CrashReporter DialogType -string "none"

# Re-enable crash reporter dialog
defaults write com.apple.CrashReporter DialogType -string "crashreport"

# Set a custom login window message
sudo defaults write /Library/Preferences/com.apple.loginwindow LoginwindowText "Property of [Your Name] — [phone number]"

# Remove login window message
sudo defaults delete /Library/Preferences/com.apple.loginwindow LoginwindowText

# Show/enable firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on

# Check SIP status
csrutil status
```

---

## Activity Monitor

```bash
# Set update frequency: 0=very often(0.5s), 1=often(1s), 2=normal(2s), 3=rarely(5s)
defaults write com.apple.ActivityMonitor UpdatePeriod -int 1

# Set Dock icon to show:
# 0=App Icon, 2=Network Usage, 3=Disk Activity, 4=CPU Usage, 5=CPU History
defaults write com.apple.ActivityMonitor IconType -int 5

# Show all processes (not just user's)
defaults write com.apple.ActivityMonitor ShowCategory -int 0
```

---

## Time Machine

```bash
# Disable Time Machine prompt when connecting new drives
defaults write com.apple.TimeMachine DoNotOfferNewDisksForBackup -bool true

# Disable local Time Machine backups (snapshots)
sudo tmutil disablelocal

# Enable local Time Machine backups
sudo tmutil enablelocal

# List all Time Machine snapshots
tmutil listlocalsnapshots /

# Delete a specific snapshot
tmutil deletelocalsnapshots <YYYY-MM-DD-HHMMSS>
```

---

## Launchpad

```bash
# Reset Launchpad layout to default
defaults write com.apple.dock ResetLaunchPad -bool true; killall Dock

# Speed up Launchpad open animation
defaults write com.apple.dock springboard-show-duration -float 0.1; killall Dock

# Speed up Launchpad close animation
defaults write com.apple.dock springboard-hide-duration -float 0.1; killall Dock

# Speed up Launchpad page-flip animation
defaults write com.apple.dock springboard-page-duration -float 0.15; killall Dock

# Change Launchpad grid layout (columns x rows)
defaults write com.apple.dock springboard-columns -int 8; killall Dock
defaults write com.apple.dock springboard-rows -int 6; killall Dock
```

---

## Hot Corners Reference

> **Command format —** `defaults write com.apple.dock wvous-XX-corner -int [ACTION]` and `defaults write com.apple.dock wvous-XX-modifier -int [MODIFIER]`, then `killall Dock`. Replace `XX` with: `tl` (top-left), `tr` (top-right), `bl` (bottom-left), `br` (bottom-right).

### Action Values

| Value | Action |
| --- | --- |
| `0` | Disabled / No-op |
| `2` | Mission Control |
| `3` | Application Windows |
| `4` | Desktop |
| `5` | Start Screen Saver |
| `6` | Disable Screen Saver |
| `10` | Put Display to Sleep |
| `11` | Launchpad |
| `12` | Notification Centre |
| `13` | Lock Screen |

### Modifier Values

| Value | Modifier Key |
| --- | --- |
| `0` | None |
| `131072` | Shift |
| `262144` | Control |
| `524288` | Option |
| `1048576` | Command |

### Example: Bottom-Right → Lock Screen (no modifier)
```bash
defaults write com.apple.dock wvous-br-corner -int 13
defaults write com.apple.dock wvous-br-modifier -int 0
killall Dock
```

### Example: Top-Left → Mission Control with Shift held
```bash
defaults write com.apple.dock wvous-tl-corner -int 2
defaults write com.apple.dock wvous-tl-modifier -int 131072
killall Dock
```

---

## Miscellaneous System

### System UI & Menu Bar
```bash
# Show battery percentage in menu bar
defaults -currentHost write com.apple.controlcenter BatteryShowPercentage -bool true; killall SystemUIServer

# Show Bluetooth in menu bar
defaults -currentHost write com.apple.controlcenter Bluetooth -int 18; killall SystemUIServer

# Expand save dialog by default
defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode -bool true

# Disable "Application Downloaded from Internet" warning
defaults write com.apple.LaunchServices LSQuarantine -bool false
```

### Terminal
```bash
# Only allow UTF-8 in Terminal.app
defaults write com.apple.terminal StringEncodings -array 4

# Disable the "Are you sure you want to quit Terminal?" prompt
defaults write com.apple.terminal QuitTabText -bool false
```

### App Behaviour
```bash
# Prevent apps from being automatically terminated when idle
defaults write NSGlobalDomain NSDisableAutomaticTermination -bool true

# Resume apps on launch (keep windows from last session)
defaults write NSGlobalDomain NSQuitAlwaysKeepsWindows -bool true

# Auto-quit printer app when print jobs complete
defaults write com.apple.print.PrintingPrefs "Quit When Finished" -bool true
```

### Disk Utility
```bash
# Enable Disk Utility debug menu
defaults write com.apple.DiskUtility DUDebugMenuEnabled -bool true

# Show all partitions in Disk Utility
defaults write com.apple.DiskUtility advanced-image-options -bool true
```

### Quick Look
```bash
# Enable text selection in Quick Look
defaults write com.apple.finder QLEnableTextSelection -bool true; killall Finder
```

### App Store
```bash
# Enable WebKit Developer Tools in App Store
defaults write com.apple.appstore WebKitDeveloperExtras -bool true

# Enable debug menu in App Store
defaults write com.apple.appstore ShowDebugMenu -bool true
```

---

## Quick Resets

```bash
# Restart Dock (apply most Dock changes)
killall Dock

# Restart Finder (apply most Finder changes)
killall Finder

# Restart SystemUIServer (apply menu bar changes)
killall SystemUIServer

# Restart ControlCenter (macOS 11+)
killall ControlCenter

# Read a specific preference to check its current value
defaults read com.apple.dock autohide-delay

# List ALL preferences for an app
defaults read com.apple.finder

# Delete a single preference key (restore default)
defaults delete com.apple.dock autohide-delay; killall Dock
```

---

*Sources: mathiasbynens/dotfiles, macos-defaults.com, robservatory.com, sickcodes gist.*
