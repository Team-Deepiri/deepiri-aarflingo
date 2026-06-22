import React, { useCallback, useEffect, useRef, useState } from "react";

import type { CaptureMode } from "../lib/platform";
import { postFrame, useCameraCapture } from "../hooks/useCameraCapture";
import { useRuntimeLive } from "../hooks/useRuntimeLive";
import { runtimeUrl } from "../lib/platform";

const INTENT_LABELS: Record<string, string> = {
  outside: "Wants outside",
  play: "Wants to play",
  food: "Wants food",
  avoid: "Needs space",
  rest: "Resting",
  explore: "Exploring",
};

const WORDS: Record<string, string> = {
  outside: "outside",
  play: "play",
  food: "food",
  avoid: "help",
  rest: "rest",
};

function speak(intent: string) {
  if (!("speechSynthesis" in window)) return;
  const text = WORDS[intent] || intent.replace(/_/g, " ");
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 1.05;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}

function IntentRing({ confidence, gate }: { confidence: number; gate: string }) {
  const pct = Math.round(confidence * 100);
  const color = gate === "pass" ? "#3dd68c" : gate === "reject" ? "#f07178" : "#f0c674";
  return (
    <div className="intent-ring" style={{ ["--pct" as string]: pct, ["--ring" as string]: color }}>
      <span>{pct}%</span>
    </div>
  );
}

