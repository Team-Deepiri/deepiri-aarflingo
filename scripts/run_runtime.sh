#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/services/runtime"
export PYTHONPATH="$ROOT:$ROOT/services/runtime"
poetry run aarflingo-runtime serve --host 127.0.0.1 --port 8765
