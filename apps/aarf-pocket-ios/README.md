# Aarflingo Pocket (iOS)

SwiftUI companion app for on-the-go dog intent monitoring. **v0.1 is UI-only** — no CoreML inference yet.

## Requirements

- Xcode 15+ / iOS 16+
- macOS for Simulator (iOS Simulator does not run on Linux/WSL)

## Generate Xcode project

```bash
# macOS — install XcodeGen once: brew install xcodegen
cd apps/aarf-pocket-ios
./scripts/sync-branding.sh
xcodegen generate
open AarflingoPocket.xcodeproj
```

## Simulator (macOS)

```bash
./scripts/mobile/ios-simulator.sh
```

## WSL developers

iOS Simulator requires macOS. From WSL:

1. Validate project structure: `../../scripts/mobile/verify-ios.sh`
2. CI builds on `macos-latest` — see `.github/workflows/mobile.yml`
3. Use a Mac or cloud Mac for interactive Simulator testing

Branding sync copies `assets/branding/Aarflingo-logo.png` into the asset catalog.
