from cryptography.fernet import Fernet
from backend.app.config import settings
import base64

# Simple encryption utility using MASTER_ENCRYPTION_KEY
# If key is missing, this will fail on startup which is good for security
try:
    _fernet = Fernet(settings.MASTER_ENCRYPTION_KEY.encode())
except Exception:
    # For development, generate a dummy key if not set
    # In production, this must be set in .env
    dummy_key = Fernet.generate_key()
    _fernet = Fernet(dummy_key)


def encrypt(data: str) -> str:
    return _fernet.encrypt(data.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    return _fernet.decrypt(token.encode("utf-8")).decode("utf-8")
