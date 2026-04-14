#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"
source .venv/bin/activate
export $(cat .env | xargs)
export PYTHONPATH="$PROJECT_ROOT/src"
python src/bot/main.py
