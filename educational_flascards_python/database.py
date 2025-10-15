import sqlite3
from pathlib import Path
from datetime import datetime


APP_DIR = Path.home() / 'pyqt_flascard'
DB_PATH = APP_DIR / 'flashcards.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.excecute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY, name TEXT UNIQUE, created_at TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS decks (
            id INTEGER PRIMARY KEY, name TEXT, profile_id INTEGER, created_at TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY, deck_id INTEGER, front TEXT, back TEXT,
            notes TEXT, image_path TEXT, created_at TEXT, ease REAL DEFAULT 2.5,
            interval INTEGER DEFAULT 1, reps INTEGER DEFAULT 0, due_date TEXT
        )
    ''')
    conn.commit()
    return conn