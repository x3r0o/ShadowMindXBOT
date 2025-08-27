import fpl_api
import storage

# ======== Captaincy Advisor 👑 ========
def captaincy_advisor(entry_id, gw):
    """
    يقترح أفضل كابتن للجولة القادمة بناءً على النقاط السابقة وأداء اللاعبين
    """
    try:
        picks = fpl_api.get_entry_picks(entry_id)
        if not picks:
            return "مش قادر يجلب بيانات الفريق الآن."

        players = picks.get("picks", [])
        if not players:
            return "لا توجد تشكيلة حالية."

        # اختيار أول لاعب مؤقت (يمكن تطويره لاحقًا بتحليل الأداء والمباراة القادمة)
        captain = players[0]
        player_name = fpl_api.get_player_name(captain['element'])
        return f"أفضل اختيار للكابتن في الجولة {gw}: {player_name}"

    except Exception as e:
        return f"حدث خطأ أثناء اقتراح الكابتن: {e}"

# ======== Differentials Radar 🌟 ========
def differentials_radar(entry_id):
    """
    يوضح اللاعبين المختلفين (نسبة اختيار قليلة ونقاط محتملة عالية)
    """
    try:
        bootstrap = fpl_api.get_bootstrap_data()
        if not bootstrap:
            return "مش قادر يجلب بيانات اللاعبين الآن."
        
        players = bootstrap.get("elements", [])
        diffs = []

        for player in players:
            if player.get("selected_by_percent", 0) < 5.0:  # أقل من 5% اختيار
                diffs.append(f"{player['web_name']} - نسبة اختيار: {player['selected_by_percent']}%")
        
        if not diffs:
            return "لا يوجد فروقات مهمة حاليًا."
        
        return "أفضل الفروقات:\n" + "\n".join(diffs)

    except Exception as e:
        return f"حدث خطأ أثناء تحليل الفروقات: {e}"

# ======== Performance Review 📊 ========
def performance_review(entry_id):
    """
    تقييم أداء الفريق الحالي أو اللاعبين الفرديين
    """
    try:
        picks = fpl_api.get_entry_picks(entry_id)
        if not picks:
            return "مش قادر يجلب بيانات الفريق الآن."
        
        players = picks.get("picks", [])
        if not players:
            return "لا توجد تشكيلة حالية."

        message = "تقييم أداء اللاعبين الحالي:\n"
        for p in players:
            points = p.get("stats", {}).get("total_points", 0)
            player_name = fpl_api.get_player_name(p['element'])
            message += f"- {player_name}: نقاط حتى الآن {points}\n"
        
        return message

    except Exception as e:
        return f"حدث خطأ أثناء تقييم الأداء: {e}"