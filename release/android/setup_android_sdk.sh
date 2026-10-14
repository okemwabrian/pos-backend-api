#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
SDK_ROOT="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"
TOOLS_VERSION="16111833"
TOOLS_URL="https://dl.google.com/android/repository/commandlinetools-linux-${TOOLS_VERSION}_latest.zip"
TOOLS_DIR="$SDK_ROOT/cmdline-tools/latest"
mkdir -p "$HOME/.cache" "$SDK_ROOT/cmdline-tools"
WORK_DIR="$(mktemp -d "$HOME/.cache/chiwas-android-sdk.XXXXXX")"
trap 'rm -rf "$WORK_DIR"' EXIT

if [[ ! -x "$TOOLS_DIR/bin/sdkmanager" ]]; then
    printf 'Downloading official Android command-line tools...\n'
    curl --fail --location --retry 2 "$TOOLS_URL" --output "$WORK_DIR/tools.zip"
    mkdir "$WORK_DIR/extracted"
    unzip -q "$WORK_DIR/tools.zip" -d "$WORK_DIR/extracted"
    mkdir -p "$TOOLS_DIR"
    cp -a "$WORK_DIR/extracted/cmdline-tools/." "$TOOLS_DIR/"
fi

export ANDROID_HOME="$SDK_ROOT"
export ANDROID_SDK_ROOT="$SDK_ROOT"
SDKMANAGER="$TOOLS_DIR/bin/sdkmanager"

printf 'Accepting Android SDK licenses as requested...\n'
set +o pipefail
yes | "$SDKMANAGER" --sdk_root="$SDK_ROOT" --licenses
set -o pipefail

printf 'Installing platform tools, Android API 35, and build tools...\n'
"$SDKMANAGER" --sdk_root="$SDK_ROOT" \
    "platform-tools" \
    "platforms;android-35" \
    "build-tools;35.0.0"

printf 'Writing Android SDK location to mobile/android/local.properties...\n'
printf 'sdk.dir=%s\n' "$SDK_ROOT" > "$PROJECT_DIR/mobile/android/local.properties"
printf 'Android SDK is ready at %s\n' "$SDK_ROOT"
