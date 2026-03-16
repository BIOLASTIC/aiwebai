from typing import Dict, Any, List
from sqlalchemy import func, select, desc
from backend.app.db.engine import AsyncSessionLocal
from backend.app.db.models import RequestLog
from datetime import datetime, timedelta


class AnalyticsAggregator:
    @staticmethod
    async def get_request_volume(days: int = 7) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            since = datetime.utcnow() - timedelta(days=days)
            stmt = (
                select(
                    func.strftime("%Y-%m-%d", RequestLog.created_at).label("date"),
                    func.count(RequestLog.id).label("count"),
                )
                .where(RequestLog.created_at >= since)
                .group_by("date")
                .order_by("date")
            )
            result = await db.execute(stmt)
            return [{"date": row.date, "count": row.count} for row in result]

    @staticmethod
    async def get_latency_stats() -> Dict[str, Any]:
        async with AsyncSessionLocal() as db:
            stmt = select(
                func.avg(RequestLog.latency_ms).label("avg"),
                func.min(RequestLog.latency_ms).label("min"),
                func.max(RequestLog.latency_ms).label("max"),
            )
            row = (await db.execute(stmt)).first()
            return {
                "avg": round(float(row.avg), 1) if row and row.avg else 0,
                "min": row.min if row else 0,
                "max": row.max if row else 0,
            }

    @staticmethod
    async def get_error_rate() -> float:
        async with AsyncSessionLocal() as db:
            total = (await db.execute(select(func.count(RequestLog.id)))).scalar() or 0
            errors = (
                await db.execute(
                    select(func.count(RequestLog.id)).where(RequestLog.status_code >= 400)
                )
            ).scalar() or 0
            return round((errors / total) * 100, 1) if total else 0.0

    @staticmethod
    async def get_recent_requests(limit: int = 10) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            stmt = select(RequestLog).order_by(desc(RequestLog.created_at)).limit(limit)
            logs = (await db.execute(stmt)).scalars().all()
            return [
                {
                    "timestamp": log.created_at.isoformat() if log.created_at else None,
                    "endpoint": log.endpoint,
                    "model": log.model_alias or log.resolved_model,
                    "status_code": log.status_code,
                    "latency": log.latency_ms,
                }
                for log in logs
            ]

    @staticmethod
    async def get_endpoint_breakdown() -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            stmt = (
                select(RequestLog.endpoint, func.count(RequestLog.id).label("count"))
                .where(RequestLog.endpoint.isnot(None))
                .group_by(RequestLog.endpoint)
                .order_by(desc("count"))
                .limit(10)
            )
            rows = (await db.execute(stmt)).all()
            return [{"endpoint": r.endpoint, "count": r.count} for r in rows]

    @staticmethod
    async def get_status_breakdown() -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            stmt = (
                select(RequestLog.status_code, func.count(RequestLog.id).label("count"))
                .where(RequestLog.status_code.isnot(None))
                .group_by(RequestLog.status_code)
                .order_by(desc("count"))
            )
            rows = (await db.execute(stmt)).all()
            return [{"status_code": r.status_code, "count": r.count} for r in rows]

    @staticmethod
    async def get_total_requests() -> int:
        async with AsyncSessionLocal() as db:
            return (await db.execute(select(func.count(RequestLog.id)))).scalar() or 0
