from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from backend.app.schemas.openai import ChatCompletionRequest, ChatCompletionResponse
from backend.app.adapters.router import adapter_router
from backend.app.adapters.webapi_adapter import WebApiAdapter
from backend.app.adapters.mcpcli_adapter import McpCliAdapter
from backend.app.config import settings
from backend.app.auth.api_key_auth import get_user_by_key_or_jwt
from backend.app.db.models import User
import json
import asyncio

router = APIRouter(prefix="/v1/chat", tags=["openai"])

@router.post("/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    current_user: User = Depends(get_user_by_key_or_jwt)
):
    if request.stream:
        return StreamingResponse(
            chat_streamer(request),
            media_type="text/event-stream"
        )
    
    return await adapter_router.chat_completion(request)

async def chat_streamer(request: ChatCompletionRequest):
    async for chunk in adapter_router.stream_chat(request):
        yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"
