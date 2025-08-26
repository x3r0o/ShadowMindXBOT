import os
import logging
from typing import Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes, PicklePersistence
)
import fantasy
import planner
import versus
import alerts
import utils

# ===== Logging =====
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
log = logging.getLogger("ShadowMindX")

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ===== Helpers =====
def get_user_entry_id(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> Optional[int]:
    return context.user_data.get("entry_id")

def set_user_entry_id(context: ContextTypes.DEFAULT_TYPE, chat_id: int, entry_id: int):
    context.user_data["entry_id"] = entry_id

def parse_int_safe(x: str) -> Optional[int]:
    try:
        return int(x)
    except:
        return None

# ===== Commands =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلا! أنا ShadowMindX — ابنك الخارق للفانتازي 🐉\n\n"
        "⚡ الأوامر الأساسية:\n"
        "• /set_entry <ENTRY_ID> — اربط فريقك\n"
        "• /plan [START END] — خطة نقاط\n"
        "• /versus <LEAGUE_ID> <END_GW> [START_GW] — تحدي خصمك\n"
        "• /alerts — الإصابات والإيقافات\n"
        "• /help — كل الأوامر\n"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 ShadowMindX — كل الأوامر:\n\n"
        "📌 /set_entry <ENTRY_ID>\n"
        "📌 /plan [START END]\n"
        "📌 /versus <LEAGUE_ID> <END_GW> [START_GW]\n"
        "📌 /alerts\n"
        "📌 /api_status — متابعة حالة الـ API\n"
    )

async def api_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, msg = fantasy.check_api_health()
    await update.message.reply_text("✅ API شغّال" if ok else f"❌ {msg}")

async def set_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("استخدم: /set_entry 1234567")
        return
    eid = parse_int_safe(context.args[0])
    if not eid:
        await update.message.reply_text("⚠️ لازم تدخل ENTRY_ID رقم صحيح.")
        return
    set_user_entry_id(context, update.effective_chat.id, eid)
    await update.message.reply_text(f"✅ تم حفظ Entry ID: {eid}")

# ===== Planner =====
async def plan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    entry_id = get_user_entry_id(context, chat_id)
    if not entry_id:
        await update.message.reply_text("الأول اربط فريقك: /set_entry <ENTRY_ID>")
        return

    bootstrap = await fantasy.get_bootstrap_async()
    if isinstance(bootstrap, dict) and bootstrap.get("error"):
        await alerts.offer_api_wait(update, context, reason="bootstrap")
        return

    current_gw = fantasy.get_current_gw(bootstrap)

    if len(context.args) == 2:
        start_gw = parse_int_safe(context.args[0]) or current_gw
        end_gw   = parse_int_safe(context.args[1]) or start_gw
    elif len(context.args) == 0:
        start_gw = end_gw = current_gw
    else:
        await update.message.reply_text("❌ استخدام صحيح: /plan [START END]")
        return

    text = await planner.build_plan_text(entry_id, start_gw, end_gw)
    await update.message.reply_text(text[:4096])

# ===== Versus Mode =====
async def versus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    entry_id = get_user_entry_id(context, chat_id)
    if not entry_id:
        await update.message.reply_text("الأول اربط فريقك: /set_entry <ENTRY_ID>")
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ استخدام صحيح: /versus <LEAGUE_ID> <END_GW> [START_GW]")
        return

    league_id = parse_int_safe(context.args[0])
    end_gw = parse_int_safe(context.args[1])
    if not league_id or not end_gw:
        await update.message.reply_text("⚠️ LEAGUE_ID و END_GW لازم يكونوا أرقام.")
        return

    bootstrap = await fantasy.get_bootstrap_async()
    if isinstance(bootstrap, dict) and bootstrap.get("error"):
        await alerts.offer_api_wait(update, context, reason="bootstrap")
        return
    current_gw = fantasy.get_current_gw(bootstrap)
    start_gw = parse_int_safe(context.args[2]) if len(context.args) >= 3 else current_gw

    cb_base = f"vs|{league_id}|{start_gw}|{end_gw}"
    keyboard = [
        [
            InlineKeyboardButton("📝 تقرير", callback_data=cb_base + "|report"),
            InlineKeyboardButton("🎯 خطة", callback_data=cb_base + "|plan"),
        ],
        [InlineKeyboardButton("📝+🎯 الاتنين", callback_data=cb_base + "|both")]
    ]
    await update.message.reply_text(
        f"⚔️ Versus Mode\nالدوري: {league_id}\nالجولات: {start_gw} → {end_gw}\n"
        "تحب أديك إيه؟", reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    if len(data) >= 5 and data[0] == "vs":
        league_id, start_gw, end_gw, action = int(data[1]), int(data[2]), int(data[3]), data[4]
        chat_id = update.effective_chat.id
        entry_id = get_user_entry_id(context, chat_id)
        if not entry_id:
            await query.edit_message_text("سجل فريقك الأول: /set_entry <ENTRY_ID>")
            return

        try:
            report_text, plan_text = await versus.report_and_plan(entry_id, league_id, start_gw, end_gw)
        except versus.ApiDownError as e:
            await alerts.offer_api_wait(update, context, reason=str(e))
            return

        if action == "report":
            await query.edit_message_text(report_text[:4096])
        elif action == "plan":
            await query.edit_message_text(plan_text[:4096])
        else:
            await query.edit_message_text(report_text[:4096])
            if plan_text:
                await context.bot.send_message(chat_id=chat_id, text=plan_text[:4096])

# ===== Alerts =====
async def alerts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    entry_id = get_user_entry_id(context, chat_id)
    if not entry_id:
        await update.message.reply_text("سجل فريقك الأول: /set_entry <ENTRY_ID>")
        return
    text = await alerts.team_injuries_now(entry_id)
    await update.message.reply_text(text[:4096])

# ===== API Fallback =====
async def api_retry_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    ok, _ = fantasy.check_api_health()
    if ok:
        await context.bot.send_message(chat_id, "✅ الـ API رجع! تقدر تعيد الأمر.")
        context.job.schedule_removal()

async def api_wait_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "api_wait_60s":
        context.job_queue.run_once(api_retry_job, when=60, chat_id=update.effective_chat.id)
        await query.edit_message_text("⏳ هستنى 60 ثانية وأشيّك وأبلغك.")
    elif query.data == "api_use_cache":
        await query.edit_message_text("📦 هشوف لو في داتا قديمة أستخدمها.")

# ===== Main =====
def main():
    if not BOT_TOKEN:
        raise RuntimeError("⚠️ BOT_TOKEN مش موجود في Environment Variables")

    persistence = PicklePersistence(filepath="state.pkl")
    app = Application.builder().token(BOT_TOKEN).persistence(persistence).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("api_status", api_status))
    app.add_handler(CommandHandler("set_entry", set_entry))
    app.add_handler(CommandHandler("plan", plan_cmd))
    app.add_handler(CommandHandler("versus", versus_cmd))
    app.add_handler(CommandHandler("alerts", alerts_cmd))
    app.add_handler(CallbackQueryHandler(callbacks, pattern=r"^vs\|"))
    app.add_handler(CallbackQueryHandler(api_wait_button, pattern=r"^api_"))

    log.info("🚀 ShadowMindX is running...")
    app.run_polling()

if __name__ == "__main__":
    main()