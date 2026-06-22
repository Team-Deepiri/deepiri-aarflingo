#!/usr/bin/env bash
# Delegate to repo-root setup (canonical entrypoint).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec "$ROOT/setup.sh" "$@"
