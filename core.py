from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import storage
import fpl_api
import logic
import alerts
import luxury
import hacker
import os
import asyncio

# ======== TOKEN من Environment Variable ========
TOKEN = os.getenv("TOKEN_BOT")

# ======== START COMMAND ========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entry_id = storage.get_entry_id()
    if not entry_id:
        await update.message.reply_text("أهلاً! من فضلك ادخل Entry ID الخاص بك:")
        return
    await show_main_menu(update)

# ======== MAIN MENU ========
async def show_main_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("/review", callback_data='review')],
        [InlineKeyboardButton("/plan", callback_data='plan')],
        [InlineKeyboardButton("/versus", callback_data='versus')],
        [InlineKeyboardButton("/alerts", callback_data='alerts')],
        [InlineKeyboardButton("/luxury", callback_data='luxury')],
        [InlineKeyboardButton("/hacker", callback_data='hacker')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("اختر أمر من القائمة الرئيسية:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("اختر أمر من القائمة الرئيسية:", reply_markup=reply_markup)

# ======== HANDLE BUTTON CLICKS ========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    entry_id = storage.get_entry_id()
    
    if not entry_id:
        await query.edit_message_text("Entry ID غير مسجل. من فضلك أعد تشغيل البوت واكتب Entry ID.")
        return

    # ======== التعامل مع كل أمر حسب الـ Flow ========
    if choice == "review":
        await query.edit_message_text("جاري تحليل الفريق...")
        result = logic.review_team(entry_id)
        await query.edit_message_text(result)

    elif choice == "plan":
        await query.edit_message_text("جاري تجهيز خطة الجولة...")
        # مثال: جولة واحدة، GW 1
        result = logic.plan_gw(entry_id, start_gw=1)
        await query.edit_message_text(result)

    elif choice == "versus":
        await query.edit_message_text("جاري تجهيز مقارنة مع الخصم...")
        # مثال: خصم Entry ID 999999، GW 1
        opponent_entry_id = 999999
        result = logic.versus_strategy(entry_id, opponent_entry_id, gw=1)
        await query.edit_message_text(result)

    elif choice == "alerts":
        await query.edit_message_text("جاري جلب الأخبار والإصابات...")
        result = alerts.get_alerts()
        await query.edit_message_text(result)

    elif choice == "luxury":
        await query.edit_message_text("جاري تجهيز الميزات المتقدمة...")
        # مثال: عرض Captaincy Advisor GW 1
        cap = luxury.captaincy_advisor(entry_id, gw=1)
        diffs = luxury.differentials_radar(entry_id)
        perf = luxury.performance_review(entry_id)
        result = f"{cap}\n\n{diffs}\n\n{perf}"
        await query.edit_message_text(result)

    elif choice == "hacker":
        await query.edit_message_text("جاري تجهيز بيانات Hacker Mode...")
        # مثال: League ID 12345
        league_id = 12345
        track = hacker.track_opponents(league_id)
        file_msg = hacker.generate_files(league_id)
        result = f"{track}\n\n{file_msg}"
        await query.edit_message_text(result)

    else:
        await query.edit_message_text("اختيار غير معروف!")

# ======== ENTRY ID TEXT HANDLER ========
async def entry_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.isdigit():
        # تحقق مستقبلي ممكن نضيف call للـ FPL API
        storage.set_entry_id(text)
        await update.message.reply_text(f"تم تسجيل Entry ID: {text}")
        await show_main_menu(update)
    else:
        await update.message.reply_text("Entry ID غير صحيح، حاول مرة أخرى:")

# ======== MAIN FUNCTION ========
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, entry_id_handler))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()