#!/usr/bin/env bash
#
# Deepiri AARFLingo — one-shot setup.
#
#   ./setup.sh              Install system deps, Python services, model, studio.
#   ./setup.sh --run        Install everything, then launch runtime + Electron.
#   ./setup.sh --skip-system  Skip apt/brew system package install.
#   ./setup.sh --kill       Stop runtime / Electron / Vite for this repo.
#   ./setup.sh --help       Show this help.
#
set -euo pipefail

if [ -t 1 ]; then
  BOLD="$(printf '\033[1m')"; GREEN="$(printf '\033[32m')"
  YELLOW="$(printf '\033[33m')"; RED="$(printf '\033[31m')"; RESET="$(printf '\033[0m')"
else
  BOLD=""; GREEN=""; YELLOW=""; RED=""; RESET=""
fi
info()  { printf '%s\n' "${GREEN}==>${RESET} ${BOLD}$*${RESET}"; }
warn()  { printf '%s\n' "${YELLOW}warning:${RESET} $*"; }
die()   { printf '%s\n' "${RED}error:${RESET} $*" >&2; exit 1; }

RUN=0
KILL=0
SKIP_SYSTEM=0
for arg in "$@"; do
  case "$arg" in
    --run) RUN=1 ;;
    --kill) KILL=1 ;;
    --skip-system) SKIP_SYSTEM=1 ;;
    --help|-h)
      sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) die "unknown option: $arg (try --help)" ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

PYTHON_SERVICES=(ingest labeler perception forecast artifact-bridge feedback runtime edge-runtime)

kill_repo_processes() {
  declare -A seen=()
  local -a pids=()
  local pid cmd line

  add_pid() {
    local p="$1"
    [[ "$p" =~ ^[0-9]+$ ]] || return
    [ "$p" -eq $$ ] && return
    [ "$p" -eq "$PPID" ] && return
    [ -n "${seen[$p]:-}" ] && return
    seen[$p]=1
    pids+=("$p")
  }

  matches_repo_process() {
    case "$1" in
      bash*|/bin/sh*|zsh*|*setup.sh*) return 1 ;;
      *"$REPO_ROOT/services/runtime"*) return 0 ;;
      *aarflingo-runtime*) return 0 ;;
      *"$REPO_ROOT/apps/aarf-studio"*) return 0 ;;
      *"$REPO_ROOT/node_modules/"*"electron"*) return 0 ;;
      *vite*"$REPO_ROOT/apps/aarf-studio"*) return 0 ;;
    esac
    return 1
  }

  while IFS= read -r line; do
    [ -n "$line" ] || continue
    pid="${line%% *}"
    cmd="${line#* }"
    matches_repo_process "$cmd" && add_pid "$pid"
  done < <(pgrep -af . 2>/dev/null || true)

  if [ "${#pids[@]}" -eq 0 ]; then
    info "No running AARFLingo processes found."
    return 0
  fi

  info "Stopping ${#pids[@]} process(es)..."
  for pid in "${pids[@]}"; do
    cmd="$(ps -p "$pid" -o args= 2>/dev/null || echo "(already exited)")"
    printf '  %s  %s\n' "$pid" "$cmd"
    kill "$pid" 2>/dev/null || true
  done
  sleep 0.5
  for pid in "${pids[@]}"; do
    kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
  done
  info "All AARFLingo processes stopped."
}

if [ "$KILL" -eq 1 ]; then
  kill_repo_processes
  exit 0
fi

