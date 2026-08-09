---
title: "Git Branching"
description: "Branch workflows: create/switch, track remotes, merge vs rebase, and moving edits between branches."
category: git-workflow
tags: [git, branching, workflow]
tools: [git]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:Git/Branches Expanded.md"
---

# Git Branching

This guide covers a multi-vault branching model: one GitHub repo holding several completely different working trees, each on its own orphan branch. Switching branch swaps the entire file tree.

> **Use case —** One GitHub repo, multiple completely different vaults (e.g. Obsidian), each living on its own branch with totally different files. Each branch = its own world. Switching branch = switching vault. Zero overlap.

> **Repository architecture —**
> ```text
> your-repo (on GitHub)
> │
> ├── main ──────────────────► Personal Vault (your notes, templates etc)
> │
> ├── HTB-Labs ──────────────► HTB Vault (writeups, lab notes etc)
> │
> └── Work-Notes ────────────► Work Vault (completely different again)
> ```

> **Warning — Obsidian users, branch-switching:** Always close the current vault in Obsidian **before** running `git checkout`. Obsidian can recreate files or get confused when files suddenly change under it. After switching branch, reopen Obsidian and point it to the same folder.

> **Tip — Golden rules for multi-vault repos:**
> 1. Always run `git branch` before committing — make sure you're on the right vault.
> 2. Use `--orphan` for new vaults — never branch off main or you'll inherit its files.
> 3. Close Obsidian before switching branches to avoid file conflicts.
> 4. Push regularly — GitHub is your backup for every vault.

> **Overview —** Git is a distributed version control system, used here to manage isolated vaults on separate branches within a single repository.
> 1. `--orphan` creates a branch with no history and no inherited files.
> 2. `git rm -rf .` wipes all files after orphan creation for a clean slate.
> 3. `git reset --hard` force-syncs local state to match a remote or previous commit.
> 4. Each branch operates as a fully independent file tree.

## Part 1 — Initial Setup (First Time)

**Step 1 — Set up your Main vault branch first**

```bash
# Initialise the repo if you haven't already
git init
git remote add origin https://github.com/yourusername/your-repo.git

# Add all your main vault files
git add .
git commit -m "Initial main vault setup"
git push -u origin main
```

> **Command breakdown —**
> 1. `git init`: initialises a new local Git repository in the current directory.
> 2. `git remote add origin <url>`: links your local repo to the remote GitHub repository.
> 3. `git add .`: stages all files in the current directory for commit.
> 4. `git commit -m "..."`: commits staged files with a descriptive message.
> 5. `git push -u origin main`: pushes to GitHub and sets `origin/main` as the upstream tracking branch.

**Step 2 — Create a completely empty new branch (e.g. HTB-Labs)**

```bash
# Create orphan branch — NO history, NO files carried over from main
git checkout --orphan HTB-Labs

# Wipe every file that carried over from main
git rm -rf .
```

> **Command breakdown —**
> 1. `git checkout --orphan HTB-Labs`: creates a new branch with zero commit history — files from the current branch are present in the working tree but untracked, so the next step wipes them.
> 2. `git rm -rf .`: recursively force-removes all files from the working tree and staging area, leaving a completely blank slate.
> 3. `main` is entirely untouched by this operation.

> **Result —** You now have a completely blank slate on the `HTB-Labs` branch. The `main` branch and all its files remain untouched.

**Step 3 — Add your second vault files**

```bash
# Create your new vault structure
mkdir HTB-Labs
echo "# HTB Labs Vault" > README.md

# Add and commit
git add .
git commit -m "Initial HTB Labs vault setup"

# Push to GitHub
git push -u origin HTB-Labs
```

> **Command breakdown —**
> 1. `mkdir HTB-Labs`: creates a new directory for the vault structure.
> 2. `echo "# HTB Labs Vault" > README.md`: creates a minimal README as the first file, required for an initial commit.
> 3. `git push -u origin HTB-Labs`: pushes the new orphan branch to GitHub and sets tracking — `-u` only needed on the first push of a new branch.

## Part 2 — Switching Between Vaults

```bash
git checkout main        # Switch to Personal Vault
git checkout HTB-Labs    # Switch to HTB Vault
git checkout Work-Notes  # Switch to Work Vault
```

> **Command breakdown —**
> 1. `git checkout <branch>`: switches the working directory to the specified branch, replacing all files with that branch's contents.
> 2. Because each branch was created with `--orphan`, each has a completely different file tree — switching branches is equivalent to switching between entirely different vaults.

> **Warning — Before every switch:** Run `git status` first to confirm you have no uncommitted changes. Unsaved changes can carry over or cause conflicts when switching branches.

## Part 3 — Saving Changes to Each Vault

> **Important — Verify your branch before committing:** Always confirm you are on the correct branch before staging or committing. Use `git branch` or `git status`.

```bash
# Check which branch/vault you are on
git branch

# Save changes to whichever vault you're currently on
git add .
git commit -m "Update HTB writeup for box XYZ"
git push
```

> **Command breakdown —**
> 1. `git branch`: lists all local branches with an asterisk (`*`) next to the currently active one.
> 2. `git add .`: stages all new, modified, and deleted files in the working directory.
> 3. `git commit -m "..."`: creates a snapshot of staged changes — use descriptive messages for easy history navigation.
> 4. `git push`: pushes committed changes to the tracked remote branch on GitHub.

**Saving to a specific vault (ensuring correct branch)**

```bash
# Switch to the vault you want to update
git checkout HTB-Labs

# Make your changes, then save
git add .
git commit -m "Add new lab notes"
git push
```

