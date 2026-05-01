import { useTranslation } from "react-i18next";
import { useScanStatus } from "@/hooks/useScanStatus";
import { StatsCards } from "@/components/dashboard/stats-cards";
import { ScanControlCard } from "@/components/dashboard/scan-control-card";
import { LiveLogsCard } from "@/components/dashboard/live-logs-card";
import { KeysTableCard } from "@/components/dashboard/keys-table-card";

export function DashboardPage() {
  const { t } = useTranslation();
  const { status } = useScanStatus();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t("dashboard.title")}</h1>
        <p className="text-sm text-muted-foreground">{t("dashboard.subtitle")}</p>
      </div>

      <StatsCards stats={status?.stats} />
      <ScanControlCard status={status} />

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <LiveLogsCard />
        </div>
        <div className="lg:col-span-3">
          <KeysTableCard />
        </div>
      </div>
    </div>
  );
}
