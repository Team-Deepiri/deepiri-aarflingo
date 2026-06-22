#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> core metrics"
python3 core/metrics/test_anticipate.py

echo "==> perception pipeline"
cd services/perception
PYTHONPATH="$ROOT:$PWD" poetry run pytest -q 2>/dev/null || PYTHONPATH="$ROOT:$PWD" python -m pytest -q

echo "==> forecast train + checkpoint"
cd "$ROOT/services/forecast"
PYTHONPATH="$ROOT:$PWD" poetry run aarflingo-forecast build-default

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
curl -sf http://127.0.0.1:8765/health >/dev/null && echo "runtime ok" || echo "runtime not running (start ./scripts/run_runtime.sh)"

echo "smoke ok"
