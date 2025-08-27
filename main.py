import asyncio
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from fantasy import get_user_leagues, get_entry_team, get_h2h_matches, get_current_gw, get_bootstrap_sync
from planner import (
    plan_rounds,
    review_team,
    generate_versus_plan,
    generate_versus_report,
    hacker_analysis,
    captaincy_advisor,
    differentials_radar
)
from alerts import send_alerts, captain_alert
from utils import format_team, format_alerts, top_differentials, format_plan

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
    "timeline": False,
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
async def get_h2h_opponent(league_id: int, gw: int, entry_id: int):
    try:
        matches_data = await get_h2h_matches(league_id)
        matches = matches_data.get("matches", [])
        for m in matches:
            if m["event"] == gw:
                if m["entry_1"] == entry_id:
                    return {"id": m["entry_2"], "name": m.get("entry_2_name")}
                elif m["entry_2"] == entry_id:
                    return {"id": m["entry_1"], "name": m.get("entry_1_name")}
        return {"id": None, "name": None}
    except Exception as e:
        log.error(f"get_h2h_opponent failed: {e}")
        return {"id": None, "name": None}

# ----------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "choose_mode":
        keyboard = [
            [InlineKeyboardButton("Normal Mode 🟢", callback_data="normal")],
            [InlineKeyboardButton("Versus Mode 🔴", callback_data="versus")],
            [InlineKeyboardButton("Auto Review 🔵", callback_data="autoreview")],
            [InlineKeyboardButton("Hacker Mode 😎", callback_data="hacker")],
            [InlineKeyboardButton("Luxury Features ✨", callback_data="luxury")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("اختار المود:", reply_markup=reply_markup)

    elif query.data in ["normal", "versus", "autoreview", "luxury"]:
        session["selected_mode"] = query.data
        await query.edit_message_text(f"تم اختيار المود: {query.data}\nمن فضلك ادخل رقم الـ entry ID الخاص بك:")

    elif query.data == "hacker":
        session["selected_mode"] = "hacker"
        if not session.get("entry_id"):
            await query.edit_message_text("من فضلك ادخل الـ entry ID أولاً.")
            return
        try:
            leagues = await get_user_leagues(session["entry_id"])
        except Exception as e:
            await query.edit_message_text(f"❌ حدث خطأ في جلب الدوريات: {e}")
            return
        if len(leagues) > 1:
            keyboard = [[InlineKeyboardButton(l["name"], callback_data=f"league_{l['id']}")] for l in leagues]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("اختر الدوري لتحليل Hacker Mode:", reply_markup=reply_markup)
        elif len(leagues) == 1:
            session["league_id"] = leagues[0]["id"]
            await ask_hacker_gw(update)

    elif query.data == "help":
        help_text = (
            "/start → بداية البوت\n"
            "مودات → اختيار المود (Normal, Versus, Auto Review, Hacker, Luxury)\n"
            "Alerts → آخر injuries / risks / captain alerts\n"
            "بعد اختيار المود → أزرار إضافية حسب المود"
        )
        await query.edit_message_text(help_text)

    elif query.data == "alerts":
        if session["entry_id"]:
            try:
                alerts_dict = await send_alerts(session["entry_id"])
                alerts_text = format_alerts(alerts_dict)
                captain_warn = await captain_alert(session["entry_id"])
                await update.message.reply_text(f"{alerts_text}\n{captain_warn}")
            except Exception as e:
                await update.message.reply_text(f"❌ حدث خطأ أثناء جلب التنبيهات: {e}")
        else:
            await update.message.reply_text("ادخل الـ entry ID أولاً.")

    elif query.data == "hacker_refresh":
        if session["selected_mode"] == "hacker":
            await execute_mode(update, context)

# ----------------------------
async def ask_hacker_gw(update):
    try:
        bootstrap = get_bootstrap_sync()
        current_gw = get_current_gw(bootstrap)
        session["target_gw"] = current_gw + 1
        opponent_info = await get_h2h_opponent(session["league_id"], session["target_gw"], session["entry_id"])
        session["opponent_entry_id"] = opponent_info.get("id")
        await update.callback_query.edit_message_text(
            f"🕵️ سيتم تحليل Hacker Mode للجولة {session['target_gw']} في الدوري المختار."
        )
    except Exception as e:
        log.error(f"ask_hacker_gw failed: {e}")
        await update.callback_query.edit_message_text(f"❌ حدث خطأ أثناء تحديد الجولة: {e}")

# ----------------------------
async def handle_entry_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not session.get("selected_mode") or session.get("entry_id"):
        return
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("⚠️ ادخل رقم صحيح للـ entry ID.")
        return
    session["entry_id"] = int(text)
    try:
        leagues = await get_user_leagues(session["entry_id"])
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ في جلب الدوريات: {e}")
        return
    if len(leagues) > 1:
        keyboard = [[InlineKeyboardButton(l["name"], callback_data=f"league_{l['id']}")] for l in leagues]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("اختار الدوري:", reply_markup=reply_markup)
    elif len(leagues) == 1:
        session["league_id"] = leagues[0]["id"]
        await update.message.reply_text("تم تحديد الدوري تلقائيًا، يمكنك الآن استخدام المود المختار.")
    else:
        await update.message.reply_text("لا يوجد دوري لهذا الفريق.")
    if session["selected_mode"] == "normal":
        await update.message.reply_text("كم عدد الجولات التي تريد التخطيط لها؟")

# ----------------------------
async def handle_num_rounds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if session.get("selected_mode") == "normal" and not session.get("num_rounds_set"):
        text = update.message.text.strip()
        if text.isdigit() and int(text) > 0:
            session["num_rounds"] = int(text)
            session["num_rounds_set"] = True
            await update.message.reply_text(f"✅ تم ضبط عدد الجولات على {session['num_rounds']}.")
        else:
            await update.message.reply_text("⚠️ ادخل رقم صحيح للجولات.")

# ----------------------------
async def league_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("league_"):
        league_id = int(query.data.split("_")[1])
        session["league_id"] = league_id
        if session["selected_mode"] == "hacker":
            await ask_hacker_gw(update)
        else:
            await query.edit_message_text("✅ تم اختيار الدوري، يمكنك الآن استخدام المود المختار.")

# ----------------------------
async def execute_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not session.get("selected_mode") or not session.get("entry_id"):
        await update.message.reply_text("⚠️ ادخل entry ID واختر مود أولاً.")
        return

    mode = session["selected_mode"]
    entry_id = session["entry_id"]
    league_id = session.get("league_id")
    opponent_id = session.get("opponent_entry_id")
    target_gw = session.get("target_gw") or (get_current_gw(get_bootstrap_sync()) + 1)

    try:
        if mode == "normal":
            plan_dict = await plan_rounds(entry_id, league_id, target_gw, num_rounds=session["num_rounds"], balance_mode=session["balance_mode"])
            plan_text = format_plan(plan_dict)
            await update.message.reply_text(f"📋 خطتك للجولات القادمة:\n{plan_text}")

        elif mode == "autoreview":
            team_data = await review_team(entry_id, target_gw)
            formatted_team = "\n".join(format_team(team_data))
            await update.message.reply_text(f"📝 تقرير الفريق:\n{formatted_team}")

        elif mode == "versus":
            if not opponent_id:
                await update.message.reply_text("⚠️ ادخل opponent entry ID لاستخدام Versus Mode.")
                return
            plan_dict = await generate_versus_plan(entry_id, opponent_id, target_gw)
            report_dict = await generate_versus_report(entry_id, opponent_id, target_gw)
            plan_text = format_plan(plan_dict)
            report_text = f"⚔️ نقاطك: {report_dict.get('your_score', 0)}\n👤 نقاط الخصم: {report_dict.get('opponent_score', 0)}"
            await update.message.reply_text(f"{report_text}\n📋 خطة ضد الخصم:\n{plan_text}")

        elif mode == "hacker":
            if not league_id or not opponent_id:
                await update.message.reply_text("⚠️ اختر الدوري والجولة أولاً.")
                return
            data = await hacker_analysis(entry_id, league_id, opponent_id, target_gw)
            keyboard = [
                [InlineKeyboardButton("Refresh 🔄", callback_data="hacker_refresh")],
                [InlineKeyboardButton("رجوع للمودات ↩️", callback_data="choose_mode")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(f"🕵️ Hacker Mode Analysis 🕵️\n\n{data}", reply_markup=reply_markup)

        elif mode == "luxury":
            team_data = await review_team(entry_id, target_gw)
            captain_advice = await captaincy_advisor(team_data)
            diff_sorted = sorted(top_differentials(team_data))  # يمكن تعديل حسب الأفضلية
            plan_dict = await plan_rounds(entry_id, league_id, target_gw, num_rounds=session.get("num_rounds",1), balance_mode=session["balance_mode"])
            plan_text = format_plan(plan_dict)
            await update.message.reply_text(f"{captain_advice}\n✨ Differentials: {', '.join(diff_sorted)}\n📋 خطتك:\n{plan_text}")

    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء تنفيذ المود: {e}")
        log.error(f"execute_mode failed: {e}")

# ----------------------------
async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not session.get("entry_id"):
        await handle_entry_id(update, context)
    elif session.get("selected_mode") == "normal" and not session.get("num_rounds_set"):
        await handle_num_rounds(update, context)
    else:
        await execute_mode(update, context)

# ----------------------------
if __name__ == "__main__":
   
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN غير موجود في Environment Variables")

    from telegram.ext import ApplicationBuilder

    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(league_handler, pattern=r"^league_\d+$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_router))

    # الطريقة الصحيحة لتشغيل البوت بدون asyncio.run()
    app.run_polling()