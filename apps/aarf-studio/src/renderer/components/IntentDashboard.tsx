import React, { useEffect, useState } from "react";
import { useRuntimeLive } from "../hooks/useRuntimeLive";
import { runtimeUrl } from "../lib/platform";

export function IntentDashboard() {
  const { prediction, connected, health } = useRuntimeLive();
  const [metrics, setMetrics] = useState<Record<string, number>>({});

  useEffect(() => {
    fetch(`${runtimeUrl()}/metrics`)
      .then((r) => r.json())
      .then(setMetrics)
      .catch(() => {});
  }, [prediction]);

  const p = prediction || {
    intent: "—",
    emotion: "—",
    behavior: "—",
    confidence: 0,
    gate: "idle",
  };

  return (
    <div className="dashboard-grid">
      <section className="card">
        <h2>Intent dashboard</h2>
        <p className="meta">
          Runtime {connected ? "connected" : "offline"}
          {health.wsl ? " · WSL bridge ready" : ""}
        </p>
        <dl className="kv">
          <dt>Intent</dt>
          <dd>{p.intent}</dd>
          <dt>Emotion</dt>
          <dd>{p.emotion}</dd>
          <dt>Behavior</dt>
          <dd>{p.behavior}</dd>
          <dt>Confidence</dt>
          <dd>{(p.confidence * 100).toFixed(0)}%</dd>
          <dt>Gate</dt>
          <dd className={`gate-${p.gate}`}>{p.gate}</dd>
        </dl>
      </section>
      <section className="card">
        <h3>Feedback metrics</h3>
        <ul className="metric-list">
          <li><span>Predictions</span><strong>{metrics.predictions ?? 0}</strong></li>
          <li><span>Feedback events</span><strong>{metrics.feedback_events ?? 0}</strong></li>
          <li><span>Positive ratings</span><strong>{metrics.positive_ratings ?? 0}</strong></li>
        </ul>
      </section>
    </div>
  );
}
