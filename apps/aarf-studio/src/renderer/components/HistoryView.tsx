import React, { useEffect, useState } from "react";

import { runtimeUrl } from "../lib/platform";
import { EMOTION_LABELS, INTENT_LABELS } from "../lib/labels";

const RUNTIME = runtimeUrl();

type Row = {
  id: string;
  intent: string;
  emotion: string;
  behavior: string;
  confidence: number;
  ts_ms: number;
};

export function HistoryView() {
  const [rows, setRows] = useState<Row[]>([]);

  useEffect(() => {
    const load = () =>
      fetch(`${RUNTIME}/predictions/recent`)
        .then((r) => r.json())
        .then(setRows)
        .catch(() => {});
    load();
    const id = setInterval(load, 3000);
    return () => clearInterval(id);
  }, []);

  return (
    <section className="card">
      <h2>Recent predictions</h2>
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Intent</th>
            <th>Emotion</th>
            <th>Behavior</th>
            <th>Conf</th>
            <th>Signal</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td>{new Date(r.ts_ms).toLocaleTimeString()}</td>
              <td>{INTENT_LABELS[r.intent] || r.intent}</td>
              <td>{EMOTION_LABELS[r.emotion] || r.emotion}</td>
              <td>{r.behavior}</td>
              <td>{(r.confidence * 100).toFixed(0)}%</td>
              <td>
                <div className="history-bar">
                  <div style={{ width: `${Math.min(100, r.confidence * 100)}%` }} />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
