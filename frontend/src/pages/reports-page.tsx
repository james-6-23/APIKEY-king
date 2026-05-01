import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Copy, Eye, Loader2, RefreshCw, Trash2 } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/useToast";
import {
  copyToClipboard,
  formatDateTime,
  formatDuration,
  formatNumber,
} from "@/lib/format";
import type {
  ReportKeysResponse,
  ReportsResponse,
  ScanReport,
} from "@/types/api";

export function ReportsPage() {
  const { t } = useTranslation();
  const toast = useToast();
  const [reports, setReports] = useState<ScanReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [toDelete, setToDelete] = useState<ScanReport | null>(null);
  const [keysReport, setKeysReport] = useState<ScanReport | null>(null);
  const [keysData, setKeysData] = useState<string[]>([]);
  const [keysLoading, setKeysLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<ReportsResponse>("/api/reports", {
        query: { limit: 50 },
      });
      setReports(res.reports ?? []);
    } catch (err) {
      toast.error(t("common.error"), (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const openKeys = async (report: ScanReport) => {
    setKeysReport(report);
    setKeysData([]);
    setKeysLoading(true);
    try {
      const res = await api.get<ReportKeysResponse>(`/api/reports/${report.id}/keys`);
      setKeysData(res.keys ?? []);
    } catch (err) {
      toast.error(t("common.error"), (err as Error).message);
    } finally {
      setKeysLoading(false);
    }
  };

  const copyReportKeys = async (report: ScanReport) => {
    try {
      const res = await api.get<ReportKeysResponse>(`/api/reports/${report.id}/keys`);
      if (!res.keys?.length) {
        toast.info(t("reports.noKeys"));
        return;
      }
      const ok = await copyToClipboard(res.keys.join("\n"));
      if (ok) toast.success(t("common.copied"));
    } catch (err) {
      toast.error(t("common.error"), (err as Error).message);
    }
  };

  const performDelete = async () => {
    if (!toDelete) return;
    try {
      await api.delete(`/api/reports/${toDelete.id}`);
      toast.success(t("reports.deleteSuccess"));
      setToDelete(null);
      await load();
    } catch (err) {
      toast.error(t("common.error"), (err as Error).message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t("reports.title")}</h1>
          <p className="text-sm text-muted-foreground">{t("reports.subtitle")}</p>
        </div>
        <Button variant="ghost" size="icon" onClick={() => void load()} aria-label="refresh">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
        </Button>
      </div>

      {reports.length === 0 && !loading ? (
        <Card>
          <CardContent className="py-16 text-center text-muted-foreground">
            {t("reports.empty")}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {reports.map((r) => (
            <ReportCard
              key={r.id}
              report={r}
              onView={() => void openKeys(r)}
              onCopy={() => void copyReportKeys(r)}
              onDelete={() => setToDelete(r)}
            />
          ))}
        </div>
      )}

      <Dialog open={Boolean(toDelete)} onOpenChange={(open) => !open && setToDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("reports.deleteConfirmTitle")}</DialogTitle>
            <DialogDescription>{t("reports.deleteConfirmDescription")}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setToDelete(null)}>
              {t("common.cancel")}
            </Button>
            <Button variant="destructive" onClick={performDelete}>
              {t("common.delete")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(keysReport)} onOpenChange={(open) => !open && setKeysReport(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {t("reports.keysDialogTitle", { id: keysReport?.id ?? "" })}
            </DialogTitle>
            <DialogDescription>
              {formatDateTime(keysReport?.start_time)} → {formatDateTime(keysReport?.end_time)}
            </DialogDescription>
          </DialogHeader>
          {keysLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : keysData.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">{t("reports.noKeys")}</p>
          ) : (
            <ScrollArea className="h-[360px] rounded-md border">
              <pre className="p-4 font-mono text-xs">{keysData.join("\n")}</pre>
            </ScrollArea>
          )}
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={async () => {
                if (keysData.length === 0) return;
                const ok = await copyToClipboard(keysData.join("\n"));
                if (ok) toast.success(t("common.copied"));
              }}
              disabled={keysData.length === 0}
            >
              <Copy /> {t("reports.copyKeys")}
            </Button>
            <Button variant="ghost" onClick={() => setKeysReport(null)}>
              {t("common.close")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function ReportCard({
  report,
  onView,
  onCopy,
  onDelete,
}: {
  report: ScanReport;
  onView: () => void;
  onCopy: () => void;
  onDelete: () => void;
}) {
  const { t } = useTranslation();
  const rate =
    report.total_keys > 0
      ? Math.round((report.valid_keys / report.total_keys) * 100)
      : 0;

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="space-y-2">
        <div className="flex items-center justify-between">
          <CardTitle className="mono text-base">#{report.id}</CardTitle>
          <Badge variant="outline" className="uppercase">
            {report.scan_mode}
          </Badge>
        </div>
        <CardDescription>
          {formatDateTime(report.start_time)}
          <span className="mx-1">→</span>
          {formatDateTime(report.end_time)}
          <span className="ml-2 inline-block rounded bg-muted px-1.5 py-0.5 text-xs">
            {formatDuration(report.duration_seconds)}
          </span>
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1 space-y-4">
        <div className="grid grid-cols-3 gap-3 text-center">
          <Stat label={t("reports.totalFiles")} value={report.total_files} />
          <Stat label={t("reports.totalKeys")} value={report.total_keys} />
          <Stat label={t("reports.validKeys")} value={report.valid_keys} highlight />
        </div>
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{t("reports.successRate")}</span>
            <span className="tabular-nums">{rate}%</span>
          </div>
          <Progress value={rate} />
        </div>
      </CardContent>
      <CardFooter className="gap-2">
        <Button variant="secondary" size="sm" onClick={onView}>
          <Eye /> {t("reports.viewKeys")}
        </Button>
        <Button variant="ghost" size="sm" onClick={onCopy}>
          <Copy /> {t("reports.copyKeys")}
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="ml-auto text-destructive hover:text-destructive"
          onClick={onDelete}
          aria-label={t("common.delete")}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  );
}

function Stat({
  label,
  value,
  highlight,
}: {
  label: string;
  value: number;
  highlight?: boolean;
}) {
  return (
    <div className="rounded-md border bg-muted/30 p-2">
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div
        className={
          "text-lg font-semibold tabular-nums " +
          (highlight ? "text-[color:var(--color-success)]" : "")
        }
      >
        {formatNumber(value)}
      </div>
    </div>
  );
}
