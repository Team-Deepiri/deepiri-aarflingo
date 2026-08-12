import React, { useCallback, useEffect, useRef, useState } from "react";

import { fetchZones, saveZones } from "../lib/zones";
import type { ZoneRect, Zones } from "../lib/zones";

const PREVIEW_PALETTE = ["door", "toy", "bowl"];

function clamp(v: number, lo: number, hi: number) {
  return Math.min(hi, Math.max(lo, v));
}

function toClient(e: { clientX: number; clientY: number }) {
  return { x: e.clientX, y: e.clientY };
}

/**
 * Gaze zone editor — draggable / resizable rects over the live preview.
 *
 * Coordinates are normalized 0–1 relative to the video stage box, matching the
 * schema read by the perception pipeline. Save writes to zones.default.yaml
 * via PUT /gaze/zones and the runtime hot-reloads the zones in memory.
 */
export function GazeZoneEditor({ stageRef }: { stageRef: React.RefObject<HTMLDivElement | null> }) {
  const [zones, setZones] = useState<Zones | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const zonesRef = useRef(zones);
  zonesRef.current = zones;
  const dragRef = useRef<{ name: string; mode: "move" | "resize"; startX: number; startY: number; orig: ZoneRect } | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    const res = await fetchZones();
    if (res) {
      setZones(res.zones);
      setStatus(`Loaded from ${res.path}`);
    } else {
      setError("Couldn't reach runtime /gaze/zones.");
      setZones(null);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const normalized = useCallback(
    (clientX: number, clientY: number): { nx: number; ny: number } => {
      const box = stageRef.current?.getBoundingClientRect();
      if (!box || box.width === 0 || box.height === 0) return { nx: 0, ny: 0 };
      return {
        nx: clamp((clientX - box.left) / box.width, 0, 1),
        ny: clamp((clientY - box.top) / box.height, 0, 1),
      };
    },
    [stageRef]
  );

  const onPointerDown = useCallback(
    (e: React.PointerEvent, name: string, mode: "move" | "resize") => {
      e.preventDefault();
      e.stopPropagation();
      (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
      setSelected(name);
      const z = zonesRef.current?.[name];
      if (!z) return;
      const { x, y } = toClient(e);
      dragRef.current = { name, mode, startX: x, startY: y, orig: { ...z } };
    },
    []
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent) => {
      const drag = dragRef.current;
      if (!drag || !zonesRef.current) return;
      const { nx, ny } = normalized(e.clientX, e.clientY);
      const dx = nx - normalized(drag.startX, drag.startY).nx;
      const dy = ny - normalized(drag.startX, drag.startY).ny;
      const orig = drag.orig;
      setZones((prev) => {
        if (!prev?.[drag.name]) return prev;
        const cur = { ...prev[drag.name] };
        if (drag.mode === "move") {
          cur.x = clamp(orig.x + dx, 0, 1 - cur.w);
          cur.y = clamp(orig.y + dy, 0, 1 - cur.h);
        } else {
          cur.w = clamp(orig.w + dx, 0.02, 1 - cur.x);
          cur.h = clamp(orig.h + dy, 0.02, 1 - cur.y);
        }
        return { ...prev, [drag.name]: cur };
      });
    },
    [normalized]
  );

  const onPointerUp = useCallback(() => {
    dragRef.current = null;
  }, []);

  const addZone = useCallback(() => {
    setZones((prev) => {
      const origin = { ...(prev ?? {}) };
      const base = Object.keys(origin).length + 1;
      origin[`zone_${base}`] = { x: 0.1, y: 0.1, w: 0.2, h: 0.2 };
      setSelected(`zone_${base}`);
      return origin;
    });
  }, []);

  const removeZone = useCallback(
    (name: string) => {
      setZones((prev) => {
        if (!prev) return prev;
        const next = { ...prev };
        delete next[name];
        return next;
      });
      if (selected === name) setSelected(null);
    },
    [selected]
  );

  const handleSave = useCallback(async () => {
    if (!zonesRef.current) return;
    setSaving(true);
    const res = await saveZones(zonesRef.current);
    setSaving(false);
    if (res) {
      setStatus(res.reloaded ? "Saved — perception pipeline hot-reloaded." : `Saved to ${res.path}.`);
      setZones(res.zones);
    } else {
      setError("Save failed — runtime unreachable.");
    }
  }, []);

  if (loading) {
    return <div className="zone-editor zone-editor-msg">Loading zones…</div>;
  }

  return (
    <div className="zone-editor">
      {zones ? (
        <div className="zone-canvas" onPointerMove={onPointerMove} onPointerUp={onPointerUp}>
          {Object.entries(zones).map(([name, z]) => (
            <div
              key={name}
              className={`zone-rect${selected === name ? " selected" : ""}`}
              style={{
                left: `${z.x * 100}%`,
                top: `${z.y * 100}%`,
                width: `${z.w * 100}%`,
                height: `${z.h * 100}%`,
              }}
              onPointerDown={(e) => onPointerDown(e, name, "move")}
              title={`${name} — drag to move`}
            >
              <span className="zone-label">{name}</span>
              <span
                className="zone-resize"
                onPointerDown={(e) => onPointerDown(e, name, "resize")}
                title="Drag to resize"
              />
              <button
                type="button"
                className="zone-remove"
                onClick={(e) => {
                  e.stopPropagation();
                  removeZone(name);
                }}
                title={`Remove ${name}`}
                aria-label={`Remove ${name}`}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      ) : null}

      <div className="zone-toolbar">
        <button type="button" className="btn primary" onClick={() => void handleSave()} disabled={!zones || saving}>
          {saving ? "Saving…" : "Save zones"}
        </button>
        <button type="button" className="btn ghost" onClick={addZone}>
          Add zone
        </button>
        <button type="button" className="btn ghost" onClick={() => void refresh()}>
          Reload
        </button>
        <span className="meta zone-hint">Normalized 0–1 · drag to move · corner to resize · {PREVIEW_PALETTE.join(", ")}</span>
      </div>
      {status ? <p className="meta zone-status">{status}</p> : null}
      {error ? <div className="alert alert-error">{error}</div> : null}
    </div>
  );
}