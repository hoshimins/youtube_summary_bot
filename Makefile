# Makefile

.PHONY: setup sync run help test

MODE ?= latest
PYTHON ?= .venv/bin/python
UV ?= mise exec -- uv

help:
	@echo "Usage: make setup|sync|run|test"
	@echo "  make setup       miseでPython/uvを準備し、依存関係を同期"
	@echo "  make sync        requirements.txtを.venvへ同期"
	@echo "  make run         latest（MODE=latest|all|summarize|id）"
	@echo "  make test        ローカル単体テスト"
	@echo "  例: make run MODE=summarize"

setup:
	@mise install
	@$(UV) venv --python 3.12.14
	@$(UV) pip sync --python $(PYTHON) requirements.txt

sync:
	@$(UV) pip sync --python $(PYTHON) requirements.txt

run:
	@echo "Running with mode: $(MODE)"
	@PYTHONPATH=src $(PYTHON) src/main.py $(MODE)

test:
	@PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v
