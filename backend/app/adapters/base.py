from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List

from backend.app.schemas.native import ImageGenerationRequest, VideoResult
from backend.app.schemas.openai import ChatCompletionRequest, ChatCompletionResponse


class BaseAdapter(ABC):
    @abstractmethod
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        raise NotImplementedError

    @abstractmethod
    async def stream_chat(self, request: ChatCompletionRequest) -> AsyncGenerator[Dict[str, Any], None]:
        raise NotImplementedError

    @abstractmethod
    async def generate_image(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        raise NotImplementedError

    async def edit_image(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        return await self.generate_image(request)

    @abstractmethod
    async def list_models(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def generate_video(
        self,
        prompt: str,
        model: str | None,
        account_id: int | None,
        reference_files: list[Path] | None,
        options: dict | None,
    ) -> VideoResult:
        raise NotImplementedError

    async def get_limits(self) -> Dict[str, Any]:
        """Return usage limits and remaining quota. By default, returns empty/not supported."""
        return {"status": "not_supported_by_adapter"}

