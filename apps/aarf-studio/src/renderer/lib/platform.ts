export type CaptureMode = "browser" | "bridge" | "server";

export type DetectedPlatform = "mobile" | "electron" | "wsl" | "native";

export type BridgeInfo = {
  platform: string;
  wsl: boolean;
  windows_host: string;
  lan_ip: string;
  stream_url: string;
  health_url: string;
  internal_stream_url: string;
  start_windows: string;
};

export type DogProfile = {
  dog_id: string;
  name: string;
  breed: string;
  age_years: number;
  weight_kg: number;
  traits: Record<string, number>;
  personality: string;
  baseline_hr_bpm: number;
  baseline_tail_deg: number;
  notes: string;
  updated_ms: number;
  trait_keys?: string[];
  personalities?: string[];
};

export type LiveStatus = {
  running: boolean;
  session_id: string | null;
  dog_id: string;
  camera: string;
  frames: number;
  predictions: number;
  fps: number;
  avg_infer_ms: number;
  sequence_len: number;
  sequence_capacity: number;
  uptime_s: number;
};

export type VoiceOutcome = {
  id: string;
  ts_ms: number;
  phrase: string;
  intent: string;
  emotion: string;
  responded: boolean;
  bark_arousal: string | null;
  bark_valence: string | null;
  reward: number;
};

export function detectPlatform(): DetectedPlatform {
  if (typeof navigator === "undefined") return "native";
  const ua = navigator.userAgent.toLowerCase();
  if (isMobileBrowser()) return "mobile";
  if (ua.includes("electron")) return "electron";
  if (ua.includes("wsl") || ua.includes("microsoft-standard")) return "wsl";
  return "native";
}

export function isLikelyWsl(): boolean {
  if (typeof navigator === "undefined") return false;
  const ua = navigator.userAgent.toLowerCase();
  return ua.includes("wsl") || ua.includes("microsoft-standard");
}

/** True when running in a mobile browser (iOS Safari, Android Chrome, etc.) */
export function isMobileBrowser(): boolean {
  if (typeof navigator === "undefined") return false;
  return /android|iphone|ipad|ipod|mobile|opera mini|iemobile|wpdesktop/i.test(
    navigator.userAgent
  );
}

/** True when running inside Electron (desktop app, not a plain browser) */
export function isElectron(): boolean {
  return (
    typeof navigator !== "undefined" &&
    navigator.userAgent.toLowerCase().includes("electron")
  );
}

export function defaultBridgeUrl(): string {
  return import.meta.env.VITE_WEBCAM_BRIDGE_URL || "http://127.0.0.1:8766/video/stream";
}

export function runtimeUrl(): string {
  // Same-origin by default: the runtime server serves both the UI and the API,
  // so relative URLs work from any device on the LAN (rohomieo-style hosting).
  return import.meta.env.VITE_RUNTIME_URL || "";
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

export async function startBridgeOnServer(): Promise<boolean> {
  try {
    const res = await fetch(`${runtimeUrl()}/bridge/start`, { method: "POST" });
    if (!res.ok) return false;
    const data = await res.json();
    return Boolean(data.ok);
  } catch {
    return false;
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

export async function fetchDogProfile(): Promise<DogProfile | null> {
  try {
    const res = await fetch(`${runtimeUrl()}/dog/profile`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function saveDogProfile(patch: Partial<DogProfile>): Promise<DogProfile | null> {
  try {
    const res = await fetch(`${runtimeUrl()}/dog/profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.profile ?? null;
  } catch {
    return null;
  }
}

export async function fetchLiveStatus(): Promise<LiveStatus | null> {
  try {
    const res = await fetch(`${runtimeUrl()}/live/status`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchVoiceWeights(): Promise<Record<string, number>> {
  try {
    const res = await fetch(`${runtimeUrl()}/voice/weights`);
    if (!res.ok) return {};
    return res.json();
  } catch {
    return {};
  }
}

export async function fetchVoiceOutcomes(): Promise<VoiceOutcome[]> {
  try {
    const res = await fetch(`${runtimeUrl()}/voice/outcomes`);
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}
