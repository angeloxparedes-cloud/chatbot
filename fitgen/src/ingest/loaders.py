"""
Loaders: turn raw files on disk into a common in-memory representation
(list of dicts with 'text', 'source', and 'metadata') before preprocessing.

This is the "Data Source" box in the architecture diagram — it doesn't know
anything about embeddings or chunking, it just reads files.
"""
from __future__ import annotations
import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RawDocument:
    text: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


def load_markdown_dir(directory: Path) -> list[RawDocument]:
    """Load every .md file in a directory as one RawDocument each."""
    docs: list[RawDocument] = []
    for path in sorted(directory.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        docs.append(
            RawDocument(
                text=text,
                source=path.name,
                metadata={"category": "training_principle", "file_type": "markdown"},
            )
        )
    return docs


def load_exercise_csv(csv_path: Path) -> list[RawDocument]:
    """
    Load the structured exercise database. Each row becomes its own
    RawDocument, rendered as a short natural-language paragraph so it
    embeds and retrieves well alongside the markdown prose documents.
    """
    docs: list[RawDocument] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            text = (
                f"Exercise: {row['name']}. "
                f"Muscle group: {row['muscle_group']}. "
                f"Equipment needed: {row['equipment']}. "
                f"Difficulty: {row['difficulty']}. "
                f"Movement pattern: {row['movement_pattern']}. "
                f"How to perform it: {row['instructions']} "
                f"Safety notes: {row['precautions']}"
            )
            docs.append(
                RawDocument(
                    text=text,
                    source=f"exercises.csv#row{i}",
                    metadata={
                        "category": "exercise",
                        "file_type": "csv",
                        "name": row["name"],
                        "muscle_group": row["muscle_group"],
                        "equipment": row["equipment"],
                        "difficulty": row["difficulty"],
                    },
                )
            )
    return docs


def load_all_raw_documents(raw_dir: Path) -> list[RawDocument]:
    """Entry point used by the ingestion pipeline: load everything under data/raw."""
    docs: list[RawDocument] = []
    docs.extend(load_markdown_dir(raw_dir / "training_principles"))
    docs.extend(load_exercise_csv(raw_dir / "exercises.csv"))
    return docs
