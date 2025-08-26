from typing import Tuple, Optional, List
import fantasy
import utils

class ApiDownError(Exception):
    pass

async def report_and_plan(entry_id: int, league_id: int, start_gw: int, end_gw: int) -> Tuple[str, str]:
    bootstrap = await fantasy.get_bootstrap_async()
    if isinstance(bootstrap, dict) and bootstrap.get("error"):
        raise ApiDownError("bootstrap")

    # هجيب خصمك في H2H للجولة المستهدفة
    opp_entry, opp_name = fantasy.get_h2h_match(league_id, end_gw, entry_id)
    if not opp_entry:
        # ممكن يكون الدوري Classic مش H2H
        report = ("ℹ️ باين إن الدوري Classic (مفيش خصم مباشر).\n"
                  "لو عندك ENTRY_ID للخصم ابعتهولي بقى في رسالة منفصلة (النسخة دي مركزة H2H).")
        return report, ""

    # تقرير سريع
    report = await build_versus_report(entry_id, opp_entry, opp_name, end_gw, bootstrap)

    # خطة مضادة بسيطة (هيوريستك)
    plan = await build_counter_plan(entry_id, opp_entry, start_gw, end_gw, bootstrap)

    return report, plan

async def build_versus_report(my_entry: int, opp_entry: int, opp_name: str, gw: int, bootstrap: dict) -> str:
    my_exp = fantasy.get_entry_live_expected_points(my_entry, gw, bootstrap)
    op_exp = fantasy.get_entry_live_expected_points(opp_entry, gw, bootstrap)

    # Overlap تقديري (مش دقيق 100% بدون تفاصيل picks، بنحسب بأسماء XI الأساسي تقريبًا)
    my_ok, my_picks = fantasy.get_entry_picks(my_entry, gw)
    op_ok, op_picks = fantasy.get_entry_picks(opp_entry, gw)

    overlap_names: List[str] = []
    if my_ok and op_ok:
        pmap = fantasy.get_player_dict(bootstrap)
        my_ids = {p["element"] for p in my_picks.get("picks", []) if p.get("multiplier", 0) > 0}
        op_ids = {p["element"] for p in op_picks.get("picks", []) if p.get("multiplier", 0) > 0}
        both = list(my_ids & op_ids)
        for pid in both[:8]:
            nm = pmap.get(pid, {}).get("web_name", "??")
            overlap_names.append(nm)

    text = []
    text.append(f"📝 تقرير خصمك ({opp_name}) — GW {gw}")
    text.append(f"• نقاط متوقعة (تقريبية): أنت {my_exp} vs هو {op_exp}")
    if overlap_names:
        text.append("• لاعيبة مشتركة (تقريبية): " + ", ".join(overlap_names))
    else:
        text.append("• مفيش Overlap واضح كتير — فرصة تفرق بالديفرينشالز.")

    # Captaincy hint تقديري
    text.append("• نصيحة كابتن: اختار لاعب فورم + خصم سهل، ومش موجود عنده إن أمكن.")
    return "\n".join(text)

async def build_counter_plan(my_entry: int, opp_entry: int, start_gw: int, end_gw: int, bootstrap: dict) -> str:
    text = []
    text.append(f"🎯 خطة الفوز من GW {start_gw} → GW {end_gw}")

    # أول جولة: عالج إصابة/مخاطرة عندك
    my_ok, my_picks = fantasy.get_entry_picks(my_entry, start_gw)
    if not my_ok:
        text.append("⚠️ مش قادر أجيب تشكيلتك دلوقتي.")
        return "\n".join(text)

    pmap = fantasy.get_player_dict(bootstrap)
    bank = (my_picks.get("entry_history") or {}).get("bank", 0) / 10.0
    risky = []
    for p in my_picks.get("picks", []):
        el = pmap.get(p["element"])
        if not el: 
            continue
        if el.get("status") in ("d", "i", "s"):
            risky.append(el)

    if risky:
        vic = risky[0]
        pos = vic["element_type"]
        budget = vic["now_cost"]/10.0 + bank
        candidates = utils.best_replacements(bootstrap, pos, budget, exclude_ids=[vic["id"]])
        if candidates:
            c = candidates[0]
            text.append(f"• GW {start_gw}: بيع {vic['web_name']} → هات {c['web_name']} (فورم {c['form']}, £{c['now_cost']/10:.1f})")
        else:
            text.append(f"• GW {start_gw}: عندك مخاطرة ({vic['web_name']}), بس الميزانية ضيقة.")
    else:
        text.append(f"• GW {start_gw}: راجع الكابتنة + ظبط XI حسب الخصوم السهلة.")

    # الجولة المستهدفة: حاول تجيب Differential ضد خصمك
    op_ok, op_picks = fantasy.get_entry_picks(opp_entry, end_gw)
    op_set = set()
    if op_ok:
        op_set = {p["element"] for p in op_picks.get("picks", []) if p.get("multiplier", 0) > 0}
    diff = utils.find_differentials(bootstrap, exclude_ids=list(op_set), top_n=5)
    if diff:
        text.append(f"• GW {end_gw}: فكّر في Differential ضد خصمك: " + ", ".join([d['web_name'] for d in diff[:3]]))

    text.append("⚖️ لو محتاج -4، اعملها بس لو هتدي فرق نقاط واضح قدام خصمك.")
    return "\n".join(text)