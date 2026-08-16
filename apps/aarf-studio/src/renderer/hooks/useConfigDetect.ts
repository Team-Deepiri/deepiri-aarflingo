import { useCallback, useEffect, useState } from "react";

import type { BridgeInfo, CaptureMode, DetectedPlatform } from "../lib/platform";
import { detectPlatform, fetchBridgeInfo, isElectron, isMobileBrowser, probeBridgeHealth } from "../lib/platform";

export type CaptureOption = {
  mode: CaptureMode;
  recommended: boolean;
  available: boolean;
  reason: string;
};

export function useConfigDetect() {
  const [platform, setPlatform] = useState<DetectedPlatform>(detectPlatform());
  const [bridgeInfo, setBridgeInfo] = useState<BridgeInfo | null>(null);
  const [bridgeHealthy, setBridgeHealthy] = useState<boolean | null>(null);
  const [probing, setProbing] = useState(true);

  const detect = useCallback(async () => {
    setProbing(true);
    setPlatform(detectPlatform());
    const info = await fetchBridgeInfo();
    setBridgeInfo(info);
    if (info) {
      const healthUrl = info.health_url || info.stream_url.replace("/video/stream", "/health");
      const healthy = await probeBridgeHealth(healthUrl);
      setBridgeHealthy(healthy);
    } else {
      setBridgeHealthy(false);
    }
    setProbing(false);
  }, []);

  useEffect(() => {
    void detect();
  }, [detect]);

  const mobile = isMobileBrowser();
  const electron = isElectron();
  const isWsl = platform === "wsl" || Boolean(bridgeInfo?.wsl);

  const options: CaptureOption[] = [
    {
      mode: "browser",
      recommended: !isWsl,
      available: !mobile || platform === "mobile",
      reason: mobile ? "Phone camera" : "Local webcam via this browser",
    },
    {
      mode: "bridge",
      recommended: isWsl,
      available: true,
      reason: bridgeHealthy === null
        ? "Probing Windows bridge…"
        : bridgeHealthy
        ? "Windows bridge reachable"
        : "Bridge script not running",
    },
    {
      mode: "server",
      recommended: false,
      available: !mobile,
      reason: electron ? "Runtime OpenCV on this machine" : "Runtime reads the camera (OpenCV)",
    },
  ];

  return {
    platform,
    bridgeInfo,
    bridgeHealthy,
    probing,
    mobile,
    electron,
    isWsl,
    options,
    redetect: detect,
  };
}
