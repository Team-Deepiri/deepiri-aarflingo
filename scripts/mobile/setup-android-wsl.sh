#!/usr/bin/env bash
# WSL / Linux setup for Aarflingo Pocket Android builds and emulator.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ANDROID_DIR="${ROOT}/apps/aarf-pocket-android"
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"

echo "==> Aarflingo mobile — Android WSL setup"
echo "    SDK: ${SDK}"

if ! command -v java >/dev/null 2>&1; then
  if [[ -x "${HOME}/.local/jdk/bin/java" ]]; then
    export JAVA_HOME="${HOME}/.local/jdk"
    export PATH="${JAVA_HOME}/bin:${PATH}"
  else
    echo "Java 17 required. Install openjdk-17-jdk or run setup with Temurin in ~/.local/jdk"
    exit 1
  fi
fi

if [[ ! -d "${SDK}" ]]; then
  echo "Android SDK not found at ${SDK}"
  echo "Install Android Studio on Windows, then symlink or set ANDROID_HOME."
  echo "  export ANDROID_HOME=\$HOME/Android/Sdk"
  exit 1
fi

export ANDROID_HOME="${SDK}"
export ANDROID_SDK_ROOT="${SDK}"
export PATH="${SDK}/platform-tools:${SDK}/emulator:${SDK}/cmdline-tools/latest/bin:${PATH}"

# Ensure platform + build-tools
if [[ ! -d "${SDK}/platforms/android-35" ]]; then
  echo "Installing Android platform 35..."
  sdkmanager "platforms;android-35" "build-tools;35.0.0"
fi

# Gradle wrapper jar if missing
WRAPPER_JAR="${ANDROID_DIR}/gradle/wrapper/gradle-wrapper.jar"
if [[ ! -f "${WRAPPER_JAR}" ]]; then
  echo "Downloading gradle-wrapper.jar..."
  curl -fsSL -o /tmp/gradle-8.7-bin.zip https://services.gradle.org/distributions/gradle-8.7-bin.zip
  unzip -qo /tmp/gradle-8.7-bin.zip -d /tmp
  /tmp/gradle-8.7/bin/gradle -p "${ANDROID_DIR}" wrapper --gradle-version 8.7
fi

chmod +x "${ANDROID_DIR}/gradlew" 2>/dev/null || true

echo "==> Building debug APK..."
cd "${ANDROID_DIR}"
./gradlew assembleDebug --no-daemon

echo ""
echo "Done. APK: ${ANDROID_DIR}/app/build/outputs/apk/debug/app-debug.apk"
echo "Run emulator: ${ROOT}/scripts/mobile/run-android-emulator.sh"
