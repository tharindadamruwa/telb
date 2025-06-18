import os
import zipfile
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from uuid import uuid4

BOT_TOKEN = "7896182510:AAHprQJ36Yuc0gqYUJeiwfT_DIZ8QqK-FRo"
TEMP_DIR = "temp"

# Create temp folder if not exist
os.makedirs(TEMP_DIR, exist_ok=True)

file_cache = {}  # chat_id: [file_info_list]

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in file_cache:
        file_cache[chat_id] = []

    file_id = update.message.document.file_id
    file_name = update.message.document.file_name
    message_id = update.message.message_id

    file_cache[chat_id].append({
        "file_id": file_id,
        "file_name": file_name,
        "message_id": message_id
    })

async def handle_zip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to one of the files you sent earlier.")
        return

    zip_name = "files.zip"
    if context.args:
        zip_name = f"{context.args[0]}.zip"

    # Filter messages up to the replied message
    reply_to_msg_id = update.message.reply_to_message.message_id
    files_to_zip = [f for f in file_cache.get(chat_id, []) if f["message_id"] <= reply_to_msg_id]

    if not files_to_zip:
        await update.message.reply_text("Couldn't find files to zip.")
        return

    zip_path = os.path.join(TEMP_DIR, f"{uuid4().hex}.zip")

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for f in files_to_zip:
            telegram_file = await context.bot.get_file(f["file_id"])
            file_path = os.path.join(TEMP_DIR, f["file_name"])
            await telegram_file.download_to_drive(file_path)
            zipf.write(file_path, f["file_name"])
            os.remove(file_path)

    with open(zip_path, "rb") as zf:
        await update.message.reply_document(document=zf, filename=zip_name)

    os.remove(zip_path)
    file_cache[chat_id] = []  # Clear cache after zipping

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me multiple files, then reply to one with 'zip [optional_name]' to zip them.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^zip(\s+\w+)?'), handle_zip_command))
    app.run_polling()

if __name__ == "__main__":
    main()
