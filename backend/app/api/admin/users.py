from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.engine import get_db
from backend.app.db.models import User
from backend.app.schemas.admin import UserCreate, UserResponse
from backend.app.auth.password import get_password_hash
from backend.app.auth.dependencies import get_current_admin

router = APIRouter(prefix="/admin/users", tags=["admin-users"])

@router.get("/", response_model=List[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    result = await db.execute(select(User))
    return result.scalars().all()

@router.post("/", response_model=UserResponse)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="User already exists")
    
    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role,
        status=user_in.status
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_in: UserCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_in.email:
        user.email = user_in.email
    if user_in.password:
        user.password_hash = get_password_hash(user_in.password)
    if user_in.role:
        user.role = user_in.role
    if user_in.status:
        user.status = user_in.status
        
    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    return {"status": "success"}
