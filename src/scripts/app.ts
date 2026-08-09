// Progressive enhancement, re-run after every (view-transition) navigation.

function applyTheme(next: 'light' | 'dark'): void {
  document.documentElement.setAttribute('data-theme', next);
  try { localStorage.setItem('theme', next); } catch {}
  document.documentElement.style.colorScheme = next;
}

function initTheme(): void {
  const toggles = document.querySelectorAll<HTMLButtonElement>('[data-theme-toggle]');
  toggles.forEach((btn) => {
    if (btn.dataset.bound) return;
    btn.dataset.bound = '1';
    btn.addEventListener('click', () => {
      const cur = document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
      const next: 'light' | 'dark' = cur === 'light' ? 'dark' : 'light';
      const root = document.documentElement;

      // Feature/consent gate: no View Transitions or reduced-motion -> flip instantly.
      const startVT = (document as unknown as {
        startViewTransition?: (cb: () => void) => { finished: Promise<void> };
      }).startViewTransition;
      const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (!startVT || reduce) { applyTheme(next); return; }

      // Origin + radius for the circular reveal: expand from the toggle's centre
      // out to the farthest viewport corner so the circle always covers the screen.
      const r = btn.getBoundingClientRect();
      const x = r.left + r.width / 2;
      const y = r.top + r.height / 2;
      const endR = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
      root.style.setProperty('--vt-x', `${x}px`);
      root.style.setProperty('--vt-y', `${y}px`);
      root.style.setProperty('--vt-r', `${endR}px`);

      root.classList.add('theme-vt');
      const t = startVT.call(document, () => applyTheme(next));
      t.finished.finally(() => root.classList.remove('theme-vt'));
    });
  });
}

function enhanceCode(): void {
  const blocks = document.querySelectorAll<HTMLPreElement>('.prose pre.astro-code:not([data-enhanced])');
  blocks.forEach((pre) => {
    pre.dataset.enhanced = '1';
    const lang = pre.getAttribute('data-language') || 'sh';

    const pane = document.createElement('div');
    pane.className = 'code-pane';
    const bar = document.createElement('div');
    bar.className = 'code-pane__bar';

    const dots = document.createElement('span');
    dots.className = 'code-pane__dots';
    dots.append(document.createElement('i'), document.createElement('i'), document.createElement('i'));
    const langEl = document.createElement('span');
    langEl.className = 'code-pane__lang';
    langEl.textContent = lang.replace(/[^a-z0-9+#-]/gi, '').slice(0, 16) || 'sh';
    bar.append(dots, langEl);

    const copy = document.createElement('button');
    copy.className = 'code-copy';
    copy.type = 'button';
    copy.textContent = 'copy';
    copy.addEventListener('click', async () => {
      const text = pre.innerText;
      try {
        await navigator.clipboard.writeText(text);
      } catch {
        const ta = document.createElement('textarea');
        ta.value = text; document.body.appendChild(ta); ta.select();
        try { document.execCommand('copy'); } catch {}
        ta.remove();
      }
      copy.textContent = 'copied'; copy.classList.add('copied');
      setTimeout(() => { copy.textContent = 'copy'; copy.classList.remove('copied'); }, 1400);
    });
    bar.appendChild(copy);

    pre.parentNode?.insertBefore(pane, pre);
    pane.appendChild(bar);
    pane.appendChild(pre);
  });
}

function wrapTables(): void {
  document.querySelectorAll<HTMLTableElement>('.prose table:not([data-wrapped])').forEach((t) => {
    t.dataset.wrapped = '1';
    const scroll = document.createElement('div');
    scroll.className = 'table-scroll';
    t.parentNode?.insertBefore(scroll, t);
    scroll.appendChild(t);
  });
}

function initTOC(): void {
  const toc = document.querySelector('.toc');
  if (!toc) return;
  const links = Array.from(toc.querySelectorAll<HTMLAnchorElement>('a[href^="#"]'));
  if (!links.length) return;
  const byId = new Map(links.map((l) => [decodeURIComponent(l.getAttribute('href')!.slice(1)), l]));
  const heads = Array.from(document.querySelectorAll<HTMLElement>('.prose h2[id], .prose h3[id]'));
  const obs = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        const id = (e.target as HTMLElement).id;
        links.forEach((l) => l.classList.remove('active'));
        byId.get(id)?.classList.add('active');
      });
    },
    { rootMargin: '-70px 0px -70% 0px', threshold: 0 }
  );
  heads.forEach((h) => obs.observe(h));
}

function init(): void {
  initTheme();
  enhanceCode();
  wrapTables();
  initTOC();
}

document.addEventListener('astro:page-load', init);
if (document.readyState !== 'loading') init();
else document.addEventListener('DOMContentLoaded', init);
