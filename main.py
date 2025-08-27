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
        [InlineKeyboardButton("مودات 🕹️", callback_data="choose_mode")],
        [InlineKeyboardButton("Help ℹ️", callback_data="help")],
        [InlineKeyboardButton("Alerts 🚨", callback_data="alerts")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("أهلاً بك في FPL Bot 🐉\nاختر الخيار المناسب:", reply_markup=reply_markup)

# ----------------------------
async def handle_entry_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("⚠️ ادخل رقم صحيح للـ entry ID.")
        return
    entry_id = int(text)

    # جلب معلومات الـ entry للتحقق
    info = await get_entry_info(entry_id)
    if "error" in info:
        await update.message.reply_text(f"❌ الـ entry ID غير صحيح أو لا يمكن جلب البيانات: {info['error']}")
        return

    # حفظ الـ entry ID في السيشن
    session["entry_id"] = entry_id
    player_name = info.get("player_first_name", "") + " " + info.get("player_last_name", "")
    await update.message.reply_text(f"✅ تم التحقق من الـ entry ID.\nالاسم: {player_name}")

    # جلب الدوريات
    leagues = await get_user_leagues(entry_id)
    if isinstance(leagues, dict) and "error" in leagues:
        await update.message.reply_text(f"❌ حدث خطأ في جلب الدوريات: {leagues['error']}")
        return

    if len(leagues) > 1:
        keyboard = [[InlineKeyboardButton(l["name"], callback_data=f"league_{l['id']}")] for l in leagues]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("اختر الدوري:", reply_markup=reply_markup)
    elif len(leagues) == 1:
        session["league_id"] = leagues[0]["id"]
        await update.message.reply_text("تم تحديد الدوري تلقائيًا، يمكنك الآن استخدام المود المختار.")
    else:
        await update.message.reply_text("لا يوجد دوري لهذا الفريق.")

# ----------------------------
async def select_hacker_gw(update: Update):
    bootstrap = get_bootstrap_sync()
    current_gw = get_current_gw(bootstrap)
    session["target_gw"] = current_gw + 1  # الجولة الجاية افتراضي
    await update.callback_query.edit_message_text(
        f"🕵️ Hacker Mode: سيتم تحليل الجولة {session['target_gw']}.\nيمكنك تغيير الجولة بإرسال رقم جديد."
    )

# ----------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "choose_mode":
        keyboard = [
            [InlineKeyboardButton("Normal Mode 🟢", callback_data="normal")],
            [InlineKeyboardButton("Auto Review 🔵", callback_data="autoreview")],
            [InlineKeyboardButton("Hacker Mode 😎", callback_data="hacker")],
            [InlineKeyboardButton("Luxury Features ✨", callback_data="luxury")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("اختار المود:", reply_markup=reply_markup)

    elif data in ["normal", "autoreview", "luxury"]:
        session["selected_mode"] = data
        await query.edit_message_text(f"تم اختيار المود: {data}\nمن فضلك ادخل رقم الـ entry ID الخاص بك:")

    elif data == "hacker":
        session["selected_mode"] = "hacker"
        if not session.get("entry_id"):
            await query.edit_message_text("من فضلك ادخل الـ entry ID أولاً.")
            return
        leagues = await get_user_leagues(session["entry_id"])
        if len(leagues) > 1:
            keyboard = [[InlineKeyboardButton(l["name"], callback_data=f"league_{l['id']}")] for l in leagues]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("اختر الدوري لتحليل Hacker Mode:", reply_markup=reply_markup)
        elif len(leagues) == 1:
            session["league_id"] = leagues[0]["id"]
            await select_hacker_gw(update)
    
    elif data.startswith("league_"):
        league_id = int(data.split("_")[1])
        session["league_id"] = league_id
        if session["selected_mode"] == "hacker":
            await select_hacker_gw(update)
        else:
            await query.edit_message_text("✅ تم اختيار الدوري.")

    elif data == "help":
        help_text = (
            "/start → بداية البوت\n"
            "مودات → اختيار المود (Normal, Auto Review, Hacker, Luxury)\n"
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

# ----------------------------
async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not session.get("entry_id"):
        await handle_entry_id(update, context)
    elif session.get("selected_mode") == "hacker":
        # السماح للمستخدم بتغيير الجولة قبل التحليل
        if text.isdigit():
            session["target_gw"] = int(text)
            data = await hacker_analysis(session["entry_id"], session["league_id"], None, session["target_gw"])
            await update.message.reply_text(f"🕵️ Hacker Mode Analysis GW{session['target_gw']}:\n{data}")
        else:
            await update.message.reply_text("⚠️ ادخل رقم صحيح للجولة أو انتظر الافتراضي.")
    else:
        await update.message.reply_text("اختر مود أولاً من /start ثم اضغط على المود المطلوب.")

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