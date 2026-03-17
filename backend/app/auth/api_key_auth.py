import hashlib
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.jwt_handler import decode_token
from backend.app.db.engine import get_db
from backend.app.db.models import ConsumerApiKey, User

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)
_oauth2_optional = OAuth2PasswordBearer(tokenUrl="/admin/login", auto_error=False)


def generate_api_key() -> str:
    return f"sk-{secrets.token_urlsafe(32)}"


def hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


async def _lookup_user_by_api_key(db: AsyncSession, api_key: str) -> User | None:
    # Handle Bearer prefix if present manually (though HTTPBearer handles it)
    if api_key.startswith("Bearer "):
        api_key = api_key.replace("Bearer ", "")

    hashed_key = hash_key(api_key)
    result = await db.execute(select(ConsumerApiKey).where(ConsumerApiKey.status == "active"))
    for record in result.scalars().all():
        if record.key_hash in {api_key, hashed_key}:
            user = (await db.execute(select(User).where(User.id == record.user_id))).scalars().first()
            if user:
                return user
    return None


async def get_user_by_api_key(
    api_key: str = Security(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    key = api_key
    if not key and bearer:
        key = bearer.credentials

    if not key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key missing")
    user = await _lookup_user_by_api_key(db, key)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or inactive API Key")
    return user


async def get_user_by_key_or_jwt(
    api_key: Optional[str] = Security(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    token: Optional[str] = Depends(_oauth2_optional),
    db: AsyncSession = Depends(get_db),
) -> User:
    key = api_key
    if not key and bearer:
        key = bearer.credentials

    if key:
        user = await _lookup_user_by_api_key(db, key)
        if user:
            return user
    if token:
        payload = decode_token(token)
        email = payload.get("sub")
        if email:
            user = (await db.execute(select(User).where(User.email == email))).scalars().first()
            if user:
                return user
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Valid API Key or admin token required")
