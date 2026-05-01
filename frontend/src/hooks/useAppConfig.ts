import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AppConfig, ConfigResponse } from "@/types/api";

export function useAppConfig() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<ConfigResponse>("/api/config");
      setConfig(res.config ?? null);
    } catch {
      setConfig(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { config, loading, reload };
}
