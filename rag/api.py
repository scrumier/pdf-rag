from flask import Flask, request, jsonify, send_file
from rag.core import ingest_directory, search_documents, ask_question, collection_count
import openai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="../static")


@app.get("/api/status")
def status():
    count = collection_count()
    return jsonify({"chunks": count, "ready": count > 0})


@app.post("/api/ingest")
def ingest():
    data = request.get_json(silent=True) or {}
    path = data.get("path", os.getenv("DOCS_PATH", "./demo_docs"))
    force = data.get("force", False)
    if not force and collection_count() > 0:
        return jsonify({"skipped": True, "reason": "already loaded", "total_chunks": collection_count()})
    result = ingest_directory(path)
    return jsonify(result)


@app.post("/api/search")
def search():
    data = request.get_json()
    query = data.get("query", "")
    n = int(data.get("n_results", 5))
    if not query:
        return jsonify({"error": "query required"}), 400
    return jsonify(search_documents(query, n_results=n))


@app.post("/api/ask")
def ask():
    data = request.get_json()
    question = data.get("question", "")
    if not question:
        return jsonify({"error": "question required"}), 400
    try:
        return jsonify(ask_question(question))
    except openai.AuthenticationError:
        return jsonify({"error": "Clé API OpenRouter manquante ou invalide. Remplir OPENROUTER_API_KEY dans .env et relancer le serveur."}), 401
    except openai.APIError as e:
        return jsonify({"error": f"Erreur API: {str(e)}"}), 502


@app.get("/")
def ui():
    return send_file("../static/index.html")


def run():
    port = int(os.getenv("FLASK_PORT", 5050))
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run()
