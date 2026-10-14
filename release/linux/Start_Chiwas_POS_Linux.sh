#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$PACKAGE_DIR/portable-pos"
PORT="${CHIWAS_POS_PORT:-8766}"
URL="http://127.0.0.1:$PORT/"
PROFILE="${XDG_DATA_HOME:-$HOME/.local/share}/chiwas-pos-browser"

if [[ ! -f "$APP_DIR/index.html" ]]; then
    printf 'The portable POS web files are missing from %s\n' "$APP_DIR" >&2
    exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
    printf 'Python 3 is required to serve the local POS files on Ubuntu.\n' >&2
    exit 1
fi

cd "$APP_DIR"
python3 -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 &
server_pid=$!
cleanup() {
    kill "$server_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

for _ in $(seq 1 40); do
    if curl --fail --silent "$URL" >/dev/null; then
        break
    fi
    if ! kill -0 "$server_pid" 2>/dev/null; then
        printf 'The local POS server stopped unexpectedly.\n' >&2
        exit 1
    fi
    sleep 0.25
done
if ! curl --fail --silent "$URL" >/dev/null; then
    printf 'The local POS did not become ready at %s\n' "$URL" >&2
    exit 1
fi

mkdir -p "$PROFILE"
if command -v google-chrome >/dev/null 2>&1; then
    google-chrome --app="$URL" --user-data-dir="$PROFILE" --no-first-run
elif command -v chromium-browser >/dev/null 2>&1; then
    chromium-browser --app="$URL" --user-data-dir="$PROFILE" --no-first-run
elif command -v chromium >/dev/null 2>&1; then
    chromium --app="$URL" --user-data-dir="$PROFILE" --no-first-run
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL"
    wait "$server_pid"
else
    printf 'Install Chromium/Chrome or xdg-utils to open the POS window.\n' >&2
    exit 1
fi
