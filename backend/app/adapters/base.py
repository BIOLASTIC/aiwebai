from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional, Dict, Any
from pathlib import Path
from backend.app.schemas.openai import ChatCompletionRequest, ChatCompletionResponse
from backend.app.schemas.native import ImageGenerationRequest, JobResponse


class VideoResult:
    """Represents the result of a video generation operation."""

    def __init__(self, video_urls: List[str], metadata: Optional[Dict[str, Any]] = None):
        self.video_urls = video_urls
        self.metadata = metadata or {}


class BaseAdapter(ABC):
    @abstractmethod
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        pass

    @abstractmethod
    async def stream_chat(self, request: ChatCompletionRequest) -> AsyncGenerator[Dict[str, Any], None]:
        pass

    @abstractmethod
    async def generate_image(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def list_models(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    @abstractmethod
    async def generate_video(
        self,
        prompt: str,
        model: str | None,
        account_id: int | None,
        reference_files: list[Path] | None,
        options: dict | None,
    ) -> "VideoResult":
        pass
