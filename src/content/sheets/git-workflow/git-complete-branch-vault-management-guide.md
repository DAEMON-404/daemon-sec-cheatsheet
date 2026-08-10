---
title: "Git — Complete Branch & Vault Management Guide"
description: "git init git remote add origin https://github.com/yourusername/your-repo.git"
category: git-workflow
tags: ["git-workflow", "adcs"]
tools: []
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Git — Complete Branch & Vault Management Guide.md"
---
# Initialise the repo if you haven't already
git init
git remote add origin https://github.com/yourusername/your-repo.git

# Add all your main vault files
git add .
git commit -m "Initial main vault setup"
git push -u origin main
```

> [!info]+ Command Breakdown
> 1. **`git init`**: Initialises a new local [Git](https://git-scm.com/docs/git-init) repository in the current directory
> 2. **`git remote add origin <url>`**: Links your local repo to the remote GitHub repository
> 3. **`git add .`**: Stages all files in the current directory for commit
> 4. **`git commit -m "..."`**: Commits staged files with a descriptive message
> 5. **`git push -u origin main`**: Pushes to GitHub and sets `origin/main` as the upstream tracking branch — `-u` only needed on the first push

---

**Step 2 — Create a completely empty new vault branch**

```bash
# Create orphan branch — NO history, NO files carried over from main
git checkout --orphan HTB-Labs

# Wipe every file that carried over
git rm -rf .
```

> [!info]+ Command Breakdown
> 1. **`git checkout --orphan HTB-Labs`**: Creates a new branch with zero commit history — files from the current branch are present in the working tree but untracked, so the next step wipes them
> 2. **`git rm -rf .`**: Recursively force-removes all files from the working tree and staging area, leaving a completely blank slate
> 3. *`main` is entirely untouched by this operation*

> [!success]+ Expected Result
> Completely blank slate on `HTB-Labs`. The `main` branch and all its files remain untouched.

---

**Step 3 — Add vault files and push**

```bash
# Create your new vault structure
mkdir HTB-Labs
echo "# HTB Labs Vault" > README.md

# Add, commit, and push
git add .
git commit -m "Initial HTB Labs vault setup"
git push -u origin HTB-Labs
```

> [!info]+ Command Breakdown
> 1. **`mkdir HTB-Labs`**: Creates a new directory for the vault structure
> 2. **`echo "# HTB Labs Vault" > README.md`**: Creates a minimal README — required for an initial commit on an empty branch
> 3. **`git push -u origin HTB-Labs`**: Pushes the orphan branch to GitHub and sets upstream tracking

> [!important]+ Adding More Vaults Later
> Repeat Steps 2 and 3 for every new vault — always start from `--orphan`. Never use `git checkout -b` to create a new vault branch or you will inherit files from the current branch.

---

## Section 3 — Workflow B — Move Existing Edits to a New Branch

> [!faq]+ Which Scenario Are You In?
> Before running anything, check your current state:
> ```bash
> git status
> ```
> 1. Shows **modified files** → edits are **uncommitted** — follow Scenario A below
> 2. Shows **nothing to commit** → edits are already **committed** on main — follow Scenario B below

---

**Scenario A — Edits are uncommitted (not yet committed)**

*Your changes exist only as working-directory edits*

```bash
# 1. Create a new branch and switch to it — uncommitted edits travel with you automatically
git checkout -b my-new-branch

# 2. Commit your edits on the new branch
git add .
git commit -m "Site edits — moved to own branch"

# 3. Push the new branch to GitHub
git push -u origin my-new-branch
```

> [!info]+ Command Breakdown
> 1. **`git checkout -b my-new-branch`**: Creates the new branch and switches to it — all uncommitted file changes come with you because they live in the working directory, not on any branch
> 2. **`git add .`**: Stages every modified file
> 3. **`git commit -m "..."`**: Locks your edits into the new branch's history
> 4. **`git push -u origin my-new-branch`**: Creates the branch on GitHub and sets upstream — Railway or any other service can now be pointed at this branch

> [!success]+ Expected Result
> 1. `my-new-branch` exists on GitHub with all edits committed
> 2. `main` is unchanged — still matches the original repo
> 3. No merging has occurred — the two branches are fully independent

---

**Scenario B — Edits are already committed on main**

*You already ran `git commit` — the changes are in `main`'s history*

```bash
# 1. Create a new branch at the current point in history
#    This copies main's current state (including your commits) into the new branch
git checkout -b my-new-branch

