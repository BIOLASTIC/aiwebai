import asyncio
import httpx

async def run():
    async with httpx.AsyncClient() as client:
        # Login
        r = await client.post("http://0.0.0.0:6400/admin/login", data={"username": "admin@local.host", "password": "111111"})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Add account
        payload = {
            "label": "Test MCP Account",
            "provider": "mcpcli",
            "auth_methods": [
                {
                    "auth_type": "none",
                    "credentials": "{}"
                }
            ]
        }
        r2 = await client.post("http://0.0.0.0:6400/admin/accounts/", json=payload, headers=headers)
        print("Create account:", r2.status_code, r2.text)
        
        if r2.status_code == 200:
            # Refresh adapters in the server
            r3 = await client.post("http://0.0.0.0:6400/admin/accounts/refresh", headers=headers)
            print("Refresh accounts:", r3.status_code, r3.text)

asyncio.run(run())
