# Makefile

.PHONY: setup sync audit channel-list run help test

MODE ?= latest
AUDIT_SOURCE ?= api
AUDIT_LIMIT ?= 0
AUDIT_FORMAT ?= text
PYTHON ?= .venv/bin/python
UV ?= mise exec -- uv

help:
	@echo "Usage: make setup|sync|audit|run|test"
	@echo "  make setup       miseでPython/uvを準備し、依存関係を同期"
	@echo "  make sync        requirements.txtを.venvへ同期"
	@echo "  make audit       YouTubeとDBの動画差分を確認（AUDIT_SOURCE=rss可）"
	@echo "  make channel-list 登録チャンネルを表示"
	@echo "  make run         latest（MODE=latest|all|summarize|id）"
	@echo "  make test        ローカル単体テスト"
	@echo "  例: make run MODE=summarize"

setup:
	@mise install
	@$(UV) venv --python 3.12.14
	@$(UV) pip sync --python $(PYTHON) requirements.txt

sync:
	@$(UV) pip sync --python $(PYTHON) requirements.txt

audit:
	@PYTHONPATH=src $(PYTHON) src/script/audit_channels.py --source $(AUDIT_SOURCE) --limit $(AUDIT_LIMIT) --format $(AUDIT_FORMAT) $(if $(CHANNEL_ID),--channel-id $(CHANNEL_ID),)

channel-list:
	@PYTHONPATH=src $(PYTHON) src/script/manage_channels.py list

run:
	@echo "Running with mode: $(MODE)"
	@PYTHONPATH=src $(PYTHON) src/main.py $(MODE)

test:
	@PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v