# 2. Push the new branch to GitHub — DO THIS BEFORE TOUCHING MAIN
git push -u origin my-new-branch

# 3. Switch back to main
git checkout main

# 4. Reset main back to match the original remote
git reset --hard origin/main
```

> [!info]+ Command Breakdown
> 1. **`git checkout -b my-new-branch`**: Creates a new branch starting from exactly where `main` currently is — all committed edits are included
> 2. **`git push -u origin my-new-branch`**: Pushes the new branch to GitHub **before** touching `main` — your work is safely backed up remotely
> 3. **`git checkout main`**: Switches back to main to clean it up
> 4. **`git reset --hard origin/main`**: Forces local `main` to exactly match the GitHub remote — effectively removes your local commits from it

> [!warning]+ Push the New Branch BEFORE Resetting Main
> Push `my-new-branch` to GitHub first. Once you reset `main`, those commits are gone from `main` locally. They are safe on `my-new-branch` — but only if you pushed it first.

> [!success]+ Expected Result
> 1. `my-new-branch` on GitHub contains all your edits
> 2. `main` is clean — matches the original forked repo
> 3. No merging has occurred

---

## Section 4 — Switching Between Vaults / Branches

```bash
git checkout main        # Switch to Personal Vault
git checkout HTB-Labs    # Switch to HTB Vault
git checkout Work-Notes  # Switch to Work Vault
git checkout -           # Jump back to the previous branch instantly
```

> [!info]+ Command Breakdown
> 1. **`git checkout <branch>`**: Switches the working directory to the specified branch — because each vault branch was created with `--orphan`, switching branches is equivalent to switching between entirely different vaults
> 2. **`git checkout -`**: Shorthand for the previously checked-out branch; equivalent to `cd -` in shell

> [!warning]+ Obsidian Users — Branch Switching Warning
> Always close the current vault in Obsidian **before** running `git checkout`. Obsidian can recreate files or get confused when files suddenly change under it. After switching, reopen Obsidian and point it to the same folder.

> [!warning]+ Uncommitted Changes Block Switching
> 1. If local changes conflict with the target branch, switching will abort
> 2. Resolve by committing: `git add . && git commit -m "WIP"`
> 3. Or stash: `git stash` — then restore after switching: `git stash pop`

---

## Section 5 — Saving Changes (Daily Workflow)

> [!important]+ Always Verify Your Branch Before Committing
> Running a commit on the wrong branch is the most common mistake in a multi-vault setup. Always check first.

```bash
# Check which branch/vault you are on
git branch

