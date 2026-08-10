import React, { useEffect, useState } from "react";
import { useRuntimeLive } from "../hooks/useRuntimeLive";
import { useVoiceData } from "../hooks/useVoiceData";
import { runtimeUrl } from "../lib/platform";
import { EMOTION_LABELS, INTENT_LABELS } from "../lib/labels";

export function IntentDashboard() {
  const { prediction, connected, health, liveStatus, bark } = useRuntimeLive();
  const voice = useVoiceData(true, 5000);
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
          <dd>{INTENT_LABELS[p.intent] || p.intent}</dd>
          <dt>Emotion</dt>
          <dd>{EMOTION_LABELS[p.emotion] || p.emotion}</dd>
          <dt>Behavior</dt>
          <dd>{p.behavior}</dd>
          <dt>Confidence</dt>
          <dd>{(p.confidence * 100).toFixed(0)}%</dd>
          <dt>Gate</dt>
          <dd className={`gate-${p.gate}`}>{p.gate}</dd>
          <dt>Sequence</dt>
          <dd>{liveStatus?.sequence_len ?? 0}/{liveStatus?.sequence_capacity ?? 15}</dd>
          <dt>FPS</dt>
          <dd>{liveStatus?.fps?.toFixed(1) ?? "—"}</dd>
          <dt>Avg infer</dt>
          <dd>{liveStatus?.avg_infer_ms ?? "—"} ms</dd>
        </dl>
      </section>
      <section className="card">
        <h3>Feedback metrics</h3>
        <ul className="metric-list">
          <li><span>Predictions</span><strong>{metrics.predictions ?? 0}</strong></li>
          <li><span>Feedback events</span><strong>{metrics.feedback_events ?? 0}</strong></li>
          <li><span>Positive ratings</span><strong>{metrics.positive_ratings ?? 0}</strong></li>
          <li><span>Voice outcomes</span><strong>{metrics.voice_outcomes ?? 0}</strong></li>
          <li><span>Voice responded</span><strong>{metrics.voice_responded ?? 0}</strong></li>
        </ul>
      </section>
      <section className="card">
        <h3>Live streaming</h3>
        <ul className="metric-list">
          <li><span>Frames processed</span><strong>{liveStatus?.frames ?? 0}</strong></li>
          <li><span>Predictions emitted</span><strong>{liveStatus?.predictions ?? 0}</strong></li>
          <li><span>Inference rate</span><strong>{liveStatus?.fps ? `${liveStatus.fps.toFixed(1)} fps` : "—"}</strong></li>
          <li><span>Uptime</span><strong>{liveStatus ? `${Math.round(liveStatus.uptime_s)}s` : "—"}</strong></li>
          <li><span>Camera</span><strong>{liveStatus?.camera ?? "—"}</strong></li>
        </ul>
      </section>
      <section className="card">
        <h3>Voice activity</h3>
        {bark ? (
          <div className="voice-now">
            <p className="meta">Latest bark</p>
            <p className="voice-phrase">{bark.phrase ?? "bark"}</p>
            <p className="meta">valence: {bark.valence ?? "?"} · arousal: {bark.arousal ?? "?"} · reward: {bark.reward ?? "?"}</p>
          </div>
        ) : (
          <p className="meta">No bark events yet.</p>
        )}
        {voice.outcomes.length ? (
          <ul className="outcome-list">
            {voice.outcomes.slice(0, 5).map((o) => (
              <li key={o.id}>
                <span className="outcome-phrase">{o.phrase}</span>
                <span className={`chip ${o.responded ? "chip-ok" : "chip-warn"}`}>
                  {o.responded ? `bark ${o.bark_valence ?? ""}` : "silent"}
                </span>
              </li>
            ))}
          </ul>
        ) : null}
      </section>
    </div>
  );
}
