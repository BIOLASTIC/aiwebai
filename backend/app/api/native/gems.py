from fastapi import APIRouter, Depends, HTTPException
from typing import List, Any, Dict
from backend.app.adapters.router import adapter_router
from backend.app.auth.api_key_auth import get_user_by_api_key
from backend.app.db.models import User
from pydantic import BaseModel

router = APIRouter(prefix="/native/gems", tags=["native-gems"])

class GemCreate(BaseModel):
    name: str
    instruction: str
    model: str = "gemini-pro"

@router.get("/")
async def list_gems(user: User = Depends(get_user_by_api_key)):
    adapter = adapter_router.get_best_adapter("chat")
    if hasattr(adapter, "client") and hasattr(adapter.client, "get_gems"):
        return await adapter.client.get_gems()
    return {"status": "not_supported"}

@router.post("/")
async def create_gem(gem: GemCreate, user: User = Depends(get_user_by_api_key)):
    adapter = adapter_router.get_best_adapter("chat")
    if hasattr(adapter, "client") and hasattr(adapter.client, "create_gem"):
        return await adapter.client.create_gem(gem.name, gem.instruction, gem.model)
    return {"status": "not_supported"}

@router.delete("/{gem_id}")
async def delete_gem(gem_id: str, user: User = Depends(get_user_by_api_key)):
    adapter = adapter_router.get_best_adapter("chat")
    if hasattr(adapter, "client") and hasattr(adapter.client, "delete_gem"):
        await adapter.client.delete_gem(gem_id)
        return {"status": "deleted"}
    return {"status": "not_supported"}
