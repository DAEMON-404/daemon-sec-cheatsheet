# DÆMON//SEC — Cyber & IT Cheatsheet Vault — Design Spec

**Date:** 2026-08-09
**Status:** Approved
**Owner:** DAΞMON (Daemon-AT4)

## Purpose

A GitHub Pages website that is a curated, high-polish public vault of the best IT
and cybersecurity cheatsheets. Sourced from the local NetrunnerVault cheatsheet
collection (`/Volumes/bmdrbeKUVgvV/NetrunnerVault/02Cybersecurity/Cheatsheets`,
224 markdown + 14 PDF + 6 SVG) plus the `Ethical_Hacking-Cheatsheets` working
repo. Curated to ~60 canonical pages, each modernized before first deploy.

## Success criteria

- Live at `https://daemon-at4.github.io/daemon-sec` via GitHub Actions.
- ~60 curated cheatsheets, deduplicated, each with normalized frontmatter and
  reviewed/modernized content (current flags, versions, CVE refs).
- Distinctive visual identity: Rose Pine (dark, default) + Rose Pine Dawn (light),
  Apple-glass frosted panels, restrained cyberpunk neon accents.
- Instant offline fuzzy search (Pagefind), keyboard shortcut `/`.
- Fully responsive, WCAG AA contrast both themes, respects reduced-motion.

## Stack

- **Astro 5** static site (TypeScript, content collections).
- **Pagefind** for build-time search index (offline, no server).
- **Shiki** syntax highlighting with a rose-pine code theme.
- Self-hosted fonts (Chakra Petch / Inter / JetBrains Mono).
- **GitHub Actions → Pages**. Project page, base path `/daemon-sec/`.

## Design system

### Palette — Rose Pine + Rose Pine Dawn
Dark (default, Rose Pine):
`base #191724, surface #1f1d2e, overlay #26233a, muted #6e6a86, subtle #908caa,
text #e0def4, love #eb6f92, gold #f6c177, rose #ebbcba, pine #31748f,
foam #9ccfd8, iris #c4a7e7, highlight #403d52`

Light (Rose Pine Dawn):
`base #faf4ed, surface #fffaf3, overlay #f2e9e1, muted #9893a5, subtle #797593,
text #575279, love #b4637a, gold #ea9d34, rose #d7827e, pine #286983,
foam #56949f, iris #907aa9, highlight #dfdad9`

Delivered as CSS custom properties on `:root` (light) and `:root[data-theme]`
overrides. Toggle persisted to `localStorage`, honors `prefers-color-scheme`.
Dark is the default.

### Apple glass
Frosted translucent panels: `backdrop-filter: blur(16px) saturate(140%)`,
semi-transparent surface fill, hairline 1px border with low-alpha highlight,
layered box-shadow for depth, subtle inner top highlight. Applied to header,
nav rail, cards, search modal.

### Cyberpunk accents (restrained)
- Neon edge-glow on hover using palette accents (rose/iris/foam/gold).
- Faint scanline + grid texture on the hero only.
- Animated gradient borders on featured/hover cards.
- Subtle noise grain overlay at very low opacity.
- Monospace command blocks with a terminal-style top bar + copy button.
All motion gated behind `prefers-reduced-motion`.

### Typography
- Display: Chakra Petch (cyber geometric). Body: Inter. Code: JetBrains Mono.
- Self-hosted woff2 in `public/fonts`, `font-display: swap`.

## Content pipeline

1. **Curate** (~60): score all 224 vault sheets, select one canonical page per
   topic, resolve duplicates (keep the richer copy), include IT staples
   (git, tmux, linux find, chmod, macOS terminal). Output: selection manifest.
2. **Ingest**: copy selected markdown into `src/content/sheets/<category>/`,
   normalize frontmatter: `title, description, category, tags, tools, difficulty,
   updated, source`. Strip Obsidian-only syntax; rewrite wikilinks/attachment
   embeds to site-relative or drop.
3. **PDF-only best content** (netexec, rustscan, ffuf, HTB sheets): rewrite into
   native themed markdown pages (searchable, on-theme). Any that cannot be
   cleanly extracted → embedded PDF viewer + download link in `public/pdfs`.
4. **Modernize**: one pass per selected sheet — update stale flags, tool
   versions, CVE references, fix broken commands, add common missing usage.
   **Guardrails:** never fabricate flags/CVEs; if unsure keep the original and
   flag it; preserve author voice. Legal note: content is for authorized
   testing / education (matches existing repo framing).

## Taxonomy & pages

Categories (from folder tree, ~12): Active Directory, Enumeration, Exploitation,
Privilege Escalation, Password Attacks, Web, Tunneling & Pivoting, Cryptography,
DFIR, Tools, Linux & IT, Git & Workflow.

- **Landing**: hero (glass + scanline) → search → glass category grid → featured.
- **Category page**: filtered card grid, count, description.
- **Sheet page**: sticky TOC rail, copy-code buttons, updated/source/difficulty
  badges, tag pills, prev/next, breadcrumb.
- **Tag index** + **Tool index** cross-reference pages.
- Themed **404**. Global search modal (`/`). Theme toggle in header.

## Repo structure

```
daemon-sec-vault/                 # local; GitHub repo = Daemon-AT4/daemon-sec
  .github/workflows/deploy.yml
  astro.config.mjs · package.json · tsconfig.json
  scripts/ingest.mjs              # copy + normalize curated files from vault
  content-manifest.json           # curation selection + dedupe decisions
  src/
    content/sheets/<cat>/*.md      # curated, modernized content
    content/config.ts              # collection schema (zod)
    components/  (GlassCard, CodeBlock, ThemeToggle, SearchModal, TOC, NavRail,
                  CategoryBadge, TagPill, Hero, Footer, Prose)
    layouts/     (Base.astro, Sheet.astro)
    pages/       (index, [category]/index, sheets/[...slug], tags, tools, 404)
    styles/      (tokens.css, glass.css, global.css, prose.css)
    lib/         (nav.ts, taxonomy.ts)
  public/  fonts/  pdfs/  svgs/  favicon.svg  og image
```

## Execution phases (multi-agent)

- **A — Curate**: agents score & select ~60 → `content-manifest.json`.
- **B — Modernize**: pipeline, ~1 agent per selected sheet → cleaned + updated
  markdown with normalized frontmatter. Human-reviewed batch.
- **C — Scaffold**: build Astro app, theme, components, pages (parallel with A/B).
- **D — Integrate & deploy**: assemble content, `astro build` + Pagefind, create
  `Daemon-AT4/daemon-sec`, push, enable Pages, verify live.

## Decisions locked

- Engine: Astro + Pagefind. Scope: curated ~60 tight. Deploy: new public repo
  `Daemon-AT4/daemon-sec`. Content updates: enhance-during-build.
- Default theme: dark Rose Pine. PDFs: rewrite to markdown where feasible.

## Out of scope (v1)

- Custom domain. Comments/analytics. Auth. Non-cyber IT beyond staples.
- Full 224-page ingest (deferred; can expand later from manifest).
