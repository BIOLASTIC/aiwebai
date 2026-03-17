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

# Map provider string → adapter class
_ADAPTER_TYPE_MAP: Dict[str, type] = {
    "webapi": WebApiAdapter,
    "mcpcli": McpCliAdapter,
}

# Human-readable names for error messages
_ADAPTER_DISPLAY_NAMES: Dict[type, str] = {
    WebApiAdapter: "webapi",
    McpCliAdapter: "mcpcli",
}

# Capabilities not supported by each adapter type
_ADAPTER_MISSING_CAPS: Dict[type, Dict[str, str]] = {
    WebApiAdapter: {
        "video": "Video generation is not supported by the gemini-webapi adapter.",
        "music": "Music generation is not supported by the gemini-webapi adapter.",
        "research": "Deep research is not supported by the gemini-webapi adapter.",
    },
    McpCliAdapter: {},
}


def _resolve_forced_adapter(adapter_param: str | None, all_adapters: List[BaseAdapter]) -> BaseAdapter | None:
    """Return a specific adapter instance based on the forced adapter name, or None if not applicable."""
    if adapter_param is None:
        return None
    cls = _ADAPTER_TYPE_MAP.get(adapter_param.lower())
    if cls is None:
        raise HTTPException(status_code=400, detail=f"Unknown adapter '{adapter_param}'. Valid values: webapi, mcpcli.")
    for a in all_adapters:
        if isinstance(a, cls):
            return a
    raise HTTPException(
        status_code=400,
        detail=(
            f"Adapter '{adapter_param}' is not available. "
            "No active account of that type is configured."
        ),
    )


def _assert_capability(adapter: BaseAdapter, capability: str) -> None:
    """Raise HTTPException if the adapter does not support the requested capability."""
    missing = _ADAPTER_MISSING_CAPS.get(type(adapter), {})
    reason = missing.get(capability)
    if reason:
        name = _ADAPTER_DISPLAY_NAMES.get(type(adapter), str(type(adapter)))
        raise HTTPException(
            status_code=422,
            detail=f"Adapter '{name}' cannot handle '{capability}': {reason}",
        )


