#!/usr/bin/env bash
# Build the studio web UI and host it (rohomieo-style) from the runtime server.
# Any device on the same Wi-Fi can open http://<lan-ip>:8765
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

cd apps/aarf-studio
if [ ! -d node_modules ]; then npm ci; fi
npm run build
cd "$ROOT"

exec ./scripts/run_runtime.sh
