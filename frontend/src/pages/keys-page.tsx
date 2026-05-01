import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ArrowDownUp,
  Copy,
  Download,
  ExternalLink,
  Eye,
  FileText,
  Filter,
  Loader2,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RTooltip } from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tabs,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/useToast";
import {
  copyToClipboard,
  formatDateTime,
  formatNumber,
  truncate,
} from "@/lib/format";
import { cn } from "@/lib/cn";
import {
  KEY_TYPES,
  KEY_TYPE_BADGE,
  KEY_TYPE_COLOR,
  KEY_TYPE_LABEL,
  countByType,
  exportKeysAsCsv,
  exportKeysAsTxt,
  filterByDays,
  parseBalance,
  sortKeys,
  type SortDir,
  type SortKey,
} from "@/lib/keys";
import type { ApiKey, ApiKeysResponse, KeyType } from "@/types/api";

const PAGE_SIZES = [20, 50, 100, 200];

export function KeysPage() {
  const { t } = useTranslation();
  const toast = useToast();
  const [all, setAll] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [activeType, setActiveType] = useState<"all" | KeyType>("all");
  const [status, setStatus] = useState<string>("all");
  const [days, setDays] = useState<number>(0);
  const [minBalance, setMinBalance] = useState<string>("");
  const [sortBy, setSortBy] = useState<SortKey>("found_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [detail, setDetail] = useState<ApiKey | null>(null);
  const [clearOpen, setClearOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<ApiKeysResponse>("/api/keys", {
        query: { search: search || undefined },
      });
      setAll(res.keys ?? []);
      setSelected(new Set());
      setPage(1);
    } catch (err) {
      toast.error(t("common.error"), (err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [search, toast, t]);

  useEffect(() => {
    void load();
  }, [load]);

  // ------------------------------------------------------------------
  // Derived data
  // ------------------------------------------------------------------

  const counts = useMemo(() => countByType(all), [all]);
  const statuses = useMemo(() => {
    const set = new Set<string>();
    for (const k of all) if (k.validation_status) set.add(k.validation_status);
    return Array.from(set).sort();
  }, [all]);

  const filtered = useMemo(() => {
    let list = all;
    if (activeType !== "all") list = list.filter((k) => k.type === activeType);
    if (status !== "all") list = list.filter((k) => k.validation_status === status);
    if (days > 0) list = filterByDays(list, days);
    if (minBalance) {
      const min = Number(minBalance);
      if (!Number.isNaN(min)) {
        list = list.filter((k) => {
          const b = parseBalance(k.balance);
          return Number.isFinite(b) && b >= min;
        });
      }
    }
    return sortKeys(list, sortBy, sortDir);
  }, [all, activeType, status, days, minBalance, sortBy, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const rows = useMemo(
    () => filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize),
    [filtered, currentPage, pageSize],
  );

  const chartData = useMemo(
    () =>
      (KEY_TYPES as KeyType[])
        .map((k) => ({ name: KEY_TYPE_LABEL[k], value: counts[k], type: k }))
        .filter((d) => d.value > 0),
    [counts],
  );

  // ------------------------------------------------------------------
  // Actions
  // ------------------------------------------------------------------

  const toggleSort = (key: SortKey) => {
    if (sortBy === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(key);
      setSortDir("desc");
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

  const toggleSelectAllOnPage = () => {
    setSelected((prev) => {
      if (rows.every((r) => prev.has(r.key))) {
        const next = new Set(prev);
        rows.forEach((r) => next.delete(r.key));
        return next;
      }
      const next = new Set(prev);
      rows.forEach((r) => next.add(r.key));
      return next;
    });
  };

  const copyKeys = async (list: ApiKey[]) => {
    if (list.length === 0) return;
    const ok = await copyToClipboard(list.map((k) => k.key).join("\n"));
    if (ok) toast.success(t("keysPage.copiedCount", { count: list.length }));
    else toast.error(t("common.failed"));
  };

  const handleClear = async () => {
    try {
      await api.delete("/api/keys/clear");
      toast.success(t("keysPage.cleared"));
      setClearOpen(false);
      await load();
    } catch (err) {
      toast.error(t("common.error"), (err as Error).message);
    }
  };

  const selectedList = all.filter((k) => selected.has(k.key));
  const hasFilters =
    activeType !== "all" || status !== "all" || days > 0 || !!minBalance || !!search;

  const resetFilters = () => {
    setActiveType("all");
    setStatus("all");
    setDays(0);
    setMinBalance("");
    setSearch("");
  };

  // ------------------------------------------------------------------
  // Render
  // ------------------------------------------------------------------

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t("keysPage.title")}</h1>
          <p className="text-sm text-muted-foreground">{t("keysPage.subtitle")}</p>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" onClick={() => void load()} aria-label="refresh">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="secondary" size="sm" disabled={filtered.length === 0}>
                <Download /> {t("keysPage.export")}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => exportKeysAsTxt(filtered)}>
                <FileText className="mr-2 h-4 w-4" />
                {t("keysPage.exportTxt", { count: filtered.length })}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => exportKeysAsCsv(filtered)}>
                <FileText className="mr-2 h-4 w-4" />
                {t("keysPage.exportCsv", { count: filtered.length })}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <Button
            variant="ghost"
            size="sm"
            className="text-destructive hover:text-destructive"
            onClick={() => setClearOpen(true)}
            disabled={all.length === 0}
          >
            <Trash2 /> {t("keysPage.clearAll")}
          </Button>
        </div>
      </div>

      {/* Summary */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card className="md:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              {t("keysPage.summaryTotal")}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-4">
            <div className="flex-1">
              <div className="text-4xl font-semibold tabular-nums">{formatNumber(all.length)}</div>
              <div className="mt-2 space-y-1 text-xs">
                {KEY_TYPES.map((k) => {
                  const n = counts[k];
                  const pct = all.length ? Math.round((n / all.length) * 100) : 0;
                  return (
                    <div key={k} className="flex items-center gap-2">
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: KEY_TYPE_COLOR[k] }}
                      />
                      <span className="w-24 text-muted-foreground">{KEY_TYPE_LABEL[k]}</span>
                      <span className="mono tabular-nums">{formatNumber(n)}</span>
                      <span className="ml-auto text-muted-foreground">{pct}%</span>
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="h-32 w-32 shrink-0">
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <RTooltip
                      contentStyle={{
                        background: "var(--color-popover)",
                        border: "1px solid var(--color-border)",
                        borderRadius: 6,
                        fontSize: 12,
                      }}
                    />
                    <Pie
                      data={chartData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius="60%"
                      outerRadius="100%"
                      paddingAngle={2}
                      stroke="none"
                    >
                      {chartData.map((d) => (
                        <Cell key={d.type} fill={KEY_TYPE_COLOR[d.type]} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              ) : null}
            </div>
          </CardContent>
        </Card>

        {KEY_TYPES.map((k) => {
          const n = counts[k];
          const pct = all.length ? Math.round((n / all.length) * 100) : 0;
          return (
            <Card key={k}>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: KEY_TYPE_COLOR[k] }}
                  />
                  {KEY_TYPE_LABEL[k]}
                </CardTitle>
                <CardDescription>{t("keysPage.summaryPerType")}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-semibold tabular-nums">{formatNumber(n)}</div>
                <div className="mt-1 text-xs text-muted-foreground">{pct}%</div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Main */}
      <Card>
        <CardHeader className="space-y-4">
          <Tabs value={activeType} onValueChange={(v) => setActiveType(v as "all" | KeyType)}>
            <TabsList>
              <TabsTrigger value="all">
                {t("common.all")}
                <Badge variant="secondary" className="ml-2 font-mono">
                  {all.length}
                </Badge>
              </TabsTrigger>
              {KEY_TYPES.map((k) => (
                <TabsTrigger key={k} value={k}>
                  {KEY_TYPE_LABEL[k]}
                  <Badge variant="secondary" className="ml-2 font-mono">
                    {counts[k]}
                  </Badge>
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>

          <div className="flex flex-wrap items-center gap-2">
            <div className="relative min-w-[240px] flex-1">
              <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={t("keysPage.searchPlaceholder")}
                className="pl-8"
              />
            </div>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder={t("keysPage.statusLabel")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("keysPage.statusAll")}</SelectItem>
                {statuses.map((s) => (
                  <SelectItem key={s} value={s}>
                    {s}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={String(days)} onValueChange={(v) => setDays(Number(v))}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder={t("keysPage.daysLabel")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0">{t("keysPage.daysAll")}</SelectItem>
                <SelectItem value="1">{t("keysPage.daysN", { n: 1 })}</SelectItem>
                <SelectItem value="7">{t("keysPage.daysN", { n: 7 })}</SelectItem>
                <SelectItem value="30">{t("keysPage.daysN", { n: 30 })}</SelectItem>
                <SelectItem value="90">{t("keysPage.daysN", { n: 90 })}</SelectItem>
              </SelectContent>
            </Select>
            <Input
              type="number"
              inputMode="decimal"
              step="0.01"
              placeholder={t("keysPage.minBalance")}
              value={minBalance}
              onChange={(e) => setMinBalance(e.target.value)}
              className="w-[140px]"
            />
            {hasFilters ? (
              <Button variant="ghost" size="sm" onClick={resetFilters}>
                <Filter /> {t("keysPage.resetFilters")}
              </Button>
            ) : null}
            <div className="ml-auto flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => copyKeys(rows)}
                disabled={rows.length === 0}
              >
                <Copy /> {t("keysPage.copyPage")}
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => copyKeys(selectedList)}
                disabled={selectedList.length === 0}
              >
                <Copy /> {t("keysPage.copySelected")}
                {selectedList.length > 0 ? ` (${selectedList.length})` : ""}
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="px-0 pb-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">
                  <input
                    type="checkbox"
                    aria-label="select all on page"
                    checked={rows.length > 0 && rows.every((r) => selected.has(r.key))}
                    onChange={toggleSelectAllOnPage}
                  />
                </TableHead>
                <SortableHead label={t("keysPage.columnType")} k="type" sortBy={sortBy} sortDir={sortDir} onClick={toggleSort} className="w-[130px]" />
                <TableHead>{t("keysPage.columnKey")}</TableHead>
                <SortableHead label={t("keysPage.columnBalance")} k="balance" sortBy={sortBy} sortDir={sortDir} onClick={toggleSort} className="w-[110px]" />
                <TableHead className="w-[120px]">{t("keysPage.columnStatus")}</TableHead>
                <SortableHead label={t("keysPage.columnSource")} k="source" sortBy={sortBy} sortDir={sortDir} onClick={toggleSort} className="w-[240px]" />
                <SortableHead label={t("keysPage.columnFoundAt")} k="found_at" sortBy={sortBy} sortDir={sortDir} onClick={toggleSort} className="w-[170px]" />
                <TableHead className="w-[110px]">{t("keysPage.columnActions")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.length === 0 && !loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="h-32 text-center text-muted-foreground">
                    {t("keysPage.empty")}
                  </TableCell>
                </TableRow>
              ) : (
                rows.map((row) => (
                  <TableRow
                    key={row.key}
                    data-state={selected.has(row.key) ? "selected" : undefined}
                  >
                    <TableCell>
                      <input
                        type="checkbox"
                        aria-label="select"
                        checked={selected.has(row.key)}
                        onChange={() => toggleSelect(row.key)}
                      />
                    </TableCell>
                    <TableCell>
                      <Badge variant={KEY_TYPE_BADGE[row.type] ?? "outline"} className="uppercase">
                        {row.type}
                      </Badge>
                    </TableCell>
                    <TableCell className="mono text-xs">
                      <span className="break-all">{truncate(row.key, 10)}</span>
                    </TableCell>
                    <TableCell
                      className={cn(
                        "mono text-xs",
                        row.balance ? "text-foreground" : "text-muted-foreground",
                      )}
                    >
                      {row.balance ?? "—"}
                    </TableCell>
                    <TableCell className="text-xs">
                      {row.validation_status ? (
                        <Badge variant={statusVariant(row.validation_status)}>
                          {row.validation_status}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
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
                      <div className="flex items-center gap-0.5">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDetail(row)}
                          aria-label={t("keysPage.detailTitle")}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={async () => {
                            const ok = await copyToClipboard(row.key);
                            if (ok) toast.success(t("common.copied"));
                          }}
                          aria-label={t("common.copy")}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        {row.url ? (
                          <Button variant="ghost" size="icon" asChild aria-label="source">
                            <a href={row.url} target="_blank" rel="noreferrer noopener">
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          </Button>
                        ) : null}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>

          <div className="flex flex-wrap items-center justify-between gap-3 border-t px-4 py-3 text-sm">
            <div className="flex items-center gap-3 text-muted-foreground">
              <span>
                {t("keysPage.pageInfo", {
                  page: currentPage,
                  total: totalPages,
                  count: filtered.length,
                })}
              </span>
              {selectedList.length > 0 ? (
                <Badge variant="outline">
                  {t("keysPage.selectedCount", { count: selectedList.length })}
                </Badge>
              ) : null}
            </div>
            <div className="flex items-center gap-2">
              <Select value={String(pageSize)} onValueChange={(v) => setPageSize(Number(v))}>
                <SelectTrigger className="h-8 w-[110px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PAGE_SIZES.map((s) => (
                    <SelectItem key={s} value={String(s)}>
                      {t("keysPage.pageSize", { n: s })}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage <= 1}
                  onClick={() => setPage(1)}
                >
                  «
                </Button>
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
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage >= totalPages}
                  onClick={() => setPage(totalPages)}
                >
                  »
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detail dialog */}
      <Dialog open={Boolean(detail)} onOpenChange={(open) => !open && setDetail(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {detail ? (
                <Badge variant={KEY_TYPE_BADGE[detail.type] ?? "outline"} className="uppercase">
                  {detail.type}
                </Badge>
              ) : null}
              {t("keysPage.detailTitle")}
            </DialogTitle>
            <DialogDescription>{t("keysPage.detailDescription")}</DialogDescription>
          </DialogHeader>
          {detail ? (
            <div className="space-y-3 text-sm">
              <DetailRow label={t("keysPage.columnKey")}>
                <ScrollArea className="max-h-32 rounded border bg-muted/30 p-2">
                  <code className="mono break-all text-xs">{detail.key}</code>
                </ScrollArea>
              </DetailRow>
              <div className="grid grid-cols-2 gap-3">
                <DetailRow label={t("keysPage.columnBalance")}>
                  <span className="mono">{detail.balance ?? "—"}</span>
                </DetailRow>
                <DetailRow label={t("keysPage.columnStatus")}>
                  {detail.validation_status ? (
                    <Badge variant={statusVariant(detail.validation_status)}>
                      {detail.validation_status}
                    </Badge>
                  ) : (
                    "—"
                  )}
                </DetailRow>
                <DetailRow label={t("keysPage.columnSource")}>
                  {detail.source ?? "—"}
                </DetailRow>
                <DetailRow label={t("keysPage.columnFoundAt")}>
                  {formatDateTime(detail.found_at)}
                </DetailRow>
              </div>
              {detail.url ? (
                <DetailRow label="URL">
                  <a
                    href={detail.url}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="break-all text-primary hover:underline"
                  >
                    {detail.url}
                  </a>
                </DetailRow>
              ) : null}
            </div>
          ) : null}
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={async () => {
                if (!detail) return;
                const ok = await copyToClipboard(detail.key);
                if (ok) toast.success(t("common.copied"));
              }}
            >
              <Copy /> {t("common.copy")}
            </Button>
            <Button variant="ghost" onClick={() => setDetail(null)}>
              {t("common.close")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={clearOpen} onOpenChange={setClearOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("keysPage.clearAll")}</DialogTitle>
            <DialogDescription>{t("keysPage.confirmClear")}</DialogDescription>
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
    </div>
  );
}

function SortableHead({
  label,
  k,
  sortBy,
  sortDir,
  onClick,
  className,
}: {
  label: string;
  k: SortKey;
  sortBy: SortKey;
  sortDir: SortDir;
  onClick: (k: SortKey) => void;
  className?: string;
}) {
  const active = sortBy === k;
  return (
    <TableHead className={className}>
      <button
        type="button"
        onClick={() => onClick(k)}
        className={cn(
          "inline-flex items-center gap-1 uppercase transition-colors hover:text-foreground",
          active ? "text-foreground" : "",
        )}
      >
        {label}
        <ArrowDownUp
          className={cn(
            "h-3 w-3 transition-transform",
            active && sortDir === "asc" && "rotate-180",
            !active && "opacity-40",
          )}
        />
      </button>
    </TableHead>
  );
}

function DetailRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
      <div>{children}</div>
    </div>
  );
}

function statusVariant(
  s: string,
): "success" | "destructive" | "warning" | "info" | "outline" {
  const low = s.toLowerCase();
  if (low.includes("valid") && !low.includes("invalid")) return "success";
  if (low.includes("invalid") || low.includes("error") || low.includes("fail")) return "destructive";
  if (low.includes("rate") || low.includes("limit")) return "warning";
  if (low.includes("info")) return "info";
  return "outline";
}
