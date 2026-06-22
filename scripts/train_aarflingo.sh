#!/usr/bin/env bash
# Train TriadNet, export ONNX, and verify artifacts bring Aarflingo to life.
#
#   ./scripts/train_aarflingo.sh
#   EPOCHS=20 ./scripts/train_aarflingo.sh
#
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

EPOCHS="${EPOCHS:-30}"
CKPT="$ROOT/artifacts/models/default/triad.pt"
ONNX_DIR="$ROOT/artifacts/bundles/default/studio"
METRICS="$ROOT/artifacts/models/default/train_metrics.json"

mkdir -p "$(dirname "$CKPT")" "$ONNX_DIR" "$ROOT/artifacts/manifests"

echo "==> train TriadNet (${EPOCHS} epochs, batched, val split)"
cd "$ROOT/services/forecast"
export PYTHONPATH="$ROOT:$PWD"
TRAIN_JSON="$(poetry run aarflingo-forecast train --epochs "$EPOCHS" --out "$CKPT")"
echo "$TRAIN_JSON"

echo "==> export ONNX for studio + edge"
EXPORT_JSON="$(poetry run aarflingo-forecast export-onnx --out "$ONNX_DIR")"
echo "$EXPORT_JSON"

echo "==> verify checkpoint, ONNX, and live inference"
cd "$ROOT/services/forecast"
export PYTHONPATH="$ROOT:$PWD"
VERIFY_JSON="$(poetry run python "$ROOT/scripts/verify_artifacts.py")"
echo "$VERIFY_JSON"
cd "$ROOT"

TMP_TRAIN="$(mktemp)"
TMP_VERIFY="$(mktemp)"
printf '%s\n' "$TRAIN_JSON" >"$TMP_TRAIN"
printf '%s\n' "$VERIFY_JSON" >"$TMP_VERIFY"
MANIFEST_OUT="$ROOT/artifacts/manifests/aarflingo-default.json"
python3 - "$TMP_TRAIN" "$TMP_VERIFY" "$MANIFEST_OUT" "$EPOCHS" "$ROOT" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

train_path, verify_path, manifest_path, epochs_s, root_s = sys.argv[1:6]
root = Path(root_s)
train = json.loads(Path(train_path).read_text(encoding="utf-8"))
verify = json.loads(Path(verify_path).read_text(encoding="utf-8"))
payload = {
    "bundle_id": "aarflingo-default",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "epochs": int(epochs_s),
    "train": train,
    "verify": verify,
    "paths": {
        "checkpoint": str(root / "artifacts/models/default/triad.pt"),
        "onnx": str(root / "artifacts/bundles/default/studio/triad.onnx"),
        "metrics": str(root / "artifacts/models/default/train_metrics.json"),
    },
}
out = Path(manifest_path)
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(f"wrote {out}")
PY
rm -f "$TMP_TRAIN" "$TMP_VERIFY"

echo "aarflingo trained — checkpoint: $CKPT"
echo "onnx bundle: $ONNX_DIR/triad.onnx"
echo "manifest: artifacts/manifests/aarflingo-default.json"
