import { useCallback, useEffect, useRef, useState } from "react";

const RUNTIME = import.meta.env.VITE_RUNTIME_URL || "http://127.0.0.1:8765";

export type LivePrediction = {
  type?: string;
  prediction_id?: string;
  intent: string;
  emotion: string;
  behavior: string;
  confidence: number;
  gate: string;
  intent_probs?: Record<string, number>;
  dog_present?: boolean;
  features?: Record<string, number>;
  ts_ms?: number;
};

export function useRuntimeLive() {
  const [prediction, setPrediction] = useState<LivePrediction | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current) return;
    const ws = new WebSocket(RUNTIME.replace("http", "ws") + "/ws/live");
    wsRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
    };
    ws.onerror = () => setError("WebSocket error");
    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      if (data.type === "prediction") setPrediction(data);
      if (data.type === "error") setError(data.message);
    };
  }, []);

  const startWebcam = useCallback(async (camera = 0) => {
    const res = await fetch(`${RUNTIME}/live/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ camera, dog_id: "default" }),
    });
    return res.json();
  }, []);

  const stopWebcam = useCallback(async () => {
    await fetch(`${RUNTIME}/live/stop`, { method: "POST" });
  }, []);

  const sendFeedback = useCallback(
    async (rating: number, corrected_intent?: string) => {
      if (!prediction?.prediction_id) return;
      await fetch(`${RUNTIME}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prediction_id: prediction.prediction_id,
          rating,
          corrected_intent,
        }),
      });
    },
    [prediction]
  );

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  return { prediction, connected, error, startWebcam, stopWebcam, sendFeedback };
}
