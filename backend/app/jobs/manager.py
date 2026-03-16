from typing import Dict, Any, Optional
import uuid
import time
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.models import Job, RequestLog
from backend.app.schemas.native import JobResponse

class JobManager:
    @staticmethod
    async def create_job(db: AsyncSession, request_id: Optional[int], account_id: Optional[int], job_type: str) -> Job:
        job = Job(
            request_id=request_id,
            account_id=account_id,
            job_type=job_type,
            status="pending"
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def update_job(db: AsyncSession, job_id: int, status: str, progress: float = 0.0, result_url: Optional[str] = None, error: Optional[str] = None):
        result = await db.get(Job, job_id)
        if result:
            result.status = status
            result.progress_pct = progress
            if result_url:
                result.result_url = result_url
            if error:
                result.error = error
            await db.commit()
            return result
        return None
