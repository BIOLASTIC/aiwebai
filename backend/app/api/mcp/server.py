from __future__ import annotations

import json
from typing import Optional

from fastmcp import FastMCP
from backend.app.adapters.router import AdapterRouter
from backend.app.schemas.openai import ChatCompletionRequest, ChatMessage
from backend.app.config import settings

mcp = FastMCP("Gemini Gateway")

# Shared adapter router
from backend.app.api.openai.chat_completions import adapter_router


# ---------------------------------------------------------------------------
# Core generation tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def chat(
    prompt: str,
    account_id: Optional[int] = None,
    adapter: Optional[str] = None,
) -> str:
    """Send a message to Gemini and get a response.

    adapter: 'webapi' (gemini-webapi) or 'mcpcli' (gemini-web-mcp-cli) — omit for auto.
    account_id: ID of a specific configured account to use.
    """
    try:
        model = "gemini-2.0-flash"
        request = ChatCompletionRequest(
            model=model,
            messages=[ChatMessage(role="user", content=prompt)],
        )
        # adapter/account_id selection: route via best adapter if specified
        if adapter or account_id:
            from backend.app.accounts.manager import account_manager
            from backend.app.adapters.webapi_adapter import WebApiAdapter
            from backend.app.adapters.mcpcli_adapter import McpCliAdapter

            chosen = None
            if account_id:
                chosen = account_manager.get_adapter_for_account(account_id)
            if chosen is None and adapter:
                all_adapters = account_manager.get_all_adapters()
                for a in all_adapters:
                    if adapter == "webapi" and isinstance(a, WebApiAdapter):
                        chosen = a
                        break
                    if adapter == "mcpcli" and isinstance(a, McpCliAdapter):
                        chosen = a
                        break
            if chosen:
                response = await chosen.chat_completion(request)
                return response.choices[0].message.content

        response = await adapter_router.chat_completion(request)
        return response.choices[0].message.content
    except Exception as e:
        return (
            f"Chat failed: {str(e)}. "
            "Try specifying adapter='webapi' with a valid account or check your credentials."
        )


@mcp.tool()
async def generate_image(
    prompt: str,
    account_id: Optional[int] = None,
    adapter: Optional[str] = None,
) -> str:
    """Generate an image from a text prompt.

    adapter: 'webapi' (gemini-webapi) or 'mcpcli' (gemini-web-mcp-cli) — omit for auto.
    account_id: ID of a specific configured account to use.
    """
    try:
        from backend.app.schemas.native import ImageGenerationRequest

        request = ImageGenerationRequest(prompt=prompt, account_id=account_id)
        response = await adapter_router.generate_image(request, adapter=adapter)
        data = response.get("data", [])
        if not data:
            return (
                "Image generation returned no results. "
                "Try specifying adapter='mcpcli' and ensure 'gemcli login' has been run, "
                "or adapter='webapi' with a valid account."
            )
        return f"Image generated: {data[0]['url']}"
    except Exception as e:
        return (
            f"Image generation failed: {str(e)}. "
            "Try specifying adapter='mcpcli' and running 'gemcli login' first, "
            "or adapter='webapi' with a valid account."
        )


