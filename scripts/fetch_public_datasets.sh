#!/usr/bin/env bash
# Optional download helpers for public canine datasets (see docs/DATASETS.md).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data/raw"
mkdir -p "$DATA"

list() {
  cat <<'EOF'
Vision:  Stanford Dogs images.tar (real dog photos, ~750MB)   --dog-images
Vision:  ultralytics yolov8n (auto via train_aarflingo vision stage)
Audio:   huggingface ArlingtonCL2/BarkopediaDogEmotionClassification_Data  --barkopedia
Audio:   huggingface ArlingtonCL2/DogSpeak_Dataset (large)
Physio:  physionet.org/content/physiozoo/1.0.0/ (dog ECG, credentials required)
Physio:  zenodo.org/records/19383015 (dog HRV stress)
IMU:     data.mendeley.com/datasets/mpph6bmn7g/1
IMU:     data.mendeley.com/datasets/vxhx934tbn/3
EOF
}

fetch_dog_images() {
  local dest="$DATA/dog_images"
  local url="http://vision.stanford.edu/aditya86/ImageNetDogs/images.tar"
  if [ -d "$dest/images" ] && ls "$dest"/images/n0* >/dev/null 2>&1; then
    echo "Stanford Dogs already present at $dest/images"
    return
  fi
  if [ ! -f "$DATA/images.tar" ]; then
    echo "Downloading Stanford Dogs images.tar (~750MB) from $url"
    wget -c -O "$DATA/images.tar" "$url"
  fi
  mkdir -p "$dest"
  tar -xf "$DATA/images.tar" -C "$dest"
  echo "saved to $dest"
  echo "Next: poetry run aarflingo-perception collect-real --directory $dest"
}

fetch_dog_images_sample() {
  # A few real Stanford Dogs images by breed for a quick local sanity check.
  local dest="$DATA/dog_images"
  mkdir -p "$dest"
  python3 - "$dest" <<'PY'
import sys
from pathlib import Path
import urllib.request

dest = Path(sys.argv[1])
# Stanford Dogs sample: one well-known breed id per class is fetched from the
# official images server used by vision.stanford.edu/aditya86/ImageNetDogs.
urls = {
    "n02085620-Chihuahua": "http://vision.stanford.edu/aditya86/ImageNetDogs/thumbnails/n02085620-Chihuahua/n02085620_1001.jpg",
    "n02099601-Golden_retriever": "http://vision.stanford.edu/aditya86/ImageNetDogs/thumbnails/n02099601-Golden_retriever/n02099601_1001.jpg",
    "n02096051-Airedale": "http://vision.stanford.edu/aditya86/ImageNetDogs/thumbnails/n02096051-Airedale/n02096051_1001.jpg",
    "n02111889-Samoyed": "http://vision.stanford.edu/aditya86/ImageNetDogs/thumbnails/n02111889-Samoyed/n02111889_1001.jpg",
}
fetched = 0
for folder, url in urls.items():
    out_dir = dest / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / url.rsplit("/", 1)[1]
    if out.exists():
        fetched += 1
        continue
    try:
        with urllib.request.urlopen(url, timeout=20) as r, out.open("wb") as fh:
            fh.write(r.read())
        fetched += 1
    except Exception as exc:  # noqa: BLE001 - sample fetch is best-effort
        print(f"skip {folder}: {exc}", file=sys.stderr)
print(f"fetched {fetched}/{len(urls)} sample images into {dest}")
PY
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
  --dog-images) fetch_dog_images ;;
  --dog-images-sample) fetch_dog_images_sample ;;
  --barkopedia) fetch_barkopedia ;;
  --physiozoo-hint) fetch_physiozoo_hint ;;
  *)
    echo "Usage: $0 --list | --dog-images | --dog-images-sample | --barkopedia | --physiozoo-hint"
    exit 1
    ;;
esac
