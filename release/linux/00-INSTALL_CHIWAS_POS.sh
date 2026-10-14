#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/chiwas-pos"
APPLICATIONS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"

if [[ ! -f "$PACKAGE_DIR/portable-pos/index.html" ]]; then
    printf 'Extract the complete FREE HOUSE POS ZIP before running setup.\n' >&2
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
Name=FREE HOUSE BAR & RESTAURANT POS
Comment=FREE HOUSE BAR & RESTAURANT
Exec="$APP_DIR/Start_Chiwas_POS_Linux.sh"
Icon=$APP_DIR/portable-pos/free-house-app-icon.svg
Terminal=true
Categories=Office;Finance;
StartupNotify=true
EOF
chmod +x "$DESKTOP_FILE"

if [[ -d "$HOME/Desktop" ]]; then
    cp "$DESKTOP_FILE" "$HOME/Desktop/FREE HOUSE POS.desktop"
    chmod +x "$HOME/Desktop/FREE HOUSE POS.desktop"
fi

printf 'FREE HOUSE POS is installed for this Linux user.\n'
printf 'Open "FREE HOUSE BAR & RESTAURANT POS" from the Applications menu or Desktop.\n'
printf 'For this run: %s\n' "$APP_DIR/Start_Chiwas_POS_Linux.sh"
