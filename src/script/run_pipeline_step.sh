#!/bin/bash
set -euo pipefail
MODE="${1:?mode is required: sync|captions|summarize}"
case "$MODE" in
  sync|captions|summarize) ;;
  *) echo "unsupported mode: $MODE" >&2; exit 2 ;;
esac
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"
source .venv/bin/activate
set -a
# shellcheck disable=SC1091
source .env
set +a
export PYTHONPATH="$PROJECT_ROOT/src"
exec python src/main.py "$MODE"
