<div align="center">

# DÆMON//SEC

**The cheatsheet vault for operators.**

A curated, glassy vault of the best IT & cybersecurity cheatsheets —
Active Directory, enumeration, exploitation, priv-esc, web, DFIR, and more.
Fast offline search, copy-ready commands, zero fluff.

🌐 **[daemon-404.github.io/daemon-sec-vault](https://daemon-404.github.io/daemon-sec-vault)**

`Rose Pine · Apple-glass · cyberpunk` — built with [Astro](https://astro.build) + [Pagefind](https://pagefind.app)

</div>

---

## What's inside

60 hand-picked, modernized cheatsheets across 12 domains:

| Domain | Domain | Domain |
| ------ | ------ | ------ |
| Active Directory | Enumeration | Exploitation |
| Privilege Escalation | Password Attacks | Web |
| Tunneling & Pivoting | Cryptography | DFIR |
| Tools | Linux & IT | Git & Workflow |

Each page is stripped of vault-specific syntax, given consistent frontmatter
(tags, tools, difficulty), and refreshed for current tool flags and versions.

## Features

- **Rose Pine** dark theme with a **Rose Pine Dawn** light toggle (respects your system preference).
- **Apple-glass** frosted panels with restrained cyberpunk neon accents.
- Every code block is a **terminal pane** with one-click copy.
- **Instant offline fuzzy search** (`/` or `⌘K`) — no server, no tracking.
- Fully responsive, keyboard-accessible, `prefers-reduced-motion` aware.

## Develop

```bash
npm install
npm run dev        # local dev server
npm run build      # astro build + pagefind search index -> dist/
npm run preview    # preview the production build
```

## Deploy

Pushing to `main` triggers `.github/workflows/deploy.yml`, which builds the site
and publishes `dist/` to GitHub Pages. Enable Pages once under
**Settings → Pages → Source: GitHub Actions**.

## Content structure

Cheatsheets live in `src/content/sheets/<category>/<slug>.md` with frontmatter:

```yaml
---
title: "Rubeus"
description: "Kerberos abuse toolkit…"
category: active-directory
tags: [kerberos, tickets]
tools: [Rubeus]
difficulty: advanced
updated: "2026-08-09"
---
```

Category slugs, colors, and labels are defined in `src/lib/taxonomy.ts`.

## Legal

For **authorized testing, CTFs, and education only**. Know your scope and get
written permission before touching a system you don't own. The maintainers are
not responsible for misuse.

Licensed under [MIT](./LICENSE).
