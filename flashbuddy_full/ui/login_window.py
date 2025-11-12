from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QMessageBox,
    QToolButton, QMenu, QGraphicsOpacityEffect
)
from PyQt6.QtGui import QIcon, QPixmap, QAction, QPalette, QColor
from PyQt6.QtCore import Qt
from core import Database
from core.user_auth import Auth
from ui.theme_manager import apply_theme, set_app_font
from core.settings import find_dyslexic_font, FALLBACK_FONT


class LoginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Window sizing
        self.setMinimumSize(600, 420)
        self.setFixedSize(650, 450)
        self.setWindowTitle("FlashBuddy — Login")

        # Core objects
        self.db = Database()
        self.auth = Auth(self.db)
        self.user_id = None
        self.dys = find_dyslexic_font()
        self.theme = "Light"
        self.using_dys = False

        # Build UI and apply theme
        self._build_ui()
        apply_theme(self.theme)

    def _build_ui(self):
        # Layout setup
        layout = QVBoxLayout()
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(18)

        # === Background color (matching logo tone) ===
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#f3e9d2"))  # warm beige
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        # === Logo ===
        self.logo = QLabel()
        pix = QPixmap("FLEEP.png")  # <-- your logo file
        if pix.isNull():
            pix = QPixmap("76894f4f-5988-41f5-85e0-4dd25ad34fe3.png")  # fallback

        # Make logo larger (280x180)
        self.logo.setPixmap(
            pix.scaled(280, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.logo)

        # === Username and Password Fields ===
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.user_input)
        layout.addWidget(self.pass_input)

        # === Buttons layout ===
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(14)

        self.login_btn = QPushButton("Login")
        self.reg_btn = QPushButton("Register")
        self.login_btn.clicked.connect(self._try_login)
        self.reg_btn.clicked.connect(self._try_register)

        btn_layout.addWidget(self.login_btn)
        btn_layout.addWidget(self.reg_btn)
        layout.addLayout(btn_layout)

        # Apply layout
        self.setLayout(layout)

        # === Style ===
        self.setStyleSheet("""
        QDialog {
            background-color: #f3e9d2;
        }
        QLabel {
            color: #3b2f1e;
        }
        QLineEdit {
            padding: 8px;
            border-radius: 6px;
            border: 1px solid #cbbf9d;
            background: #fffaf0;
            color: #3b2f1e;
            font-size: 14px;
        }
        QPushButton {
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 14px;
            border: 1px solid #d6c4a2;
            background-color: #d6b88d;
            color: #3b2f1e;
        }
        QPushButton:hover {
            background-color: #c8a97f;
        }
        """)

    # ========== SETTINGS MENU ==========
    def _open_settings_menu(self):
        menu = QMenu(self)

        # Toggle Dark/Light
        theme_action = QAction("Toggle Dark/Light Mode", self)
        theme_action.triggered.connect(self._toggle_theme)
        menu.addAction(theme_action)

        # Toggle Dyslexic Font
        dys_action = QAction("Toggle Dyslexic Font", self)
        dys_action.triggered.connect(self._toggle_dyslexic)
        menu.addAction(dys_action)

        menu.exec(self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomLeft()))

    # ========== Authentication handlers ==========
    def _try_login(self):
        u = self.user_input.text().strip()
        p = self.pass_input.text()
        if not u or not p:
            QMessageBox.warning(self, "Missing", "Enter username and password")
            return
        uid = self.auth.verify_user(u, p)
        if uid:
            self.user_id = uid
            self.accept()
        else:
            QMessageBox.warning(self, "Failed", "Invalid credentials")

    def _try_register(self):
        u = self.user_input.text().strip()
        p = self.pass_input.text()
        if not u or not p:
            QMessageBox.warning(self, "Missing", "Enter username and password")
            return
        try:
            self.auth.create_user(u, p)
            QMessageBox.information(self, "Created", "User created — you can now log in")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not create user: {e}")

    # ========== Theme / Dyslexic toggles ==========
    def _toggle_theme(self):
        self.theme = "Dark" if self.theme == "Light" else "Light"
        apply_theme(self.theme)

    def _toggle_dyslexic(self):
        if not self.dys:
            QMessageBox.information(self, "Not found", "Install OpenDyslexic to enable this option")
            return
        if self.using_dys:
            set_app_font(FALLBACK_FONT, 12)
            self.using_dys = False
        else:
            set_app_font(self.dys, 12)
            self.using_dys = True
