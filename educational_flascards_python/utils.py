# utils.py
import shutil
from pathlib import Path
from datetime import datetime

APP_DIR = Path.home() / '.pyqt_flashcards'
IMG_DIR = APP_DIR / 'images'
IMG_DIR.mkdir(exist_ok=True)

def now_iso():
    return datetime.utcnow().isoformat()

def copy_image_to_storage(src_path: str) -> str:
    if not src_path:
        return ''
    try:
        src = Path(src_path)
        if not src.exists():
            return ''
        dest = IMG_DIR / f"{int(datetime.utcnow().timestamp())}_{src.name}"
        shutil.copy(src, dest)
        return str(dest)
    except Exception as e:
        print('Image copy error:', e)
        return ''