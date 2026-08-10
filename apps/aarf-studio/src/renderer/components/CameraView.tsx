import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { CaptureMode } from "../lib/platform";
import { isMobileBrowser, runtimeUrl } from "../lib/platform";
import { postFrame, useCameraCapture } from "../hooks/useCameraCapture";
import { useConfigDetect } from "../hooks/useConfigDetect";
import { useDogProfile } from "../hooks/useDogProfile";
import { useRuntimeLive } from "../hooks/useRuntimeLive";
import { useStreamingMetrics } from "../hooks/useStreamingMetrics";
import { useVoiceData } from "../hooks/useVoiceData";
import {
  BEHAVIOR_LABELS,
  EMOTION_LABELS,
  FEATURE_NAMES,
  INTENT_LABELS,
  MODALITY_DEFS,
  MODE_HINTS,
  MODE_LABELS,
  SPEECH_WORDS,
  TOKEN_FEATURES,
  TRAIT_LABELS,
} from "../lib/labels";
import { ConfidenceRing, SignalBars, Sparkline, TokenHeatmap } from "./viz";

function speak(intent: string) {
  if (!("speechSynthesis" in window)) return;
  const text = SPEECH_WORDS[intent] || intent.replace(/_/g, " ");
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 1.05;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}

const _isMobile = isMobileBrowser();

