import os
import zipfile
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)

# Temporary folder to store files
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

# Dict to store user files
user_files = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me files. Type /zip to get them as a zip file.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    document = update.message.document

    if not document:
        await update.message.reply_text("Send only document files.")
        return

    file = await context.bot.get_file(document.file_id)
    filename = f"{user_id}_{document.file_name}"
    filepath = os.path.join(TEMP_DIR, filename)
    await file.download_to_drive(filepath)

    user_files.setdefault(user_id, []).append(filepath)
    await update.message.reply_text(f"Saved file: {document.file_name}")

async def zip_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    files = user_files.get(user_id, [])

    if not files:
        await update.message.reply_text("No files found. Send me some first.")
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

    await update.message.reply_text("Here is your zipped file!")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    for f in user_files.get(user_id, []):
        if os.path.exists(f):
            os.remove(f)
    user_files[user_id] = []
    await update.message.reply_text("Cleared your uploaded files.")

def main():
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN_HERE").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("zip", zip_files))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
