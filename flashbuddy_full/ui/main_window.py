# ui/main_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QFileDialog, QMessageBox, QInputDialog, QDialog
)
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QPixmap
import os

from ui.widgets.toggle_switch import ToggleSwitch
from ui.theme_manager import apply_theme, set_app_font
from core.settings import find_dyslexic_font, FALLBACK_FONT, IMG_DIR
from ui.login_window import LoginWindow
from core.database import Database
from ui.flashcard_widget import FlashcardWidget
from ui.add_card_dialog import AddCardDialog


class MainWindow(QMainWindow):
    def __init__(self, user_id=None):
        super().__init__()
        self.user_id = user_id
        self.theme = "Light"
        self.using_dys = False

        # data / selection state
        self.current_deck_id = None
        self.current_card_index = 0
        self.cards = []  # list of sqlite3.Row for current deck

        # DB
        self.db = Database()
        self.profile_id = self.db.create_profile_if_missing(f"user_{self.user_id}")

        # timer
        self.session_time = QTime(0, 0, 0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_session_timer)
        self.timer.start(1000)

        # fonts
        self.dys = find_dyslexic_font()

        # window
        self.setWindowTitle("FlashBuddy")
        self.setMinimumSize(1100, 650)

        self._build_ui()
        # ensure theme switch connection works with either signal name
        ts = getattr(self, "theme_switch", None)
        if ts is not None:
            if hasattr(ts, "toggle_signal"):
                ts.toggle_signal.connect(self.on_theme_toggled)
            elif hasattr(ts, "toggled"):
                try:
                    ts.toggled.connect(self.on_theme_toggled)
                except Exception:
                    pass

        self.on_theme_toggled(False)
        self.load_profile_picture()
        self.reload_decks()

    # ---------------- UI ----------------
    def _build_ui(self):
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        # top bar
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_bar.setFixedHeight(46)
        bar_layout = QHBoxLayout(top_bar)
        bar_layout.setContentsMargins(12, 6, 12, 6)
        bar_layout.setSpacing(10)

        # deck controls in top bar
        self.btn_add_deck = QPushButton("➕ Add Deck")
        self.btn_delete_deck = QPushButton("🗑 Delete Deck")
        self.btn_import = QPushButton("Import")
        self.btn_export = QPushButton("Export")
        self.btn_dys = QPushButton("Toggle Dyslexic")
        self.btn_logout = QPushButton("Logout")

        for b in (self.btn_add_deck, self.btn_delete_deck, self.btn_import,
                  self.btn_export, self.btn_dys, self.btn_logout):
            b.setFixedHeight(32)
            b.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_add_deck.clicked.connect(self.add_deck)
        self.btn_delete_deck.clicked.connect(self.delete_deck)
        self.btn_import.clicked.connect(self.import_deck)
        self.btn_export.clicked.connect(self.export_deck)
        self.btn_dys.clicked.connect(self.toggle_dyslexic)
        self.btn_logout.clicked.connect(self.logout)

        bar_layout.addWidget(self.btn_add_deck)
        bar_layout.addWidget(self.btn_delete_deck)
        bar_layout.addWidget(self.btn_import)
        bar_layout.addWidget(self.btn_export)
        bar_layout.addWidget(self.btn_dys)
        bar_layout.addStretch(1)

        # theme toggle widget (some versions emit toggle_signal, others toggled)
        self.theme_switch = ToggleSwitch(self, checked=False)
        # We connect signals after building UI in __init__ to handle both names.

        bar_layout.addWidget(self.theme_switch)
        bar_layout.addWidget(self.btn_logout)

        # body
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # left panel - profile + decks
        left = QFrame()
        left.setObjectName("LeftPanel")
        left.setFixedWidth(260)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(16, 16, 16, 16)
        ll.setSpacing(12)

        self.profile_pic = QLabel()
        self.profile_pic.setObjectName("PhotoLabel")
        self.profile_pic.setFixedSize(120, 120)
        self.profile_pic.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.change_photo_btn = QPushButton("Change Photo")
        self.change_photo_btn.setFixedWidth(140)
        self.change_photo_btn.clicked.connect(self.change_profile_picture)

        self.timer_label = QLabel("Session: 00:00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stats_label = QLabel("Stats:\nDecks: 0\nCards: 0\nReviews: 0")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ll.addWidget(self.profile_pic, 0, Qt.AlignmentFlag.AlignHCenter)
        ll.addWidget(self.change_photo_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        ll.addWidget(self.timer_label)
        ll.addWidget(self.stats_label)
        ll.addSpacing(6)
        ll.addWidget(QLabel("Decks"))
        self.deck_list = QListWidget()
        self.deck_list.itemClicked.connect(self.on_deck_clicked)
        ll.addWidget(self.deck_list, 1)

        # center panel - flashcard display
        center = QFrame()
        center.setObjectName("CenterPanel")
        cl = QVBoxLayout(center)
        cl.setContentsMargins(24, 24, 24, 24)
        cl.setSpacing(18)

        self.add_card_btn = QPushButton("+ Add Card")
        self.add_card_btn.setFixedSize(150, 40)
        self.add_card_btn.clicked.connect(self.add_card)
        cl.addWidget(self.add_card_btn, alignment=Qt.AlignmentFlag.AlignRight)

        # your flashcard widget (QLabel subclass with flip)
        self.card_widget = FlashcardWidget()
        self.card_widget.setFixedHeight(320)
        # clicking the widget flips
        try:
            self.card_widget.mousePressEvent = self._card_mousepress
        except Exception:
            pass
        cl.addWidget(self.card_widget)

        nav = QHBoxLayout()
        self.prev_btn = QPushButton("Prev"); self.prev_btn.setFixedSize(140, 40)
        self.flip_btn = QPushButton("Flip"); self.flip_btn.setFixedSize(140, 40)
        self.next_btn = QPushButton("Next"); self.next_btn.setFixedSize(140, 40)
        self.prev_btn.clicked.connect(self.prev_card)
        self.flip_btn.clicked.connect(self.flip_card)
        self.next_btn.clicked.connect(self.next_card)
        nav.addStretch(1)
        nav.addWidget(self.prev_btn)
        nav.addSpacing(20)
        nav.addWidget(self.flip_btn)
        nav.addSpacing(20)
        nav.addWidget(self.next_btn)
        nav.addStretch(1)
        cl.addLayout(nav)

        # right panel - card list + stats
        right = QFrame()
        right.setObjectName("RightPanel")
        right.setFixedWidth(280)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(12, 12, 12, 12)
        rl.setSpacing(8)

        rl.addWidget(QLabel("Cards"))
        self.card_list = QListWidget()
        self.card_list.itemClicked.connect(self.on_card_clicked)
        rl.addWidget(self.card_list, 1)

        # more stats labels (kept for compatibility)
        self.label_decks = QLabel("Decks: 0")
        self.label_cards = QLabel("Cards: 0")
        self.label_reviews = QLabel("Reviews: 0")
        self.label_mastered = QLabel("Mastered: 0")
        self.label_ease = QLabel("Avg Ease: 0.0")
        for lbl in (self.label_decks, self.label_cards, self.label_reviews, self.label_mastered, self.label_ease):
            rl.addWidget(lbl)

        # assemble
        body.addWidget(left)
        body.addWidget(center, 1)
        body.addWidget(right)
        root_layout.addWidget(top_bar)
        root_layout.addLayout(body)

        # apply base stylesheet
        self.setStyleSheet(self._app_stylesheet())

    # ---------------- stylesheet ----------------
    def _app_stylesheet(self):
        return """
        QMainWindow { background-color: #f3e9d2; color: #3b2f1e; }
        QFrame#TopBar { background-color: #d6b88d; border-bottom: 1px solid #bfa378; }
        QFrame#LeftPanel { background-color: #e8ddc3; border-right: 1px solid #c7b58a; }
        QFrame#CenterPanel { background-color: #f3e9d2; }
        QFrame#RightPanel { background-color: #f7f2e6; border-left: 1px solid #c7b58a; }
        QLabel { color: #3b2f1e; }
        QPushButton { background-color: #d6b88d; color: #3b2f1e; border-radius: 10px; padding: 6px 10px; border: none; }
        QPushButton:hover { background-color: #c8a97f; }
        QLabel#PhotoLabel { background-color: #f7f1e1; border: 2px solid #cbbf9d; border-radius: 12px; }
        QListWidget { background-color: #f9f5ea; border: 1px solid #d6caa7; border-radius: 6px; }
        """

    # ---------------- deck/card loading ----------------
    def reload_decks(self):
        self.deck_list.clear()
        try:
            decks = self.db.list_decks(self.profile_id)
            for d in decks:
                item = QListWidgetItem(d["name"])
                item.setData(Qt.ItemDataRole.UserRole, d["id"])
                self.deck_list.addItem(item)
        except Exception as e:
            print("reload_decks error:", e)
        self.update_stats()

    def on_deck_clicked(self, item):
        deck_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_deck_id = deck_id
        self.load_cards(deck_id)

    def load_cards(self, deck_id):
        self.card_list.clear()
        self.cards = list(self.db.list_cards(deck_id))  # list of rows with id and front
        # store full card objects in memory? we get details on show_current_card
        for r in self.cards:
            it = QListWidgetItem(r["front"])
            it.setData(Qt.ItemDataRole.UserRole, r["id"])
            self.card_list.addItem(it)

        if self.cards:
            self.current_card_index = 0
            self.show_current_card()
        else:
            # clear widget (use QLabel API)
            self.card_widget.setPixmap(QPixmap())
            self.card_widget.setText("No cards")
        self.update_stats()

    def on_card_clicked(self, item):
        card_id = item.data(Qt.ItemDataRole.UserRole)
        # find index in self.cards
        for i, r in enumerate(self.cards):
            if r["id"] == card_id:
                self.current_card_index = i
                self.show_current_card()
                return

    def show_current_card(self):
        if not self.cards:
            return
        try:
            card_meta = self.cards[self.current_card_index]
            card = self.db.get_card(card_meta["id"])  # this returns a sqlite3.Row
            if not card:
                self.card_widget.setText("Card not found")
                return

            # Determine display
            display_text = card["front"] if getattr(self, "show_front", True) else card["back"]
            img_path = card["image_path"] if "image_path" in card.keys() else None

            # If there's an image path and file exists, show pixmap
            if img_path and img_path.strip():
                # if relative path, allow as-is; check existence
                if os.path.exists(img_path):
                    pix = QPixmap(img_path)
                else:
                    # maybe stored as just filename in IMG_DIR
                    alt = os.path.join(IMG_DIR, img_path)
                    pix = QPixmap(alt) if os.path.exists(alt) else QPixmap()

                if not pix.isNull():
                    # show image when front; if showing back, still show image but overlay text via tooltip/text
                    self.card_widget.setPixmap(pix.scaledToHeight(240, Qt.TransformationMode.SmoothTransformation))
                    if getattr(self, "show_front", True):
                        self.card_widget.setText("")  # clear any overlay text
                    else:
                        # show back text in the label (QLabel can show text over pixmap if styled; we'll set text)
                        # shorter approach: set tooltip and text (text will be shown if pixmap smaller)
                        self.card_widget.setText(display_text)
                        self.card_widget.setToolTip(display_text)
                    return

            # fallback: plain text
            self.card_widget.setPixmap(QPixmap())
            self.card_widget.setText(display_text)
        except Exception as e:
            print("show_current_card error:", e)
            self.card_widget.setText("Error showing card")

    # ---------------- card navigation ----------------
    def flip_card(self):
        # flip animation provided by FlashcardWidget
        def finished():
            # toggle show_front flag and re-render
            self.show_front = not getattr(self, "show_front", True)
            self.show_current_card()

        try:
            self.card_widget.flip(on_finished=finished)
        except Exception:
            # fallback
            finished()

    def next_card(self):
        if not self.cards:
            return
        self.current_card_index = (self.current_card_index + 1) % len(self.cards)
        self.show_front = True
        self.show_current_card()

    def prev_card(self):
        if not self.cards:
            return
        self.current_card_index = (self.current_card_index - 1) % len(self.cards)
        self.show_front = True
        self.show_current_card()

    def _card_mousepress(self, event):
        self.flip_card()

    # ---------------- add / edit / delete ----------------
    def add_card(self):
        if not self.current_deck_id:
            QMessageBox.warning(self, "No deck", "Select a deck first")
            return
        dlg = AddCardDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            vals = dlg.get_values()
            self.db.add_card(self.current_deck_id, vals["front"], vals["back"], vals["notes"], vals["image_path"])
            self.load_cards(self.current_deck_id)

    def add_deck(self):
        name, ok = QInputDialog.getText(self, "Add deck", "Deck name:")
        if ok and name.strip():
            self.db.create_deck(name.strip(), self.profile_id)
            self.reload_decks()

    def delete_deck(self):
        it = self.deck_list.currentItem()
        if not it:
            QMessageBox.information(self, "No deck", "Select a deck to delete")
            return
        name = it.text()
        for d in self.db.list_decks(self.profile_id):
            if d["name"] == name:
                confirm = QMessageBox.question(self, "Delete", f"Delete deck '{name}'?")
                if confirm == QMessageBox.StandardButton.Yes:
                    self.db.delete_deck(d["id"])
                    self.current_deck_id = None
                    self.reload_decks()
                return

    # ---------------- import/export placeholders ----------------
    def import_deck(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        # If you have import_csv helper, use it; otherwise placeholder
        try:
            from core.import_export import import_csv
            import_csv(path, self.db, self.profile_id)
            QMessageBox.information(self, "Import", "Import successful")
            self.reload_decks()
        except Exception as e:
            QMessageBox.warning(self, "Import failed", str(e))

    def export_deck(self):
        if not self.current_deck_id:
            QMessageBox.warning(self, "No deck", "Select a deck to export")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            from core.import_export import export_csv
            export_csv(self.current_deck_id, self.db, path)
            QMessageBox.information(self, "Export", "Export successful")
        except Exception as e:
            QMessageBox.warning(self, "Export failed", str(e))

    # ---------------- profile / timer / stats ----------------
    def load_profile_picture(self):
        os.makedirs(IMG_DIR, exist_ok=True)
        path = os.path.join(IMG_DIR, f"profile_{self.user_id}.png")
        pix = QPixmap(path)
        if pix.isNull():
            self.profile_pic.setText("No Photo")
        else:
            self.profile_pic.setPixmap(pix.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                                  Qt.TransformationMode.SmoothTransformation))

    def change_profile_picture(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose Profile Image", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        out = os.path.join(IMG_DIR, f"profile_{self.user_id}.png")
        QPixmap(path).save(out)
        self.load_profile_picture()

    def update_session_timer(self):
        self.session_time = self.session_time.addSecs(1)
        self.timer_label.setText(self.session_time.toString("hh:mm:ss"))

    def update_stats(self):
        try:
            deck_count = len(self.db.list_decks(self.profile_id))
            card_count = sum(len(self.db.list_cards(d["id"])) for d in self.db.list_decks(self.profile_id))
            reviews = self.db.count_reviews(self.profile_id)
            avg_ease = self.db.get_average_ease(self.profile_id)
            mastered = self.db.count_mastered_cards(self.profile_id)
            self.stats_label.setText(f"Stats:\nDecks: {deck_count}\nCards: {card_count}\nReviews: {reviews}")
            self.label_decks.setText(f"Decks: {deck_count}")
            self.label_cards.setText(f"Cards: {card_count}")
            self.label_reviews.setText(f"Reviews: {reviews}")
            self.label_mastered.setText(f"Mastered: {mastered}")
            self.label_ease.setText(f"Avg Ease: {avg_ease:.2f}")
        except Exception as e:
            print("update_stats error:", e)

    # ---------------- theme / dyslexic / logout ----------------
    def toggle_dyslexic(self):
        """Toggle the global font between OpenDyslexic and default."""
        if not self.dys:
            QMessageBox.warning(self, "Font Missing", "OpenDyslexic font not found.")
            return

        self.using_dys = not self.using_dys

        if self.using_dys:
            set_app_font(self.dys, 11)
            print("✅ Switched to OpenDyslexic font.")
        else:
            set_app_font("Arial", 11)
            print("✅ Switched to default system font.")

    def on_theme_toggled(self, is_dark):
        """Switch between light and dark mode with font integration."""
        font_name = self.dys if self.using_dys else "Arial"

        if is_dark:
            self.theme = "Dark"
            stylesheet = f"""
                QMainWindow {{
                    background-color: #2b2b2b;
                    color: #e6e6e6;
                    font-family: '{font_name}';
                }}
                QFrame#TopBar {{
                    background-color: #3c3c3c;
                    border-bottom: 1px solid #555;
                }}
                QFrame#LeftPanel {{
                    background-color: #3a3a3a;
                    border-right: 1px solid #444;
                }}
                QFrame#CenterPanel {{
                    background-color: #2b2b2b;
                }}
                QFrame#RightPanel {{
                    background-color: #333;
                    border-left: 1px solid #444;
                }}
                QLabel, QListWidget {{
                    color: #f2f2f2;
                    font-family: '{font_name}';
                }}
                QPushButton {{
                    background-color: #4a4a4a;
                    color: #f0f0f0;
                    border-radius: 8px;
                    padding: 6px 10px;
                    font-family: '{font_name}';
                }}
                QListWidget {{
                    background-color: #2f2f2f;
                    border: 1px solid #444;
                    border-radius: 6px;
                }}
                QLabel#PhotoLabel {{
                    background-color: #444;
                    border: 2px solid #666;
                    border-radius: 12px;
                }}
            """
        else:
            self.theme = "Light"
            stylesheet = f"""
                QMainWindow {{
                    background-color: #f3e9d2;
                    color: #3b2f1e;
                    font-family: '{font_name}';
                }}
                QFrame#TopBar {{
                    background-color: #d6b88d;
                    border-bottom: 1px solid #bfa378;
                }}
                QFrame#LeftPanel {{
                    background-color: #e8ddc3;
                    border-right: 1px solid #c7b58a;
                }}
                QFrame#CenterPanel {{
                    background-color: #f3e9d2;
                }}
                QFrame#RightPanel {{
                    background-color: #f7f2e6;
                    border-left: 1px solid #c7b58a;
                }}
                QLabel, QListWidget {{
                    color: #3b2f1e;
                    font-family: '{font_name}';
                }}
                QPushButton {{
                    background-color: #d6b88d;
                    color: #3b2f1e;
                    border-radius: 8px;
                    padding: 6px 10px;
                    border: none;
                    font-family: '{font_name}';
                }}
                QPushButton:hover {{
                    background-color: #c8a97f;
                }}
                QLabel#PhotoLabel {{
                    background-color: #f7f1e1;
                    border: 2px solid #cbbf9d;
                    border-radius: 12px;
                }}
                QListWidget {{
                    background-color: #f9f5ea;
                    border: 1px solid #d6caa7;
                    border-radius: 6px;
                }}
            """

        self.setStyleSheet(stylesheet)
        apply_theme(self.theme)

    def logout(self):
        self.close()
        dlg = LoginWindow()
        dlg.exec()
