#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
ANDROID_DIR="$PROJECT_DIR/mobile/android"

find_jdk21() {
    local candidates=()
    if [[ -n "${JAVA_HOME:-}" && -x "${JAVA_HOME}/bin/javac" ]]; then
        candidates+=("$JAVA_HOME")
    fi
    candidates+=("$HOME/.local/share/jdk"/jdk-*)
    candidates+=("/usr/lib/jvm/java-21-openjdk-amd64" "/usr/lib/jvm/java-21-openjdk-amd64/bin" "/usr/lib/jvm/default-java")

    for candidate in "${candidates[@]}"; do
        if [[ -n "$candidate" && -x "$candidate/bin/javac" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}

if ! JDK_21_HOME="$(find_jdk21)"; then
    printf 'Java 21 JDK with javac is required to compile the Capacitor Android app.\n' >&2
    printf 'Install a local JDK 21 such as: %s\n' "$HOME/.local/share/jdk/jdk-21.0.12.1+1" >&2
    printf 'Then re-run ./release/android/build_apk.sh\n' >&2
    exit 1
fi

export JAVA_HOME="$JDK_21_HOME"
export PATH="$JAVA_HOME/bin:$PATH"

"$PROJECT_DIR/release/android/setup_android_sdk.sh"
cd "$PROJECT_DIR/mobile"
npm run build
npx cap sync android
cd "$ANDROID_DIR"
./gradlew assembleDebug

mkdir -p "$PROJECT_DIR/release/android"
cp app/build/outputs/apk/debug/app-debug.apk "$PROJECT_DIR/release/android/Free-House-POS.apk"
printf 'Debug APK created at %s\n' "$PROJECT_DIR/release/android/Free-House-POS.apk"
