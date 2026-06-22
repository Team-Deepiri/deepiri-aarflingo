import React, { useEffect, useState } from "react";
import { useRuntimeLive } from "../hooks/useRuntimeLive";

const RUNTIME = import.meta.env.VITE_RUNTIME_URL || "http://127.0.0.1:8765";

export function IntentDashboard() {
  const { prediction } = useRuntimeLive();
  const [metrics, setMetrics] = useState<Record<string, number>>({});

  useEffect(() => {
    fetch(`${RUNTIME}/metrics`)
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
    <section className="card">
      <h2>Intent dashboard</h2>
      <dl>
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
      <h3>Feedback metrics</h3>
      <ul>
        <li>Predictions logged: {metrics.predictions ?? 0}</li>
        <li>Feedback events: {metrics.feedback_events ?? 0}</li>
        <li>Positive ratings: {metrics.positive_ratings ?? 0}</li>
      </ul>
    </section>
  );
}
