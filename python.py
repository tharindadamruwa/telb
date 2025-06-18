import os
import zipfile
import threading
import time
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
from dotenv import load_dotenv

# Keep-alive thread for Replit
def keep_alive():
    while True:
        time.sleep(600)

threading.Thread(target=keep_alive).start()

# Load token from .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Temp folder
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

# Store files per user
user_files = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me files. Use /zip to get them zipped!")

# Handle documents
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    document = update.message.document
    if not document:
        await update.message.reply_text("Only document files are supported.")
        return

    file = await context.bot.get_file(document.file_id)
    filename = f"{user_id}_{document.file_name}"
    filepath = os.path.join(TEMP_DIR, filename)
    await file.download_to_drive(filepath)

    user_files.setdefault(user_id, []).append(filepath)
    await update.message.reply_text(f"Saved: {document.file_name}")

# /zip command
async def zip_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    files = user_files.get(user_id, [])

    if not files:
        await update.message.reply_text("You haven't sent any files yet.")
        return

    zip_path = os.path.join(TEMP_DIR, f"{user_id}_files.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for f in files:
            zipf.write(f, os.path.basename(f))

    await update.message.reply_document(InputFile(zip_path))

    # Clean up
    for f in files:
        os.remove(f)
    os.remove(zip_path)
    user_files[user_id] = []

    await update.message.reply_text("Here is your ZIP file!")

# /clear command
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    for f in user_files.get(user_id, []):
        if os.path.exists(f):
            os.remove(f)
    user_files[user_id] = []
    await update.message.reply_text("Your files have been cleared.")

# Main bot app
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("zip", zip_files))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
