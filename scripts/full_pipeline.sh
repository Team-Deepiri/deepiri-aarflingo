#!/usr/bin/env bash
# End-to-end verification: unit tests → train → ONNX → runtime API smoke.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -t 1 ]; then
  G="$(printf '\033[32m')"; B="$(printf '\033[1m')"; R="$(printf '\033[0m')"
else
  G=""; B=""; R=""
fi
step() { printf '%s\n' "${G}==>${R} ${B}$*${R}"; }

RUNTIME_PID=""
cleanup() {
  if [ -n "$RUNTIME_PID" ] && kill -0 "$RUNTIME_PID" 2>/dev/null; then
    kill "$RUNTIME_PID" 2>/dev/null || true
    wait "$RUNTIME_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

step "core metrics + math tests"
python3 core/metrics/test_anticipate.py
PYTHONPATH="$ROOT" python3 -m pytest -q core/tests

step "python service unit tests"
for svc in ingest perception forecast feedback runtime; do
  step "  pytest services/$svc"
  (cd "services/$svc" && PYTHONPATH="$ROOT:$PWD" poetry run pytest -q)
done

step "aarf-gate"
(cd lib/aarf-gate && npm test -s)

step "train TriadNet + export ONNX"
EPOCHS="${EPOCHS:-15}" bash "$ROOT/scripts/train_pipeline.sh"

step "runtime API smoke (start server)"
RUNTIME_LOG="${TMPDIR:-/tmp}/aarflingo-full-pipeline-runtime.log"
(
  cd "$ROOT/services/runtime"
  export PYTHONPATH="$ROOT:$ROOT/services/runtime"
  poetry run aarflingo-runtime --host 127.0.0.1 --port 8765 >"$RUNTIME_LOG" 2>&1 &
  echo $!
) > "${TMPDIR:-/tmp}/aarflingo-runtime.pid"
RUNTIME_PID="$(cat "${TMPDIR:-/tmp}/aarflingo-runtime.pid")"

for _ in $(seq 1 60); do
  if curl -sf http://127.0.0.1:8765/health >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done
curl -sf http://127.0.0.1:8765/health | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('ok')"

step "  runtime infer + feedback (pytest integration)"
(cd "$ROOT/services/runtime" && PYTHONPATH="$ROOT:$PWD" poetry run pytest -q tests/test_server.py)

step "studio build"
bash "$ROOT/scripts/sync-branding.sh"
(cd apps/aarf-studio && npm run build -s)

kill "$RUNTIME_PID" 2>/dev/null || true
wait "$RUNTIME_PID" 2>/dev/null || true
RUNTIME_PID=""

step "full pipeline OK"
