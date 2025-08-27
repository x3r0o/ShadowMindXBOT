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
from fantasy import get_user_leagues, get_entry_info, get_entry_team, get_current_gw, get_bootstrap_sync
from planner import plan_rounds, review_team, hacker_analysis, captaincy_advisor
from alerts import send_alerts, captain_alert
from utils import format_team, format_alerts, format_captain, format_plan, top_differentials

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("FPLBot")

# ----------------------------
session = {
    "entry_id": None,
    "player_name": None,
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
    await update.message.reply_text("أهلاً بك في FPL Bot 🐉\n✏️ ادخل الـ entry ID الخاص بك:")

# ----------------------------
async def handle_entry_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("⚠️ ادخل رقم صحيح للـ entry ID.")
        return
    entry_id = int(text)

    # تحقق من ID
    info = await get_entry_info(entry_id)
    if "error" in info:
        await update.message.reply_text(f"❌ الـ entry ID غير صحيح أو لا يمكن جلب البيانات: {info['error']}")
        return

    session["entry_id"] = entry_id
    session["player_name"] = info.get("player_first_name", "") + " " + info.get("player_last_name", "")
    await update.message.reply_text(f"✅ تم التحقق من الـ entry ID.\nالاسم: {session['player_name']}")

    await show_mode_choices(update)

# ----------------------------
async def show_mode_choices(update: Update):
    keyboard = [
        [InlineKeyboardButton("Normal Mode 🟢", callback_data="normal")],
        [InlineKeyboardButton("Auto Review 🔵", callback_data="autoreview")],
        [InlineKeyboardButton("Hacker Mode 😎", callback_data="hacker")],
        [InlineKeyboardButton("Luxury Features ✨", callback_data="luxury")],
        [InlineKeyboardButton("Alerts 🚨", callback_data="alerts")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.edit_message_text("اختر المود أو الخدمة:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("اختر المود أو الخدمة:", reply_markup=reply_markup)

# ----------------------------
async def get_league_opponents(league_id):
    leagues = await get_user_leagues(session["entry_id"])
    all_entries = []
    for l in leagues:
        if l["id"] == league_id:
            all_entries = l.get("entries", [])
            break
    opponents = [e for e in all_entries if e["entry_id"] != session["entry_id"]]
    return opponents

# ----------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data in ["normal", "autoreview", "luxury"]:
        session["selected_mode"] = data
        await execute_mode(update, context)
        return

    elif data == "hacker":
        session["selected_mode"] = "hacker"
        leagues = await get_user_leagues(session["entry_id"])
        if len(leagues) > 1:
            keyboard = [[InlineKeyboardButton(l["name"], callback_data=f"league_{l['id']}")] for l in leagues]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("اختر الدوري لتحليل Hacker Mode:", reply_markup=reply_markup)
        elif len(leagues) == 1:
            session["league_id"] = leagues[0]["id"]
            await select_hacker_opponent(update)
        return

    elif data.startswith("league_"):
        league_id = int(data.split("_")[1])
        session["league_id"] = league_id
        await select_hacker_opponent(update)
        return

    elif data.startswith("opponent_"):
        opponent_id = int(data.split("_")[1])
        session["opponent_entry_id"] = opponent_id
        await select_hacker_gw(update)
        return

    elif data.startswith("gw_"):
        gw = int(data.split("_")[1])
        session["target_gw"] = gw
        await execute_mode(update, context)
        return

    elif data == "alerts":
        alerts_dict = await send_alerts(session["entry_id"])
        alerts_text = format_alerts(alerts_dict)
        captain_warn = await captain_alert(session["entry_id"])
        await query.edit_message_text(f"{alerts_text}\n{captain_warn}")
        return

    elif data == "back":
        await show_mode_choices(update)
        return

# ----------------------------
async def select_hacker_opponent(update):
    opponents = await get_league_opponents(session["league_id"])
    if not opponents:
        await update.callback_query.edit_message_text("لا يوجد خصوم في الدوري.")
        return
    keyboard = [[InlineKeyboardButton(o["name"], callback_data=f"opponent_{o['entry_id']}")] for o in opponents]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("اختر الخصم لتحليل Hacker Mode:", reply_markup=reply_markup)

# ----------------------------
async def select_hacker_gw(update):
    current_gw = get_current_gw(get_bootstrap_sync())
    keyboard = [[InlineKeyboardButton(f"GW{current_gw + i}", callback_data=f"gw_{current_gw + i}")] for i in range(3)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("اختر الجولة:", reply_markup=reply_markup)

# ----------------------------
async def execute_mode(update, context):
    mode = session.get("selected_mode")
    entry_id = session.get("entry_id")
    league_id = session.get("league_id")
    target_gw = session.get("target_gw") or (get_current_gw(get_bootstrap_sync()) + 1)
    opponent_id = session.get("opponent_entry_id")

    try:
        if mode == "normal":
            plan_dict = await plan_rounds(entry_id, league_id, target_gw, num_rounds=session.get("num_rounds",1))
            plan_text = format_plan(plan_dict)
            await update.callback_query.edit_message_text(f"📋 خطتك للجولات القادمة:\n{plan_text}")

        elif mode == "autoreview":
            team_data = await review_team(entry_id, target_gw)
            formatted_team = "\n".join(format_team(team_data))
            await update.callback_query.edit_message_text(f"📝 تقرير الفريق:\n{formatted_team}")

        elif mode == "luxury":
            team_data = await review_team(entry_id, target_gw)
            captain_advice = await captaincy_advisor(team_data)
            diff_sorted = top_differentials(team_data)
            await update.callback_query.edit_message_text(f"{captain_advice}\n✨ Differentials: {', '.join(diff_sorted)}")

        elif mode == "hacker":
            if not league_id or not opponent_id:
                await update.callback_query.edit_message_text("⚠️ اختر الدوري والخصم أولاً.")
                return
            data = await hacker_analysis(entry_id, league_id, opponent_id, target_gw)
            keyboard = [[InlineKeyboardButton("رجوع ↩️", callback_data="back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(f"🕵️ Hacker Mode Analysis 🕵️\n\n{data}", reply_markup=reply_markup)

    except Exception as e:
        keyboard = [[InlineKeyboardButton("رجوع ↩️", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(f"❌ حدث خطأ: {e}", reply_markup=reply_markup)
        log.error(f"execute_mode failed: {e}")

# ----------------------------
async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not session.get("entry_id"):
        await handle_entry_id(update, context)
    else:
        keyboard = [
            [InlineKeyboardButton("استخدم الـ ID المحفوظ ✅", callback_data="use_saved_id")],
            [InlineKeyboardButton("أدخل ID جديد ✏️", callback_data="new_id")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
       await update.message.reply_text(
            "✏️ تريد استخدام الـ entry ID المحفوظ أم إدخال جديد؟",
            reply_markup=reply_markup
        )

# ----------------------------
async def saved_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "use_saved_id":
        await show_mode_choices(update)
    elif query.data == "new_id":
        session["entry_id"] = None
        session["player_name"] = None
        await query.edit_message_text("✏️ من فضلك ادخل الـ entry ID الجديد:")

# ----------------------------
if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN غير موجود في Environment Variables")

    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(saved_id_handler, pattern="^(use_saved_id|new_id)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_router))

    app.run_polling()