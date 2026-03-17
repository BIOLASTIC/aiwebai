from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import Job, JobEvent


class JobManager:
    @staticmethod
    async def create_job(db: AsyncSession, request_id: Optional[int], account_id: Optional[int], job_type: str) -> Job:
        job = Job(request_id=request_id, account_id=account_id, job_type=job_type, status="pending")
        db.add(job)
        await db.flush()
        db.add(JobEvent(job_id=job.id, status="submitted", progress_pct=0.0, details={"job_type": job_type}))
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def update_job(
        db: AsyncSession,
        job_id: int,
        status: str,
        progress: float = 0.0,
        result_url: Optional[str] = None,
        error: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        job = await db.get(Job, job_id)
        if not job:
            return None
        job.status = status
        job.progress_pct = progress
        if result_url is not None:
            job.result_url = result_url
        if error is not None:
            job.error = error
        if status == "completed":
            job.completed_at = datetime.utcnow()
        db.add(JobEvent(job_id=job.id, status=status, progress_pct=progress, details=details or {"error": error, "result_url": result_url}))
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def get_job_events(db: AsyncSession, job_id: int):
        return (await db.execute(select(JobEvent).where(JobEvent.job_id == job_id).order_by(JobEvent.id.asc()))).scalars().all()
