import httpx
import json
import asyncio
from typing import Dict, Any, List
from sqlalchemy.future import select
from backend.app.db.engine import AsyncSessionLocal
from backend.app.db.models import Webhook
from backend.app.logging.structured import logger

async def dispatch_event(event_type: str, data: Dict[str, Any]):
    """Dispatches an event to all registered webhooks for that event type."""
    logger.info("Dispatching event", event_type=event_type)
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Webhook).where(Webhook.status == "active")
        )
        webhooks = result.scalars().all()
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for webhook in webhooks:
            if "*" in webhook.event_types or event_type in webhook.event_types:
                tasks.append(send_webhook(client, webhook.url, event_type, data, webhook.secret))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

async def send_webhook(client: httpx.AsyncClient, url: str, event_type: str, data: Dict[str, Any], secret: str = None):
    payload = {
        "event": event_type,
        "data": data
    }
    headers = {"Content-Type": "application/json"}
    if secret:
        # Simplified: in real app, use HMAC signature
        headers["X-Gateway-Secret"] = secret
        
    try:
        response = await client.post(url, json=payload, headers=headers, timeout=10.0)
        logger.info("Webhook sent", url=url, status_code=response.status_code)
    except Exception as e:
        logger.error("Webhook failed", url=url, error=str(e))
