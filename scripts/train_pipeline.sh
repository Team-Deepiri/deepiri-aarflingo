#!/usr/bin/env bash
# Full forecast training pipeline: train → metrics → ONNX export.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> train TriadNet (batched, val split, best checkpoint)"
cd services/forecast
export PYTHONPATH="$ROOT:$PWD"
poetry run aarflingo-forecast train --epochs "${EPOCHS:-30}" --out "$ROOT/artifacts/models/default/triad.pt"
TRAIN_JSON="$ROOT/artifacts/models/default/train_metrics.json"
if [ -f "$TRAIN_JSON" ]; then
  echo "==> metrics: $(cat "$TRAIN_JSON" | python3 -c "import json,sys; d=json.load(sys.stdin); print('best_val_acc', d.get('best_val_acc'))")"
fi

echo "==> export ONNX bundle"
cd "$ROOT/services/forecast"
export PYTHONPATH="$ROOT:$PWD"
poetry run aarflingo-forecast export-onnx --out "$ROOT/artifacts/bundles/default/studio"

echo "==> core math tests"
cd "$ROOT"
PYTHONPATH="$ROOT" python3 -m pytest -q core/tests

echo "train pipeline ok — checkpoint: artifacts/models/default/triad.pt"
