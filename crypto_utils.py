from __future__ import annotations

import base64
import hashlib
import os

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

try:
    from cryptography.fernet import Fernet
    HAS_FERNET = True
except ImportError:
    HAS_FERNET = False


def hash_password(password: str) -> str:
    if HAS_BCRYPT:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    return _fallback_hash(password)


def check_password(password: str, hashed: str) -> bool:
    if HAS_BCRYPT and _is_bcrypt(hashed):
        return bcrypt.checkpw(password.encode(), hashed.encode())
    return _fallback_verify(password, hashed)


def _is_bcrypt(hashed: str) -> bool:
    return hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$2y$")


def _fallback_hash(password: str) -> str:
    salt = hashlib.sha256(os.urandom(16)).hexdigest()[:16]
    return f"sha256${salt}${hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()}"


def _fallback_verify(password: str, hashed: str) -> bool:
    if not hashed.startswith("sha256$"):
        return False
    _, salt, stored_hash = hashed.split("$", 2)
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex() == stored_hash


def encrypt_password(plaintext: str, key: str | None = None) -> str:
    if not HAS_FERNET or not key:
        return plaintext
    try:
        f = Fernet(key.encode() if isinstance(key, str) else key)
        return f.encrypt(plaintext.encode()).decode()
    except Exception:
        return plaintext


def decrypt_password(ciphertext: str, key: str | None = None) -> str:
    if not HAS_FERNET or not key:
        return ciphertext
    try:
        f = Fernet(key.encode() if isinstance(key, str) else key)
        return f.decrypt(ciphertext.encode()).decode()
    except Exception:
        return ciphertext


def generate_fernet_key() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode()
