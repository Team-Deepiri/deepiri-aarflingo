import { useCallback, useEffect, useRef, useState } from "react";

import { fetchBridgeInfo, probeBridgeHealth, runtimeUrl } from "../lib/platform";

export type RuntimeHealth = {
  ok: boolean;
  checking: boolean;
  bridgeOk: boolean | null;
  bridgeProbing: boolean;
  wsl: boolean;
  bridgeUrl: string | null;
  httpLatency: number | null;
  wsLatency: number | null;
};

const RUNTIME = runtimeUrl();

function wsBase(url: string) {
  return url.replace(/^https/, "wss").replace(/^http/, "ws");
}

/**
 * Polls the runtime + bridge once per second and measures WS round-trip
 * latency. Used by the global header indicator so the user always sees whether
 * the runtime is reachable and whether the Windows bridge is up.
 */
export function useRuntimeHealth(intervalMs = 1000): RuntimeHealth {
  const [ok, setOk] = useState(false);
  const [checking, setChecking] = useState(true);
  const [bridgeOk, setBridgeOk] = useState<boolean | null>(null);
  const [bridgeProbing, setBridgeProbing] = useState(true);
  const [wsl, setWsl] = useState(false);
  const [bridgeUrl, setBridgeUrl] = useState<string | null>(null);
  const [httpLatency, setHttpLatency] = useState<number | null>(null);
  const [wsLatency, setWsLatency] = useState<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const probeBridge = useCallback(async () => {
    const info = await fetchBridgeInfo();
    if (!info) return;
    setWsl(Boolean(info.wsl));
    setBridgeUrl(info.stream_url);
    const url = info.health_url || info.stream_url.replace("/video/stream", "/health");
    setBridgeProbing(true);
    const healthy = await probeBridgeHealth(url);
    setBridgeOk(healthy);
    setBridgeProbing(false);
  }, []);

  const check = useCallback(async () => {
    try {
      const started = performance.now();
      const res = await fetch(`${RUNTIME}/health`);
      const body = await res.json();
      const ms = Math.round(performance.now() - started);
      setOk(Boolean(body?.ok));
      setHttpLatency(ms);
    } catch {
      setOk(false);
    }
    setChecking(false);
  }, []);

  const probeWs = useCallback(() => {
    try {
      const ws = new WebSocket(`${wsBase(RUNTIME)}/ws/live`);
      wsRef.current?.close();
      wsRef.current = ws;
      const t0 = performance.now();
      ws.onopen = () => {
        setWsLatency(Math.round(performance.now() - t0));
        ws.close();
      };
      ws.onerror = () => ws.close();
    } catch {
      // ignore — the HTTP poll defines `ok`
    }
  }, []);

  useEffect(() => {
    void check();
    void probeBridge();
    void probeWs();
    const id = window.setInterval(() => {
      void check();
      void probeWs();
    }, intervalMs);
    const bridgeId = window.setInterval(() => void probeBridge(), 5000);
    return () => {
      window.clearInterval(id);
      window.clearInterval(bridgeId);
      wsRef.current?.close();
    };
  }, [check, probeWs, probeBridge, intervalMs]);

  return { ok, checking, bridgeOk, bridgeProbing, wsl, bridgeUrl, httpLatency, wsLatency };
}