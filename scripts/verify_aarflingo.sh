#!/usr/bin/env bash
# Run tests, train model artifacts, and prove runtime + studio work.
#
#   ./scripts/verify_aarflingo.sh
#   EPOCHS=12 ./scripts/verify_aarflingo.sh
#
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

step "unit tests (core + services + aarf-gate)"
python3 core/metrics/test_anticipate.py
PYTHONPATH="$ROOT" python3 -m pytest -q core/tests
for svc in ingest perception forecast feedback runtime; do
  (cd "services/$svc" && PYTHONPATH="$ROOT:$PWD" poetry run pytest -q)
done
(cd lib/aarf-gate && npm test -s)

step "train model + export ONNX + verify artifacts"
EPOCHS="${EPOCHS:-20}" bash "$ROOT/scripts/train_aarflingo.sh"

step "runtime live smoke"
RUNTIME_LOG="${TMPDIR:-/tmp}/aarflingo-runtime-verify.log"
(
  cd "$ROOT/services/runtime"
  export PYTHONPATH="$ROOT:$ROOT/services/runtime"
  poetry run aarflingo-runtime --host 127.0.0.1 --port 8765 >"$RUNTIME_LOG" 2>&1 &
  echo $!
) > "${TMPDIR:-/tmp}/aarflingo-runtime.pid"
RUNTIME_PID="$(cat "${TMPDIR:-/tmp}/aarflingo-runtime.pid")"

for _ in $(seq 1 60); do
  curl -sf http://127.0.0.1:8765/health >/dev/null 2>&1 && break
  sleep 0.5
done
curl -sf http://127.0.0.1:8765/health | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['ok']"
(cd "$ROOT/services/runtime" && PYTHONPATH="$ROOT:$PWD" poetry run pytest -q tests/test_server.py)

step "studio build"
bash "$ROOT/scripts/sync-branding.sh"
(cd apps/aarf-studio && npm run build -s)

kill "$RUNTIME_PID" 2>/dev/null || true
wait "$RUNTIME_PID" 2>/dev/null || true
RUNTIME_PID=""

step "aarflingo verify OK"
