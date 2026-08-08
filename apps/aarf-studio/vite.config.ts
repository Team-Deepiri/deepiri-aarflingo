import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const appRoot = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(appRoot, "../..");

export default defineConfig({
  plugins: [react()],
  root: ".",
  resolve: {
    alias: {
      "@brand": path.join(repoRoot, "assets/branding"),
    },
  },
  server: {
    fs: {
      allow: [repoRoot],
    },
    proxy: {
      "/runtime": {
        target: "http://127.0.0.1:8765",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/runtime/, ""),
      },
      "/bridge/info": {
        target: "http://127.0.0.1:8765",
        changeOrigin: true,
      },
      "/bridge": {
        target: "http://127.0.0.1:8766",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/bridge/, ""),
      },
      "/health": "http://127.0.0.1:8765",
      "/metrics": "http://127.0.0.1:8765",
      "/predictions": "http://127.0.0.1:8765",
      "/live": "http://127.0.0.1:8765",
      "/infer": "http://127.0.0.1:8765",
      "/feedback": "http://127.0.0.1:8765",
      "/voice": "http://127.0.0.1:8765",
      "/ws": {
        target: "ws://127.0.0.1:8765",
        ws: true,
      },
    },
  },
  build: {
    outDir: "dist",
  },
});
