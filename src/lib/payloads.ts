import { getCollection, type CollectionEntry } from 'astro:content';

export type Payload = CollectionEntry<'payloads'>;

export async function allPayloads(): Promise<Payload[]> {
  return await getCollection('payloads');
}

/** Route (relative to base) for a payload entry. README -> topic root. */
export function payloadHref(entry: Payload): string {
  const id = entry.id.replace(/\/index$/, '');
  return `payloads/${id}`;
}

export interface TopicGroup {
  slug: string;
  title: string;
  readme?: Payload;
  items: Payload[]; // sub-pages (excludes readme), alpha
  count: number; // total pages incl. readme
}

/** Payloads grouped by topic, topics alpha, readme first inside a topic. */
export async function payloadsByTopic(): Promise<TopicGroup[]> {
  const all = await allPayloads();
  const map = new Map<string, Payload[]>();
  for (const p of all) {
    const arr = map.get(p.data.topicSlug) ?? [];
    arr.push(p);
    map.set(p.data.topicSlug, arr);
  }
  const groups: TopicGroup[] = [];
  for (const [slug, entries] of map) {
    const readme = entries.find((e) => e.data.isReadme);
    const items = entries
      .filter((e) => !e.data.isReadme)
      .sort((a, b) => a.data.title.localeCompare(b.data.title));
    groups.push({
      slug,
      title: readme?.data.topic ?? entries[0].data.topic,
      readme,
      items,
      count: entries.length,
    });
  }
  return groups.sort((a, b) => a.title.localeCompare(b.title));
}

/** Ordered pages within a topic (readme first) for prev/next. */
export function topicOrder(group: TopicGroup): Payload[] {
  return [...(group.readme ? [group.readme] : []), ...group.items];
}

export function prevNext(order: Payload[], current: Payload): { prev?: Payload; next?: Payload } {
  const i = order.findIndex((p) => p.id === current.id);
  return {
    prev: i > 0 ? order[i - 1] : undefined,
    next: i >= 0 && i < order.length - 1 ? order[i + 1] : undefined,
  };
}
