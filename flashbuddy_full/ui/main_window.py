from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QWidget, QVBoxLayout, QLabel, QListWidget,
    QPushButton, QHBoxLayout, QToolBar, QMessageBox, QInputDialog,
    QFileDialog, QComboBox, QDialog
)
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QAction, QPixmap

from ui.flashcard_widget import FlashcardWidget
from ui.add_card_dialog import AddCardDialog

from ui.theme_manager import apply_theme, set_app_font, THEMES
from core import Database
from core.settings import find_dyslexic_font, FALLBACK_FONT, IMG_DIR
from core.import_export import import_csv, export_csv
from core.spaced_repetition import review as sr_review

from ui.login_window import LoginWindow


class MainWindow(QMainWindow):

    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle('FlashBuddy')

        # === Core app data ===
        self.db = Database()
        self.user_id = user_id
        self.profile_id = self.db.create_profile_if_missing(f"user_{user_id}")

        self.current_deck = None
        self.card_ids = []
        self.index = 0
        self.show_front = True

        # === Theme + Font ===
        self.dys = find_dyslexic_font()
        self.current_theme = "Light"
        apply_theme(self.current_theme)
        self.using_dys = False

        # === SESSION TIMER ===
        self.session_time = QTime(0, 0, 0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_session_timer)
        self.timer.start(1000)  # 1 second updates

        self._build_ui()

    #
    # UI BUILDING
    #
    def _build_ui(self):

        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)

        # Core actions
        toolbar.addAction(QAction("New Deck", self, triggered=self.new_deck))
        toolbar.addAction(QAction("Add Card", self, triggered=self.add_card))
        toolbar.addAction(QAction("Import", self, triggered=self.import_deck))
        toolbar.addAction(QAction("Export", self, triggered=self.export_deck))

        # Theme dropdown
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(self.current_theme)
        self.theme_combo.currentTextChanged.connect(self.on_theme_change)
        toolbar.addWidget(self.theme_combo)

        # Dyslexic toggle
        toolbar.addAction(QAction("Toggle Dyslexic", self, triggered=self.toggle_dyslexic))

        # === LOGOUT BUTTON ===
        logout = QAction("Logout", self)
        logout.triggered.connect(self.logout)
        toolbar.addAction(logout)

        # === MAIN SPLITTER ===
        splitter = QSplitter()

        # LEFT PANEL
        left = QWidget()
        llay = QVBoxLayout()
        left.setLayout(llay)

        # PROFILE + TIMER + STATS
        prof = QWidget()
        p = QVBoxLayout()
        prof.setLayout(p)

        # USER PROFILE PICTURE
        self.profile_pic = QLabel()
        self.profile_pic.setFixedSize(120, 120)
        self.profile_pic.setStyleSheet("border: 2px solid gray; border-radius: 10px;")
        self.profile_pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_profile_picture()

        pic_btn = QPushButton("Change Photo")
        pic_btn.clicked.connect(self.change_profile_picture)

        # SESSION TIMER
        self.timer_label = QLabel("Session: 00:00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # STATS
        self.stats_label = QLabel("Stats:\nDecks: 0\nCards: 0\nReviews: 0")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        p.addWidget(self.profile_pic)
        p.addWidget(pic_btn)
        p.addWidget(self.timer_label)
        p.addWidget(self.stats_label)

        llay.addWidget(prof)

        # Deck list
        llay.addWidget(QLabel("Decks"))
        self.deck_list = QListWidget()
        self.deck_list.itemClicked.connect(self.select_deck)
        llay.addWidget(self.deck_list)
        llay.addWidget(self._deck_buttons())

        # CENTER PANEL
        center = QWidget()
        clay = QVBoxLayout()
        center.setLayout(clay)

        self.card_widget = FlashcardWidget()
        self.card_widget.setFixedHeight(360)
        self.card_widget.mousePressEvent = self.flip_card
        clay.addWidget(self.card_widget)

        clay.addLayout(self._nav_buttons())

        # RIGHT PANEL
        right = QWidget()
        rlay = QVBoxLayout()
        right.setLayout(rlay)

        rlay.addWidget(QLabel("Cards"))
        self.card_list = QListWidget()
        self.card_list.itemClicked.connect(self.edit_card)
        rlay.addWidget(self.card_list)
        rlay.addWidget(self._card_buttons())

        splitter.addWidget(left)
        splitter.addWidget(center)
        splitter.addWidget(right)

        splitter.setSizes([220, 550, 300])

        self.setCentralWidget(splitter)

        # Load decks + stats
        self.reload_decks()
        self.update_stats()


    # PROFILE PICTURE

    def load_profile_picture(self):
        path = f"{IMG_DIR}/profile_{self.user_id}.png"
        pix = QPixmap(path)
        if pix.isNull():
            self.profile_pic.setText("No Photo")
            return
        self.profile_pic.setPixmap(pix.scaled(
            120, 120,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

    def change_profile_picture(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose Profile Image", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        out = f"{IMG_DIR}/profile_{self.user_id}.png"
        QPixmap(path).save(out)
        self.load_profile_picture()


    # STATS + SESSION TIMER

    def update_session_timer(self):
        self.session_time = self.session_time.addSecs(1)
        self.timer_label.setText(f"Session: {self.session_time.toString('hh:mm:ss')}")

    def update_stats(self):
        deck_count = len(self.db.list_decks(self.profile_id))
        cards = sum(len(self.db.list_cards(d["id"])) for d in self.db.list_decks(self.profile_id))
        reviews = self.db.count_reviews(self.profile_id)

        self.stats_label.setText(
            f"Stats:\nDecks: {deck_count}\nCards: {cards}\nReviews: {reviews}"
        )


    # LOGOUT HANDLER

    def logout(self):
        self.close()
        dlg = LoginWindow()
        dlg.exec()


    # DECK BUTTONS

    def _deck_buttons(self):
        w = QWidget()
        h = QHBoxLayout()
        w.setLayout(h)

        b1 = QPushButton("New")
        b2 = QPushButton("Delete")

        b1.clicked.connect(self.new_deck)
        b2.clicked.connect(self.delete_deck)

        h.addWidget(b1)
        h.addWidget(b2)
        return w


    # CARD BUTTONS

    def _card_buttons(self):
        w = QWidget()
        h = QHBoxLayout()
        w.setLayout(h)

        b1 = QPushButton("Edit")
        b2 = QPushButton("Delete")

        b1.clicked.connect(self.edit_selected)
        b2.clicked.connect(self.delete_selected)

        h.addWidget(b1)
        h.addWidget(b2)
        return w


    # NAV BUTTONS

    def _nav_buttons(self):
        h = QHBoxLayout()
        bprev = QPushButton("Prev")
        bflip = QPushButton("Flip")
        bnext = QPushButton("Next")

        bprev.clicked.connect(self.prev_card)
        bflip.clicked.connect(self.flip_card)
        bnext.clicked.connect(self.next_card)

        h.addWidget(bprev)
        h.addWidget(bflip)
        h.addWidget(bnext)

        return h


    # DECK / CARD OPERATIONS

    def reload_decks(self):
        self.deck_list.clear()
        rows = self.db.list_decks(self.profile_id)

        for row in rows:
            self.deck_list.addItem(row["name"])

        self.update_stats()

    def new_deck(self):
        name, ok = QInputDialog.getText(self, "New deck", "Name:")
        if ok and name.strip():
            self.db.create_deck(name.strip(), self.profile_id)
            self.reload_decks()

    def delete_deck(self):
        it = self.deck_list.currentItem()
        if not it:
            return

        name = it.text()
        for row in self.db.list_decks(self.profile_id):
            if row["name"] == name:
                confirm = QMessageBox.question(self, "Delete", f"Delete {name}?")
                if confirm == QMessageBox.StandardButton.Yes:
                    self.db.delete_deck(row["id"])
                    self.reload_decks()
                return

    def select_deck(self, item):
        name = item.text()
        for row in self.db.list_decks(self.profile_id):
            if row["name"] == name:
                self.current_deck = row["id"]
                self.reload_cards()
                return

    def reload_cards(self):
        self.card_list.clear()
        rows = self.db.list_cards(self.current_deck)
        self.card_ids = [r["id"] for r in rows]

        for r in rows:
            self.card_list.addItem(r["front"])

        self.index = 0
        self.show_front = True

        self.update_stats()
        self.show_current()

    def add_card(self):
        if not self.current_deck:
            QMessageBox.warning(self, "No deck", "Select a deck")
            return

        dlg = AddCardDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            v = dlg.get_values()
            self.db.add_card(
                self.current_deck, v["front"], v["back"],
                v["notes"], v["image_path"]
            )
            self.reload_cards()

    def edit_card(self, item):
        text = item.text()
        for r in self.db.list_cards(self.current_deck):
            if r["front"] == text:
                card = self.db.get_card(r["id"])
                dlg = AddCardDialog(
                    self,
                    front=card["front"],
                    back=card["back"],
                    notes=card["notes"],
                    image_path=card["image_path"]
                )
                if dlg.exec() == QDialog.DialogCode.Accepted:
                    v = dlg.get_values()
                    self.db.update_card(
                        r["id"], v["front"], v["back"],
                        v["notes"], v["image_path"]
                    )
                    self.reload_cards()
                return

    def edit_selected(self):
        it = self.card_list.currentItem()
        if it:
            self.edit_card(it)

    def delete_selected(self):
        it = self.card_list.currentItem()
        if not it:
            return

        name = it.text()
        for r in self.db.list_cards(self.current_deck):
            if r["front"] == name:
                self.db.delete_card(r["id"])
                self.reload_cards()
                return


    # STUDY CARD UI

    def show_current(self):
        if not self.card_ids:
            self.card_widget.setText("No cards")
            return

        cid = self.card_ids[self.index]
        card = self.db.get_card(cid)

        display = card["front"] if self.show_front else card["back"]

        if card["image_path"]:
            pix = QPixmap(card["image_path"])
            if not pix.isNull():
                self.card_widget.setPixmap(pix.scaledToHeight(160))
                self.card_widget.setToolTip(display)
                return

        self.card_widget.setPixmap(QPixmap())
        self.card_widget.setText(display)

    def flip_card(self, event=None):
        if not self.card_ids:
            return

        def done():
            self.show_front = not self.show_front
            self.show_current()

        self.card_widget.flip(on_finished=done)

    def next_card(self):
        if not self.card_ids:
            return

        self.index = (self.index + 1) % len(self.card_ids)
        self.show_front = True
        self.show_current()

    def prev_card(self):
        if not self.card_ids:
            return

        self.index = (self.index - 1) % len(self.card_ids)
        self.show_front = True
        self.show_current()


    # SPACED REPETITION

    def record_review(self, quality):
        if not self.card_ids:
            return

        cid = self.card_ids[self.index]
        card = self.db.get_card(cid)
        ease, interval, reps, due = sr_review(card, quality)
        self.db.update_review(cid, ease, interval, reps, due)
        self.next_card()


    # IMPORT / EXPORT

    def import_deck(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if not path:
            return

        import_csv(path, self.db, self.profile_id)
        self.reload_decks()

    def export_deck(self):
        if not self.current_deck:
            QMessageBox.warning(self, "No deck", "Select a deck")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if not path:
            return

        export_csv(self.current_deck, self.db, path)


    # THEME + FONT

    def on_theme_change(self, name):
        self.current_theme = name
        apply_theme(name)

    def toggle_dyslexic(self):
        if not self.dys:
            QMessageBox.information(self, "Not found", "Install OpenDyslexic to enable this option")
            return

        if self.using_dys:
            set_app_font(FALLBACK_FONT, 12)
            self.using_dys = False
        else:
            set_app_font(self.dys, 12)
            self.using_dys = True
