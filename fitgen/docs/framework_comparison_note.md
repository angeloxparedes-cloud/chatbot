# Framework Comparison Note — LangChain vs. LlamaIndex

**Checkpoint 3, Deliverable 13.**

## What each framework is built around

**LangChain** is organized around *chains of composable components* —
prompts, models, retrievers, and output parsers connected via LCEL
(`prompt | llm | parser`) or higher-level chain abstractions. Its retrieval
layer treats the vector store as one interchangeable component among many
(memory, tools, agents), which makes it well-suited to a project like ours
where retrieval is one step inside a larger conversational pipeline
(retrieve → inject into prompt → call LLM → persist to session memory →
send through Telegram).

**LlamaIndex** is organized around *data indexing and routing* — its core
abstraction is the `Index` (Vector, List, Tree, Keyword, etc.) with a
`QueryEngine` on top, plus `NodeParser`s that are more opinionated about
document structure (hierarchical nodes, auto-merging retrieval, sentence
windowing). It shines when the *ingestion/indexing side* is the hard part
of the problem — e.g., routing a query to different indexes depending on
document type, or retrieving parent context around a small matched chunk.

## Data routing / node indexing, concretely

| | LangChain | LlamaIndex |
|---|---|---|
| Core retrieval unit | `Document` (page_content + metadata dict) | `Node` (with explicit parent/child/next/prev relationships) |
| Multi-source routing | Compose retrievers manually (`EnsembleRetriever`, custom logic) | Built-in `RouterQueryEngine` picks an index per query type |
| Best fit here | Wiring retrieval into a stateful, multi-turn chat app | Would shine if we had to route between very differently-structured sources (e.g., structured exercise DB vs. free-text guides) as *separate indexes* rather than one shared vector store |

## What we actually used and why

We built FitGen's retrieval layer on **LangChain** (`langchain_community.
vectorstores.FAISS`, `langchain_huggingface.HuggingFaceEmbeddings`,
`langchain_google_genai.ChatGoogleGenerativeAI`, `langchain_text_splitters.
RecursiveCharacterTextSplitter`) for three reasons specific to this project:

1. **The interface is a stateful chat app, not a document Q&A tool.**
   LangChain's LCEL made it straightforward to hand-roll a lightweight
   per-Telegram-chat memory (`src/rag/chain.py::FitGenSession`) sitting
   directly next to the retrieval + generation call, without adopting a
   heavier agent/query-engine abstraction we didn't need.
2. **Our dataset doesn't need multi-index routing.** All our content
   (exercise rows + training-principle prose) lives comfortably in one
   FAISS index; LlamaIndex's routing/`NodeParser` sophistication solves a
   problem (heterogeneous multi-source indexes) that we don't have at our
   current dataset size (~85 chunks).
3. **Telegram + Gemini integration.** `python-telegram-bot` integrates
   cleanly as a thin layer calling into a LangChain-built chain; LangChain's
   `langchain-google-genai` package gave us a drop-in `ChatGoogleGenerativeAI`
   without writing raw Gemini SDK calls ourselves.

## Where LlamaIndex would be the better choice
If FitGen's dataset grew to include, say, video transcripts, a separate
nutrition database, and long-form PDF certification textbooks, LlamaIndex's
`RouterQueryEngine` + varied `NodeParser`s (sentence-window retrieval for
long PDFs, keyword indexing for the structured DB) would likely outperform
manually wiring multiple LangChain retrievers together. We would revisit
this trade-off if the dataset requirement moved past Checkpoint 3's scale
(20–30 documents) toward a genuinely heterogeneous multi-source knowledge
base.
