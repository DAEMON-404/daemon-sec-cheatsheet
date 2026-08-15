import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { Window } from 'happy-dom';

test('the homepage features both mirrored references', async () => {
  const html = await readFile(new URL('../dist/index.html', import.meta.url), 'utf8');
  const window = new Window();
  window.document.write(html);

  const bands = [...window.document.querySelectorAll('a.cta-band')];
  const internal = bands.find((band) => band.getAttribute('href')?.endsWith('/internal'));

  assert.equal(bands.length, 2);
  assert.ok(internal, 'InternalAllTheThings feature band is missing');
  assert.match(internal.textContent, /03\s+\^:\s+Full mirror · credit upstream/i);
  assert.match(internal.textContent, /InternalAllTheThings/i);
  assert.match(internal.textContent, /9-section, 175-page/i);
  assert.match(internal.textContent, /Browse internal/i);
});
