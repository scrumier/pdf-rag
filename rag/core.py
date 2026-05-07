import os
import pdfplumber
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
_client = None
_collection = None
_embedder = None
_llm = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_or_create_collection("samse_docs")
    return _collection


def _get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _get_llm():
    global _llm
    if _llm is None:
        _llm = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
    return _llm


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
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


def collection_count() -> int:
    return _get_collection().count()


def ingest_directory(directory: str) -> dict:
    collection = _get_collection()
    embedder = _get_embedder()
    ingested = []
    for fname in os.listdir(directory):
        if not fname.endswith(".pdf"):
            continue
        path = os.path.join(directory, fname)
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        chunks = chunk_text(text)
        if not chunks:
            continue
        embeddings = embedder.encode(chunks).tolist()
        ids = [f"{fname}::chunk::{i}" for i in range(len(chunks))]
        metadatas = [{"source": fname, "chunk_index": i} for i in range(len(chunks))]
        collection.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
        ingested.append({"file": fname, "chunks": len(chunks)})
    return {"ingested": ingested, "total_chunks": sum(r["chunks"] for r in ingested)}


def search_documents(query: str, n_results: int = 5) -> list[dict]:
    collection = _get_collection()
    embedder = _get_embedder()
    q_emb = embedder.encode([query]).tolist()
    results = collection.query(query_embeddings=q_emb, n_results=n_results, include=["documents", "metadatas", "distances"])
    output = []
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        output.append({"content": doc, "source": meta["source"], "score": round(1 - dist, 3)})
    return output


def ask_question(question: str, n_results: int = 5) -> dict:
    chunks = search_documents(question, n_results=n_results)
    context = "\n\n---\n\n".join(
        f"[Source: {c['source']}]\n{c['content']}" for c in chunks
    )
    client = _get_llm()
    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-5"),
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es un assistant interne SAMSE. Reponds en francais a partir UNIQUEMENT des documents fournis. "
                    "Si la reponse n'est pas dans les documents, dis-le clairement. "
                    "Cite toujours la source entre crochets [nom_fichier]."
                ),
            },
            {"role": "user", "content": f"Documents:\n{context}\n\nQuestion: {question}"},
        ],
    )
    return {
        "answer": response.choices[0].message.content,
        "sources": list({c["source"] for c in chunks}),
        "chunks_used": len(chunks),
    }
