"""
End-to-end ingestion pipeline (Checkpoint 3 deliverable #10):
parse -> clean -> chunk -> embed -> store, in one automated run.

Usage:
    python -m src.ingest.pipeline
"""
import time

from src import config
from src.ingest.loaders import load_all_raw_documents
from src.ingest.preprocess import preprocess_documents
from src.ingest.chunker import chunk_documents
from src.ingest.embed_store import build_and_save_index


def run_pipeline() -> None:
    t0 = time.time()

    print(f"[1/4] Loading raw documents from {config.DATA_RAW_DIR} ...")
    raw_docs = load_all_raw_documents(config.DATA_RAW_DIR)
    print(f"      Loaded {len(raw_docs)} raw documents.")

    print("[2/4] Cleaning / normalizing text ...")
    cleaned_docs = preprocess_documents(raw_docs)

    print(f"[3/4] Chunking (chunk_size={config.CHUNK_SIZE}, overlap={config.CHUNK_OVERLAP}) ...")
    chunks = chunk_documents(cleaned_docs)
    print(f"      Produced {len(chunks)} chunks.")

    print(f"[4/4] Embedding with '{config.EMBEDDING_MODEL_NAME}' and building FAISS index ...")
    build_and_save_index(chunks)
    print(f"      Index saved to {config.FAISS_INDEX_DIR}")

    print(f"\nDone in {time.time() - t0:.1f}s. Run the RAG app or the Telegram bot next.")


if __name__ == "__main__":
    run_pipeline()