# Save changes to whichever vault you're currently on
git add .
git commit -m "Update HTB writeup for box XYZ"
git push
```

> [!info]+ Command Breakdown
> 1. **`git branch`**: Lists all local branches — asterisk (`*`) marks the currently active one
> 2. **`git add .`**: Stages all new, modified, and deleted files in the working directory
> 3. **`git commit -m "..."`**: Creates a snapshot of staged changes — use descriptive messages for easy history navigation
> 4. **`git push`**: Pushes committed changes to the tracked remote branch on GitHub

**Standard vault update pattern — switch, change, commit, push**

```bash
git checkout HTB-Labs
git add .
git commit -m "Add new lab notes"
git push
```

> [!tip]+ Golden Rules for Multi-Vault Repos
> 1. Always run `git branch` before committing — confirm you are on the right vault
> 2. Use `--orphan` for new vaults — never branch off main or you will inherit its files
> 3. Close Obsidian before switching branches to avoid file conflicts
> 4. Push regularly — GitHub is your backup for every vault

---

## Section 6 — Pointing Railway at a Branch

> [!tip]+ Railway Deployment Branch
> 1. Go to your project in [Railway](https://railway.app/)
> 2. Navigate to **Settings → Source**
> 3. Change the deployment branch from `main` to your edits branch
> 4. Railway will now build and deploy from that branch
> 5. `main` remains your clean baseline / fallback

---

## Section 7 — Inspecting History with git log

> [!info]+ [git log](https://git-scm.com/book/en/v2/Git-Basics-Viewing-the-Commit-History) Overview
> Inspects commit history and surfaces commit references — hashes, HEAD pointers, tags, branches
> 1. Displays commits in reverse chronological order by default
> 2. Opens in a pager — press `q` to exit, arrow keys to scroll
> 3. Supports filtering by author, file, date, and branch
> 4. Read-only — makes no changes to the repo or working tree

**Commit Reference Types**

| Reference | Example | Meaning |
|---|---|---|
| Full SHA-1 | `346ca091076783c70623aba03fb7139d3d27134f` | Exact commit identifier |
| Short SHA | `346ca09` | First 7 chars — minimum Git requires |
| Tag | `v1.0` | Human-readable bookmark |
| Branch name | `main`, `HTB-Labs` | Latest commit on that branch |
| HEAD | `HEAD` | Currently checked-out commit |
| Relative | `HEAD~2`, `HEAD^` | Commits before HEAD |

**`git log` — Flags**

| Flag | Effect |
|---|---|
| `--oneline` | Shortened hash + message, one line per commit |
| `--graph` | ASCII branch/merge graph alongside log |
| `--all` | Show commits from all branches |
| `--decorate` | Show branch/tag names next to commits |
| `-n <number>` | Limit to `n` most recent commits |
| `--author="Name"` | Filter by author |
| `-- <file>` | Show only commits touching a specific file |

```bash
# Best daily driver — compact, decorated, graphed, all branches
git log --oneline --graph --decorate --all

# Last 5 commits, compact
git log --oneline -5

# Commits touching a specific file
git log --oneline -- hello.html
```

> [!info]+ Command Breakdown
> 1. **`--oneline --graph --decorate --all`**: Combines short hash, ASCII branch topology, branch/tag names, and all branches into the clearest possible history view
> 2. **`-5`**: Limits output to the 5 most recent commits — replace with any integer
> 3. **`-- hello.html`**: The `--` separator tells Git what follows is a file path, not a branch name — filters log to only commits that modified that file

---

## Section 8 — Tagging Versions

> [!info]+ [git tag](https://git-scm.com/book/en/v2/Git-Basics-Tagging) Overview
> Creates permanent, human-readable bookmarks on specific commits (e.g. release versions)
> 1. Two types: **lightweight** (pointer only) and **annotated** (full metadata object)
> 2. Tags are local until explicitly pushed to a remote
> 3. Annotated tags are required for `git describe` to work correctly
> 4. Tags can be applied retroactively to any past commit using its hash

**Tag Types**

| Type | Command | Use Case |
|---|---|---|
| Lightweight | `git tag v1.0` | Quick private/temporary label; no metadata |
| Annotated | `git tag -a v1.0 -m "Release"` | Public releases; includes author, date, message |

**`git tag` — Flags**

| Flag | Effect |
|---|---|
| `-a` | Create an annotated tag (stores author, date, message) |
| `-m "<msg>"` | Attach a message inline (skips editor prompt) |
| `<tagname> <hash>` | Tag a past commit by hash |
| `-d <tagname>` | Delete a tag locally |
| `-l "v1.*"` | List tags matching a pattern |

```bash
# Annotated tag on current HEAD
git tag -a v1.0 -m "First public release"

# Tag a specific past commit
git tag -a v0.9 558151a -m "Pre-release"

# List all tags
git tag

# Delete a local tag
git tag -d v1.0
```

> [!info]+ Command Breakdown
> 1. **`-a v1.0 -m "..."`**: Creates a full annotated tag object — `-m` attaches the message inline, bypassing the editor
> 2. **`558151a`**: Short SHA of a past commit — retrieve via `git log --oneline`
> 3. **`git tag`**: With no args, outputs a plain alphabetical list of all tags
> 4. **`-d v1.0`**: Removes the tag locally — does **not** affect the remote

> [!warning]+ Tags Are Local Until Pushed
> 1. Tags do not sync automatically with `git push`
> 2. Push a single tag: `git push origin v1.0`
> 3. Push all tags at once: `git push --tags`
> 4. Remove a remote tag: `git push origin -d v1.0`

---

## Section 9 — Branch Management

**`git branch` — Flags**

| Flag | Effect |
|---|---|
| *(no args)* | List local branches; `*` marks current |
| `-a` | List all local and remote-tracking branches |
| `-r` | List remote-tracking branches only |
| `-v` | Verbose: show last commit hash + message per branch |
| `-d <name>` | Delete branch (safe; refuses if unmerged) |
| `-D <name>` | Force-delete regardless of merge status |
| `-m <old> <new>` | Rename a branch |
| `--merged` | List branches already merged into current |
| `--no-merged` | List branches not yet merged |

```bash
# See all local branches (* = current)
git branch

