import { contextBridge } from "electron";

contextBridge.exposeInMainWorld("aarf", {
  isElectron: true,
  runtimeUrl: process.env.VITE_RUNTIME_URL || "http://127.0.0.1:8765",
  bridgeUrl: process.env.VITE_WEBCAM_BRIDGE_URL || "http://127.0.0.1:8766/video/stream",
});
