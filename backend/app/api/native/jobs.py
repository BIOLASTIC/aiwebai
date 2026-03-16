from typing import Optional, AsyncGenerator, Dict, Any
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.db.engine import get_db
from backend.app.db.models import User, Job, JobEvent
from backend.app.auth.api_key_auth import get_user_by_key_or_jwt
from backend.app.utils.sse import create_sse_event
from backend.app.jobs.manager import JobManager

router = APIRouter(prefix="/native/jobs", tags=["native-jobs"])


@router.get("/{job_id}")
async def get_job_status(job_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_user_by_key_or_jwt)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "type": job.job_type,
        "status": job.status,
        "progress": job.progress_pct,
        "result_url": job.result_url,
        "error": job.error,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
    }


@router.get("/{job_id}/events")
async def get_job_events(job_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_user_by_key_or_jwt)):
    """Get all lifecycle events for a job"""
    events = await JobManager.get_job_events(db, job_id)
    return [
        {"status": event.status, "progress": event.progress_pct, "timestamp": event.timestamp, "details": event.details}
        for event in events
    ]


@router.get("/{job_id}/stream")
async def stream_job_events(
    job_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_user_by_key_or_jwt)
):
    """
    Stream job progress events via Server-Sent Events (SSE).
    This endpoint sends progress updates for long-running tasks like video/music/research generation.
    """

    async def event_generator():
        # Check if job exists
        job = await db.get(Job, job_id)
        if not job:
            yield create_sse_event({"error": "Job not found"}, event_type="error")
            return

        # Send initial event
        yield create_sse_event(
            {
                "job_id": job.id,
                "type": job.job_type,
                "status": job.status,
                "progress": job.progress_pct,
                "message": f"Monitoring job {job.id}",
            },
            event_type="progress",
        )

        # Poll for job updates
        last_status = job.status
        last_progress = job.progress_pct

        while True:
            # Get updated job status
            updated_job = await db.get(Job, job_id)

            if not updated_job:
                yield create_sse_event({"error": "Job no longer exists"}, event_type="error")
                break

            # If status or progress changed, send update
            if (
                updated_job.status != last_status or abs(updated_job.progress_pct - last_progress) >= 0.01
            ):  # At least 1% change
                event_data = {
                    "job_id": updated_job.id,
                    "type": updated_job.job_type,
                    "status": updated_job.status,
                    "progress": updated_job.progress_pct,
                    "result_url": updated_job.result_url,
                    "error": updated_job.error,
                }

                # Determine event type based on status
                if updated_job.status == "completed":
                    event_type = "completed"
                    yield create_sse_event(event_data, event_type=event_type)
                    break
                elif updated_job.status == "failed":
                    event_type = "error"
                    yield create_sse_event(event_data, event_type=event_type)
                    break
                else:
                    event_type = "progress"
                    yield create_sse_event(event_data, event_type=event_type)

                last_status = updated_job.status
                last_progress = updated_job.progress_pct

            # Wait before next poll
            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )
