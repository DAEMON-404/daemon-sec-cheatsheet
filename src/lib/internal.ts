import { getCollection, type CollectionEntry } from 'astro:content';

export type Internal = CollectionEntry<'internal'>;

export async function allInternal(): Promise<Internal[]> {
  return await getCollection('internal');
}

/** Route (relative to base) for an internal entry. Index -> section root. */
export function internalHref(entry: Internal): string {
  const id = entry.id.replace(/\/index$/, '');
  return `internal/${id}`;
}

/** Pages upstream keeps at the docs root (DISCLAIMER) — in no section. */
export async function internalRootPages(): Promise<Internal[]> {
  return (await allInternal())
    .filter((e) => !e.id.includes('/'))
    .sort((a, b) => a.data.title.localeCompare(b.data.title));
}

export interface SectionGroup {
  slug: string;
  title: string;
  index?: Internal;
  items: Internal[]; // sub-pages (excludes index), alpha
  count: number; // total pages incl. index
}

/** Pages grouped by section, sections alpha, index first inside a section. */
export async function internalBySection(): Promise<SectionGroup[]> {
  const all = await allInternal();
  const map = new Map<string, Internal[]>();
  for (const p of all) {
    if (!p.id.includes('/')) continue; // root page, not a section member
    const arr = map.get(p.data.sectionSlug) ?? [];
    arr.push(p);
    map.set(p.data.sectionSlug, arr);
  }
  const groups: SectionGroup[] = [];
  for (const [slug, entries] of map) {
    const index = entries.find((e) => e.data.isIndex);
    const items = entries
      .filter((e) => !e.data.isIndex)
      .sort((a, b) => a.data.title.localeCompare(b.data.title));
    groups.push({
      slug,
      title: index?.data.section ?? entries[0].data.section,
      index,
      items,
      count: entries.length,
    });
  }
  return groups.sort((a, b) => a.title.localeCompare(b.title));
}

/** Ordered pages within a section (index first) for prev/next. */
export function sectionOrder(group: SectionGroup): Internal[] {
  return [...(group.index ? [group.index] : []), ...group.items];
}

export function prevNext(order: Internal[], current: Internal): { prev?: Internal; next?: Internal } {
  const i = order.findIndex((p) => p.id === current.id);
  return {
    prev: i > 0 ? order[i - 1] : undefined,
    next: i >= 0 && i < order.length - 1 ? order[i + 1] : undefined,
  };
}
