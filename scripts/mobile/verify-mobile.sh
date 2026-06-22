#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
"${ROOT}/scripts/mobile/setup-android-wsl.sh"
"${ROOT}/scripts/mobile/verify-ios.sh"
echo "Mobile verify complete."
