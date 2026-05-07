from flask import Flask, request, jsonify, send_file
from rag.core import ingest_directory, search_documents, ask_question
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="../static")


@app.post("/api/ingest")
def ingest():
    data = request.get_json(silent=True) or {}
    path = data.get("path", os.getenv("DOCS_PATH", "./demo_docs"))
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
    return jsonify(ask_question(question))


@app.get("/")
def ui():
    return send_file("../static/index.html")


def run():
    port = int(os.getenv("FLASK_PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    run()
