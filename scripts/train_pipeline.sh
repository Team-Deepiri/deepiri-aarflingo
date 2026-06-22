#!/usr/bin/env bash
# Deprecated alias — use train_aarflingo.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec "$ROOT/scripts/train_aarflingo.sh" "$@"
