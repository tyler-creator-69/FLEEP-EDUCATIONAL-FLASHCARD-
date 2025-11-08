from pathlib import Path
import sys
from PyQt6.QtGui import QFontDatabase

APP_DIR = Path.home() / '.pyqt_flashcards'
IMG_DIR = APP_DIR / 'images'
APP_DIR.mkdir(exist_ok=True)
IMG_DIR.mkdir(exist_ok=True)
DB_PATH = APP_DIR / 'flashcards.db'

# Detect dyslexic font if available
def find_dyslexic_font():
    try:
        families = QFontDatabase().families()
        for f in families:
            if 'OpenDyslexic' in f or 'OpenDyslexic3' in f:
                return f
    except Exception:
        pass
    return None

FALLBACK_FONT = 'Segoe UI' if sys.platform.startswith('win') else 'DejaVu Sans'
