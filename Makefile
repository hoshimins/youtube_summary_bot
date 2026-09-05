# Makefile

.PHONY: run help test

# default mode is 'latest' if not specified
MODE ?= latest

help:
	@echo "Usage: make run MODE=latest|all|summarize|id"
	@echo "  MODE=latest     RSS 監視 + 字幕取得（デフォルト）"
	@echo "  MODE=all        全動画取得 + 字幕取得"
	@echo "  MODE=summarize  未要約を要約"
	@echo "  make test       ローカル単体テスト"
	@echo "  例: make run MODE=summarize"

# 実行
run:
	@echo "Activating venv and running with mode: $(MODE)"
	@. .venv/bin/activate && PYTHONPATH=src python3 src/main.py $(MODE)

test:
	@. .venv/bin/activate && PYTHONPATH=src python3 -m unittest discover -s tests -v
