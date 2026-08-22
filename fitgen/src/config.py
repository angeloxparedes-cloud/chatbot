"""
Central configuration for FitGen.
All values are loaded from environment variables (see .env.example).
Keeping this in one place means every module (ingestion, RAG chain, bot)
reads the same settings instead of hardcoding paths or keys.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
FAISS_INDEX_DIR = DATA_PROCESSED_DIR / "faiss_index"

# --- API Keys / Secrets (never commit real values — use .env) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# --- Model choices ---
# Embedding model: a local Hugging Face sentence-transformers model.
# Chosen because it's free, runs locally (no per-call API cost), and is
# small/fast enough to embed a document set of this size in seconds.
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

# Chat model: Google Gemini via the Gemini Developer API.
# Model IDs on Google's side change fairly often (see ai.google.dev/gemini-api/docs/models) —
# override via env var if this one is retired.
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

# --- Chunking ---
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "75"))

# --- Retrieval ---
TOP_K = int(os.getenv("TOP_K", "4"))


def require_gemini_key() -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key "
            "from https://aistudio.google.com/apikey"
        )
    return GEMINI_API_KEY


def require_telegram_token() -> str:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. Copy .env.example to .env and add the token "
            "you got from @BotFather on Telegram."
        )
    return TELEGRAM_BOT_TOKEN
