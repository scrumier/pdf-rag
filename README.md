# samse-rag

RAG chatbot sur documents d'entreprise. Ingère des PDFs, répond en langage naturel via une interface web ou directement depuis Claude (MCP).

## Setup

```bash
# 1. Installer uv (si pas encore fait)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Installer les dépendances
cd samse-rag
uv sync

# 3. Configurer la clé API
cp .env.example .env
# Editer .env et remplir ANTHROPIC_API_KEY

# 4. Générer les documents de démo
uv run python scripts/gen_docs.py
```

## Utilisation

### Interface web
```bash
uv run python rag/api.py
# Ouvrir http://localhost:5050
```

### Via Claude Code (MCP)
Ajouter dans `.claude/settings.json` :
```json
{
  "mcpServers": {
    "samse-rag": {
      "command": "uv",
      "args": ["run", "python", "rag/mcp_server.py"],
      "cwd": "/chemin/vers/samse-rag"
    }
  }
}
```
Puis depuis Claude : `ingest_documents()` → `ask_doc("votre question")`

## Architecture

```
Core RAG (rag/core.py)
    ↓
MCP Server (rag/mcp_server.py)  →  Claude peut l'utiliser comme outil
REST API   (rag/api.py)         →  3 endpoints : /api/ingest, /api/search, /api/ask
Chat UI    (static/index.html)  →  Interface web par-dessus l'API
```

## Ajouter des documents

Déposer des PDFs dans `demo_docs/` puis cliquer "Recharger les docs" dans l'interface, ou appeler `POST /api/ingest`.
