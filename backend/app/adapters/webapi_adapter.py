from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.app.adapters.base import BaseAdapter
from backend.app.schemas.native import ImageGenerationRequest, VideoResult
from backend.app.utils.media import download_to_uploads
from backend.app.schemas.openai import ChatCompletionChoice, ChatCompletionRequest, ChatCompletionResponse, ChatMessage

KNOWN_WEBAPI_MODELS: List[Dict[str, Any]] = [
    {"id": "gemini-2.5-pro", "display_name": "Gemini 2.5 Pro", "family": "pro", "capabilities": {"chat": True, "thinking": True}},
    {"id": "gemini-2.5-flash", "display_name": "Gemini 2.5 Flash", "family": "flash", "capabilities": {"chat": True, "streaming": True}},
    {"id": "gemini-2.0-flash", "display_name": "Gemini 2.0 Flash", "family": "flash", "capabilities": {"chat": True, "streaming": True, "images": True}},
    {"id": "gemini-2.0-flash-thinking-exp", "display_name": "Gemini Thinking", "family": "thinking", "capabilities": {"chat": True, "thinking": True}},
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
                raise Exception("Account credentials are invalid or expired. Please re-import your browser session in the Admin panel.")
            else:
                self.chat_sessions[key] = self.client.start_chat()
        return self.chat_sessions[key]

    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        last_message = request.messages[-1].content if request.messages else ""
        if self.mock_mode or not self.client:
            raise Exception("Account credentials are invalid or expired. Please re-import your browser session in the Admin panel.")
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
            raise Exception("Account credentials are invalid or expired. Please re-import your browser session in the Admin panel.")
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
            raise Exception("Account credentials are invalid or expired. Please re-import your browser session in the Admin panel.")
        await self.init()
        # Map our standard model IDs → webapi internal names; mcpcli-only models use default
        _WEBAPI_MODEL_MAP: Dict[str, str] = {
            "gemini-2.5-pro": "gemini-3.1-pro",
            "gemini-2.5-flash": "gemini-3.0-flash",
            "gemini-2.0-flash": "gemini-3.0-flash",
            "gemini-2.0-flash-thinking-exp": "gemini-3.0-flash-thinking",
        }
        _MCPCLI_ONLY = {"imagen-3.0", "gemini-image-latest", "veo-2.0", "veo-pro"}
        webapi_model: Optional[str] = None
        if request.model and request.model not in _MCPCLI_ONLY:
            webapi_model = _WEBAPI_MODEL_MAP.get(request.model)
        kwargs: Dict[str, Any] = {}
        if webapi_model:
            kwargs["model"] = webapi_model
        # Gemini web needs an explicit image generation instruction to trigger Imagen
        _img_triggers = ("generate", "create", "draw", "make", "render", "produce", "paint", "design")
        if not any(w in prompt.lower() for w in _img_triggers):
            gen_prompt = f"Generate an image of: {prompt}"
        else:
            gen_prompt = prompt
        output = await self.client.generate_content(gen_prompt, **kwargs)
        images = getattr(output, "images", []) or []
        urls = []
        for image in images:
            url = getattr(image, "url", None)
            if url:
                # Download locally to avoid cloud dependency
                local_url = await download_to_uploads(url)
                urls.append({"url": local_url})
        if not urls:
            response_text = getattr(output, "text", "") or ""
            if "not available" in response_text.lower() or "can't" in response_text.lower() or "cannot" in response_text.lower():
                raise Exception(
                    "Image generation is not available for this Google account. "
                    "You likely need a Gemini Advanced subscription. "
                    "Alternatively, run 'gemcli login' in the terminal to enable image generation via the mcpcli account."
                )
            raise Exception(
                "Gemini returned a response but no images were generated. "
                "The prompt may have been blocked by safety filters, or image generation may not be available for this account."
            )
        return {"created": int(time.time()), "data": urls}

    async def generate_video(
        self,
        prompt: str,
        model: str | None,
        account_id: int | None,
        reference_files: list[Path] | None,
        options: dict | None,
    ) -> VideoResult:
        if self.mock_mode or not self.client:
            raise Exception("Account credentials are invalid or expired. Please re-import your browser session in the Admin panel.")
        
        await self.init()
        output = await self.client.generate_content(prompt)

        videos = getattr(output, "videos", []) or []
        local_url_strings: list[str] = []

        for video in videos:
            url = getattr(video, "url", None)
            if url:
                local_url = await download_to_uploads(url)
                local_url_strings.append(local_url)

        if not local_url_strings:
            raise Exception("Gemini returned a response but no video results were found. Note: Video generation is experimental in the Web interface.")

        # Store url string in metadata to avoid Path() mangling http:// into http:/
        return VideoResult(
            video_paths=[Path(u) for u in local_url_strings],
            metadata={"model": "gemini-2.0-flash", "url": local_url_strings[0]},
        )

    async def list_models(self) -> List[Dict[str, Any]]:
        return KNOWN_WEBAPI_MODELS

    async def health_check(self) -> bool:
        if self.mock_mode:
            return False
        try:
            await self.init()
            await self.client.generate_content("hi")
            return True
        except Exception:
            return False