# See all branches including remotes
git branch -a

# See last commit per branch
git branch -v

# Delete a merged branch (safe)
git branch -d style

# Force-delete an unmerged branch
git branch -D experiment

# List branches already merged into main (safe to delete)
git branch --merged main
```

> [!warning]+ Deleting Branches
> 1. `git branch -d` refuses to delete a branch with unmerged changes — this is a safety net
> 2. `git branch -D` force-deletes regardless — use only when you are certain the data is not needed
> 3. Deleting a remote branch with `git push origin --delete` is permanent — GitHub has no recycle bin

---

## Section 10 — Creating and Switching Branches (git switch)

> [!info]+ [git switch](https://git-scm.com/docs/git-switch) Overview
> Creates and/or switches between branches — introduced in Git 2.23 as a focused replacement for `git checkout`
> 1. `-c` flag creates a new branch and switches in a single step
> 2. Switching with uncommitted changes will fail unless Git can carry them safely
> 3. Each branch maintains its own working tree state — files from other branches are hidden, not deleted
> 4. Legacy equivalent: `git checkout -b <name>`

**`git switch` — Flags**

| Flag | Effect |
|---|---|
| *(branch name)* | Switch to existing local branch |
| `-c <name>` | Create new branch and switch to it (from current HEAD) |
| `-c <name> <start-point>` | Create from a specific branch or commit |
| `-C <name>` | Force-create: resets branch if it already exists |
| `--detach` | Switch to a commit directly (detached HEAD state) |
| `-` | Switch back to the previously checked-out branch |

```bash
# Confirm which branch you're on before creating
git branch

# Create new branch from current HEAD and switch to it
git switch -c style

# Switch to an existing branch
git switch main

# Create branch from a specific past commit
git switch -c hotfix abc1234

# Jump back to the previous branch
git switch -
```

> [!faq]+ git switch vs git checkout
> 1. `git switch` (Git 2.23+) handles **branch operations only** — cleaner, less ambiguous
> 2. `git checkout` handles branches **and** file restoration — can be confusing
> 3. Legacy equivalent: `git checkout -b <name>` = `git switch -c <name>`
> 4. *Both commands still work — `git switch` is preferred in modern workflows*

---

## Section 11 — Merging Branches

> [!info]+ [git merge](https://git-scm.com/docs/git-merge) Overview
> Integrates commits from one branch into the current branch, preserving full commit history
> 1. Always switch to the **target** (receiving) branch before merging
> 2. Fast-forward merges create no new commit; merge commits have two parents
> 3. Conflicts require manual resolution of `<<<<<<<` / `=======` / `>>>>>>>` markers
> 4. Git 2.34+ uses the `ort` strategy by default instead of `recursive`

**`git merge` — Flags**

| Flag | Effect |
|---|---|
| *(branch name)* | Merge named branch into current branch |
| `--no-ff` | Always create a merge commit (preserves branch history) |
| `--ff-only` | Abort if fast-forward is not possible |
| `--squash` | Combine all source commits into one unstaged change |
| `--abort` | Cancel an in-progress conflicted merge |
| `--continue` | Resume merge after resolving conflicts |
| `-m "<msg>"` | Override the auto-generated merge commit message |

```bash
# Standard merge — bring style into main
git switch main
git merge style

# Force a merge commit even if fast-forward is possible
git merge --no-ff style -m "Merge style feature"

# Fast-forward only — abort if not possible
git merge --ff-only style

# Squash all commits from style into one clean commit
git merge --squash style
git commit -m "Add styling feature"

# Abort a merge gone wrong
git merge --abort

