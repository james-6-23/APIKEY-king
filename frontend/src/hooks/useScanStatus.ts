import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { ScanStatusResponse } from "@/types/api";

const POLL_INTERVAL = 3000;

export function useScanStatus() {
  const [status, setStatus] = useState<ScanStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    const tick = async () => {
      try {
        const data = await api.get<ScanStatusResponse>("/api/scan/status");
        if (!mountedRef.current) return;
        setStatus(data);
        setError(null);
      } catch (err) {
        if (!mountedRef.current) return;
        setError((err as Error).message);
      } finally {
        if (mountedRef.current) {
          pollRef.current = window.setTimeout(tick, POLL_INTERVAL);
        }
      }
    };
    tick();
    return () => {
      mountedRef.current = false;
      if (pollRef.current) window.clearTimeout(pollRef.current);
    };
  }, []);

  return { status, error };
}
