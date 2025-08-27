import os
from pathlib import Path

# مجلد حفظ السكرينز
SCREENSHOT_DIR = Path("screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

# ======== حفظ السكرين شوت ========
def save_screenshot(file, entry_id, command, side=None):
    """
    يحفظ الصورة في المسار المناسب:
    side: 'own' أو 'opponent' للـ versus
    """
    entry_dir = SCREENSHOT_DIR / str(entry_id)
    entry_dir.mkdir(exist_ok=True)
    
    if command == "versus":
        if side not in ["own", "opponent"]:
            raise ValueError("لـ versus يجب تحديد side: 'own' أو 'opponent'")
        filename = entry_dir / f"{command}_{side}.png"
    else:
        filename = entry_dir / f"{command}.png"

    file.download(str(filename))
    return filename

# ======== تحقق من السكرين شوت موجود ========
def check_screenshot(entry_id, command, side=None):
    entry_dir = SCREENSHOT_DIR / str(entry_id)
    if not entry_dir.exists():
        return False
    if command == "versus":
        if side not in ["own", "opponent"]:
            return False
        file_path = entry_dir / f"{command}_{side}.png"
        return file_path.exists()
    else:
        file_path = entry_dir / f"{command}.png"
        return file_path.exists()

# ======== استخراج اللاعبين من صورة عادية ========
def extract_players(entry_id, command, side=None):
    """
    ترجع لائحة اللاعبين من السكرين المحفوظ
    side: فقط لل versus
    """
    entry_dir = SCREENSHOT_DIR / str(entry_id)
    if command == "versus":
        if side not in ["own", "opponent"]:
            raise ValueError("لـ versus يجب تحديد side: 'own' أو 'opponent'")
        file_path = entry_dir / f"{command}_{side}.png"
        return extract_players_from_file(file_path)
    else:
        file_path = entry_dir / f"{command}.png"
        return extract_players_from_file(file_path)

# ======== استخراج اللاعبين من ملف الصورة ========
def extract_players_from_file(file_path):
    """
    هنا ضع الكود الفعلي لاستخراج أسماء اللاعبين من الصورة.
    حاليا مجرد مثال:
    """
    players = ["Player1", "Player2", "Player3", "Player4", "Player5"]
    return players