# After resolving conflicts manually
git add <resolved-file>
git merge --continue
```

> [!info]+ Merge Output Interpretation
> 1. `Fast-forward` — branch pointer advanced; no new commit created
> 2. `Merge made by the 'ort' strategy` — merge commit created; histories had diverged
> 3. `CONFLICT (content): Merge conflict in <file>` — manual resolution required
> 4. `Already up to date.` — source branch has no commits not already in target; nothing to do

> [!warning]+ Merge Safety Considerations
> 1. Merge commits are visible in `git log` — use `--squash` or `--ff` to reduce noise in history
> 2. Merging directly into `main` without a pull request is not recommended in team workflows
> 3. Accidental merge recovery: `git reset --hard HEAD~1` — **use with extreme caution**

---

## Section 12 — Restoring Deleted or Lost Files

> [!tip]+ Best All-in-One Fix — Force Sync with GitHub
> When in doubt, this restores your branch to exactly match the remote:
> ```bash
> git fetch --all
> git reset --hard origin/HTB-Labs   # Replace with your branch name
> ```

**Recovery Decision Table**

| Situation | Command | Risk |
|---|---|---|
| Deleted, not yet staged | `git restore .` | None — safe |
| Deleted and staged, not committed | `git restore --staged --worktree .` | None — safe |
| Committed locally, not pushed | `git reset --hard HEAD~1` | Low — local only |
| Committed and pushed | `git fetch --all` then `git reset --hard origin/<branch>` | Medium — confirm first |

```bash
# Scenario 1 — Deleted files, not yet staged
git restore .

# Scenario 2 — Deleted and staged, NOT yet committed
git restore --staged --worktree .

# Scenario 3 — Deleted, committed, NOT yet pushed
git reset --hard HEAD~1   # Roll back 1 commit; replace 1 with number of commits to undo

# Scenario 4 — Deleted, committed AND pushed
git fetch --all
git reset --hard origin/main   # Replace main with your branch name
```

> [!info]+ Command Breakdown
> 1. **`git restore .`**: Discards all unstaged changes — safe, only affects uncommitted/unstaged changes
> 2. **`git restore --staged --worktree .`**: Combines unstaging and file restoration in a single command
> 3. **`git reset --hard HEAD~1`**: Resets both commit history and working directory to one commit before HEAD — safe because the bad commit has not been pushed
> 4. **`git fetch --all`**: Downloads all latest data from every remote branch without merging
> 5. **`git reset --hard origin/main`**: Forces local branch to exactly match the remote state

> [!warning]+ Destructive Operation
> `git reset --hard` permanently discards local changes and commits ahead of the reset point. Ensure you do not need that data before running this command.

---

## Section 13 — Branch Naming Conventions

> [!tip]+ Naming Rules
> Keep names clean, lowercase, no spaces — use hyphens `-` as separators

| Vault / Purpose | Good Branch Name |
|---|---|
| Personal Obsidian vault | `main` or `personal-vault` |
| HTB / CTF notes | `HTB-Labs` |
| Work notes | `work-notes` |
| Study notes | `study-vault` |
| Railway site edits | `site-edits` |
| New feature / test | `feature/new-template` |
| Bug / fix | `bugfix/broken-link` |
| Archive / old version | `archive/2024-vault` |

---

## Section 14 — Master Quick Reference Card

```bash
# ── DIAGNOSE ──────────────────────────────────────────
git status                           # See uncommitted changes + current branch
git branch                           # List local branches (* = active)
git branch -a                        # List all branches including remotes
git branch -v                        # See last commit per branch
git log --oneline --graph --decorate --all  # Full history visualisation
git log --oneline -5                 # Last 5 commits compact

# ── CREATING ──────────────────────────────────────────
git checkout --orphan branch-name    # New empty branch (no history, no files)
git rm -rf .                         # Wipe files after orphan create (required)
git checkout -b branch-name          # New branch inheriting current working state
git switch -c branch-name            # Modern equivalent of checkout -b

# ── SWITCHING ─────────────────────────────────────────
git checkout branch-name             # Switch to vault/branch
git switch branch-name               # Modern equivalent
git checkout -                       # Jump back to previous branch
git switch -                         # Modern equivalent

# ── SAVING ────────────────────────────────────────────
git add .                            # Stage all changes
git commit -m "your message"         # Commit changes
git push                             # Push to GitHub
git push -u origin branch-name      # First push of a new branch

