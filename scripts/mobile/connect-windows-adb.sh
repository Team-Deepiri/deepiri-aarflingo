#!/usr/bin/env bash
# Connect WSL adb to Android Emulator running on Windows host (common WSL2 setup).
set -euo pipefail

SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"
export PATH="${SDK}/platform-tools:${PATH}"

WIN_HOST=""
if grep -q microsoft /proc/version 2>/dev/null; then
  WIN_HOST="$(ip route show | awk '/default/ {print $3; exit}')"
fi

if [[ -z "${WIN_HOST}" ]]; then
  echo "Could not detect Windows host IP from WSL."
  exit 1
fi

echo "Windows host: ${WIN_HOST}"
adb kill-server 2>/dev/null || true
adb start-server
adb connect "${WIN_HOST}:5555" || true
adb devices -l
