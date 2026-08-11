import { useCallback, useEffect, useState } from "react";

import type { VoiceOutcome } from "../lib/platform";
import { fetchVoiceOutcomes, fetchVoiceWeights } from "../lib/platform";

export function useVoiceData(active: boolean, pollMs = 4000) {
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [outcomes, setOutcomes] = useState<VoiceOutcome[]>([]);
  const [enabled, setEnabled] = useState<boolean | null>(null);

  const load = useCallback(async () => {
    const [w, o] = await Promise.all([fetchVoiceWeights(), fetchVoiceOutcomes()]);
    setWeights(w);
    setOutcomes(o);
    setEnabled(Object.keys(w).length > 0 || o.length > 0);
  }, []);

  useEffect(() => {
    if (!active) return;
    void load();
    const id = window.setInterval(load, pollMs);
    return () => window.clearInterval(id);
  }, [active, pollMs, load]);

  return { weights, outcomes, enabled, reload: load };
}
