"""
Request Logger Middleware - ASGI-level response capture
"""

import asyncio
import json
import time


class RequestLoggerASGIMiddleware:
    """ASGI middleware that wraps the entire app to capture responses"""

    def __init__(self, app):
        self.app = app
        # Store for later
        self._db_session = None
        self._RequestLog = None
        self._logger = None

    def _get_deps(self):
        from backend.app.db.engine import AsyncSessionLocal
        from backend.app.db.models import RequestLog
        from backend.app.logging.structured import logger

        self._AsyncSessionLocal = AsyncSessionLocal
        self._RequestLog = RequestLog
        self._logger = logger

    async def __call__(self, scope, receive, send):
        if self._logger is None:
            self._get_deps()

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # Only log API paths
        if not any(path.startswith(p) for p in ("/v1/", "/native/", "/admin/")):
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")

        # Get request headers
        request_headers = None
        try:
            headers_dict = {k.decode(): v.decode() for k, v in scope.get("headers", [])}
            request_headers = json.dumps(headers_dict)[:5000]
        except:
            pass

        # Read ALL request body upfront
        request_body = None
        body_bytes = b""

        if method in ("POST", "PUT", "PATCH"):
            # Collect entire body
            while True:
                message = await receive()
                if message.get("type") == "http.request":
                    body = message.get("body", b"")
                    if body:
                        body_bytes += body
                if message.get("type") == "http.request" and not message.get("more_body", False):
                    break
                if message.get("type") != "http.request":
                    break

            if body_bytes:
                try:
                    request_body = body_bytes.decode("utf-8", errors="replace")[:10000]
                except:
                    pass

            # Create new receive function that returns the body we already read
            remaining_body = body_bytes

            async def body_receiver():
                nonlocal remaining_body
                if not remaining_body:
                    return {"type": "http.request", "body": b""}
                chunk = remaining_body
                remaining_body = b""
                return {"type": "http.request", "body": chunk}

            receive = body_receiver

        # Capture response
        response_body_bytes = bytearray()
        status_code = 200

        async def send_capturing(message):
            nonlocal status_code
            if message.get("type") == "http.response.start":
                status_code = message.get("status", 200)
            elif message.get("type") == "http.response.body":
                body = message.get("body", b"")
                if body:
                    response_body_bytes.extend(body)
            await send(message)

        start_time = time.time()
        await self.app(scope, receive, send_capturing)
        latency_ms = int((time.time() - start_time) * 1000)

        # Decode response body
        response_body = None
        if response_body_bytes:
            try:
                response_body = response_body_bytes.decode("utf-8", errors="replace")[:10000]
            except:
                pass

        # Extract model
        model_alias = None
        if request_body:
            try:
                body_json = json.loads(request_body)
                model_alias = body_json.get("model")
            except:
                pass

        # Log
        self._logger.info(
            "API Request",
            path=path,
            method=method,
            status_code=status_code,
            latency_ms=latency_ms,
            has_response_body=bool(response_body),
        )

        # Persist async
        asyncio.create_task(
            self._persist_log(
                endpoint=path,
                method=method,
                status_code=status_code,
                latency_ms=latency_ms,
                request_body=request_body,
                response_body=response_body,
                request_headers=request_headers,
                model_alias=model_alias,
            )
        )

    async def _persist_log(self, **kwargs):
        try:
            async with self._AsyncSessionLocal() as db:
                log = self._RequestLog(**kwargs)
                db.add(log)
                await db.commit()
        except Exception as exc:
            self._logger.error("Failed to persist request log", error=str(exc))
