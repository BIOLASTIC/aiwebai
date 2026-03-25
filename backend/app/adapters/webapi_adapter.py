from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.app.adapters.base import BaseAdapter
from backend.app.config import settings
from backend.app.schemas.native import ImageGenerationRequest, VideoResult
from backend.app.schemas.openai import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
)

# ---------------------------------------------------------------------------
# gemini-webapi Model enum import
# ---------------------------------------------------------------------------
try:
    from gemini_webapi import GeminiClient  # type: ignore
    from gemini_webapi.constants import Model as GeminiModel  # type: ignore
    from gemini_webapi.types.image import GeneratedImage  # type: ignore
except Exception:  # pragma: no cover
    GeminiClient = None  # type: ignore
    GeminiModel = None  # type: ignore
    GeneratedImage = None  # type: ignore

# ---------------------------------------------------------------------------
# User-facing model IDs exposed by this adapter
# ---------------------------------------------------------------------------
KNOWN_WEBAPI_MODELS: List[Dict[str, Any]] = [
    {
        "id": "gemini-3.0-pro",
        "display_name": "Gemini 3.0 Pro",
        "family": "pro",
        "capabilities": {"chat": True, "images": True, "image_edit": True, "thinking": True, "streaming": True},
    },
    {
        "id": "gemini-3.0-flash",
        "display_name": "Gemini 3.0 Flash",
        "family": "flash",
        "capabilities": {"chat": True, "images": True, "image_edit": True, "streaming": True},
    },
    {
        "id": "gemini-3.0-flash-thinking",
        "display_name": "Gemini 3.0 Flash Thinking",
        "family": "thinking",
        "capabilities": {"chat": True, "thinking": True, "streaming": True},
    },
]


# ---------------------------------------------------------------------------
# Map user-facing IDs → gemini-webapi internal Model enum values
# Also includes legacy aliases so existing accounts keep working.
# ---------------------------------------------------------------------------
def _build_model_map() -> Dict[str, Any]:
    if GeminiModel is None:
        return {}
    return {
        # Current model IDs
        "gemini-3.0-pro": GeminiModel.G_3_1_PRO,
        "gemini-3.0-flash": GeminiModel.G_3_0_FLASH,
        "gemini-3.0-flash-thinking": GeminiModel.G_3_0_FLASH_THINKING,
        # Legacy aliases → map to closest current model
        "gemini-2.5-pro": GeminiModel.G_3_1_PRO,
        "gemini-2.5-flash": GeminiModel.G_3_0_FLASH,
        "gemini-2.0-flash": GeminiModel.G_3_0_FLASH,
        "gemini-2.0-flash-thinking-exp": GeminiModel.G_3_0_FLASH_THINKING,
        "gemini-1.5-pro": GeminiModel.G_3_1_PRO,
        "gemini-1.5-flash": GeminiModel.G_3_0_FLASH,
    }


_WEBAPI_MODEL_MAP: Dict[str, Any] = _build_model_map()

# Models served only by mcpcli; never route to webapi for these
_MCPCLI_ONLY_MODELS = {"imagen-3.0", "gemini-image-latest", "veo-2.0", "veo-pro", "lyria-1.0"}

# Trigger words that cause Gemini to invoke ImageFX image generation
_IMG_TRIGGERS = ("generate", "create", "draw", "make", "render", "produce", "paint", "design", "show me", "illustrate")


def _uploads_dir() -> Path:
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    d = project_root / "uploads"
    d.mkdir(exist_ok=True)
    return d


def _local_url(filename: str) -> str:
    from backend.app.config import settings

    return f"{settings.BASE_URL}/uploads/{filename}"


