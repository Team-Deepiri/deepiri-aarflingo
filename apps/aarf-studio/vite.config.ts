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
      "/bridge": {
        target: "http://127.0.0.1:8766",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/bridge/, ""),
      },
    },
  },
  build: {
    outDir: "dist",
  },
});
