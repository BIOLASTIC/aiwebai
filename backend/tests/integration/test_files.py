import pytest
import json
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_files_upload_persists():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Need to add an API key for authentication
        resp = await ac.post(
            "/v1/files",
            files={"file": ("ref.png", b"abc", "image/png")},
            headers={"X-API-Key": "sk-pXHS7Y5hP2f-6EEFHn_pVAUm_5mtFZmG3s43e38SbYc"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"].startswith("file_")
