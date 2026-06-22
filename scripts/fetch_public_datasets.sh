#!/usr/bin/env bash
# Optional download helpers for public canine datasets (see docs/DATASETS.md).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data/raw"
mkdir -p "$DATA"

list() {
  cat <<'EOF'
Vision:  ultralytics yolov8n (auto via train_aarflingo vision stage)
Audio:   huggingface ArlingtonCL2/BarkopediaDogEmotionClassification_Data
Audio:   huggingface ArlingtonCL2/DogSpeak_Dataset (large)
Physio:  physionet.org/content/physiozoo/1.0.0/ (dog ECG, credentials required)
Physio:  zenodo.org/records/19383015 (dog HRV stress)
IMU:     data.mendeley.com/datasets/mpph6bmn7g/1
IMU:     data.mendeley.com/datasets/vxhx934tbn/3
EOF
}

fetch_barkopedia() {
  if ! command -v huggingface-cli >/dev/null 2>&1; then
    python3 -m pip install --user "huggingface_hub[cli]"
    export PATH="${HOME}/.local/bin:${PATH}"
  fi
  huggingface-cli download ArlingtonCL2/BarkopediaDogEmotionClassification_Data \
    --repo-type dataset \
    --local-dir "$DATA/barkopedia" \
    --local-dir-use-symlinks False
  echo "saved to $DATA/barkopedia"
}

fetch_physiozoo_hint() {
  echo "PhysioZoo dog ECG: register at https://physionet.org/settings/credentials/"
  echo "Then: wget -r -N -c -np --user USER --password PASS https://physionet.org/files/physiozoo/1.0.0/"
  echo "Place under: $DATA/physiozoo/"
}

case "${1:-}" in
  --list) list ;;
  --barkopedia) fetch_barkopedia ;;
  --physiozoo-hint) fetch_physiozoo_hint ;;
  *)
    echo "Usage: $0 --list | --barkopedia | --physiozoo-hint"
    exit 1
    ;;
esac
