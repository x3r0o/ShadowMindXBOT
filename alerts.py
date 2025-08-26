from typing import List
import fantasy
import utils
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

async def team_injuries_now(entry_id: int) -> str:
    bootstrap = await fantasy.get_bootstrap_async()
    if isinstance(bootstrap, dict) and bootstrap.get("error"):
        return "❌ الـ API مش متاح دلوقتي."

    current_gw = fantasy.get_current_gw(bootstrap)
    ok, picks = fantasy.get_entry_picks(entry_id, current_gw)
    if not ok:
        return "⚠️ مش قادر أجيب تشكيلتك دلوقتي."

    pmap = fantasy.get_player_dict(bootstrap)
    flagged: List[str] = []
    for p in picks.get("picks", []):
        el = pmap.get(p["element"])
        if not el: continue
        st = el.get("status")
        if st in ("d", "i", "s"):
            flagged.append(f"• {el['web_name']} — {utils.status_to_text(st)} | {el.get('news','')[:70]}")

    if not flagged:
        return "✅ مفيش إصابات/إيقافات ظاهرة في فريقك دلوقتي."
    return "🚑 تنبيه إصابات/إيقافات:\n" + "\n".join(flagged)

async def offer_api_wait(update: Update, context: ContextTypes.DEFAULT_TYPE, reason: str):
    keyboard = [
        [InlineKeyboardButton("⏳ استنى 60 ثانية وجرب", callback_data="api_wait_60s")],
        [InlineKeyboardButton("📦 كمّل بآخر داتا مخزنة (لو متاحة)", callback_data="api_use_cache")],
    ]
    await update.effective_message.reply_text(
        "🟥 الـ API واقع أو مش متاح حاليًا.\n"
        "تحب تعمل إيه؟", reply_markup=InlineKeyboardMarkup(keyboard)
    )