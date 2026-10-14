#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${CHIWAS_VENV:-$PROJECT_DIR/venv}"
POS_URL="http://127.0.0.1:8000"
DATA_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/chiwas-pos"
LOG_FILE="$DATA_DIR/server.log"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    printf 'Python virtual environment not found at %s\n' "$VENV_DIR" >&2
    exit 1
fi

mkdir -p "$DATA_DIR" "$HOME/.local/share/chiwas-pos"
source "$VENV_DIR/bin/activate"
export DJANGO_DEBUG=true
export DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost,$(hostname -I 2>/dev/null | awk '{print $1}')"
export CORS_ALLOWED_ORIGINS="http://127.0.0.1:8766,http://localhost:8766,https://localhost,capacitor://localhost"

cd "$PROJECT_DIR"
python manage.py migrate --noinput
python manage.py runserver 0.0.0.0:8000 --noreload >>"$LOG_FILE" 2>&1 &
server_pid=$!

cleanup() {
    kill "$server_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

for _ in {1..60}; do
    if curl --fail --silent "$POS_URL/" >/dev/null; then
        break
    fi
    if ! kill -0 "$server_pid" 2>/dev/null; then
        printf 'Django server stopped unexpectedly. See %s\n' "$LOG_FILE" >&2
        exit 1
    fi
    sleep 1
done

if ! curl --fail --silent "$POS_URL/" >/dev/null; then
    printf 'Django did not become ready. See %s\n' "$LOG_FILE" >&2
    exit 1
fi

if command -v google-chrome >/dev/null 2>&1; then
    google-chrome --app="$POS_URL" --user-data-dir="$HOME/.local/share/chiwas-pos/chrome-profile" --no-first-run
elif command -v chromium-browser >/dev/null 2>&1; then
    chromium-browser --app="$POS_URL" --user-data-dir="$HOME/.local/share/chiwas-pos/chrome-profile" --no-first-run
elif command -v chromium >/dev/null 2>&1; then
    chromium --app="$POS_URL" --user-data-dir="$HOME/.local/share/chiwas-pos/chrome-profile" --no-first-run
else
    xdg-open "$POS_URL"
fi
