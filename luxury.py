import fpl_api
import storage
import screenshot_handler

# ======== Captaincy Advisor 👑 ========
def captaincy_advisor(entry_id, gw, players=None):
    """
    يقترح أفضل كابتن للجولة القادمة.
    players: قائمة اللاعبين أو dict للـ versus
    """
    try:
        if players is None:
            picks_data = fpl_api.get_entry_picks(entry_id)
            if not picks_data:
                return "مش قادر يجلب بيانات الفريق الآن."
            players_list = picks_data.get("picks", [])
        else:
            # لو players dict (versus) ناخد own
            if isinstance(players, dict) and "own" in players:
                players_list = players["own"]
            else:
                players_list = players

        if not players_list:
            return "لا توجد تشكيلة حالية."

        captain = players_list[0]  # مؤقت، ممكن نضيف خوارزمية أفضل
        if isinstance(captain, dict) and "element" in captain:
            player_name = fpl_api.get_player_name(captain['element'])
        else:
            player_name = captain  # لو اسم مباشرة من السكرين شوت

        return f"أفضل اختيار للكابتن في الجولة {gw}: {player_name}"

    except Exception as e:
        return f"حدث خطأ أثناء اقتراح الكابتن: {e}"


# ======== Differentials Radar 🌟 ========
def differentials_radar(entry_id, players=None):
    """
    يوضح اللاعبين المختلفين (نسبة اختيار قليلة ونقاط محتملة عالية)
    """
    try:
        bootstrap = fpl_api.get_bootstrap_data()
        if not bootstrap:
            return "مش قادر يجلب بيانات اللاعبين الآن."
        
        all_players = bootstrap.get("elements", [])
        diffs = []

        for player in all_players:
            if player.get("selected_by_percent", 0) < 5.0:  # أقل من 5% اختيار
                diffs.append(f"{player['web_name']} - نسبة اختيار: {player['selected_by_percent']}%")
        
        if not diffs:
            return "لا يوجد فروقات مهمة حاليًا."
        
        return "أفضل الفروقات:\n" + "\n".join(diffs)

    except Exception as e:
        return f"حدث خطأ أثناء تحليل الفروقات: {e}"


# ======== Performance Review 📊 ========
def performance_review(entry_id, players=None):
    """
    تقييم أداء الفريق الحالي أو اللاعبين الفرديين
    """
    try:
        if players is None:
            picks_data = fpl_api.get_entry_picks(entry_id)
            if not picks_data:
                return "مش قادر يجلب بيانات الفريق الآن."
            players_list = picks_data.get("picks", [])
        else:
            # لو players dict (versus) ناخد own
            if isinstance(players, dict) and "own" in players:
                players_list = players["own"]
            else:
                players_list = players

        if not players_list:
            return "لا توجد تشكيلة حالية."

        message = "تقييم أداء اللاعبين الحالي:\n"
        for p in players_list:
            if isinstance(p, dict) and "element" in p:
                points = p.get("stats", {}).get("total_points", 0)
                player_name = fpl_api.get_player_name(p['element'])
            else:
                player_name = p
                points = "غير متاح"

            message += f"- {player_name}: نقاط حتى الآن {points}\n"
        
        return message

    except Exception as e:
        return f"حدث خطأ أثناء تقييم الأداء: {e}"