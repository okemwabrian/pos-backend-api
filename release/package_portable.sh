#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
WINDOWS_DIR="$PROJECT_DIR/release/windows"
LINUX_DIR="$PROJECT_DIR/release/linux"
OUTPUT_DIR="$PROJECT_DIR/release/dist"
STAGING_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGING_DIR"' EXIT

command -v zip >/dev/null 2>&1 || {
    printf 'The zip utility is required to create downloadable packages.\n' >&2
    exit 1
}

mkdir -p "$OUTPUT_DIR"
rm -f "$OUTPUT_DIR/Free-House-POS-Windows-7-8-10-11.zip" \
    "$OUTPUT_DIR/Free-House-POS-Ubuntu.zip" \
    "$OUTPUT_DIR/Chiwas-POS-Windows-7-8-10-11.zip" \
    "$OUTPUT_DIR/Chiwas-POS-Ubuntu.zip"

WINDOWS_STAGE="$STAGING_DIR/windows"
mkdir -p "$WINDOWS_STAGE"
for app in core users inventory crm sales purchases finance offline; do
    cp -R "$PROJECT_DIR/$app" "$WINDOWS_STAGE/"
done
cp -R "$PROJECT_DIR/templates" "$PROJECT_DIR/static" "$WINDOWS_STAGE/"
find "$WINDOWS_STAGE" -type d -name __pycache__ -prune -exec rm -rf {} +
cp "$PROJECT_DIR/manage.py" \
    "$PROJECT_DIR/desktop_runtime.py" \
    "$PROJECT_DIR/setup_local_pos.py" \
    "$PROJECT_DIR/run_django_pos.py" \
    "$PROJECT_DIR/requirements.txt" \
    "$WINDOWS_DIR/SETUP_FREE_HOUSE_POS.bat" \
    "$WINDOWS_DIR/START_FREE_HOUSE_POS.bat" \
    "$WINDOWS_STAGE/"
cat > "$WINDOWS_STAGE/README.txt" <<'EOF'
FREE HOUSE BAR & RESTAURANT - Portable POS

This download runs the Django server-rendered POS templates used by the local
web app. It does not use the standalone JavaScript POS interface.

REQUIREMENTS: Windows, Python 3.12 or newer, and internet access for the first
setup (to install Python packages). Extract this ZIP to a permanent folder.
Double-click SETUP_FREE_HOUSE_POS.bat once to install requirements, apply
database migrations, and launch the POS in your browser.

For later launches, double-click START_FREE_HOUSE_POS.bat. Sign in at
http://127.0.0.1:8000/. On first launch, create passwords for the Brian and
Chiwas full-access administrator accounts. Passwords must include at least
four digits; 1234 and 2580 are accepted.

The POS keeps you signed in across browser restarts and renews the session while
you use it (ten-year idle expiration). Sign out to end your session.

Database, uploaded images, and the generated Django secret key are stored
outside this folder under your Windows LocalAppData. The server listens only
on this computer and is not exposed to the network.
EOF
(cd "$WINDOWS_STAGE" && zip -qr "$OUTPUT_DIR/Free-House-POS-Windows-7-8-10-11.zip" .)

LINUX_STAGE="$STAGING_DIR/ubuntu"
mkdir -p "$LINUX_STAGE"
for app in core users inventory crm sales purchases finance offline; do
    cp -R "$PROJECT_DIR/$app" "$LINUX_STAGE/"
done
cp -R "$PROJECT_DIR/templates" "$PROJECT_DIR/static" "$LINUX_STAGE/"
find "$LINUX_STAGE" -type d -name __pycache__ -prune -exec rm -rf {} +
cp "$PROJECT_DIR/manage.py" \
    "$PROJECT_DIR/desktop_runtime.py" \
    "$PROJECT_DIR/setup_local_pos.py" \
    "$PROJECT_DIR/run_django_pos.py" \
    "$PROJECT_DIR/requirements.txt" \
    "$LINUX_DIR/SETUP_FREE_HOUSE_POS.sh" \
    "$LINUX_DIR/START_FREE_HOUSE_POS.sh" \
    "$LINUX_STAGE/"
chmod +x "$LINUX_STAGE/SETUP_FREE_HOUSE_POS.sh" \
    "$LINUX_STAGE/START_FREE_HOUSE_POS.sh"
cat > "$LINUX_STAGE/README.txt" <<'EOF'
FREE HOUSE BAR & RESTAURANT - Ubuntu Portable POS

This download runs the Django server-rendered POS templates used by the local
web app. It does not use the standalone JavaScript POS interface.

REQUIREMENTS: Ubuntu, Python 3.12 or newer with venv support, and internet
access for first setup. Extract this ZIP to a permanent folder, then run
./SETUP_FREE_HOUSE_POS.sh once to install requirements, apply migrations, and
launch the POS in your browser.

For later launches, run ./START_FREE_HOUSE_POS.sh. Sign in at
http://127.0.0.1:8000/. On first launch, create passwords for the Brian and
Chiwas full-access administrator accounts. Passwords must include at least
four digits; 1234 and 2580 are accepted.

The POS keeps you signed in across browser restarts and renews the session while
you use it (ten-year idle expiration). Sign out to end your session.

Database, uploaded images, and the generated Django secret key are stored
outside this folder under ~/.local/share/free-house-pos. The server listens
only on this computer and is not exposed to the network.
EOF
(cd "$LINUX_STAGE" && zip -qr "$OUTPUT_DIR/Free-House-POS-Ubuntu.zip" .)

printf 'Created portable packages in %s\n' "$OUTPUT_DIR"
