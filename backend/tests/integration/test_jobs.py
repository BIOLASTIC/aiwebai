import asyncio
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.db.models import Job, JobEvent
from backend.app.jobs.manager import JobManager
from backend.app.db.engine import AsyncSessionLocal


@pytest.mark.asyncio
async def test_video_job_lifecycle_events():
    """Test that video jobs emit proper lifecycle events"""
    async with AsyncSessionLocal() as db:
        # Create a video job
        job = await JobManager.create_job(db, request_id=None, account_id=None, job_type="video")

        # Initially, job should be in pending state and should have a "submitted" event
        assert job.status == "pending"

        # Check that a job event was recorded for the creation ("submitted")
        events = await JobManager.get_job_events(db, job.id)
        assert len(events) >= 1  # At least the initial "submitted" event
        assert "submitted" in [e.status for e in events]

        # Update job status to simulate lifecycle
        await JobManager.update_job(db, job.id, "provider_processing")
        updated_job = await db.get(Job, job.id)
        assert updated_job.status == "provider_processing"

        # Check that a new event was recorded
        events = await JobManager.get_job_events(db, job.id)
        assert "provider_processing" in [e.status for e in events]

        await JobManager.update_job(db, job.id, "polling")
        updated_job = await db.get(Job, job.id)
        assert updated_job.status == "polling"

        # Check that a new event was recorded
        events = await JobManager.get_job_events(db, job.id)
        assert "polling" in [e.status for e in events]

        await JobManager.update_job(db, job.id, "completed", progress=1.0, result_url="test_url")
        updated_job = await db.get(Job, job.id)
        assert updated_job.status == "completed"
        assert updated_job.result_url == "test_url"

        # Final check that all events are recorded
        events = await JobManager.get_job_events(db, job.id)
        event_statuses = [e.status for e in events]
        assert "submitted" in event_statuses  # Initial event from creation
        assert "provider_processing" in event_statuses
        assert "polling" in event_statuses
        assert "completed" in event_statuses
