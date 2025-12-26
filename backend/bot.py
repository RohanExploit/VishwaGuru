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

async def run_bot():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Warning: TELEGRAM_BOT_TOKEN environment variable not set. Bot will not start.")
        return

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

    print("Bot is starting...")
    # Initialize and start the application
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # Keep the bot running
    # In a real asyncio loop, we might wait on a future or similar.
    # But since this is a background task in FastAPI, it will run until the loop stops.
    # However, application.updater.start_polling() is non-blocking (starts background task).
    # We don't need to block here.

    # Wait for stop signal?
    # For MVP simplicity in FastAPI lifespan:
    # We just return application so we can stop it later.
    return application

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_bot())
    loop.run_forever()
