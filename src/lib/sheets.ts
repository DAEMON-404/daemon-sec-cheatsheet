import { getCollection, type CollectionEntry } from 'astro:content';
import { CATEGORIES } from './taxonomy';

export type Sheet = CollectionEntry<'sheets'>;

export async function allSheets(): Promise<Sheet[]> {
  const sheets = await getCollection('sheets', ({ data }) => data.draft !== true);
  return sheets.sort((a, b) => a.data.title.localeCompare(b.data.title));
}

export function sheetHref(entry: Sheet): string {
  return `sheets/${entry.id}`;
}

/** Sheets grouped by category, in taxonomy order. */
export async function sheetsByCategory(): Promise<{ slug: string; items: Sheet[] }[]> {
  const sheets = await allSheets();
  return CATEGORIES.map((c) => ({
    slug: c.slug,
    items: sheets.filter((s) => s.data.category === c.slug),
  }));
}

export async function categoryCounts(): Promise<Record<string, number>> {
  const sheets = await allSheets();
  const counts: Record<string, number> = {};
  for (const s of sheets) counts[s.data.category] = (counts[s.data.category] ?? 0) + 1;
  return counts;
}

/** Previous / next sheet within the same category. */
export function prevNext(items: Sheet[], current: Sheet): { prev?: Sheet; next?: Sheet } {
  const i = items.findIndex((s) => s.id === current.id);
  return { prev: i > 0 ? items[i - 1] : undefined, next: i >= 0 && i < items.length - 1 ? items[i + 1] : undefined };
}

/** Distinct tags with usage counts, most-used first. */
export async function allTags(): Promise<{ tag: string; count: number }[]> {
  const sheets = await allSheets();
  const map = new Map<string, number>();
  for (const s of sheets) for (const t of s.data.tags) map.set(t, (map.get(t) ?? 0) + 1);
  return [...map.entries()].map(([tag, count]) => ({ tag, count })).sort((a, b) => b.count - a.count || a.tag.localeCompare(b.tag));
}

export async function allTools(): Promise<{ tool: string; count: number }[]> {
  const sheets = await allSheets();
  const map = new Map<string, number>();
  for (const s of sheets) for (const t of s.data.tools) map.set(t, (map.get(t) ?? 0) + 1);
  return [...map.entries()].map(([tool, count]) => ({ tool, count })).sort((a, b) => b.count - a.count || a.tool.localeCompare(b.tool));
}

export function tagSlug(tag: string): string {
  return tag.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}
