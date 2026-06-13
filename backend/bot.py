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

# Global variables for bot management
_bot_application = None
_bot_thread = None
_bot_loop = None
_shutdown_event = threading.Event()

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

async def _run_bot_async():
    """Internal async function to run the bot polling loop"""
    global _bot_application

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logging.warning("TELEGRAM_BOT_TOKEN environment variable not set. Bot will not start.")
        return

    try:
        application = ApplicationBuilder().token(token).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                PHOTO: [MessageHandler(filters.PHOTO, receive_photo)],
                DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
                CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_category)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )

        application.add_handler(conv_handler)

        logging.info("Bot is starting...")
        # Initialize and start the application
        await application.initialize()
        await application.start()

        _bot_application = application

        # Run polling with shutdown check
        await application.updater.start_polling()

        # Keep the polling alive until shutdown is requested
        while not _shutdown_event.is_set():
            await asyncio.sleep(1)

        logging.info("Bot polling loop ended.")

    except Exception as e:
        logging.error(f"Error in bot polling loop: {e}")
    finally:
        if _bot_application:
            try:
                await _bot_application.updater.stop()
                await _bot_application.stop()
                await _bot_application.shutdown()
                logging.info("Bot shut down gracefully.")
            except Exception as e:
                logging.error(f"Error shutting down bot: {e}")

def _bot_worker():
    """Worker function that runs in a separate thread"""
    global _bot_loop
    try:
        # Create a new event loop for this thread
        _bot_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_bot_loop)

        # Run the bot in the new loop
        _bot_loop.run_until_complete(_run_bot_async())
    except Exception as e:
        logging.error(f"Error in bot worker thread: {e}")
    finally:
        if _bot_loop:
            _bot_loop.close()

def start_bot_thread():
    """Start the bot in a separate thread to avoid blocking FastAPI's event loop"""
    global _bot_thread, _shutdown_event

    if _bot_thread and _bot_thread.is_alive():
        logging.warning("Bot thread is already running")
        return

    _shutdown_event.clear()

    _bot_thread = threading.Thread(target=_bot_worker, daemon=True, name="TelegramBot")
    _bot_thread.start()
    logging.info("Bot thread started successfully")

def stop_bot_thread():
    """Stop the bot thread gracefully"""
    global _bot_thread, _shutdown_event, _bot_application

    if not _bot_thread:
        logging.info("Bot thread is not initialized")
        return

    if _bot_thread.is_alive():
        logging.info("Stopping bot thread...")
        # Signal shutdown
        _shutdown_event.set()
        # Wait for thread to finish (with timeout)
        _bot_thread.join(timeout=10)
        if _bot_thread.is_alive():
            logging.warning("Bot thread did not stop gracefully within timeout")
    else:
        logging.info("Bot thread is already stopped")

    _bot_thread = None
    _bot_application = None
    logging.info("Bot thread cleanup complete")

async def run_bot():
    """
    Legacy function for backward compatibility.
    Now starts the bot in a separate thread instead of blocking the event loop.
    """
    start_bot_thread()
    return _bot_application

if __name__ == '__main__':
    # For standalone bot testing
    start_bot_thread()

    # Keep main thread alive
    try:
        while True:
            if not _bot_thread or not _bot_thread.is_alive():
                logging.error("Bot thread died unexpectedly")
                break
            asyncio.sleep(5)
    except KeyboardInterrupt:
        logging.info("Received interrupt signal")
    finally:
        stop_bot_thread()
