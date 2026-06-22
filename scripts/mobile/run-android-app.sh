#!/usr/bin/env bash
# Build, install, and launch Aarflingo Pocket on a connected emulator/device.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ANDROID_DIR="${ROOT}/apps/aarf-pocket-android"
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"
export ANDROID_HOME="${SDK}"
export ANDROID_SDK_ROOT="${SDK}"
export PATH="${SDK}/platform-tools:${SDK}/emulator:${PATH}"

"${ROOT}/scripts/mobile/run-android-emulator.sh" || true

if ! adb devices | grep -qE '\tdevice$'; then
  echo "No Android device/emulator connected."
  echo "WSL tip: run Android Emulator on Windows and connect with:"
  echo "  ${ROOT}/scripts/mobile/connect-windows-adb.sh"
  exit 1
fi

cd "${ANDROID_DIR}"
./gradlew installDebug --no-daemon
adb shell am start -n dev.deepiri.aarflingo/.MainActivity
echo "Aarflingo Pocket launched."
