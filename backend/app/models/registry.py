from typing import Dict, Any
from sqlalchemy.future import select
from backend.app.db.engine import AsyncSessionLocal
from backend.app.db.models import Model
from backend.app.accounts.manager import account_manager
from backend.app.logging.structured import logger
import datetime


class ModelRegistry:
    @staticmethod
    async def discover_models() -> None:
        """Fetch models from all active adapters and upsert into DB."""
        adapters = account_manager.get_all_adapters()

        if not adapters:
            # Seed static lists even when no accounts are configured
            logger.info("No adapters active — seeding static model list from webapi adapter")
            from backend.app.adapters.webapi_adapter import KNOWN_WEBAPI_MODELS
            from backend.app.adapters.mcpcli_adapter import McpCliAdapter
            for m in KNOWN_WEBAPI_MODELS:
                await ModelRegistry._sync_model(m, "webapi")
            dummy = McpCliAdapter()
            for m in await dummy.list_models():
                await ModelRegistry._sync_model(m, "mcpcli")
            return

        seen: set = set()
        for adapter in adapters:
            adapter_name = "webapi" if "WebApi" in type(adapter).__name__ else "mcpcli"
            try:
                models = await adapter.list_models()
                for m in models:
                    key = m["id"]
                    if key not in seen:
                        seen.add(key)
                        await ModelRegistry._sync_model(m, adapter_name)
            except Exception as e:
                logger.error("Failed to discover models", adapter=adapter_name, error=str(e))

    @staticmethod
    async def _sync_model(model_data: Dict[str, Any], adapter_name: str) -> None:
        async with AsyncSessionLocal() as db:
            model_id = model_data["id"]
            result = await db.execute(select(Model).where(Model.provider_model_name == model_id))
            model = result.scalars().first()

            if not model:
                model = Model(
                    provider_model_name=model_id,
                    display_name=model_data.get("display_name", model_id),
                    family=model_data.get("family", "gemini"),
                    source_provider=model_data.get("source", adapter_name),
                    status="active",
                    discovered_at=datetime.datetime.utcnow(),
                )
                db.add(model)
            else:
                model.display_name = model_data.get("display_name", model.display_name)
                model.family = model_data.get("family", model.family)
                model.status = "active"
            await db.commit()

    @staticmethod
    async def resolve_alias(alias: str) -> str:
        """Resolve a human-friendly alias to a concrete model id."""
        _aliases: Dict[str, str] = {
            "gemini-pro-latest": "gemini-1.5-pro",
            "gemini-flash-latest": "gemini-2.0-flash",
            "gemini-thinking-latest": "gemini-2.0-flash-thinking-exp",
            "gemini-image-latest": "imagen-3.0",
            "gemini-video-latest": "veo-2.0",
            "gemini-music-latest": "lyria-1.0",
        }
        return _aliases.get(alias, alias)


model_registry = ModelRegistry()
