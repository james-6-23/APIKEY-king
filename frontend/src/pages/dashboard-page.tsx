import { useTranslation } from "react-i18next";
import { useScanStatus } from "@/hooks/useScanStatus";
import { useAppConfig } from "@/hooks/useAppConfig";
import { StatsCards } from "@/components/dashboard/stats-cards";
import { ScanControlCard } from "@/components/dashboard/scan-control-card";
import { LiveLogsCard } from "@/components/dashboard/live-logs-card";

export function DashboardPage() {
  const { t } = useTranslation();
  const { status } = useScanStatus();
  const { config } = useAppConfig();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t("dashboard.title")}</h1>
        <p className="text-sm text-muted-foreground">{t("dashboard.subtitle")}</p>
      </div>

      <StatsCards stats={status?.stats} />
      <ScanControlCard status={status} config={config} />
      <LiveLogsCard />
    </div>
  );
}
