#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
MOBILE_DIR="$PROJECT_DIR/mobile"
WINDOWS_DIR="$PROJECT_DIR/release/windows"
LINUX_DIR="$PROJECT_DIR/release/linux"
OUTPUT_DIR="$PROJECT_DIR/release/dist"
STAGING_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGING_DIR"' EXIT

if [[ ! -f "$MOBILE_DIR/www/index.html" ]]; then
    printf 'Build mobile/www first by running npm ci && npm run build in mobile/.\n' >&2
    exit 1
fi
command -v zip >/dev/null 2>&1 || {
    printf 'The zip utility is required to create downloadable packages.\n' >&2
    exit 1
}

mkdir -p "$OUTPUT_DIR"
rm -f "$OUTPUT_DIR/Chiwas-POS-Windows-7-8-10-11.zip" \
    "$OUTPUT_DIR/Chiwas-POS-Ubuntu.zip"

WINDOWS_STAGE="$STAGING_DIR/windows"
mkdir -p "$WINDOWS_STAGE"
cp -R "$MOBILE_DIR/www" "$WINDOWS_STAGE/portable-pos"
cp "$WINDOWS_DIR/Start_Chiwas_POS_All_Windows.bat" \
    "$WINDOWS_STAGE/Start_Chiwas_POS_Windows.bat"
cp "$WINDOWS_DIR/Start_Offline_Pos.ps1" "$WINDOWS_STAGE/"
cat > "$WINDOWS_STAGE/README.txt" <<'EOF'
CHIWAS LIQUOR STORE & RESTAURANT - Portable POS

Start_Chiwas_POS_Windows.bat launches the standalone local POS.
Create the owner account on first launch; no Django server or network is
required. Inventory and sales are stored in this Windows user/browser profile.
Use the in-app JSON backup regularly and store a copy somewhere safe.

A current Chromium-based browser is required. Windows 7 and 8 are no longer
supported by current Chrome releases; use a compatible browser build at your
own risk. Internet Explorer is not supported.
EOF
(cd "$WINDOWS_STAGE" && zip -qr "$OUTPUT_DIR/Chiwas-POS-Windows-7-8-10-11.zip" .)

LINUX_STAGE="$STAGING_DIR/ubuntu"
mkdir -p "$LINUX_STAGE"
cp -R "$MOBILE_DIR/www" "$LINUX_STAGE/portable-pos"
cp "$LINUX_DIR/Start_Chiwas_POS_Linux.sh" "$LINUX_STAGE/"
cat > "$LINUX_STAGE/README.txt" <<'EOF'
CHIWAS LIQUOR STORE & RESTAURANT - Ubuntu Portable POS

Run ./Start_Chiwas_POS_Linux.sh. Python 3 and Chrome/Chromium are required to
serve and open the local app. No Django backend or internet connection is
required for standalone sales. Use the in-app JSON backup regularly.
EOF
(cd "$LINUX_STAGE" && zip -qr "$OUTPUT_DIR/Chiwas-POS-Ubuntu.zip" .)

printf 'Created portable packages in %s\n' "$OUTPUT_DIR"
