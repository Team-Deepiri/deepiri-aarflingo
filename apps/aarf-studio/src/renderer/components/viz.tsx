import React from "react";

export function ConfidenceRing({ pct, color, label }: { pct: number; color: string; label?: string }) {
  return (
    <div
      className="intent-ring"
      style={{ ["--pct" as string]: pct, ["--ring" as string]: color }}
    >
      <span>{label ?? `${pct}%`}</span>
    </div>
  );
}

export function Sparkline({
  points,
  width = 200,
  height = 44,
  color = "#3dd68c",
  max = 1,
}: {
  points: number[];
  width?: number;
  height?: number;
  color?: string;
  max?: number;
}) {
  if (points.length < 2) {
    return <div className="sparkline-empty meta">awaiting data…</div>;
  }
  const step = width / (points.length - 1);
  const pts = points
    .map((p, i) => {
      const x = i * step;
      const y = height - Math.min(1, Math.max(0, p) / max) * (height - 4) - 2;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} className="sparkline" aria-hidden="true">
      <polyline points={pts} fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
      <line x1={0} y1={height - 2} x2={width} y2={height - 2} stroke="var(--border)" strokeWidth={1} />
    </svg>
  );
}

export function TokenHeatmap({
  sequence,
  featureNames,
  featureRows,
  height = 96,
}: {
  sequence: number[][];
  featureNames: string[];
  featureRows: string[];
  height?: number;
}) {
  const rows = featureRows.map((name) => ({ name, index: featureNames.indexOf(name) })).filter((r) => r.index >= 0);
  if (rows.length === 0 || sequence.length === 0) {
    return <p className="meta">Collecting sequence tokens…</p>;
  }
  const cols = sequence.length;
  const cellW = Math.max(10, 640 / cols);
  const cellH = Math.max(8, height / rows.length);
  return (
    <div className="token-heatmap" role="img" aria-label="Feature sequence token heatmap">
      <div className="token-rows">
        {rows.map((r) => (
          <span key={r.name} className="token-row-label">
            {r.name}
          </span>
        ))}
      </div>
      <div className="token-grid">
        {rows.map((r) => (
          <div key={r.name} className="token-row">
            {sequence.map((frame, fi) => {
              const v = frame[r.index] ?? 0;
              const alpha = Math.min(1, Math.max(0, v));
              return (
                <span
                  key={fi}
                  className="token-cell"
                  style={{ width: cellW, height: cellH, background: `rgba(61, 214, 140, ${(alpha * 0.9).toFixed(2)})` }}
                  title={`${r.name} frame ${fi}: ${v.toFixed(3)}`}
                />
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

export function SignalBars({ signals }: { signals: { key: string; label: string; value: number }[] }) {
  return (
    <div className="signal-grid">
      {signals.map(({ key, label, value }) => {
        const v = Number(value || 0);
        const pct = Math.min(100, Math.max(0, v * 100));
        return (
          <div key={key} className="signal">
            <span>{label}</span>
            <div className="signal-bar">
              <div style={{ width: `${pct}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function BarRow({ label, value, max = 1, color }: { label: string; value: number; max?: number; color?: string }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className="bar-row">
      <span className="bar-label">{label}</span>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${pct}%`, background: color ?? "var(--grad-accent)" }} />
      </div>
      <span className="bar-value">{Math.round(pct)}%</span>
    </div>
  );
}
