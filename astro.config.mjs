// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';

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
    rehypePlugins: [rehypeBaseLinks, rehypeDropCap],
    shikiConfig: {
      // One theme, not two. Code blocks are dark plates in both modes (see
      // prose.css) — a listing that turns cream in light mode stops reading
      // as terminal output — so there is no second palette to flip to.
      theme: 'rose-pine-moon',
      wrap: false,
    },
  },
});
