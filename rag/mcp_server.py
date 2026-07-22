"""Expose the document assistant as MCP tools.

Lets an MCP client (Claude Desktop, or anything else that speaks the protocol)
query the same corpus the web UI uses, without going through the HTTP API.
"""

import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from rag.core import ask_question, ingest_directory, search_documents

load_dotenv()

DEFAULT_DOCS_PATH = "./demo_docs"
SNIPPET_CHARS = 300

mcp = FastMCP("pdf-rag")


@mcp.tool()
def ingest_documents(directory_path: str = "") -> str:
    """Index every PDF in a folder into the vector store.

    Args:
        directory_path: Folder to index. Defaults to the configured corpus.

    Returns:
        A summary of what was indexed.
    """
    path = directory_path or os.getenv("DOCS_PATH", DEFAULT_DOCS_PATH)
    result = ingest_directory(path)
    files = [entry["file"] for entry in result["ingested"]]
    if not files:
        return f"Aucun PDF exploitable dans {path}."
    return (
        f"Ingestion terminée: {len(files)} fichiers, "
        f"{result['total_chunks']} passages. Fichiers: {', '.join(files)}"
    )


@mcp.tool()
def search_docs(query: str, n_results: int = 5) -> str:
    """Search the indexed documents and return the closest passages.

    Args:
        query: What to look for, in plain language.
        n_results: How many passages to return.

    Returns:
        The passages, each with its source file and similarity score.
    """
    results = search_documents(query, n_results=n_results)
    if not results:
        return "Aucun résultat trouvé."
    return "\n\n---\n\n".join(
        f"[{result['source']} - score {result['score']}]\n"
        f"{result['content'][:SNIPPET_CHARS]}"
        for result in results
    )


@mcp.tool()
def ask_doc(question: str) -> str:
    """Answer a question from the indexed documents.

    Args:
        question: The question, in plain language.

    Returns:
        The answer, followed by the source files it drew on.
    """
    result = ask_question(question)
    return f"{result['answer']}\n\n[Sources: {', '.join(result['sources'])}]"


if __name__ == "__main__":
    mcp.run()
