#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${CHIWAS_DATA_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/free-house-pos}"
PYTHON="$DATA_DIR/venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
    printf 'Run ./SETUP_FREE_HOUSE_POS.sh first to install the Django requirements.\n' >&2
    exit 1
fi

export CHIWAS_DATA_DIR="$DATA_DIR"
exec "$PYTHON" "$PACKAGE_DIR/run_django_pos.py"
