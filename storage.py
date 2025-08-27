import json
import os

# اسم ملف التخزين
DATA_FILE = "user_data.json"

# تهيئة الملف لو مش موجود
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)


# جلب البيانات كاملة
def load_data():
    with open(DATA_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    return data

# حفظ البيانات كاملة
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# Entry ID
def get_entry_id():
    data = load_data()
    return data.get("entry_id")

def set_entry_id(entry_id):
    data = load_data()
    data["entry_id"] = entry_id
    save_data(data)


# إعدادات الدوري والجولة
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