from fastmcp import FastMCP
from backend.app.adapters.router import AdapterRouter
from backend.app.schemas.openai import ChatCompletionRequest, ChatMessage
from backend.app.config import settings
import asyncio

mcp = FastMCP("Gemini Gateway")

# Shared adapter router (In a real app, this would be a global or injected)
from backend.app.api.openai.chat_completions import adapter_router

@mcp.tool()
async def chat(prompt: str) -> str:
    """Send a message to Gemini and get a response."""
    request = ChatCompletionRequest(
        model="gemini-pro",
        messages=[ChatMessage(role="user", content=prompt)]
    )
    response = await adapter_router.chat_completion(request)
    return response.choices[0].message.content

@mcp.tool()
async def generate_image(prompt: str) -> str:
    """Generate an image from a text prompt."""
    from backend.app.schemas.native import ImageGenerationRequest
    request = ImageGenerationRequest(prompt=prompt)
    response = await adapter_router.generate_image(request)
    return f"Image generated: {response['data'][0]['url']}"

if __name__ == "__main__":
    mcp.run()
