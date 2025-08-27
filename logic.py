import fpl_api
import storage

# ======== /review ========
def review_team(entry_id):
    """
    تحليل الفريق الحالي واقتراح التحسينات.
    ترجع نص يمكن عرضه مباشرة للمستخدم.
    """
    picks_data = fpl_api.get_entry_picks(entry_id)
    if not picks_data:
        return "مش قادر يجلب بيانات الفريق الآن. حاول لاحقًا."
    
    # مثال تبسيطي: عرض اللاعبين الحاليين والنقاط
    message = "تشكيلة الفريق الحالية:\n"
    for pick in picks_data.get("picks", []):
        player_id = pick["element"]
        multiplier = pick["multiplier"]  # كابتن 2 أو vice 1
        message += f"- لاعب ID: {player_id}, multiplier: {multiplier}\n"
    
    # لاحقًا ممكن نضيف اقتراحات لتحسين الفريق
    return message

# ======== /plan ========
def plan_gw(entry_id, start_gw, end_gw=None):
    """
    التخطيط للجولات:
    - start_gw: جولة البداية
    - end_gw: جولة النهاية (لو None يبقى جولة واحدة)
    """
    history = fpl_api.get_entry_history(entry_id)
    if not history:
        return "مش قادر يجلب تاريخ النقاط للفريق."
    
    # مثال مبسط: عرض نقاط الجولات
    message = ""
    if end_gw is None:
        # جولة واحدة
        gw = start_gw
        points = next((g["points"] for g in history.get("current", []) if g["event"] == gw), None)
        message = f"نقاط الجولة {gw}: {points}"
    else:
        # خطة طويلة المدى
        message = "نقاط الجولات:\n"
        for gw in range(start_gw, end_gw + 1):
            points = next((g["points"] for g in history.get("current", []) if g["event"] == gw), None)
            message += f"- الجولة {gw}: {points}\n"
    
    return message

# ======== /versus ========
def versus_strategy(entry_id, opponent_entry_id, gw):
    """
    تحليل الجولة ضد خصم محدد ووضع خطة المواجهة.
    """
    your_picks = fpl_api.get_entry_picks(entry_id)
    opponent_picks = fpl_api.get_entry_picks(opponent_entry_id)
    
    if not your_picks or not opponent_picks:
        return "مش قادر يجلب بيانات الفريق أو المنافس."
    
    # مثال مبسط: مقارنة عدد اللاعبين
    message = f"مقارنة الجولة {gw} مع الخصم:\n"
    message += f"- عدد لاعبيك: {len(your_picks.get('picks', []))}\n"
    message += f"- عدد لاعبي الخصم: {len(opponent_picks.get('picks', []))}\n"
    
    # لاحقًا ممكن نضيف اقتراح تغييرات أو خطة لمواجهة الخصم
    return message