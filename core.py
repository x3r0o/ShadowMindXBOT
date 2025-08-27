from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os
import storage
import logic
import alerts
import luxury
import hacker
import screenshot_handler  # ملف التعامل مع السكرين شوت

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

# ======== BUTTON HANDLER ========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    entry_id = storage.get_entry_id()

    # START OPTIONS
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

    if not entry_id:
        await query.edit_message_text("Entry ID غير مسجل. من فضلك أدخل ID أولاً.")
        return

    # ======== REVIEW / PLAN / LUXURY ========
    if choice in ["review", "plan", "luxury"]:
        existing = screenshot_handler.check_screenshot(entry_id, choice)
        keyboard = []
        if existing:
            keyboard = [
                [InlineKeyboardButton("استخدم السكرين القديم", callback_data=f"use_old_{choice}")],
                [InlineKeyboardButton("ارفع سكرين جديد", callback_data=f"upload_new_{choice}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"تم العثور على سكرين شوت سابق لأمر {choice}. اختر خيار:", reply_markup=reply_markup)
        else:
            await query.edit_message_text(f"من فضلك ارفع سكرين شوت لأمر {choice}:")
        context.user_data["current_command"] = choice

    # ======== VERSUS ========
    elif choice == "versus":
        own_existing = screenshot_handler.check_screenshot(entry_id, "versus_own")
        opp_existing = screenshot_handler.check_screenshot(entry_id, "versus_opponent")
        keyboard = []
        if own_existing and opp_existing:
            keyboard = [
                [InlineKeyboardButton("استخدم السكرينز القديمة", callback_data="use_old_versus")],
                [InlineKeyboardButton("ارفع سكرينز جديدة", callback_data="upload_new_versus")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("تم العثور على سكرينز قديمة للـ Versus. اختر خيار:", reply_markup=reply_markup)
        else:
            await query.edit_message_text("من فضلك ارفع سكرين شوت لك وللمنافس للـ Versus:")
        context.user_data["current_command"] = "versus"

    # ======== HACKER MODE ========
    elif choice == "hacker":
        result = hacker.main_hacker(entry_id)
        keyboard = [[InlineKeyboardButton("الرجوع للقائمة الرئيسية", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(result, reply_markup=reply_markup)

    # ======== التعامل مع السكرين القديم أو الجديد ========
    elif choice.startswith("use_old_") or choice.startswith("upload_new_"):
        cmd = choice.split("_")[-1]
        if "use_old" in choice:
            if cmd == "versus":
                own_players = screenshot_handler.extract_players(entry_id, "versus_own")
                opp_players = screenshot_handler.extract_players(entry_id, "versus_opponent")
                players = {"own": own_players, "opponent": opp_players}
            else:
                players = screenshot_handler.extract_players(entry_id, cmd)
        else:
            await query.edit_message_text(f"من فضلك ارفع السكرين شوت الجديد لأمر {cmd}:")
            return

        result = logic.run_command_with_players(cmd, entry_id, players)
        keyboard = [[InlineKeyboardButton("الرجوع للقائمة الرئيسية", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(result, reply_markup=reply_markup)

# ======== ENTRY ID HANDLER ========
async def entry_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.isdigit():
        storage.set_entry_id(text)
        await update.message.reply_text("تم حفظ Entry ID، جاري الانتقال للقائمة الرئيسية...")
        await show_main_menu(update)
    else:
        await update.message.reply_text("Entry ID غير صحيح، حاول مرة أخرى:")

# ======== SCREENSHOT HANDLER ========
async def screenshot_handler_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    cmd = context.user_data.get("current_command")
    file_path = screenshot_handler.save_screenshot(file, storage.get_entry_id(), cmd)
    await update.message.reply_text("تم حفظ السكرين شوت بنجاح، جاري استخراج اللاعبين...")

    if cmd == "versus":
        players_own, players_opp = screenshot_handler.extract_players_from_file_versus(file_path)
        context.user_data["last_players"] = {"own": players_own, "opponent": players_opp}
        await update.message.reply_text(f"تم استخراج {len(players_own)} لاعب لك و {len(players_opp)} لاعب للمنافس.")
    else:
        players = screenshot_handler.extract_players_from_file(file_path)
        context.user_data["last_players"] = players
        await update.message.reply_text(f"تم استخراج {len(players)} لاعب من السكرين.")

# ======== MAIN FUNCTION ========
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, entry_id_handler))
    app.add_handler(MessageHandler(filters.PHOTO, screenshot_handler_func))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()