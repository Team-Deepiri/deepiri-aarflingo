import React, { useEffect, useState } from "react";

const RUNTIME = import.meta.env.VITE_RUNTIME_URL || "http://127.0.0.1:8765";

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
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td>{new Date(r.ts_ms).toLocaleTimeString()}</td>
              <td>{r.intent}</td>
              <td>{r.emotion}</td>
              <td>{r.behavior}</td>
              <td>{(r.confidence * 100).toFixed(0)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
