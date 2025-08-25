from telegram.ext import Application, CommandHandler
import os

# هنقرأ التوكن من متغير البيئة (هندخله في Render بعدين)
TOKEN = os.getenv("7685806243:AAFuZgaz4XGH_JUGtflpQ_ZsXO06n9ytPdA")

async def start(update, context):
    await update.message.reply_text("👋 الواد اشتغل وبقى معاك يا كبير 🔥")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()