// Single source of truth for the 12 site domains.
// `accent` maps to a Rose Pine palette token used for the neon edge-glow.
// `tag` is the monospace module label shown on cards ( [AD], [ENUM], ... ).

export type CategoryDef = {
  slug: string;
  title: string;
  tag: string;
  accent: 'iris' | 'foam' | 'love' | 'gold' | 'rose' | 'pine';
  blurb: string;
};

export const CATEGORIES: CategoryDef[] = [
  { slug: 'active-directory',     title: 'Active Directory',     tag: 'AD',    accent: 'iris', blurb: 'Kerberos, ADCS, delegation, and domain takeover paths.' },
  { slug: 'enumeration',          title: 'Enumeration',          tag: 'ENUM',  accent: 'foam', blurb: 'Port, service, web, and host discovery — mapping the attack surface.' },
  { slug: 'exploitation',         title: 'Exploitation',         tag: 'PWN',   accent: 'love', blurb: 'Gaining a foothold: injection, upload, and shell delivery.' },
  { slug: 'privilege-escalation', title: 'Privilege Escalation', tag: 'PRIV',  accent: 'gold', blurb: 'From user to root/SYSTEM on Linux and Windows.' },
  { slug: 'password-attacks',     title: 'Password Attacks',     tag: 'CRED',  accent: 'rose', blurb: 'Cracking, spraying, and credential recovery.' },
  { slug: 'web',                  title: 'Web',                  tag: 'WEB',   accent: 'foam', blurb: 'XSS, injection, and web application testing.' },
  { slug: 'tunneling-pivoting',   title: 'Tunneling & Pivoting', tag: 'PIVOT', accent: 'pine', blurb: 'Moving through segmented networks and double pivots.' },
  { slug: 'cryptography',         title: 'Cryptography',         tag: 'CRYPTO',accent: 'iris', blurb: 'Hashing, encryption, GPG, and key handling.' },
  { slug: 'dfir',                 title: 'DFIR',                 tag: 'DFIR',  accent: 'gold', blurb: 'Forensics, memory, and registry analysis.' },
  { slug: 'tools',                title: 'Tools',                tag: 'TOOL',  accent: 'foam', blurb: 'General-purpose offensive tooling and multiplexers.' },
  { slug: 'linux-it',             title: 'Linux & IT',           tag: 'NIX',   accent: 'foam', blurb: 'Shell, filesystem, and everyday IT fundamentals.' },
  { slug: 'git-workflow',         title: 'Git & Workflow',       tag: 'GIT',   accent: 'rose', blurb: 'Version control and operator workflow.' },
];

export const CATEGORY_BY_SLUG: Record<string, CategoryDef> =
  Object.fromEntries(CATEGORIES.map((c) => [c.slug, c]));

export function categoryOf(slug: string): CategoryDef {
  return CATEGORY_BY_SLUG[slug] ?? {
    slug, title: slug, tag: slug.slice(0, 5).toUpperCase(), accent: 'foam',
    blurb: '',
  };
}
