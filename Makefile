# Makefile

.PHONY: run

# default mode is 'latest' if not specified
MODE ?= latest

# venv の activate
VENV_ACTIVATE = . venv/bin/activate

# 実行
run:
	@echo "Activating venv and running with mode: $(MODE)"
	@. venv/bin/activate && PYTHONPATH=src python3 -m src.feed.main $(MODE)
