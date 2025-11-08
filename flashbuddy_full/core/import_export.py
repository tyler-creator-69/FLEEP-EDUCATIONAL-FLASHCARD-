import pandas as pd
from .database import Database
from .settings import IMG_DIR
from pathlib import Path
import shutil
import time

def import_csv(path, db: Database, profile_id):
    df = pd.read_csv(path)
    name = Path(path).stem
    deck_id = db.create_deck(name, profile_id)
    for _, row in df.iterrows():
        img = ''
        if 'image_path' in row and pd.notna(row['image_path']):
            src = Path(row['image_path'])
            if src.exists():
                dest = IMG_DIR / f"{int(time.time())}_{src.name}"
                shutil.copy(src, dest)
                img = str(dest)
        db.add_card(deck_id, row.get('front',''), row.get('back',''), row.get('notes',''), img)
    return deck_id

def export_csv(deck_id, db: Database, path):
    rows = db.conn.cursor().execute('SELECT front, back, notes, image_path FROM cards WHERE deck_id=?', (deck_id,)).fetchall()
    import pandas as pd
    df = pd.DataFrame(rows, columns=['front','back','notes','image_path'])
    df.to_csv(path, index=False)
