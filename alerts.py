import fpl_api

# ======== جلب الأخبار والإصابات ========
def get_alerts():
    """
    ترجع كل أخبار اللاعبين والإصابات جاهزة للعرض على تيليجرام
    """
    bootstrap = fpl_api.get_bootstrap_data()
    fixtures = fpl_api.get_fixtures()
    
    if not bootstrap or not fixtures:
        return "مش قادر يجلب الأخبار أو الإصابات الآن."
    
    players = bootstrap.get("elements", [])
    news_messages = []
    
    for player in players:
        news = player.get("news", "")
        injury_status = player.get("injury_status", "")
        if news or injury_status:
            msg = f"{player['web_name']}: "
            if injury_status:
                msg += f"إصابة ({injury_status}) "
            if news:
                msg += f"خبر: {news}"
            news_messages.append(msg)
    
    if not news_messages:
        return "لا توجد أخبار أو إصابات حالياً."
    
    return "\n".join(news_messages)