import fpl_api
import storage
import screenshot_handler

# ======== GET CURRENT GW ========
def get_current_gw():
    events = fpl_api.get_events()
    for event in events:
        if not event["finished"]:
            return event["id"]
    return events[-1]["id"]

# ======== /review ========
def review_team(entry_id, players=None):
    """
    تحليل الفريق الحالي واقتراح التحسينات.
    إذا تم تمرير players من screenshot يستخدمهم بدل API.
    """
    try:
        if players is None:
            picks_data = fpl_api.get_entry_picks(entry_id)
            if not picks_data:
                return "مش قادر يجلب بيانات الفريق الآن. حاول لاحقًا."
            
            players_list = []
            for pick in picks_data.get("picks", []):
                player_id = pick["element"]
                multiplier = pick.get("multiplier", 1)
                player_name = fpl_api.get_player_name(player_id)
                players_list.append(f"{player_name} (Multiplier: {multiplier})")
        else:
            # players جاي من screenshot
            players_list = [f"{p}" for p in players]

        message = "تشكيلة الفريق الحالية:\n"
        for p in players_list:
            message += f"- {p}\n"
        
        message += "\nاقتراح: راجع اللاعبين المصابين وغيرهم لتعديل التشكيلة."
        return message

    except Exception as e:
        return f"حدث خطأ أثناء تحليل الفريق: {e}"

# ======== /plan ========
def plan_gw(entry_id, players=None, start_gw=None, end_gw=None):
    """
    اقتراح أفضل تشكيلة ونقلات للجولات.
    players: قائمة اللاعبين المستخرجة من screenshot
    """
    try:
        if start_gw is None:
            start_gw = get_current_gw()
        
        message = f"اقتراح التشكيلة للجولة {start_gw}:\n"
        
        if players is None:
            # استدعاء FPL API للحصول على أفضل اللاعبين المتاحين
            best_squad = fpl_api.get_best_squad(entry_id, start_gw)
            for player in best_squad:
                message += f"- {player['name']} ({player['position']})\n"
        else:
            for player in players:
                message += f"- {player}\n"
        
        if end_gw and end_gw > start_gw:
            message += "\nخطة طويلة المدى للجولات القادمة:\n"
            for gw in range(start_gw + 1, end_gw + 1):
                message += f"- الجولة {gw}: راجع التشكيلة لاحقًا\n"
        
        message += "\nاقتراح نقلات: قم بتبديل اللاعبين المصابين أو أصحاب الأداء المنخفض."
        return message

    except Exception as e:
        return f"حدث خطأ أثناء تجهيز خطة الجولة: {e}"

# ======== /versus ========
def versus_strategy(entry_id, league_id=None, gw=None, players=None):
    """
    تحليل الجولة ضد خصم محدد ووضع خطة المواجهة.
    players: {"own": [...], "opponent": [...]} إذا موجود من screenshot
    """
    try:
        if gw is None:
            gw = get_current_gw()
        if league_id is None:
            league_id = storage.get_settings().get("league_id")
        if not league_id:
            return "يرجى تحديد الدوري أولاً."
        
        if players is None:
            league_data = fpl_api.get_league_data(league_id)
            opponent = fpl_api.get_opponent(entry_id, league_data, gw)
            if not opponent:
                return "غير قادر على جلب بيانات الخصم."
            own_players = None
            opp_players = None
        else:
            own_players = players.get("own", [])
            opp_players = players.get("opponent", [])
            opponent = {"name": "الخصم", "points": "غير متوفر"}

        message = f"مواجهة الجولة {gw} ضد {opponent['name']}:\n"
        if opponent.get("points"):
            message += f"- نقاط الخصم: {opponent['points']}\n"
        if own_players:
            message += "\nلاعبوك:\n" + "\n".join(f"- {p}" for p in own_players)
        if opp_players:
            message += "\nلاعبو الخصم:\n" + "\n".join(f"- {p}" for p in opp_players)
        message += "\nاقتراح استراتيجية: اختر التشكيلة التي تتفوق على نقاط ومراكز الخصم.\n"
        return message

    except Exception as e:
        return f"حدث خطأ أثناء تجهيز استراتيجية المواجهة: {e}"

# ======== RUN COMMAND WITH PLAYERS ========
def run_command_with_players(cmd, entry_id, players):
    """
    استدعاء الدوال المناسبة بناءً على cmd و players من screenshot
    """
    if cmd == "review":
        return review_team(entry_id, players)
    elif cmd == "plan":
        return plan_gw(entry_id, players)
    elif cmd == "versus":
        return versus_strategy(entry_id, players=players)
    elif cmd == "luxury":
        return f"ميّزات Luxury ستعمل هنا على {len(players)} لاعب"
    elif cmd == "hacker":
        return f"Hacker Mode سيعمل هنا على {len(players)} لاعب"
    else:
        return "أمر غير معروف"