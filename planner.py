# planner.py
from fantasy import get_entry_team, get_bootstrap_sync, get_current_gw
import random

# ----------------------------
# Normal Mode + Timeline + Balance
async def plan_rounds(entry_id, league_id=None, target_gw=None, num_rounds=1, balance_mode=False):
    """
    تحضير خطة الجولة أو جولات متعددة
    """
    results = []
    bootstrap = get_bootstrap_sync()
    current_gw = get_current_gw(bootstrap)
    start_gw = target_gw or current_gw + 1

    for i in range(num_rounds):
        gw = start_gw + i
        team_data = await get_entry_team(entry_id, gw)
        plan = {
            "gw": gw,
            "players": [p["element"] for p in team_data.get("picks", [])],
            "captain": team_data["picks"][0]["element"] if team_data.get("picks") else None
        }
        results.append(plan)

    if balance_mode:
        safe_plan = results
        risky_plan = []
        for r in results:
            risky_r = r.copy()
            risky_r["players"] = r["players"][::-1]  # مثال للاعبي high-risk
            risky_plan.append(risky_r)
        return {"safe": safe_plan, "risky": risky_plan}

    return {"plan": results}

# ----------------------------
# Auto Review
async def review_team(entry_id, target_gw=None):
    gw = target_gw or get_current_gw(get_bootstrap_sync()) + 1
    team_data = await get_entry_team(entry_id, gw)
    review = {
        "players": [p["element"] for p in team_data.get("picks", [])],
        "captain": team_data["picks"][0]["element"] if team_data.get("picks") else None
    }
    return review

# ----------------------------
# Hacker Mode 😎
async def hacker_analysis(entry_id, league_id, opponent_entry_id=None, target_gw=None):
    """
    تحليل خصم الجولة القادمة في الدوري H2H
    """
    if not opponent_entry_id:
        # إذا لم يُحدد الخصم، نختار أول خصم متاح من الدوري
        matches_data = await get_h2h_matches(league_id)
        matches = matches_data.get("matches", [])
        gw = target_gw or get_current_gw(get_bootstrap_sync()) + 1
        for m in matches:
            if m["event"] == gw:
                if m["entry_1"] == entry_id:
                    opponent_entry_id = m["entry_2"]
                    break
                elif m["entry_2"] == entry_id:
                    opponent_entry_id = m["entry_1"]
                    break
        if not opponent_entry_id:
            return "❌ لا يوجد خصم محدد للجولة القادمة."

    opp_team = await get_entry_team(opponent_entry_id, target_gw or get_current_gw(get_bootstrap_sync()) + 1)
    predicted_points = sum([random.randint(1, 10) for _ in opp_team.get("picks", [])])
    return {
        "opponent_id": opponent_entry_id,
        "predicted_points": predicted_points
    }

# ----------------------------
# Luxury Features ✨
async def captaincy_advisor(team_data):
    players = team_data.get("players", [])
    if not players:
        return "لا يوجد بيانات للاعبين"
    captain = team_data.get("captain") or players[0]
    advice = f"اختيار الكابتن: {captain}. تحقق من سلامته قبل الجولة!"
    return advice

async def differentials_radar(team_data):
    players = team_data.get("players", [])
    if not players:
        return []
    diff_players = random.sample(players, min(3, len(players)))
    return diff_players