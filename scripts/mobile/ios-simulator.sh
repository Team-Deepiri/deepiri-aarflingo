#!/usr/bin/env bash
# Build and run Aarflingo Pocket in iOS Simulator (macOS only).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IOS_DIR="${ROOT}/apps/aarf-pocket-ios"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "iOS Simulator requires macOS."
  exit 1
fi

cd "${IOS_DIR}"
./scripts/sync-branding.sh
xcodegen generate

DEVICE="${IOS_SIM_DEVICE:-iPhone 16}"
xcodebuild \
  -project AarflingoPocket.xcodeproj \
  -scheme AarflingoPocket \
  -destination "platform=iOS Simulator,name=${DEVICE}" \
  -configuration Debug \
  build

BUNDLE_ID="dev.deepiri.aarflingo-pocket"
xcrun simctl boot "${DEVICE}" 2>/dev/null || true
open -a Simulator
APP_PATH="$(find ~/Library/Developer/Xcode/DerivedData -name 'AarflingoPocket.app' -path '*/Build/Products/Debug-iphonesimulator/*' 2>/dev/null | head -1)"
if [[ -n "${APP_PATH}" ]]; then
  xcrun simctl install booted "${APP_PATH}"
  xcrun simctl launch booted "${BUNDLE_ID}"
fi
