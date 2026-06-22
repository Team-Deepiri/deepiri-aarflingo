export type CaptureMode = "browser" | "bridge" | "server";

export type BridgeInfo = {
  wsl: boolean;
  windows_host: string;
  stream_url: string;
  health_url: string;
  start_windows: string;
};

export function isLikelyWsl(): boolean {
  if (typeof navigator === "undefined") return false;
  const ua = navigator.userAgent.toLowerCase();
  return ua.includes("wsl") || ua.includes("microsoft-standard");
}

export function defaultBridgeUrl(): string {
  return import.meta.env.VITE_WEBCAM_BRIDGE_URL || "http://127.0.0.1:8766/video/stream";
}

export function runtimeUrl(): string {
  return import.meta.env.VITE_RUNTIME_URL || "http://127.0.0.1:8765";
}

export async function fetchBridgeInfo(): Promise<BridgeInfo | null> {
  try {
    const res = await fetch(`${runtimeUrl()}/bridge/info`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function probeBridgeHealth(healthUrl: string): Promise<boolean> {
  try {
    const res = await fetch(healthUrl, { signal: AbortSignal.timeout(2500) });
    if (!res.ok) return false;
    const data = await res.json();
    return Boolean(data.video_available ?? data.status === "ok");
  } catch {
    return false;
  }
}
