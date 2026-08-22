#!/usr/bin/env bash
# Home data capture: webcam frames → model-assisted labels → ready to fine-tune.
#
#   ./scripts/home_capture.sh                 # auto-detect camera or WSL bridge
#   FRAMES=300 ./scripts/home_capture.sh
#   SOURCE=http://192.168.1.50:8766/video/stream ./scripts/home_capture.sh
#
# After this finishes: review data/dog/captures/labels.jsonl, then run the
# prep/finetune commands it prints (or `make home-train`).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FRAMES="${FRAMES:-200}"
OUT="${OUT:-data/dog/captures}"
SOURCE="${SOURCE:-}"

if [ ! -t 1 ]; then G=""; B=""; R=""; else
  G="$(printf '\033[32m')"; B="$(printf '\033[1m')"; R="$(printf '\033[0m')"
fi
step() { printf '%s\n' "${G}==>${R} ${B}$*${R}"; }

run_perc() { PYTHONPATH="$ROOT:$ROOT/services/perception" poetry run aarflingo-perception "$@"; }

step "capturing $FRAMES frames → $OUT"
run_perc capture-frames --out "$OUT" --frames "$FRAMES" ${SOURCE:+--source "$SOURCE"}

step "auto-labeling (COCO YOLO dog boxes, review before training)"
run_perc auto-label-dog --captures "$OUT"

cat <<EOF

${B}Captures ready for review:${R} $OUT
  1. Open ${B}$OUT/labels.jsonl${R} — fix/remove bad boxes (x,y = center, normalized 0–1).
     Frames with no box train as background; delete hopeless frames.
  2. Build + fine-tune the detector:
       ${B}make home-train${R}
     (runs prep-dog-yolo && finetune-dog-yolo → artifacts/models/vision/dog_yolo.onnx)
  3. Breed ID on your dog: drop stills in ${B}data/my_dog/breed/<Breed>/${R} then
       ${B}poetry run aarflingo-perception train-breed --extra-dir data/my_dog/breed${R}
  4. Restart the runtime so it picks up the new ONNX:
       ${B}./scripts/run_runtime.sh${R}
EOF
