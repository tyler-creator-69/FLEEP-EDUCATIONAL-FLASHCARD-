from PyQt6.QtGui import QPalette, QColor, QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication
import os


# === FLAT MINIMALIST THEMES ===
THEMES = {
    'Light': {
        'window': '#f3e9d2',   # light beige
        'text': '#2b2b2b',     # dark gray text
        'card': '#ffffff',     # white cards
        'accent': '#d6b88d'    # warm accent
    },
    'Dark': {
        'window': '#2b2b2b',   # dark gray
        'text': '#f3e9d2',     # light beige text
        'card': '#3a3a3a',     # slightly lighter gray cards
        'accent': '#a07f5a'    # muted warm tone
    }
}


def apply_theme(name):
    """Applies the minimalist color palette globally."""
    th = THEMES.get(name, THEMES['Light'])
    app = QApplication.instance()
    if not app:
        return

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(th['window']))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(th['text']))
    pal.setColor(QPalette.ColorRole.Base, QColor(th['card']))
    pal.setColor(QPalette.ColorRole.Text, QColor(th['text']))
    pal.setColor(QPalette.ColorRole.Button, QColor(th['accent']))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(th['text']))

    app.setPalette(pal)


def set_app_font(font_source, size=12):
    app = QApplication.instance()
    if not app:
        return

    # Load from file or use installed font
    if os.path.isfile(font_source):
        font_id = QFontDatabase.addApplicationFont(font_source)
        loaded_fonts = QFontDatabase.applicationFontFamilies(font_id)
        if loaded_fonts:
            font_source = loaded_fonts[0]
            print(f"✅ Loaded OpenDyslexic: {font_source}")
        else:
            print("⚠️ Failed to load font from file, fallback to Arial.")
            font_source = "Arial"

    font = QFont(font_source, size)
    app.setFont(font)
    print(f"✅ Applied font: {font_source} ({size}pt)")
