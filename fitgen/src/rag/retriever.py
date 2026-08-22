"""
Thin wrapper around the FAISS retriever: top-k similarity search, with an
optional simple keyword-based category boost (exercise vs training-principle)
so a question like "what's a good warmup" doesn't get drowned out purely by
exercise-row chunks.
"""
from langchain_community.vectorstores import FAISS

from src import config
from src.ingest.embed_store import load_index

_vectorstore: FAISS | None = None


def get_vectorstore() -> FAISS:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = load_index()
    return _vectorstore


def retrieve(query: str, k: int = config.TOP_K) -> list[str]:
    """Return the top-k most relevant chunk texts for a query, formatted
    with a light source tag so the LLM can (optionally) reference where
    a fact came from."""
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search(query, k=k)
    formatted = []
    for doc in results:
        tag = doc.metadata.get("name") or doc.metadata.get("source", "reference")
        formatted.append(f"[{tag}] {doc.page_content}")
    return formatted


def retrieve_as_context_block(query: str, k: int = config.TOP_K) -> str:
    chunks = retrieve(query, k=k)
    if not chunks:
        return "No relevant context found."
    return "\n\n".join(chunks)
