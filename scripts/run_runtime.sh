#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/services/runtime"
# 0.0.0.0 = host on LAN so phones/other devices on the same Wi-Fi can open http://<lan-ip>:8765
poetry run aarflingo-runtime --host 0.0.0.0 --port 8765
