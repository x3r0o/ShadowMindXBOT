from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os
import asyncio
import storage
import fpl_api
import logic
import alerts
import luxury
import hacker

# ======== TOKEN من Environment Variable ========
TOKEN = os.getenv("BOT_TOKEN")

# ======== START COMMAND ========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entry_id = storage.get_entry_id()
    keyboard = []
    if entry_id:
        keyboard = [
            [InlineKeyboardButton("استخدم Entry ID المحفوظ", callback_data='use_saved_id')],
            [InlineKeyboardButton("أدخل Entry ID جديد", callback_data='enter_new_id')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Entry ID موجود مسبقًا، اختر خيار:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("أدخل Entry ID الخاص بك:")

# ======== MAIN MENU ========
async def show_main_menu(update):
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

    # ======== START OPTIONS ========
    if choice == "use_saved_id":
        await query.edit_message_text("استخدام Entry ID المحفوظ...")
        await show_main_menu(update)
        return

    if choice == "enter_new_id":
        await query.edit_message_text("من فضلك أدخل Entry ID جديد:")
        return

    # ======== VERIFY ENTRY ID ========
    entry_id = storage.get_entry_id()
    if not entry_id:
        await query.edit_message_text("Entry ID غير مسجل. من فضلك أدخل ID صحيح أولاً.")
        return

    # ======== MAIN MENU OPTIONS ========
    if choice == "review":
        await query.edit_message_text("جاري تحليل الفريق...")
        result = logic.review_team(entry_id)
        await query.edit_message_text(result + "\n\nللرجوع للقائمة الرئيسية اضغط /start")

    elif choice == "plan":
        await query.edit_message_text("جاري تجهيز خطة الجولة...")
        # استرجاع الإعدادات إذا موجودة
        settings = storage.get_settings()
        selected_gw = settings.get("selected_gw")
        result = logic.plan_gw(entry_id, selected_gw)
        await query.edit_message_text(result + "\n\nللرجوع للقائمة الرئيسية اضغط /start")

    elif choice == "versus":
        await query.edit_message_text("جاري تجهيز مقارنة مع الخصم...")
        settings = storage.get_settings()
        league_id = settings.get("league_id")
        selected_gw = settings.get("selected_gw")
        result = logic.versus_strategy(entry_id, league_id, selected_gw)
        await query.edit_message_text(result + "\n\nللرجوع للقائمة الرئيسية اضغط /start")

    elif choice == "alerts":
        await query.edit_message_text("جاري جلب الأخبار والإصابات...")
        result = alerts.get_alerts()
        await query.edit_message_text(result + "\n\nللرجوع للقائمة الرئيسية اضغط /start")

    elif choice == "luxury":
        await query.edit_message_text("جاري تجهيز الميزات المتقدمة...")
        current_gw = logic.get_current_gw()
        cap = luxury.captaincy_advisor(entry_id, gw=current_gw)
        diffs = luxury.differentials_radar(entry_id)
        perf = luxury.performance_review(entry_id)
        result = f"{cap}\n\n{diffs}\n\n{perf}\n\nللرجوع للقائمة الرئيسية اضغط /start"
        await query.edit_message_text(result)

    elif choice == "hacker":
        await query.edit_message_text("جاري تجهيز بيانات Hacker Mode...")
        result = hacker.main_hacker(entry_id)
        await query.edit_message_text(result + "\n\nللرجوع للقائمة الرئيسية اضغط /start")

    else:
        await query.edit_message_text("اختيار غير معروف!")

# ======== ENTRY ID TEXT HANDLER ========
async def entry_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.isdigit():
        valid = fpl_api.validate_entry_id(text)
        if valid:
            storage.set_entry_id(text)
            await update.message.reply_text(f"تم تسجيل Entry ID: {text}")
            await show_main_menu(update)
        else:
            await update.message.reply_text("Entry ID غير صحيح، حاول مرة أخرى:")
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