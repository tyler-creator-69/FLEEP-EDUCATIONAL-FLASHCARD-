from pathlib import Path
import sys
from PyQt6.QtGui import QFontDatabase
import os


APP_DIR = Path.home() / '.pyqt_flashcards'
IMG_DIR = APP_DIR / 'images'
APP_DIR.mkdir(exist_ok=True)
IMG_DIR.mkdir(exist_ok=True)
DB_PATH = APP_DIR / 'flashcards.db'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Detect dyslexic font if available
def find_dyslexic_font():
    font_path = os.path.join(BASE_DIR, "fonts", "OpenDyslexic3-Regular.ttf")
    if not os.path.exists(font_path):
        print(f"❌ Font file not found: {font_path}")
        return None

    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id != -1:
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            print(f"✅ Loaded OpenDyslexic: {families[0]}")
            return families[0]
    print("⚠️ Failed to load OpenDyslexic font.")
    return None

FALLBACK_FONT = 'Segoe UI' if sys.platform.startswith('win') else 'DejaVu Sans'
