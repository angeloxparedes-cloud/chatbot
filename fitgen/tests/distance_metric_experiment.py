"""
Empirical distance-metric comparison for docs/distance_metric_comparison.md.

Uses TF-IDF vectors (deterministic, no model download required) purely to
demonstrate how Cosine, Euclidean, and Dot Product similarity rank
differently on this dataset. The production system (src/ingest/embed_store.py)
uses dense sentence-transformer embeddings + FAISS's L2 index instead of
TF-IDF — this script's job is only to illustrate metric *behavior*, which
generalizes regardless of which embedding produced the vectors.

Run: python -m tests.distance_metric_experiment
"""
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances

from src.ingest.loaders import load_all_raw_documents
from src.ingest.preprocess import preprocess_documents
from src.ingest.chunker import chunk_documents

QUERIES = [
    "beginner 3 day full body workout with dumbbells",
    "my knees hurt during squats, what should I do",
    "how many sets and reps for building muscle",
]


def main():
    raw = load_all_raw_documents(Path("data/raw"))
    cleaned = preprocess_documents(raw)
    chunks = chunk_documents(cleaned)
    texts = [c.text for c in chunks]
    labels = [c.chunk_id for c in chunks]

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(texts)  # (n_chunks, vocab_size), L2-normalizable

    for query in QUERIES:
        q_vec = vectorizer.transform([query])

        cos_scores = cosine_similarity(q_vec, matrix).flatten()
        euc_scores = euclidean_distances(q_vec, matrix).flatten()  # lower = closer
        dot_scores = (q_vec @ matrix.T).toarray().flatten()

        top_cos = np.argsort(-cos_scores)[:3]
        top_euc = np.argsort(euc_scores)[:3]
        top_dot = np.argsort(-dot_scores)[:3]

        print(f"\n=== Query: \"{query}\" ===")
        print("-- Cosine similarity (higher=better) --")
        for i in top_cos:
            print(f"   {cos_scores[i]:.4f}  {labels[i]}")
        print("-- Euclidean distance (lower=better) --")
        for i in top_euc:
            print(f"   {euc_scores[i]:.4f}  {labels[i]}")
        print("-- Dot product (higher=better) --")
        for i in top_dot:
            print(f"   {dot_scores[i]:.4f}  {labels[i]}")


if __name__ == "__main__":
    main()
