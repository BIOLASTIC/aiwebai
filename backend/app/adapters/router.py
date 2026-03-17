from __future__ import annotations

import time
from typing import Any, AsyncGenerator, Dict, List, Optional
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.accounts.manager import account_manager
from backend.app.adapters.base import BaseAdapter
from backend.app.adapters.mcpcli_adapter import McpCliAdapter
from backend.app.adapters.webapi_adapter import WebApiAdapter
from backend.app.db.models import Model
from backend.app.models.registry import model_registry
from backend.app.schemas.native import ImageGenerationRequest
from backend.app.schemas.openai import ChatCompletionRequest, ChatCompletionResponse


class AdapterRouter:
    def __init__(self) -> None:
        self.mock_adapter = WebApiAdapter(mock_mode=True)

    def get_best_adapter(self, capability: str) -> BaseAdapter:
        adapters = account_manager.get_all_adapters()
        if not adapters:
            return self.mock_adapter
        if capability == "chat":
            for adapter in adapters:
                if isinstance(adapter, WebApiAdapter):
                    return adapter
        if capability in {"image", "image_edit"}:
            for adapter in adapters:
                if isinstance(adapter, WebApiAdapter):
                    return adapter
            for adapter in adapters:
                if isinstance(adapter, McpCliAdapter):
                    return adapter
        if capability in {"video", "music", "research"}:
            for adapter in adapters:
                if isinstance(adapter, McpCliAdapter):
                    return adapter
        return adapters[0]

    async def refresh_catalog(self, db: AsyncSession) -> None:
        await model_registry.discover_models()

    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        adapter = self.get_best_adapter("chat")
        return await adapter.chat_completion(request)

    async def stream_chat(self, request: ChatCompletionRequest) -> AsyncGenerator[Dict[str, Any], None]:
        adapter = self.get_best_adapter("chat")
        async for chunk in adapter.stream_chat(request):
            yield chunk

    async def generate_image(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        if request.account_id:
            adapter = account_manager.get_adapter_for_account(request.account_id)
            if adapter:
                return await adapter.generate_image(request)
        
        last_error = None
        for adapter in [a for a in account_manager.get_all_adapters()] or [self.mock_adapter]:
            try:
                result = await adapter.generate_image(request)
                if result.get("data"):
                    return result
            except Exception as exc:
                last_error = exc
        if last_error:
            raise last_error
        return {"created": int(time.time()), "data": []}

    async def generate_video(self, prompt: str, model: str | None, account_id: int | None, reference_files: list[Path] | None, options: dict | None):
        adapter = self.get_best_adapter("video")
        return await adapter.generate_video(prompt, model, account_id, reference_files, options)

    async def generate_music(self, prompt: str) -> str:
        adapter = self.get_best_adapter("music")
        return await adapter.generate_music(prompt)

    async def generate_research(self, prompt: str) -> str:
        adapter = self.get_best_adapter("research")
        return await adapter.deep_research(prompt)


adapter_router = AdapterRouter()
