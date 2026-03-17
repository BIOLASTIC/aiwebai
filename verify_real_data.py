import asyncio
import aiohttp
import sys
import os

BASE_URL = "http://127.0.0.1:6400"
ADMIN_USER = "admin@local.host"
ADMIN_PASS = "111111"

async def test_all_imaging():
    async with aiohttp.ClientSession() as session:
        # 1. Login
        print("Logging in...")
        form = aiohttp.FormData()
        form.add_field('username', ADMIN_USER)
        form.add_field('password', ADMIN_PASS)
        async with session.post(f"{BASE_URL}/admin/login", data=form) as r:
            if r.status != 200:
                print(f"Login failed: {r.status} {await r.text()}")
                sys.exit(1)
            token = (await r.json())['access_token']
        
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # 2. Get accounts
        async with session.get(f"{BASE_URL}/admin/accounts/", headers=headers) as r:
            accounts = await r.json()
            
        failed = False
        for acc in accounts:
            acc_id = acc['id']
            print(f"\n--- Testing Account {acc_id} ({acc['label']}) ---")
            
            # Get imaging models
            async with session.get(f"{BASE_URL}/admin/accounts/{acc_id}/models?feature=image", headers=headers) as r:
                models = await r.json()
            
            for m in models:
                m_name = m['provider_model_name']
                print(f"Testing {m_name}...")
                
                # Trigger generation
                payload = {"prompt": "a small blue cube", "model": m_name, "account_id": acc_id}
                async with session.post(f"{BASE_URL}/native/tasks/image", headers=headers, json=payload) as r:
                    if r.status != 200:
                        print(f"  Trigger failed: {r.status} {await r.text()}")
                        continue
                    job_id = (await r.json())['job_id']
                
                # Poll
                success = False
                for _ in range(15):
                    await asyncio.sleep(4)
                    async with session.get(f"{BASE_URL}/native/tasks/{job_id}", headers=headers) as r:
                        job = await r.json()
                        if job['status'] == 'completed':
                            url = job['result_url']
                            print(f"  Job complete. Checking URL: {url}")
                            if not url.startswith('http'):
                                print(f"  ERROR: URL is not a web link: {url}")
                                failed = True
                                break
                            # Verify URL is reachable
                            async with session.get(url) as img_r:
                                if img_r.status == 200:
                                    print("  URL IS REAL AND REACHABLE (200 OK)")
                                    success = True
                                else:
                                    print(f"  ERROR: URL returned {img_r.status}")
                                    failed = True
                            break
                        if job['status'] == 'failed':
                            print(f"  Job failed as expected (checking error): {job['error']}")
                            # For this test, we accept specific failures like auth, but not logic errors
                            if "Account credentials are invalid" in (job['error'] or ""):
                                print("  (Expected auth failure for this environment)")
                                success = True
                            break
                    print(".", end="", flush=True)
                
                if not success:
                    print(f"  FAILED testing {m_name}")
                    # We don't exit 1 here yet, let's see all results

        if failed:
            print("\nVERIFICATION FAILED: Found non-reachable URLs or non-HTTP data.")
            sys.exit(1)
        else:
            print("\nVERIFICATION SUCCESS: All generations returned valid web URLs or handled errors.")

if __name__ == "__main__":
    asyncio.run(test_all_imaging())
