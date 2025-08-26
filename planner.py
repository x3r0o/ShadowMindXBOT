import fantasy
import utils

async def build_plan_text(entry_id: int, start_gw: int, end_gw: int) -> str:
    """
    بيبني خطة كاملة للجولات مع فلاتر و تحليل
    """
    bootstrap = await fantasy.get_bootstrap_async()
    if isinstance(bootstrap, dict) and bootstrap.get("error"):
        return "❌ مش قادر أجيب داتا دلوقتي. حاول تاني."

    team_name = f"Entry {entry_id}"
    info = await fantasy.get_entry_info(entry_id)
    if info and "name" in info:
        team_name = info["name"]

    lines = [f"📊 خطة {team_name}\nمن GW {start_gw} لحد GW {end_gw}"]

    for gw in range(start_gw, end_gw + 1):
        gw_data = await fantasy.get_entry_team(entry_id, gw)
        if not gw_data or "error" in gw_data:
            lines.append(f"\n🗓️ GW {gw}: ❌ مش لاقي داتا")
            continue

        picks = gw_data.get("picks", [])
        history = gw_data.get("entry_history", {})
        score = history.get("points", 0)
        transfers = history.get("event_transfers", 0)
        bank = history.get("bank", 0) / 10.0

        # تقييم التشكيلة
        valid_picks = utils.filter_injuries(picks, bootstrap)
        clean_picks = utils.avoid_conflicts(valid_picks)

        # نقاط متوقعة
        expected_points = utils.estimate_points(clean_picks, gw, bootstrap)

        lines.append(
            f"\n🗓️ GW {gw}:"
            f"\n   • التشكيلة: {len(clean_picks)} لاعب"
            f"\n   • الترانسفيرات: {transfers}"
            f"\n   • البنك: £{bank:.1f}m"
            f"\n   • النقاط الفعلية: {score}"
            f"\n   • النقاط المتوقعة: {expected_points}"
        )

        # ملاحظات
        warnings = []
        if len(clean_picks) < 11:
            warnings.append("❗ ناقصك لاعيبة أساسية")
        if len(valid_picks) != len(picks):
            warnings.append("⚠️ عندك لاعيبة مصابة/موقوفة")
        if bank < 0:
            warnings.append("💸 الخطة دي مش في حدود الميزانية")

        if warnings:
            lines.extend(["   " + w for w in warnings])

    return "\n".join(lines)