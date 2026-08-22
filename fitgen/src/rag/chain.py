"""
The RAG chain itself: retrieve -> build grounded prompt -> call Gemini,
with simple per-session conversational memory (Checkpoint 3 deliverable #12).

Design note (see docs/framework_comparison_note.md for the full writeup):
We use LangChain's LCEL (prompt | llm) style rather than the older
ConversationChain/ConversationBufferMemory classes, which are being phased
out across the LangChain ecosystem. Memory here is a plain list we manage
ourselves and inject into the prompt — this is transparent, easy to persist
per Telegram chat_id, and avoids a moving-target dependency.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from src import config
from src.rag.prompts import SYSTEM_PROMPT, CONTEXT_PROMPT_TEMPLATE
from src.rag.retriever import retrieve_as_context_block

MAX_HISTORY_TURNS = 6  # keep the last N (user, assistant) turns per session


def _build_llm() -> ChatGoogleGenerativeAI:
    config.require_gemini_key()
    return ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL_NAME,
        google_api_key=config.GEMINI_API_KEY,
        temperature=0.4,
    )


_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", CONTEXT_PROMPT_TEMPLATE),
    ]
)


@dataclass
class FitGenSession:
    """One conversational session — one per Telegram chat_id."""

    history: list[tuple[str, str]] = field(default_factory=list)
    _llm: ChatGoogleGenerativeAI | None = None

    def _get_llm(self) -> ChatGoogleGenerativeAI:
        if self._llm is None:
            self._llm = _build_llm()
        return self._llm

    def _format_history(self) -> str:
        if not self.history:
            return "(no previous messages)"
        lines = []
        for user_msg, bot_msg in self.history[-MAX_HISTORY_TURNS:]:
            lines.append(f"User: {user_msg}")
            lines.append(f"FitGen: {bot_msg}")
        return "\n".join(lines)

    def ask(self, question: str) -> str:
        context = retrieve_as_context_block(question)
        chat_history_text = self._format_history()

        messages = _prompt.format_messages(
            context=context,
            chat_history=chat_history_text,
            question=question,
        )

        llm = self._get_llm()
        response = llm.invoke(messages)
        answer = response.content

        self.history.append((question, answer))
        return answer

    def reset(self) -> None:
        self.history.clear()


# In-memory session store keyed by an arbitrary session id (e.g. Telegram chat_id).
# For a class project this is sufficient; a production version would persist
# this to Redis/a database so history survives a restart.
_sessions: dict[str, FitGenSession] = {}


def get_session(session_id: str) -> FitGenSession:
    if session_id not in _sessions:
        _sessions[session_id] = FitGenSession()
    return _sessions[session_id]
