"""HTTP API and chat UI for the document assistant."""

import os

import openai
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_file

from rag.core import (
    ask_question,
    collection_count,
    ingest_directory,
    search_documents,
)

load_dotenv()

app = Flask(__name__, static_folder="../static")

DEFAULT_DOCS_PATH = "./demo_docs"
DEFAULT_PORT = 5050

HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_BAD_GATEWAY = 502

MISSING_KEY_MESSAGE = (
    "Clé API OpenRouter manquante ou invalide. Remplir OPENROUTER_API_KEY "
    "dans .env et relancer le serveur."
)


@app.get("/api/status")
def status() -> Response:
    """Report whether anything has been indexed yet.

    Returns:
        The chunk count and whether the assistant can answer.
    """
    count = collection_count()
    return jsonify({"chunks": count, "ready": count > 0})


@app.post("/api/ingest")
def ingest() -> Response:
    """Index the configured document folder.

    Skips the work when the store is already populated, unless `force` is set,
    so reloading the page does not re-embed the whole corpus.

    Returns:
        What was ingested, or why it was skipped.
    """
    payload = request.get_json(silent=True) or {}
    path = payload.get("path", os.getenv("DOCS_PATH", DEFAULT_DOCS_PATH))

    if not payload.get("force", False) and collection_count() > 0:
        return jsonify(
            {
                "skipped": True,
                "reason": "already loaded",
                "total_chunks": collection_count(),
            }
        )
    return jsonify(ingest_directory(path))


@app.post("/api/search")
def search() -> Response | tuple[Response, int]:
    """Return the passages closest to a query, without asking the model.

    Returns:
        The matching chunks, or a 400 if no query was given.
    """
    payload = request.get_json(silent=True) or {}
    query = payload.get("query", "")
    if not query:
        return jsonify({"error": "query required"}), HTTP_BAD_REQUEST
    return jsonify(search_documents(query, n_results=int(payload.get("n_results", 5))))


@app.post("/api/ask")
def ask() -> Response | tuple[Response, int]:
    """Answer a question from the indexed documents.

    Returns:
        The answer and its sources, or an error the UI can show as-is.
    """
    payload = request.get_json(silent=True) or {}
    question = payload.get("question", "")
    if not question:
        return jsonify({"error": "question required"}), HTTP_BAD_REQUEST

    try:
        return jsonify(ask_question(question))
    except openai.AuthenticationError:
        return jsonify({"error": MISSING_KEY_MESSAGE}), HTTP_UNAUTHORIZED
    except openai.APIError as exc:
        return jsonify({"error": f"Erreur API: {exc}"}), HTTP_BAD_GATEWAY
    except ValueError as exc:
        return jsonify({"error": str(exc)}), HTTP_BAD_GATEWAY


@app.get("/")
def ui() -> Response:
    """Serve the chat page.

    Returns:
        The single-page UI.
    """
    return send_file("../static/index.html")


def run() -> None:
    """Serve the app on the configured host and port."""
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT") or DEFAULT_PORT),
        debug=False,
    )


if __name__ == "__main__":
    run()
