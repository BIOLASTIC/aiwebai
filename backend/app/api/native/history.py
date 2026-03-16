from fastapi import APIRouter, Depends, HTTPException
from typing import List, Any, Dict
from backend.app.adapters.router import adapter_router
from backend.app.auth.api_key_auth import get_user_by_api_key
from backend.app.db.models import User

router = APIRouter(prefix="/native/history", tags=["native-history"])

@router.get("/")
async def list_history(user: User = Depends(get_user_by_api_key)):
    adapter = adapter_router.get_best_adapter("chat")
    if hasattr(adapter, "client") and hasattr(adapter.client, "get_conversations"):
        return await adapter.client.get_conversations()
    return {"status": "not_supported"}

@router.delete("/{chat_id}")
async def delete_history(chat_id: str, user: User = Depends(get_user_by_api_key)):
    adapter = adapter_router.get_best_adapter("chat")
    if hasattr(adapter, "client") and hasattr(adapter.client, "delete_conversation"):
        await adapter.client.delete_conversation(chat_id)
        return {"status": "deleted"}
    return {"status": "not_supported"}
