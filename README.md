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

---

## Questions de démo

Corpus: 98 PDFs (fiches produits, procédures internes, tarifs régionaux, contrats fournisseurs, fiches techniques Rockwool).

### Produits et prix

- "Quelles sont les applications de la laine de roche ?"
- "Quelle est la résistance thermique de la laine de verre 160mm ?"
- "Quels isolants sont certifiés pour MaPrimeRénov ?"

### Procédures internes

- "Quelles sont les conditions pour retourner une marchandise ?"
- "Comment passer une commande urgente ?"
- "Quelles sont les conditions pour ouvrir un crédit client ?"
- "Quelle est la procédure en cas de non-conformité fournisseur ?"
- "Comment se déroule l'inventaire annuel ?"

### Contrats fournisseurs

- "Quelles sont les pénalités de retard de livraison fournisseur ?"
- "Quel est le délai de paiement standard avec les fournisseurs ?"
- "Quelles sont les conditions de révision des prix fournisseurs ?"

### Tarifs

- "Quel est le tarif de la laine de verre 100mm en Ile-de-France ?"
- "Quelles remises volume sont disponibles ?"

### Test anti-hallucination (pas de réponse dans les docs)

- "Quel est le prix du placo BA13 en région Bretagne ?" → doit dire qu'il n'a pas l'info
- "Quels sont les horaires de l'agence de Lyon ?" → doit dire qu'il n'a pas l'info

### Conseil démo

Utiliser des mots proches du vocabulaire des documents ("procédure retour", "crédit client", "non-conformité") plutôt que du langage très naturel. Le moteur de recherche sémantique fonctionne mieux quand la question ressemble aux titres des sections.
