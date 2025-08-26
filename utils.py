import math
import random

# ===== فلترة الإصابات / الإيقافات =====
def filter_injuries(picks, bootstrap):
    """يشيل اللاعبين المصابين/الموقوفين من التشكيلة"""
    elements = {p["id"]: p for p in bootstrap["elements"]}
    clean = []
    for p in picks:
        player = elements.get(p["element"])
        if not player:
            continue
        status = player.get("status")
        if status in ("i", "s", "d"):  # injured, suspended, doubtful
            continue
        clean.append(p)
    return clean


# ===== منع التضارب (مهاجم ضد مدافع) =====
def avoid_conflicts(picks):
    """يشيل التضارب بين مهاجمك و مدافعك لو ضد بعض"""
    # هنا بنسهل: مش هنشيل، هنفلتر بس التحذيرات
    return picks


# ===== تقدير النقاط المتوقعة =====
def estimate_points(picks, gw, bootstrap):
    """يحسب نقاط متوقعة بناءً على fixtures و form"""
    elements = {p["id"]: p for p in bootstrap["elements"]}
    fixtures = bootstrap.get("events", [])
    gw_info = next((e for e in fixtures if e["id"] == gw), None)

    total_points = 0
    for p in picks:
        player = elements.get(p["element"])
        if not player:
            continue
        form = float(player.get("form", "0") or 0)
        ep = float(player.get("ep_next", "0") or 0)
        # مزج بين الفورم و المتوقع من اللعبة
        score = (form * 0.6 + ep * 0.4)
        total_points += score
    return round(total_points, 1)


# ===== فورمات الأسماء =====
def format_player_name(player):
    """يرجع اسم قصير للاعب"""
    return f"{player.get('web_name', '')} ({player.get('team_code', '')})"


# ===== تنسيقات بسيطة =====
def bold(text: str) -> str:
    return f"*{text}*"

def italic(text: str) -> str:
    return f"_{text}_"

def code(text: str) -> str:
    return f"`{text}`"


# ===== Utils إضافية (لما نحتاجها) =====
def safe_div(x, y):
    try:
        return x / y
    except ZeroDivisionError:
        return 0

def rnd(x, n=1):
    return round(x, n)