---
title: "Git Reset & Undo"
description: "Undo work safely: reset soft/mixed/hard, restore, revert, reflog recovery and stash rescue."
category: git-workflow
tags: [git, undo, recovery]
tools: [git]
difficulty: intermediate
updated: "2026-08-09"
source: "vault:Git/Resetting.md"
---

# Git Reset & Undo

Working-tree inspection, diffing, restoring, and amending — knowing which of Git's three zones a change lives in determines which command undoes it safely.

> **Prerequisites —**
> 1. Must be inside a valid Git repository (`git init` or cloned).
> 2. `git restore` requires **Git 2.23.0+** (2019) — use legacy equivalents on older versions.
> 3. For `--amend`: must be on a **local-only** branch — do not amend commits already pushed to a shared remote.

> **Working tree state — conceptual overview:** Git tracks files across three zones:
> 1. **Working Tree** — your local filesystem; where you edit files.
> 2. **Staging Area (Index)** — files queued for the next commit via `git add`.
> 3. **Repository** — committed history; each snapshot has a unique SHA hash.
>
> Understanding which zone a file lives in determines which command to use.

> **Output state reference —**
>
> | Status Message | Meaning |
> |---|---|
> | `Changes not staged for commit` | Modified in working tree, not yet staged |
> | `Changes to be committed` | Staged; ready for next commit |
> | `nothing to commit, working tree clean` | Working tree matches last commit exactly |
> | `Untracked files` | New file Git has never seen |

> **Diff output prefix reference —**
>
> | Prefix | Meaning |
> |---|---|
> | `---` | Old version of the file |
> | `+++` | New version of the file |
> | `-` | Line removed in new version |
> | `+` | Line added in new version |
> | (none) | Unchanged context line |
>
> `@@ -1 +1 @@` indicates line numbers affected in the old (`-`) and new (`+`) file.

## Inspecting Working Tree State

```bash
# Check current state of working tree and staging area
git status
```

> **Command breakdown — `git status`:**
> 1. No flags required — produces full human-readable output by default.
> 2. `-s` / `--short` — terse, machine-friendly output format.
> 3. Read-only; generates no network traffic and no Git history artefacts.

## Diffing Working Tree vs. Last Commit

```bash
# Diff all modified files against staging area / last commit
git diff

# Explicitly diff working tree against latest commit on current branch
git diff HEAD

# Diff a specific file against a specific commit hash
git diff 4620193 example.html
```

> **Command breakdown — `git diff`:**
> 1. (no args) — compares working tree against the staging area; equivalent to last commit if nothing is staged.
> 2. `HEAD` — explicitly targets the latest commit on the current branch.
> 3. `<commit> <file>` — targets a specific file at a specific commit SHA.
> 4. Read-only; no history artefacts created.

> **Warning — Pager mode:** If output fills the terminal, Git enters pager mode (usually `less`). Scroll with arrow keys; press `q` to exit. Pager behaviour is controlled by the `$PAGER` environment variable.

> **No output shown —** The file may already be staged; staged changes are invisible to `git diff` (no args). Use `git diff --staged` to compare staged changes against the last commit.

## Discarding Local (Unstaged) Changes

> **Danger — Destructive operation:** `git restore` on the **working tree** permanently discards uncommitted edits. Changes are **not recoverable** unless a stash or reflog entry exists. Always run `git diff` first to review what will be lost.

```bash
# Restore all files in the current directory to last committed state
git restore .

# Restore a single named file only
git restore hello.html

# Restore a subdirectory
git restore src/
```

> **Command breakdown — `git restore` (working tree):**
> 1. `.` — restores all files in the current directory recursively.
> 2. `<file>` — restores a single named file only.
> 3. `<path/>` — restores an entire subdirectory.
> 4. `--worktree` — explicit flag for this mode; same as omitting it (default behaviour).
> 5. No network activity; modifies only local files.

