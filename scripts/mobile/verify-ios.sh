#!/usr/bin/env bash
# Verify iOS project structure (full build requires macOS + Xcode).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IOS_DIR="${ROOT}/apps/aarf-pocket-ios"

echo "==> Aarflingo Pocket iOS verify"

required=(
  "${IOS_DIR}/project.yml"
  "${IOS_DIR}/AarflingoPocket/AarflingoPocketApp.swift"
  "${IOS_DIR}/AarflingoPocket/Views/RootTabView.swift"
)

for f in "${required[@]}"; do
  [[ -f "${f}" ]] || { echo "Missing: ${f}"; exit 1; }
done

if command -v xcodegen >/dev/null 2>&1; then
  echo "Running xcodegen..."
  (cd "${IOS_DIR}" && xcodegen generate)
  echo "Generated AarflingoPocket.xcodeproj"
else
  echo "xcodegen not installed — skipping .xcodeproj generation."
  echo "CI generates the project on macos-latest. On Mac: brew install xcodegen && cd apps/aarf-pocket-ios && xcodegen generate"
fi

if [[ "$(uname -s)" == "Darwin" ]] && command -v xcodebuild >/dev/null 2>&1; then
  (cd "${IOS_DIR}" && xcodegen generate 2>/dev/null || true)
  xcodebuild -project "${IOS_DIR}/AarflingoPocket.xcodeproj" -scheme AarflingoPocket -destination 'platform=iOS Simulator,name=iPhone 16' -quiet build
  echo "iOS simulator build OK."
else
  echo "iOS Simulator build skipped (requires macOS). Use GitHub Actions mobile workflow or a Mac."
fi

echo "iOS source verify OK."
