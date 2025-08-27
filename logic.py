import fpl_api
import storage

# ======== GET CURRENT GW ========
def get_current_gw():
    events = fpl_api.get_events()
    for event in events:
        if not event["finished"]:
            return event["id"]
    return events[-1]["id"]

# ======== /review ========
def review_team(entry_id):
    """
    تحليل الفريق الحالي واقتراح التحسينات.
    """
    try:
        picks_data = fpl_api.get_entry_picks(entry_id)
        if not picks_data:
            return "مش قادر يجلب بيانات الفريق الآن. حاول لاحقًا."
        
        message = "تشكيلة الفريق الحالية:\n"
        for pick in picks_data.get("picks", []):
            player_id = pick["element"]
            multiplier = pick.get("multiplier", 1)
            player_name = fpl_api.get_player_name(player_id)
            message += f"- {player_name} (Multiplier: {multiplier})\n"
        
        message += "\nاقتراح: راجع اللاعبين المصابين وغيرهم لتعديل التشكيلة."
        return message

    except Exception as e:
        return f"حدث خطأ أثناء تحليل الفريق: {e}"

# ======== /plan ========
def plan_gw(entry_id, start_gw=None, end_gw=None):
    """
    اقتراح أفضل تشكيلة ونقلات للجولات.
    """
    try:
        if start_gw is None:
            start_gw = get_current_gw()
        
        message = f"اقتراح التشكيلة للجولة {start_gw}:\n"
        
        # استدعاء FPL API للحصول على أفضل اللاعبين المتاحين (مثال)
        best_squad = fpl_api.get_best_squad(entry_id, start_gw)
        for player in best_squad:
            message += f"- {player['name']} ({player['position']})\n"
        
        if end_gw and end_gw > start_gw:
            message += "\nخطة طويلة المدى للجولات القادمة:\n"
            for gw in range(start_gw + 1, end_gw + 1):
                message += f"- الجولة {gw}: راجع التشكيلة لاحقًا\n"
        
        message += "\nاقتراح نقلات: قم بتبديل اللاعبين المصابين أو أصحاب الأداء المنخفض."
        return message

    except Exception as e:
        return f"حدث خطأ أثناء تجهيز خطة الجولة: {e}"

# ======== /versus ========
def versus_strategy(entry_id, league_id=None, gw=None):
    """
    تحليل الجولة ضد خصم محدد ووضع خطة المواجهة.
    """
    try:
        if gw is None:
            gw = get_current_gw()
        if league_id is None:
            league_id = storage.get_settings().get("league_id")
        if not league_id:
            return "يرجى تحديد الدوري أولاً."
        
        league_data = fpl_api.get_league_data(league_id)
        opponent = fpl_api.get_opponent(entry_id, league_data, gw)
        if not opponent:
            return "غير قادر على جلب بيانات الخصم."

        message = f"مواجهة الجولة {gw} ضد {opponent['name']}:\n"
        message += f"- نقاط الخصم: {opponent['points']}\n"
        message += "- اقتراح استراتيجية: اختر التشكيلة التي تتفوق على نقاط ومراكز الخصم.\n"
        return message

    except Exception as e:
        return f"حدث خطأ أثناء تجهيز استراتيجية المواجهة: {e}"