import React from "react";

const DEMO = {
  intent: "solicit_play",
  emotion: "excited",
  behavior: "play_bow",
  confidence: 0.88,
  gate: "pass",
};

export function IntentDashboard() {
  return (
    <section className="card">
      <h2>Intent dashboard</h2>
      <dl>
        <dt>Intent</dt>
        <dd>{DEMO.intent}</dd>
        <dt>Emotion</dt>
        <dd>{DEMO.emotion}</dd>
        <dt>Behavior</dt>
        <dd>{DEMO.behavior}</dd>
        <dt>Confidence</dt>
        <dd>{(DEMO.confidence * 100).toFixed(0)}%</dd>
        <dt>Gate</dt>
        <dd className={`gate-${DEMO.gate}`}>{DEMO.gate}</dd>
      </dl>
    </section>
  );
}