class AdapterRouter:
    def __init__(self) -> None:
        self.mock_adapter = WebApiAdapter(mock_mode=True)

    def get_best_adapter(self, capability: str, model_alias: str | None = None) -> BaseAdapter:
        adapters = account_manager.get_all_adapters()
        if not adapters:
            return self.mock_adapter

        # Priority 1: If model is imagen or veo, prefer McpCliAdapter
        if model_alias and ("imagen" in model_alias.lower() or "veo" in model_alias.lower()):
            for adapter in adapters:
                if isinstance(adapter, McpCliAdapter):
                    return adapter

        if capability == "chat":
            for adapter in adapters:
                if isinstance(adapter, WebApiAdapter):
                    return adapter
        if capability == "image_edit":
            # Image editing requires webapi (Gemini Advanced) — mcpcli cannot edit images
            for adapter in adapters:
                if isinstance(adapter, WebApiAdapter):
                    return adapter
        if capability == "image":
            # Prefer McpCliAdapter for generation — webapi requires Gemini Advanced subscription
            for adapter in adapters:
                if isinstance(adapter, McpCliAdapter):
                    return adapter
            for adapter in adapters:
                if isinstance(adapter, WebApiAdapter):
                    return adapter
        if capability in {"video", "music", "research"}:
            for adapter in adapters:
                if isinstance(adapter, McpCliAdapter):
                    return adapter
        return adapters[0]

    async def refresh_catalog(self, db: AsyncSession) -> None:
        await model_registry.discover_models()

    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        from backend.app.accounts.manager import account_manager
        all_adapters = account_manager.get_all_adapters() or [self.mock_adapter]
        # For mcpcli-only models, skip webapi adapters
        mcpcli_only = {"imagen-3.0", "veo-2.0", "lyria-1.0"}
        if request.model and request.model in mcpcli_only:
            candidates = [a for a in all_adapters if isinstance(a, McpCliAdapter)] or all_adapters
        else:
            # Try all webapi adapters first (multi-account fallback for rate limits), then mcpcli
            candidates = (
                [a for a in all_adapters if isinstance(a, WebApiAdapter)]
                + [a for a in all_adapters if isinstance(a, McpCliAdapter)]
            ) or all_adapters

        errors: Dict[str, str] = {}
        for adapter in candidates:
            try:
                response = await adapter.chat_completion(request)
                # Inject adapter metadata
                adapter_name = _ADAPTER_DISPLAY_NAMES.get(type(adapter), "unknown")
                response.metadata["adapter"] = adapter_name
                # Find account label if possible
                for aid, adpt in account_manager.adapters.items():
                    if adpt is adapter:
                        from backend.app.db.engine import AsyncSessionLocal
                        async with AsyncSessionLocal() as db:
                            from backend.app.db.models import Account
                            acct = await db.get(Account, aid)
                            if acct:
                                response.metadata["account"] = acct.label
                        break
                return response
            except Exception as exc:
                name = _ADAPTER_DISPLAY_NAMES.get(type(adapter), str(type(adapter)))
                errors[name] = str(exc)
        tried = "; ".join(f"{k}: {v}" for k, v in errors.items()) if errors else "no adapters available"
        raise HTTPException(status_code=502, detail=f"No adapter could complete chat. {tried}")

    async def stream_chat(self, request: ChatCompletionRequest) -> AsyncGenerator[Dict[str, Any], None]:
        all_adapters = account_manager.get_all_adapters() or [self.mock_adapter]
        mcpcli_only = {"imagen-3.0", "veo-2.0", "lyria-1.0"}
        if request.model and request.model in mcpcli_only:
            candidates = [a for a in all_adapters if isinstance(a, McpCliAdapter)] or all_adapters
        else:
            candidates = (
                [a for a in all_adapters if isinstance(a, WebApiAdapter)]
                + [a for a in all_adapters if isinstance(a, McpCliAdapter)]
            ) or all_adapters

        last_exc: Exception | None = None
        for adapter in candidates:
            try:
                async for chunk in adapter.stream_chat(request):
                    yield chunk
                return  # success — stop trying other adapters
            except Exception as exc:
                last_exc = exc
        if last_exc:
            raise last_exc

    async def generate_image(self, request: ImageGenerationRequest, adapter: str | None = None) -> Dict[str, Any]:
        all_adapters = account_manager.get_all_adapters() or [self.mock_adapter]

        # Forced adapter path
        if adapter is not None:
            forced = _resolve_forced_adapter(adapter, all_adapters)
            _assert_capability(forced, "image")
            return await forced.generate_image(request)

        # Build ordered list: account-specific first, then model-preference, then rest
        ordered: List[BaseAdapter] = []
        if request.account_id:
            acct_adapter = account_manager.get_adapter_for_account(request.account_id)
            if acct_adapter:
                ordered.append(acct_adapter)

        # Route by model first (imagen -> McpCliAdapter, others -> WebApiAdapter)
        preferred_adapter = self.get_best_adapter("image", request.model)
        if preferred_adapter not in ordered:
            ordered.append(preferred_adapter)
        for a in all_adapters:
            if a not in ordered:
                ordered.append(a)

        errors: Dict[str, str] = {}
        for adpt in ordered:
            try:
                result = await adpt.generate_image(request)
                if result.get("data"):
                    return result
            except Exception as exc:
                name = _ADAPTER_DISPLAY_NAMES.get(type(adpt), str(type(adpt)))
                errors[name] = str(exc)

        tried = "; ".join(f"{k}: {v}" for k, v in errors.items()) if errors else "no adapters available"
        raise HTTPException(
            status_code=502,
            detail=f"No adapter could generate image. {tried}",
        )

    async def edit_image(self, request: ImageGenerationRequest, reference_file: bytes | None = None, adapter: str | None = None) -> Dict[str, Any]:
        all_adapters = account_manager.get_all_adapters() or [self.mock_adapter]

        if adapter is not None:
            forced = _resolve_forced_adapter(adapter, all_adapters)
            _assert_capability(forced, "image")
            return await forced.edit_image(request, reference_file)

        # Build ordered list: account-specific first, then model preference, then rest
        ordered: List[BaseAdapter] = []
        if request.account_id:
            acct_adapter = account_manager.get_adapter_for_account(request.account_id)
            if acct_adapter:
                ordered.append(acct_adapter)

        preferred_adapter = self.get_best_adapter("image_edit", request.model)
        if preferred_adapter not in ordered:
            ordered.append(preferred_adapter)
        for a in all_adapters:
            if a not in ordered:
                ordered.append(a)

        errors: Dict[str, str] = {}
        for adpt in ordered:
            try:
                result = await adpt.edit_image(request, reference_file)
                if result.get("data"):
                    return result
            except Exception as exc:
                name = _ADAPTER_DISPLAY_NAMES.get(type(adpt), str(type(adpt)))
                errors[name] = str(exc)

        tried = "; ".join(f"{k}: {v}" for k, v in errors.items()) if errors else "no adapters available"
        raise HTTPException(status_code=502, detail=f"No adapter could edit image. {tried}")

    async def generate_video(self, prompt: str, model: str | None, account_id: int | None, reference_files: list[Path] | None, options: dict | None, adapter: str | None = None):
        all_adapters = account_manager.get_all_adapters() or [self.mock_adapter]

        if adapter is not None:
            forced = _resolve_forced_adapter(adapter, all_adapters)
            _assert_capability(forced, "video")
            return await forced.generate_video(prompt, model, account_id, reference_files, options)

        if account_id:
            acct_adapter = account_manager.get_adapter_for_account(account_id)
            if acct_adapter:
                return await acct_adapter.generate_video(prompt, model, account_id, reference_files, options)

        best = self.get_best_adapter("video", model)
        errors: Dict[str, str] = {}
        for adpt in [best] + [a for a in all_adapters if a is not best]:
            try:
                return await adpt.generate_video(prompt, model, account_id, reference_files, options)
            except Exception as exc:
                name = _ADAPTER_DISPLAY_NAMES.get(type(adpt), str(type(adpt)))
                errors[name] = str(exc)
        tried = "; ".join(f"{k}: {v}" for k, v in errors.items()) if errors else "no adapters available"
        raise HTTPException(status_code=502, detail=f"No adapter could generate video. {tried}")

    async def generate_music(self, prompt: str, account_id: int | None = None, adapter: str | None = None) -> str:
        all_adapters = account_manager.get_all_adapters() or [self.mock_adapter]

        if adapter is not None:
            forced = _resolve_forced_adapter(adapter, all_adapters)
            _assert_capability(forced, "music")
            return await forced.generate_music(prompt)

        if account_id:
            acct_adapter = account_manager.get_adapter_for_account(account_id)
            if acct_adapter:
                return await acct_adapter.generate_music(prompt)

        best = self.get_best_adapter("music")
        errors: Dict[str, str] = {}
        for adpt in [best] + [a for a in all_adapters if a is not best]:
            try:
                return await adpt.generate_music(prompt)
            except Exception as exc:
                name = _ADAPTER_DISPLAY_NAMES.get(type(adpt), str(type(adpt)))
                errors[name] = str(exc)
        tried = "; ".join(f"{k}: {v}" for k, v in errors.items()) if errors else "no adapters available"
        raise HTTPException(status_code=502, detail=f"No adapter could generate music. {tried}")

    async def generate_research(self, prompt: str, account_id: int | None = None, adapter: str | None = None) -> str:
        all_adapters = account_manager.get_all_adapters() or [self.mock_adapter]

        if adapter is not None:
            forced = _resolve_forced_adapter(adapter, all_adapters)
            _assert_capability(forced, "research")
            return await forced.deep_research(prompt)

        if account_id:
            acct_adapter = account_manager.get_adapter_for_account(account_id)
            if acct_adapter:
                return await acct_adapter.deep_research(prompt)

        best = self.get_best_adapter("research")
        errors: Dict[str, str] = {}
        for adpt in [best] + [a for a in all_adapters if a is not best]:
            try:
                return await adpt.deep_research(prompt)
            except Exception as exc:
                name = _ADAPTER_DISPLAY_NAMES.get(type(adpt), str(type(adpt)))
                errors[name] = str(exc)
        tried = "; ".join(f"{k}: {v}" for k, v in errors.items()) if errors else "no adapters available"
        raise HTTPException(status_code=502, detail=f"No adapter could generate research. {tried}")


adapter_router = AdapterRouter()
