import asyncio
from backend.app.models.registry import model_registry
async def test():
    await model_registry.discover_models()
    import sqlite3
    conn = sqlite3.connect('gemini_gateway.db')
    print(conn.cursor().execute('SELECT id, provider_model_name, capabilities FROM models WHERE source_provider=\"mcpcli\"').fetchall())
    conn.close()
asyncio.run(test())
