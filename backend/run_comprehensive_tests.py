import asyncio
import aiohttp
import json
import os
import sys

# Constants
BASE_URL = "http://127.0.0.1:6400"
USERNAME = "admin@local.host"
PASSWORD = "111111"

async def test_endpoint(session, method, path, headers, json_data=None, data=None, timeout=15):
    try:
        url = f"{BASE_URL}{path}"
        async with session.request(method, url, headers=headers, json=json_data, data=data, timeout=timeout) as resp:
            text = await resp.text()
            try:
                data_parsed = json.loads(text)
            except:
                data_parsed = text
            return resp.status, data_parsed
    except Exception as e:
        return 0, str(e)

async def poll_job(session, job_id, headers):
    for _ in range(10):
        await asyncio.sleep(3)
        status, data = await test_endpoint(session, "GET", f"/native/tasks/{job_id}", headers)
        if status == 200:
            if data.get("status") == "completed":
                return True, data.get("result_url")
            if data.get("status") == "failed":
                return False, data.get("error")
    return False, "Timeout"

async def main():
    async with aiohttp.ClientSession() as session:
        print("1. Authenticating...")
        # Use aiohttp.FormData for x-www-form-urlencoded
        form = aiohttp.FormData()
        form.add_field('username', USERNAME)
        form.add_field('password', PASSWORD)
        
        status, data = await test_endpoint(session, "POST", "/admin/login", headers={}, data=form)
        
        if status != 200:
            print(f"FAILED TO LOGIN: {status} {data}")
            return
            
        token = data.get("access_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        print("   Login Successful.")

        print("\n2. Fetching Active Accounts...")
        status, accounts = await test_endpoint(session, "GET", "/admin/accounts/", headers)
        if status != 200:
            print(f"FAILED TO FETCH ACCOUNTS: {status} {accounts}")
            return
        
        print(f"   Found {len(accounts)} accounts.")
        
        all_passed = True
        
        for acc in accounts:
            acc_id = acc["id"]
            provider = acc["provider"]
            label = acc["label"]
            print(f"\n--- Testing Account {acc_id}: {label} ({provider}) ---")
            
            # Fetch models for this account
            status, models = await test_endpoint(session, "GET", f"/admin/accounts/{acc_id}/models", headers)
            if status != 200:
                print(f"   FAILED TO FETCH MODELS for Account {acc_id}: {status}")
                all_passed = False
                continue
                
            for model in models:
                m_name = model["provider_model_name"]
                caps = model["capabilities"]
                print(f"   Model: {m_name}")
                
                # Test Chat
                if caps.get("chat"):
                    print(f"      [Chat]: ", end="", flush=True)
                    chat_payload = {
                        "model": m_name,
                        "messages": [{"role": "user", "content": "Hi"}],
                        "account_id": acc_id
                    }
                    s, d = await test_endpoint(session, "POST", "/v1/chat/completions", headers, chat_payload)
                    if s == 200:
                        content = d["choices"][0]["message"]["content"].replace("\n", " ")[:30]
                        print(f"OK ({content}...)")
                    else:
                        print(f"FAILED ({s}): {d}")
                        all_passed = False

                # Test Image
                if caps.get("images") or caps.get("image"):
                    print(f"      [Image]: ", end="", flush=True)
                    img_payload = {
                        "model": m_name,
                        "prompt": "A small blue dot",
                        "account_id": acc_id
                    }
                    s, d = await test_endpoint(session, "POST", "/native/tasks/image", headers, img_payload)
                    if s == 200:
                        job_id = d.get("job_id")
                        success, result = await poll_job(session, job_id, headers)
                        if success:
                            # Trim URL for display
                            display_url = result[:60] + "..." if len(result) > 60 else result
                            print(f"OK ({display_url})")
                        else:
                            print(f"FAILED: {result}")
                            all_passed = False
                    else:
                        print(f"FAILED ({s}): {d}")
                        all_passed = False
                        
        print("\n" + "="*40)
        if all_passed:
            print("FINAL RESULT: ALL TESTS PASSED (100% FIXED)")
            sys.exit(0)
        else:
            print("FINAL RESULT: SOME TESTS FAILED")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
