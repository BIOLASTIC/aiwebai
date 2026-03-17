from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.api_key_auth import generate_api_key, hash_key
from backend.app.auth.dependencies import get_current_admin
from backend.app.db.engine import get_db
from backend.app.db.models import ConsumerApiKey, User

router = APIRouter(prefix="/admin/mcp/tokens", tags=["admin-mcp-tokens"])


@router.get("/")
async def list_mcp_tokens(db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    result = await db.execute(select(ConsumerApiKey).where(ConsumerApiKey.scopes.contains(["mcp"])))
    keys = result.scalars().all()
    return [{"id": k.id, "label": k.label, "status": k.status, "created_at": k.created_at} for k in keys]


@router.post("/")
async def create_mcp_token(label: str, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    raw_key = generate_api_key()
    api_key = ConsumerApiKey(user_id=admin.id, key_hash=hash_key(raw_key), label=label, status="active", scopes=["mcp"])
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return {"id": api_key.id, "token": raw_key, "label": label}


@router.delete("/{token_id}")
async def revoke_mcp_token(token_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    api_key = await db.get(ConsumerApiKey, token_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="MCP token not found")
    await db.delete(api_key)
    await db.commit()
    return {"status": "success"}
