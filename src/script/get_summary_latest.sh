#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"
source .venv/bin/activate
set -a
# shellcheck disable=SC1091
source .env
set +a
export PYTHONPATH="$PROJECT_ROOT/src"
python src/main.py latest
python src/main.py summarize
