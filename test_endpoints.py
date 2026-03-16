import asyncio
import httpx

async def run():
    async with httpx.AsyncClient() as client:
        r = await client.post("http://localhost:6400/admin/login", data={"username": "admin@local.host", "password": "111111"})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test import
        print("Testing import...")
        r_imp = await client.post("http://localhost:6400/admin/accounts/import/browser?browser=chrome", headers=headers)
        print("Import response:", r_imp.status_code, r_imp.text)
        
        # Get accounts
        r_acc = await client.get("http://localhost:6400/admin/accounts/", headers=headers)
        accounts = r_acc.json()
        print("Accounts:", len(accounts))
        if accounts:
            first_id = accounts[0]["id"]
            print(f"Testing validate for account {first_id}...")
            r_val = await client.post(f"http://localhost:6400/admin/accounts/{first_id}/validate", headers=headers)
            print("Validate response:", r_val.status_code, r_val.text)

asyncio.run(run())
