# flashcard_app.py
import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QSplitter, QWidget, QToolBar,
    QInputDialog, QMessageBox, QDialog
)
from PyQt6.QtGui import QFont, QColor, QPalette, QFontDatabase, QPixmap,QAction
from PyQt6.QtCore import Qt, QPropertyAnimation
from database import init_db
from dialogs import CardDialog
from utils import now_iso, copy_image_to_storage

class FlashcardApp(QMainWindow):
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

    def __init__(self):
        super().__init__()
        self.setWindowTitle('FlashBuddy — Educational Flashcards')
        self.resize(1100, 700)
        self.conn = conn
        self.profile_id = self._ensure_profile()
        self.current_deck_id = None
        self.current_card_ids = []
        self.current_index = 0
        self.show_front = True

        # Appearance
        self.font_size = 22
        self.use_dyslexic = False
        self.current_theme = 'Light'
        self._load_fonts()

        self._build_toolbar()
        self._build_main()
        self._load_decks()
        self.apply_theme(self.current_theme)

    def _ensure_profile(self):
        cur = self.conn.cursor()
        cur.execute('SELECT id FROM profiles LIMIT 1')
        r = cur.fetchone()
        if r:
            return r[0]
        cur.execute('INSERT INTO profiles (name, created_at) VALUES (?, ?)', ('default', now_iso()))
        self.conn.commit()
        return cur.lastrowid

    def _load_fonts(self):
        # Detect available font families
        self.available_fonts = QFontDatabase().families()
        self.dyslexic_family = None
        for f in self.available_fonts:
            if 'OpenDyslexic' in f or 'OpenDyslexic3' in f:
                self.dyslexic_family = f
                break
        self.fallback_family = 'Segoe UI' if sys.platform.startswith('win') else 'DejaVu Sans'

    def _build_toolbar(self):
        toolbar = QToolBar('Main');
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        btn_new_deck = QAction('New Deck', self);
        btn_new_deck.triggered.connect(self.create_deck_dialog)
        btn_add_card = QAction('Add Card', self);
        btn_add_card.triggered.connect(self.add_card_dialog)
        btn_import = QAction('Import', self);
        btn_import.triggered.connect(self.import_deck)
        btn_export = QAction('Export', self);
        btn_export.triggered.connect(self.export_deck)
        btn_theme = QAction('Change Theme', self);
        btn_theme.triggered.connect(self.choose_theme)
        btn_dys = QAction('Toggle Dyslexic Font', self);
        btn_dys.triggered.connect(self.toggle_dyslexia)

        toolbar.addAction(btn_new_deck);
        toolbar.addAction(btn_add_card)
        toolbar.addSeparator();
        toolbar.addAction(btn_import);
        toolbar.addAction(btn_export)
        toolbar.addSeparator();
        toolbar.addAction(btn_theme);
        toolbar.addAction(btn_dys)

    def _build_main(self):
        splitter = QSplitter()
        # Left: Deck list
        left = QWidget();
        llay = QVBoxLayout();
        left.setLayout(llay)
        self.deck_list = QListWidget();
        self.deck_list.itemClicked.connect(self.on_deck_selected)
        llay.addWidget(QLabel('Decks'))
        llay.addWidget(self.deck_list)
        llay.addWidget(self._make_deck_buttons())

        # Center: card display
        center = QWidget();
        clay = QVBoxLayout();
        center.setLayout(clay)
        self.card_frame = QLabel('Select a deck to begin')
        self.card_frame.setAlignment(Qt.AlignmentFlag.AlignCenter);
        self.card_frame.setWordWrap(True)
        self.card_frame.setFixedHeight(360);
        self.card_frame.setStyleSheet(self.card_stylesheet())
        self.card_frame.mousePressEvent = self.flip_card
        clay.addWidget(self.card_frame)

        nav = QHBoxLayout()
        btn_prev = QPushButton('◀ Prev');
        btn_prev.clicked.connect(self.prev_card)
        btn_flip = QPushButton('Flip');
        btn_flip.clicked.connect(self.flip_card)
        btn_next = QPushButton('Next ▶');
        btn_next.clicked.connect(self.next_card)
        nav.addWidget(btn_prev);
        nav.addWidget(btn_flip);
        nav.addWidget(btn_next)
        clay.addLayout(nav)

        assess = QHBoxLayout()
        for label, q in [('Again', 0), ('Hard', 3), ('Good', 4), ('Easy', 5)]:
            b = QPushButton(label);
            b.clicked.connect(lambda _, s=q: self.record_assessment(s))
            assess.addWidget(b)
        clay.addLayout(assess)

        # Right: card list / editor controls
        right = QWidget();
        rlay = QVBoxLayout();
        right.setLayout(rlay)
        rlay.addWidget(QLabel('Cards'))
        self.card_list_widget = QListWidget();
        self.card_list_widget.itemClicked.connect(self.edit_card_from_list)
        rlay.addWidget(self.card_list_widget)
        rlay.addWidget(self._make_card_controls())

        splitter.addWidget(left);
        splitter.addWidget(center);
        splitter.addWidget(right)
        splitter.setSizes([200, 600, 300])
        self.setCentralWidget(splitter)

    def card_stylesheet(self):
        th = self.THEMES.get(self.current_theme, self.THEMES['Light'])
        return (
                'QLabel { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 %s, stop:1 %s);'
                ' border-radius: 14px; padding: 20px; font-size: %dpt; color: %s }' % (
                th['card_start'], th['card_end'], self.font_size, th['text'])
        )

    def _make_deck_buttons(self):
        w = QWidget();
        h = QHBoxLayout();
        w.setLayout(h)
        b1 = QPushButton('New');
        b1.clicked.connect(self.create_deck_dialog)
        b2 = QPushButton('Delete');
        b2.clicked.connect(self.delete_selected_deck)
        h.addWidget(b1);
        h.addWidget(b2)
        return w

    def _make_card_controls(self):
        w = QWidget();
        h = QHBoxLayout();
        w.setLayout(h)
        btn_edit = QPushButton('Edit Selected');
        btn_edit.clicked.connect(self.edit_selected_card)
        btn_delete = QPushButton('Delete Selected');
        btn_delete.clicked.connect(self.delete_selected_card)
        h.addWidget(btn_edit);
        h.addWidget(btn_delete)
        return w

    # --- Deck & Card operations ---
    def _load_decks(self):
        self.deck_list.clear();
        cur = self.conn.cursor();
        cur.execute('SELECT id, name FROM decks WHERE profile_id=?', (self.profile_id,))
        for id_, name in cur.fetchall(): self.deck_list.addItem(name)
        # create a sample deck if none
        cur.execute('SELECT COUNT(*) FROM decks WHERE profile_id=?', (self.profile_id,))
        if cur.fetchone()[0] == 0:
            self.create_deck('Sample Deck')

    def create_deck_dialog(self):
        name, ok = QInputDialog.getText(self, 'New Deck', 'Deck name:')
        if ok and name.strip():
            self.create_deck(name.strip())

    def create_deck(self, name):
        cur = self.conn.cursor();
        cur.execute('INSERT INTO decks (name, profile_id, created_at) VALUES (?, ?, ?)',
                    (name, self.profile_id, now_iso()))
        self.conn.commit();
        self._load_decks()

    def delete_selected_deck(self):
        item = self.deck_list.currentItem()
        if not item: return
        name = item.text();
        cur = self.conn.cursor();
        cur.execute('SELECT id FROM decks WHERE name=? AND profile_id=?', (name, self.profile_id))
        r = cur.fetchone();
        if not r: return
        deck_id = r[0]
        confirm = QMessageBox.question(self, 'Delete deck', f'Delete deck "{name}" and all its cards?')
        if confirm == QMessageBox.StandardButton.Yes:
            cur.execute('DELETE FROM cards WHERE deck_id=?', (deck_id,));
            cur.execute('DELETE FROM decks WHERE id=?', (deck_id,));
            self.conn.commit();
            self._load_decks()

    def on_deck_selected(self, item):
        name = item.text();
        cur = self.conn.cursor();
        cur.execute('SELECT id FROM decks WHERE name=? AND profile_id=?', (name, self.profile_id))
        r = cur.fetchone();
        if not r: return
        self.current_deck_id = r[0];
        self.load_cards()

    def load_cards(self):
        self.card_list_widget.clear();
        cur = self.conn.cursor();
        cur.execute('SELECT id, front FROM cards WHERE deck_id=?', (self.current_deck_id,))
        rows = cur.fetchall();
        self.current_card_ids = [r[0] for r in rows]
        for _, f in rows: self.card_list_widget.addItem(f)
        self.current_index = 0;
        self.show_front = True;
        self.update_card_display()

    def add_card_dialog(self):
        if not self.current_deck_id:
            QMessageBox.warning(self, 'No deck', 'Please select or create a deck first')
            return
        d = CardDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            vals = d.get_values()
            cur = self.conn.cursor();
            cur.execute(
                'INSERT INTO cards (deck_id, front, back, notes, image_path, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (self.current_deck_id, vals['front'], vals['back'], vals['notes'], vals['image_path'], now_iso()))
            self.conn.commit();
            self.load_cards()

    def edit_card_from_list(self, item):
        text = item.text();
        cur = self.conn.cursor();
        cur.execute('SELECT id, front, back, notes, image_path FROM cards WHERE front=? AND deck_id=?',
                    (text, self.current_deck_id))
        r = cur.fetchone();
        if not r: return
        cid, front, back, notes, img = r
        d = CardDialog(self, front=front, back=back, notes=notes, image_path=img)
        if d.exec() == QDialog.DialogCode.Accepted:
            vals = d.get_values();
            cur.execute('UPDATE cards SET front=?, back=?, notes=?, image_path=? WHERE id=?',
                        (vals['front'], vals['back'], vals['notes'], vals['image_path'], cid))
            self.conn.commit();
            self.load_cards()

    def edit_selected_card(self):
        sel = self.card_list_widget.currentItem()
        if sel: self.edit_card_from_list(sel)

    def delete_selected_card(self):
        sel = self.card_list_widget.currentItem()
        if not sel: return
        cur = self.conn.cursor();
        cur.execute('DELETE FROM cards WHERE front=? AND deck_id=?', (sel.text(), self.current_deck_id))
        self.conn.commit();
        self.load_cards()

    # --- Study UI ---
    def update_card_display(self):
        if not self.current_card_ids:
            self.card_frame.setText('No cards in this deck — add some!');
            return
        cid = self.current_card_ids[self.current_index]
        cur = self.conn.cursor();
        cur.execute('SELECT front, back, image_path FROM cards WHERE id=?', (cid,))
        f, b, img = cur.fetchone()
        display = f if self.show_front else b
        # If there's an image, display image above text using HTML
        if img:
            pix = QPixmap(img)
            if not pix.isNull():
                scaled = pix.scaledToHeight(160, Qt.TransformationMode.SmoothTransformation)
                # We show the pixmap and text together by setting the pixmap and tooltip with the text
                self.card_frame.setPixmap(scaled)
                self.card_frame.setToolTip(display)
                # also show the text below the image
                self.card_frame.setText('' + display)
                return
        self.card_frame.setPixmap(QPixmap())
        self.card_frame.setText(display)

    def animate_flip(self):
        anim = QPropertyAnimation(self.card_frame, b'windowOpacity')
        anim.setDuration(220);
        anim.setStartValue(1.0);
        anim.setEndValue(0.0)
        anim.finished.connect(self._finish_flip)
        anim.start()

    def _finish_flip(self):
        self.show_front = not self.show_front;
        self.update_card_display()
        anim = QPropertyAnimation(self.card_frame, b'windowOpacity')
        anim.setDuration(220);
        anim.setStartValue(0.0);
        anim.setEndValue(1.0)
        anim.start()

    def flip_card(self, event=None):
        if not self.current_card_ids: return
        self.animate_flip()

    def next_card(self):
        if not self.current_card_ids: return
        self.current_index = (self.current_index + 1) % len(self.current_card_ids)
        self.show_front = True;
        self.update_card_display()

    def prev_card(self):
        if not self.current_card_ids: return
        self.current_index = (self.current_index - 1) % len(self.current_card_ids)
        self.show_front = True;
        self.update_card_display()

    # --- Spaced repetition (SM-2 inspired) ---
    def record_assessment(self, quality):
        if not self.current_card_ids: return
        cid = self.current_card_ids[self.current_index]
        cur = self.conn.cursor();
        cur.execute('SELECT ease, interval, reps FROM cards WHERE id=?', (cid,))
        row = cur.fetchone();
        if not row: return
        ease, interval, reps = row
        if quality < 3:
            reps = 0;
            interval = 1
        else:
            reps += 1
            ease = max(1.3, ease + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            if reps == 1:
                interval = 1
            elif reps == 2:
                interval = 6
            else:
                interval = int(interval * ease)
        due = datetime.utcnow().strftime('%Y-%m-%d')
        cur.execute('UPDATE cards SET ease=?, interval=?, reps=?, due_date=? WHERE id=?',
                    (ease, interval, reps, due, cid))
        self.conn.commit()
        self.next_card()

    # --- Import / Export ---
    def import_deck(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Import Deck CSV', '', 'CSV Files (*.csv)')
        if not path: return
        df = pd.read_csv(path)
        name, ok = QInputDialog.getText(self, 'Imported deck name', 'Deck name:')
        if not ok or not name.strip(): return
        self.create_deck(name.strip())
        cur = self.conn.cursor();
        cur.execute('SELECT id FROM decks WHERE name=? AND profile_id=?', (name, self.profile_id))
        deck_id = cur.fetchone()[0]
        for _, row in df.iterrows():
            img = ''
            if 'image_path' in row and pd.notna(row['image_path']):
                img = copy_image_to_storage(row['image_path'])
            cur.execute(
                'INSERT INTO cards (deck_id, front, back, notes, image_path, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (deck_id, row.get('front', ''), row.get('back', ''), row.get('notes', ''), img, now_iso()))
        self.conn.commit();
        self._load_decks()

    def export_deck(self):
        if not self.current_deck_id: return
        path, _ = QFileDialog.getSaveFileName(self, 'Export Deck CSV', '', 'CSV Files (*.csv)')
        if not path: return
        cur = self.conn.cursor();
        cur.execute('SELECT front, back, notes, image_path FROM cards WHERE deck_id=?', (self.current_deck_id,))
        rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=['front', 'back', 'notes', 'image_path'])
        df.to_csv(path, index=False)

    # --- Theme & Dyslexia font support ---
    def choose_theme(self):
        options = list(self.THEMES.keys())
        name, ok = QInputDialog.getItem(self, 'Choose Theme', 'Theme:', options,
                                        options.index(self.current_theme) if self.current_theme in options else 0,
                                        False)
        if ok:
            self.current_theme = name
            self.apply_theme(name)

    def apply_theme(self, name):
        th = self.THEMES.get(name, self.THEMES['Light'])
        pal = QPalette()
        pal.setColor(QPalette.ColorRole.Window, QColor(th['window']))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(th['text']))
        pal.setColor(QPalette.ColorRole.Base, QColor(th['card_start']))
        pal.setColor(QPalette.ColorRole.Text, QColor(th['text']))
        QApplication.instance().setPalette(pal)
        # update card stylesheet
        self.card_frame.setStyleSheet(self.card_stylesheet())

    def toggle_dyslexia(self):
        # toggle between dyslexic font and fallback
        if self.dyslexic_family:
            self.use_dyslexic = not self.use_dyslexic
            fam = self.dyslexic_family if self.use_dyslexic else self.fallback_family
            font = QFont(fam, self.font_size)
            QApplication.instance().setFont(font)
            self.card_frame.setStyleSheet(self.card_stylesheet())
        else:
            QMessageBox.information(self, 'Font not found',
                                    'OpenDyslexic font is not installed on your system. Please install it to use dyslexic-friendly font.')

    pass