import requests

BASE_URL = "https://fantasy.premierleague.com/api"

# ======== جلب كل بيانات اللعبة الأساسية ========
def get_bootstrap_data():
    try:
        res = requests.get(f"{BASE_URL}/bootstrap-static/", timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Error fetching bootstrap data: {e}")
        return None

# ======== دالة مساعدة ========
def get_player_name(player_id):
    """ترجع اسم اللاعب من الـ bootstrap data"""
    data = get_bootstrap_data()
    if not data:
        return f"Player {player_id}"
    for player in data.get("elements", []):
        if player["id"] == player_id:
            return player["web_name"]
    return f"Player {player_id}"

# ======== بيانات فريق محدد ========
def get_entry(entry_id):
    try:
        res = requests.get(f"{BASE_URL}/entry/{entry_id}/", timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Error fetching entry {entry_id}: {e}")
        return None

# ======== تحقق من Entry ID ========
def validate_entry_id(entry_id):
    entry = get_entry(entry_id)
    return bool(entry and "id" in entry)

# ======== تاريخ النقاط للفريق ========
def get_entry_history(entry_id):
    try:
        res = requests.get(f"{BASE_URL}/entry/{entry_id}/history/", timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Error fetching entry history {entry_id}: {e}")
        return None

# ======== تشكيلة الفريق الحالية ========
def get_entry_picks(entry_id):
    try:
        res = requests.get(f"{BASE_URL}/entry/{entry_id}/picks/", timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Error fetching entry picks {entry_id}: {e}")
        return None

# ======== الدوريات الخاصة بالفريق ========
def get_entry_leagues(entry_id):
    try:
        res = requests.get(f"{BASE_URL}/entry/{entry_id}/leagues/standard/", timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Error fetching entry leagues {entry_id}: {e}")
        return None

# ======== ترتيب الدوري ========
def get_league_standings(league_id):
    try:
        res = requests.get(f"{BASE_URL}/leagues-classic/{league_id}/standings/", timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Error fetching league standings {league_id}: {e}")
        return None

# ======== بيانات الجولة الحالية ========
def get_event_live(event_id):
    try:
        res = requests.get(f"{BASE_URL}/event/{event_id}/live/", timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Error fetching live event {event_id}: {e}")
        return None

# ======== جلب مباريات و أخبار اللاعبين ========
def get_fixtures():
    try:
        res = requests.get(f"{BASE_URL}/fixtures/", timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Error fetching fixtures: {e}")
        return None