import React from "react";

const EVENTS = [
  { id: "evt-1", intent: "explore", confidence: 0.62 },
  { id: "evt-2", intent: "rest", confidence: 0.71 },
];

export function HistoryView() {
  return (
    <section className="card">
      <h2>History</h2>
      <ul>
        {EVENTS.map((e) => (
          <li key={e.id}>
            {e.id}: {e.intent} ({(e.confidence * 100).toFixed(0)}%)
          </li>
        ))}
      </ul>
    </section>
  );
}
