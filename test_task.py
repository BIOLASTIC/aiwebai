import asyncio
from backend.app.api.native.tasks import run_task_background

async def test():
    # Simulate a background task request
    req = {"prompt": "a cat", "model": "gemini-2.0-flash", "account_id": 1, "reference_file_ids": []}
    try:
        await run_task_background(1, "image", req)
        print('ok')
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test())
