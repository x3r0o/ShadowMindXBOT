import json
import os

# اسم ملف التخزين
DATA_FILE = "user_data.json"

# تهيئة الملف لو مش موجود
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f, indent=4)

# ======== جلب البيانات كاملة ========
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = {}
    return data

# ======== حفظ البيانات كاملة ========
def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving data: {e}")

# ======== Entry ID ========
def get_entry_id():
    data = load_data()
    return data.get("entry_id")

def set_entry_id(entry_id):
    data = load_data()
    data["entry_id"] = entry_id
    save_data(data)

def clear_entry_id():
    data = load_data()
    if "entry_id" in data:
        del data["entry_id"]
        save_data(data)

# ======== إعدادات الدوري والجولة ========
def get_settings():
    data = load_data()
    return {
        "league_id": data.get("league_id"),
        "selected_gw": data.get("selected_gw")
    }

def set_settings(league_id=None, selected_gw=None):
    data = load_data()
    if league_id is not None:
        data["league_id"] = league_id
    if selected_gw is not None:
        data["selected_gw"] = selected_gw
    save_data(data)

def clear_settings():
    data = load_data()
    removed = False
    for key in ["league_id", "selected_gw"]:
        if key in data:
            del data[key]
            removed = True
    if removed:
        save_data(data)