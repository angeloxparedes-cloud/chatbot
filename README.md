# FitGen — A RAG-based Telegram Chatbot for Personalized Workout Plans

## Project purpose

FitGen is a Retrieval-Augmented Generation (RAG) chatbot that creates
personalized workout plans and answers exercise questions on Telegram. Free
workout content online is generic, and personal training is expensive. FitGen
sits in between: you tell it your goal, experience level, available equipment
and training days, and it builds a plan grounded in a curated exercise
database and a set of training-principle reference documents, rather than
relying only on what the language model remembers. It also supports natural
follow-ups such as "this hurts my knees, can you swap it?" because it keeps
conversation memory per chat.

## Live app

- **Telegram bot:** https://t.me/FitGenTest_bot (username `@FitGenTest_bot`).
  Open the link and send `/start`.
- **Hosting:** Render (free tier). Service URL: https://chatbot-4wwj.onrender.com
  (this URL only returns a "FitGen bot is running" health-check message; the
  chatbot itself lives in Telegram).
- The bot is kept awake by an UptimeRobot monitor that pings the service URL
  every 5 minutes. Because it runs on a free tier with limited CPU, replies can
  take a few seconds.

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Interface | Telegram, via `python-telegram-bot` (long polling) |
| Orchestration | LangChain (LCEL prompt-to-LLM style) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (Hugging Face, runs locally, 384-dim) |
| Vector store | FAISS (`faiss-cpu`) |
| LLM | Google Gemini via `langchain-google-genai` (`gemini-3.5-flash-lite` in the deployed version, set with `GEMINI_MODEL_NAME`) |
| Packaging / deploy | Docker, hosted on Render, monitored with UptimeRobot |

PyTorch is installed from the CPU-only wheel index (see `requirements.txt`) to
keep memory under the 512 MB limit on Render's free tier.

## How to run it locally

1. **Clone and install**
   ```bash
   git clone https://github.com/angeloxparedes-cloud/chatbot.git
   cd chatbot/fitgen
   python3 -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Configure secrets.** Copy `.env.example` to `.env` and fill in:
   - `GEMINI_API_KEY` — free key from https://aistudio.google.com/apikey
   - `TELEGRAM_BOT_TOKEN` — from [@BotFather](https://t.me/BotFather) (`/newbot`)
   - `GEMINI_MODEL_NAME` — optional; use a model currently available to your key,
     for example `gemini-3.5-flash-lite`

   Never commit your real `.env` file or paste real keys into `.env.example`.
3. **Build the vector index**
   ```bash
   python -m src.ingest.pipeline
   ```
   Re-run this whenever you add or edit files in `data/raw/`.
4. **Start the bot**
   ```bash
   python -m src.bot.telegram_bot
   ```
   Then find your bot on Telegram and send `/start`.

**With Docker:**
```bash
docker build -t fitgen-bot .
docker run --env-file .env fitgen-bot
```
The image builds the FAISS index at build time, so the container is ready as
soon as it starts. When a `PORT` environment variable is present (as on
Render), the bot also starts a tiny HTTP health-check server so web-service
hosts and uptime monitors can reach it.

## How the RAG pipeline works

```
data/raw (CSV + Markdown)
   -> Ingestion pipeline (src/ingest/pipeline.py)
        load -> clean -> chunk -> embed -> store in FAISS
   -> data/processed/faiss_index
   -> RAG chain (src/rag/chain.py)
        question -> retrieve top-k chunks -> grounded prompt -> Gemini -> answer
   -> Telegram bot (src/bot/telegram_bot.py), one session per chat
```

1. **Load.** `loaders.py` reads `exercises.csv` and the Markdown files in
   `data/raw/training_principles/`.
2. **Clean.** `preprocess.py` normalizes Unicode, strips Markdown syntax and
   collapses whitespace.
3. **Chunk.** `chunker.py` splits prose with `RecursiveCharacterTextSplitter`
   (chunk size 500, overlap 75). Each exercise row stays a single chunk so its
   instructions are never split across two results. The 57 source documents
   become 84 indexed chunks.
4. **Embed and store.** `embed_store.py` embeds every chunk with
   `all-MiniLM-L6-v2` and saves the vectors to a FAISS index.
5. **Retrieve.** When a user sends a message, `retriever.py` embeds the question
   and returns the top 4 most similar chunks (`TOP_K`, configurable).
6. **Generate.** `chain.py` combines the system prompt, the retrieved context,
   the last 6 conversation turns and the new question, then calls Gemini
   (temperature 0.4). The model is instructed to ground the plan in the
   retrieved material and to prioritize injury safety.
7. **Reply.** `telegram_bot.py` keeps a separate session (conversation memory)
   per Telegram `chat_id`, trims long answers into Telegram-sized messages, and
   supports `/start`, `/help` and `/reset`.

More detail: `docs/prompt_engineering_document.md`,
`docs/distance_metric_comparison.md` and `docs/final_technical_report.md`.

## Sample documents and where they came from

The knowledge base in `data/raw/` has two parts:

- `exercises.csv` — a 52-row structured exercise database with name, muscle
  group, equipment, difficulty, movement pattern, instructions and safety
  precautions.
- `training_principles/` — 5 Markdown reference documents: progressive
  overload, warm-up and cool-down, program design and splits, injury safety
  modifications, and reps/sets/rest guidelines.

**Origin:** TODO — replace this line with how your team actually produced these
files (for example, written by the team from general training knowledge, drafted
with an AI assistant and reviewed by the team, or adapted from named
references, with the references listed). The repository itself does not record
where the content came from, so this needs to come from you.

## Project structure

```
fitgen/
  data/raw/                 # source documents (exercises.csv, training_principles/*.md)
  data/processed/           # generated FAISS index (gitignored)
  src/
    config.py               # env var loading and central settings
    ingest/                 # loaders, preprocess, chunker, embed_store, pipeline
    rag/                    # prompts, retriever, chain
    bot/telegram_bot.py     # Telegram interface + health-check server
  docs/                     # written checkpoint deliverables
  tests/distance_metric_experiment.py
  Dockerfile
  docker-compose.yml
  requirements.txt
  .env.example
```

## Known limitations

- Conversation history is in memory and resets when the service restarts.
- The FAISS index is rebuilt from scratch each time; a much larger dataset
  would need incremental updates.
- The bot has no authentication or rate limiting beyond what Telegram provides.
- On Render's free tier the service has very limited CPU and memory, so replies
  can be slow, and Gemini models occasionally return temporary 503 "high
  demand" errors.
