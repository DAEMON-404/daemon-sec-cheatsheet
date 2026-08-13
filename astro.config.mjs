// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import Slugger from 'github-slugger';

const BASE = '/daemon-sec-cheatsheet';

// Root-relative links written into markdown content (e.g. the internalized
// PayloadsAllTheThings nav links "/payloads/...") don't get the project base
// prefix from Astro automatically. This rehype pass prepends it to internal
// href/src, so links resolve correctly under the GitHub Pages sub-path.
function rehypeBaseLinks() {
  const walk = (node) => {
    if (node.type === 'element' && node.properties) {
      for (const attr of ['href', 'src']) {
        const v = node.properties[attr];
        if (
          typeof v === 'string' &&
          v.startsWith('/') &&
          !v.startsWith('//') &&
          v !== BASE &&
          !v.startsWith(BASE + '/')
        ) {
          node.properties[attr] = BASE + v;
        }
      }
    }
    if (node.children) for (const c of node.children) walk(c);
  };
  return (tree) => walk(tree);
}

/**
 * MkDocs anchor aliases for the InternalAllTheThings mirror.
 *
 * Upstream is a MkDocs site, and python-markdown's slugifier collapses every
 * run of `[-\s]` to one dash where github-slugger (Astro's) keeps them: the
 * heading "Meterpreter - Basic" is `#meterpreter-basic` upstream and
 * `#meterpreter---basic` here. Every deep link ever written against the
 * upstream page carries the MkDocs form — outside bookmarks and search hits,
 * and the IATT links this site rewrites out of the PayloadsAllTheThings stubs
 * — so without an alias they all land at the top of the page.
 *
 * The github-slugger id stays primary, because IATT's own in-page tables of
 * contents are written GitHub-style and resolve against it (they are in fact
 * broken on the live upstream site). The MkDocs form is emitted as an empty
 * span *inside* the heading: a sibling before it would break
 * `.prose > h1:first-child`, which hides the duplicated page title.
 *
 * Ids are assigned here rather than left to Astro because user rehype plugins
 * run before its heading-id pass, so the id has to exist to be compared
 * against. Astro keeps an id that is already a string, so this is the same
 * value it would have written.
 */
const RAW_NODE_TYPES = new Set(['text', 'raw', 'mdxTextExpression']);
const CODE_TAG_NAMES = new Set(['code', 'pre']);

/** python-markdown's `toc.slugify`, separator "-". */
function mkdocsSlug(text) {
  return text
    .normalize('NFKD')
    .replace(/[^\x00-\x7f]/g, '')
    .replace(/[^\w\s-]/g, '')
    .trim()
    .toLowerCase()
    .replace(/[-\s]+/g, '-');
}

/** python-markdown disambiguates a repeat with `_1`, `_2`; github-slugger `-1`. */
function uniqueMkdocsSlug(slug, used) {
  let id = slug;
  while (!id || used.has(id)) {
    const m = /^(.*)_(\d+)$/.exec(id);
    id = m ? `${m[1]}_${Number(m[2]) + 1}` : `${id}_1`;
  }
  used.add(id);
  return id;
}

// Mirrors @astrojs/markdown-remark's own heading-text collection, so the two
// slugifiers are fed byte-identical input.
function headingText(heading) {
  let text = '';
  const walk = (node, parent) => {
    if (node.type !== 'element' && parent !== null && RAW_NODE_TYPES.has(node.type)) {
      if (!(node.type === 'raw' && /^\n?<.*>\n?$/.test(node.value))) {
        text += CODE_TAG_NAMES.has(parent.tagName)
          ? node.value
          : node.value.replace(/\{/g, '${');
      }
    }
    if (node.children) for (const child of node.children) walk(child, node);
  };
  walk(heading, null);
  return text;
}

function rehypeMkdocsAnchors() {
  return (tree, file) => {
    const source = (file?.history?.[0] ?? '').replace(/\\/g, '/');
    if (!source.includes('/src/content/internal/')) return;

    const slugger = new Slugger();
    const mkdocsUsed = new Set();
    const walk = (node) => {
      if (node.type === 'element' && /^h[1-6]$/.test(node.tagName)) {
        const text = headingText(node);
        node.properties = node.properties || {};
        if (typeof node.properties.id !== 'string') {
          const slug = slugger.slug(text);
          node.properties.id = slug.endsWith('-') ? slug.slice(0, -1) : slug;
        }
        const alias = uniqueMkdocsSlug(mkdocsSlug(text), mkdocsUsed);
        if (alias !== node.properties.id) {
          node.children.unshift({
            type: 'element',
            tagName: 'span',
            properties: { id: alias, className: ['anchor-alias'] },
            children: [],
          });
        }
        return; // headings do not nest
      }
      if (node.children) for (const child of node.children) walk(child);
    };
    walk(tree);
  };
}

/**
 * The drop cap, as the main site sets it: the opening letter of a sheet
 * floated three lines deep in EB Garamond.
 *
 * The letter is split out of the paragraph's first text node and wrapped
 * in a `<span class="cap">` rather than left to `::first-letter`. That
 * keeps it real text — selectable, searchable, and read aloud as part of
 * the word it opens — and it is the only way to give it a different family
 * and weight that renders the same across engines.
 *
 * Only the first top-level paragraph of the document takes one, and only
 * if it is long enough to have three lines for the letter to sit in.
 * Short openers — an image caption, a one-line note, a lede that is really
 * a subtitle — are left alone, because a cap floated into a two-line
 * paragraph pushes the text into a column beside it.
 */
const CAP_MIN_CHARS = 80;

function rehypeDropCap() {
  return (tree) => {
    const paragraph = tree.children.find(
      (n) => n.type === 'element' && n.tagName === 'p' && textLength(n) >= CAP_MIN_CHARS,
    );
    if (!paragraph) return;

    // The first non-empty text node, wherever it sits — the paragraph may
    // legitimately open with a <strong> or an <a>, and the cap belongs to
    // the first *letter* rather than to the first direct child.
    const lead = firstText(paragraph);
    if (!lead) return;
    const trimmed = lead.value.trimStart();
    const letter = trimmed[0];
    // Punctuation and quotes make poor caps: floated at 72px an opening
    // quote reads as a stray mark rather than as a letter.
    if (!letter || !/[A-Za-z0-9]/.test(letter)) return;

    lead.value = trimmed.slice(1);
    paragraph.children.unshift({
      type: 'element',
      tagName: 'span',
      properties: { className: ['cap'] },
      children: [{ type: 'text', value: letter }],
    });
  };

  function textLength(node) {
    if (node.type === 'text') return node.value.trim().length;
    if (!node.children) return 0;
    return node.children.reduce((n, c) => n + textLength(c), 0);
  }

  function firstText(node) {
    if (!node.children) return null;
    for (const child of node.children) {
      if (child.type === 'text' && child.value.trim()) return child;
      if (child.type === 'element') {
        const found = firstText(child);
        if (found) return found;
      }
    }
    return null;
  }
}

// Project page: https://daemon-404.github.io/daemon-sec-cheatsheet
export default defineConfig({
  site: 'https://daemon-404.github.io',
  base: BASE,
  trailingSlash: 'ignore',
  integrations: [mdx(), sitemap()],
  markdown: {
    rehypePlugins: [rehypeBaseLinks, rehypeMkdocsAnchors, rehypeDropCap],
    shikiConfig: {
      // One theme, not two. Code blocks are dark plates in both modes (see
      // prose.css) — a listing that turns cream in light mode stops reading
      // as terminal output — so there is no second palette to flip to.
      theme: 'rose-pine-moon',
      wrap: false,
    },
  },
});
