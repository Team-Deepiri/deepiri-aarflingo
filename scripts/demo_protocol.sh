#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

./scripts/setup.sh
./scripts/record-baseline.sh dog-demo 78 32
./scripts/smoke_pipeline.sh

echo "Demo protocol complete — open apps/aarf-studio with npm run dev"
