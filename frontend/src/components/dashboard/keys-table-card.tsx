import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Copy,
  Loader2,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";
import { copyToClipboard, formatDateTime, truncate } from "@/lib/format";
import { useToast } from "@/hooks/useToast";
import type { ApiKey, ApiKeysResponse, KeyType } from "@/types/api";
import { cn } from "@/lib/cn";

const PAGE_SIZE = 20;
const TYPES: { value: KeyType | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "modelscope", label: "ModelScope" },
  { value: "siliconflow", label: "SiliconFlow" },
  { value: "deepseek", label: "DeepSeek" },
];

const TYPE_VARIANT: Record<string, "modelscope" | "siliconflow" | "deepseek" | "outline"> = {
  modelscope: "modelscope",
  siliconflow: "siliconflow",
  deepseek: "deepseek",
};

export function KeysTableCard() {
  const { t } = useTranslation();
  const toast = useToast();
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [keyType, setKeyType] = useState<string>("all");
  const [page, setPage] = useState(1);
  const [clearOpen, setClearOpen] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<ApiKeysResponse>("/api/keys", {
        query: {
          key_type: keyType === "all" ? undefined : keyType,
          search: search || undefined,
        },
      });
      setKeys(res.keys ?? []);
      setSelected(new Set());
      setPage(1);
    } catch (err) {
      toast.error(t("common.error"), (err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [keyType, search, toast, t]);

  useEffect(() => {
    void load();
    const id = window.setInterval(() => void load(), 30000);
    return () => window.clearInterval(id);
  }, [load]);

  const totalPages = Math.max(1, Math.ceil(keys.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const rows = useMemo(
    () => keys.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE),
    [keys, currentPage],
  );

  const handleCopy = async (text: string) => {
    const ok = await copyToClipboard(text);
    if (ok) toast.success(t("common.copied"));
    else toast.error(t("common.failed"));
  };

  const handleCopyVisible = async () => {
    if (rows.length === 0) return;
    const ok = await copyToClipboard(rows.map((r) => r.key).join("\n"));
    if (ok) toast.success(t("dashboard.keys.copiedCount", { count: rows.length }));
  };

  const handleCopySelected = async () => {
    if (selected.size === 0) return;
    const list = keys.filter((k) => selected.has(k.key)).map((k) => k.key);
    const ok = await copyToClipboard(list.join("\n"));
    if (ok) toast.success(t("dashboard.keys.copiedCount", { count: list.length }));
  };

  const handleClear = async () => {
    try {
      await api.delete("/api/keys/clear");
      toast.success(t("dashboard.keys.cleared"));
      setClearOpen(false);
      await load();
    } catch (err) {
      toast.error(t("common.error"), (err as Error).message);
    }
  };

  const toggleSelect = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const toggleSelectAll = () => {
    setSelected((prev) => {
      if (prev.size === rows.length) return new Set();
      return new Set(rows.map((r) => r.key));
    });
  };

  return (
    <Card>
      <CardHeader className="space-y-4">
        <div className="flex items-center justify-between gap-2">
          <div>
            <CardTitle>{t("dashboard.keys.title")}</CardTitle>
            <CardDescription>{t("dashboard.keys.description")}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={() => void load()} aria-label="refresh">
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-destructive hover:text-destructive"
              onClick={() => setClearOpen(true)}
              disabled={keys.length === 0}
            >
              <Trash2 className="h-4 w-4" />
              {t("dashboard.keys.clearAll")}
            </Button>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative min-w-[220px] flex-1">
            <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t("dashboard.keys.search")}
              className="pl-8"
            />
          </div>
          <Select value={keyType} onValueChange={setKeyType}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder={t("dashboard.keys.filterType")} />
            </SelectTrigger>
            <SelectContent>
              {TYPES.map((tp) => (
                <SelectItem key={tp.value} value={tp.value}>
                  {tp.value === "all" ? t("common.all") : tp.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="secondary" size="sm" onClick={handleCopyVisible} disabled={rows.length === 0}>
            <Copy /> {t("dashboard.keys.copyVisible")}
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleCopySelected}
            disabled={selected.size === 0}
          >
            <Copy /> {t("dashboard.keys.copySelected")}
            {selected.size > 0 ? ` (${selected.size})` : ""}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="px-0 pb-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-10">
                <input
                  type="checkbox"
                  aria-label="select all"
                  checked={rows.length > 0 && selected.size === rows.length}
                  onChange={toggleSelectAll}
                />
              </TableHead>
              <TableHead className="w-[120px]">{t("dashboard.keys.columnType")}</TableHead>
              <TableHead>{t("dashboard.keys.columnKey")}</TableHead>
              <TableHead className="w-[110px]">{t("dashboard.keys.columnBalance")}</TableHead>
              <TableHead className="w-[260px]">{t("dashboard.keys.columnSource")}</TableHead>
              <TableHead className="w-[180px]">{t("dashboard.keys.columnFoundAt")}</TableHead>
              <TableHead className="w-[80px]">{t("dashboard.keys.columnActions")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.length === 0 && !loading ? (
              <TableRow>
                <TableCell colSpan={7} className="h-32 text-center text-muted-foreground">
                  {t("dashboard.keys.empty")}
                </TableCell>
              </TableRow>
            ) : (
              rows.map((row) => (
                <TableRow key={row.key} data-state={selected.has(row.key) ? "selected" : undefined}>
                  <TableCell>
                    <input
                      type="checkbox"
                      aria-label="select row"
                      checked={selected.has(row.key)}
                      onChange={() => toggleSelect(row.key)}
                    />
                  </TableCell>
                  <TableCell>
                    <Badge variant={TYPE_VARIANT[row.type] ?? "outline"} className="uppercase">
                      {row.type}
                    </Badge>
                  </TableCell>
                  <TableCell className="mono text-xs">
                    <span className="break-all">{truncate(row.key, 10)}</span>
                  </TableCell>
                  <TableCell className={cn("mono text-xs", row.balance ? "text-foreground" : "text-muted-foreground")}>
                    {row.balance ?? "—"}
                  </TableCell>
                  <TableCell className="text-xs">
                    {row.url ? (
                      <a
                        href={row.url}
                        target="_blank"
                        rel="noreferrer noopener"
                        className="text-primary hover:underline"
                      >
                        {row.source ?? row.url}
                      </a>
                    ) : (
                      <span className="text-muted-foreground">{row.source ?? "—"}</span>
                    )}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {formatDateTime(row.found_at)}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleCopy(row.key)}
                      aria-label={t("common.copy")}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>

        <div className="flex items-center justify-between border-t px-4 py-3 text-sm">
          <span className="text-muted-foreground">
            {t("dashboard.keys.pageInfo", {
              page: currentPage,
              total: totalPages,
              count: keys.length,
            })}
          </span>
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              ‹
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              ›
            </Button>
          </div>
        </div>
      </CardContent>

      <Dialog open={clearOpen} onOpenChange={setClearOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("dashboard.keys.clearAll")}</DialogTitle>
            <DialogDescription>{t("dashboard.keys.confirmClear")}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setClearOpen(false)}>
              {t("common.cancel")}
            </Button>
            <Button variant="destructive" onClick={handleClear}>
              {t("common.confirm")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
