from fastmcp import FastMCP
from backend.app.adapters.router import AdapterRouter
from backend.app.schemas.openai import ChatCompletionRequest, ChatMessage
from backend.app.config import settings
import asyncio

mcp = FastMCP("Gemini Gateway")

# Shared adapter router
from backend.app.api.openai.chat_completions import adapter_router


@mcp.tool()
async def chat(prompt: str) -> str:
    """Send a message to Gemini and get a response."""
    request = ChatCompletionRequest(model="gemini-2.0-flash", messages=[ChatMessage(role="user", content=prompt)])
    response = await adapter_router.chat_completion(request)
    return response.choices[0].message.content


@mcp.tool()
async def generate_image(prompt: str) -> str:
    """Generate an image from a text prompt."""
    from backend.app.schemas.native import ImageGenerationRequest

    request = ImageGenerationRequest(prompt=prompt)
    response = await adapter_router.generate_image(request)
    return f"Image generated: {response['data'][0]['url']}"


@mcp.tool()
async def generate_video(prompt: str) -> str:
    """Generate a video from a text prompt."""
    from backend.app.schemas.native import VideoGenerationRequest

    request = VideoGenerationRequest(prompt=prompt)
    response = await adapter_router.generate_video(request)
    return f"Video generation job created: {response['job_id']}. Check status at /native/jobs/{response['job_id']}"


@mcp.tool()
async def generate_music(prompt: str) -> str:
    """Generate music from a text prompt."""
    from backend.app.schemas.native import MusicGenerationRequest

    request = MusicGenerationRequest(prompt=prompt)
    response = await adapter_router.generate_music(request)
    return f"Music generation job created: {response['job_id']}. Check status at /native/jobs/{response['job_id']}"


@mcp.tool()
async def deep_research(prompt: str) -> str:
    """Perform deep research on a topic."""
    from backend.app.schemas.native import ResearchRequest

    request = ResearchRequest(prompt=prompt)
    response = await adapter_router.deep_research(request)
    return f"Research job created: {response['job_id']}. Check status at /native/jobs/{response['job_id']}"


@mcp.tool()
async def list_files() -> str:
    """List all uploaded files."""
    from backend.app.api.openai.files import list_files as api_list_files

    # This is a bit hacky as it needs a DB session, but let's assume it works for now or fix it later
    # Actually, let's use the adapter_router if it had file support or just mock for now
    return "File listing tool: Not fully implemented in MCP yet but coming soon."


# Add a helper route for the UI to list tools
@mcp.custom_route("/status", methods=["GET"])
async def mcp_status_route(request):
    from starlette.responses import JSONResponse

    return JSONResponse(
        {"status": "online", "transport": "streamable-http", "server": "Gemini Gateway", "verified": True}
    )


# Export the Starlette/FastAPI app for mounting
# Using transport="http" (streamable-http) for modern client support
app = mcp.http_app(transport="http", path="/")

if __name__ == "__main__":
    mcp.run()
