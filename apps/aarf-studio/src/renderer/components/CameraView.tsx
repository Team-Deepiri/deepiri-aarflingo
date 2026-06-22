import React, { useEffect, useRef, useState } from "react";
import { useRuntimeLive } from "../hooks/useRuntimeLive";

const WORDS: Record<string, string> = {
  outside: "outside",
  play: "play",
  food: "food",
  solicit_play: "play",
  approach: "come",
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

export function CameraView() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [localOn, setLocalOn] = useState(false);
  const [retrainMsg, setRetrainMsg] = useState("");
  const lastSpoke = useRef("");
  const { prediction, connected, error, startWebcam, stopWebcam, sendFeedback } = useRuntimeLive();

  useEffect(() => {
    if (!prediction || prediction.gate !== "pass" || prediction.confidence < 0.85) return;
    const key = `${prediction.intent}-${prediction.ts_ms}`;
    if (lastSpoke.current === key) return;
    lastSpoke.current = key;
    speak(prediction.intent);
  }, [prediction]);

  useEffect(() => {
    if (!localOn || !videoRef.current) return;
    let stream: MediaStream;
    navigator.mediaDevices
      .getUserMedia({ video: { width: 640, height: 480 }, audio: false })
      .then((s) => {
        stream = s;
        if (videoRef.current) videoRef.current.srcObject = s;
      })
      .catch((e) => console.error(e));
    return () => stream?.getTracks().forEach((t) => t.stop());
  }, [localOn]);

  // Push browser frames to runtime when local preview on
  useEffect(() => {
    if (!localOn) return;
    const id = setInterval(async () => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas || video.readyState < 2) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0);
      canvas.toBlob(async (blob) => {
        if (!blob) return;
        const fd = new FormData();
        fd.append("file", blob, "frame.jpg");
        await fetch(
          (import.meta.env.VITE_RUNTIME_URL || "http://127.0.0.1:8765") + "/infer/frame",
          { method: "POST", body: fd }
        );
      }, "image/jpeg", 0.75);
    }, 200);
    return () => clearInterval(id);
  }, [localOn]);

  return (
    <section className="card camera-panel">
      <h2>Live camera</h2>
      <p className="meta">
        Runtime: {connected ? "connected" : "disconnected"}
        {error ? ` — ${error}` : ""}
      </p>
      <div className="camera-row">
        <video ref={videoRef} autoPlay playsInline muted className="camera-feed" />
        <canvas ref={canvasRef} style={{ display: "none" }} />
        <aside className="prediction-panel">
          {prediction ? (
            <>
              <h3>{prediction.intent}</h3>
              <p>{prediction.emotion} · {prediction.behavior}</p>
              <p>{(prediction.confidence * 100).toFixed(0)}% · gate: {prediction.gate}</p>
            </>
          ) : (
            <p>Awaiting prediction…</p>
          )}
          <div className="feedback-row">
            <button type="button" onClick={() => sendFeedback(1)}>Correct</button>
            <button type="button" onClick={() => sendFeedback(-1)}>Wrong</button>
            <button type="button" onClick={() => sendFeedback(1, "outside")}>Fix: outside</button>
            <button type="button" onClick={() => sendFeedback(1, "play")}>Fix: play</button>
            <button type="button" onClick={() => sendFeedback(1, "food")}>Fix: food</button>
          </div>
        </aside>
      </div>
      <div className="toolbar">
        <button
          type="button"
          onClick={async () => {
            setLocalOn(true);
            await startWebcam(0);
          }}
        >
          Start webcam + runtime
        </button>
        <button
          type="button"
          onClick={async () => {
            setLocalOn(false);
            await stopWebcam();
          }}
        >
          Stop
        </button>
        <button
          type="button"
          onClick={async () => {
            const r = await fetch(
              (import.meta.env.VITE_RUNTIME_URL || "http://127.0.0.1:8765") + "/live/retrain",
              { method: "POST" }
            );
            const j = await r.json();
            setRetrainMsg(JSON.stringify(j));
          }}
        >
          Retrain from feedback
        </button>
      </div>
      {retrainMsg ? <pre className="meta">{retrainMsg}</pre> : null}
    </section>
  );
}
