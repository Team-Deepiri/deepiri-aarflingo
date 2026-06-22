#!/usr/bin/env bash
# Copy canonical branding from assets/ into AARF Studio public (favicon + Electron fallback).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/assets/branding/Aarflingo-logo.png"
DST="$ROOT/apps/aarf-studio/public"

if [ ! -f "$SRC" ]; then
  echo "error: missing $SRC" >&2
  exit 1
fi

mkdir -p "$DST"
cp "$SRC" "$DST/aarflingo-logo.png"
cp "$SRC" "$DST/logo.png"
echo "synced branding -> apps/aarf-studio/public/"
