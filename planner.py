from fantasy import get_entry_team, get_bootstrap_sync, get_current_gw
import random

# ----------------------------
# Normal Mode + Timeline + Balance
async def plan_rounds(entry_id, league_id, target_gw=None, num_rounds=None, balance_mode=False):
    """
    تحضير خطة الجولة أو جولات متعددة
    """
    results = []
    bootstrap = get_bootstrap_sync()
    if "error" in bootstrap:
        return {"plan": [], "error": f"API error: {bootstrap['error']}"}

    current_gw = get_current_gw(bootstrap)
    start_gw = target_gw or current_gw + 1
    rounds = num_rounds or 1

    for i in range(rounds):
        gw = start_gw + i
        team_data = await get_entry_team(entry_id, gw)
        if "error" in team_data:
            results.append({"gw": gw, "error": team_data["error"]})
            continue

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
            risky_r["players"] = r["players"][::-1]
            risky_plan.append(risky_r)
        return {"safe": safe_plan, "risky": risky_plan}

    return {"plan": results}

# ----------------------------
# Auto Review
async def review_team(entry_id, target_gw=None):
    gw = target_gw or get_current_gw(get_bootstrap_sync()) + 1
    team_data = await get_entry_team(entry_id, gw)
    if "error" in team_data:
        return {"error": team_data["error"]}

    review = {
        "players": [p["element"] for p in team_data.get("picks", [])],
        "captain": team_data["picks"][0]["element"] if team_data.get("picks") else None
    }
    return review

# ----------------------------
# Versus Mode
async def generate_versus_report(entry_id, opponent_entry_id, target_gw):
    your_team = await get_entry_team(entry_id, target_gw)
    opp_team = await get_entry_team(opponent_entry_id, target_gw)
    if "error" in your_team:
        return {"your_score": 0, "opponent_score": 0, "error": your_team["error"]}
    if "error" in opp_team:
        return {"your_score": 0, "opponent_score": 0, "error": opp_team["error"]}

    your_score = sum([p.get("multiplier", 1) * 2 for p in your_team.get("picks", [])])
    opponent_score = sum([p.get("multiplier", 1) * 2 for p in opp_team.get("picks", [])])
    return {"your_score": your_score, "opponent_score": opponent_score}

async def generate_versus_plan(entry_id, opponent_entry_id, target_gw):
    report = await generate_versus_report(entry_id, opponent_entry_id, target_gw)
    if "error" in report:
        return {"plan": f"Error: {report['error']}"}

    if report["your_score"] < report["opponent_score"]:
        advice = "قم بتعديل الكابتن وبعض اللاعبين لتحسين النتيجة."
    else:
        advice = "الفريق جيد، لا تعديل مطلوب."
    return {"plan": advice}

# ----------------------------
# Hacker Mode 😎
async def hacker_analysis(entry_id, league_id, opponent_entry_id, target_gw):
    """
    تحليل خصم الجولة القادمة في الدوري H2H
    """
    if not opponent_entry_id:
        return "لا يوجد خصم محدد للجولة."
    opp_team = await get_entry_team(opponent_entry_id, target_gw)
    if "error" in opp_team:
        return f"API error: {opp_team['error']}"

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

# ----------------------------
# Optional: قراءة Screenshot
async def read_screenshot(image_path):
    """
    تحليل صورة اللاعبين (اختياري)
    """
    return {"players_detected": ["Player1", "Player2", "Player3"]}