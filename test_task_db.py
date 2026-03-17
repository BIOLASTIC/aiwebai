import asyncio
from backend.app.api.native.tasks import run_task_background

async def test():
    req = {"prompt": "a cat", "model": "gemini-2.0-flash", "account_id": 1, "reference_file_ids": []}
    try:
        await run_task_background(1, "image", req)
        import sqlite3
        conn = sqlite3.connect('backend/gemini_gateway.db')
        c = conn.cursor()
        c.execute('SELECT result_url FROM jobs WHERE id=1')
        print('RESULT_URL:', c.fetchone()[0])
        conn.close()
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test())
