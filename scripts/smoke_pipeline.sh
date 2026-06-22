#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> core metrics"
python core/metrics/test_anticipate.py

echo "==> ingest capture"
cd services/ingest
PYTHONPATH=. python -m app.cli capture --out /tmp/aarf_clip.json
cat /tmp/aarf_clip.json

echo "==> perception pipeline"
cd "$ROOT/services/perception"
PYTHONPATH=. python -c "from app.pipeline import run_pipeline; print(run_pipeline(bytes([128]*64)))"

echo "==> forecast train"
cd "$ROOT/services/forecast"
PYTHONPATH=. python -m app.cli train

echo "smoke ok"
