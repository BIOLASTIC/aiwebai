from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.api_key_auth import generate_api_key, hash_key
from backend.app.auth.dependencies import get_current_admin
from backend.app.db.engine import get_db
from backend.app.db.models import ConsumerApiKey, User

router = APIRouter(prefix="/admin/api-keys", tags=["admin-api-keys"])


@router.get("/")
async def list_api_keys(db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    keys = (await db.execute(select(ConsumerApiKey))).scalars().all()
    return [{"id": k.id, "label": k.label, "status": k.status, "created_at": k.created_at} for k in keys]


@router.post("/")
async def create_api_key(label: str, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    raw_key = generate_api_key()
    api_key = ConsumerApiKey(user_id=admin.id, key_hash=hash_key(raw_key), label=label, status="active")
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return {"id": api_key.id, "key": raw_key, "label": label}


@router.delete("/{key_id}")
async def revoke_api_key(key_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    api_key = await db.get(ConsumerApiKey, key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    await db.delete(api_key)
    await db.commit()
    return {"status": "success"}
