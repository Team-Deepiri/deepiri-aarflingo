#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SRC="$ROOT/assets/branding/Aarflingo-logo.png"
DST="$ROOT/apps/aarf-pocket-ios/AarflingoPocket/Assets.xcassets/AarflingoLogo.imageset/Aarflingo-logo.png"
mkdir -p "$(dirname "$DST")"
cp "$SRC" "$DST"
echo "synced logo -> $DST"
