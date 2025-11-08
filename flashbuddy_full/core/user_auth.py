import hashlib
import os
from .database import Database

class Auth:
    def __init__(self, db: Database):
        self.db = db

    def _hash_password(self, password: str, salt: bytes) -> str:
        # PBKDF2-HMAC-SHA256
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000).hex()

    def create_user(self, username: str, password: str):
        salt = os.urandom(16)
        phash = self._hash_password(password, salt)
        return self.db.create_user(username, phash, salt.hex())

    def verify_user(self, username: str, password: str):
        row = self.db.get_user_by_username(username)
        if not row:
            return None
        stored_hash = row['password_hash']
        salt_hex = row['salt']
        salt = bytes.fromhex(salt_hex)
        check = self._hash_password(password, salt)
        if check == stored_hash:
            return row['id']
        return None
