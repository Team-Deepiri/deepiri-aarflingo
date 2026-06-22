#!/usr/bin/env bash
# Multimodal Aarflingo training: vision (YOLO) → audio → physio → TriadNet fusion.
#
#   ./scripts/train_aarflingo.sh
#   STAGES=physio,triad ./scripts/train_aarflingo.sh
#   SKIP_VISION=1 ./scripts/train_aarflingo.sh   # skip YOLO download (CI / offline)
#
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

EPOCHS="${EPOCHS:-30}"
AUDIO_EPOCHS="${AUDIO_EPOCHS:-20}"
PHYSIO_EPOCHS="${PHYSIO_EPOCHS:-20}"
STAGES="${STAGES:-vision,audio,physio,triad}"
SKIP_VISION="${SKIP_VISION:-0}"

CKPT="$ROOT/artifacts/models/default/triad.pt"
ONNX_DIR="$ROOT/artifacts/bundles/default/studio"
MANIFEST="$ROOT/artifacts/manifests/aarflingo-multimodal.json"
STAGE_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGE_DIR"' EXIT

mkdir -p "$(dirname "$CKPT")" "$ONNX_DIR" "$ROOT/artifacts/manifests" "$ROOT/artifacts/models/vision"

if [ -t 1 ]; then
  G="$(printf '\033[32m')"; B="$(printf '\033[1m')"; R="$(printf '\033[0m')"
else
  G=""; B=""; R=""
fi
step() { printf '%s\n' "${G}==>${R} ${B}$*${R}"; }

stage_enabled() {
  case ",$STAGES," in
    *,"$1",*) return 0 ;;
    *) return 1 ;;
  esac
}

run_stage_json() {
  local out_file="$1"
  shift
  "$@" >"$out_file"
  cat "$out_file"
}

echo '{"skipped":true}' >"$STAGE_DIR/vision.json"
echo '{"skipped":true}' >"$STAGE_DIR/audio.json"
echo '{"skipped":true}' >"$STAGE_DIR/physio.json"
echo '{}' >"$STAGE_DIR/triad_train.json"
echo '{}' >"$STAGE_DIR/triad_export.json"
echo '{}' >"$STAGE_DIR/verify.json"

if stage_enabled vision && [ "$SKIP_VISION" != "1" ]; then
  step "vision — YOLOv8 dog detector (COCO pretrained)"
  pushd "$ROOT/services/perception" >/dev/null
  poetry install --no-interaction --no-ansi -E yolo >&2
  export PYTHONPATH="$ROOT:$PWD"
  run_stage_json "$STAGE_DIR/vision.json" poetry run aarflingo-perception prepare-vision
  popd >/dev/null
elif stage_enabled vision; then
  step "vision — skipped (SKIP_VISION=1)"
fi

if stage_enabled audio; then
  step "audio — vocal encoder (DogSpeak / Barkopedia-shaped)"
  pushd "$ROOT/services/audio" >/dev/null
  poetry install --no-interaction --no-ansi >&2
  export PYTHONPATH="$ROOT:$PWD"
  run_stage_json "$STAGE_DIR/audio.json" poetry run aarflingo-audio train --epochs "$AUDIO_EPOCHS"
  popd >/dev/null
fi

if stage_enabled physio; then
  step "physio — ECG/IMU vitals encoder (PhysioZoo / Mendeley-shaped)"
  pushd "$ROOT/lib/aarf-physio" >/dev/null
  poetry install --no-interaction --no-ansi >&2
  run_stage_json "$STAGE_DIR/physio.json" poetry run aarf-physio train --epochs "$PHYSIO_EPOCHS"
  popd >/dev/null
fi

if stage_enabled triad; then
  step "triad — multimodal TriadNet (${EPOCHS} epochs)"
  pushd "$ROOT/services/forecast" >/dev/null
  export PYTHONPATH="$ROOT:$PWD"
  poetry install --no-interaction --no-ansi >&2
  run_stage_json "$STAGE_DIR/triad_train.json" poetry run aarflingo-forecast train --epochs "$EPOCHS" --out "$CKPT"
  popd >/dev/null

  step "export TriadNet ONNX"
  pushd "$ROOT/services/forecast" >/dev/null
  export PYTHONPATH="$ROOT:$PWD"
  run_stage_json "$STAGE_DIR/triad_export.json" poetry run aarflingo-forecast export-onnx --out "$ONNX_DIR"
  popd >/dev/null

  step "verify all model artifacts + live inference"
  pushd "$ROOT/services/forecast" >/dev/null
  export PYTHONPATH="$ROOT:$PWD"
  run_stage_json "$STAGE_DIR/verify.json" poetry run python "$ROOT/scripts/verify_artifacts.py"
  popd >/dev/null
fi

python3 - "$STAGE_DIR" "$MANIFEST" "$EPOCHS" "$AUDIO_EPOCHS" "$PHYSIO_EPOCHS" "$STAGES" "$ROOT" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

stage_dir, manifest_path, epochs, audio_e, physio_e, stages, root_s = sys.argv[1:8]
root = Path(root_s)
payload = {
    "bundle_id": "aarflingo-multimodal",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "stages": stages.split(","),
    "epochs": {"triad": int(epochs), "audio": int(audio_e), "physio": int(physio_e)},
    "artifacts": {
        "triad_pt": str(root / "artifacts/models/default/triad.pt"),
        "triad_onnx": str(root / "artifacts/bundles/default/studio/triad.onnx"),
        "vocal_pt": str(root / "artifacts/models/default/vocal.pt"),
        "vitals_pt": str(root / "artifacts/models/default/vitals.pt"),
        "dog_yolo_onnx": str(root / "artifacts/bundles/default/studio/dog_yolo.onnx"),
        "dog_yolo_weights": str(root / "artifacts/models/vision/yolov8n.pt"),
    },
}
for name in ("vision", "audio", "physio", "triad_train", "triad_export", "verify"):
    p = Path(stage_dir) / f"{name}.json"
    if p.is_file():
        try:
            payload[name] = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload[name] = {"raw": p.read_text(encoding="utf-8")}
Path(manifest_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(f"wrote {manifest_path}")
PY

echo "aarflingo multimodal training complete"
echo "manifest: $MANIFEST"
