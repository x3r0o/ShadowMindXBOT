from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os
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

    if choice == "main_menu":
        await show_main_menu(update)
        return

    # ======== VERIFY ENTRY ID ========
    entry_id = storage.get_entry_id()
    if not entry_id:
        await query.edit_message_text("Entry ID غير مسجل. من فضلك أدخل ID صحيح أولاً.")
        return

    # ======== MAIN MENU OPTIONS ========
    if choice == "review":
        await query.edit_message_text("جاري تحليل الفريق، يرجى الانتظار...")
        result = logic.review_team(entry_id)
        keyboard = [[InlineKeyboardButton("الرجوع للقائمة الرئيسية", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(result, reply_markup=reply_markup)

    elif choice == "plan":
        settings = storage.get_settings()
        selected_gw = settings.get("selected_gw")
        if not selected_gw:
            await query.edit_message_text("لم يتم تحديد الجولة، من فضلك اختر الجولة أولاً.")
            return
        await query.edit_message_text("جاري تجهيز خطة الجولة، يرجى الانتظار...")
        result = logic.plan_gw(entry_id, selected_gw)
        keyboard = [[InlineKeyboardButton("الرجوع للقائمة الرئيسية", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(result, reply_markup=reply_markup)

    elif choice == "versus":
        settings = storage.get_settings()
        league_id = settings.get("league_id")
        selected_gw = settings.get("selected_gw")
        if not league_id or not selected_gw:
            await query.edit_message_text("لم يتم تحديد الدوري أو الجولة، من فضلك اخترهما أولاً.")
            return
        await query.edit_message_text("جاري تجهيز مقارنة مع الخصم، يرجى الانتظار...")
        result = logic.versus_strategy(entry_id, league_id, selected_gw)
        keyboard = [[InlineKeyboardButton("الرجوع للقائمة الرئيسية", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(result, reply_markup=reply_markup)

    elif choice == "alerts":
        await query.edit_message_text("جاري جلب الأخبار والإصابات، يرجى الانتظار...")
        result = alerts.get_alerts()
        keyboard = [[InlineKeyboardButton("الرجوع للقائمة الرئيسية", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(result, reply_markup=reply_markup)

    elif choice == "luxury":
        await query.edit_message_text("جاري تجهيز الميزات المتقدمة، يرجى الانتظار...")
        current_gw = logic.get_current_gw()
        cap = luxury.captaincy_advisor(entry_id, gw=current_gw)
        diffs = luxury.differentials_radar(entry_id)
        perf = luxury.performance_review(entry_id)
        result = f"{cap}\n\n{diffs}\n\n{perf}"
        keyboard = [[InlineKeyboardButton("الرجوع للقائمة الرئيسية", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(result, reply_markup=reply_markup)

    elif choice == "hacker":
        await query.edit_message_text("جاري تجهيز بيانات Hacker Mode، يرجى الانتظار...")
        result = hacker.main_hacker(entry_id)
        keyboard = [[InlineKeyboardButton("الرجوع للقائمة الرئيسية", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(result, reply_markup=reply_markup)

    else:
        await query.edit_message_text("اختيار غير معروف!")

# ======== ENTRY ID TEXT HANDLER ========
async def entry_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.isdigit():
        valid = fpl_api.validate_entry_id(text)
        if valid:
            storage.set_entry_id(text)
            await update.message.reply_text(f"Entry ID محفوظ، جاري الانتقال للقائمة الرئيسية...")
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