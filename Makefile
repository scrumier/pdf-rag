# pdf-rag
#   make setup   install dependencies (once, downloads the embedding model)
#   make run     start the chat  ->  http://127.0.0.1:5050
#   make docs    regenerate the demo PDFs
#   make test    run the test suite
#   make lint    lint and format check

-include local.mk
HOST ?= 127.0.0.1
PORT ?= 5050

.PHONY: help setup run docs test lint

help:
	@echo ""
	@echo "  make setup   install dependencies (downloads the embedding model)"
	@echo "  make run     chat  ->  http://$(HOST):$(PORT)"
	@echo "  make docs    regenerate the demo PDFs"
	@echo "  make test    run the test suite"
	@echo "  make lint    lint and format check"
	@echo ""

setup:
	@uv sync --quiet
	@echo "==> Ready. Copy .env.example to .env and add your OPENROUTER_API_KEY."

run:
	@echo "==> http://$(HOST):$(PORT)   (~10s to start, Ctrl+C to stop)"
	@FLASK_HOST=$(HOST) FLASK_PORT=$(PORT) uv run python -m rag.api

docs:
	@uv run python scripts/gen_docs.py

test:
	@uv run pytest -q

lint:
	@uv run ruff check .
	@uv run ruff format --check .
