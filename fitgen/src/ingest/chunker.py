"""
Chunking: splits cleaned documents into overlapping windows small enough
to embed meaningfully and retrieve precisely.

Uses LangChain's RecursiveCharacterTextSplitter, which tries to split on
paragraph -> sentence -> word boundaries in order, so chunks stay
semantically coherent instead of cutting mid-sentence.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.ingest.loaders import RawDocument
from src import config


@dataclass
class Chunk:
    text: str
    source: str
    chunk_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


def chunk_documents(
    docs: list[RawDocument],
    chunk_size: int = config.CHUNK_SIZE,
    chunk_overlap: int = config.CHUNK_OVERLAP,
) -> list[Chunk]:
    """
    Exercise rows (short, already-atomic) are kept as a single chunk each so
    a single exercise's instructions never get split across two chunks.
    Longer prose (training principle markdown) gets recursively split.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[Chunk] = []
    for doc in docs:
        if doc.metadata.get("category") == "exercise":
            # Exercise rows are short and atomic — don't split them further.
            chunks.append(
                Chunk(
                    text=doc.text,
                    source=doc.source,
                    chunk_id=f"{doc.source}",
                    metadata=doc.metadata,
                )
            )
            continue

        pieces = splitter.split_text(doc.text)
        for i, piece in enumerate(pieces):
            chunks.append(
                Chunk(
                    text=piece,
                    source=doc.source,
                    chunk_id=f"{doc.source}::chunk{i}",
                    metadata=doc.metadata,
                )
            )
    return chunks
