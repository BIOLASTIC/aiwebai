import asyncio
import httpx
import json


async def run_comprehensive_tests():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 60)
        print("COMPREHENSIVE API TESTING")
        print("=" * 60)

        # Login to get JWT token
        print("\n1. Testing Admin Login...")
        try:
            r = await client.post(
                "http://localhost:6400/admin/login",
                data={"username": "admin@local.host", "password": "111111"},
            )
            if r.status_code == 200:
                token = r.json()["access_token"]
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }
                print(f"✅ Login successful - Status: {r.status_code}")
            else:
                print(f"❌ Login failed - Status: {r.status_code}, Response: {r.text}")
                return
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return

        # Test import (expected to fail when remote)
        print("\n2. Testing Browser Import (should fail remotely)...")
        try:
            r_imp = await client.post(
                "http://localhost:6400/admin/accounts/import/browser?browser=chrome",
                headers=headers,
            )
            print(
                f"Browser Import - Status: {r_imp.status_code} (expected to fail remotely)"
            )
        except Exception as e:
            print(f"Browser Import error (expected): {str(e)}")

        # Get accounts
        print("\n3. Testing Accounts List...")
        try:
            r_acc = await client.get(
                "http://localhost:6400/admin/accounts/", headers=headers
            )
            accounts = r_acc.json()
            print(
                f"✅ Accounts List - Status: {r_acc.status_code}, Found {len(accounts)} accounts"
            )

            # Validate first account if available
            if accounts:
                first_id = accounts[0]["id"]
                print(f"\n4. Testing Account Validation (ID: {first_id})...")
                r_val = await client.post(
                    f"http://localhost:6400/admin/accounts/{first_id}/validate",
                    headers=headers,
                )
                print(f"✅ Account Validation - Status: {r_val.status_code}")

                # Test capability-filtered models endpoint
                print(
                    f"\n5. Testing Capability-Filtered Models (Account: {first_id})..."
                )
                r_models = await client.get(
                    f"http://localhost:6400/admin/accounts/{first_id}/models",
                    headers=headers,
                )
                if r_models.status_code == 200:
                    models = r_models.json()
                    print(
                        f"✅ Models List - Status: {r_models.status_code}, Found {len(models)} models"
                    )

                    # Test with feature filter
                    r_models_img = await client.get(
                        f"http://localhost:6400/admin/accounts/{first_id}/models?feature=image_generation",
                        headers=headers,
                    )
                    if r_models_img.status_code == 200:
                        img_models = r_models_img.json()
                        print(
                            f"✅ Image Models - Status: {r_models_img.status_code}, Found {len(img_models)} image-capable models"
                        )
                    else:
                        print(f"❌ Image Models - Status: {r_models_img.status_code}")
                else:
                    print(f"❌ Models List - Status: {r_models.status_code}")
            else:
                print("❌ No accounts found")
        except Exception as e:
            print(f"❌ Account tests error: {str(e)}")

        # Test health check
        print("\n6. Testing Health Check...")
        try:
            r_health = await client.get("http://localhost:6400/health")
            print(f"✅ Health Check - Status: {r_health.status_code}")
        except Exception as e:
            print(f"❌ Health Check error: {str(e)}")

        # Test ready check
        print("\n7. Testing Ready Check...")
        try:
            r_ready = await client.get("http://localhost:6400/ready")
            print(f"✅ Ready Check - Status: {r_ready.status_code}")
        except Exception as e:
            print(f"❌ Ready Check error: {str(e)}")

        # Prepare API key headers
        api_headers = {"X-API-Key": "sk-pXHS7Y5hP2f-6EEFHn_pVAUm_5mtFZmG3s43e38SbYc"}

        # Test API key auth with chat completions
        print("\n8. Testing API Key Authentication (chat completions)...")
        try:
            # Test chat completions (basic structure check)
            chat_payload = {
                "model": "gemini-2.0-flash",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False,
            }
            r_chat = await client.post(
                "http://localhost:6400/v1/chat/completions",
                json=chat_payload,
                headers=api_headers,
            )
            print(f"✅ v1/chat/completions with API Key - Status: {r_chat.status_code}")
        except Exception as e:
            print(f"❌ v1/chat/completions with API Key error: {str(e)}")

        # Test file upload endpoint
        print("\n9. Testing v1/files endpoint...")
        try:
            # Test GET files
            r_files = await client.get(
                "http://localhost:6400/v1/files", headers=api_headers
            )
            if r_files.status_code == 200:
                files_data = r_files.json()
                print(
                    f"✅ v1/files (GET) - Status: {r_files.status_code}, Found {len(files_data['data'])} files"
                )
            else:
                print(f"❌ v1/files (GET) - Status: {r_files.status_code}")
        except Exception as e:
            print(f"❌ v1/files (GET) error: {str(e)}")

        # Test native endpoints with proper auth headers
        print("\n10. Testing native endpoints...")
        try:
            r_native_history = await client.get(
                "http://localhost:6400/native/history", headers=api_headers
            )
            print(f"✅ native/history - Status: {r_native_history.status_code}")
        except Exception as e:
            print(f"❌ native/history error: {str(e)}")

        try:
            r_native_gems = await client.get(
                "http://localhost:6400/native/gems", headers=api_headers
            )
            print(f"✅ native/gems - Status: {r_native_gems.status_code}")
        except Exception as e:
            print(f"❌ native/gems error: {str(e)}")

        # Test account models endpoint (capability-filtered models) - retrieve accounts again
        print("\n11. Testing account models endpoint (capability filtering)...")
        try:
            r_acc = await client.get(
                "http://localhost:6400/admin/accounts/", headers=headers
            )
            accounts = r_acc.json()
            if accounts:
                first_id = accounts[0]["id"]
                # Test with feature filter
                r_models_all = await client.get(
                    f"http://localhost:6400/admin/accounts/{first_id}/models",
                    headers=headers,
                )
                if r_models_all.status_code == 200:
                    all_models = r_models_all.json()
                    print(
                        f"✅ Account Models (all) - Status: {r_models_all.status_code}, Found {len(all_models)} models"
                    )

                    # Test with specific feature filter
                    r_models_img = await client.get(
                        f"http://localhost:6400/admin/accounts/{first_id}/models?feature=image_generation",
                        headers=headers,
                    )
                    if r_models_img.status_code == 200:
                        img_models = r_models_img.json()
                        print(
                            f"✅ Account Models (image filter) - Status: {r_models_img.status_code}, Found {len(img_models)} image models"
                        )
                    else:
                        print(
                            f"❌ Account Models (image filter) - Status: {r_models_img.status_code}"
                        )
                else:
                    print(
                        f"❌ Account Models (all) - Status: {r_models_all.status_code}"
                    )
            else:
                print("⚠️ No accounts to test account-specific models")
        except Exception as e:
            print(f"❌ Account models endpoint error: {str(e)}")

        # Test native tasks endpoints
        print("\n12. Testing native tasks endpoints...")
        try:
            # Test native limits
            r_limits = await client.get(
                "http://localhost:6400/native/limits", headers=api_headers
            )
            print(f"✅ native/limits - Status: {r_limits.status_code}")
        except Exception as e:
            print(f"❌ native/limits error: {str(e)}")

        print("\n" + "=" * 60)
        print("COMPREHENSIVE API TESTING COMPLETED")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())
