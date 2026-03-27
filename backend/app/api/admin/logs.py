from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from backend.app.db.engine import get_db
from backend.app.db.models import RequestLog, User, Account
from backend.app.auth.dependencies import get_current_admin
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/admin/logs", tags=["admin-logs"])


class LogEntry(BaseModel):
    id: int
    user_id: Optional[int]
    account_id: Optional[int]
    provider: Optional[str]
    endpoint: Optional[str]
    model_alias: Optional[str]
    resolved_model: Optional[str]
    feature_type: Optional[str]
    stream_mode: Optional[bool]
    latency_ms: Optional[int]
    status_code: Optional[int]
    retry_count: Optional[int]
    prompt_hash: Optional[str]
    created_at: datetime
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    request_headers: Optional[str] = None
    method: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedLogs(BaseModel):
    items: List[LogEntry]
    total: int
    page: int
    page_size: int


@router.get("/", response_model=PaginatedLogs)
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    endpoint: Optional[str] = None,
    status_code: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    offset = (page - 1) * page_size

    query = select(RequestLog).order_by(desc(RequestLog.created_at))

    if endpoint:
        query = query.where(RequestLog.endpoint == endpoint)
    if status_code:
        query = query.where(RequestLog.status_code == status_code)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Get items
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedLogs(items=items, total=total, page=page, page_size=page_size)


@router.get("/{log_id}", response_model=LogEntry)
async def get_log_detail(log_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    log = await db.get(RequestLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return log
