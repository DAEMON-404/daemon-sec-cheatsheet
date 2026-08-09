// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';

const BASE = '/daemon-sec-vault';

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

// Project page: https://daemon-404.github.io/daemon-sec-vault
export default defineConfig({
  site: 'https://daemon-404.github.io',
  base: BASE,
  trailingSlash: 'ignore',
  integrations: [mdx(), sitemap()],
  markdown: {
    rehypePlugins: [rehypeBaseLinks],
    shikiConfig: {
      // Dual theme -> CSS variables we flip via [data-theme]. defaultColor:false
      // means Shiki writes both palettes as --shiki-light / --shiki-dark.
      themes: { light: 'rose-pine-dawn', dark: 'rose-pine-moon' },
      defaultColor: false,
      wrap: false,
    },
  },
});