@mcp.tool()
async def generate_video(
    prompt: str,
    account_id: Optional[int] = None,
    adapter: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """Generate a video from a text prompt.

    adapter: 'webapi' (gemini-webapi) or 'mcpcli' (gemini-web-mcp-cli) — omit for auto.
    Note: Video generation requires an mcpcli account. webapi does not support video.
    account_id: ID of a specific configured account to use.
    """
    try:
        response = await adapter_router.generate_video(
            prompt=prompt,
            model=model,
            account_id=account_id,
            reference_files=None,
            options={},
            adapter=adapter,
        )
        job_id = getattr(response, "job_id", None) or response.metadata.get("job_id", "unknown")
        return f"Video generation job created: {job_id}. Check status at /native/jobs/{job_id}"
    except Exception as e:
        return (
            f"Video generation failed: {str(e)}. "
            "Video generation requires an mcpcli account. "
            "Use adapter='mcpcli' and ensure 'gemcli login' has been run."
        )


@mcp.tool()
async def generate_music(
    prompt: str,
    account_id: Optional[int] = None,
    adapter: Optional[str] = None,
) -> str:
    """Generate music from a text prompt.

    adapter: 'webapi' (gemini-webapi) or 'mcpcli' (gemini-web-mcp-cli) — omit for auto.
    Note: Music generation requires an mcpcli account. webapi does not support music.
    account_id: ID of a specific configured account to use.
    """
    try:
        result = await adapter_router.generate_music(
            prompt=prompt,
            account_id=account_id,
            adapter=adapter,
        )
        return f"Music generation job created: {result}. Check status at /native/jobs/{result}"
    except Exception as e:
        return (
            f"Music generation failed: {str(e)}. "
            "Music generation requires an mcpcli account. "
            "Use adapter='mcpcli' and ensure 'gemcli login' has been run."
        )


@mcp.tool()
async def deep_research(
    prompt: str,
    account_id: Optional[int] = None,
    adapter: Optional[str] = None,
) -> str:
    """Perform deep research on a topic.

    adapter: 'webapi' (gemini-webapi) or 'mcpcli' (gemini-web-mcp-cli) — omit for auto.
    Note: Deep research requires an mcpcli account. webapi does not support research.
    account_id: ID of a specific configured account to use.
    """
    try:
        result = await adapter_router.generate_research(
            prompt=prompt,
            account_id=account_id,
            adapter=adapter,
        )
        return f"Research job created: {result}. Check status at /native/jobs/{result}"
    except Exception as e:
        return (
            f"Deep research failed: {str(e)}. "
            "Deep research requires an mcpcli account. "
            "Use adapter='mcpcli' and ensure 'gemcli login' has been run."
        )


# ---------------------------------------------------------------------------
# Discovery tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_accounts() -> str:
    """List all available Gemini accounts with their capabilities and adapter type.

    Returns JSON with accounts, their provider (webapi/mcpcli), capabilities, and health status.
    """
    try:
        from sqlalchemy import select
        from backend.app.db.engine import AsyncSessionLocal
        from backend.app.db.models import Account
        from backend.app.accounts.manager import account_manager
        from backend.app.adapters.webapi_adapter import WebApiAdapter
        from backend.app.adapters.mcpcli_adapter import McpCliAdapter

        _PROVIDER_CAPS = {
            "webapi": ["chat", "image"],
            "mcpcli": ["chat", "image", "video", "music", "research"],
        }

        async with AsyncSessionLocal() as db:
            rows = (
                await db.execute(select(Account).where(Account.status == "active"))
            ).scalars().all()

        result = []
        for acct in rows:
            adp = account_manager.get_adapter_for_account(acct.id)
            adapter_type = "webapi" if isinstance(adp, WebApiAdapter) else "mcpcli" if isinstance(adp, McpCliAdapter) else acct.provider
            capabilities = _PROVIDER_CAPS.get(adapter_type, ["chat"])
            result.append({
                "id": acct.id,
                "label": acct.label,
                "provider": acct.provider,
                "adapter_type": adapter_type,
                "health": acct.health_status,
                "capabilities": capabilities,
                "active": adp is not None,
            })

        return json.dumps({"accounts": result, "total": len(result)}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to list accounts: {str(e)}"})


@mcp.tool()
async def list_models(capability: Optional[str] = None) -> str:
    """List available models, optionally filtered by capability.

    capability: one of 'chat', 'image', 'video', 'music', 'research' — omit for all.
    Returns JSON with model list.
    """
    try:
        from sqlalchemy import select
        from backend.app.db.engine import AsyncSessionLocal
        from backend.app.db.models import Model

        async with AsyncSessionLocal() as db:
            query = select(Model).where(Model.status == "active")
            rows = (await db.execute(query)).scalars().all()

        models = []
        for m in rows:
            caps = m.capabilities or {}
            if capability:
                cap_key = capability if capability != "image" else "images"
                if not caps.get(cap_key) and not caps.get(capability):
                    continue
            models.append({
                "id": m.provider_model_name,
                "display_name": m.display_name,
                "family": m.family,
                "source_provider": m.source_provider,
                "capabilities": caps,
            })

        return json.dumps({"models": models, "total": len(models)}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to list models: {str(e)}"})


@mcp.tool()
async def get_capabilities() -> str:
    """Get system capabilities: which accounts are available and what they can generate.

    Returns a human-readable summary of accounts, their adapter types, capabilities, and auth status.
    """
    try:
        from sqlalchemy import select
        from backend.app.db.engine import AsyncSessionLocal
        from backend.app.db.models import Account
        from backend.app.accounts.manager import account_manager
        from backend.app.adapters.webapi_adapter import WebApiAdapter
        from backend.app.adapters.mcpcli_adapter import McpCliAdapter

        _PROVIDER_CAPS = {
            "webapi": ["chat", "image"],
            "mcpcli": ["chat", "image", "video", "music", "research"],
        }

        async with AsyncSessionLocal() as db:
            rows = (
                await db.execute(select(Account).where(Account.status == "active"))
            ).scalars().all()

        webapi_accounts = []
        mcpcli_accounts = []
        total_active = 0

        for acct in rows:
            adp = account_manager.get_adapter_for_account(acct.id)
            is_active = adp is not None
            if is_active:
                total_active += 1
            if isinstance(adp, WebApiAdapter) or acct.provider == "webapi":
                webapi_accounts.append({"id": acct.id, "label": acct.label, "active": is_active, "health": acct.health_status})
            elif isinstance(adp, McpCliAdapter) or acct.provider == "mcpcli":
                mcpcli_accounts.append({"id": acct.id, "label": acct.label, "active": is_active, "health": acct.health_status})

        summary = {
            "system_status": "online" if total_active > 0 else "degraded — no active accounts",
            "total_accounts": len(rows),
            "active_accounts": total_active,
            "webapi_accounts": webapi_accounts,
            "webapi_capabilities": _PROVIDER_CAPS["webapi"],
            "mcpcli_accounts": mcpcli_accounts,
            "mcpcli_capabilities": _PROVIDER_CAPS["mcpcli"],
            "capability_notes": {
                "chat": "Available via webapi or mcpcli",
                "image": "Available via webapi or mcpcli (mcpcli required for imagen-3.0/veo models)",
                "video": "mcpcli only — webapi does not support video generation",
                "music": "mcpcli only — webapi does not support music generation",
                "research": "mcpcli only — webapi does not support deep research",
            },
        }

        return json.dumps(summary, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to get capabilities: {str(e)}"})


# ---------------------------------------------------------------------------
# Miscellaneous
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_files() -> str:
    """List all uploaded files."""
    return "File listing tool: Not fully implemented in MCP yet but coming soon."


# ---------------------------------------------------------------------------
# Status route for UI health-check
# ---------------------------------------------------------------------------

@mcp.custom_route("/status", methods=["GET"])
async def mcp_status_route(request):
    from starlette.responses import JSONResponse

    try:
        tools = await mcp.list_tools()
        tools_count = len(tools) if tools else 0
    except Exception:
        tools_count = 0
    return JSONResponse(
        {
            "status": "online",
            "transport": "streamable-http",
            "server": "Gemini Gateway",
            "verified": True,
            "tools_count": tools_count,
        }
    )


# Export the Starlette/FastAPI app for mounting
app = mcp.http_app(transport="http", path="/")

if __name__ == "__main__":
    mcp.run()
