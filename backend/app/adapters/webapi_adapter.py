from typing import AsyncGenerator, List, Optional, Dict, Any
import time
import uuid
from gemini_webapi import GeminiClient, ChatSession, ModelOutput
from backend.app.adapters.base import BaseAdapter
from backend.app.schemas.openai import ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChoice, ChatMessage
from backend.app.schemas.native import ImageGenerationRequest

# Comprehensive list of known Gemini models available via the web API
KNOWN_WEBAPI_MODELS: List[Dict[str, Any]] = [
    # --- Gemini 2.x ---
    {"id": "gemini-2.5-pro", "display_name": "Gemini 2.5 Pro", "family": "gemini-2.5"},
    {"id": "gemini-2.5-flash", "display_name": "Gemini 2.5 Flash", "family": "gemini-2.5"},
    {"id": "gemini-2.0-flash", "display_name": "Gemini 2.0 Flash", "family": "gemini-2.0"},
    {"id": "gemini-2.0-flash-thinking-exp", "display_name": "Gemini 2.0 Flash Thinking (Exp)", "family": "gemini-2.0"},
    {"id": "gemini-2.0-pro-exp", "display_name": "Gemini 2.0 Pro (Exp)", "family": "gemini-2.0"},
    {"id": "gemini-2.0-flash-exp", "display_name": "Gemini 2.0 Flash (Exp)", "family": "gemini-2.0"},
    # --- Gemini 1.5 ---
    {"id": "gemini-1.5-pro", "display_name": "Gemini 1.5 Pro", "family": "gemini-1.5"},
    {"id": "gemini-1.5-flash", "display_name": "Gemini 1.5 Flash", "family": "gemini-1.5"},
    {"id": "gemini-1.5-flash-8b", "display_name": "Gemini 1.5 Flash 8B", "family": "gemini-1.5"},
    # --- Gemini 1.0 ---
    {"id": "gemini-pro", "display_name": "Gemini Pro", "family": "gemini-1.0"},
    {"id": "gemini-1.0-pro", "display_name": "Gemini 1.0 Pro", "family": "gemini-1.0"},
    # --- Learnlm ---
    {"id": "learnlm-1.5-pro-experimental", "display_name": "LearnLM 1.5 Pro (Exp)", "family": "learnlm"},
]


class WebApiAdapter(BaseAdapter):
    def __init__(self, secure_1psid: str, secure_1psidts: str):
        self.client = GeminiClient(secure_1psid, secure_1psidts)
        self._secure_1psid = secure_1psid
        self.chat_sessions: Dict[str, ChatSession] = {}
        self._initialized = False

    async def init(self) -> None:
        """Initialize the underlying GeminiClient HTTP session."""
        if not self._initialized:
            await self.client.init(timeout=30, auto_close=False, close_delay=300, auto_refresh=True)
            self._initialized = True

    async def _get_chat_session(self, session_id: Optional[str] = None) -> ChatSession:
        key = session_id or "default"
        if key not in self.chat_sessions:
            self.chat_sessions[key] = self.client.start_chat()
        return self.chat_sessions[key]

    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        await self.init()
        last_message = request.messages[-1].content
        session = await self._get_chat_session(request.user)
        output: ModelOutput = await session.send_message(last_message)

        choice = ChatCompletionChoice(
            index=0,
            message=ChatMessage(role="assistant", content=output.text),
            finish_reason="stop",
        )
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4()}",
            created=int(time.time()),
            model=request.model,
            choices=[choice],
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        )

    async def stream_chat(self, request: ChatCompletionRequest) -> AsyncGenerator[Dict[str, Any], None]:
        await self.init()
        last_message = request.messages[-1].content
        session = await self._get_chat_session(request.user)
        chunk_id = f"chatcmpl-{uuid.uuid4()}"
        created = int(time.time())

        async for chunk in session.send_message_stream(last_message):
            yield {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": request.model,
                "choices": [{"index": 0, "delta": {"content": chunk.text}, "finish_reason": None}],
            }

        yield {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": request.model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }

    async def generate_image(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        from backend.app.logging.structured import logger
        try:
            logger.info("WebApiAdapter.generate_image starting", prompt=request.prompt, model=request.model)
            # Pass model if provided and valid in gemini-webapi context
            kwargs = {}
            if request.model and request.model != "gemini-image-latest":
                kwargs["model"] = request.model
            
            output = await self.client.generate_content(request.prompt, **kwargs)
            logger.info("WebApiAdapter.generate_image output received", 
                        has_images=hasattr(output, "images"),
                        num_images=len(output.images) if hasattr(output, "images") else 0,
                        text=output.text[:100] if hasattr(output, "text") else "N/A")
            
            image_urls = [{"url": img.url} for img in output.images] if hasattr(output, "images") else []
            return {"created": int(time.time()), "data": image_urls}
        except Exception as e:
            logger.error("WebApiAdapter.generate_image failed", error=str(e))
            raise

    async def list_models(self) -> List[Dict[str, Any]]:
        """Return the known Gemini web-API model list.

        gemini-webapi doesn't expose a public list_models() call, so we return
        a curated static list that matches what the web interface supports.
        """
        return KNOWN_WEBAPI_MODELS

    async def health_check(self) -> bool:
        """Send a minimal ping to Gemini to verify the cookie is still valid."""
        try:
            await self.init()
            await self.client.generate_content("hi")
            return True
        except Exception as e:
            from backend.app.logging.structured import logger
            logger.warning("WebApiAdapter health_check failed", error=type(e).__name__, detail=str(e))
            return False
