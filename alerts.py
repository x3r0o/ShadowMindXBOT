import logging
from fantasy import get_bootstrap_sync, get_entry_team

log = logging.getLogger("alerts")

# ----------------------------
async def send_alerts(entry_id: int):
    try:
        bootstrap = get_bootstrap_sync()
        current_gw = max([e["id"] for e in bootstrap.get("events", []) if e["is_current"]] or [1])
        team_data = await get_entry_team(entry_id, current_gw)
        picks = team_data.get("picks", [])
        elements = {e["id"]: e for e in bootstrap.get("elements", [])}

        alerts_list = []
        differentials = []

        for p in picks:
            player = elements.get(p["element"])
            if not player:
                continue
            status = player.get("status")
            news = player.get("news", "")
            ownership = player.get("selected_by_percent", 0.0)

            if status != "a" or news:
                alerts_list.append(f"{player['web_name']} ({status}) → {news}")
            if ownership < 5.0:
                differentials.append(f"{player['web_name']} ({ownership:.1f}%)")

        alerts_text = "🚨 Alerts:\n" + ("\n".join(alerts_list) if alerts_list else "لا توجد إصابات أو تحذيرات حالياً.")
        diff_text = "✨ Differentials:\n" + (", ".join(differentials) if differentials else "لا يوجد.")

        return f"{alerts_text}\n\n{diff_text}"
    except Exception as e:
        log.error(f"send_alerts failed: {e}")
        return f"حدث خطأ أثناء جلب التنبيهات: {e}"

# ----------------------------
async def captain_alert(entry_id: int):
    try:
        bootstrap = get_bootstrap_sync()
        current_gw = max([e["id"] for e in bootstrap.get("events", []) if e["is_current"]] or [1])
        team_data = await get_entry_team(entry_id, current_gw)
        picks = team_data.get("picks", [])
        elements = {e["id"]: e for e in bootstrap.get("elements", [])}

        # البحث عن اللاعب اللي محدد ككابتن
        captain_pick = next((p for p in picks if p.get("is_captain")), None)
        if not captain_pick:
            return "❌ لم يتم تحديد كابتن لهذا الفريق."

        captain = elements.get(captain_pick["element"])
        if not captain:
            return "❌ بيانات الكابتن غير موجودة."

        status = captain.get("status")
        news = captain.get("news", "")
        if status != "a" or news:
            return f"⚠️ تحذير الكابتن: {captain['web_name']} ({status}) → {news}"

        return "✔️ الكابتن آمن."
    except Exception as e:
        log.error(f"captain_alert failed: {e}")
        return f"حدث خطأ أثناء فحص الكابتن: {e}"