from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional, Dict, Any
from backend.app.schemas.openai import ChatCompletionRequest, ChatCompletionResponse
from backend.app.schemas.native import ImageGenerationRequest, JobResponse

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

