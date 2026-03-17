from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import select

from backend.app.accounts.manager import account_manager
from backend.app.adapters.mcpcli_adapter import McpCliAdapter
from backend.app.adapters.webapi_adapter import KNOWN_WEBAPI_MODELS
from backend.app.db.engine import AsyncSessionLocal
from backend.app.db.models import Model
from backend.app.logging.structured import logger


LATEST_ALIASES: Dict[str, str] = {
    "gemini-pro-latest": "gemini-2.5-pro",
    "gemini-flash-latest": "gemini-2.5-flash",
    "gemini-thinking-latest": "gemini-2.0-flash-thinking-exp",
    "gemini-image-latest": "imagen-3.0",
    "gemini-video-latest": "veo-2.0",
    "gemini-music-latest": "lyria-1.0",
    "gemini-research-latest": "gemini-research",
}


class ModelRegistry:
    @staticmethod
    async def discover_models() -> None:
        adapters = account_manager.get_all_adapters()
        if not adapters:
            adapters = [McpCliAdapter()]
            sources = [(KNOWN_WEBAPI_MODELS, "webapi"), (await adapters[0].list_models(), "mcpcli")]
        else:
            sources = []
            for adapter in adapters:
                provider = "webapi" if "WebApi" in type(adapter).__name__ else "mcpcli"
                try:
                    sources.append((await adapter.list_models(), provider))
                except Exception as exc:
                    logger.error("Failed to discover models", adapter=provider, error=str(exc))
        for models, provider in sources:
            for model in models:
                await ModelRegistry._sync_model(model, provider)

    @staticmethod
    async def _sync_model(model_data: Dict[str, Any], provider: str) -> None:
        async with AsyncSessionLocal() as db:
            model_id = model_data["id"]
            result = await db.execute(select(Model).where(Model.provider_model_name == model_id))
            model = result.scalars().first()
            if not model:
                model = Model(
                    provider_model_name=model_id,
                    display_name=model_data.get("display_name", model_id),
                    family=model_data.get("family", "gemini"),
                    source_provider=model_data.get("source", provider),
                    status="active",
                    capabilities=model_data.get("capabilities", {}),
                )
                db.add(model)
            else:
                model.display_name = model_data.get("display_name", model.display_name)
                model.family = model_data.get("family", model.family)
                model.source_provider = model_data.get("source", provider)
                model.capabilities = model_data.get("capabilities", model.capabilities)
                model.status = "active"
            await db.commit()

    @staticmethod
    async def resolve_alias(alias: str) -> str:
        return LATEST_ALIASES.get(alias, alias)


model_registry = ModelRegistry()
