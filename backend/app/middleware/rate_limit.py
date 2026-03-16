from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Dict, Tuple, List

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.visitor_records: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next):
        # Use API key or IP for rate limiting
        client_id = request.headers.get("X-API-Key") or request.client.host
        
        now = time.time()
        if client_id not in self.visitor_records:
            self.visitor_records[client_id] = []
        
        # Filter records in the last 60 seconds
        self.visitor_records[client_id] = [t for t in self.visitor_records[client_id] if now - t < 60]
        
        if len(self.visitor_records[client_id]) >= self.requests_per_minute:
            raise HTTPException(status_code=429, detail="Too many requests")
        
        self.visitor_records[client_id].append(now)
        response = await call_next(request)
        return response
