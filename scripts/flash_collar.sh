#!/usr/bin/env bash
# Host-test and flash Aarflingo collar Rev-A firmware.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 -m pytest -q firmware/collar/test
cd "$ROOT/firmware/collar"
platformio run -t upload "$@"
