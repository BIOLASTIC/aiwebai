from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.app.adapters.base import BaseAdapter
from backend.app.schemas.native import ImageGenerationRequest, VideoResult
from backend.app.schemas.openai import ChatCompletionChoice, ChatCompletionRequest, ChatCompletionResponse, ChatMessage

KNOWN_WEBAPI_MODELS: List[Dict[str, Any]] = [
    {"id": "gemini-2.5-pro", "display_name": "Gemini 2.5 Pro", "family": "pro", "capabilities": {"chat": True, "thinking": True}},
    {"id": "gemini-2.5-flash", "display_name": "Gemini 2.5 Flash", "family": "flash", "capabilities": {"chat": True, "streaming": True}},
    {"id": "gemini-2.0-flash-thinking-exp", "display_name": "Gemini Thinking", "family": "thinking", "capabilities": {"chat": True, "thinking": True}},
    {"id": "imagen-3.0", "display_name": "Imagen 3.0", "family": "image", "capabilities": {"images": True, "image_edit": True}},
    {"id": "gemini-research", "display_name": "Gemini Research", "family": "research", "capabilities": {"research": True}},
]

try:
    from gemini_webapi import GeminiClient  # type: ignore
except Exception:  # pragma: no cover
    GeminiClient = None  # type: ignore


class WebApiAdapter(BaseAdapter):
    def __init__(self, secure_1psid: str | None = None, secure_1psidts: str | None = None, mock_mode: bool | None = None):
        self._secure_1psid = secure_1psid
        self._secure_1psidts = secure_1psidts
        self.mock_mode = bool(mock_mode) if mock_mode is not None else not (secure_1psid and GeminiClient)
        self.client = GeminiClient(secure_1psid, secure_1psidts) if (GeminiClient and secure_1psid) else None
        self._initialized = False
        self.chat_sessions: Dict[str, Any] = {}

    async def init(self) -> None:
        if self.mock_mode or not self.client or self._initialized:
            return
        await self.client.init(timeout=30, auto_close=False, close_delay=300, auto_refresh=True)
        self._initialized = True

    async def _get_chat_session(self, session_id: Optional[str] = None):
        key = session_id or "default"
        if key not in self.chat_sessions:
            if self.mock_mode or not self.client:
                self.chat_sessions[key] = None
            else:
                self.chat_sessions[key] = self.client.start_chat()
        return self.chat_sessions[key]

    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        last_message = request.messages[-1].content if request.messages else ""
        if self.mock_mode or not self.client:
            text = f"[mock webapi] {last_message}" if last_message else "[mock webapi]"
        else:
            await self.init()
            session = await self._get_chat_session(request.user)
            output = await session.send_message(last_message)
            text = getattr(output, "text", str(output))
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4()}",
            created=int(time.time()),
            model=request.model,
            choices=[ChatCompletionChoice(index=0, message=ChatMessage(role="assistant", content=text), finish_reason="stop")],
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        )

    async def stream_chat(self, request: ChatCompletionRequest) -> AsyncGenerator[Dict[str, Any], None]:
        last_message = request.messages[-1].content if request.messages else ""
        chunk_id = f"chatcmpl-{uuid.uuid4()}"
        created = int(time.time())
        if self.mock_mode or not self.client:
            for token in (f"[mock webapi] {last_message}").split():
                yield {"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": request.model, "choices": [{"index": 0, "delta": {"content": token + ' '}, "finish_reason": None}]}
        else:
            await self.init()
            session = await self._get_chat_session(request.user)
            async for chunk in session.send_message_stream(last_message):
                delta = getattr(chunk, "text_delta", None) or getattr(chunk, "text", "")
                yield {"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": request.model, "choices": [{"index": 0, "delta": {"content": delta}, "finish_reason": None}]}
        yield {"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": request.model, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}

    async def generate_image(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        prompt = request.prompt.strip()
        if self.mock_mode or not self.client:
            return {"created": int(time.time()), "data": [{"url": f"mock://image/{uuid.uuid4().hex}", "prompt": prompt}]}
        await self.init()
        output = await self.client.generate_content(prompt, model="gemini-3.0-flash")
        images = getattr(output, "images", []) or []
        urls = []
        for image in images:
            url = getattr(image, "url", None)
            if url:
                urls.append({"url": url})
        if not urls:
            urls.append({"url": f"mock://image/{uuid.uuid4().hex}", "prompt": prompt})
        return {"created": int(time.time()), "data": urls}

    async def edit_image(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        return await self.generate_image(request)

    async def list_models(self) -> List[Dict[str, Any]]:
        return KNOWN_WEBAPI_MODELS

    async def health_check(self) -> bool:
        if self.mock_mode:
            return True
        try:
            await self.init()
            await self.client.generate_content("hi")
            return True
        except Exception:
            return False

    async def generate_video(self, prompt: str, model: str | None, account_id: int | None, reference_files: list[Path] | None, options: dict | None) -> VideoResult:
        return VideoResult(video_paths=[], metadata={"error": "video generation not supported via webapi"})
