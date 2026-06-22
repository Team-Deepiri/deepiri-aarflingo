import { useCallback, useEffect, useRef, useState } from "react";

import type { CaptureMode } from "../lib/platform";
import { defaultBridgeUrl, fetchBridgeInfo, probeBridgeHealth, runtimeUrl } from "../lib/platform";
import type { LivePrediction } from "./useRuntimeLive";

export type CameraStatus = "idle" | "starting" | "live" | "error";

export function useCameraCapture(
  onFrame: (blob: Blob) => Promise<void>,
  prediction: LivePrediction | null
) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const bridgeImgRef = useRef<HTMLImageElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [mode, setMode] = useState<CaptureMode>("browser");
  const [status, setStatus] = useState<CameraStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [bridgeUrl, setBridgeUrl] = useState(defaultBridgeUrl());
  const [bridgeOk, setBridgeOk] = useState(false);
  const [wsl, setWsl] = useState(false);

  useEffect(() => {
    fetchBridgeInfo().then((info) => {
      if (!info) return;
      setWsl(info.wsl);
      setBridgeUrl(info.stream_url);
      if (info.wsl) setMode("bridge");
    });
  }, []);

  const stopTracks = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }, []);

  const captureToBlob = useCallback(async (): Promise<Blob | null> => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    if (mode === "browser") {
      const video = videoRef.current;
      if (!video || video.readyState < 2 || !video.videoWidth) return null;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0);
    } else {
      const img = bridgeImgRef.current;
      if (!img || !img.naturalWidth) return null;
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      ctx.drawImage(img, 0, 0);
    }

    return new Promise((resolve) => {
      canvas.toBlob((b) => resolve(b), "image/jpeg", 0.8);
    });
  }, [mode]);

  const startBrowser = useCallback(async () => {
    stopTracks();
    setStatus("starting");
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "environment" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setStatus("live");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Camera permission denied";
      setError(msg);
      setStatus("error");
      throw e;
    }
  }, [stopTracks]);

  const startBridge = useCallback(async () => {
    setStatus("starting");
    setError(null);
    const info = await fetchBridgeInfo();
    const url = info?.stream_url || bridgeUrl;
    const health = info?.health_url || url.replace("/video/stream", "/health");
    const ok = await probeBridgeHealth(health);
    setBridgeOk(ok);
    if (!ok) {
      const hint = wsl || info?.wsl
        ? "Start scripts/webcam/start_webcam_bridge.ps1 in Windows PowerShell, then retry."
        : "Run ./scripts/wsl-webcam-bridge.sh or the Windows PowerShell bridge script.";
      setError(`Bridge not reachable at ${health}. ${hint}`);
      setStatus("error");
      return;
    }
    setBridgeUrl(`${url}${url.includes("?") ? "&" : "?"}t=${Date.now()}`);
    setStatus("live");
  }, [bridgeUrl, wsl]);

  const start = useCallback(
    async (nextMode: CaptureMode) => {
      setMode(nextMode);
      if (nextMode === "server") {
        setStatus("live");
        setError(null);
        return;
      }
      if (nextMode === "browser") await startBrowser();
      else await startBridge();
    },
    [startBrowser, startBridge]
  );

  const stop = useCallback(() => {
    stopTracks();
    if (videoRef.current) videoRef.current.srcObject = null;
    setStatus("idle");
    setError(null);
  }, [stopTracks]);

  // Frame push loop (browser + bridge client-side infer)
  useEffect(() => {
    if (status !== "live" || mode === "server") return;
    const id = window.setInterval(async () => {
      const blob = await captureToBlob();
      if (blob) await onFrame(blob);
    }, 180);
    return () => window.clearInterval(id);
  }, [status, mode, captureToBlob, onFrame]);

  // Keep overlay synced with visible feed
  useEffect(() => {
    if (status !== "live") return;
    const id = window.setInterval(() => {
      const overlay = overlayRef.current;
      const video = mode === "browser" ? videoRef.current : bridgeImgRef.current;
      const f = prediction?.features;
      if (!overlay || !video || !f?.dog_present) return;
      const w = mode === "browser" ? (video as HTMLVideoElement).videoWidth : (video as HTMLImageElement).naturalWidth;
      const h = mode === "browser" ? (video as HTMLVideoElement).videoHeight : (video as HTMLImageElement).naturalHeight;
      if (!w || !h) return;
      overlay.width = w;
      overlay.height = h;
      const ctx = overlay.getContext("2d");
      if (!ctx) return;
      ctx.clearRect(0, 0, w, h);
      const cx = (f.bbox_cx ?? 0) * w;
      const cy = (f.bbox_cy ?? 0) * h;
      const bw = (f.bbox_w ?? 0) * w;
      const bh = (f.bbox_h ?? 0) * h;
      ctx.strokeStyle = prediction?.gate === "pass" ? "#3dd68c" : "#f0c674";
      ctx.lineWidth = 3;
      ctx.strokeRect(cx - bw / 2, cy - bh / 2, bw, bh);
    }, 150);
    return () => window.clearInterval(id);
  }, [prediction, mode, status]);

  return {
    videoRef,
    bridgeImgRef,
    canvasRef,
    overlayRef,
    mode,
    setMode,
    status,
    error,
    bridgeUrl,
    bridgeOk,
    wsl,
    start,
    stop,
  };
}

export async function postFrame(blob: Blob): Promise<void> {
  const fd = new FormData();
  fd.append("file", blob, "frame.jpg");
  await fetch(`${runtimeUrl()}/infer/frame`, { method: "POST", body: fd });
}
