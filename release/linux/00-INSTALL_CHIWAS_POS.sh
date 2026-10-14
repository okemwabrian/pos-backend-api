#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/chiwas-pos"
APPLICATIONS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"

if [[ ! -f "$PACKAGE_DIR/portable-pos/index.html" ]]; then
    printf 'Extract the complete CHIWAS POS ZIP before running setup.\n' >&2
    exit 1
fi

mkdir -p "$APP_DIR" "$APPLICATIONS_DIR"
cp -R "$PACKAGE_DIR/portable-pos" "$APP_DIR/"
cp "$PACKAGE_DIR/Start_Chiwas_POS_Linux.sh" "$APP_DIR/"
chmod +x "$APP_DIR/Start_Chiwas_POS_Linux.sh"

DESKTOP_FILE="$APPLICATIONS_DIR/chiwas-pos.desktop"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=CHIWAS LIQUOR STORE POS
Comment=CHIWAS LIQUOR STORE & RESTAURANT
Exec="$APP_DIR/Start_Chiwas_POS_Linux.sh"
Icon=$APP_DIR/portable-pos/chiwas-logo.svg
Terminal=true
Categories=Office;Finance;
StartupNotify=true
EOF
chmod +x "$DESKTOP_FILE"

if [[ -d "$HOME/Desktop" ]]; then
    cp "$DESKTOP_FILE" "$HOME/Desktop/CHIWAS POS.desktop"
    chmod +x "$HOME/Desktop/CHIWAS POS.desktop"
fi

printf 'CHIWAS POS is installed for this Linux user.\n'
printf 'Open "CHIWAS LIQUOR STORE POS" from the Applications menu or Desktop.\n'
printf 'For this run: %s\n' "$APP_DIR/Start_Chiwas_POS_Linux.sh"
