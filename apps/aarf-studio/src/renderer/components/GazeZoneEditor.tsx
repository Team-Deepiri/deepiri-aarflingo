import React, { useCallback, useEffect, useRef, useState } from "react";

import type { CaptureMode } from "../lib/platform";
import { fetchZones, saveZones } from "../lib/zones";
import type { ZoneRect, Zones } from "../lib/zones";

const PREVIEW_PALETTE = ["door", "toy", "bowl"];

function clamp(v: number, lo: number, hi: number) {
  return Math.min(hi, Math.max(lo, v));
}

function toClient(e: { clientX: number; clientY: number }) {
  return { x: e.clientX, y: e.clientY };
}

type Box = { w: number; h: number };

/**
 * Map between stage-normalized and source-frame-normalized coordinates.
 *
 * The `.video-feed` uses `object-fit: cover`, so the visible video is the
 * source frame scaled to fill the stage and cropped to the stage aspect. The
 * perception pipeline sees the *full* source frame, so saved zones must be
 * expressed in source-frame space. This transform inverts the cover crop.
 */
function coverTransform(stage: Box, src: Box) {
  const scale = Math.max(stage.w / src.w, stage.h / src.h);
  const scaledW = src.w * scale;
  const scaledH = src.h * scale;
  const offX = (scaledW - stage.w) / 2;
  const offY = (scaledH - stage.h) / 2;
  const toSource = (nx: number, ny: number) => ({
    sx: (nx * stage.w + offX) / scaledW,
    sy: (ny * stage.h + offY) / scaledH,
  });
  const toStage = (sx: number, sy: number) => ({
    nx: (sx * scaledW - offX) / stage.w,
    ny: (sy * scaledH - offY) / stage.h,
  });
  return { toSource, toStage };
}

/**
 * Gaze zone editor — draggable / resizable rects over the live preview.
 *
 * Zones are stored and saved in source-frame-normalized 0–1 space (matching
 * the perception pipeline); `object-fit: cover` cropping is undone on render
 * so the rects sit exactly where they will be detected.
 */
export function GazeZoneEditor({
  stageRef,
  mode,
  videoRef,
  bridgeImgRef,
}: {
  stageRef: React.RefObject<HTMLDivElement | null>;
  mode: CaptureMode;
  videoRef: React.RefObject<HTMLVideoElement | null>;
  bridgeImgRef: React.RefObject<HTMLImageElement | null>;
}) {
  const [zones, setZones] = useState<Zones | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stageSize, setStageSize] = useState<Box | null>(null);
  const [sourceSize, setSourceSize] = useState<Box | null>(null);

  const zonesRef = useRef(zones);
  zonesRef.current = zones;
  const dragRef = useRef<{ name: string; mode: "move" | "resize"; startX: number; startY: number; orig: ZoneRect } | null>(null);

  // Keep the stage + source frame sizes in sync so the cover-crop transform
  // tracks the live feed (browser video / bridge image).
  useEffect(() => {
    const read = () => {
      const box = stageRef.current?.getBoundingClientRect();
      if (box && box.width > 0 && box.height > 0) {
        setStageSize({ w: box.width, h: box.height });
      }
      if (mode === "browser") {
        const v = videoRef.current;
        if (v && v.videoWidth > 0) setSourceSize({ w: v.videoWidth, h: v.videoHeight });
      } else if (mode === "bridge") {
        const img = bridgeImgRef.current;
        if (img && img.naturalWidth > 0) setSourceSize({ w: img.naturalWidth, h: img.naturalHeight });
      } else {
        // server mode: no browser feed to measure; assume stage == source.
        setSourceSize(null);
      }
    };
    read();
    const id = window.setInterval(read, 500);
    return () => window.clearInterval(id);
  }, [stageRef, mode, videoRef, bridgeImgRef]);

  const transform = (): ReturnType<typeof coverTransform> | null => {
    if (!stageSize || !sourceSize) return null;
    return coverTransform(stageSize, sourceSize);
  };

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

  // Pointer → source-frame normalized coords (undoes the cover crop).
  const normalized = useCallback(
    (clientX: number, clientY: number): { nx: number; ny: number } => {
      const box = stageRef.current?.getBoundingClientRect();
      if (!box || box.width === 0 || box.height === 0) return { nx: 0, ny: 0 };
      const nx = clamp((clientX - box.left) / box.width, 0, 1);
      const ny = clamp((clientY - box.top) / box.height, 0, 1);
      const t = transform();
      if (!t) return { nx, ny };
      const s = t.toSource(nx, ny);
      return { nx: clamp(s.sx, 0, 1), ny: clamp(s.sy, 0, 1) };
    },
    [stageRef, stageSize, sourceSize]
  );

  // Source-frame zone → stage-frame rect for rendering (applies the crop).
  const toStageRect = useCallback(
    (z: ZoneRect): ZoneRect => {
      const t = transform();
      if (!t) return z;
      const tl = t.toStage(z.x, z.y);
      const br = t.toStage(z.x + z.w, z.y + z.h);
      return {
        x: clamp(tl.nx, 0, 1),
        y: clamp(tl.ny, 0, 1),
        w: clamp(br.nx - tl.nx, 0.02, 1 - tl.nx),
        h: clamp(br.ny - tl.ny, 0.02, 1 - tl.ny),
      };
    },
    [stageSize, sourceSize]
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
          {Object.entries(zones).map(([name, z]) => {
            const stage = toStageRect(z);
            return (
              <div
                key={name}
                className={`zone-rect${selected === name ? " selected" : ""}`}
                style={{
                  left: `${stage.x * 100}%`,
                  top: `${stage.y * 100}%`,
                  width: `${stage.w * 100}%`,
                  height: `${stage.h * 100}%`,
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
            );
          })}
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