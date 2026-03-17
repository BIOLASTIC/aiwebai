import httpx
import json
import asyncio


async def test_mcp_tools():
    url = "http://0.0.0.0:6400/mcp/"
    # Using the token we created earlier
    token = "sk-58RoF8_g5QhwCIRotxkI_FMfGYCNfEkfBEhuMWHJ-eA"
    headers = {"X-API-Key": token, "Accept": "text/event-stream"}

    print(f"Testing MCP Root at {url}...")
    async with httpx.AsyncClient() as client:
        try:
            # MCP Streamable HTTP starts with a GET to establish session
            response = await client.get(url, headers=headers)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("Session established successfully!")
                # In text/event-stream, we would read the session ID from the stream or headers
                session_id = response.headers.get("mcp-session-id")
                print(f"Session ID: {session_id}")
            else:
                print(f"Failed to establish session: {response.text}")
        except Exception as e:
            print(f"Error during request: {e}")


if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