install_system_deps() {
  if [ "$SKIP_SYSTEM" -eq 1 ]; then
    info "Skipping system package install (--skip-system)."
    return 0
  fi

  local os
  os="$(uname -s)"
  info "Checking system dependencies ($os)..."

  if [ "$os" = "Linux" ] && command -v apt-get >/dev/null 2>&1; then
    local pkgs=(
      python3 python3-pip python3-venv python3-dev
      curl ca-certificates git build-essential
      libgl1 libglib2.0-0
      libgtk-3-0 libgbm1 libnss3 libatk-bridge2.0-0 libdrm2
      libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2
      libasound2 libx11-xcb1 libxcb-dri3-0 libxshmfence1
    )
    if command -v sudo >/dev/null 2>&1 && [ "$EUID" -ne 0 ]; then
      sudo apt-get update -qq
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${pkgs[@]}"
    elif [ "$EUID" -eq 0 ]; then
      apt-get update -qq
      DEBIAN_FRONTEND=noninteractive apt-get install -y "${pkgs[@]}"
    else
      warn "sudo not available; install manually: ${pkgs[*]}"
    fi
  elif [ "$os" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    brew install python@3.11 node 2>/dev/null || brew install python node || true
  fi
}

ensure_node() {
  command -v node >/dev/null 2>&1 || die "Node.js is not installed. Install Node 18+ and re-run."
  command -v npm  >/dev/null 2>&1 || die "npm is not installed (ships with Node.js)."
  local major
  major="$(node -p 'process.versions.node.split(".")[0]')"
  if [ "$major" -lt 18 ]; then
    warn "Node $(node -v) detected; Node 18+ recommended."
  fi
  info "Node $(node -v), npm $(npm -v)"
}

ensure_python() {
  command -v python3 >/dev/null 2>&1 || die "python3 is not installed."
  info "Python $(python3 --version | cut -d' ' -f2)"
}

ensure_poetry() {
  if command -v poetry >/dev/null 2>&1; then
    info "Poetry $(poetry --version | awk '{print $2}')"
    return 0
  fi
  info "Installing Poetry via pip..."
  python3 -m pip install --user poetry
  export PATH="${HOME}/.local/bin:${PATH}"
  command -v poetry >/dev/null 2>&1 || die "Poetry install failed; add ~/.local/bin to PATH"
  info "Poetry $(poetry --version | awk '{print $2}')"
}

install_python_services() {
  local svc
  for svc in "${PYTHON_SERVICES[@]}"; do
    info "Poetry install: services/$svc"
    (cd "services/$svc" && poetry install --no-interaction --no-ansi)
  done
}

train_and_export() {
  info "Training default TriadNet checkpoint (first run ~1–2 min)..."
  (cd services/forecast && poetry run aarflingo-forecast build-default)
  info "Exporting ONNX bundle..."
  (cd services/forecast && poetry run aarflingo-forecast export-onnx --out "$REPO_ROOT/artifacts/bundles/default/studio")
}

install_js() {
  info "Installing aarf-gate..."
  (cd lib/aarf-gate && if [ -f package-lock.json ]; then npm ci; else npm install; fi)
  (cd lib/aarf-gate && npm test)

  info "Installing AARF Studio (Electron + Vite)..."
  (cd apps/aarf-studio && if [ -f package-lock.json ]; then npm ci; else npm install; fi)
}

wait_for_runtime() {
  local i
  for i in $(seq 1 60); do
    if curl -sf http://127.0.0.1:8765/health >/dev/null 2>&1; then
      info "Runtime API ready at http://127.0.0.1:8765"
      return 0
    fi
    sleep 0.5
  done
  die "Runtime did not become healthy on :8765 (check logs)"
}

electron_linux_flags() {
  if [ "$(uname -s)" = "Linux" ]; then
    local sandbox="apps/aarf-studio/node_modules/electron/dist/chrome-sandbox"
    if [ -f "$sandbox" ] && [ ! -u "$sandbox" ]; then
      warn "Electron sandbox not SUID; using --no-sandbox (common on WSL)."
      warn "Fix: sudo chown root:root $sandbox && sudo chmod 4755 $sandbox"
      export AARF_ELECTRON_NO_SANDBOX=1
    fi
  fi
}

run_stack() {
  electron_linux_flags
  mkdir -p "${TMPDIR:-/tmp}"
  local runtime_log="${TMPDIR:-/tmp}/deepiri-aarflingo-runtime.log"

  info "Starting AARF runtime in background..."
  (
    cd "$REPO_ROOT/services/runtime"
    export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/services/runtime"
    nohup poetry run aarflingo-runtime --host 127.0.0.1 --port 8765 \
      >"$runtime_log" 2>&1 &
    echo $! > "${TMPDIR:-/tmp}/deepiri-aarflingo-runtime.pid"
  )
  wait_for_runtime

  info "Launching Deepiri AARF Studio (Electron)..."
  info "Runtime logs: $runtime_log"
  info "Stop everything with: ${BOLD}./setup.sh --kill${RESET}"

  cd apps/aarf-studio
  export VITE_RUNTIME_URL="http://127.0.0.1:8765"
  npm run electron:dev
}

# --- main -------------------------------------------------------------------
install_system_deps
ensure_node
ensure_python
ensure_poetry
install_python_services
train_and_export
install_js

if [ "$RUN" -eq 1 ]; then
  run_stack
else
  info "Done. Launch with: ${BOLD}./setup.sh --run${RESET}"
  info "Or: make dev (web) · make electron · ./scripts/run_runtime.sh"
fi
