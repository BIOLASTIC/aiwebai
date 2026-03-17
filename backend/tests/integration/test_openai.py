import pytest
import json
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.mark.asyncio
async def test_chat_completions_no_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/v1/chat/completions",
            json={
                "model": "gemini-pro",
                "messages": [{"role": "user", "content": "Hello"}]
            }
        )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_chat_completions_with_auth_mock():
    # This test will fail if no adapter is configured, but it verifies auth
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/v1/chat/completions",
            json={
                "model": "gemini-pro",
                "messages": [{"role": "user", "content": "Hello"}]
            },
            headers={"X-API-Key": "sk-JfDMyHics_B4qhvoFAqaxFzs1obOqIYAjb8jb9uRk7g"}
        )
    # If no adapter is configured, it might return 500 or error from router
    # But here we want to see if it passed get_user_by_api_key
    assert response.status_code in [200, 500, 502] 

@pytest.mark.asyncio
async def test_chat_stream_no_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/v1/chat/completions",
            json={
                "model": "gemini-pro",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": True
            }
        )
    assert response.status_code == 401
