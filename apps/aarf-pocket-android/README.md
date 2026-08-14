# Aarflingo Pocket (Android)

Kotlin + Jetpack Compose companion app. Runs TriadNet **on-device** via ONNX Runtime from bundled `models/triad.onnx` (no WiFi needed); falls back to the runtime client when the model isn't bundled. Bundle it with `scripts/mobile/bundle-mobile-models.sh`.

## Build (WSL / Linux)

```bash
export JAVA_HOME=$HOME/.local/jdk   # or system OpenJDK 17
export ANDROID_HOME=$HOME/Android/Sdk
cd apps/aarf-pocket-android
./gradlew assembleDebug
```

Or use the repo helper:

```bash
./scripts/mobile/setup-android-wsl.sh
./scripts/mobile/run-android-app.sh
```

APK: `app/build/outputs/apk/debug/app-debug.apk`

Default runtime URL in Settings: `http://10.0.2.2:8765` (Android emulator → host localhost).
