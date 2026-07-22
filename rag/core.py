"""Retrieval-augmented question answering over a folder of PDFs.

The pipeline is deliberately short. PDFs are split into overlapping chunks,
each chunk is turned into an embedding (a vector whose distance to another
vector reflects how close the two texts are in meaning), and the vectors live
in a local Chroma database. A question is embedded the same way, the nearest
chunks come back, and the model is asked to answer from those chunks only.

That last constraint is the whole point: the model is not asked what it knows,
it is asked what these passages say, which is why it can cite.
"""

import os
from functools import lru_cache

import chromadb
import pdfplumber
from chromadb.api.models.Collection import Collection
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
COLLECTION_NAME = "docs"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-sonnet-4.5"
MAX_TOKENS = 1024

# Small, fast, runs on CPU. Good enough to retrieve on; swap it for a
# multilingual model if the corpus is not mostly one language.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Chunks are measured in words. 300 keeps a chunk inside one topic, and the
# 50-word overlap stops an answer being cut in half at a boundary.
DEFAULT_CHUNK_SIZE = 300
DEFAULT_OVERLAP = 50
DEFAULT_N_RESULTS = 5

SYSTEM_PROMPT = (
    "Tu es un assistant documentaire interne. Réponds en français à partir "
    "UNIQUEMENT des documents fournis. Si la réponse n'est pas dans les "
    "documents, dis-le clairement au lieu de deviner. Cite toujours la source "
    "entre crochets [nom_fichier]."
)


@lru_cache(maxsize=1)
def _get_collection() -> Collection:
    """Open the vector store, once per process.

    Returns:
        The Chroma collection holding every ingested chunk.
    """
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(COLLECTION_NAME)


@lru_cache(maxsize=1)
def _get_embedder() -> SentenceTransformer:
    """Load the embedding model, once per process.

    It weighs enough that reloading it per request would dominate response
    time, hence the cache.

    Returns:
        The sentence-transformers model.
    """
    return SentenceTransformer(EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def _get_llm() -> OpenAI:
    """Open the OpenRouter client, once per process.

    Returns:
        An OpenAI-compatible client pointed at OpenRouter.
    """
    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    """Split text into overlapping windows of words.

    Args:
        text: The document text.
        chunk_size: Words per chunk.
        overlap: Words each chunk repeats from the previous one.

    Returns:
        The chunks, in reading order. Empty if the text holds nothing.
    """
    if not text.strip():
        return []

    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks


def extract_pdf_text(pdf_path: str) -> str:
    """Read every page of a PDF as text.

    Args:
        pdf_path: Path to the PDF.

    Returns:
        The pages joined by newlines. Empty for a scan with no text layer.
    """
    with pdfplumber.open(pdf_path) as pdf:
        pages = [page.extract_text() for page in pdf.pages]
    return "\n".join(page for page in pages if page)


def collection_count() -> int:
    """Count the chunks currently indexed.

    Returns:
        Number of chunks in the store.
    """
    return _get_collection().count()


def ingest_directory(directory: str) -> dict:
    """Index every PDF in a folder.

    Chunk ids are derived from the filename, so re-ingesting a document
    replaces its chunks instead of duplicating them.

    Args:
        directory: Folder to scan, not recursive.

    Returns:
        What was ingested, per file, and the total chunk count.
    """
    collection = _get_collection()
    embedder = _get_embedder()

    ingested = []
    for filename in sorted(os.listdir(directory)):
        if not filename.lower().endswith(".pdf"):
            continue

        chunks = chunk_text(extract_pdf_text(os.path.join(directory, filename)))
        if not chunks:
            continue

        collection.upsert(
            ids=[f"{filename}::chunk::{i}" for i in range(len(chunks))],
            embeddings=embedder.encode(chunks).tolist(),
            documents=chunks,
            metadatas=[
                {"source": filename, "chunk_index": i} for i in range(len(chunks))
            ],
        )
        ingested.append({"file": filename, "chunks": len(chunks)})

    return {
        "ingested": ingested,
        "total_chunks": sum(entry["chunks"] for entry in ingested),
    }


def search_documents(query: str, n_results: int = DEFAULT_N_RESULTS) -> list[dict]:
    """Find the chunks closest in meaning to a query.

    Args:
        query: What to look for, in plain language.
        n_results: How many chunks to return.

    Returns:
        The matches, closest first, each with its text, source file and a
        similarity score where 1 is an exact match.
    """
    results = _get_collection().query(
        query_embeddings=_get_embedder().encode([query]).tolist(),
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    return [
        {
            "content": document,
            "source": metadata["source"],
            "score": round(1 - distance, 3),
        }
        for document, metadata, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
            strict=True,
        )
    ]


def ask_question(question: str, n_results: int = DEFAULT_N_RESULTS) -> dict:
    """Answer a question from the indexed documents.

    Args:
        question: The question, in plain language.
        n_results: How many chunks to put in front of the model.

    Returns:
        The answer, the source files it drew on, and how many chunks were used.

    Raises:
        ValueError: If the model returned an empty answer.
    """
    chunks = search_documents(question, n_results=n_results)
    context = "\n\n---\n\n".join(
        f"[Source: {chunk['source']}]\n{chunk['content']}" for chunk in chunks
    )

    response = _get_llm().chat.completions.create(
        model=os.getenv("LLM_MODEL", DEFAULT_MODEL),
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Documents:\n{context}\n\nQuestion: {question}",
            },
        ],
    )

    answer = response.choices[0].message.content
    if not answer:
        raise ValueError("Le modèle n'a renvoyé aucune réponse.")

    return {
        "answer": answer,
        "sources": sorted({chunk["source"] for chunk in chunks}),
        "chunks_used": len(chunks),
    }
