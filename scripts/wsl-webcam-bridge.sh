#!/usr/bin/env bash
# Start webcam bridge on Linux/WSL (works when /dev/video0 exists or use Windows PS script).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SOURCE="${SOURCE:-0}"
PORT="${PORT:-8766}"

python3 -m pip install -q -r "$ROOT/scripts/webcam/requirements.txt"
exec python3 "$ROOT/scripts/webcam/webcam_bridge.py" --source "$SOURCE" --port "$PORT" --host 0.0.0.0
