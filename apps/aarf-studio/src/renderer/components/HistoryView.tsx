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
  has_feedback?: boolean;
  needs_label?: boolean;
};

export function HistoryView() {
  const [rows, setRows] = useState<Row[]>([]);
  const [labelling, setLabelling] = useState<string | null>(null);
  const [intent, setIntent] = useState("");
  const [emotion, setEmotion] = useState("");

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

  const begin = (row: Row) => {
    setLabelling(row.id);
    setIntent(row.intent);
    setEmotion(row.emotion);
  };

  const submit = async (row: Row) => {
    await fetch(`${RUNTIME}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prediction_id: row.id,
        rating: 1,
        corrected_intent: intent === row.intent ? undefined : intent,
        corrected_emotion: emotion === row.emotion ? undefined : emotion,
      }),
    });
    setLabelling(null);
    setRows((prev) =>
      prev.map((r) => (r.id === row.id ? { ...r, has_feedback: true, needs_label: false } : r))
    );
  };

  return (
    <section className="card">
      <h2>Recent predictions</h2>
      <p className="meta">
        Low-confidence rows (<code>&lt;80%</code>, unlabelled) are highlighted — use
        <strong> Label this </strong>
        to correct them into the training set.
      </p>
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Intent</th>
            <th>Emotion</th>
            <th>Behavior</th>
            <th>Conf</th>
            <th>Signal</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} className={r.needs_label ? "row-review" : ""}>
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
              <td>
                {r.has_feedback ? (
                  <span className="chip chip-ok">labelled</span>
                ) : r.needs_label ? (
                  labelling === r.id ? (
                    <span className="label-inline">
                      <select value={intent} onChange={(e) => setIntent(e.target.value)}>
                        {Object.entries(INTENT_LABELS).map(([k, v]) => (
                          <option key={k} value={k}>
                            {v}
                          </option>
                        ))}
                      </select>
                      <select value={emotion} onChange={(e) => setEmotion(e.target.value)}>
                        {Object.entries(EMOTION_LABELS).map(([k, v]) => (
                          <option key={k} value={k}>
                            {v}
                          </option>
                        ))}
                      </select>
                      <button type="button" className="btn ghost" onClick={() => void submit(r)}>
                        Save
                      </button>
                    </span>
                  ) : (
                    <button type="button" className="btn ghost" onClick={() => begin(r)}>
                      Label this
                    </button>
                  )
                ) : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}