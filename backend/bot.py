"""
Telegram Bot for VishwaGuru Issue Reporting

Handles issue reporting via Telegram using a multi-step conversation flow:
1. Collect issue photo
2. Get issue description
3. Select issue category
4. Save to database
"""
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
    """Send welcome message and request issue photo to start conversation."""
    await update.message.reply_text(
        "Namaste! Welcome to VishwaGuru.\n"
        "Let's fix our community together.\n\n"
        "Please send me a photo of the issue you want to report."
    )
    return PHOTO

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save photo and request issue description."""
    user = update.message.from_user
    photo_file = await update.message.photo[-1].get_file()

    # Ensure data/uploads directory exists
    os.makedirs("data/uploads", exist_ok=True)

    # Save photo with naming convention: telegram_userid_fileuniqueid.jpg
    filename = f"data/uploads/telegram_{user.id}_{photo_file.file_unique_id}.jpg"
    await photo_file.download_to_drive(filename)

    # Store filename in context for later database save
    context.user_data['photo_path'] = filename

    await update.message.reply_text(
        "Photo received! Now, please describe the issue in a few words."
    )
    return DESCRIPTION

async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store description and ask user to select issue category."""
    issue_description = update.message.text
    context.user_data['description'] = issue_description

    issue_categories = [["Road", "Water"], ["Streetlight", "Garbage"], ["College Infra", "Women Safety"]]

    await update.message.reply_text(
        "Got it. Which category does this belong to?",
        reply_markup=ReplyKeyboardMarkup(issue_categories, one_time_keyboard=True, resize_keyboard=True)
    )
    return CATEGORY

def save_issue_to_db(description, category, photo_path):
    """Save issue to database synchronously. Run in threadpool to avoid blocking async."""
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
    """Save issue category, store in database, and send confirmation with issue ID."""
    selected_category = update.message.text
    photo_path = context.user_data.get('photo_path')
    issue_description = context.user_data.get('description')

    try:
        # Save to database in threadpool to prevent event loop blocking
        issue_id = await asyncio.to_thread(save_issue_to_db, issue_description, selected_category, photo_path)

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
    """Cancel issue reporting and end conversation."""
    await update.message.reply_text(
        "Issue reporting cancelled.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def run_bot():
    """Initialize and start Telegram bot. Returns app instance or None if token missing."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Warning: TELEGRAM_BOT_TOKEN environment variable not set. Bot will not start.")
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

        print("Bot is starting...")
        # Initialize and start the application
        await application.initialize()
        await application.start()
        await application.updater.start_polling()

        print("Bot started successfully and is polling for updates.")
        
        # Return application so we can stop it later
        return application
    except Exception as e:
        print(f"Error initializing bot: {e}")
        logging.error(f"Bot initialization failed: {e}")
        return None

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_bot())
    loop.run_forever()
