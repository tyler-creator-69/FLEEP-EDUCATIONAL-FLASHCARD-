import sqlite3
from .settings import DB_PATH
from datetime import datetime


# ===============================
# Database schema
# ===============================

CREATE_TABLES = [
    '''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT,
        salt TEXT,
        created_at TEXT
    )''',

    '''CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        created_at TEXT
    )''',

    '''CREATE TABLE IF NOT EXISTS decks (
        id INTEGER PRIMARY KEY,
        name TEXT,
        profile_id INTEGER,
        created_at TEXT
    )''',

    '''CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY,
        deck_id INTEGER,
        front TEXT,
        back TEXT,
        notes TEXT,
        image_path TEXT,
        created_at TEXT,
        ease REAL DEFAULT 2.5,
        interval INTEGER DEFAULT 1,
        reps INTEGER DEFAULT 0,
        due_date TEXT
    )'''
]


# ===============================
# Database Class
# ===============================


class Database:
    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        cur = self.conn.cursor()
        for q in CREATE_TABLES:
            cur.execute(q)
        self.conn.commit()

    # ===============================
    # User management
    # ===============================

    def create_user(self, username, password_hash, salt_hex):
        cur = self.conn.cursor()
        cur.execute(
            'INSERT INTO users (username, password_hash, salt, created_at) VALUES (?, ?, ?, ?)',
            (username, password_hash, salt_hex, datetime.utcnow().isoformat())
        )
        self.conn.commit()
        return cur.lastrowid

    def get_user_by_username(self, username):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM users WHERE username=?', (username,))
        return cur.fetchone()

    # ===============================
    # Profiles
    # ===============================

    def create_profile_if_missing(self, name='default'):
        cur = self.conn.cursor()
        cur.execute('SELECT id FROM profiles WHERE name=?', (name,))
        r = cur.fetchone()

        if r:
            return r['id']

        cur.execute(
            'INSERT INTO profiles (name, created_at) VALUES (?, ?)',
            (name, datetime.utcnow().isoformat())
        )
        self.conn.commit()
        return cur.lastrowid

    # ===============================
    # Decks
    # ===============================

    def list_decks(self, profile_id):
        cur = self.conn.cursor()
        cur.execute('SELECT id, name FROM decks WHERE profile_id=?', (profile_id,))
        return cur.fetchall()

    def create_deck(self, name, profile_id):
        cur = self.conn.cursor()
        cur.execute(
            'INSERT INTO decks (name, profile_id, created_at) VALUES (?, ?, ?)',
            (name, profile_id, datetime.utcnow().isoformat())
        )
        self.conn.commit()
        return cur.lastrowid

    def delete_deck(self, deck_id):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM cards WHERE deck_id=?', (deck_id,))
        cur.execute('DELETE FROM decks WHERE id=?', (deck_id,))
        self.conn.commit()

    # ===============================
    # Cards
    # ===============================

    def list_cards(self, deck_id):
        cur = self.conn.cursor()
        cur.execute('SELECT id, front FROM cards WHERE deck_id=?', (deck_id,))
        return cur.fetchall()

    def add_card(self, deck_id, front, back, notes, image_path):
        cur = self.conn.cursor()
        cur.execute(
            'INSERT INTO cards (deck_id, front, back, notes, image_path, created_at) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (deck_id, front, back, notes, image_path, datetime.utcnow().isoformat())
        )
        self.conn.commit()
        return cur.lastrowid

    def get_card(self, card_id):
        cur = self.conn.cursor()
        cur.execute(
            '''SELECT id, front, back, notes, image_path, ease, interval, reps
               FROM cards WHERE id=?''',
            (card_id,)
        )
        return cur.fetchone()

    def update_card(self, card_id, front, back, notes, image_path):
        cur = self.conn.cursor()
        cur.execute(
            'UPDATE cards SET front=?, back=?, notes=?, image_path=? WHERE id=?',
            (front, back, notes, image_path, card_id)
        )
        self.conn.commit()

    def delete_card(self, card_id):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM cards WHERE id=?', (card_id,))
        self.conn.commit()

    def update_review(self, card_id, ease, interval, reps, due_date):
        cur = self.conn.cursor()
        cur.execute(
            'UPDATE cards SET ease=?, interval=?, reps=?, due_date=? WHERE id=?',
            (ease, interval, reps, due_date, card_id)
        )
        self.conn.commit()

    # ===============================
    # Stats for Dashboard
    # ===============================

    def count_reviews(self, profile_id: int) -> int:
        """Total number of reviews across all cards."""
        cur = self.conn.cursor()
        q = """
        SELECT SUM(reps) AS total_reviews
        FROM cards
        WHERE deck_id IN (SELECT id FROM decks WHERE profile_id=?)
        """
        cur.execute(q, (profile_id,))
        row = cur.fetchone()
        return row["total_reviews"] if row and row["total_reviews"] is not None else 0

    def get_average_ease(self, profile_id: int) -> float:
        """Average ease score of all cards."""
        cur = self.conn.cursor()
        q = """
        SELECT AVG(ease) AS avg_ease
        FROM cards
        WHERE deck_id IN (SELECT id FROM decks WHERE profile_id=?)
        """
        cur.execute(q, (profile_id,))
        row = cur.fetchone()
        return float(row["avg_ease"]) if row and row["avg_ease"] is not None else 0.0

    def count_mastered_cards(self, profile_id: int) -> int:
        """Mastered = reps >= 5 AND ease >= 3.0."""
        cur = self.conn.cursor()
        q = """
        SELECT COUNT(*) AS mastered
        FROM cards
        WHERE deck_id IN (SELECT id FROM decks WHERE profile_id=?)
        AND reps >= 5 AND ease >= 3.0
        """
        cur.execute(q, (profile_id,))
        row = cur.fetchone()
        return row["mastered"] if row else 0
