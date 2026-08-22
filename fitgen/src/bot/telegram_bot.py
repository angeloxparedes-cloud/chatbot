"""
FitGen Telegram bot — the deployed interface (Checkpoint 4 deliverable #16).

Each Telegram chat gets its own FitGenSession so multi-turn conversation
memory (Checkpoint 3 deliverable #12) is per-user, not global.

Run locally:
    python -m src.bot.telegram_bot

Requires TELEGRAM_BOT_TOKEN and GEMINI_API_KEY set (see .env.example).
"""
import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src import config
from src.rag.chain import get_session

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

WELCOME_MESSAGE = (
    "💪 Welcome to *FitGen*!\n\n"
    "Tell me your fitness goal, experience level, available equipment, and "
    "how many days a week you can train, and I'll put together a workout plan.\n\n"
    "Example: \"I'm a beginner, I have dumbbells only, and I can train 3 days "
    "a week. My goal is general strength.\"\n\n"
    "You can also ask follow-up questions like \"can you swap the squats, "
    "they hurt my knees\" — I'll remember our conversation.\n\n"
    "Commands:\n"
    "/reset — start a new conversation\n"
    "/help — show this message again"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    get_session(chat_id).reset()
    await update.message.reply_text("Conversation history cleared. Let's start fresh!")


def _extract_text(raw) -> str:
    """Normalize whatever session.ask() returns into plain display text.

    Some Gemini SDK/LangChain versions return response.content as a list
    of content blocks rather than a plain string, e.g.:
    [{'type': 'text', 'text': '...', 'extras': {'signature': '<large blob>'}}]
    We only want the 'text' fields — the 'signature' field is internal
    model metadata, not meant for the user, and can be large enough to
    blow past Telegram's message-length limit if serialized by mistake.
    """
    if isinstance(raw, str):
        return raw.strip()

    if isinstance(raw, list):
        parts = []
        for block in raw:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts).strip()

    return str(raw).strip()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    user_text = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    session = get_session(chat_id)
    try:
        raw = session.ask(user_text)
        answer = _extract_text(raw)
        if not answer:
            answer = "Sorry, I couldn't generate a response. Please try again."
    except Exception:
        logger.exception("Error generating response")
        answer = (
            "Sorry, something went wrong generating your plan. Please try "
            "again in a moment."
        )

    # Telegram caps messages at 4096 characters (measured in UTF-16 code
    # units, not Python characters, so emoji-heavy text can exceed a raw
    # length-based split). We use a smaller 3000-char buffer to stay safely
    # under the limit, and fall back to a plain-text retry if a chunk still
    # fails to send (e.g. because markdown got cut mid-tag across chunks).
    CHUNK_SIZE = 3000
    for i in range(0, len(answer), CHUNK_SIZE):
        chunk = answer[i : i + CHUNK_SIZE]
        try:
            await update.message.reply_text(chunk, parse_mode="Markdown")
        except Exception:
            logger.exception(f"Failed to send chunk starting at {i}, len={len(chunk)}")
            await update.message.reply_text(chunk)  # retry without markdown


def build_app() -> Application:
    token = config.require_telegram_token()
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return application


def main() -> None:
    app = build_app()
    logger.info("FitGen Telegram bot starting (long polling)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()