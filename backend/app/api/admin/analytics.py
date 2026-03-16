from fastapi import APIRouter, Depends
from backend.app.analytics.aggregator import AnalyticsAggregator
from backend.app.auth.dependencies import get_current_admin
from backend.app.db.models import User

router = APIRouter(prefix="/admin/analytics", tags=["admin-analytics"])


@router.get("/summary")
async def get_summary(admin: User = Depends(get_current_admin)):
    volume = await AnalyticsAggregator.get_request_volume()
    latency = await AnalyticsAggregator.get_latency_stats()
    error_rate = await AnalyticsAggregator.get_error_rate()
    total = await AnalyticsAggregator.get_total_requests()
    endpoints = await AnalyticsAggregator.get_endpoint_breakdown()
    statuses = await AnalyticsAggregator.get_status_breakdown()
    return {
        "volume": volume,
        "latency": latency,
        "error_rate": error_rate,
        "total_requests": total,
        "endpoints": endpoints,
        "statuses": statuses,
    }


@router.get("/recent")
async def get_recent_requests(admin: User = Depends(get_current_admin)):
    return await AnalyticsAggregator.get_recent_requests()
