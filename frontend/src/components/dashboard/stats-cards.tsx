import { useTranslation } from "react-i18next";
import { FileSearch, KeyRound, ShieldCheck } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { ScanStats } from "@/types/api";

interface Props {
  stats: ScanStats | undefined;
}

export function StatsCards({ stats }: Props) {
  const { t } = useTranslation();

  const cells = [
    {
      label: t("dashboard.stats.filesScanned"),
      sub: t("dashboard.stats.filesScannedSub"),
      value: stats?.total_files ?? 0,
      Icon: FileSearch,
      accent: "from-sky-500/20",
    },
    {
      label: t("dashboard.stats.keysDiscovered"),
      sub: t("dashboard.stats.keysDiscoveredSub"),
      value: stats?.total_keys ?? 0,
      Icon: KeyRound,
      accent: "from-amber-500/20",
    },
    {
      label: t("dashboard.stats.keysValidated"),
      sub: t("dashboard.stats.keysValidatedSub"),
      value: stats?.valid_keys ?? 0,
      Icon: ShieldCheck,
      accent: "from-emerald-500/25",
      highlight: true,
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {cells.map((cell) => (
        <Card
          key={cell.label}
          className={cn(
            "relative overflow-hidden",
            cell.highlight && "ring-1 ring-primary/20",
          )}
        >
          <div
            className={cn(
              "pointer-events-none absolute inset-0 bg-gradient-to-br to-transparent opacity-60",
              cell.accent,
            )}
          />
          <CardContent className="relative flex items-start justify-between p-6">
            <div>
              <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {cell.label}
              </div>
              <div className="mt-3 text-3xl font-semibold tabular-nums">
                {stats ? (
                  formatNumber(cell.value)
                ) : (
                  <Skeleton className="h-8 w-20" />
                )}
              </div>
              <div className="mt-1 text-xs text-muted-foreground">{cell.sub}</div>
            </div>
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-background/70 text-foreground shadow-sm">
              <cell.Icon className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
