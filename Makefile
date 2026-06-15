# pdf-rag — launcher autonome.
#   make setup   <- une fois : venv + deps (uv) [lourd : modèles ML]
#   make run     <- démarre le chatbot RAG  ->  http://127.0.0.1:5050
# Bind Tailscale uniquement, jamais exposé publiquement.

TS   := 127.0.0.1
PORT := 5050

.PHONY: help setup run

help:
	@echo ""
	@echo "  pdf-rag   ->  http://$(TS):$(PORT)"
	@echo "    make setup   installe les deps (une fois, peut être long)"
	@echo "    make run     démarre la démo"
	@echo ""

setup:
	@echo "==> uv sync (peut télécharger des modèles ML)..."
	@uv sync --quiet
	@echo "==> Prêt. Lancer :  make run"

run:
	@echo ""
	@echo "==> Ouvre sur ton Mac :  http://$(TS):$(PORT)      (~10s de démarrage, Ctrl+C pour arrêter)"
	@echo ""
	@FLASK_HOST=$(TS) FLASK_PORT=$(PORT) uv run python -m rag.api
