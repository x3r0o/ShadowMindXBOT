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
    "opponent_entry_id": None,
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
    # إذا في ID موجود نقترح استخدامه أو إدخال جديد
    if session.get("entry_id"):
        keyboard = [
            [InlineKeyboardButton("استخدم الـ Entry ID المحفوظ", callback_data="use_saved_id")],
            [InlineKeyboardButton("أدخل Entry ID جديد", callback_data="enter_new_id")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("هل تريد استخدام الـ Entry ID المحفوظ أم إدخال واحد جديد؟", reply_markup=reply_markup)
        return

    await set_entry_id(update)

async def set_entry_id(update):
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
async def select_hacker_gw(update: Update):
    current_gw = get_current_gw(get_bootstrap_sync())
    keyboard = [
        [InlineKeyboardButton(f"GW{current_gw}", callback_data=f"hacker_gw_{current_gw}")],
        [InlineKeyboardButton(f"GW{current_gw + 1}", callback_data=f"hacker_gw_{current_gw + 1}")],
        [InlineKeyboardButton(f"GW{current_gw + 2}", callback_data=f"hacker_gw_{current_gw + 2}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("اختر الجولة للتحليل:", reply_markup=reply_markup)

# ----------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # اختيار مودات
    if data == "choose_mode":
        keyboard = [
            [InlineKeyboardButton("Normal Mode 🟢", callback_data="normal")],
            [InlineKeyboardButton("Auto Review 🔵", callback_data="autoreview")],
            [InlineKeyboardButton("Hacker Mode 😎", callback_data="hacker")],
            [InlineKeyboardButton("Luxury Features ✨", callback_data="luxury")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("اختار المود:", reply_markup=reply_markup)

    # مودات تستخدم الـ Entry ID
    elif data in ["normal", "autoreview", "luxury"]:
        session["selected_mode"] = data
        if session.get("entry_id"):
            await query.edit_message_text(f"✅ ستعمل المود {data} بالـ Entry ID المحفوظ: {session['entry_id']}")
        else:
            await query.edit_message_text(f"تم اختيار المود: {data}\nمن فضلك ادخل رقم الـ entry ID الخاص بك:")

    # Hacker Mode
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

    # اختيار الجولة في Hacker Mode
    elif data.startswith("hacker_gw_"):
        gw = int(data.split("_")[2])
        session["target_gw"] = gw
        await execute_mode(update, context)

    # اختيار الدوري
    elif data.startswith("league_"):
        league_id = int(data.split("_")[1])
        session["league_id"] = league_id
        if session["selected_mode"] == "hacker":
            await select_hacker_gw(update)
        else:
            await query.edit_message_text("✅ تم اختيار الدوري، يمكنك الآن استخدام المود المختار.")

    # استخدام ID المحفوظ أو إدخال جديد
    elif data == "use_saved_id":
        await query.edit_message_text(f"✅ سيتم استخدام Entry ID المحفوظ: {session['entry_id']}")
    elif data == "enter_new_id":
        session["entry_id"] = None
        await query.edit_message_text("من فضلك ادخل الـ Entry ID الجديد:")

    # Help
    elif data == "help":
        help_text = (
            "/start → بداية البوت\n"
            "مودات → اختيار المود (Normal, Auto Review, Hacker, Luxury)\n"
            "Alerts → آخر injuries / risks / captain alerts"
        )
        await query.edit_message_text(help_text)

    # Alerts
    elif data == "alerts":
        if not session.get("entry_id"):
            await query.edit_message_text("ادخل الـ entry ID أولاً.")
            return
        alerts_dict = await send_alerts(session["entry_id"])
        alerts_text = format_alerts(alerts_dict)
        captain_warn = await captain_alert(session["entry_id"])
        await query.message.reply_text(f"{alerts_text}\n{captain_warn}")

# ----------------------------
async def execute_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not session.get("selected_mode") or not session.get("entry_id"):
        await update.message.reply_text("⚠️ اختر مود وأدخل Entry ID أولاً.")
        return
    mode = session["selected_mode"]
    entry_id = session["entry_id"]
    target_gw = session.get("target_gw") or (get_current_gw(get_bootstrap_sync()) + 1)

    if mode == "normal":
        plan_dict = await plan_rounds(entry_id, session.get("league_id"), target_gw, num_rounds=session["num_rounds"], balance_mode=session["balance_mode"])
        plan_text = format_plan(plan_dict)
        await update.callback_query.edit_message_text(f"📋 خطتك للجولات القادمة:\n{plan_text}")

    elif mode == "autoreview":
        team_data = await review_team(entry_id, target_gw)
        formatted_team = "\n".join(format_team(team_data))
        await update.callback_query.edit_message_text(f"📝 تقرير الفريق:\n{formatted_team}")

    elif mode == "hacker":
        opponent_id = session.get("opponent_entry_id")
        data = await hacker_analysis(entry_id, session.get("league_id"), opponent_id, target_gw)
        keyboard = [[InlineKeyboardButton("رجوع للمودات ↩️", callback_data="choose_mode")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(f"🕵️ Hacker Mode Analysis 🕵️\n\n{data}", reply_markup=reply_markup)

    elif mode == "luxury":
        team_data = await review_team(entry_id, target_gw)
        captain_advice = await captaincy_advisor(team_data)
        diff_sorted = sorted(top_differentials(team_data))
        await update.callback_query.edit_message_text(f"{captain_advice}\n✨ Differentials: {', '.join(diff_sorted)}")

# ----------------------------
async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_entry_id(update, context)

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