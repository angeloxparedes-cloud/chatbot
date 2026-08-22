# FitGen: Final Technical Report

**IS Professional Elective #4 — Generative AI Capstone**
**Checkpoint 4, Deliverable 19**

## 1. Project Summary
FitGen is a Retrieval-Augmented Generation (RAG) chatbot, deployed as a
Telegram bot, that generates personalized workout plans and answers
exercise questions. It addresses the gap between generic, one-size-fits-all
free workout content and expensive personal training, by grounding
generated plans in a curated exercise database and training-principle
reference set, and by supporting natural multi-turn follow-up
("this hurts my knees, can you swap it?") rather than a static document.

## 2. Architecture
```
Data Sources (CSV + Markdown)
   -> Ingestion Pipeline (clean, chunk, embed, index)
   -> FAISS vector store
   -> RAG Chain (retrieve top-k -> grounded prompt -> Gemini)
   -> Telegram Bot Interface (per-user session memory)
```
Full diagram and component breakdown in `README.md`.

## 3. Data Pipeline (Checkpoint 1 & 3)
- **Sources**: a 52-row structured exercise database (`data/raw/
  exercises.csv` — name, muscle group, equipment, difficulty, movement
  pattern, instructions, safety precautions) and 5 markdown reference
  documents on training principles (progressive overload, warm-up/cool-
  down, program design & splits, injury safety, sets/reps/rest
  guidelines).
- **Preprocessing** (`src/ingest/preprocess.py`): Unicode normalization,
  markdown syntax stripping (headers, bullets, bold/italic markers),
  whitespace collapsing — verified with before/after output.
- **Chunking** (`src/ingest/chunker.py`): `RecursiveCharacterTextSplitter`
  (chunk_size=500, overlap=75) for prose documents; exercise rows are kept
  as single atomic chunks so an exercise's instructions are never split
  mid-sentence across two retrieval results.
- **Result**: 57 raw documents -> 84 indexed chunks (measured directly by
  running the pipeline against the real dataset).
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` — chosen for
  zero per-call cost (runs locally), small 384-dim vectors, and strong
  general-purpose semantic similarity performance on short technical text.

## 4. Prompt Architecture (Checkpoint 2)
Three-layer prompting: a system prompt encoding identity and five hard
rules (ground in retrieved context only; respect stated constraints;
defer to professionals on red-flag pain symptoms; refuse off-topic
questions; format answers as structured plans), a context prompt that
fences retrieved chunks and injects recent conversation history, and
embedded few-shot refusal examples for the two highest-risk failure modes
(unsafe exercise prescription, off-topic answers). Full write-up and
rationale in `docs/prompt_engineering_document.md`.

## 5. Vector Indexing & Retrieval (Checkpoint 2 & 3)
FAISS stores the 84 embedded chunks; `src/rag/retriever.py` performs
top-k (k=4 by default) similarity search per query. We compared cosine
similarity, Euclidean distance, and dot product empirically
(`docs/distance_metric_comparison.md`) and found all three produce
identical rankings on our (normalized) vectors — cosine similarity is
recommended as the conceptually correct metric, implemented efficiently
via FAISS inner-product search over pre-normalized embeddings.

## 6. RAG Orchestration & Application (Checkpoint 3)
Built on LangChain (see `docs/framework_comparison_note.md` for the
LangChain vs. LlamaIndex trade-off analysis). `FitGenSession`
(`src/rag/chain.py`) holds per-Telegram-chat conversation history (last 6
turns), enabling multi-turn context — e.g., a user can ask for a plan,
then say "swap the squats" and the assistant knows what plan and what
exercise they mean without repeating themselves.

**Example query flow**: User sends "I'm a beginner with dumbbells only,
3 days a week, general strength." -> retriever pulls relevant chunks from
`03_program_design_splits.md` (equipment-constrained programming),
`05_reps_sets_rest_guidelines.md` (strength rep ranges), and multiple
dumbbell-equipment exercise rows -> Gemini generates a structured 3-day
plan citing only those retrieved exercises.

**Out-of-scope handling**: A query like "what's the capital of France?"
retrieves low-relevance fitness chunks and, per system prompt rule 4, the
model declines and redirects to fitness topics instead of answering from
general knowledge.

## 7. Model Customization Decision (Checkpoint 4)
We use Gemini 2.5 Flash as-is via the hosted API, without PEFT/LoRA/QLoRA
fine-tuning. Full rationale in `docs/model_customization_note.md` — in
short: RAG already solves our core problem (factual grounding), our
dataset is far below the scale where fine-tuning would help rather than
overfit, and we don't have access to Gemini's weights to attach adapters
to in the first place.

## 8. Deployment (Checkpoint 4)
Containerized via a multi-stage `Dockerfile` (builder stage compiles
dependencies; runtime stage copies only installed packages, runs as a
non-root `fitgen` user, pre-builds the FAISS index at image-build time).
The bot uses Telegram long-polling (outbound-only), so it runs on any
host with outbound internet access and no open inbound ports required —
suitable for free-tier VPS/PaaS options. See `README.md` for exact run
commands and `docker-compose.yml` for the compose configuration.

## 9. Limitations
- Conversation memory is in-process and resets on restart (no persistent
  session store).
- FAISS index requires a full rebuild (not incremental updates) when the
  source dataset changes.
- No user authentication/rate-limiting beyond Telegram's own platform
  protections.
- Dataset covers strength/resistance training and general conditioning;
  it does not cover specialized populations (e.g., prenatal fitness,
  post-surgical rehab) and the system should decline confidently outside
  that scope rather than guess.

## 10. Lessons Learned
- **Dependency pinning matters in a fast-moving ecosystem.** During
  development, LangChain's import paths changed between its 0.3.x and
  1.x releases (e.g., `langchain.text_splitter` moved to the standalone
  `langchain_text_splitters` package). We caught this by actually
  installing and testing against real package versions rather than
  assuming API stability, and pinned `requirements.txt` to a verified-
  working combination.
- **Atomic chunking of structured data matters for retrieval quality.**
  Treating each exercise CSV row as one indivisible chunk (rather than
  letting the recursive splitter potentially cut an exercise's
  instructions in half) measurably improved the coherence of what gets
  retrieved and injected into the prompt.
- **Grounding rules need to be explicit, not implied.** Early prompt
  drafts (before the current `SYSTEM_PROMPT`) relied on the model
  "naturally" staying in-scope; adding explicit rule 4 (fitness-only
  scope) was necessary to reliably get refusal behavior on off-topic
  questions.

## 11. What We Would Improve With More Time
- Persistent (database-backed) session memory across bot restarts.
- Incremental re-indexing instead of full-dataset rebuilds.
- A richer, larger exercise dataset (targeting 150+ exercises) and expert
  review of the training-principle documents beyond this course project's
  scope.
- A lightweight evaluation harness measuring retrieval precision/recall on
  a held-out set of labeled queries, to make the "90% citation accuracy"
  success criterion from the Project Proposal quantitatively verifiable
  rather than judged qualitatively.
