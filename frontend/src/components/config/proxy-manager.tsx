import { useCallback, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Copy, Eraser, FileUp, Filter, Globe2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/useToast";
import { copyToClipboard } from "@/lib/format";

interface Props {
  value: string;
  onChange: (next: string) => void;
}

const SCHEME_RE = /^(?:https?|socks5?):\/\//i;

/** Normalize one proxy entry: add http:// if scheme is missing, return null when invalid. */
function normalizeOne(raw: string): string | null {
  const trimmed = raw.trim();
  if (!trimmed || trimmed.startsWith("#")) return null;
  // Allow comma-separated entries mixed in a single line
  const withScheme = SCHEME_RE.test(trimmed) ? trimmed : `http://${trimmed}`;
  // Minimal sanity check: needs a host after scheme
  try {
    const u = new URL(withScheme);
    if (!u.host) return null;
    return withScheme;
  } catch {
    return null;
  }
}

function parseProxies(text: string): string[] {
  return text
    .split(/[\n,]+/)
    .map((line) => normalizeOne(line))
    .filter((v): v is string => Boolean(v));
}

export function ProxyManager({ value, onChange }: Props) {
  const { t } = useTranslation();
  const toast = useToast();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [working, setWorking] = useState(false);

  const proxies = useMemo(() => parseProxies(value), [value]);
  const duplicates = proxies.length - new Set(proxies).size;

  const replaceValue = useCallback(
    (list: string[]) => {
      onChange(list.join("\n"));
    },
    [onChange],
  );

  const handleImportFile = () => fileInputRef.current?.click();

  const onFileChosen = async (file: File) => {
    setWorking(true);
    try {
      const text = await file.text();
      const parsed = parseProxies(text);
      if (parsed.length === 0) {
        toast.warning(t("config.credentials.proxyImportEmpty"));
        return;
      }
      // Merge with existing, dedup, preserve original order (existing first)
      const seen = new Set(proxies);
      const merged = [...proxies];
      for (const p of parsed) {
        if (!seen.has(p)) {
          merged.push(p);
          seen.add(p);
        }
      }
      replaceValue(merged);
      toast.success(
        t("config.credentials.proxyImportSuccess", {
          added: merged.length - proxies.length,
          total: merged.length,
        }),
      );
    } catch (err) {
      toast.error(t("common.error"), (err as Error).message);
    } finally {
      setWorking(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDedup = () => {
    const unique = Array.from(new Set(proxies));
    replaceValue(unique);
    toast.success(
      t("config.credentials.proxyDedupSuccess", {
        removed: proxies.length - unique.length,
      }),
    );
  };

  const handleClear = () => {
    if (proxies.length === 0) return;
    replaceValue([]);
  };

  const handleCopy = async () => {
    if (proxies.length === 0) return;
    const ok = await copyToClipboard(proxies.join("\n"));
    if (ok) toast.success(t("common.copied"));
  };

  return (
    <div className="space-y-2 md:col-span-2">
      <div className="flex items-center justify-between gap-2">
        <Label className="flex items-center gap-2">
          <Globe2 className="h-4 w-4 text-muted-foreground" />
          {t("config.credentials.proxies")}
          <Badge variant="secondary" className="ml-1 font-mono">
            {proxies.length}
          </Badge>
          {duplicates > 0 ? (
            <Badge variant="warning" className="font-mono">
              {t("config.credentials.proxyDuplicates", { count: duplicates })}
            </Badge>
          ) : null}
        </Label>
        <div className="flex items-center gap-1">
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.list,text/plain"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void onFileChosen(file);
            }}
          />
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleImportFile}
            disabled={working}
          >
            <FileUp /> {t("config.credentials.proxyImport")}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleDedup}
            disabled={proxies.length === 0}
          >
            <Filter /> {t("config.credentials.proxyDedup")}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            disabled={proxies.length === 0}
          >
            <Copy /> {t("common.copy")}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="text-destructive hover:text-destructive"
            onClick={handleClear}
            disabled={proxies.length === 0}
          >
            <Eraser /> {t("config.credentials.proxyClear")}
          </Button>
        </div>
      </div>
      <Textarea
        rows={6}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={"http://127.0.0.1:7890\nuser:pass@proxy.example.com:3128"}
        className="mono text-xs"
        spellCheck={false}
      />
      <p className="text-xs text-muted-foreground">
        {t("config.credentials.proxiesHint")}
      </p>
    </div>
  );
}
