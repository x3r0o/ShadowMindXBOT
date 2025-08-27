import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from fantasy import get_user_leagues, get_entry_info, get_current_gw, get_bootstrap_sync
from planner import plan_rounds, review_team, hacker_analysis, captaincy_advisor
from alerts import send_alerts, captain_alert
from utils import format_team, format_alerts, format_captain, format_plan, top_differentials

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("FPLBot")

# ----------------------------
session = {
    "entry_id": None,
    "league_id": None,
    "selected_mode": None,
    "target_gw": None,
    "num_rounds": 1,
    "num_rounds_set": False,
    "balance_mode": False
}

# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Auto Review 🔵", callback_data="autoreview")],
        [InlineKeyboardButton("Luxury Features ✨", callback_data="luxury")],
        [InlineKeyboardButton("مودات 🕹️", callback_data="choose_mode")],
        [InlineKeyboardButton("Help ℹ️", callback_data="help")],
        [InlineKeyboardButton("Alerts 🚨", callback_data="alerts")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "أهلاً بك في FPL Bot 🐉\nاختر الخيار المناسب أو أدخل الـ entry ID:", 
        reply_markup=reply_markup
    )

# ----------------------------
async def handle_entry_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("⚠️ ادخل رقم صحيح للـ entry ID.")
        return
    entry_id = int(text)

    info = await get_entry_info(entry_id)
    if "error" in info:
        await update.message.reply_text(f"❌ الـ entry ID غير صحيح أو لا يمكن جلب البيانات: {info['error']}")
        return

    session["entry_id"] = entry_id
    player_name = info.get("player_first_name", "") + " " + info.get("player_last_name", "")
    await update.message.reply_text(f"✅ تم التحقق من الـ entry ID.\nالاسم: {player_name}")

# ----------------------------
async def choose_mode_keyboard(query):
    keyboard = [
        [InlineKeyboardButton("Normal Mode 🟢", callback_data="normal")],
        [InlineKeyboardButton("Hacker Mode 😎", callback_data="hacker")],
        [InlineKeyboardButton("رجوع ↩️", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("اختر المود:", reply_markup=reply_markup)

# ----------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "choose_mode":
        await choose_mode_keyboard(query)

    elif data in ["normal", "hacker"]:
        if not session.get("entry_id"):
            await query.edit_message_text("من فضلك ادخل الـ entry ID أولاً.")
            return
        session["selected_mode"] = data
        await query.edit_message_text(f"تم اختيار المود: {data}")

    elif data == "autoreview":
        if not session.get("entry_id"):
            await query.edit_message_text("ادخل الـ entry ID أولاً.")
            return
        team_data = await review_team(session["entry_id"])
        formatted_team = "\n".join(format_team(team_data))
        await query.edit_message_text(f"📝 تقرير الفريق:\n{formatted_team}")

    elif data == "luxury":
        if not session.get("entry_id"):
            await query.edit_message_text("ادخل الـ entry ID أولاً.")
            return
        team_data = await review_team(session["entry_id"])
        captain_advice = await captaincy_advisor(team_data)
        diff_sorted = sorted(top_differentials(team_data))
        await query.edit_message_text(f"{captain_advice}\n✨ Differentials: {', '.join(diff_sorted)}")

    elif data == "help":
        help_text = (
            "/start → بداية البوت\n"
            "مودات → اختيار المود (Normal, Hacker)\n"
            "Auto Review و Luxury → بعد إدخال الـ entry ID\n"
            "Alerts → آخر injuries / risks / captain alerts"
        )
        await query.edit_message_text(help_text)

    elif data == "alerts":
        if not session.get("entry_id"):
            await query.edit_message_text("ادخل الـ entry ID أولاً.")
            return
        alerts_dict = await send_alerts(session["entry_id"])
        alerts_text = format_alerts(alerts_dict)
        captain_warn = await captain_alert(session["entry_id"])
        await query.message.reply_text(f"{alerts_text}\n{captain_warn}")

    elif data == "back":
        await start(query, context)

# ----------------------------
async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not session.get("entry_id"):
        await handle_entry_id(update, context)
    else:
        keyboard = [
            [InlineKeyboardButton("استخدم المحفوظ ✅", callback_data="use_saved")],
            [InlineKeyboardButton("أدخل جديد ✏️", callback_data="enter_new")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("هل تريد استخدام الـ entry ID المحفوظ أم إدخال جديد؟", reply_markup=reply_markup)

# ----------------------------
if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN غير موجود في Environment Variables")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_router))

    app.run_polling()