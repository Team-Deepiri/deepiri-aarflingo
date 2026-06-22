# Mobile apps (WSL / macOS)

Aarflingo Pocket ships as native shells for **Android** (Kotlin + Jetpack Compose) and **iOS** (SwiftUI). ML inference is not wired yet — both apps use mock predictions and polished UI.

## Android on WSL2

Prerequisites:

- Android SDK at `~/Android/Sdk` (from Android Studio on Windows is fine)
- OpenJDK 17: `sudo apt install openjdk-17-jdk`
- `export ANDROID_HOME=$HOME/Android/Sdk`

```bash
# One-shot setup + debug APK build
./scripts/mobile/setup-android-wsl.sh

# Start emulator (WSL) or connect Windows emulator
./scripts/mobile/run-android-emulator.sh
./scripts/mobile/connect-windows-adb.sh   # if emulator runs on Windows host

# Install and launch
./scripts/mobile/run-android-app.sh
```

Emulator default runtime URL is `http://10.0.2.2:8765` (maps to host `localhost`).

## iOS (macOS only for Simulator)

iOS Simulator **cannot run on WSL/Linux**. Use a Mac or CI:

```bash
brew install xcodegen
cd apps/aarf-pocket-ios && xcodegen generate
open AarflingoPocket.xcodeproj
```

Verify sources from Linux/WSL:

```bash
./scripts/mobile/verify-ios.sh
```

CI builds both platforms on `.github/workflows/mobile.yml`.
