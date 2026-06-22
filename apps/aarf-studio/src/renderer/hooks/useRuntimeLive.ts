import { useCallback, useEffect, useRef, useState } from "react";

import { runtimeUrl } from "../lib/platform";

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

const RUNTIME = runtimeUrl();

export function useRuntimeLive() {
  const [prediction, setPrediction] = useState<LivePrediction | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<Record<string, unknown>>({});
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<number>(0);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    const ws = new WebSocket(RUNTIME.replace("http", "ws") + "/ws/live");
    wsRef.current = ws;
    ws.onopen = () => {
      setConnected(true);
      setError(null);
      retryRef.current = 0;
    };
    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
      const delay = Math.min(10_000, 1000 * 2 ** retryRef.current);
      retryRef.current += 1;
      window.setTimeout(connect, delay);
    };
    ws.onerror = () => setError("Runtime WebSocket error");
    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      if (data.type === "prediction") setPrediction(data);
      if (data.type === "error") setError(data.message);
    };
  }, []);

  const refreshHealth = useCallback(async () => {
    try {
      const res = await fetch(`${RUNTIME}/health`);
      setHealth(await res.json());
    } catch {
      setHealth({});
    }
  }, []);

  const startWebcam = useCallback(
    async (opts?: { camera?: number | string; mode?: "browser" | "server" | "bridge" }) => {
      if (opts?.mode === "browser") {
        connect();
        return { status: "browser" };
      }
      const res = await fetch(`${RUNTIME}/live/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          camera: opts?.camera ?? 0,
          dog_id: "default",
          mode: opts?.mode ?? "bridge",
        }),
      });
      const data = await res.json();
      connect();
      return data;
    },
    [connect]
  );

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
    refreshHealth();
    const id = window.setInterval(refreshHealth, 5000);
    return () => {
      window.clearInterval(id);
      wsRef.current?.close();
    };
  }, [connect, refreshHealth]);

  return {
    prediction,
    connected,
    error,
    health,
    startWebcam,
    stopWebcam,
    sendFeedback,
    refreshHealth,
  };
}
