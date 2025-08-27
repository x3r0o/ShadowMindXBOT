import aiohttp
import requests
import logging
from functools import lru_cache

log = logging.getLogger("fantasy")
BASE_URL = "https://fantasy.premierleague.com/api"

# ===== Health Check =====
def check_api_health() -> (bool, str):
    """
    يتأكد إن API شغال قبل أي طلبات
    """
    try:
        r = requests.get(f"{BASE_URL}/bootstrap-static/", timeout=5)
        if r.status_code == 200:
            return True, "API OK"
        return False, f"Status {r.status_code}"
    except Exception as e:
        return False, str(e)

# ===== Bootstrap =====
@lru_cache(maxsize=1)
def get_bootstrap_sync():
    try:
        r = requests.get(f"{BASE_URL}/bootstrap-static/", timeout=10)
        if r.status_code != 200:
            log.error(f"Bootstrap failed, status: {r.status_code}")
            return {"error": f"status {r.status_code}"}
        return r.json()
    except Exception as e:
        log.error(f"bootstrap failed: {e}")
        return {"error": str(e)}

async def get_bootstrap_async():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/bootstrap-static/") as resp:
                if resp.status != 200:
                    return {"error": f"status {resp.status}"}
                return await resp.json()
    except Exception as e:
        log.error(f"bootstrap async failed: {e}")
        return {"error": str(e)}

# ===== Current Gameweek =====
def get_current_gw(bootstrap: dict) -> int:
    events = bootstrap.get("events", [])
    for ev in events:
        if ev.get("is_current"):
            return ev["id"]
    return max([e["id"] for e in events]) if events else 1

# ===== Entry / Team =====
async def get_entry_team(entry_id: int, gw: int):
    url = f"{BASE_URL}/entry/{entry_id}/event/{gw}/picks/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {"error": f"status {resp.status}"}
                return await resp.json()
    except Exception as e:
        log.error(f"get_entry_team failed: {e}")
        return {"error": str(e)}

async def get_entry_info(entry_id: int):
    url = f"{BASE_URL}/entry/{entry_id}/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {"error": f"status {resp.status}"}
                return await resp.json()
    except Exception as e:
        log.error(f"get_entry_info failed: {e}")
        return {"error": str(e)}

# ===== Leagues =====
async def get_user_leagues(entry_id: int):
    url = f"{BASE_URL}/entry/{entry_id}/leagues/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {"error": f"status {resp.status}"}
                data = await resp.json()
                leagues = []
                # Classic leagues
                classic = data.get("classic", {}).get("standings", {}).get("results", [])
                # H2H leagues
                h2h = data.get("h2h", {}).get("standings", {}).get("results", [])
                for l in classic + h2h:
                    leagues.append({"id": l["entry"], "name": l["player_name"]})
                return leagues
    except Exception as e:
        log.error(f"get_user_leagues failed: {e}")
        return {"error": str(e)}

# ===== H2H Matches =====
async def get_h2h_matches(league_id: int, page: int = 1):
    url = f"{BASE_URL}/leagues-h2h-matches/league/{league_id}/?page={page}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {"error": f"status {resp.status}"}
                return await resp.json()
    except Exception as e:
        log.error(f"get_h2h_matches failed: {e}")
        return {"error": str(e)}

async def get_h2h_opponent(league_id: int, gw: int, entry_id: int):
    try:
        page = 1
        while True:
            matches_data = await get_h2h_matches(league_id, page)
            if "error" in matches_data:
                return {"id": None, "name": None}
            matches = matches_data.get("matches", [])
            if not matches:
                break
            for m in matches:
                if m["event"] == gw:
                    if m["entry_1"] == entry_id:
                        return {"id": m["entry_2"], "name": m.get("entry_2_name")}
                    elif m["entry_2"] == entry_id:
                        return {"id": m["entry_1"], "name": m.get("entry_1_name")}
            if matches_data.get("pagination", {}).get("has_next"):
                page += 1
            else:
                break
        return {"id": None, "name": None}
    except Exception as e:
        log.error(f"get_h2h_opponent failed: {e}")
        return {"id": None, "name": None}