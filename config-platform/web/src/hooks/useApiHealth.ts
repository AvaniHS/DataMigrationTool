import { useEffect, useState } from "react";
import { fetchHealth } from "@/api/health";
import { logClientError } from "@/api/logger";

export type ApiHealthStatus = "checking" | "ok" | "offline";

export function useApiHealth(): ApiHealthStatus {
  const [apiStatus, setApiStatus] = useState<ApiHealthStatus>("checking");

  useEffect(() => {
    let cancelled = false;
    fetchHealth()
      .then(() => {
        if (!cancelled) {
          setApiStatus("ok");
        }
      })
      .catch((error: unknown) => {
        logClientError("api_health_check_failed", error);
        if (!cancelled) {
          setApiStatus("offline");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return apiStatus;
}
