import fpl_api
import storage
import json

# ======== تتبع المنافسين ========
def track_opponents(league_id=None):
    """
    جلب بيانات الفرق المنافسة في الدوري المحدد
    """
    try:
        if league_id is None:
            league_id = storage.get_settings().get("league_id")
        if not league_id:
            return "❌ يرجى تحديد الدوري أولاً."
        
        standings = fpl_api.get_league_standings(league_id)
        if not standings:
            return "⚠️ مش قادر يجلب بيانات الدوري الآن."
        
        results = []
        for entry in standings.get("standings", {}).get("results", []):
            team_name = entry.get("player_name", "Unknown")
            points = entry.get("total", 0)
            results.append(f"- {team_name}: {points} نقطة")
        
        return "🏆 ترتيب الفرق في الدوري:\n" + "\n".join(results)

    except Exception as e:
        return f"❌ حدث خطأ أثناء جلب ترتيب الفرق: {e}"


# ======== إنشاء ملفات البيانات ========
def generate_files(league_id=None, filename="league_data.json"):
    """
    إنشاء ملف JSON يحتوي على بيانات الفرق في الدوري
    """
    try:
        if league_id is None:
            league_id = storage.get_settings().get("league_id")
        if not league_id:
            return "❌ يرجى تحديد الدوري أولاً."
        
        standings = fpl_api.get_league_standings(league_id)
        if not standings:
            return "⚠️ مش قادر يجلب بيانات الدوري الآن."
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(standings, f, indent=4, ensure_ascii=False)
        return f"✅ تم إنشاء الملف بنجاح: {filename}"

    except Exception as e:
        return f"❌ حدث خطأ أثناء إنشاء الملف: {e}"


# ======== MAIN HACKER FUNCTION ========
def main_hacker(entry_id=None):
    """
    واجهة تشغيل Hacker Mode: يجمع Track + Generate Files
    """
    league_id = storage.get_settings().get("league_id")
    track_msg = track_opponents(league_id)
    file_msg = generate_files(league_id)
    return f"{track_msg}\n\n{file_msg}"