> **Note —** Explicitly checking out the target branch before making changes eliminates the risk of committing to the wrong vault. This pattern — switch, change, commit, push — should be the standard workflow for every vault update.

## Part 4 — Adding More Vaults Later

> **Important — Always use orphan branches for new vaults:** Never use `git checkout -b` to create a new vault branch — it inherits all files from the current branch. Always use `--orphan` to start with a completely empty branch.

```bash
# 1. Create a new empty branch
git checkout --orphan Work-Notes

# 2. Wipe everything (removes any leftover files)
git rm -rf .

# 3. Create your new vault files
mkdir Work-Notes-Vault
echo "# Work Notes" > README.md

# 4. Commit and push
git add .
git commit -m "Initial Work Notes vault"
git push -u origin Work-Notes
```

> **Command breakdown —**
> 1. `git checkout --orphan Work-Notes`: creates a new isolated branch with no shared history with any other branch.
> 2. `git rm -rf .`: required after every orphan creation to remove working-tree files that carried over.
> 3. Steps 3 and 4 follow the same pattern as any initial vault setup — create a minimal structure, then commit and push.

## Part 5 — Restoring Deleted Files

> **Tip — Best all-in-one fix, force sync with GitHub:** When in doubt, this restores your branch to exactly match the remote:
> ```bash
> git fetch --all
> git reset --hard origin/HTB-Labs   # Replace with your branch name
> ```

**Scenario 1 — Deleted files, not yet staged**

```bash
git restore .
```

> **Note —** `git restore .` discards all unstaged changes in the working directory, restoring files to their last committed state. Safe to use — only affects uncommitted, unstaged changes.

**Scenario 2 — Deleted and staged, NOT yet committed**

```bash
git restore --staged --worktree .
```

> **Note —** `--staged` removes files from the staging area (index); `--worktree` also restores the actual files in the working directory. Combines unstaging and file restoration in a single command.

**Scenario 3 — Deleted, committed, NOT yet pushed**

```bash
git reset --hard HEAD~1   # Roll back 1 commit
```

> **Note —** `git reset --hard` resets both the commit history and the working directory to the specified point. `HEAD~1` refers to one commit before the current `HEAD` — replace `1` with however many commits you need to roll back. This rewrites local history — safe because the bad commit has not been pushed yet.

**Scenario 4 — Deleted, committed AND pushed**

```bash
git fetch --all
git reset --hard origin/main   # Force match the remote
```

> **Command breakdown —**
> 1. `git fetch --all`: downloads all latest data from every remote branch without merging anything.
> 2. `git reset --hard origin/main`: forces the local branch to exactly match the remote state, discarding any local divergence.
> 3. Replace `main` with whichever branch name you need to restore.

> **Warning — Destructive operation:** `git reset --hard` permanently discards local changes and commits ahead of the reset point. Ensure you do not need any of that local data before running this command.

## Part 6 — Managing Branches

| Action | Command |
|---|---|
| See all branches | `git branch -a` |
| See which branch you're on | `git branch` |
| Rename a branch | `git branch -m old-name new-name` |
| Delete local branch | `git branch -d branch-name` |
| Force delete local branch | `git branch -D branch-name` |
| Delete branch from GitHub | `git push origin --delete branch-name` |
| See last commit on each branch | `git branch -v` |

> **Warning — Deleting branches:**
> 1. `git branch -d` refuses to delete a branch with unmerged changes — a safety net.
> 2. `git branch -D` force-deletes regardless — use only when certain the data is not needed.
> 3. Deleting a remote branch with `git push origin --delete` is permanent — GitHub has no recycle bin.

## Part 7 — Branch Naming Conventions

> **Tip — Naming rules:** Keep names clean, lowercase, no spaces — use hyphens `-` as separators.

| Vault / Purpose | Good Branch Name |
|---|---|
| Personal Obsidian vault | `main` or `personal-vault` |
| HTB / CTF notes | `HTB-Labs` |
| Work notes | `work-notes` |
| Study notes | `study-vault` |
| New feature / test | `feature/new-template` |
| Bug / fix | `bugfix/broken-link` |
| Archive / old version | `archive/2024-vault` |

## Part 8 — Quick Reference Card

```bash
# ── CREATING ──────────────────────────────────────────
git checkout --orphan branch-name   # New empty branch (no history)
git rm -rf .                        # Wipe files after orphan create
git checkout -b branch-name         # New branch copied from current

# ── SWITCHING ─────────────────────────────────────────
git checkout branch-name            # Switch to vault/branch
git checkout -                      # Jump back to previous branch

# ── SAVING ────────────────────────────────────────────
git add .                           # Stage all changes
git commit -m "your message"        # Commit changes
git push                            # Push to GitHub
git push -u origin branch-name      # First push of a new branch

# ── SYNCING ───────────────────────────────────────────
git pull                            # Pull latest from GitHub
git fetch --all                     # Fetch all remote branches

# ── RESTORING ─────────────────────────────────────────
git restore .                       # Undo unstaged deletions
git reset --hard origin/branch-name # Force match GitHub
git reset --hard HEAD~1             # Roll back 1 commit

# ── CLEANUP ───────────────────────────────────────────
git branch -d branch-name            # Delete local branch
git push origin --delete branch-name # Delete remote branch
```

## References

- [Git Official Documentation](https://git-scm.com/doc)
- [git-checkout Reference](https://git-scm.com/docs/git-checkout)
- [git-branch Reference](https://git-scm.com/docs/git-branch)
- [git-reset Reference](https://git-scm.com/docs/git-reset)
- [git-restore Reference](https://git-scm.com/docs/git-restore)
