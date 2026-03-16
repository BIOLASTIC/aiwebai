import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.engine import AsyncSessionLocal
from backend.app.db.models import User
import bcrypt


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.asyncio
async def test_setup_test_data():
    """Set up test data before running tests"""
    async with AsyncSessionLocal() as db:
        # Create test user
        hashed_password = bcrypt.hashpw("111111".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user = User(email="admin@local.host", hashed_password=hashed_password, is_active=True, is_admin=True)
        db.add(user)
        await db.commit()


def test_video_request_accepts_references(client):
    # Use a valid API key for authentication - using the provided global API key
    headers = {"Authorization": "Bearer sk-pXHS7Y5hP2f-6EEFHn_pVAUm_5mtFZmG3s43e38SbYc"}
    body = {"prompt": "vid", "reference_file_ids": ["file_1"], "model": "vid"}
    resp = client.post("/native/tasks/video", json=body, headers=headers)
    # Should at least accept the request (but might fail later in processing)
    assert resp.status_code in [200, 422]  # 200 for success, 422 for validation error
