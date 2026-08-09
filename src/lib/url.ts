// Base-aware URL helper. On the project page the site is served under
// /daemon-sec/, so every internal link must carry that prefix.
const BASE = import.meta.env.BASE_URL; // e.g. "/daemon-sec/"

export function url(path = ''): string {
  const base = BASE.replace(/\/$/, '');
  const p = String(path).replace(/^\//, '');
  return p ? `${base}/${p}` : `${base}/`;
}
