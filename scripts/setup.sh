#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Python services"
for svc in ingest labeler perception forecast artifact-bridge feedback runtime edge-runtime; do
  if command -v poetry >/dev/null 2>&1; then
    (cd "services/$svc" && poetry install --no-interaction)
  else
    echo "poetry not found; install manually in services/$svc"
  fi
done

echo "==> default triad model"
if command -v poetry >/dev/null 2>&1; then
  (cd services/forecast && poetry run aarflingo-forecast build-default)
  (cd services/artifact-bridge && poetry run aarflingo-artifact-bridge export --out "$ROOT/artifacts/bundles/default/studio")
fi

echo "==> aarf-gate"
if command -v npm >/dev/null 2>&1; then
  (cd lib/aarf-gate && npm install && npm run build 2>/dev/null || npm test)
fi

echo "==> aarf-studio"
if command -v npm >/dev/null 2>&1; then
  (cd apps/aarf-studio && npm install)
fi

echo "setup complete — run: ./scripts/run_runtime.sh"
