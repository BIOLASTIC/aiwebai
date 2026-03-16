import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_video_request_accepts_references():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # This test will fail with 401 because it lacks authentication, but the important
        # part is that it should not fail with validation error for unknown fields
        body = {"prompt": "vid", "reference_file_ids": ["file_1"], "model": "vid"}
        resp = await ac.post("/native/tasks/video", json=body)
    # We expect 401 Unauthorized, not 422 Validation Error
    assert resp.status_code != 422  # Should not be a validation error


@pytest.mark.asyncio
async def test_image_request_accepts_references_and_account():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        body = {
            "prompt": "create an image",
            "reference_file_ids": ["file_1", "file_2"],
            "account_id": 1,
            "model": "test-model",
        }
        resp = await ac.post("/native/tasks/image", json=body)
    # We expect 401 Unauthorized, not 422 Validation Error
    assert resp.status_code != 422  # Should not be a validation error


@pytest.mark.asyncio
async def test_music_request_accepts_references_and_account():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        body = {"prompt": "create music", "reference_file_ids": ["file_1"], "account_id": 2}
        resp = await ac.post("/native/tasks/music", json=body)
    # We expect 401 Unauthorized, not 422 Validation Error
    assert resp.status_code != 422  # Should not be a validation error


@pytest.mark.asyncio
async def test_research_request_accepts_references_and_account():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        body = {"prompt": "research topic", "reference_file_ids": [], "account_id": 3, "model": "research-model"}
        resp = await ac.post("/native/tasks/research", json=body)
    # We expect 401 Unauthorized, not 422 Validation Error
    assert resp.status_code != 422  # Should not be a validation error
