import os
import logging
import asyncio
import threading
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
from backend.database import engine, SessionLocal

from backend.models import Base, Issue


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# States for ConversationHandler
PHOTO, DESCRIPTION, CATEGORY = range(3)

# Initialize Database
Base.metadata.create_all(bind=engine)

# Create a global application instance placeholder
application = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! Welcome to VishwaGuru.\n"
        "Let's fix our community together.\n\n"
        "Please send me a photo of the issue you want to report."
    )
    return PHOTO

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    photo_file = await update.message.photo[-1].get_file()

    # Ensure data/uploads directory exists
    os.makedirs("data/uploads", exist_ok=True)

    # Save photo
    # We use a simple naming convention: telegram_userid_fileuniqueid.jpg
    filename = f"data/uploads/telegram_{user.id}_{photo_file.file_unique_id}.jpg"
    await photo_file.download_to_drive(filename)

    # Store filename in context to save later
    context.user_data['photo_path'] = filename

    await update.message.reply_text(
        "Photo received! Now, please describe the issue in a few words."
    )
    return DESCRIPTION

async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data['description'] = text

    categories = [["Road", "Water"], ["Streetlight", "Garbage"], ["College Infra", "Women Safety"]]

    await update.message.reply_text(
        "Got it. Which category does this belong to?",
        reply_markup=ReplyKeyboardMarkup(categories, one_time_keyboard=True, resize_keyboard=True)
    )
    return CATEGORY

def save_issue_to_db(description, category, photo_path):
    """
    Synchronous helper to save issue to DB.
    To be run in a threadpool to avoid blocking the async event loop.
    """
    db = SessionLocal()
    try:
        new_issue = Issue(
            description=description,
            category=category,
            image_path=photo_path,
            source='telegram'
        )
        db.add(new_issue)
        db.commit()
        db.refresh(new_issue)
        return new_issue.id
    except Exception as e:
        logging.error(f"Error saving to DB: {e}")
        raise e
    finally:
        db.close()

async def receive_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    photo_path = context.user_data.get('photo_path')
    description = context.user_data.get('description')

    try:
        # Save to Database using threadpool to prevent blocking the event loop
        # asyncio.to_thread runs the synchronous function in a separate thread (Python 3.9+)
        issue_id = await asyncio.to_thread(save_issue_to_db, description, category, photo_path)

        await update.message.reply_text(
            f"Thank you! Your issue has been reported.\n"
            f"Reference ID: #{issue_id}\n\n"
            f"We will generate an action plan for you soon.",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception:
        await update.message.reply_text("Sorry, something went wrong while saving your issue.")
        return ConversationHandler.END

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Issue reporting cancelled.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# Global variable to hold the bot application
# --- Application construction -------------------------------------------------

logger = logging.getLogger(__name__)

application = None
_bot_application = None
_bot_thread = None
_shutdown_event = None


def _build_conversation_handler() -> ConversationHandler:
    """The bot's single conversation flow: photo -> description -> category."""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, receive_photo)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_category)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


class MockApplication:
    """Stand-in used when TELEGRAM_BOT_TOKEN is absent.

    `backend.main` imports `application` unconditionally and awaits its
    lifecycle methods, so this has to be an object rather than None.
    """

    class _Updater:
        async def start_polling(self):
            return None

        async def stop(self):
            return None

    def __init__(self):
        self.updater = self._Updater()

    async def initialize(self):
        return None

    async def start(self):
        return None

    async def stop(self):
        return None

    async def shutdown(self):
        return None


def _make_application():
    """Build a real Application when a token is configured, else a mock."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set - using MockApplication.")
        return MockApplication()
    app = ApplicationBuilder().token(token).build()
    app.add_handler(_build_conversation_handler())
    return app


async def build_app():
    """Async accessor kept for callers that expect a coroutine."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return None
    return _make_application()


try:
    application = _make_application()
except Exception:
    logger.exception("Error building bot application at import time")
    application = None


async def run_bot():
    """Legacy entry point, reused if needed."""
    if application:
        return application
    return await build_app()


# --- Threaded runner ----------------------------------------------------------
#
# Running the bot's polling loop inside the FastAPI lifespan means every uvicorn
# worker opens its own long-poll against Telegram, and Telegram rejects the
# extras with HTTP 409 -- so the API could never scale past one worker. Owning
# the loop in a dedicated thread here lets the bot be started independently of
# the web process.


def start_bot_thread():
    """Start the polling loop on a background thread. Idempotent."""
    global _bot_thread, _shutdown_event, _bot_application

    if _bot_thread is not None and _bot_thread.is_alive():
        return _bot_thread

    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        logger.warning("TELEGRAM_BOT_TOKEN not set - bot thread not started.")
        return None

    _shutdown_event = threading.Event()

    def _run() -> None:
        global _bot_application
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            _bot_application = _make_application()
            loop.run_until_complete(_bot_application.initialize())
            loop.run_until_complete(_bot_application.start())
            loop.run_until_complete(_bot_application.updater.start_polling())
            logger.info("Telegram bot polling started.")
            while not _shutdown_event.is_set():
                loop.run_until_complete(asyncio.sleep(0.5))
        except Exception:
            logger.exception("Telegram bot thread terminated with an error")
        finally:
            try:
                if _bot_application is not None:
                    loop.run_until_complete(_bot_application.updater.stop())
                    loop.run_until_complete(_bot_application.stop())
                    loop.run_until_complete(_bot_application.shutdown())
            except Exception:
                logger.exception("Error during Telegram bot shutdown")
            finally:
                loop.close()
                logger.info("Telegram bot thread stopped.")

    _bot_thread = threading.Thread(target=_run, name="telegram-bot", daemon=True)
    _bot_thread.start()
    return _bot_thread


def stop_bot_thread(timeout: float = 10.0) -> None:
    """Signal the polling loop to finish and wait for the thread to exit."""
    global _bot_thread

    if _shutdown_event is not None:
        _shutdown_event.set()

    if _bot_thread is not None and _bot_thread.is_alive():
        _bot_thread.join(timeout=timeout)
        if _bot_thread.is_alive():
            logger.error("Telegram bot thread did not stop within %ss", timeout)

    _bot_thread = None


if __name__ == "__main__":
    if start_bot_thread() is None:
        raise SystemExit("Cannot start bot: TELEGRAM_BOT_TOKEN is not set.")
    try:
        while _bot_thread is not None and _bot_thread.is_alive():
            _bot_thread.join(timeout=5)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        stop_bot_thread()
