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
logger = logging.getLogger(__name__)

# States for ConversationHandler
PHOTO, DESCRIPTION, CATEGORY = range(3)

# Initialize Database
Base.metadata.create_all(bind=engine)

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
        logger.warning("TELEGRAM_BOT_TOKEN environment variable not set. Bot will not start.")
        return None

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

        logger.info("Bot is starting...")
        # Initialize and start the application
        await application.initialize()
        await application.start()

        _bot_application = application

        # Run polling with shutdown check
        await application.updater.start_polling()

        logger.info("Bot started successfully and is polling for updates.")
        
        # Return application so we can stop it later
        return application
    except Exception as e:
        logger.error(f"Error initializing bot: {e}", exc_info=True)
        return None

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
