#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

do_commit() {
  local msg="$1"
  shift
  local has=0
  for p in "$@"; do
    if git status --porcelain -- "$p" 2>/dev/null | grep -q .; then
      has=1
      break
    fi
  done
  if [ "$has" -eq 0 ]; then
    for p in "$@"; do
      if [ -e "$p" ] && ! git ls-files --error-unmatch "$p" >/dev/null 2>&1; then
        has=1
        break
      fi
    done
  fi
  if [ "$has" -eq 1 ]; then
    git add "$@"
    git commit -m "$msg"
  fi
}

# --- core + ethogram ---
do_commit "feat(core): add feature vector spec" core/feature_spec.py
do_commit "feat(ethogram): outside play food intents" ethogram/intents.yaml
do_commit "feat(ethogram): coupling for demo intents" ethogram/coupling-matrix.json
do_commit "chore(infra): gaze zone defaults" infra/configs/zones.default.yaml

# --- perception (granular) ---
do_commit "feat(perception): OpenCV dog detection" services/perception/app/dog_detect.py
do_commit "feat(perception): frame codec" services/perception/app/frame_codec.py
do_commit "feat(perception): temporal motion tracker" services/perception/app/temporal.py
do_commit "feat(perception): gaze zones YAML" services/perception/app/gaze.py
do_commit "feat(perception): scene signals" services/perception/app/scene.py
do_commit "feat(perception): pose proxy from bbox" services/perception/app/pose.py
do_commit "feat(perception): face stress heuristics" services/perception/app/face.py
do_commit "feat(perception): feature dict builder" services/perception/app/features.py
do_commit "feat(perception): BGR pipeline entrypoint" services/perception/app/pipeline.py
do_commit "refactor(perception): relative imports" services/perception/app/face.py services/perception/app/gaze.py services/perception/app/pipeline.py services/perception/app/pose.py services/perception/app/temporal.py
do_commit "chore(perception): deps lock and gaze test" services/perception/pyproject.toml services/perception/tests/test_gaze.py services/perception/poetry.lock

# --- forecast ---
do_commit "feat(forecast): label loaders" services/forecast/app/labels.py
do_commit "feat(forecast): synthetic and feedback dataset" services/forecast/app/dataset.py
do_commit "feat(forecast): TriadNet model and heuristics" services/forecast/app/triad_model.py
do_commit "feat(forecast): coupling loss" services/forecast/app/losses.py
do_commit "feat(forecast): feature vectorize shim" services/forecast/app/features.py
do_commit "feat(forecast): train loop" services/forecast/app/train.py
do_commit "feat(forecast): infer and checkpoint load" services/forecast/app/infer.py
do_commit "refactor(forecast): relative imports" services/forecast/app/cli.py services/forecast/app/infer.py services/forecast/app/train.py services/forecast/app/triad_model.py
do_commit "feat(forecast): CLI build-default" services/forecast/app/cli.py services/forecast/pyproject.toml services/forecast/poetry.lock

# --- feedback ---
do_commit "feat(feedback): SQLite prediction store" services/feedback/app/store.py
do_commit "feat(feedback): export and metrics CLI" services/feedback/app/cli.py
do_commit "test(feedback): store roundtrip" services/feedback/tests/test_store.py
do_commit "chore(feedback): poetry project" services/feedback/pyproject.toml services/feedback/poetry.lock

# --- runtime ---
do_commit "feat(runtime): monorepo path setup" services/runtime/app/paths.py
do_commit "feat(runtime): isolated service package loader" services/runtime/app/engine.py
do_commit "feat(runtime): FastAPI live server" services/runtime/app/server.py
do_commit "feat(runtime): CLI entry" services/runtime/app/cli.py services/runtime/app/__init__.py
do_commit "chore(runtime): poetry deps" services/runtime/pyproject.toml services/runtime/poetry.lock
do_commit "test(runtime): gate and process_frame" services/runtime/tests/test_engine.py

# --- edge + bridge ---
do_commit "feat(edge): Jetson inference loop" services/edge-runtime/app/loop.py
do_commit "feat(edge): edge CLI" services/edge-runtime/app/cli.py services/edge-runtime/pyproject.toml services/edge-runtime/poetry.lock
do_commit "feat(artifact-bridge): ONNX export" services/artifact-bridge/app/export_onnx.py services/artifact-bridge/pyproject.toml

# --- docker + ingest ---
do_commit "chore(docker): runtime image" infra/docker/runtime.Dockerfile
do_commit "chore(docker): jetson image" infra/docker/jetson.Dockerfile
do_commit "chore(docker): compose stack" infra/docker/docker-compose.yml
do_commit "feat(ingest): webcam capture session" services/ingest/app/webcam.py
do_commit "feat(ingest): webcam CLI commands" services/ingest/app/cli.py services/ingest/pyproject.toml

# --- studio ---
do_commit "feat(studio): useRuntimeLive hook" apps/aarf-studio/src/renderer/hooks/useRuntimeLive.ts
do_commit "feat(studio): CameraView live infer" apps/aarf-studio/src/renderer/components/CameraView.tsx
do_commit "feat(studio): IntentDashboard live" apps/aarf-studio/src/renderer/components/IntentDashboard.tsx
do_commit "feat(studio): HistoryView from API" apps/aarf-studio/src/renderer/components/HistoryView.tsx
do_commit "style(studio): layout tokens" apps/aarf-studio/src/renderer/styles.css apps/aarf-studio/.env.example

# --- docs + scripts ---
do_commit "docs: webcam live guide" docs/WEBCAM.md
do_commit "docs: deploy Jetson and Docker" docs/DEPLOY.md
do_commit "docs: product roadmap" docs/ROADMAP.md
do_commit "docs: README live workflow" README.md
do_commit "chore(scripts): setup and runtime launcher" scripts/setup.sh scripts/run_runtime.sh
do_commit "chore(scripts): smoke pipeline" scripts/smoke_pipeline.sh scripts/record-baseline.sh scripts/demo_protocol.sh
do_commit "chore(scripts): atomic commit helper" scripts/commit_batches.sh

# --- ci + hygiene ---
do_commit "ci: feedback runtime matrix" .github/workflows/ci.yml
do_commit "chore: gitignore artifacts and venv" .gitignore
do_commit "chore(lib): aarf-gate lockfile" lib/aarf-gate/package-lock.json

if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -m "chore: sync remaining files" || true
fi

echo "commits ahead of origin/main: $(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"
