"""
Embedding generation + FAISS vector store construction.

Embedding model: sentence-transformers/all-MiniLM-L6-v2 (Hugging Face),
run locally via LangChain's HuggingFaceEmbeddings wrapper.

Why this model:
- Free and runs on CPU in seconds for a dataset this size (no API cost or
  rate limits during ingestion, unlike calling an embeddings API per chunk).
- 384-dim vectors keep the FAISS index small and fast to search.
- Well-established general-purpose sentence embedding model, strong
  baseline for semantic similarity search on short technical text like
  ours (exercise descriptions, training-principle paragraphs).
"""
from __future__ import annotations
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from src.ingest.chunker import Chunk
from src import config


def get_embedding_model() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)


def chunks_to_langchain_documents(chunks: list[Chunk]) -> list[Document]:
    return [
        Document(page_content=c.text, metadata={**c.metadata, "source": c.source, "chunk_id": c.chunk_id})
        for c in chunks
    ]


def build_and_save_index(chunks: list[Chunk], index_dir: Path = config.FAISS_INDEX_DIR) -> FAISS:
    embeddings = get_embedding_model()
    documents = chunks_to_langchain_documents(chunks)

    vectorstore = FAISS.from_documents(documents, embeddings)

    index_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(index_dir))
    return vectorstore


def load_index(index_dir: Path = config.FAISS_INDEX_DIR) -> FAISS:
    embeddings = get_embedding_model()
    return FAISS.load_local(
        str(index_dir), embeddings, allow_dangerous_deserialization=True
    )
