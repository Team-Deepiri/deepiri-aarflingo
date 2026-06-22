#!/usr/bin/env bash
# Quick smoke: perception + train artifacts + feedback (no long test suite).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> core metrics"
python3 core/metrics/test_anticipate.py

echo "==> perception"
cd services/perception
PYTHONPATH="$ROOT:$PWD" poetry run pytest -q

echo "==> train aarflingo model + verify artifacts"
cd "$ROOT"
SKIP_VISION=1 EPOCHS="${EPOCHS:-12}" bash "$ROOT/scripts/train_aarflingo.sh"

echo "==> feedback store"
cd "$ROOT/services/feedback"
PYTHONPATH="$ROOT:$PWD" poetry run python -c "
from app.store import FeedbackStore
from pathlib import Path
s = FeedbackStore(Path('$ROOT/artifacts/feedback/test.db'))
sid = s.start_session()
pid = s.log_prediction(sid, 'play', 'excited', 'play_bow', 0.9, {}, [[0.0]*20]*15)
s.add_feedback(pid, rating=1)
print(s.metrics())
"

echo "==> runtime health (if running)"
curl -sf http://127.0.0.1:8765/health >/dev/null && echo "runtime ok" || echo "runtime not running (./scripts/run_runtime.sh)"

echo "smoke ok"
