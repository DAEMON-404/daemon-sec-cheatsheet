import assert from 'node:assert/strict';
import test from 'node:test';
import { Window } from 'happy-dom';

test('mobile navigation follows accessible open and close state transitions', async () => {
  const window = new Window({ url: 'https://example.test/internal' });
  globalThis.window = window;
  globalThis.document = window.document;
  globalThis.localStorage = window.localStorage;

  document.body.innerHTML = `
    <header class="site-header">
      <button
        type="button"
        data-mobile-nav-toggle
        aria-controls="mobile-primary-nav"
        aria-expanded="false"
      >Menu</button>
      <nav id="mobile-primary-nav" data-mobile-nav hidden>
        <a href="/payloads">Payloads</a>
        <a href="/internal" aria-current="page">Internal</a>
      </nav>
    </header>
  `;

  await import('../src/scripts/app.ts');

  const trigger = document.querySelector('[data-mobile-nav-toggle]');
  const menu = document.querySelector('[data-mobile-nav]');
  trigger.click();

  assert.equal(trigger.getAttribute('aria-expanded'), 'true');
  assert.equal(menu.hidden, false);

  menu.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));

  assert.equal(trigger.getAttribute('aria-expanded'), 'false');
  assert.equal(menu.hidden, true);
  assert.equal(document.activeElement, trigger);

  trigger.click();
  menu.querySelector('a[aria-current="page"]').click();

  assert.equal(trigger.getAttribute('aria-expanded'), 'false');
  assert.equal(menu.hidden, true);
});
