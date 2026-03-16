from typing import Dict, Any, Optional
from sqlalchemy.future import select
from backend.app.db.engine import AsyncSessionLocal
from backend.app.db.models import RequestLog
from backend.app.logging.structured import logger

class AnalyticsCollector:
    @staticmethod
    async def log_request(
        user_id: int,
        account_id: Optional[int],
        provider: str,
        endpoint: str,
        model_alias: str,
        resolved_model: str,
        feature_type: str,
        latency_ms: int,
        status_code: int,
        stream_mode: bool = False
    ):
        async with AsyncSessionLocal() as db:
            log = RequestLog(
                user_id=user_id,
                account_id=account_id,
                provider=provider,
                endpoint=endpoint,
                model_alias=model_alias,
                resolved_model=resolved_model,
                feature_type=feature_type,
                latency_ms=latency_ms,
                status_code=status_code,
                stream_mode=stream_mode
            )
            db.add(log)
            await db.commit()
            logger.info("Request logged for analytics", user_id=user_id, endpoint=endpoint)
