import React from "react";

import { useRuntimeHealth } from "../hooks/useRuntimeHealth";

/**
 * Global header status strip — runtime reachability + WS latency + bridge
 * health, visible on every tab.
 */
export function HealthHeader() {
  const { ok, checking, bridgeOk, bridgeProbing, wsl, bridgeUrl, httpLatency, wsLatency } = useRuntimeHealth();

  const state = checking ? "checking" : ok ? "ok" : "down";
  const bridgeState = bridgeProbing ? "checking" : bridgeOk === null ? "unknown" : bridgeOk ? "ok" : "down";

  return (
    <header className="health-header">
      <div className="health-item">
        <span className={`dot dot-${state}`} aria-hidden="true" />
        <span className={`health-label health-${state}`}>
          {checking ? "Runtime…" : ok ? "Runtime live" : "Runtime down"}
        </span>
      </div>
      {ok ? (
        <div className="health-item" title="Round-trip latency to the runtime">
          <span className={`health-label ${wsLatency == null ? "health-checking" : ""}`}>
            {wsLatency == null ? "WS…" : `WS ${wsLatency} ms`}
          </span>
          {httpLatency != null ? <span className="meta">HTTP {httpLatency} ms</span> : null}
        </div>
      ) : null}
      <div className="health-item">
        <span className={`dot dot-${bridgeState}`} aria-hidden="true" />
        <span className={`health-label health-${bridgeState}`}>
          {bridgeProbing ? "Bridge…" : bridgeOk === null ? "Bridge unknown" : bridgeOk ? "Bridge up" : "Bridge down"}
        </span>
      </div>
      {wsl ? <span className="chip chip-info">WSL</span> : null}
      {bridgeUrl ? (
        <a className="health-url meta" href={bridgeUrl} target="_blank" rel="noreferrer" title={bridgeUrl}>
          view feed ↗
        </a>
      ) : null}
    </header>
  );
}