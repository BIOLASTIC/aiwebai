import json
import time
from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.adapters.router import adapter_router
from backend.app.auth.api_key_auth import get_user_by_key_or_jwt
from backend.app.db.engine import get_db
from backend.app.db.models import Model, User
from backend.app.schemas.native import ImageGenerationRequest as NativeImageGenerationRequest
from backend.app.schemas.openai import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ImageEditRequest,
    ImageGenerationRequest,
    ModelCard,
    ResponsesRequest,
    ResponsesResponse,
)

router = APIRouter(tags=["openai"])


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest, current_user: User = Depends(get_user_by_key_or_jwt)):
    if request.stream:
        return StreamingResponse(chat_streamer(request), media_type="text/event-stream")
    return await adapter_router.chat_completion(request)


async def chat_streamer(request: ChatCompletionRequest):
    async for chunk in adapter_router.stream_chat(request):
        yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"


@router.get("/v1/models")
async def list_models(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_user_by_key_or_jwt)):
    models = (await db.execute(select(Model).where(Model.status == "active"))).scalars().all()

    # Build model list with adapter prefixes
    data = []
    seen = set()

    for m in models:
        caps = m.capabilities or {}
        source = m.source_provider or ""

        # Get clean model name (remove any existing prefix)
        clean_name = m.provider_model_name
        for prefix in ["webapi-", "mcpcli-", "mcp-"]:
            if clean_name.startswith(prefix):
                clean_name = clean_name[len(prefix) :]
                break

        # Add model with appropriate prefix based on source_provider
        if source == "webapi":
            model_id = f"webapi-{clean_name}"
            if model_id not in seen:
                seen.add(model_id)
                data.append(ModelCard(id=model_id, capabilities=caps).model_dump())
        elif source == "mcpcli":
            model_id = f"mcpcli-{clean_name}"
            if model_id not in seen:
                seen.add(model_id)
                data.append(ModelCard(id=model_id, capabilities=caps).model_dump())
        else:
            # Fallback - add both
            webapi_id = f"webapi-{clean_name}"
            mcpcli_id = f"mcpcli-{clean_name}"
            if webapi_id not in seen:
                seen.add(webapi_id)
                data.append(ModelCard(id=webapi_id, capabilities=caps).model_dump())
            if mcpcli_id not in seen:
                seen.add(mcpcli_id)
                data.append(ModelCard(id=mcpcli_id, capabilities=caps).model_dump())

    if not data:
        # fall back to adapter discovery without requiring refresh
        await adapter_router.refresh_catalog(db)
        models = (await db.execute(select(Model).where(Model.status == "active"))).scalars().all()
        for m in models:
            caps = m.capabilities or {}
            source = m.source_provider or ""
            clean_name = m.provider_model_name
            for prefix in ["webapi-", "mcpcli-", "mcp-"]:
                if clean_name.startswith(prefix):
                    clean_name = clean_name[len(prefix) :]
                    break
            if source == "webapi":
                data.append(ModelCard(id=f"webapi-{clean_name}", capabilities=caps).model_dump())
            elif source == "mcpcli":
                data.append(ModelCard(id=f"mcpcli-{clean_name}", capabilities=caps).model_dump())
            else:
                data.append(ModelCard(id=f"webapi-{clean_name}", capabilities=caps).model_dump())
                data.append(ModelCard(id=f"mcpcli-{clean_name}", capabilities=caps).model_dump())

    return {"object": "list", "data": data}


@router.post("/v1/responses", response_model=ResponsesResponse)
async def responses(request: ResponsesRequest, current_user: User = Depends(get_user_by_key_or_jwt)):
    message = str(request.input) if not isinstance(request.input, str) else request.input
    chat_request = ChatCompletionRequest(
        model=request.model,
        messages=[{"role": "user", "content": message}],
        stream=request.stream,
        user=None,
        account_id=request.account_id,
    )
    response = await adapter_router.chat_completion(chat_request)
    return ResponsesResponse(
        id=f"resp-{int(time.time())}", model=request.model, output_text=response.choices[0].message.content
    )


@router.post("/v1/images/generations")
async def image_generations(request: ImageGenerationRequest, current_user: User = Depends(get_user_by_key_or_jwt)):
    payload = NativeImageGenerationRequest(
        prompt=request.prompt, model=request.model, size=request.size, account_id=request.account_id
    )
    return await adapter_router.generate_image(payload)


@router.post("/v1/images/edits")
async def image_edits(request: ImageEditRequest, current_user: User = Depends(get_user_by_key_or_jwt)):
    payload = NativeImageGenerationRequest(prompt=request.prompt, model=request.model, account_id=request.account_id)
    return await adapter_router.generate_image(payload)
