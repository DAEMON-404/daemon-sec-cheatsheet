---
title: "tmux"
description: "tmux sessions, windows, panes, copy mode and config bindings for terminal multiplexing."
category: linux-it
tags: [linux, terminal, productivity]
tools: [tmux]
difficulty: beginner
updated: "2026-08-09"
source: "vault:Misc/tmux.md"
---

# tmux

**Prefix Key: `Ctrl+a`** (changed from the default `Ctrl+b`)

> **Note —** This sheet documents a customized tmux config (remapped prefix, vim-style pane nav, and several TPM plugins). Bindings marked as plugin features assume those plugins are installed.

## Getting Started

| Command | Action |
|:---|:---|
| `tmux new -s name` | Create new session with name |
| `tmux ls` | List all sessions |
| `tmux a -t name` | Attach to existing session |
| `tmux kill-session -t name` | Kill specific session |
| `tmux kill-server` | Kill all tmux sessions |

## Session Management

| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `d` | Detach from current session |
| `Ctrl+a` then `$` | Rename current session |
| `Ctrl+a` then `(` | Switch to previous session |
| `Ctrl+a` then `)` | Switch to next session |
| `Ctrl+a` then `s` | List all sessions (interactive) |
| `Ctrl+a` then `Shift+s` | Save session (resurrect) |
| `Ctrl+a` then `Shift+r` | Restore session (resurrect) |

Sessions auto-save every 15 minutes (tmux-continuum).

## Window Management (Tabs)

| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `c` | Create new window |
| `Ctrl+a` then `,` | Rename current window |
| `Ctrl+a` then `n` | Next window |
| `Ctrl+a` then `p` | Previous window |
| `Ctrl+a` then `0-9` | Jump to window number |
| `Alt+1` .. `Alt+5` | Quick jump to window 1-5 (no prefix needed) |
| `Ctrl+a` then `w` | List all windows (interactive) |
| `Ctrl+a` then `&` | Kill current window |
| `Ctrl+a` then `f` | Find window by name |
| `Ctrl+a` then `l` | Last active window |

## Pane Management (Splits)

### Creating Panes
| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `\|` | Split pane horizontally (side by side) |
| `Ctrl+a` then `-` | Split pane vertically (top/bottom) |

### Navigation
| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `h/j/k/l` | Move to left/bottom/top/right pane |
| `Ctrl+h/j/k/l` | Move between panes (no prefix, vim-aware) |
| `Alt+Left/Down/Up/Right` | Move between panes (no prefix) |

### Resizing Panes
| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `Shift+h` | Resize pane left by 5 cells |
| `Ctrl+a` then `Shift+j` | Resize pane down by 5 cells |
| `Ctrl+a` then `Shift+k` | Resize pane up by 5 cells |
| `Ctrl+a` then `Shift+l` | Resize pane right by 5 cells |

### Pane Layouts
| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `Shift+e` | Even horizontal layout |
| `Ctrl+a` then `Shift+v` | Even vertical layout |
| `Ctrl+a` then `Shift+t` | Tiled layout |
| `Ctrl+a` then `Space` | Cycle through all layouts |

### Other Pane Actions
| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `z` | Toggle pane zoom (fullscreen) |
| `Ctrl+a` then `x` | Kill current pane |
| `Ctrl+a` then `!` | Break pane into new window |
| `Ctrl+a` then `{` | Move pane left |
| `Ctrl+a` then `}` | Move pane right |
| `Ctrl+a` then `Ctrl+o` | Rotate panes clockwise |
| `Ctrl+a` then `Shift+s` | Synchronize panes (type in all at once) |
| `Ctrl+a` then `q` | Show pane numbers |

## Copy Mode (Vim-Style)

### Entering/Exiting
| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `[` | Enter copy mode |
| `q` | Exit copy mode |
| `Esc` | Exit copy mode |

### Navigation in Copy Mode
| Keybind | Action |
|:---|:---|
| `h/j/k/l` | Move left/down/up/right |
| `w` | Move forward by word |
| `b` | Move backward by word |
| `g` | Go to top of buffer |
| `Shift+g` | Go to bottom of buffer |
| `Ctrl+u` | Page up |
| `Ctrl+d` | Page down |

### Selection & Copying
| Keybind | Action |
|:---|:---|
| `v` | Start selection (visual mode) |
| `Shift+v` | Select entire line |
| `y` | Copy selection and exit copy mode |
| `r` | Toggle rectangle selection |
| `Ctrl+a` then `Shift+p` | Paste buffer |
| `Ctrl+a` then `]` | Paste buffer (alternative) |

### Searching in Copy Mode
| Keybind | Action |
|:---|:---|
| `/` | Search forward |
| `?` | Search backward |
| `n` | Next search result |
| `Shift+n` | Previous search result |

## Smart Search (Copycat Plugin)

| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `Ctrl+i` | Search for IP addresses |
| `Ctrl+a` then `Ctrl+u` | Search for URLs |
| `Ctrl+a` then `Ctrl+f` | Search for file paths |
| `Ctrl+a` then `Ctrl+h` | Search for hashes (SHA, MD5) |
| `Ctrl+a` then `Ctrl+d` | Search for digits |
| `n` / `Shift+n` | Next / previous match |
| `Enter` | Copy selection |

## Text Extraction (Extrakto Plugin)

| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `Tab` | Open extrakto (extract all text) |
| `Tab` | Toggle filter mode (in extrakto) |
| `Ctrl+j` or `Down` | Navigate down results |
| `Ctrl+k` or `Up` | Navigate up results |
| `Enter` | Copy selection to clipboard |
| `Ctrl+o` | Open selection in editor |
| `Esc` | Cancel/exit |

## Logging & Recording

| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `Shift+l` | Toggle logging (start/stop recording) |
| `Ctrl+a` then `Ctrl+s` | Screenshot pane (save visible content) |
| `Ctrl+a` then `Ctrl+p` | Save complete history (all scrollback) |

Logs saved to `~/tmux-logs/`. Filename format: `tmux-sessionname-window-pane-20260131_120000.log`

## Quick Copy (Fingers Plugin)

| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `Shift+f` | Show copy hints on screen |
| Type the hint | Copy text at that location |
| `Enter` | Copy main match |
| `Tab` | Toggle hint mode |
| `Esc` | Cancel |

## Fuzzy Finder (tmux-fzf Plugin)

| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `Ctrl+f` | Open fuzzy finder menu |
| `Ctrl+j` or `Down` | Navigate down |
| `Ctrl+k` or `Up` | Navigate up |
| `Enter` | Select item |
| `Esc` | Cancel |

## File Sidebar (Sidebar Plugin)

| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `Tab` | Toggle file tree sidebar |
| `Ctrl+a` then `Backspace` | Toggle sidebar and focus it |
| `Enter` | Open file (when in sidebar) |
| `q` | Close sidebar |

## Open URLs/Files (Open Plugin)

In copy mode:

| Keybind | Action |
|:---|:---|
| `o` | Open highlighted URL or file |
| `Ctrl+o` | Open highlighted text in `$EDITOR` |
| `Shift+s` | Web search highlighted text |

## Pentesting Tools (Custom Bindings)

| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `Shift+y` | Open Python window |
| `Ctrl+a` then `Shift+n` | Open Nmap window |
| `Ctrl+a` then `Shift+m` | Open Metasploit window |
| `Ctrl+a` then `Shift+b` | Open Burp Suite window |
| `Ctrl+a` then `Shift+g` | Open Gobuster window |

## System & Configuration

| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `r` | Reload tmux config |
| `Ctrl+a` then `?` | Show all key bindings |
| `Ctrl+a` then `:` | Enter tmux command mode |
| `Ctrl+a` then `t` | Show clock |
| `Ctrl+a` then `b` | Toggle status bar on/off |
| `Ctrl+a` then `Ctrl+k` | Clear scrollback buffer |
| `Ctrl+a` then `i` | Show tmux info |

## Plugin Management (TPM)

| Keybind | Action |
|:---|:---|
| `Ctrl+a` then `Shift+i` | Install plugins |
| `Ctrl+a` then `Shift+u` | Update plugins |
| `Ctrl+a` then `Alt+u` | Uninstall unused plugins |

## Common Workflows

### Pentesting Setup
```text
1. tmux new -s htb-box
2. Ctrl+a then |        (split right)
3. Ctrl+a then -        (split bottom)
4. Ctrl+a then Shift+n  (open Nmap window)
5. Ctrl+a then Shift+l  (start logging)
```

### Finding IPs in Scan Output
```text
1. Run: nmap -sV 10.10.10.0/24
2. Ctrl+a then Ctrl+i   (search for IPs)
3. n                    (cycle through results)
4. Enter                (copy to clipboard)
```

### Parallel Commands
```text
1. Ctrl+a then |        (split panes 4 ways)
2. Ctrl+a then -
3. Ctrl+a then h
4. Ctrl+a then -
5. Ctrl+a then Shift+s  (synchronize panes)
6. ssh user@host1       (types in ALL panes)
7. Ctrl+a then Shift+s  (unsynchronize)
```

### Extract All IPs/URLs
```text
1. Ctrl+a then Tab      (extrakto)
2. Type to filter
3. Enter to copy
```

### Session Persistence
```bash
# Start work
tmux new -s work

# Work crashes or you disconnect...

# Restore everything
tmux a -s work
# Or if session was killed: Ctrl+a then Shift+r (restore last session)
```

## Mouse Support

Enabled. You can click to select panes, click windows in the status bar, scroll to navigate history, drag to resize panes, and drag to select text (auto-copies).

## Pro Tips

1. Always name your sessions: `tmux new -s project-name`
2. Detach, never close: `Ctrl+a` then `d` (session keeps running)
3. Start logging for reports: `Ctrl+a` then `Shift+l`
4. Find IPs instantly: `Ctrl+a` then `Ctrl+i`
5. Extract anything: `Ctrl+a` then `Tab`
6. Synchronize for parallel work: `Ctrl+a` then `Shift+s`
7. Sessions survive SSH disconnects
8. Zoom pane for focus: `Ctrl+a` then `z`
9. Quick window access: `Alt+1` through `Alt+5`

## Emergency Commands

| Command | Action |
|:---|:---|
| `tmux kill-server` | Kill ALL tmux sessions |
| `Ctrl+a` then `:kill-session` | Kill current session |
| `Ctrl+a` then `Ctrl+k` | Clear screen/history |
| `tmux a` | Attach to last session |
| `Ctrl+a` then `?` | Show all bindings if confused |
