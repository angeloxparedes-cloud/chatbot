"""
Text cleaning and normalization, applied before chunking/embedding.
This is deliberately simple and explainable — the goal (per Checkpoint 1)
is demonstrable before/after cleaning, not heavy NLP.
"""
import re
import unicodedata

from src.ingest.loaders import RawDocument


def clean_text(text: str) -> str:
    """Normalize whitespace, unicode, and strip markdown noise that doesn't
    add retrieval value (heading hashes, bullet markers, extra blank lines)."""
    # Normalize unicode (e.g. smart quotes -> plain quotes)
    text = unicodedata.normalize("NFKC", text)

    # Strip markdown heading markers but keep the heading text itself
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

    # Collapse bullet/numbered list markers into plain text
    text = re.sub(r"^[\-\*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)

    # Bold/italic markdown markers
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)

    # Collapse multiple blank lines / excess whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


def preprocess_documents(docs: list[RawDocument]) -> list[RawDocument]:
    cleaned = []
    for doc in docs:
        cleaned.append(
            RawDocument(text=clean_text(doc.text), source=doc.source, metadata=doc.metadata)
        )
    return cleaned


if __name__ == "__main__":
    # Quick before/after demo, matching the Checkpoint 1 deliverable.
    sample = "## Progressive Overload\n\n- **Increase load** by *2.5-5%*\n1. Do this\n\n\n\nExtra blank lines above."
    print("BEFORE:\n", repr(sample))
    print("\nAFTER:\n", repr(clean_text(sample)))
