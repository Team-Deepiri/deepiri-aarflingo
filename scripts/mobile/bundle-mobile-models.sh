#!/usr/bin/env bash
# Bundle the TriadNet model into Aarflingo Pocket (Android ONNX + iOS CoreML).
#
#   ./scripts/mobile/bundle-mobile-models.sh
#
# Produces:
#   apps/aarf-pocket-android/app/src/main/assets/models/triad.onnx
#   apps/aarf-pocket-android/app/src/main/assets/models/triad_manifest.json
#   apps/aarf-pocket-ios/AarflingoPocket/Models/models/triad_labels.json
#   apps/aarf-pocket-ios/AarflingoPocket/Models/models/Triad.mlpackage   (macOS)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [ -t 1 ]; then
  G="$(printf '\033[32m')"; B="$(printf '\033[1m')"; R="$(printf '\033[0m')"
else
  G=""; B=""; R=""
fi
step() { printf '%s\n' "${G}==>${R} ${B}$*${R}"; }

### 1. Export ONNX via forecast (same command as scripts/train_aarflingo.sh) ###
step "export TriadNet ONNX"
mkdir -p "artifacts/bundles/mobile"
poetry run aarflingo-forecast export-onnx --out artifacts/bundles/mobile >/dev/null
ONNX="artifacts/bundles/mobile/triad.onnx"
test -f "${ONNX}"
ls -la "${ONNX}"

### 2. Android assets ########################################################
step "copy into Android assets"
ANDROID_ASSETS="apps/aarf-pocket-android/app/src/main/assets/models"
mkdir -p "${ANDROID_ASSETS}"
cp "${ONNX}" "${ANDROID_ASSETS}/triad.onnx"

# Labels JSON read by OnDeviceEngine.kt at runtime (intents/emotions/behaviors).
step "build label manifest"
PYTHONPATH="$ROOT:$ROOT/services/forecast" poetry run python - <<PY
import json
import sys

sys.path.insert(0, "$ROOT/services/forecast")

from app.labels import (  # type: ignore[import-not-found]
    behavior_labels,
    emotion_labels,
    intent_labels,
)

labels = {
    "intents": intent_labels(),
    "emotions": emotion_labels(),
    "behaviors": behavior_labels(),
}
out = "$ROOT/artifacts/bundles/mobile/labels.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(labels, f, indent=2, ensure_ascii=False)
print(json.dumps({k: len(v) for k, v in labels.items()}))
PY
cp "artifacts/bundles/mobile/labels.json" "${ANDROID_ASSETS}/triad_manifest.json"

### 3. iOS bundle ############################################################
IOS_MODELS="apps/aarf-pocket-ios/AarflingoPocket/Models/models"
mkdir -p "${IOS_MODELS}"
cp "artifacts/bundles/mobile/labels.json" "${IOS_MODELS}/triad_labels.json"

if [[ "$(uname -s)" == "Darwin" ]]; then
  step "export CoreML (macOS only)"
  PYTHONPATH="$ROOT:$ROOT/services/forecast:$ROOT/services/artifact-bridge" \
    poetry run python -m app.cli export --out artifacts/bundles/mobile --target coreml >/dev/null || true
  CML="artifacts/bundles/mobile/triad.mlpackage"
  if [[ -d "${CML}" ]]; then
    rm -rf "${IOS_MODELS}/Triad.mlpackage"
    cp -R "${CML}" "${IOS_MODELS}/Triad.mlpackage"
    step "CoreML bundled → ${IOS_MODELS}/Triad.mlpackage"
  else
    echo "  CoreML export skipped on this machine (needs macOS + coremltools)."
    echo "  iOS still ships triad_labels.json; app falls back to WiFi runtime without the .mlpackage."
  fi
else
  echo "  Skipping CoreML .mlpackage (requires macOS + coremltools)."
  echo "  Android gets full on-device ONNX now; iOS falls back to the WiFi runtime until bundled on a Mac."
fi

step "mobile models bundled"
echo "  Android: ${ANDROID_ASSETS}/triad.onnx + triad_manifest.json"
echo "  iOS:     ${IOS_MODELS}/triad_labels.json"$( [[ "$(uname -s)" == "Darwin" && -d "${IOS_MODELS}/Triad.mlpackage" ]] && echo " + Triad.mlpackage" )
ls -la "${ANDROID_ASSETS}"