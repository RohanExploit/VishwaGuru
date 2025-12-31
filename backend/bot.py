import os
import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
from database import engine, SessionLocal
from models import Base, Issue

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
application = None

async def build_app():
    """Builds and returns the bot application."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Warning: TELEGRAM_BOT_TOKEN environment variable not set. Bot will not start.")
        # Return a dummy mock if token is missing so imports don't fail,
        # but startup checks in main.py will handle it.
        # Actually, for the purpose of 'import application' to work in main.py,
        # we need to initialize 'application' at module level or provide a getter.
        # But ApplicationBuilder() requires a token.
        return None

    app = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, receive_photo)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_category)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    return app

# We try to build it at import time if token exists,
# otherwise we might need to lazy load it or handle it in main.py differently.
# Ideally, main.py should not import 'application' directly if it's conditional.
# But existing main.py did: 'from bot import application'.
# To support that, we need 'application' to be defined here.
try:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
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
    else:
        # Create a dummy object or None
        # If None, main.py might crash if it tries to use it without check.
        # main.py code:
        # await application.initialize()
        # So it expects an object.
        class MockApp:
            async def initialize(self): pass
            class Updater:
                async def start_polling(self): pass
                async def stop(self): pass
            updater = Updater()
            async def start(self): pass
            async def stop(self): pass
            async def shutdown(self): pass

        application = MockApp()
        print("Telegram Bot Token missing, using Mock Application.")

except Exception as e:
    print(f"Error building bot app at module level: {e}")
    application = None

async def run_bot():
    """Legacy entry point, reused if needed"""
    if application:
         # If already built
         return application
    return await build_app()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_bot())
    loop.run_forever()
