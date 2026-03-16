from typing import List, Optional, Dict, Any, Union, AsyncGenerator
import time
from backend.app.adapters.base import BaseAdapter
from backend.app.adapters.webapi_adapter import WebApiAdapter
from backend.app.adapters.mcpcli_adapter import McpCliAdapter
from backend.app.accounts.manager import account_manager
from backend.app.schemas.openai import ChatCompletionRequest, ChatCompletionResponse
from backend.app.schemas.native import ImageGenerationRequest
from fastapi import HTTPException

class AdapterRouter:
    def get_best_adapter(self, capability: str) -> BaseAdapter:
        # Get adapters from account manager
        adapters = account_manager.get_all_adapters()
        
        if not adapters:
            raise HTTPException(
                status_code=503, 
                detail="No Gemini accounts linked. Please add an account in the Admin panel."
            )
            
        # Priority logic: prefer webapi for chat, mcpcli for advanced tasks if available
        if capability == "chat":
            for adapter in adapters:
                if isinstance(adapter, WebApiAdapter):
                    return adapter
        
        if capability == "image":
            for adapter in adapters:
                if isinstance(adapter, WebApiAdapter):
                    return adapter
            for adapter in adapters:
                if isinstance(adapter, McpCliAdapter):
                    return adapter
        
        # Default to first available
        return adapters[0]

    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        adapter = self.get_best_adapter("chat")
        return await adapter.chat_completion(request)

    async def stream_chat(self, request: ChatCompletionRequest) -> AsyncGenerator[Dict[str, Any], None]:
        adapter = self.get_best_adapter("chat")
        async for chunk in adapter.stream_chat(request):
            yield chunk

    async def generate_image(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        from backend.app.logging.structured import logger
        adapters = account_manager.get_all_adapters()
        
        # Sort adapters: WebApi first, then McpCli
        sorted_adapters = sorted(
            adapters, 
            key=lambda a: 0 if isinstance(a, WebApiAdapter) else 1
        )
        
        last_error = None
        for adapter in sorted_adapters:
            try:
                res = await adapter.generate_image(request)
                if res.get("data"):
                    return res
                logger.warning("Adapter returned no images, trying next", adapter=type(adapter).__name__)
            except Exception as e:
                logger.error("Adapter.generate_image failed", adapter=type(adapter).__name__, error=str(e))
                last_error = e
        
        if last_error:
            raise last_error
        return {"created": int(time.time()), "data": []}

adapter_router = AdapterRouter()
