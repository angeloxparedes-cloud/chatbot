# FitGen — A RAG-based Telegram Chatbot for Personalized Workout Plans

A Retrieval-Augmented Generation chatbot that generates personalized
workout plans grounded in a curated exercise database and training-
principle reference set, deployed as a Telegram bot.

## Architecture

```
 data/raw (CSV + Markdown)
        |
        v
 [Ingestion Pipeline]  src/ingest/pipeline.py
   load -> clean -> chunk -> embed (HuggingFace) -> store (FAISS)
        |
        v
 data/processed/faiss_index
        |
        v
 [RAG Chain]  src/rag/chain.py
   user question --retrieve(top-k)--> context
   context + chat_history + question --> prompt --> Gemini --> answer
        |
        v
 [Telegram Bot]  src/bot/telegram_bot.py
   python-telegram-bot <-> FitGenSession (per chat_id, holds memory)
```

- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (Hugging Face,
  runs locally, free)
- **Vector store**: FAISS (`langchain_community.vectorstores.FAISS`)
- **LLM**: Google Gemini (`gemini-2.5-flash`) via `langchain-google-genai`
- **Orchestration**: LangChain (see `docs/framework_comparison_note.md`
  for why over LlamaIndex)
- **Interface**: Telegram, via `python-telegram-bot`

## Project structure

```
fitgen/
  data/
    raw/                    # source documents (edit/add here)
      exercises.csv
      training_principles/*.md
    processed/               # generated FAISS index (gitignored)
  src/
    config.py                # env var loading, central settings
    ingest/                  # Checkpoint 1 & 3: data pipeline
      loaders.py
      preprocess.py
      chunker.py
      embed_store.py
      pipeline.py             # <- run this to (re)build the index
    rag/                      # Checkpoint 2 & 3: prompts + retrieval + chain
      prompts.py
      retriever.py
      chain.py
    bot/
      telegram_bot.py         # Checkpoint 4: deployed interface
  docs/                       # written deliverables (see below)
  tests/
    distance_metric_experiment.py
  Dockerfile
  docker-compose.yml
  requirements.txt
  .env.example
```

## Setup

### 1. Clone and install
```bash
git clone <your-repo-url>
cd fitgen
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure secrets
```bash
cp .env.example .env
```
Edit `.env`:
- `GEMINI_API_KEY` — get a free key at https://aistudio.google.com/apikey
- `TELEGRAM_BOT_TOKEN` — get this from [@BotFather](https://t.me/BotFather)
  on Telegram: `/newbot`, follow the prompts, copy the token it gives you.

### 3. Build the vector index
```bash
python -m src.ingest.pipeline
```
This reads everything in `data/raw/`, cleans it, chunks it, embeds it, and
saves a FAISS index to `data/processed/faiss_index/`. Re-run this any time
you add or edit files in `data/raw/`.

### 4. Run the bot locally
```bash
python -m src.bot.telegram_bot
```
Open Telegram, find your bot (the username you gave BotFather), and send
`/start`.

## Running with Docker (recommended for deployment)

```bash
docker build -t fitgen-bot .
docker run --env-file .env fitgen-bot
```
or with Compose:
```bash
docker compose up --build -d
docker compose logs -f
```
The image builds the FAISS index at build time (see `Dockerfile`), so the
container is ready to serve as soon as it starts. The bot uses Telegram's
long-polling, so it needs outbound internet access but no open inbound
ports — it will run on any host with internet access (a VPS, Render,
Railway, Fly.io, a Raspberry Pi, etc.).

**Deployment evidence for Checkpoint 4**: run the container on a host
outside your local machine (a free-tier VPS or PaaS works fine) and take a
screenshot of `docker ps` / the platform's dashboard showing it running,
plus a screenshot of a live conversation with the bot on Telegram.

## Running the distance-metric experiment (Checkpoint 2 deliverable)
```bash
python -m tests.distance_metric_experiment
```

## Documentation index
| File | Checkpoint deliverable |
|---|---|
| `docs/prompt_engineering_document.md` | CP2 #6 — Prompt Engineering Document |
| `docs/distance_metric_comparison.md` | CP2 #9 — Distance Metric Comparison |
| `docs/framework_comparison_note.md` | CP3 #13 — Framework Comparison Note |
| `docs/model_customization_note.md` | CP4 #15 — Model Customization Note |
| `docs/final_technical_report.md` | CP4 #19 — Final Technical Report |

## Known limitations
- In-memory conversation history (`src/rag/chain.py`) resets if the process
  restarts. For production use beyond this course project, back it with
  Redis or a database.
- FAISS index is a flat file rebuilt from scratch each time; at a much
  larger dataset size, an incremental-update strategy would be needed
  instead of full rebuilds.
- No authentication/rate-limiting on the Telegram bot beyond what Telegram
  itself provides — fine for a class demo, not for a public production
  launch.

## Team
Add your Checkpoint 1 Project Proposal PDF (team roles & responsibilities)
into `docs/` as `project_proposal.pdf` to keep all checkpoint deliverables
in one place, per the course's repository requirements.
