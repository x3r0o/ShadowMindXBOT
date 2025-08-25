from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os

# هنا هياخد التوكن من الـ Environment Variables
TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلا! أنا ابنك جاهز معاك.")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ أنا صاحي وجاهز يا صحبي!")

def main():
    app = Application.builder().token(TOKEN).build()

    # أوامر البوت
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))

    # تشغيل البوت
    app.run_polling()

if __name__ == "__main__":
    main()