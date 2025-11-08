# ui/theme_manager.py
from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Developer themes (edit colors here)
THEMES = {
    'Light': {
        'window': '#f6f8ff',
        'text': '#111827',
        'card_start': '#ffffff',
        'card_end': '#f2f6ff'
    },
    'Dark': {
        'window': '#121212',
        'text': '#e6eef8',
        'card_start': '#1e1e1e',
        'card_end': '#2a2a2a'
    },
    'Solarized': {
        'window': '#fdf6e3',
        'text': '#657b83',
        'card_start': '#eee8d5',
        'card_end': '#f5f1e0'
    }
}

def _qcolor(hex_or_qcolor):
    if isinstance(hex_or_qcolor, QColor):
        return hex_or_qcolor
    return QColor(hex_or_qcolor)

def apply_theme(name: str):
    """
    Robust palette application: sets many QPalette roles and forces a style
    that respects palettes. Also clears global stylesheet so palette is visible.
    """
    app = QApplication.instance()
    if app is None:
        return

    # Prefer a palette-respecting style
    try:
        app.setStyle("Fusion")
    except Exception:
        pass

    theme = THEMES.get(name, THEMES['Light'])
    window = _qcolor(theme['window'])
    text = _qcolor(theme['text'])
    base = _qcolor(theme['card_start'])
    alternate = _qcolor(theme['card_end'])

    pal = QPalette()

    # Base/background & text
    pal.setColor(QPalette.ColorRole.Window, window)              # main window background
    pal.setColor(QPalette.ColorRole.WindowText, text)            # window text
    pal.setColor(QPalette.ColorRole.Base, base)                  # e.g., QLineEdit background
    pal.setColor(QPalette.ColorRole.AlternateBase, alternate)    # alternate row backgrounds
    pal.setColor(QPalette.ColorRole.Text, text)                  # default text
    pal.setColor(QPalette.ColorRole.PlaceholderText, text.lighter(150))

    # Buttons
    pal.setColor(QPalette.ColorRole.Button, base)
    pal.setColor(QPalette.ColorRole.ButtonText, text)

    # Links / highlights
    if name.lower().startswith('dark'):
        highlight = QColor('#4a90e2')
    elif name.lower().startswith('solar'):
        highlight = QColor('#268bd2')
    else:
        highlight = QColor('#3b6edc')
    pal.setColor(QPalette.ColorRole.Highlight, highlight)
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor('#ffffff'))

    # Tooltips
    pal.setColor(QPalette.ColorRole.ToolTipBase, base)
    pal.setColor(QPalette.ColorRole.ToolTipText, text)

    # Shadows and mid colors
    pal.setColor(QPalette.ColorRole.Dark, base.darker(120))
    pal.setColor(QPalette.ColorRole.Mid, base.darker(110))
    pal.setColor(QPalette.ColorRole.Midlight, base.lighter(110))
    pal.setColor(QPalette.ColorRole.Light, base.lighter(140))

    # Disabled state (slightly faded)
    disabled_text = text.darker(130)
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text)
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_text)

    # Ensure brighttext for emergency contrast
    pal.setColor(QPalette.ColorRole.BrightText, QColor('#ffffff'))

    # Apply palette and clear stylesheet so palette wins
    app.setPalette(pal)
    # Clear global stylesheet that may hard-code colors (this allows palette to show)
    app.setStyleSheet("")


def set_app_font(family, size=12):
    QApplication.instance().setFont(QFont(family, size))
