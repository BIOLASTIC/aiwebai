from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
import jwt
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.config import settings
from backend.app.db.engine import get_db
from backend.app.db.models import User
from backend.app.auth.jwt_handler import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user
