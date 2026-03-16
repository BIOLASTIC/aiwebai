import asyncio
import httpx
import sys

BASE_URL = "http://0.0.0.0:6400"
API_KEY = "sk-pXHS7Y5hP2f-6EEFHn_pVAUm_5mtFZmG3s43e38SbYc"

async def test_endpoint(client, method, path, **kwargs):
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = await client.get(url, **kwargs)
        elif method == "POST":
            response = await client.post(url, **kwargs)
        
        status = response.status_code
        print(f"[{method}] {path} -> {status}")
        if status >= 400:
            print(f"  Error Body: {response.text}")
        
        try:
            return status, response.json() if status < 500 else None
        except:
            return status, response.text
    except Exception as e:
        print(f"[{method}] {path} -> EXCEPTION: {e}")
        return 500, None

async def run_tests():
    async with httpx.AsyncClient(timeout=10.0) as client:
        print("--- Foundation Endpoints ---")
        await test_endpoint(client, "GET", "/health")
        await test_endpoint(client, "GET", "/ready")
        
        print("\n--- Admin Auth Endpoints ---")
        # OAuth2PasswordRequestForm expects data, not json
        status, login_data = await test_endpoint(client, "POST", "/admin/login", data={"username": "admin@local.host", "password": "111111"})
        token = None
        if status == 200:
            token = login_data.get("access_token")
            print("  Login Successful")
        
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        print("\n--- Admin Management Endpoints ---")
        await test_endpoint(client, "GET", "/admin/users/", headers=headers)
        await test_endpoint(client, "GET", "/admin/accounts/", headers=headers)
        await test_endpoint(client, "GET", "/admin/models/", headers=headers)
        
        print("\n--- OpenAI Compatibility Endpoints ---")
        auth_headers = {"X-API-Key": API_KEY}
        await test_endpoint(client, "POST", "/v1/chat/completions", json={
            "model": "gemini-pro",
            "messages": [{"role": "user", "content": "Hello"}]
        }, headers=auth_headers)
        
        print("\n--- Native Gemini Endpoints ---")
        await test_endpoint(client, "GET", "/native/limits", headers=auth_headers)
        await test_endpoint(client, "POST", "/native/tasks/video", json={"prompt": "test video"}, headers=auth_headers)
        await test_endpoint(client, "POST", "/native/tasks/music", json={"prompt": "test music"}, headers=auth_headers)
        await test_endpoint(client, "POST", "/native/tasks/research", json={"prompt": "test research"}, headers=auth_headers)

if __name__ == "__main__":
    asyncio.run(run_tests())
