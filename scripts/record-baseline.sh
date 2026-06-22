#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOG_ID="${1:-dog-demo}"
HR="${2:-80}"
TAIL="${3:-35}"
cd "$ROOT"
if command -v poetry >/dev/null 2>&1; then
  export PYTHONPATH="$ROOT:$ROOT/services/ingest"
  poetry run aarflingo-ingest baseline "$DOG_ID" --hr "$HR" --tail "$TAIL"
else
  PYTHONPATH=. python -m app.cli baseline "$DOG_ID" --hr "$HR" --tail "$TAIL"
fi
