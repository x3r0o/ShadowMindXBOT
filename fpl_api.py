import requests

BASE_URL = "https://fantasy.premierleague.com/api"

# ======== جلب كل بيانات اللعبة الأساسية ========
def get_bootstrap_data():
    """ترجع بيانات كل اللاعبين، الفرق، الجولات"""
    url = f"{BASE_URL}/bootstrap-static/"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Error fetching bootstrap data: {e}")
        return None

# ======== بيانات فريق محدد ========
def get_entry(entry_id):
    """ترجع بيانات الفريق الأساسي Entry ID"""
    url = f"{BASE_URL}/entry/{entry_id}/"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Error fetching entry {entry_id}: {e}")
        return None

# ======== التحقق من Entry ID ========
def validate_entry_id(entry_id):
    """
    تتحقق من صحة Entry ID.
    ترجع True لو موجود في FPL API، False لو مش موجود.
    """
    entry = get_entry(entry_id)
    if entry and "entry" in entry:
        return True
    return False

# ======== تاريخ النقاط للفريق ========
def get_entry_history(entry_id):
    """ترجع تاريخ نقاط الفريق لكل جولة"""
    url = f"{BASE_URL}/entry/{entry_id}/history/"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Error fetching entry history {entry_id}: {e}")
        return None

# ======== تشكيلة الفريق الحالية ========
def get_entry_picks(entry_id):
    """ترجع التشكيلة الحالية للفريق"""
    url = f"{BASE_URL}/entry/{entry_id}/picks/"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Error fetching entry picks {entry_id}: {e}")
        return None

# ======== الدوريات الخاصة بالفريق ========
def get_entry_leagues(entry_id):
    """ترجع الدوريات التي ينتمي لها الفريق"""
    url = f"{BASE_URL}/entry/{entry_id}/leagues/standard/"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Error fetching entry leagues {entry_id}: {e}")
        return None

# ======== ترتيب الدوري ========
def get_league_standings(league_id):
    """ترجع ترتيب الفرق في الدوري الكلاسيكي"""
    url = f"{BASE_URL}/leagues-classic/{league_id}/standings/"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Error fetching league standings {league_id}: {e}")
        return None

# ======== بيانات الجولة الحالية ========
def get_event_live(event_id):
    """ترجع بيانات الجولة الحالية (Live)"""
    url = f"{BASE_URL}/event/{event_id}/live/"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Error fetching live event {event_id}: {e}")
        return None

# ======== جلب مباريات و أخبار اللاعبين ========
def get_fixtures():
    """ترجع مواعيد المباريات والإصابات والحالة العامة للاعبين"""
    url = f"{BASE_URL}/fixtures/"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Error fetching fixtures: {e}")
        return None