# ── SYNCING ───────────────────────────────────────────
git pull                             # Pull latest from GitHub
git fetch --all                      # Fetch all remote branches (no merge)

# ── RESTORING ─────────────────────────────────────────
git restore .                        # Undo unstaged deletions (safe)
git restore --staged --worktree .    # Undo staged deletions (safe)
git reset --hard HEAD~1              # Roll back 1 commit (local only)
git reset --hard origin/branch-name  # Force match GitHub (destructive)

# ── TAGGING ───────────────────────────────────────────
git tag -a v1.0 -m "Release"        # Create annotated tag
git tag                              # List all tags
git push origin v1.0                 # Push single tag to GitHub
git push --tags                      # Push all tags to GitHub
git tag -d v1.0                      # Delete local tag
git push origin -d v1.0             # Delete remote tag

# ── MERGING ───────────────────────────────────────────
git switch main                      # Switch to target branch first
git merge branch-name                # Merge branch into current
git merge --no-ff branch-name        # Force merge commit
git merge --squash branch-name       # Squash into one commit
git merge --abort                    # Cancel conflicted merge

# ── CLEANUP ───────────────────────────────────────────
git branch -d branch-name            # Delete local branch (safe)
git branch -D branch-name            # Force delete local branch
git push origin --delete branch-name # Delete remote branch (permanent)
git branch -m old-name new-name      # Rename a branch
```

---

## References

| Category | Resource | URL |
|---|---|---|
| Core Docs | Git Official Documentation | [git-scm.com/doc](https://git-scm.com/doc) |
| Core Docs | git-checkout | [git-scm.com/docs/git-checkout](https://git-scm.com/docs/git-checkout) |
| Core Docs | git-branch | [git-scm.com/docs/git-branch](https://git-scm.com/docs/git-branch) |
| Core Docs | git-reset | [git-scm.com/docs/git-reset](https://git-scm.com/docs/git-reset) |
| Core Docs | git-restore | [git-scm.com/docs/git-restore](https://git-scm.com/docs/git-restore) |
| Core Docs | git-switch | [git-scm.com/docs/git-switch](https://git-scm.com/docs/git-switch) |
| Core Docs | git-merge | [git-scm.com/docs/git-merge](https://git-scm.com/docs/git-merge) |
| Core Docs | git-log | [git-scm.com/book — Viewing History](https://git-scm.com/book/en/v2/Git-Basics-Viewing-the-Commit-History) |
| Core Docs | git-tag | [git-scm.com/book — Tagging](https://git-scm.com/book/en/v2/Git-Basics-Tagging) |
| Core Docs | Basic Branching and Merging | [git-scm.com/book — Branching](https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging) |
| Tutorials | git log Tutorial | [atlassian.com/git/tutorials/git-log](https://www.atlassian.com/git/tutorials/git-log) |
| Tutorials | git tag Tutorial | [atlassian.com/git/tutorials — tag](https://www.atlassian.com/git/tutorials/inspecting-a-repository/git-tag) |
| Tutorials | git switch — Git Tower | [git-tower.com/learn/git/commands/git-switch](https://www.git-tower.com/learn/git/commands/git-switch) |
| GitHub | Managing Branches | [docs.github.com — Managing Branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository) |
| GitHub | About Branches | [docs.github.com — About Branches](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-branches) |
| Deployment | Railway Docs — Deployments | [docs.railway.app/deploy/deployments](https://docs.railway.app/deploy/deployments) |
| App | Obsidian Official Site | [obsidian.md](https://obsidian.md/) |
| Cheatsheets | Atlassian Git Cheat Sheet | [Atlassian PDF](https://wac-cdn.atlassian.com/dam/jcr:e7e22f25-bba2-4ef1-a197-53f46b6df4a5/SWTM-2088_Atlassian-Git-Cheatsheet.pdf) |
| Cheatsheets | GitLab Git Cheat Sheet | [GitLab PDF](https://about.gitlab.com/images/press/git-cheat-sheet.pdf) |

---

#Git #GitHub #Obsidian #Railway #VersionControl #Workflow #BranchManagement #OrphanBranch #Branching #Merging #Tagging #GitLog #GitSwitch #GitMerge
