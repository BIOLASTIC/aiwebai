from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.api_key_auth import get_user_by_key_or_jwt
from backend.app.db.engine import get_db
from backend.app.db.models import Job, User
from backend.app.jobs.manager import JobManager
from backend.app.utils.sse import create_sse_event

router = APIRouter(prefix="/native/jobs", tags=["native-jobs"])


@router.get("/{job_id}")
async def get_job_status(job_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_user_by_key_or_jwt)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job.id, "type": job.job_type, "status": job.status, "progress": job.progress_pct, "result_url": job.result_url, "error": job.error, "created_at": job.created_at, "completed_at": job.completed_at}


@router.get("/{job_id}/events")
async def get_job_events(job_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_user_by_key_or_jwt)):
    events = await JobManager.get_job_events(db, job_id)
    return [{"status": event.status, "progress": event.progress_pct, "timestamp": event.timestamp, "details": event.details} for event in events]


@router.get("/{job_id}/stream")
async def stream_job_events(job_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_user_by_key_or_jwt)):
    async def event_generator():
        job = await db.get(Job, job_id)
        if not job:
            yield create_sse_event({"error": "Job not found"}, event_type="error")
            return
        for event in await JobManager.get_job_events(db, job_id):
            yield create_sse_event({"job_id": job.id, "status": event.status, "progress": event.progress_pct, "details": event.details}, event_type="progress")
        yield create_sse_event({"job_id": job.id, "status": job.status, "progress": job.progress_pct, "result_url": job.result_url, "error": job.error}, event_type="complete")
    return StreamingResponse(event_generator(), media_type="text/event-stream")
