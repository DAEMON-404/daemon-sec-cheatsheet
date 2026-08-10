---
title: "Git — Move Existing Edits to a New Branch (Railway Site)"
description: "git checkout -b my-new-branch"
category: git-workflow
tags: ["git-workflow"]
tools: []
difficulty: intermediate
updated: "2026-08-10"
source: "vault:Git/Git — Move Existing Edits to a New Branch (Railway Site).md"
---
# 1. Create a new branch AND switch to it immediately
#    Your uncommitted edits travel with you automatically
git checkout -b my-new-branch

# 2. Now commit your edits on the new branch
git add .
git commit -m "Site edits — moved to own branch"

# 3. Push the new branch to GitHub
git push -u origin my-new-branch
```

> [!info]+ Command Breakdown
> 1. **`git checkout -b my-new-branch`**: Creates the new branch and switches to it in one step — crucially, all your uncommitted file changes come with you because they live in the working directory, not on any branch
> 2. **`git add .`**: Stages every modified file
> 3. **`git commit -m "..."`**: Locks your edits into the new branch's history
> 4. **`git push -u origin my-new-branch`**: Creates the branch on GitHub and sets it as the upstream — Railway can then be pointed at this branch

> [!success]+ Expected Result
> 1. `my-new-branch` exists on GitHub with all your edits committed
> 2. `main` is unchanged — still matches the original forked repo
> 3. Railway can be configured to deploy from `my-new-branch`

---

## Scenario B — Edits Are Already Committed on Main

*You already ran `git commit` — the changes are in `main`'s history*

```bash
# 1. Create a new branch at the current point in history
#    This copies main's current state (including your commits) into the new branch
git checkout -b my-new-branch

# 2. Push the new branch to GitHub
git push -u origin my-new-branch

# 3. Now go back to main and strip your commits off it
git checkout main

# 4. Reset main back to match the original remote (before your edits)
git reset --hard origin/main
```

> [!info]+ Command Breakdown
> 1. **`git checkout -b my-new-branch`**: Creates a new branch that starts from exactly where `main` currently is — all your committed edits are included
> 2. **`git push -u origin my-new-branch`**: Pushes the new branch to GitHub **before** touching `main` — your work is safely backed up remotely
> 3. **`git checkout main`**: Switches back to main so you can clean it up
> 4. **`git reset --hard origin/main`**: Forces your local `main` to exactly match what GitHub's `main` looks like — effectively removing your local commits from it

> [!warning]+ Do Step 2 Before Step 4
> Push `my-new-branch` to GitHub **first**. Once you reset `main`, those commits are gone from `main` locally. They are safe on `my-new-branch` but only if you pushed it first.

> [!success]+ Expected Result
> 1. `my-new-branch` on GitHub contains all your site edits
> 2. `main` is clean — matches the original forked repo
> 3. No merging has occurred — the two branches are fully independent

---

## Pointing Railway at Your New Branch

> [!tip]+ Railway Deployment Branch
> 1. Go to your project in [Railway](https://railway.app/)
> 2. Navigate to **Settings → Source**
> 3. Change the deployment branch from `main` to `my-new-branch`
> 4. Railway will now build and deploy from your edits branch
> 5. `main` can remain as your clean baseline / fallback

---

## Quick Reference — Your Exact Workflow

```bash
# ── CHECK WHERE YOU ARE ───────────────────────────────
git status                          # See uncommitted changes
git log --oneline -5                # See last 5 commits on current branch

# ── SCENARIO A (uncommitted edits) ───────────────────
git checkout -b my-new-branch       # Move edits to new branch
git add .                           # Stage everything
git commit -m "My site edits"       # Commit on new branch
git push -u origin my-new-branch    # Push to GitHub

# ── SCENARIO B (already committed on main) ────────────
git checkout -b my-new-branch       # Branch off current main
git push -u origin my-new-branch    # Push new branch FIRST (safety)
git checkout main                   # Go back to main
git reset --hard origin/main        # Strip your commits from main

# ── VERIFY EVERYTHING LOOKS RIGHT ────────────────────
git branch -a                       # See all branches
git log --oneline -5                # Check commit history on current branch
git checkout my-new-branch          # Switch to your edits branch to confirm
```

---

## References

1. [Git Official Documentation](https://git-scm.com/doc)
2. [git-checkout — Git Reference](https://git-scm.com/docs/git-checkout)
3. [git-reset — Git Reference](https://git-scm.com/docs/git-reset)
4. [Railway Docs — Deployments](https://docs.railway.app/deploy/deployments)
5. [GitHub Docs — About Branches](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-branches)

---

#Git #GitHub #Railway #BranchManagement #Workflow #SiteDeployment
