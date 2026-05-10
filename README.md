# samse-rag

Chatbot interne alimenté par vos propres documents PDF. Posez une question en langage naturel, obtenez une réponse sourcée depuis vos fiches produits, procédures, tarifs ou contrats fournisseurs.

> Prototype réalisé en 2 jours pour explorer l'apport de l'IA sur la base documentaire SAMSE (98 PDFs de démonstration).

---

## Ce que ça fait concrètement

Un employé tape : *"Quelles sont les conditions pour retourner une marchandise ?"*

Le système :
1. Cherche dans les 98 PDFs les passages les plus pertinents
2. Les donne à un modèle de langage (Claude)
3. Retourne une réponse claire avec la source entre crochets

Si l'information n'est pas dans les documents, il le dit explicitement — pas d'inventions.

---

## Comment ça marche (RAG)

**RAG = Retrieval-Augmented Generation** : on sépare la recherche de la génération.

Sans RAG, un LLM comme ChatGPT ne connaît pas vos documents internes et invente des réponses plausibles mais fausses (hallucinations).

Avec RAG :

```
Question utilisateur
    ↓
Transformation en vecteur (embedding)
    ↓
Recherche des passages similaires dans ChromaDB
    ↓
Les passages trouvés + la question → LLM
    ↓
Réponse sourcée, ancrée dans vos vrais documents
```

### Les 4 composants techniques

**1. Extraction PDF** (`pdfplumber`)
Lit chaque page et extrait le texte brut. Premier filtre : si une page ne contient pas de texte (scan image), elle est ignorée.

**2. Chunking** (découpage en morceaux)
Chaque PDF est découpé en blocs de ~300 mots avec un chevauchement de 50 mots entre blocs. Le chevauchement évite qu'une information importante soit coupée entre deux morceaux.

**3. Embeddings** (`all-MiniLM-L6-v2` via sentence-transformers)
Chaque morceau est transformé en vecteur numérique (384 dimensions). Les phrases sémantiquement proches ont des vecteurs proches — c'est ce qui permet de trouver "renvoi produit" quand quelqu'un demande "retour marchandise".

**4. ChromaDB**
Base de données vectorielle locale (stockée dans `chroma_db/`). Quand une question arrive, elle est elle aussi transformée en vecteur, et ChromaDB retourne les 5 morceaux les plus proches. Pas de serveur externe, tout tourne en local.

---

## Architecture

```
rag/core.py          → logique RAG (ingest, search, ask)
rag/api.py           → API REST Flask (3 endpoints)
rag/mcp_server.py    → serveur MCP (utilisable depuis Claude Code)
static/index.html    → interface web chat
scripts/gen_docs.py  → génère les 98 PDFs de démo
```

### API REST

| Endpoint | Méthode | Description |
|---|---|---|
| `/api/ingest` | POST | Ingère les PDFs du dossier `demo_docs/` |
| `/api/search` | POST | Recherche sémantique brute (sans LLM) |
| `/api/ask` | POST | Question complète avec réponse LLM |

---

## Setup

```bash
# 1. Installer uv (gestionnaire de paquets Python moderne)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Installer les dépendances
cd samse-rag
uv sync

# 3. Configurer la clé API
cp .env.example .env
# Remplir OPENROUTER_API_KEY dans .env

# 4. Générer les 98 documents de démo
uv run python scripts/gen_docs.py

# 5. Lancer l'interface web
uv run python rag/api.py
# Ouvrir http://localhost:5050
```

### Via Claude Code (MCP)

Le système peut aussi être utilisé directement depuis Claude comme outil natif.

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

Puis depuis Claude : `ingest_documents()` puis `ask_doc("votre question")`.

---

## Corpus de démo

98 PDFs couvrant :
- Fiches produits isolants (laine de roche, laine de verre, Rockwool)
- Procédures internes (retours, commandes urgentes, crédit client, inventaire)
- Tarifs régionaux (Ile-de-France, PACA, Bretagne...)
- Contrats fournisseurs

### Questions de démo recommandées

**Produits**
- "Quelles sont les applications de la laine de roche ?"
- "Quelle est la résistance thermique de la laine de verre 160mm ?"
- "Quels isolants sont certifiés pour MaPrimeRénov ?"

**Procédures internes**
- "Quelles sont les conditions pour retourner une marchandise ?"
- "Comment passer une commande urgente ?"
- "Quelle est la procédure en cas de non-conformité fournisseur ?"

**Contrats fournisseurs**
- "Quelles sont les pénalités de retard de livraison fournisseur ?"
- "Quelles sont les conditions de révision des prix fournisseurs ?"

**Test anti-hallucination** (l'info n'existe pas dans les docs)
- "Quels sont les horaires de l'agence de Lyon ?" → doit répondre qu'il n'a pas l'info
- "Quel est le prix du placo BA13 en Bretagne ?" → idem

---

## Limites connues et pistes d'amélioration

Le prototype fonctionne mais plusieurs axes d'amélioration sont identifiés :

### Priorité haute

**Modèle d'embedding adapté au français**
Le modèle actuel (`all-MiniLM-L6-v2`) est entraîné principalement sur de l'anglais. Pour des documents en français, `multilingual-e5-base` ou un modèle CamemBERT donnerait de meilleurs résultats de recherche sémantique.

**Reranking**
Après la recherche vectorielle, un cross-encoder re-scorerait les 5 passages trouvés selon leur pertinence réelle par rapport à la question (pas juste leur proximité vectorielle). Résultat : moins de bruit, réponses plus précises.

**Chunking sémantique**
Découper par sections/paragraphes plutôt que par nombre de mots, pour ne pas couper des clauses juridiques ou des spécifications techniques en plein milieu.

### Priorité moyenne

**Mémoire de conversation**
Chaque question est aujourd'hui indépendante. "Et en Bretagne ?" après une première réponse ne fonctionne pas. Passer l'historique au LLM résoudrait ça.

**Filtrage par type de document**
ChromaDB supporte les filtres sur metadata. Il serait possible d'ajouter un filtre "cherche uniquement dans les tarifs" ou "uniquement dans les procédures internes".

**Authentification**
L'API n'a pas d'auth. En production, ajouter au minimum une clé API ou un token Bearer.

### Priorité basse

**Détection de changements**
Si un PDF est modifié, il faut réingesser manuellement. Un hash des fichiers permettrait de détecter automatiquement les nouveautés et de ne réingesser que ce qui a changé.

**Évaluation des réponses**
Aucune métrique pour mesurer la qualité des réponses. En production, un jeu de questions/réponses de référence permettrait de suivre les régressions.
