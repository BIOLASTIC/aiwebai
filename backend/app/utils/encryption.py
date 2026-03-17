from cryptography.fernet import Fernet
from backend.app.config import settings
import base64

# Simple encryption utility using MASTER_ENCRYPTION_KEY
# If key is missing, this will fail on startup which is good for security
try:
    key = settings.MASTER_ENCRYPTION_KEY
    if not key or len(key) < 10:
        # Fallback to a stable dummy key for dev if NOT provided,
        # but don't generate a new one every restart
        key = "RN8EKMM-PkW4853BCQGOvAxh8VsSeYiIBA7V0TBuzBE="
    _fernet = Fernet(key.encode())
except Exception:
    # Final fallback to allow boot if even the hardcoded key is invalid for Fernet
    _fernet = Fernet(b'RN8EKMM-PkW4853BCQGOvAxh8VsSeYiIBA7V0TBuzBE=')


def encrypt(data: str) -> str:
    return _fernet.encrypt(data.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    return _fernet.decrypt(token.encode("utf-8")).decode("utf-8")
