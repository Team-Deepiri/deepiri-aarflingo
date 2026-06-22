#!/usr/bin/env bash
# Start runtime API + Vite studio (web). Use `make electron` for desktop shell.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

./scripts/run_runtime.sh &
RUNTIME_PID=$!
trap 'kill $RUNTIME_PID 2>/dev/null || true' EXIT

for _ in $(seq 1 30); do
  if curl -sf http://127.0.0.1:8765/health >/dev/null; then
    break
  fi
  sleep 0.5
done

cd apps/aarf-studio
if [ ! -d node_modules ]; then npm ci; fi
npm run dev
