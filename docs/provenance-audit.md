# Provenance & Attribution Audit — `src/content/sheets`

**Date:** 2026-08-13
**Scope:** the 215 hand-curated cheatsheets under `src/content/sheets/`. The `payloads/` and
`internal/` mirrors are out of scope — they are already attributed on `/credits` and carry a
per-page `PayloadCredit` banner.
**Purpose:** find third-party content that is currently republished without credit, so it can be
credited. This audit exists to *give* attribution, not to remove content quietly.

---

## 1. Summary

| | Count |
|---|---|
| Sheets in `src/content/sheets/` | 215 |
| Sheets carrying `source: "vault:…"` (records vault path only — says nothing about origin) | 204 |
| Sheets carrying `source: "repo:…"` (self-declared external origin) | 11 |
| Screened as candidates across the two triage phases | 140 |
| Escalated to evidence-based adjudication | 5 |
| **Attributable (verbatim copy or derived) — action required** | **4** |
| Dismissed after adjudication (original commentary) | 1 |
| Never entered triage | 75 |

### Licence exposure

| Situation | Sheets | Currently satisfied? |
|---|---|---|
| MIT upstream — notice must travel with the copy | 2 | **No.** The copyright/permission notice is absent from both sheets and from `/credits`. |
| Upstream with **no licence at all** — no grant of rights to copy | 1 | **No, and credit alone does not cure it.** |
| Proprietary course material — no redistribution licence | 1 confirmed, 1 further sheet identified during report assembly | **No.** |

**Bottom line:** four sheets need action. Two are an MIT-notice problem that is fixed by adding
credit. Two are *not* fixed by adding credit — one has no licence grant at all, one is proprietary
material — and need a keep/link-only/remove decision from you.

### Honest statement of coverage

This is **not** a clean bill of health for the other 211 sheets. 140 sheets were screened and 5 were
escalated with hard evidence; the 135 that were screened but not escalated were judged to be generic
tool documentation or unattributable command references, which is the correct call for that material
(see §5). But **75 sheets never entered triage at all**, and the 11 `repo:`-sourced sheets in §3.4
declare a third-party origin in their own frontmatter and were never adjudicated. Treat the counts
above as "what has been proven so far", not "what exists".

---

## 2. Priority table

Sorted by urgency: no-licence and proprietary first (credit does not resolve them), then
notice-requiring licences, then everything already resolved.

