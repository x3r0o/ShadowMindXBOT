import fpl_api

# ======== Captaincy Advisor 👑 ========
def captaincy_advisor(entry_id, gw):
    """
    يقترح أفضل كابتن للجولة القادمة بناءً على النقاط السابقة وأداء اللاعبين
    """
    picks = fpl_api.get_entry_picks(entry_id)
    if not picks:
        return "مش قادر يجلب بيانات الفريق الآن."

    # مثال مبسط: يقترح اللاعب صاحب أكبر multiplier سابق أو أي لاعب في الفريق
    # لاحقًا يمكن تحسينه بتحليل الأداء والمباراة القادمة
    players = picks.get("picks", [])
    if not players:
        return "لا توجد تشكيلة حالية."

    captain = players[0]  # اختيار أول لاعب مؤقت
    return f"أفضل اختيار للكابتن في الجولة {gw}: لاعب ID {captain['element']}"

# ======== Differentials Radar 🌟 ========
def differentials_radar(entry_id):
    """
    يوضح اللاعبين المختلفين (نسبة اختيار قليلة ونقاط محتملة عالية)
    """
    bootstrap = fpl_api.get_bootstrap_data()
    if not bootstrap:
        return "مش قادر يجلب بيانات اللاعبين الآن."
    
    players = bootstrap.get("elements", [])
    diffs = []

    for player in players:
        if player["selected_by_percent"] < 5.0:  # أقل من 5% اختيار
            diffs.append(f"{player['web_name']} - نسبة اختيار: {player['selected_by_percent']}%")
    
    if not diffs:
        return "لا يوجد فروقات مهمة حاليًا."
    
    return "أفضل الفروقات:\n" + "\n".join(diffs)

# ======== Performance Review 📊 ========
def performance_review(entry_id):
    """
    تقييم أداء الفريق الحالي أو اللاعبين الفرديين
    """
    picks = fpl_api.get_entry_picks(entry_id)
    if not picks:
        return "مش قادر يجلب بيانات الفريق الآن."
    
    players = picks.get("picks", [])
    message = "تقييم أداء اللاعبين الحالي:\n"
    for p in players:
        # نقاط اللاعب حتى الآن (مثال مبسط)
        points = p.get("stats", {}).get("total_points", 0)
        message += f"- لاعب ID {p['element']}: نقاط حتى الآن {points}\n"
    
    return message