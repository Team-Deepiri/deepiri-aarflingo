# Aarflingo Pocket (Android)

Kotlin + Jetpack Compose companion app. **v0.1 is UI-only** — mock predictions, no on-device ML yet.

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
