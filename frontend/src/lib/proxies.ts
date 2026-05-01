const SCHEME_RE = /^(?:https?|socks5?):\/\//i;

/** Normalize a single proxy entry. Returns null when the value is empty or
 * can't be parsed into a valid URL. Entries without a scheme default to
 * `http://` so that libraries like requests/httpx accept them. */
export function normalizeProxy(raw: string): string | null {
  const trimmed = raw.trim();
  if (!trimmed || trimmed.startsWith("#")) return null;
  const withScheme = SCHEME_RE.test(trimmed) ? trimmed : `http://${trimmed}`;
  try {
    const u = new URL(withScheme);
    if (!u.host) return null;
    return withScheme;
  } catch {
    return null;
  }
}

/** Parse a free-form text blob (newlines and/or commas separated) into a
 * normalized list of proxies, dropping invalid entries silently. */
export function parseProxies(text: string): string[] {
  return text
    .split(/[\n,]+/)
    .map((line) => normalizeProxy(line))
    .filter((v): v is string => Boolean(v));
}

/** Normalize a proxy text blob for persistence: one proxy per line, all with
 * a scheme, duplicates removed. Returns empty string when nothing is valid. */
export function normalizeProxyBlob(text: string): string {
  const list = parseProxies(text);
  return Array.from(new Set(list)).join("\n");
}
