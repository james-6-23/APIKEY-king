import type { ApiKey, KeyType } from "@/types/api";

export const KEY_TYPES: KeyType[] = ["modelscope", "siliconflow", "deepseek"];

export const KEY_TYPE_LABEL: Record<KeyType, string> = {
  modelscope: "ModelScope",
  siliconflow: "SiliconFlow",
  deepseek: "DeepSeek",
};

export type KeyBadgeVariant = "modelscope" | "siliconflow" | "deepseek" | "outline";

export const KEY_TYPE_BADGE: Record<string, KeyBadgeVariant> = {
  modelscope: "modelscope",
  siliconflow: "siliconflow",
  deepseek: "deepseek",
};

export const KEY_TYPE_COLOR: Record<KeyType, string> = {
  modelscope: "var(--color-brand-modelscope)",
  siliconflow: "var(--color-brand-siliconflow)",
  deepseek: "var(--color-brand-deepseek)",
};

/** Parse a balance string (e.g. "¥12.34" / "12.34") to a number, or NaN. */
export function parseBalance(raw: string | undefined): number {
  if (!raw) return NaN;
  const m = raw.match(/-?\d+(?:\.\d+)?/);
  return m ? Number(m[0]) : NaN;
}

/** Count keys by type. */
export function countByType(keys: ApiKey[]): Record<KeyType, number> {
  const out: Record<KeyType, number> = { modelscope: 0, siliconflow: 0, deepseek: 0 };
  for (const k of keys) {
    if (k.type && (k.type in out)) {
      out[k.type as KeyType] += 1;
    }
  }
  return out;
}

/** Download a blob as a file. */
function download(filename: string, mime: string, content: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function exportKeysAsTxt(keys: ApiKey[], basename = "api-keys") {
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  download(`${basename}-${stamp}.txt`, "text/plain;charset=utf-8", keys.map((k) => k.key).join("\n"));
}

export function exportKeysAsCsv(keys: ApiKey[], basename = "api-keys") {
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const header = ["type", "key", "balance", "status", "source", "url", "found_at"];
  const esc = (v: unknown) => {
    const s = v == null ? "" : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const rows = keys.map((k) =>
    [
      k.type ?? "",
      k.key ?? "",
      k.balance ?? "",
      k.validation_status ?? "",
      k.source ?? "",
      k.url ?? "",
      k.found_at ?? "",
    ].map(esc).join(","),
  );
  download(`${basename}-${stamp}.csv`, "text/csv;charset=utf-8", [header.join(","), ...rows].join("\n"));
}

export type SortKey = "found_at" | "type" | "balance" | "source";
export type SortDir = "asc" | "desc";

export function sortKeys(list: ApiKey[], by: SortKey, dir: SortDir): ApiKey[] {
  const mul = dir === "asc" ? 1 : -1;
  const out = [...list];
  out.sort((a, b) => {
    let av: number | string = "";
    let bv: number | string = "";
    switch (by) {
      case "found_at":
        av = a.found_at ?? "";
        bv = b.found_at ?? "";
        break;
      case "type":
        av = a.type ?? "";
        bv = b.type ?? "";
        break;
      case "source":
        av = a.source ?? "";
        bv = b.source ?? "";
        break;
      case "balance": {
        const na = parseBalance(a.balance);
        const nb = parseBalance(b.balance);
        // push NaN to the end regardless of direction
        if (Number.isNaN(na) && Number.isNaN(nb)) return 0;
        if (Number.isNaN(na)) return 1;
        if (Number.isNaN(nb)) return -1;
        return (na - nb) * mul;
      }
    }
    return String(av).localeCompare(String(bv)) * mul;
  });
  return out;
}

/** Filter by recent-N-days on `found_at`. `days<=0` means no filter. */
export function filterByDays(list: ApiKey[], days: number): ApiKey[] {
  if (!days || days <= 0) return list;
  const threshold = Date.now() - days * 24 * 3600 * 1000;
  return list.filter((k) => {
    if (!k.found_at) return true;
    const t = new Date(k.found_at).getTime();
    return Number.isFinite(t) ? t >= threshold : true;
  });
}
