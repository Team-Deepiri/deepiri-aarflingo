import React from "react";

import { useVoiceData } from "../hooks/useVoiceData";
import { EMOTION_LABELS, INTENT_LABELS } from "../lib/labels";

export function VoiceView() {
  const voice = useVoiceData(true, 4000);

  return (
    <div className="voice-view">
      <section className="card">
        <h2>Voice engine</h2>
        <p className="meta">
          {voice.enabled === null
            ? "Loading voice data…"
            : voice.enabled
            ? "Learned phrase weights + recent bark outcomes for this dog."
            : "Voice engine not enabled on runtime (set VOICE_ENABLED=1)."}
        </p>
      </section>

      <section className="card">
        <h3>Learned phrase weights</h3>
        {Object.keys(voice.weights).length ? (
          <div className="signal-grid">
            {Object.entries(voice.weights)
              .sort((a, b) => b[1] - a[1])
              .map(([phrase, w]) => (
                <div key={phrase} className="signal">
                  <span>{phrase}</span>
                  <div className="signal-bar">
                    <div style={{ width: `${Math.min(100, (w / 2) * 100)}%` }} />
                  </div>
                </div>
              ))}
          </div>
        ) : (
          <p className="meta">No learned weights yet — the conversation engine adapts as it speaks.</p>
        )}
      </section>

      <section className="card">
        <h3>Recent bark outcomes</h3>
        {voice.outcomes.length ? (
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Phrase</th>
                <th>Intent</th>
                <th>Emotion</th>
                <th>Response</th>
                <th>Reward</th>
              </tr>
            </thead>
            <tbody>
              {voice.outcomes.map((o) => (
                <tr key={o.id}>
                  <td>{new Date(o.ts_ms).toLocaleTimeString()}</td>
                  <td>“{o.phrase}”</td>
                  <td>{INTENT_LABELS[o.intent] || o.intent || "—"}</td>
                  <td>{EMOTION_LABELS[o.emotion] || o.emotion || "—"}</td>
                  <td>
                    <span className={`chip ${o.responded ? "chip-ok" : "chip-warn"}`}>
                      {o.responded ? `bark ${o.bark_valence ?? ""}` : "silent"}
                    </span>
                  </td>
                  <td>{o.reward?.toFixed(2) ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="meta">No voice outcomes yet.</p>
        )}
      </section>
    </div>
  );
}
