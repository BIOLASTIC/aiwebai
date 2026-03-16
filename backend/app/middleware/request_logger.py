import asyncio
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from backend.app.db.engine import AsyncSessionLocal
from backend.app.db.models import RequestLog
from backend.app.logging.structured import logger


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only log API and admin requests
        path = request.url.path
        if not any(path.startswith(p) for p in ("/v1/", "/native/", "/admin/")):
            return await call_next(request)

        start_time = time.time()
        response = await call_next(request)
        latency_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "API Request",
            path=path,
            method=request.method,
            status_code=response.status_code,
            latency_ms=latency_ms,
        )

        # Fire-and-forget — write to DB without blocking the response
        asyncio.create_task(
            _persist_log(
                endpoint=path,
                status_code=response.status_code,
                latency_ms=latency_ms,
            )
        )

        return response


async def _persist_log(*, endpoint: str, status_code: int, latency_ms: int) -> None:
    try:
        async with AsyncSessionLocal() as db:
            log = RequestLog(
                endpoint=endpoint,
                status_code=status_code,
                latency_ms=latency_ms,
            )
            db.add(log)
            await db.commit()
    except Exception as exc:
        logger.error("Failed to persist request log", error=str(exc))
