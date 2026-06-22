#!/usr/bin/env bash
# Start (or reuse) an Android Virtual Device on WSL2.
set -euo pipefail

SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"
AVD_NAME="${AARF_AVD_NAME:-Aarflingo_Pixel_6}"
export ANDROID_HOME="${SDK}"
export ANDROID_SDK_ROOT="${SDK}"
export PATH="${SDK}/platform-tools:${SDK}/emulator:${SDK}/cmdline-tools/latest/bin:${PATH}"

if ! command -v emulator >/dev/null 2>&1; then
  echo "emulator not in PATH. Set ANDROID_HOME to your SDK root."
  exit 1
fi

if ! avdmanager list avd 2>/dev/null | grep -q "Name: ${AVD_NAME}"; then
  echo "Creating AVD ${AVD_NAME}..."
  echo "no" | avdmanager create avd -n "${AVD_NAME}" -k "system-images;android-35;google_apis;x86_64" -d pixel_6 2>/dev/null || {
    echo "Install system image first:"
    echo "  sdkmanager \"system-images;android-35;google_apis;x86_64\""
    echo "  sdkmanager \"platform-tools\" \"emulator\""
    exit 1
  }
fi

if adb devices 2>/dev/null | grep -qE 'emulator-[0-9]+\s+device'; then
  echo "Emulator already running."
  adb devices -l
  exit 0
fi

echo "Starting emulator ${AVD_NAME} (headless-friendly)..."
nohup emulator -avd "${AVD_NAME}" -no-snapshot-load -gpu swiftshader_indirect -no-audio >/tmp/aarf-emulator.log 2>&1 &
echo "Log: /tmp/aarf-emulator.log"

for i in $(seq 1 60); do
  if adb devices 2>/dev/null | grep -qE 'emulator-[0-9]+\s+device'; then
    echo "Emulator ready."
    adb devices -l
    exit 0
  fi
  sleep 2
done

echo "Timed out waiting for emulator. Check /tmp/aarf-emulator.log"
exit 1