class WebApiAdapter(BaseAdapter):
    def __init__(
        self,
        secure_1psid: str | None = None,
        secure_1psidts: str | None = None,
        mock_mode: bool | None = None,
    ):
        self._secure_1psid = secure_1psid
        self._secure_1psidts = secure_1psidts
        self.mock_mode = bool(mock_mode) if mock_mode is not None else not (secure_1psid and GeminiClient)
        self.client: Any = GeminiClient(secure_1psid, secure_1psidts) if (GeminiClient and secure_1psid) else None
        self._initialized = False
        # chat_sessions keyed by "{session_id}:{model_id}" so different models get separate chats
        self.chat_sessions: Dict[str, Any] = {}

    def _resolve_model(self, model_id: str | None) -> Any:
        """Resolve user-facing model ID to gemini-webapi internal Model enum."""
        if not model_id:
            return None
        return _WEBAPI_MODEL_MAP.get(model_id)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def init(self) -> None:
        if self.mock_mode or not self.client or self._initialized:
            return
        try:
            await self.client.init(timeout=30, auto_close=False, close_delay=300, auto_refresh=False)
            self._initialized = True
        except Exception as e:
            err = str(e).lower()
            if any(w in err for w in ("401", "unauthorized", "cookie", "expired", "auth")):
                raise Exception(
                    "Gemini session expired. Please re-import fresh browser cookies for this account "
                    "in Admin → Accounts → Edit → Credentials."
                )
            raise

    def _require_client(self) -> None:
        if not self.mock_mode and not self.client:
            raise Exception(
                "Account credentials are invalid or expired. Please re-import your browser session in the Admin panel."
            )

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------

    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        self._require_client()
        if self.mock_mode:
            return ChatCompletionResponse(
                id=f"chatcmpl-{uuid.uuid4()}",
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=f"MOCK RESPONSE: I am {request.model} running in mock mode. How can I help you with your Paperclip work today?",
                        ),
                        finish_reason="stop",
                    )
                ],
                usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            )

        await self.init()

        model_enum = self._resolve_model(request.model)
        session_key = f"{request.user or 'default'}:{request.model or 'default'}"

        if session_key not in self.chat_sessions:
            kwargs: Dict[str, Any] = {}
            if model_enum is not None:
                kwargs["model"] = model_enum
            self.chat_sessions[session_key] = self.client.start_chat(**kwargs)

        session = self.chat_sessions[session_key]
        last_message = request.messages[-1].content if request.messages else ""
        output = await session.send_message(last_message)
        text = getattr(output, "text", str(output))

        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4()}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=text),
                    finish_reason="stop",
                )
            ],
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        )

    async def stream_chat(self, request: ChatCompletionRequest) -> AsyncGenerator[Dict[str, Any], None]:
        self._require_client()
        if self.mock_mode:
            chunk_id = f"chatcmpl-{uuid.uuid4()}"
            created = int(time.time())
            content = f"MOCK STREAM: I am {request.model}."
            yield {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": request.model,
                "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}],
            }
            yield {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": request.model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            return

        await self.init()

        model_enum = self._resolve_model(request.model)
        session_key = f"{request.user or 'default'}:{request.model or 'default'}"

        if session_key not in self.chat_sessions:
            kwargs: Dict[str, Any] = {}
            if model_enum is not None:
                kwargs["model"] = model_enum
            self.chat_sessions[session_key] = self.client.start_chat(**kwargs)

        session = self.chat_sessions[session_key]
        chunk_id = f"chatcmpl-{uuid.uuid4()}"
        created = int(time.time())
        last_message = request.messages[-1].content if request.messages else ""

        async for chunk in session.send_message_stream(last_message):
            delta = getattr(chunk, "text_delta", None) or getattr(chunk, "text", "")
            yield {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": request.model,
                "choices": [{"index": 0, "delta": {"content": delta}, "finish_reason": None}],
            }
        yield {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": request.model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }

    # ------------------------------------------------------------------
    # Image generation
    # ------------------------------------------------------------------

    async def generate_image(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        self._require_client()
        if self.mock_mode:
            return {
                "created": int(time.time()),
                "data": [{"url": "https://placehold.co/1024x1024/png?text=Mock+Image+for+" + request.prompt[:20]}],
            }

        await self.init()

        prompt = request.prompt.strip()

        # Gemini needs explicit trigger words to invoke ImageFX (Imagen)
        if not any(w in prompt.lower() for w in _IMG_TRIGGERS):
            gen_prompt = f"Generate an image of: {prompt}"
        else:
            gen_prompt = prompt

        # For image generation always use UNSPECIFIED so Gemini can route to ImageFX/Imagen.
        # Passing a specific text model (e.g. G_3_1_PRO) prevents image generation.
        kwargs: Dict[str, Any] = {}
        if GeminiModel is not None:
            kwargs["model"] = GeminiModel.UNSPECIFIED

        import asyncio

        try:
            output = await asyncio.wait_for(
                self.client.generate_content(gen_prompt, **kwargs),
                timeout=90,
            )
        except asyncio.TimeoutError:
            raise Exception("Gemini image generation timed out (90s). Try again or switch to the mcpcli backend.")
        images = getattr(output, "images", []) or []

        urls = []
        uploads = _uploads_dir()

        for image in images:
            try:
                # Use the library's own save() which handles cookies for GeneratedImage
                saved_path = await image.save(path=str(uploads), verbose=False)
                if saved_path:
                    filename = Path(saved_path).name
                    urls.append({"url": _local_url(filename)})
            except Exception:
                # Fallback: download via raw URL (works for WebImage)
                raw_url = getattr(image, "url", None)
                if raw_url:
                    from backend.app.utils.media import download_to_uploads

                    local = await download_to_uploads(raw_url)
                    urls.append({"url": local})

        if not urls:
            response_text = getattr(output, "text", "") or ""
            rlt = response_text.lower()
            if any(
                w in rlt
                for w in (
                    "not available",
                    "can't generate",
                    "cannot generate",
                    "subscription",
                    "upgrade",
                    "advanced",
                    "premium",
                    "gemini advanced",
                    "i'm not able to generate",
                    "i am not able to generate",
                    "i can't create",
                    "i cannot create",
                    "unable to generate",
                    "unable to create",
                    "don't have the ability",
                    "do not have the ability",
                    "not designed to generate images",
                    "can't directly generate",
                )
            ):
                raise Exception(
                    "Image generation is not available for this Google account. "
                    "You likely need a Gemini Advanced subscription. "
                    "Alternatively, run 'gemcli login' in the terminal to enable image generation via the mcpcli account."
                )
            if any(w in rlt for w in ("expired", "session", "sign in", "log in", "authenticate")):
                raise Exception(
                    "Gemini session expired. Please re-import fresh browser cookies for this account in Admin → Accounts."
                )
            raise Exception(
                "Image generation is not available for this Google account. "
                "You likely need a Gemini Advanced subscription to use image generation via the web API. "
                "The system will automatically retry with the mcpcli backend if one is configured."
            )

        return {"created": int(time.time()), "data": urls}

    # ------------------------------------------------------------------
    # Image editing  (override base which delegates to generate_image)
    # ------------------------------------------------------------------

    async def edit_image(self, request: ImageGenerationRequest, reference_file: bytes | None = None) -> Dict[str, Any]:
        self._require_client()
        if self.mock_mode:
            return {
                "created": int(time.time()),
                "data": [{"url": "https://placehold.co/1024x1024/png?text=Mock+Edited+Image"}],
            }

        await self.init()

        prompt = request.prompt.strip()

        # Use UNSPECIFIED model so Gemini can route to ImageFX/Imagen for image editing
        kwargs: Dict[str, Any] = {}
        if GeminiModel is not None:
            kwargs["model"] = GeminiModel.UNSPECIFIED

        files: list[Any] | None = None
        if reference_file:
            import io

            files = [io.BytesIO(reference_file)]

        _EDIT_WORDS = (
            "edit",
            "change",
            "modify",
            "remove",
            "replace",
            "add",
            "adjust",
            "make",
            "turn",
            "convert",
            "apply",
            "color",
            "black",
            "white",
            "blur",
            "crop",
        )
        edit_prompt = prompt if any(w in prompt.lower() for w in _EDIT_WORDS) else f"Edit this image: {prompt}"
        try:
            output = await self.client.generate_content(edit_prompt, files=files, **kwargs)
        except Exception as exc:
            err = str(exc).lower()
            if any(w in err for w in ("timeout", "timed out", "time out")):
                raise Exception(
                    "Image editing timed out. Gemini was still processing — try again (it usually succeeds on a retry)."
                ) from exc
            raise
        images = getattr(output, "images", []) or []

        urls = []
        uploads = _uploads_dir()

        for image in images:
            try:
                saved_path = await image.save(path=str(uploads), verbose=False)
                if saved_path:
                    filename = Path(saved_path).name
                    urls.append({"url": _local_url(filename)})
            except Exception:
                raw_url = getattr(image, "url", None)
                if raw_url:
                    from backend.app.utils.media import download_to_uploads

                    local = await download_to_uploads(raw_url)
                    urls.append({"url": local})

        if not urls:
            raise Exception(
                "Image editing returned no results. "
                "Ensure you have a Gemini Advanced subscription and that the reference image is valid."
            )

        return {"created": int(time.time()), "data": urls}

    # ------------------------------------------------------------------
    # Video generation
    # ------------------------------------------------------------------

    async def generate_video(
        self,
        prompt: str,
        model: str | None,
        account_id: int | None,
        reference_files: list[Path] | None,
        options: dict | None,
    ) -> VideoResult:
        self._require_client()
        await self.init()

        output = await self.client.generate_content(prompt)
        videos = getattr(output, "videos", []) or []
        local_urls: list[str] = []

        for video in videos:
            url = getattr(video, "url", None)
            if url:
                from backend.app.utils.media import download_to_uploads

                local_url = await download_to_uploads(url)
                local_urls.append(local_url)

        if not local_urls:
            raise Exception(
                "Gemini returned no video results. Note: Video generation is experimental in the web interface."
            )

        return VideoResult(
            video_paths=[Path(u) for u in local_urls],
            metadata={"model": model or "gemini-3.0-flash", "url": local_urls[0]},
        )

    async def get_limits(self) -> Dict[str, Any]:
        """WebAPI adapter doesn't directly support usage limits retrieval in the same way."""
        return {
            "status": "not_supported_by_adapter",
            "message": "Usage limits checking is primarily supported via the mcpcli adapter.",
        }

    # ------------------------------------------------------------------
    # Model listing & health
    # ------------------------------------------------------------------

    async def list_models(self) -> List[Dict[str, Any]]:
        return KNOWN_WEBAPI_MODELS

    async def health_check(self) -> bool:
        if self.mock_mode or not self.client:
            return False
        try:
            await self.init()
            await self.client.generate_content("hi")
            return True
        except Exception:
            return False
