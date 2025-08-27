import fpl_api

# ======== تتبع المنافسين ========
def track_opponents(league_id):
    """
    جلب بيانات الفرق المنافسة في الدوري المحدد
    """
    standings = fpl_api.get_league_standings(league_id)
    if not standings:
        return "مش قادر يجلب بيانات الدوري الآن."
    
    results = []
    for entry in standings.get("standings", {}).get("results", []):
        team_name = entry.get("player_name", "Unknown")
        points = entry.get("total", 0)
        results.append(f"{team_name}: {points} نقطة")
    
    return "ترتيب الفرق في الدوري:\n" + "\n".join(results)

# ======== إنشاء ملفات البيانات ========
def generate_files(league_id, filename="league_data.json"):
    """
    إنشاء ملف JSON يحتوي على بيانات الفرق في الدوري
    """
    standings = fpl_api.get_league_standings(league_id)
    if not standings:
        return "مش قادر يجلب بيانات الدوري الآن."
    
    import json
    try:
        with open(filename, "w") as f:
            json.dump(standings, f, indent=4)
        return f"تم إنشاء الملف بنجاح: {filename}"
    except Exception as e:
        return f"حدث خطأ أثناء إنشاء الملف: {e}"