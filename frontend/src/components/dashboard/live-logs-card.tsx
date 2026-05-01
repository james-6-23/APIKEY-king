import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { Activity, Eraser, WifiOff } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useLogsSocket } from "@/hooks/useLogsSocket";
import { useToast } from "@/hooks/useToast";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { LogEntry, LogLevel } from "@/lib/ws";

const LEVEL_STYLES: Record<string, string> = {
  success: "text-[color:var(--color-success)]",
  info: "text-[color:var(--color-info)]",
  warning: "text-[color:var(--color-warning)]",
  error: "text-destructive",
  debug: "text-muted-foreground",
};

function formatTs(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString("en-GB", { hour12: false });
  } catch {
    return iso;
  }
}

export function LiveLogsCard() {
  const { t } = useTranslation();
  const toast = useToast();
  const { logs, connected } = useLogsSocket();
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [logs.length]);

  const handleClear = async () => {
    try {
      await api.delete("/api/logs");
      // WS broadcast will drop client-side logs too.
      toast.success(t("dashboard.logs.cleared"));
    } catch (err) {
      toast.error(t("common.error"), (err as Error).message);
    }
  };

  return (
    <Card className="flex flex-col">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle>{t("dashboard.logs.title")}</CardTitle>
          <CardDescription>{t("dashboard.logs.description")}</CardDescription>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={connected ? "success" : "secondary"} className="gap-1.5">
            {connected ? (
              <Activity className="h-3 w-3 animate-pulse" />
            ) : (
              <WifiOff className="h-3 w-3" />
            )}
            {connected ? t("dashboard.logs.connected") : t("dashboard.logs.disconnected")}
          </Badge>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            disabled={logs.length === 0}
          >
            <Eraser /> {t("dashboard.logs.clear")}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-1 p-0">
        <ScrollArea className="h-[500px] border-t">
          <div className="divide-y divide-border/50 px-4 py-2 font-mono text-xs">
            {logs.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground">
                {t("dashboard.logs.empty")}
              </div>
            ) : (
              logs.map((log, idx) => <LogRow key={`${log.timestamp}-${idx}`} log={log} />)
            )}
            <div ref={endRef} />
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function LogRow({ log }: { log: LogEntry }) {
  const levelClass = LEVEL_STYLES[log.type as LogLevel] ?? "text-foreground";
  return (
    <div className="flex gap-2 py-1.5">
      <span className="shrink-0 text-muted-foreground">{formatTs(log.timestamp)}</span>
      <span className={cn("w-14 shrink-0 uppercase", levelClass)}>
        {log.type}
      </span>
      <span className="flex-1 break-all">{log.message}</span>
    </div>
  );
}