export function CameraView() {
  const lastSpoke = useRef("");
  const [retrainMsg, setRetrainMsg] = useState("");
  const [captureMode, setCaptureMode] = useState<CaptureMode>("bridge");
  const { prediction, connected, error: runtimeError, health, startWebcam, stopWebcam, sendFeedback } =
    useRuntimeLive();

  const onFrame = useCallback(async (blob: Blob) => {
    await postFrame(blob);
  }, []);

  const cam = useCameraCapture(onFrame, prediction);

  useEffect(() => {
    if (cam.wsl) setCaptureMode("bridge");
  }, [cam.wsl]);

  useEffect(() => {
    if (!prediction || prediction.gate !== "pass" || prediction.confidence < 0.85) return;
    const key = `${prediction.intent}-${prediction.ts_ms}`;
    if (lastSpoke.current === key) return;
    lastSpoke.current = key;
    speak(prediction.intent);
  }, [prediction]);

  const handleStart = async () => {
    if (captureMode === "server") {
      await startWebcam({ mode: "server" });
    } else {
      await startWebcam({ mode: "browser" });
    }
    await cam.start(captureMode);
  };

  const handleStop = async () => {
    cam.stop();
    await stopWebcam();
  };

  const features = prediction?.features || {};
  const showWslHint = Boolean(health.wsl || cam.wsl) && captureMode !== "bridge";

  return (
    <div className="camera-layout">
      <div className="camera-main card">
        <div className="card-head">
          <div>
            <h2>Live perception</h2>
            <p className="meta">Webcam → TriadNet → speak intent when confidence is high</p>
          </div>
          <div className="status-chips">
            <span className={`chip ${connected ? "chip-ok" : "chip-warn"}`}>
              {connected ? "Runtime live" : "Runtime offline"}
            </span>
            {health.wsl || cam.wsl ? <span className="chip chip-info">WSL</span> : null}
            {cam.status === "live" ? <span className="chip chip-ok">Camera live</span> : null}
          </div>
        </div>

        {showWslHint ? (
          <div className="alert alert-warn">
            <strong>WSL:</strong> Use <button type="button" className="linkish" onClick={() => setCaptureMode("bridge")}>Windows bridge</button>{" "}
            — run <code>scripts/webcam/start_webcam_bridge.ps1</code> in PowerShell on Windows.
          </div>
        ) : null}

        <div className="mode-tabs" role="tablist">
          {(["bridge", "browser", "server"] as CaptureMode[]).map((m) => (
            <button
              key={m}
              type="button"
              role="tab"
              aria-selected={captureMode === m}
              className={captureMode === m ? "mode-tab active" : "mode-tab"}
              onClick={() => setCaptureMode(m)}
            >
              {m === "bridge" ? "WSL bridge" : m === "browser" ? "Browser cam" : "Server OpenCV"}
            </button>
          ))}
        </div>

        <div className="video-stage">
          <video
            ref={cam.videoRef}
            autoPlay
            playsInline
            muted
            className={`video-feed ${captureMode === "browser" && cam.status !== "idle" ? "" : "hidden-feed"}`}
          />
          <img
            ref={cam.bridgeImgRef}
            src={cam.status === "idle" ? undefined : cam.bridgeUrl}
            alt="Webcam bridge stream"
            className={`video-feed ${captureMode === "bridge" && cam.status !== "idle" ? "" : "hidden-feed"}`}
          />
          {captureMode === "server" && cam.status === "live" ? (
            <div className="video-placeholder overlay-placeholder">
              <p>Server capture active</p>
              <p className="meta">Runtime OpenCV reads the WSL bridge stream.</p>
            </div>
          ) : null}
          {cam.status === "idle" ? (
            <div className="video-placeholder">
              <p>Camera preview</p>
              <p className="meta">
                {captureMode === "bridge"
                  ? "Start bridge on Windows, then press Start here."
                  : "Press Start to begin live inference."}
              </p>
            </div>
          ) : null}
          {captureMode !== "server" && cam.status === "live" ? (
            <canvas ref={cam.overlayRef} className="video-overlay" />
          ) : null}
          <canvas ref={cam.canvasRef} hidden />
          {cam.status === "starting" ? (
            <div className="video-overlay-msg">
              <div className="spinner" />
              <p>Starting camera…</p>
            </div>
          ) : null}
        </div>

        {(cam.error || runtimeError) && <div className="alert alert-error">{cam.error || runtimeError}</div>}

        <div className="toolbar">
          <button type="button" className="btn primary" onClick={() => void handleStart()} disabled={cam.status === "live" || cam.status === "starting"}>
            Start
          </button>
          <button type="button" className="btn" onClick={() => void handleStop()} disabled={cam.status === "idle"}>
            Stop
          </button>
          <button
            type="button"
            className="btn ghost"
            onClick={async () => {
              const r = await fetch(`${runtimeUrl()}/live/retrain`, { method: "POST" });
              setRetrainMsg(JSON.stringify(await r.json(), null, 2));
            }}
          >
            Retrain
          </button>
        </div>
        {retrainMsg ? <pre className="code-block">{retrainMsg}</pre> : null}
      </div>

      <aside className="camera-side">
        <section className="card prediction-hero">
          {prediction ? (
            <>
              <p className="eyebrow">Current intent</p>
              <h2 className="intent-title">{INTENT_LABELS[prediction.intent] || prediction.intent}</h2>
              <p className="intent-sub">
                {prediction.emotion} · {prediction.behavior}
              </p>
              <div className="prediction-row">
                <IntentRing confidence={prediction.confidence} gate={prediction.gate} />
                <div>
                  <p className="gate-label">
                    Gate: <span className={`gate-${prediction.gate}`}>{prediction.gate}</span>
                  </p>
                  <p className="meta">Dog detected: {prediction.dog_present ? "yes" : "no"}</p>
                </div>
              </div>
            </>
          ) : (
            <p className="meta">Point the camera at your dog — waiting for first prediction…</p>
          )}
        </section>

        <section className="card">
          <h3>Modality signals</h3>
          <div className="signal-grid">
            {[
              ["Vision", features.vision_yolo_dog_conf],
              ["Audio arousal", features.audio_arousal],
              ["ECG stress", features.ecg_stress],
              ["IMU activity", features.imu_activity],
            ].map(([label, val]) => (
              <div key={label as string} className="signal">
                <span>{label}</span>
                <div className="signal-bar">
                  <div style={{ width: `${Math.min(100, Number(val || 0) * 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="card">
          <h3>Correct the model</h3>
          <div className="feedback-grid">
            <button type="button" className="btn good" onClick={() => sendFeedback(1)}>Correct</button>
            <button type="button" className="btn bad" onClick={() => sendFeedback(-1)}>Wrong</button>
            <button type="button" className="btn" onClick={() => sendFeedback(1, "outside")}>Fix: outside</button>
            <button type="button" className="btn" onClick={() => sendFeedback(1, "play")}>Fix: play</button>
            <button type="button" className="btn" onClick={() => sendFeedback(1, "food")}>Fix: food</button>
          </div>
        </section>
      </aside>
    </div>
  );
}
