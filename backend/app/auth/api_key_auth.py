import secrets
import hashlib
from typing import Optional
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.engine import get_db
from backend.app.db.models import ConsumerApiKey, User
from backend.app.auth.jwt_handler import decode_token

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_oauth2_optional = OAuth2PasswordBearer(tokenUrl="/admin/login", auto_error=False)

def generate_api_key() -> str:
    return f"sk-{secrets.token_urlsafe(32)}"

def hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()

async def get_user_by_api_key(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key missing",
        )
    
    hashed_key = hash_key(api_key)
    result = await db.execute(
        select(ConsumerApiKey).where(ConsumerApiKey.key_hash == hashed_key, ConsumerApiKey.status == "active")
    )
    api_key_record = result.scalars().first()
    
    if not api_key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API Key",
        )
    
    result = await db.execute(select(User).where(User.id == api_key_record.user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_user_by_key_or_jwt(
    api_key: Optional[str] = Security(api_key_header),
    token: Optional[str] = Depends(_oauth2_optional),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Accept either X-API-Key or Authorization: Bearer <admin-jwt>."""
    # Try API key first
    if api_key:
        hashed_key = hash_key(api_key)
        result = await db.execute(
            select(ConsumerApiKey).where(ConsumerApiKey.key_hash == hashed_key, ConsumerApiKey.status == "active")
        )
        api_key_record = result.scalars().first()
        if api_key_record:
            result = await db.execute(select(User).where(User.id == api_key_record.user_id))
            user = result.scalars().first()
            if user:
                return user

    # Try JWT Bearer (admin UI)
    if token:
        payload = decode_token(token)
        email: str = payload.get("sub")
        if email:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalars().first()
            if user:
                return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid API Key or admin token required",
    )
