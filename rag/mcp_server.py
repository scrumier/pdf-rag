from mcp.server.fastmcp import FastMCP
from rag.core import ingest_directory, search_documents, ask_question
import os
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("pdf-rag")


@mcp.tool()
def ingest_documents(directory_path: str = "") -> str:
    """Ingere tous les PDFs d'un dossier dans la base vectorielle."""
    path = directory_path or os.getenv("DOCS_PATH", "./demo_docs")
    result = ingest_directory(path)
    total = result["total_chunks"]
    files = [r["file"] for r in result["ingested"]]
    return f"Ingestion terminee: {len(files)} fichiers, {total} chunks. Fichiers: {', '.join(files)}"


@mcp.tool()
def search_docs(query: str, n_results: int = 5) -> str:
    """Recherche semantique dans les documents ingeres. Retourne les passages les plus pertinents."""
    results = search_documents(query, n_results=n_results)
    if not results:
        return "Aucun resultat trouve."
    lines = []
    for r in results:
        lines.append(f"[{r['source']} - score {r['score']}]\n{r['content'][:300]}")
    return "\n\n---\n\n".join(lines)


@mcp.tool()
def ask_doc(question: str) -> str:
    """Pose une question en langage naturel. Claude repond en se basant sur les documents ingeres."""
    result = ask_question(question)
    sources = ", ".join(result["sources"])
    return f"{result['answer']}\n\n[Sources utilisees: {sources}]"


if __name__ == "__main__":
    mcp.run()
