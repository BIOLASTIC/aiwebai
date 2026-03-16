from fastapi import APIRouter, Depends, HTTPException
from backend.app.adapters.router import AdapterRouter
from backend.app.auth.api_key_auth import get_user_by_api_key
from backend.app.db.models import User

router = APIRouter(prefix="/native", tags=["native"])

# Assuming adapter_router is shared
from backend.app.api.openai.chat_completions import adapter_router

@router.get("/limits")
async def get_limits(current_user: User = Depends(get_user_by_api_key)):
    adapter = adapter_router.get_best_adapter("chat") # Use any adapter for limits
    
    # Check if adapter supports get_limits (McpCliAdapter does)
    if hasattr(adapter, "get_limits"):
        return await adapter.get_limits()
    
    return {"status": "not_supported_by_adapter"}
