import asyncio
import httpx

async def run():
    async with httpx.AsyncClient() as client:
        r = await client.post("http://localhost:6400/admin/login", data={"username": "admin@local.host", "password": "111111"})
        print("Login status:", r.status_code)
        if r.status_code == 200:
            print("Token received")

asyncio.run(run())
