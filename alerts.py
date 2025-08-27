import logging
from fantasy import get_bootstrap_sync, get_entry_team

log = logging.getLogger("alerts")

# ----------------------------
async def send_alerts(entry_id: int):
    """
    جلب التنبيهات مثل الإصابات والتحذيرات ونسب الاختيار
    """
    try:
        bootstrap = get_bootstrap_sync()
        if "error" in bootstrap:
            return {"alerts": [f"API error: {bootstrap['error']}"], "differentials": []}

        current_gw = max([e["id"] for e in bootstrap.get("events", []) if e["is_current"]] or [1])
        team_data = await get_entry_team(entry_id, current_gw)
        if "error" in team_data:
            return {"alerts": [f"API error: {team_data['error']}"], "differentials": []}

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

        return {"alerts": alerts_list, "differentials": differentials}
    except Exception as e:
        log.error(f"send_alerts failed: {e}")
        return {"alerts": [f"Error: {e}"], "differentials": []}

# ----------------------------
async def captain_alert(entry_id: int):
    """
    التحقق من حالة الكابتن الحالي
    """
    try:
        bootstrap = get_bootstrap_sync()
        if "error" in bootstrap:
            return f"API error: {bootstrap['error']}"

        current_gw = max([e["id"] for e in bootstrap.get("events", []) if e["is_current"]] or [1])
        team_data = await get_entry_team(entry_id, current_gw)
        if "error" in team_data:
            return f"API error: {team_data['error']}"

        picks = team_data.get("picks", [])
        elements = {e["id"]: e for e in bootstrap.get("elements", [])}

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