#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Python services"
for svc in ingest labeler perception forecast artifact-bridge; do
  if command -v poetry >/dev/null 2>&1; then
    (cd "services/$svc" && poetry install --no-interaction)
  else
    echo "poetry not found; pip install typer in each service manually"
  fi
done

echo "==> aarf-gate"
if command -v npm >/dev/null 2>&1; then
  (cd lib/aarf-gate && npm install && npm run build)
fi

echo "==> aarf-studio"
if command -v npm >/dev/null 2>&1; then
  (cd apps/aarf-studio && npm install)
fi

echo "setup complete"
