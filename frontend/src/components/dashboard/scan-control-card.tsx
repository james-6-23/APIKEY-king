import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Loader2, Pause, Play, Square, StopCircle } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { RadialProgress } from "@/components/ui/radial-progress";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/hooks/useToast";
import type { ScanAction, ScanStatusResponse } from "@/types/api";
import { cn } from "@/lib/cn";

interface Props {
  status: ScanStatusResponse | null;
}

export function ScanControlCard({ status }: Props) {
  const { t } = useTranslation();
  const toast = useToast();
  const [pending, setPending] = useState<ScanAction | null>(null);

  const running = status?.running ?? false;
  const paused = status?.paused ?? false;
  const stats = status?.stats;
  const percent = Math.min(100, Math.max(0, stats?.progress_percent ?? 0));

  const call = async (action: ScanAction) => {
    setPending(action);
    try {
      await api.post("/api/scan/control", { action });
      toast.success(t(`dashboard.scanControl.${action}Success` as const));
    } catch (err) {
      const detail = err instanceof ApiError ? err.detail ?? err.message : (err as Error).message;
      const message =
        action === "start" && /configure/i.test(detail ?? "")
          ? t("dashboard.scanControl.configMissing")
          : detail;
      toast.error(t("dashboard.scanControl.actionFailed"), message);
    } finally {
      setPending(null);
    }
  };

  const stateLabel = !running
    ? t("dashboard.scanControl.stateIdle")
    : paused
      ? t("dashboard.scanControl.statePaused")
      : t("dashboard.scanControl.stateRunning");

  const stateVariant = !running ? "secondary" : paused ? "warning" : "success";

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle>{t("dashboard.scanControl.title")}</CardTitle>
          <CardDescription>{t("dashboard.scanControl.description")}</CardDescription>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={stateVariant}>
            <span
              className={cn(
                "mr-1 inline-block h-2 w-2 rounded-full",
                running && !paused && "animate-pulse bg-current",
                (!running || paused) && "bg-current/70",
              )}
            />
            {stateLabel}
          </Badge>
          <Badge variant="outline" className="mono uppercase">
            {status?.scan_mode ?? t("dashboard.scanControl.modeNone")}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-5 md:grid-cols-[auto_1fr] md:items-center">
          <div className="flex justify-center md:justify-start">
            <RadialProgress
              value={percent}
              size={128}
              label={t("dashboard.scanControl.progress")}
              color={running && !paused ? "var(--color-success)" : "var(--color-primary)"}
            />
          </div>
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {!running && (
                <Button onClick={() => call("start")} disabled={pending !== null}>
                  {pending === "start" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play />}
                  {t("dashboard.scanControl.start")}
                </Button>
              )}
              {running && !paused && (
                <Button variant="secondary" onClick={() => call("pause")} disabled={pending !== null}>
                  {pending === "pause" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Pause />}
                  {t("dashboard.scanControl.pause")}
                </Button>
              )}
              {running && paused && (
                <Button variant="secondary" onClick={() => call("resume")} disabled={pending !== null}>
                  {pending === "resume" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play />}
                  {t("dashboard.scanControl.resume")}
                </Button>
              )}
              {running && (
                <Button variant="destructive" onClick={() => call("stop")} disabled={pending !== null}>
                  {pending === "stop" ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <StopCircle />
                  )}
                  {t("dashboard.scanControl.stop")}
                </Button>
              )}
              {!running && stats && stats.total_queries > 0 ? (
                <Button variant="ghost" disabled>
                  <Square className="h-4 w-4" />
                  {t("dashboard.scanControl.stateStopped")}
                </Button>
              ) : null}
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">{t("dashboard.scanControl.progress")}</span>
                <span className="tabular-nums">
                  {t("dashboard.scanControl.progressDetail", {
                    done: stats?.current_query_index ?? 0,
                    total: stats?.total_queries ?? 0,
                  })}
                </span>
              </div>
              <Progress value={percent} />
              {stats?.current_query ? (
                <div className="text-xs text-muted-foreground">
                  <span className="mr-1 font-medium text-foreground">
                    {t("dashboard.scanControl.currentQuery")}:
                  </span>
                  <span className="mono break-all">{stats.current_query}</span>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
