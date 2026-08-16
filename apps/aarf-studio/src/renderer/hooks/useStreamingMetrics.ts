import { useEffect, useState } from "react";

import type { LiveStatus } from "../lib/platform";
import { fetchLiveStatus } from "../lib/platform";

export function useStreamingMetrics(active: boolean, pollMs = 2000) {
  const [status, setStatus] = useState<LiveStatus | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const s = await fetchLiveStatus();
      if (!cancelled && s) setStatus(s);
    };
    void load();
    const id = window.setInterval(load, pollMs);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [active, pollMs]);

  return { status };
}