```bash
# Confirm clean state after restoring
git status
# Expected: nothing to commit, working tree clean
```

> **Result —** `git restore` produces no output on success. Confirm with `git status` — should show `nothing to commit, working tree clean`.

> **Common errors —**
> 1. `error: pathspec 'X' did not match any file(s)` → check filename spelling and current working directory.
> 2. Accidentally discarding intended work → always run `git diff` before `git restore`.

> **Tip — Legacy equivalent:** `git checkout -- <file>` performs the same action but is superseded. Prefer `git restore` on modern installs (Git 2.23.0+).

## Unstaging Staged Changes

```bash
# Unstage all staged files — edits are preserved in working tree
git restore --staged .

# Unstage a single file — edits preserved
git restore --staged hello.html

# Unstage AND discard working tree changes in one step (destructive)
git restore --staged --worktree .
```

> **Command breakdown — `git restore --staged`:**
> 1. `--staged` — operates on the staging area (index) rather than the working tree; non-destructive.
> 2. `--staged --worktree` — unstages **and** discards working tree changes in a single command; destructive.
> 3. After `--staged` alone: file appears under `Changes not staged for commit` — edits still present.
> 4. After `--staged --worktree`: `git status` shows `nothing to commit, working tree clean`.

> **Warning — Easy to confuse:** `git restore .` ≠ `git restore --staged .` — the first only affects the **working tree**; it does not unstage. After `--staged` alone, edits are **not gone** — run `git restore .` separately if you also want to discard them.

> **Tip — Legacy equivalent:** `git reset HEAD <file>` performs the same unstaging action. Available on Git versions older than 2.23.0.

## Fixing the Last Commit — `--amend`

> **Danger — History-rewriting warning:**
> 1. `--amend` **replaces** the last commit — a new SHA is generated; the old one disappears locally.
> 2. **Do not amend commits already pushed to a shared remote** — this requires `git push --force`, which is visible to all collaborators.
> 3. The old commit object remains accessible via `git reflog` until garbage-collected.
> 4. On shared branches, prefer adding a new fix commit rather than amending.

```bash
# Fix only the commit message inline
git commit --amend -m "Added HTML tags to hello.html"

# Add a forgotten file and update the message in one step
git add hello.html
git commit --amend -m "Added H1, HTML, and BODY tags to hello.html"

# Amend message interactively via default text editor (vim/nano)
git commit --amend
```

> **Command breakdown — `git commit --amend`:**
> 1. `--amend` — replaces the most recent commit with a new one (new SHA generated).
> 2. `-m "<msg>"` — sets the new commit message inline; omit to open the configured text editor.
> 3. Pre-stage additional files with `git add` **before** running `--amend` to include them in the amended commit.
> 4. Git prints the updated commit summary including the new amended SHA on success.

> **Common editor traps —**
> 1. **Stuck in vim** (opened by omitting `-m`) → press `Esc`, type `:wq`, press `Enter` to save and exit.
> 2. **Stuck in nano** → `Ctrl+O` to save → `Enter` to confirm filename → `Ctrl+X` to exit.
> 3. **Amended a pushed commit** → coordinate with the team before force-pushing; prefer a new fix commit on shared branches.

> **Tip — Best-practice workflow:**
> 1. Stage any missed files: `git add <file>`
> 2. Review what will change: `git diff --staged`
> 3. Amend with corrected message: `git commit --amend -m "<message>"`
> 4. Verify result: `git log --oneline -1`

## References

- [git-status Documentation](https://git-scm.com/docs/git-status)
- [git-diff Documentation](https://git-scm.com/docs/git-diff)
- [git-restore Documentation](https://git-scm.com/docs/git-restore)
- [git-commit --amend Documentation](https://git-scm.com/docs/git-commit#Documentation/git-commit.txt---amend)
- [Atlassian — Rewriting Git History](https://www.atlassian.com/git/tutorials/rewriting-history)