export function LiveView() {
  const lastSpoke = useRef("");
  const [retrainMsg, setRetrainMsg] = useState("");
  const [confidenceHistory, setConfidenceHistory] = useState<number[]>([]);
  const [snack, setSnack] = useState<string | null>(null);

  const config = useConfigDetect();
  const { prediction, connected, error: runtimeError, health, liveStatus, startWebcam, stopWebcam, sendFeedback, refreshLiveStatus } = useRuntimeLive();
  const { status: streamStatus } = useStreamingMetrics(true);
  const { profile } = useDogProfile();
  const voice = useVoiceData(true);

  const onFrame = useCallback(async (blob: Blob) => {
    await postFrame(blob);
  }, []);

  const cam = useCameraCapture(onFrame, prediction);

  useEffect(() => {
    if (!prediction) return;
    setConfidenceHistory((prev) => [...prev.slice(-59), prediction.confidence]);
  }, [prediction]);

  useEffect(() => {
    if (!prediction || prediction.gate !== "pass" || prediction.confidence < 0.85) return;
    const key = `${prediction.intent}-${prediction.ts_ms}`;
    if (lastSpoke.current === key) return;
    lastSpoke.current = key;
    speak(prediction.intent);
  }, [prediction]);

  const toggleInference = async () => {
    if (cam.inferencing) {
      cam.setInferencing(false);
      await stopWebcam();
      setSnack("Inference stopped — preview stays live");
    } else {
      if (cam.mode === "server") {
        await startWebcam({ mode: "server" });
      } else {
        await startWebcam({ mode: "browser" });
      }
      cam.setInferencing(true);
      await refreshLiveStatus();
      setSnack("Inference running — predictions streaming");
    }
    window.setTimeout(() => setSnack(null), 2500);
  };

  const features = prediction?.features || {};
  const showWslHint = !_isMobile && Boolean(health.wsl || cam.wsl) && cam.mode !== "bridge";

  const modalityGroups = useMemo(() => {
    const groups: { group: string; signals: { key: string; label: string; value: number }[] }[] = [];
    const order = ["Vision", "Audio", "Heart", "Body", "Motion", "Gaze"];
    for (const g of order) {
      const items = MODALITY_DEFS.filter((d) => d.group === g).map((d) => ({
        key: d.key,
        label: d.label,
        value: Number(features[d.key] || 0),
      }));
      if (items.length) groups.push({ group: g, signals: items });
    }
    return groups;
  }, [features]);

  const intentBars = useMemo(() => {
    const probs = prediction?.intent_probs || {};
    return Object.entries(probs)
      .map(([key, v]) => ({ key, label: INTENT_LABELS[key] || key, value: v }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 5);
  }, [prediction]);

  const emotionLabel = prediction ? EMOTION_LABELS[prediction.emotion] || prediction.emotion : null;
  const behaviorLabel = prediction ? BEHAVIOR_LABELS[prediction.behavior] || prediction.behavior : null;

  return (
    <div className="studio-grid">
      <div className="studio-main">
        <section className="card config-card">
          <div className="card-head">
            <div>
              <h2>Capture source</h2>
              <p className="meta">Auto-detected for this device — pick the mode that fits.</p>
            </div>
            <div className="status-chips">
              <span className={`chip ${connected ? "chip-ok" : "chip-warn"}`}>
                {connected ? "Runtime live" : "Runtime offline"}
              </span>
              <span className="chip chip-info">{config.platform}</span>
              {config.isWsl ? <span className="chip chip-info">WSL</span> : null}
              {_isMobile ? <span className="chip chip-info">Mobile</span> : null}
              {cam.status === "live" ? <span className="chip chip-ok">Camera live</span> : null}
              {cam.inferencing ? <span className="chip chip-ok">Inferencing</span> : null}
            </div>
          </div>
          <div className="mode-tabs" role="tablist">
            {config.options.map((opt) => (
              <button
                key={opt.mode}
                type="button"
                role="tab"
                aria-selected={cam.mode === opt.mode}
                className={`mode-tab ${cam.mode === opt.mode ? "active" : ""} ${opt.recommended ? "recommended" : ""}`}
                onClick={() => {
                  if (cam.inferencing) cam.setInferencing(false);
                  void cam.startPreview(opt.mode);
                }}
                title={MODE_HINTS[opt.mode]}
              >
                {MODE_LABELS[opt.mode]}
                {opt.recommended ? <span className="rec-badge">auto</span> : null}
                {!opt.available ? <span className="unavail-badge">n/a</span> : null}
              </button>
            ))}
          </div>
          <p className="meta mode-hint">{MODE_HINTS[cam.mode]} Recommended: {config.options.find((o) => o.recommended)?.mode}.</p>
        </section>

        {showWslHint ? (
          <div className="alert alert-warn">
            <strong>WSL:</strong> Use <button type="button" className="linkish" onClick={() => void cam.startPreview("bridge")}>Windows bridge</button>{" "}
            — run <code>scripts/webcam/start_webcam_bridge.ps1</code> in PowerShell on Windows.
          </div>
        ) : null}

        <section className="card camera-card">
          <div className="card-head">
            <div>
              <h2>Live perception</h2>
              <p className="meta">
                Preview is automatic. Start/Stop only gate the inference loop.
              </p>
            </div>
          </div>

          <div className="video-stage">
            <video
              ref={cam.videoRef}
              autoPlay
              playsInline
              muted
              className={`video-feed ${cam.mode === "browser" && cam.status !== "idle" ? "" : "hidden-feed"}`}
            />
            <img
              ref={cam.bridgeImgRef}
              src={cam.status === "idle" ? undefined : cam.bridgeUrl}
              crossOrigin="anonymous"
              alt="Webcam bridge stream"
              className={`video-feed ${cam.mode === "bridge" && cam.status !== "idle" ? "" : "hidden-feed"}`}
            />
            {cam.mode === "server" && cam.status === "live" ? (
              <div className="video-placeholder overlay-placeholder">
                <p>Server capture active</p>
                <p className="meta">Runtime OpenCV reads the camera / bridge stream.</p>
              </div>
            ) : null}
            {cam.status === "idle" ? (
              <div className="video-placeholder">
                <p>Camera preview</p>
                <p className="meta">
                  {_isMobile
                    ? "Starting phone camera…"
                    : cam.mode === "bridge"
                    ? "Starting bridge stream…"
                    : "Starting browser camera…"}
                </p>
              </div>
            ) : null}
            {cam.mode !== "server" && cam.status === "live" ? (
              <canvas ref={cam.overlayRef} className="video-overlay" />
            ) : null}
            <canvas ref={cam.canvasRef} hidden />
            {cam.status === "starting" ? (
              <div className="video-overlay-msg">
                <div className="spinner" />
                <p>Starting preview…</p>
              </div>
            ) : null}
          </div>

          {(cam.error || runtimeError) && <div className="alert alert-error">{cam.error || runtimeError}</div>}
          {snack ? <div className="alert alert-warn">{snack}</div> : null}

          <div className="toolbar">
            <button
              type="button"
              className={`btn ${cam.inferencing ? "" : "primary"}`}
              onClick={() => void toggleInference()}
              disabled={cam.status !== "live"}
            >
              {cam.inferencing ? "Stop inference" : "Start inference"}
            </button>
            <button
              type="button"
              className="btn ghost"
              onClick={async () => {
                const r = await fetch(`${runtimeUrl()}/live/retrain`, { method: "POST" });
                setRetrainMsg(JSON.stringify(await r.json(), null, 2));
              }}
              disabled={cam.inferencing}
            >
              Retrain
            </button>
            <button type="button" className="btn ghost" onClick={() => void config.redetect()}>
              Re-detect
            </button>
          </div>
          {retrainMsg ? <pre className="code-block">{retrainMsg}</pre> : null}
        </section>
      </div>

      <aside className="studio-rail">
        <section className="card prediction-hero">
          {prediction ? (
            <>
              <p className="eyebrow">Current intent</p>
              <h2 className="intent-title">{INTENT_LABELS[prediction.intent] || prediction.intent}</h2>
              <p className="intent-sub">
                {emotionLabel} · {behaviorLabel}
              </p>
              <div className="prediction-row">
                <ConfidenceRing
                  pct={Math.round(prediction.confidence * 100)}
                  color={prediction.gate === "pass" ? "#3dd68c" : prediction.gate === "reject" ? "#f07178" : "#f0c674"}
                />
                <div>
                  <p className="gate-label">
                    Gate: <span className={`gate-${prediction.gate}`}>{prediction.gate}</span>
                  </p>
                  <p className="meta">Dog detected: {prediction.dog_present ? "yes" : "no"}</p>
                  <p className="meta">Margin: {(prediction.margin ?? 0).toFixed(3)}</p>
                </div>
              </div>
              <div className="confidence-history">
                <span className="meta">Confidence history</span>
                <Sparkline points={confidenceHistory} height={40} />
              </div>
            </>
          ) : (
            <p className="meta">Point the camera at your dog — predictions appear here once inference starts.</p>
          )}
        </section>

        <section className="card">
          <h3>Intent probabilities</h3>
          {intentBars.length ? (
            <div className="signal-grid">
              {intentBars.map(({ key, label, value }) => (
                <div key={key} className="signal">
                  <span>{label}</span>
                  <div className="signal-bar">
                    <div style={{ width: `${Math.min(100, value * 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="meta">Waiting for predictions…</p>
          )}
        </section>

        <section className="card">
          <h3>Streaming metrics</h3>
          <div className="metric-grid">
            <div className="metric-tile"><span className="meta">FPS</span><strong>{(streamStatus?.fps ?? liveStatus?.fps ?? 0).toFixed(1)}</strong></div>
            <div className="metric-tile"><span className="meta">Infer ms</span><strong>{streamStatus?.avg_infer_ms ?? liveStatus?.avg_infer_ms ?? "—"}</strong></div>
            <div className="metric-tile"><span className="meta">Frames</span><strong>{streamStatus?.frames ?? liveStatus?.frames ?? 0}</strong></div>
            <div className="metric-tile"><span className="meta">Predictions</span><strong>{streamStatus?.predictions ?? liveStatus?.predictions ?? 0}</strong></div>
            <div className="metric-tile"><span className="meta">Sequence</span><strong>{streamStatus?.sequence_len ?? 0}/{streamStatus?.sequence_capacity ?? 15}</strong></div>
            <div className="metric-tile"><span className="meta">Uptime</span><strong>{Math.round(streamStatus?.uptime_s ?? 0)}s</strong></div>
          </div>
        </section>

        <section className="card">
          <h3>Modality signals</h3>
          {modalityGroups.length ? (
            modalityGroups.map((g) => (
              <div key={g.group} className="modality-group">
                <p className="eyebrow">{g.group}</p>
                <SignalBars signals={g.signals} />
              </div>
            ))
          ) : (
            <p className="meta">No signal data yet.</p>
          )}
        </section>

        <section className="card">
          <h3>Sequence tokenization</h3>
          <p className="meta">Rolling {prediction?.sequence?.length ?? 0}-frame feature window fed to TriadNet.</p>
          <TokenHeatmap
            sequence={prediction?.sequence ?? []}
            featureNames={FEATURE_NAMES}
            featureRows={TOKEN_FEATURES}
            height={110}
          />
        </section>

        <section className="card">
          <h3>Speech & voice</h3>
          {voice.enabled === false ? (
            <p className="meta">Voice engine not enabled on runtime (VOICE_ENABLED=1).</p>
          ) : (
            <>
              {prediction?.voice?.phrase ? (
                <div className="voice-now">
                  <p className="meta">Last spoken phrase</p>
                  <p className="voice-phrase">“{prediction.voice.phrase}”</p>
                </div>
              ) : null}
              {voice.enabled && Object.keys(voice.weights).length ? (
                <>
                  <p className="meta">Learned phrase weights</p>
                  <div className="signal-grid">
                    {Object.entries(voice.weights)
                      .sort((a, b) => b[1] - a[1])
                      .slice(0, 6)
                      .map(([phrase, w]) => (
                        <div key={phrase} className="signal">
                          <span>{phrase}</span>
                          <div className="signal-bar">
                            <div style={{ width: `${Math.min(100, (w / 2) * 100)}%` }} />
                          </div>
                        </div>
                      ))}
                  </div>
                </>
              ) : null}
              {voice.outcomes.length ? (
                <>
                  <p className="meta">Recent bark outcomes</p>
                  <ul className="outcome-list">
                    {voice.outcomes.slice(0, 4).map((o) => (
                      <li key={o.id}>
                        <span className="outcome-phrase">{o.phrase}</span>
                        <span className={`chip ${o.responded ? "chip-ok" : "chip-warn"}`}>
                          {o.responded ? `bark ${o.bark_valence ?? ""}` : "silent"}
                        </span>
                      </li>
                    ))}
                  </ul>
                </>
              ) : null}
            </>
          )}
        </section>

        <section className="card">
          <h3>Dog profile</h3>
          {profile ? (
            <>
              <p className="intent-sub">
                {profile.name || profile.dog_id}
                {profile.breed ? ` · ${profile.breed}` : ""}
              </p>
              <p className="eyebrow">{profile.personality}</p>
              <div className="trait-grid">
                {(profile.trait_keys ?? Object.keys(profile.traits)).map((k) => (
                  <div key={k} className="trait-row">
                    <span>{TRAIT_LABELS[k] || k}</span>
                    <div className="trait-pips">
                      {Array.from({ length: 10 }, (_, i) => (
                        <span key={i} className={`pip ${i < (profile.traits[k] ?? 0) ? "on" : ""}`} />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="meta">No profile yet.</p>
          )}
        </section>

        <section className="card">
          <h3>Correct the model</h3>
          <div className="feedback-grid">
            <button type="button" className="btn good" onClick={() => sendFeedback(1)} disabled={!prediction}>Correct</button>
            <button type="button" className="btn bad" onClick={() => sendFeedback(-1)} disabled={!prediction}>Wrong</button>
            <button type="button" className="btn" onClick={() => sendFeedback(1, "outside")} disabled={!prediction}>Fix: outside</button>
            <button type="button" className="btn" onClick={() => sendFeedback(1, "play")} disabled={!prediction}>Fix: play</button>
            <button type="button" className="btn" onClick={() => sendFeedback(1, "food")} disabled={!prediction}>Fix: food</button>
          </div>
        </section>
      </aside>
    </div>
  );
}