| Sheet | Upstream | Author | License | Status | Action |
|---|---|---|---|---|---|
| `enumeration/awesome-nmap-grep.md` | [awesome-nmap-grep](https://github.com/leonjza/awesome-nmap-grep) README | Leon Jacobs ([@leonjza](https://github.com/leonjza)) | **None** — no LICENSE file, repo `license` field is `null`, `/license` API returns 404 | **Confirmed verbatim** — byte-for-byte, MD5 `069f471d9d692e02070a12d8ee0792f1`, 271 lines / 8207 bytes, `diff` reports zero differences | **Decide first.** No grant of rights exists, so republication is not permitted by any licence. Options: (a) ask Leon Jacobs for permission, (b) reduce to a short excerpt + credit + link, (c) replace with a link-only stub, (d) remove. Adding a credit line alone does **not** make this compliant. |
| `enumeration/lfi.md` | [HTB Academy — File Inclusion module](https://academy.hackthebox.com/course/preview/file-inclusion) end-of-module cheat sheet | Hack The Box | **Proprietary**, all rights reserved | **Confirmed verbatim** — row-for-row identical, incl. the session filename `sess_nhhv8i0o6ua4g88bkdl9u1fdsd` and the full File Inclusion Functions matrix | **Remove or replace with a link.** HTB course material is not licensed for redistribution; credit does not create a licence. Recommended: delete the sheet and link the module, or rewrite from scratch in your own words. |
| `active-directory/active-directory-cheat-sheet.md` | [Active-Directory-Exploitation-Cheat-Sheet](https://github.com/S1ckB0y1337/Active-Directory-Exploitation-Cheat-Sheet) README | Nikos Katsiopis & Nikos Vourdas (S1ckB0y1337) | **MIT** — notice required | **Confirmed verbatim** — the only line dropped from upstream is the authorship notice | **Add credit + reproduce the MIT notice.** Restore the dropped line `This repository was created by Nikos Katsiopis and Nikos Vourdas.` or its equivalent, add the frontmatter fields from §4, and add the MIT text to `/credits`. |
| `active-directory/active-directory-attacks.md` | Same upstream (S1ckB0y1337), itself inspired by [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) | Nikos Katsiopis & Nikos Vourdas; ancestral: Swissky | **MIT** — notice required | **Confirmed derived** — same vault source path as the sheet above; reworded but the DCSync comment, LSA-protection bypass block and "Breaking Forest Trusts" chain track upstream | **Add credit.** Same treatment; mark `upstreamRelation: derived` and name both S1ckB0y1337 and the ancestral PayloadsAllTheThings lineage. |
| `web/file-inclusion.md` | HTB Academy — File Inclusion module (per its own `source: "repo:HTB/cheatsheet-file-inclusion.pdf"`) | Hack The Box | **Proprietary** | **Probable derived** — added during report assembly, not by the triage phases. Verified directly: shares the distinctive HTB payload strings with `enumeration/lfi.md` (`?language=./languages/../../../../etc/passwd`, "Bypass appended extension with path truncation (obsolete)", `[./ REPEATED ~2048 times]`) but is reorganised and rewritten with its own prose. | **Assess alongside `enumeration/lfi.md`.** Provenance is not in doubt — the frontmatter declares it. The open question is only whether the rewriting is substantial enough to stand as your own work. If yes, keep with a "based on" credit; if no, treat as `enumeration/lfi.md`. |
| `enumeration/cheatsheet-infrastructure-enumeration-tools-1.md` | HTB Academy — Footprinting module (topic scaffolding only) | Hack The Box (topic only) | n/a | **Dismissed** — no third-party expression reproduced; the distinctive sentences return no external source and are self-described as the owner's own additions | **None.** HTB Footprinting is already cited in the file's own References section. Listed here so the dismissal is on the record. |

---

## 3. Special cases

### 3.1 Upstream with NO licence file — `enumeration/awesome-nmap-grep.md`

Stated plainly: **`github.com/leonjza/awesome-nmap-grep` carries no licence.** Verified three ways —
`gh api repos/leonjza/awesome-nmap-grep/contents` returns exactly one entry (`README.md`), the
`/license` endpoint returns HTTP 404, and the repo metadata `license` field is `null`. Grepping the
README for `licen|copyright|author|MIT` returns nothing.

Default copyright therefore applies: **all rights reserved by the author.** There is no permission to
copy, host, or redistribute the file, and no attribution line can manufacture one. This is a
*stronger* problem than the MIT precedent, not a weaker one — with MIT you have permission and merely
failed to carry the notice; here you have no permission.

The file is currently a perfect byte-for-byte copy, including the author's own captured terminal
output (the macOS `outif lo0` netcat transcript, ephemeral ports 52224/54695/58369, and literal
mojibake in a MariaDB banner) and the self-referential phrase "This repository", which is a tell that
nothing was modified.

Your options, honestly ranked:

1. **Ask.** Open an issue on the repo or email Leon Jacobs asking for permission to mirror with
   credit. Many authors say yes immediately. Until he does, do not publish a credit line that claims
   "used with permission" — that would be untrue.
2. **Excerpt.** Keep a handful of the grep one-liners with a prominent credit and a link. Short
   excerpts with attribution are a much smaller ask than a full mirror.
3. **Link-only stub.** Replace the body with a description and a link to the upstream repo.
4. **Remove.**

Do **not** simply add a credit banner and leave the full copy up — that fixes the ethics and not the
licensing.

### 3.2 Proprietary / non-redistributable upstream — the HTB Academy material

`enumeration/lfi.md` is confirmed as a reproduction of an HTB Academy end-of-module cheat sheet. HTB
Academy content is paid, proprietary course material; there is no redistribution licence, and
crediting HTB does not create one. `web/file-inclusion.md` derives from the same module.

The realistic remedy is to link to the module rather than reproduce it, or to rewrite the material in
your own words from primary sources (PHP docs, OWASP) so the expression is yours. Note the underlying
*techniques* are not ownable — LFI traversal is public knowledge. What is ownable is HTB's particular
selection, ordering, table layout and example values, which is exactly what was copied.

### 3.3 Copyleft or non-commercial upstreams

**None found.** No adjudicated sheet traces to a GPL, AGPL, CC-BY-SA or CC-BY-NC source. Nothing in
the confirmed set constrains rehosting through share-alike or non-commercial terms.

### 3.4 Sheets that declare a third-party origin but were never adjudicated

Eleven sheets carry `source: "repo:…"` rather than `source: "vault:…"`. These are self-declared
imports from an external cheatsheet collection and **none of them appear in the triage results.**
This is the largest known gap in the audit.

| Sheet | Declared source | Note |
|---|---|---|
| `web/file-inclusion.md` | `repo:HTB/cheatsheet-file-inclusion.pdf` | Assessed in §2 — HTB, probable derived |
| `web/sql-injection.md` | `repo:HTB/cheatsheet-sql-injection-fundamentals.pdf` | HTB Academy module cheat sheet; also mentions hackthebox in-body |
| `tools/file-transfers.md` | `repo:HTB/cheatsheet-file-transfers.pdf` | HTB Academy module cheat sheet |
| `exploitation/buffer-overflow.md` | `repo:HTB/cheatsheet-stack-based-buffer-overflows-on-windows-x86.pdf` | HTB Academy module cheat sheet |
| `password-attacks/password-attacks.md` | `repo:Password-Attacks/Password_Attacks_Cheat_Sheet.pdf` | Not labelled HTB, but contains `InlaneFreight` — HTB's lab domain — which is a strong HTB tell |
| `cryptography/openssl.md` | `repo:Misc/openssl-cheatsheet.pdf` | Origin of the PDF unknown |
| `linux-it/chmod.md` | `repo:Linux/chmod-cheatsheet.pdf` | Origin of the PDF unknown |
| `active-directory/impacket.md` | `repo:Active-Directory/Impacket_Cheatsheet.md` | Origin unknown; "Cheatsheet" filenames of this shape usually come from a named author |
| `active-directory/certipy.md` | `repo:Active-Directory/Certipy-ad.md` | Origin unknown |
| `active-directory/bloodhound.md` | `repo:Active-Directory/BloodHound-Python_Cheatsheet.md` | Origin unknown |
| `enumeration/shodan.md` | `repo:Enumeration/Shodan_Cheatsheet.md` | Origin unknown |

Four of these name HTB explicitly and a fifth carries HTB's lab domain — the same proprietary-source
problem as §3.2, five more times over. **Recommend a follow-up pass over these eleven before shipping
any attribution changes**, since the frontmatter has effectively already admitted the provenance and
only the upstream identity and degree of copying remain to be established.

One mitigation worth recording: the `pdf:` frontmatter field exists in the schema and
`src/pages/sheets/[...slug].astro` will embed a PDF viewer for it, but **no sheet currently sets
`pdf:` and `public/pdfs/` does not exist** — so the source PDFs themselves are not being
redistributed. Only the transcribed markdown is.

### 3.5 Disagreements or thin evidence

- **No two-agent disagreement occurred.** All five adjudications were unanimous.
- **Thinnest evidence in the confirmed set:** `active-directory/active-directory-attacks.md`. It is
  reworded rather than copied, so the case rests on shared vault provenance with the confirmed sheet
  plus matching distinctive comment strings and section chains — strong, but a step below the
  byte-for-byte proof behind the other three. `derived` is the right label; do not describe it as a
  verbatim copy.
- **`web/file-inclusion.md` is my own addition**, found while assembling this report, and has not
  been through the two triage phases. I verified the shared HTB strings directly; I have **not**
  compared it against the HTB PDF line by line. Confidence: high that HTB is the source (its own
  frontmatter says so), moderate on whether it is "derived" versus genuinely rewritten.
- **Nothing was flagged on `licenseRequiresNotice` grounds without checking the actual upstream
  licence.** In one case the earlier triage assumed MIT for `awesome-nmap-grep` and that assumption
  was wrong — the repo has no licence — which is why §3.1 is more serious than a missing credit line.

---

## 4. Recommended mechanism

The site already has a working attribution pattern for the mirrors. Extend it to `sheets` rather than
inventing anything new.

### 4.1 Schema — `src/content.config.ts`

Add to the `sheets` collection schema (after the existing `source` field on line 24). Keep `source`
as-is; it records the vault path and is orthogonal.

```ts
    source: z.string().optional(),

    // --- Third-party attribution ---------------------------------------
    // Set together. `upstreamRelation` gates the whole block: if it is
    // present, the rest is required (enforced by superRefine below).
    upstreamName: z.string().optional(),        // "Active Directory Exploitation Cheat Sheet"
    upstreamUrl: z.string().url().optional(),   // canonical upstream location
    upstreamAuthor: z.string().optional(),      // "Nikos Katsiopis & Nikos Vourdas (S1ckB0y1337)"
    upstreamLicense: z                          // SPDX id, or the two honest non-ids
      .enum([
        'MIT', 'BSD-2-Clause', 'BSD-3-Clause', 'Apache-2.0',
        'CC-BY-4.0', 'CC-BY-SA-4.0', 'GPL-3.0-only',
        'none',        // upstream publishes NO licence — no grant of rights
        'proprietary', // course material, vendor docs, all rights reserved
      ])
      .optional(),
    upstreamRelation: z.enum(['verbatim', 'derived', 'inspired']).optional(),
    // Verbatim copyright line to reproduce, e.g. "Copyright (c) 2020 Nikos Katsiopis".
    // Required for MIT/BSD/Apache — this is the notice the licence says must travel.
    upstreamNotice: z.string().optional(),
    // Rights status for licences that grant nothing on their own.
    upstreamPermission: z.enum(['licensed', 'granted', 'pending', 'none']).optional(),
```

…and close the object with a `superRefine` so a half-filled credit fails the build instead of
shipping a misleading banner:

```ts
  }).superRefine((d, ctx) => {
    if (!d.upstreamRelation) return;
    for (const f of ['upstreamName', 'upstreamUrl', 'upstreamAuthor', 'upstreamLicense'] as const) {
      if (!d[f]) ctx.addIssue({ code: 'custom', path: [f], message: `${f} is required when upstreamRelation is set` });
    }
    const noticeRequired = ['MIT', 'BSD-2-Clause', 'BSD-3-Clause', 'Apache-2.0'];
    if (d.upstreamLicense && noticeRequired.includes(d.upstreamLicense) && !d.upstreamNotice) {
      ctx.addIssue({ code: 'custom', path: ['upstreamNotice'], message: `${d.upstreamLicense} requires the copyright notice to be reproduced` });
    }
    if ((d.upstreamLicense === 'none' || d.upstreamLicense === 'proprietary') && !d.upstreamPermission) {
      ctx.addIssue({ code: 'custom', path: ['upstreamPermission'], message: 'set upstreamPermission — this licence grants no redistribution right on its own' });
    }
  }),
```

Note `defineCollection` schemas accept a `ZodEffects` from `superRefine`, but the object must be
built before `.superRefine()` is chained — keep the existing `z.object({ … })` and chain onto it.

### 4.2 Per-sheet banner — new `src/components/SheetCredit.astro`

Model it on `src/components/PayloadCredit.astro` and reuse the same class names (`patt-credit`,
`patt-badge`, `patt-credit__text`, `patt-lic`, `patt-src`) so no new CSS is needed.

```astro
---
import Icon from './Icon.astro';
import { url } from '../lib/url';
interface Props {
  name: string; upstreamUrl: string; author: string;
  license: string; relation: 'verbatim' | 'derived' | 'inspired';
  notice?: string; permission?: string;
}
const { name, upstreamUrl, author, license, relation, notice, permission } = Astro.props;
const verb = relation === 'verbatim' ? 'Reproduced from'
           : relation === 'derived'  ? 'Derived from'
           :                           'Based on';
const warn = license === 'none' || license === 'proprietary';
---
<aside class="patt-credit" aria-label="Attribution" data-warn={warn ? '' : null}>
  <span class="patt-badge">{relation}</span>
  <span class="patt-credit__text">
    {verb} <a href={upstreamUrl} target="_blank" rel="noopener">{name}</a> by <strong>{author}</strong>
    <span class="patt-lic">
      {license === 'none' ? 'no licence' : license}
      {notice && <> · {notice}</>}
      {permission === 'granted' && <> · used with permission</>}
      · <a href={url('credits')}>credits</a>
    </span>
  </span>
  <a class="patt-src" href={upstreamUrl} target="_blank" rel="noopener" aria-label="View upstream source">
    <Icon name="github" style="width:15px;height:15px;" /> source
  </a>
</aside>
```

Render it in `src/pages/sheets/[...slug].astro`, inside `<article class="prose" data-pagefind-body>`
immediately **before** the existing `{pdfHref && …}` block (currently around line 59), so the credit
sits above the content and above the fold:

```astro
{d.upstreamUrl && (
  <SheetCredit
    name={d.upstreamName!} upstreamUrl={d.upstreamUrl} author={d.upstreamAuthor!}
    license={d.upstreamLicense!} relation={d.upstreamRelation!}
    notice={d.upstreamNotice} permission={d.upstreamPermission}
  />
)}
```

Add the import next to the existing `Icon` import at the top of that file.

### 4.3 Credits page — `src/pages/credits.astro`

Two changes.

**(a) Fix the currently-inaccurate paragraph.** Lines 96–101 say sheets "credit their upstream source
in frontmatter where applicable" — today none of them do. Replace with a statement of what is
actually true once the fields land.

**(b) Add a "Third-party cheatsheets" section** between the existing
`<h2>The DÆMON//SEC cheatsheets</h2>` block and `<h2>This site</h2>`, driven by a new helper in
`src/lib/sheets.ts`:

```ts
// src/lib/sheets.ts
export async function attributedSheets() {
  const all = await getCollection('sheets');
  const withCredit = all.filter((e) => e.data.upstreamUrl);
  const byUpstream = new Map<string, { data: any; sheets: typeof withCredit }>();
  for (const e of withCredit) {
    const k = e.data.upstreamUrl!;
    if (!byUpstream.has(k)) byUpstream.set(k, { data: e.data, sheets: [] });
    byUpstream.get(k)!.sheets.push(e);
  }
  return [...byUpstream.values()].sort((a, b) => a.data.upstreamName.localeCompare(b.data.upstreamName));
}
```

The section should render, per upstream: name + link, author, licence, relation, the sheets that
derive from it (linked via `sheetHref`), and — for MIT/BSD/Apache — the **full licence text**, using
the same `<figure class="code-pane">` treatment already used for the Swissky MIT block at lines
67–73. That full-text block is what actually discharges the MIT obligation that "the above copyright
notice and this permission notice shall be included in all copies or substantial portions"; a link
alone is weaker.

For `upstreamLicense: 'none'` and `'proprietary'` entries the section should say so in plain language
rather than listing a licence — mirroring the honest wording already used for InternalAllTheThings on
line 86 ("the repository publishes no LICENSE file, so no licence is claimed or implied here"), which
is a good precedent and should be the template.

### 4.4 Frontmatter to apply, per sheet

Paste-ready, assuming you keep the sheets. For the two that need a rights decision first, the block
is written as it would be *after* permission is obtained — do not commit those until it is.

`src/content/sheets/active-directory/active-directory-cheat-sheet.md`:

```yaml
upstreamName: "Active Directory Exploitation Cheat Sheet"
upstreamUrl: "https://github.com/S1ckB0y1337/Active-Directory-Exploitation-Cheat-Sheet"
upstreamAuthor: "Nikos Katsiopis & Nikos Vourdas (S1ckB0y1337)"
upstreamLicense: "MIT"
upstreamRelation: "verbatim"
upstreamNotice: "Copyright (c) 2020 Nikos Katsiopis"
upstreamPermission: "licensed"
```

Also restore the authorship line that was dropped from the upstream README body.

`src/content/sheets/active-directory/active-directory-attacks.md`:

```yaml
upstreamName: "Active Directory Exploitation Cheat Sheet"
upstreamUrl: "https://github.com/S1ckB0y1337/Active-Directory-Exploitation-Cheat-Sheet"
upstreamAuthor: "Nikos Katsiopis & Nikos Vourdas (S1ckB0y1337); ancestral source: Swissky / PayloadsAllTheThings"
upstreamLicense: "MIT"
upstreamRelation: "derived"
upstreamNotice: "Copyright (c) 2020 Nikos Katsiopis"
upstreamPermission: "licensed"
```

`src/content/sheets/enumeration/awesome-nmap-grep.md` — **only after Leon Jacobs agrees**:

```yaml
upstreamName: "awesome-nmap-grep"
upstreamUrl: "https://github.com/leonjza/awesome-nmap-grep"
upstreamAuthor: "Leon Jacobs (@leonjza)"
upstreamLicense: "none"
upstreamRelation: "verbatim"
upstreamPermission: "granted"   # ONLY once actually granted; use "pending" until then
```

`src/content/sheets/enumeration/lfi.md` and `src/content/sheets/web/file-inclusion.md` — recommended
outcome is removal or rewrite, not a credit block. If you keep them pending a decision, set
`upstreamLicense: "proprietary"` and `upstreamPermission: "none"` so the banner states the position
honestly and the build does not let it be forgotten.

### 4.5 Suggested order of work

1. Decide the rights questions (§3.1, §3.2) — they may change what gets published at all.
2. Land the schema + component + credits section with the two MIT sheets. That closes the known
   compliance gap and creates the mechanism.
3. Run the follow-up pass over the eleven `repo:`-sourced sheets in §3.4.
4. Consider triaging the 75 sheets that never entered triage.

---

## 5. Explicitly excluded

The audit deliberately did **not** flag:

- **The 135 screened-but-not-escalated sheets.** These are command references, tool-flag listings and
  syntax tables. `nmap -sV`, `hashcat -m 1000`, `impacket-secretsdump` invocations and the like are
  facts about tools, not authorship — they look identical everywhere because there is only one way to
  write them. Documenting a public tool is not evidence of copying, and flagging on that basis would
  have produced a list too noisy to act on.
- **`enumeration/cheatsheet-infrastructure-enumeration-tools-1.md`**, which reached adjudication and
  was cleared. Its distinctive sentences ("This is cleaner than the grep | cut | awk chain in the
  original notes", "Expired subdomains are often forgotten by admins") return no external source and
  are self-described as the owner's own additions. The crt.sh + `jq` pipeline, `dig` record queries
  and Shodan filters are generic recon idioms nobody owns, and the one genuine third-party input —
  the HTB Footprinting module's topic scaffolding — is already cited in the file's own References
  section. This is what a correct dismissal looks like.
- **The 47 sheets that already carry a `## References` / `## Credits` / `## Sources` section.** These
  were not treated as suspicious; existing citation is evidence of good faith, not of copying.
- **Shared technique, structure and terminology.** Kerberoasting is Kerberoasting, and every AD
  cheatsheet covers enumeration → roasting → delegation → lateral movement in roughly that order,
  because that is the order of the attack. Only *expression* — specific prose, specific example
  values, specific selection and layout — was treated as attributable.

Four sheets out of 215 were flagged. That ratio is the point: the audit looked hard at 140 and found
a small, specific, actionable set rather than blanket-flagging a vault of public security notes.
