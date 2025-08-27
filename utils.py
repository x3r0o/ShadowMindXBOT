# utils.py
import random
from fantasy import get_bootstrap_sync

# ----------------------------
# Cache للـ bootstrap
_bootstrap_cache = None
_players_cache = None

def get_all_players():
    global _bootstrap_cache, _players_cache
    if _players_cache:
        return _players_cache
    if not _bootstrap_cache:
        _bootstrap_cache = get_bootstrap_sync()
    elements = _bootstrap_cache.get("elements", [])
    _players_cache = {e["id"]: e for e in elements}
    return _players_cache

# ----------------------------
# تحويل تشكيلة من IDs لأسماء مع الحالة
def format_team(team_data, highlight_captain=True, highlight_vice=True, show_status=True):
    elements = get_all_players()
    picks = team_data.get("players") or [p["element"] for p in team_data.get("picks", [])]
    captain_id = team_data.get("captain") or (picks[0] if picks else None)
    vice_id = team_data.get("vice_captain")

    formatted = []
    for p_id in picks:
        player = elements.get(p_id)
        if not player:
            formatted.append(str(p_id))
            continue
        name = player["web_name"]
        status = player.get("status", "OK")
        display = f"{name} ({status})" if show_status else name
        if highlight_captain and p_id == captain_id:
            display = f"✨ {display} ✨"
        elif highlight_vice and p_id == vice_id:
            display = f"🌟 {display} 🌟"
        formatted.append(display)
    return formatted

# ----------------------------
# جلب اسم الكابتن (أو vice-captain لو الكابتن غير موجود)
def format_captain(team_data):
    elements = get_all_players()
    captain_id = team_data.get("captain") or team_data.get("vice_captain") or (team_data.get("players")[0] if team_data.get("players") else None)
    return elements[captain_id]["web_name"] if captain_id in elements else str(captain_id)

# ----------------------------
# تنسيق التنبيهات
def format_alerts(alerts_dict):
    alerts_list = alerts_dict.get("alerts", [])
    diff_list = alerts_dict.get("differentials", [])
    alerts_text = "🚨 Alerts:\n" + ("\n".join(alerts_list) if alerts_list else "لا توجد إصابات أو تحذيرات حالياً.")
    diff_text = "✨ Differentials:\n" + (", ".join(diff_list) if diff_list else "لا يوجد.")
    return f"{alerts_text}\n\n{diff_text}"

# ----------------------------
# أفضل N Differentials بأسماء اللاعبين
def top_differentials(team_data, count=3):
    elements = get_all_players()
    picks = team_data.get("players") or [p["element"] for p in team_data.get("picks", [])]
    sampled = random.sample(picks, min(count, len(picks))) if picks else []
    return [elements[p]["web_name"] if p in elements else str(p) for p in sampled]

# ----------------------------
# تصنيف اللاعبين حسب الحالة
def classify_players(team_data):
    elements = get_all_players()
    picks = team_data.get("players") or [p["element"] for p in team_data.get("picks", [])]
    safe, high_risk = [], []
    for p in picks:
        status = elements[p].get("status", "OK") if p in elements else "OK"
        if status in ["OK", "Fit"]:
            safe.append(elements[p]["web_name"] if p in elements else str(p))
        else:
            high_risk.append(elements[p]["web_name"] if p in elements else str(p))
    return {"safe": safe, "high_risk": high_risk}

# ----------------------------
# تنسيق خطة الجولات للعرض
def format_plan(plan_dict):
    elements = get_all_players()
    output = []
    rounds = plan_dict.get("plan", []) if "plan" in plan_dict else plan_dict.get("safe", [])
    for gw_entry in rounds:
        gw = gw_entry.get("gw")
        players = gw_entry.get("players", [])
        player_names = [elements[p]["web_name"] if p in elements else str(p) for p in players]
        output.append(f"GW{gw}: " + ", ".join(player_names))
    return "\n".join(output)